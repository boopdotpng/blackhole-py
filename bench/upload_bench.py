"""Host -> DRAM weight upload rates with and without sysmem / a DMA core (see bench/upload.c).

  CARD=0 python3.14 bench/upload_bench.py [MiB]

  A. Allocator.copyin/copyout end to end: from a Device.pinned() buffer, from a page-aligned buffer pinned on the fly,
     and staged through 2 x 8 MiB pinned slots (bytes: data starts 32 B into the object, so not 64 B aligned)
  B. sysmem + service core DMA, data already pinned (one OP_COPY of the whole buffer)
  C. no sysmem: host stores through a 2 MiB BAR TLB window into one DRAM bank, uncached and write-combined
  D. sysmem, no DMA core: N workers pull from pinned host memory and write DRAM (bench/upload.c)"""
import mmap, os, struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fw, pci
from device import Device
from pci import HostMemory, TLB_SIZE, ioctl, map_memory, view_at

def gbs(n, s): return f"{n / s / 1e9:6.2f} GB/s"

def check(dev, addr, want, label):
  got = bytearray(len(want))
  dev.allocator.copyout(got, addr)
  for off in range(0, len(want), 1 << 20):          # say where it first differs
    if got[off:off + (1 << 20)] != want[off:off + (1 << 20)]: raise RuntimeError(f"{label}: mismatch in MiB {off >> 20}")

def bar_window(card, wc):
  _, _, tlb, _, uc_off, wc_off, _ = ioctl(card.fd, 11, "QQIIQQQ", TLB_SIZE, 0, 0, 0, 0, 0, 0)
  card.windows.append(addr := map_memory(TLB_SIZE, card.fd, wc_off if wc else uc_off))
  return tlb, view_at(addr, TLB_SIZE)

def bar_write(card, tlb, win, core, base, data):
  mv = memoryview(data)
  for off in range(0, len(mv), TLB_SIZE):
    card._configure(tlb, core, base + off)
    n = min(TLB_SIZE, len(mv) - off)
    win[:n] = mv[off:off + n]
  card._configure(tlb, core, base)
  _ = win[0]                                         # a read flushes posted writes on the way

if __name__ == "__main__":
  mib = int(sys.argv[1]) if len(sys.argv) > 1 else 512
  size = mib << 20
  dev = Device(int(os.environ.get("CARD", 0)))
  try:
    print(f"{dev.card.name}: {len(dev.workers)} workers, {mib} MiB per test")
    data = os.urandom(size)

    pinned = dev.pinned(size); pinned.mem[:size] = data
    aligned = mmap.mmap(-1, size); aligned[:] = data
    junk = bytearray(256 << 20)                      # evict the fills from the CPU cache: device reads of lines still
    for name, src in (("Device.pinned() buffer", pinned.mem[:size]),   # in cache run ~30% slower
                      ("page-aligned buffer, pinned per call", aligned), ("bytes, staged", data)):
      junk[:] = bytes(len(junk))
      t = time.perf_counter(); addr = dev.allocator.upload(src); dt = time.perf_counter() - t
      check(dev, addr, data, name)
      print(f"A  copyin  from {name:36s} {gbs(size, dt)}")
    for name, dst in (("Device.pinned() buffer", pinned.mem[:size]), ("page-aligned buffer, pinned per call", aligned),
                      ("bytearray, staged", bytearray(size))):
      dst[:] = bytes(size)
      t = time.perf_counter(); dev.allocator.copyout(dst, addr); dt = time.perf_counter() - t
      assert bytes(dst) == data, f"copyout to {name} mismatch"
      print(f"A  copyout to   {name:36s} {gbs(size, dt)}")
    del junk, aligned

    src = HostMemory(dev.card, size)
    try:
      t = time.perf_counter(); src.mem[:] = data; memcpy = time.perf_counter() - t
      print(f"   (memcpy into pinned host memory alone          {gbs(size, memcpy)})")
      addr = dev.allocator.alloc(size)
      t = time.perf_counter()
      val = dev.dma_copy(addr, src.noc_addr, size)
      dev.timeline_signal.wait(val, 120); dt = time.perf_counter() - t
      check(dev, addr, data, "B")
      print(f"B  pinned sysmem -> DRAM, service core DMA only    {gbs(size, dt)}")

      bank0 = (17, 14)                               # DRAM bank 0, port 0 (fw/noc.c dram_ports)
      raw = 0x80000000                               # bank-local, above anything the allocator handed out here
      for wc, n in ((False, min(size, 16 << 20)), (True, size)):
        tlb, win = bar_window(dev.card, wc)
        t = time.perf_counter(); bar_write(dev.card, tlb, win, bank0, raw, data[:n]); dt = time.perf_counter() - t
        back = dev.card.read(bank0, raw + n - 4096, 4096)
        ok = back == data[n - 4096:n]
        print(f"C  host BAR stores, {'write-combined' if wc else 'uncached      '} ({n >> 20:4d} MiB)  {gbs(n, dt)}"
              f"{'' if ok else '  READBACK MISMATCH'}")

      image, pcs, _ = fw.build_worker([Path(__file__).with_name("upload.c")], ("brisc",), dev.dram_banks)
      dev.load(image, pcs)
      n = len(dev.workers)
      out, args = dev.alloc_host(n * 64), dev.alloc_host(64)
      host = dev.host.noc_addr + out
      for active in (1, 2, 4, 8, 16, 32, 64, n):
        for chunk in (64 << 10,):
          addr = dev.allocator.alloc(size)
          struct.pack_into("<10I", dev.host.mem, args, src.noc_addr & 0xFFFFFFFF, src.noc_addr >> 32,
                           addr & 0xFFFFFFFF, addr >> 32, size, chunk, active, 0, host & 0xFFFFFFFF, host >> 32)
          t = time.perf_counter(); dev.launch(dev.host.noc_addr + args, 64, sync=True, timeout=120); dt = time.perf_counter() - t
          recs = [struct.unpack_from("<2I", dev.host.mem, out + i * 64) for i in range(n)]
          assert sum(b for _, b in recs) == size, f"workers moved {sum(b for _, b in recs)} of {size} bytes"
          cyc = max(c for c, b in recs if b)
          check(dev, addr, data, f"D{active}")
          print(f"D  {active:3d} workers pull sysmem -> DRAM, {chunk >> 10} KiB chunks  {gbs(size, dt)} wall,"
                f" {gbs(size, cyc / (fw.AICLK_MHZ * 1e6))} on device")
    finally: src.close()
  finally: dev.close()
