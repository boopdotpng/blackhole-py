"""Run the compiled O projection against an exact BF16 reference on a p150."""

import argparse
from pathlib import Path
import numpy as np
from ttrv import build
from ops_blackhole import BlackholeComputeQueue, BlackholeDevice


def bf16(a):
  return (np.asarray(a, dtype=np.float32).view(np.uint32) >> 16).astype("<u2")


def projection(dev, tiles):
  path = Path(__file__).parent / "docs/examples/llama3_o.ttrv"
  kernel = build(path.read_text(), {"EMBED_TILES": tiles}, str(path))
  program = kernel.install(dev)
  dim = 1024 * tiles
  ids = np.arange(dim)
  # Each row selects different lanes/faces in two tiles. Signed integer sums
  # are exactly representable at both BF16 rounding boundaries.
  x = (ids * 13 % 31 - 15).astype(np.float32)
  w = np.zeros((dim, dim), np.float32)
  cols = (ids * 97 + 43) % dim
  w[ids, cols] = 2
  w[ids, (cols + dim // 2 + 31) % dim] = -1
  residual = (ids % 19 - 9).astype(np.float32)
  buffers = {}
  for name, data in (("context", x), ("matrix", w), ("residual", residual), ("output", np.zeros_like(x))):
    raw = bf16(data)
    buffers[name] = dev.allocator._alloc(raw.nbytes, 2048)
    dev.allocator._copyin(buffers[name], raw)
  args = dev.allocator.upload(kernel.arguments(buffers))
  for run in range(4):
    if run in (1, 2):
      x = -x
      dev.allocator._copyin(buffers["context"], bf16(x))
    if run == 2:
      rng = np.random.default_rng(42)
      x = rng.integers(-1, 2, dim).astype(np.float32)
      w = rng.integers(-1, 2, (dim, dim), dtype=np.int8).astype(np.float32)
      dev.allocator._copyin(buffers["context"], bf16(x))
      dev.allocator._copyin(buffers["matrix"], bf16(w))
    if run == 3:
      rng = np.random.default_rng(73)
      x = rng.integers(-16, 17, dim).astype(np.float32) / 16
      w = rng.integers(-16, 17, (dim, dim), dtype=np.int8).astype(np.float32) / 16
      dev.allocator._copyin(buffers["context"], bf16(x))
      dev.allocator._copyin(buffers["matrix"], bf16(w))
    BlackholeComputeQueue().exec(program, args).signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
    dev.synchronize()
    actual = np.empty(dim, "<u2")
    dev.allocator._copyout(actual, buffers["output"])
    expected = bf16(2 * x[cols] - x[(cols + dim // 2 + 31) % dim] + residual)
    if run == 2:
      expected = bf16(w @ x + residual)
    if run == 3:
      # First pack truncates FP32 to BF16. The FP16b ALU adds the residual.
      dot = (bf16(w @ x).astype(np.uint32) << 16).view(np.float32)
      # ELWADD aligns both significands to the larger exponent and rounds
      # the shifted operand to 11 significant bits before adding (ttsim elwadd).
      _, exponent = np.frexp(np.maximum(np.abs(dot), np.abs(residual)))
      quantum = np.ldexp(np.ones_like(dot), exponent - 11)

      def aligned(v):
        return np.copysign(np.floor(np.abs(v) / quantum + 0.5) * quantum, v)

      bits = (aligned(dot) + aligned(residual)).view(np.uint32)
      expected = ((bits + 32768) >> 16).astype("<u2")
    np.testing.assert_array_equal(actual, expected)
    print(f"{dim} rows, launch {run + 1}: exact", flush=True)


def paged_transfer(dev):
  # Exercise both parts of the packed DRAM binding: a base above 4 GiB
  # and a first page on bank one. The transfer crosses the bank wrap.
  dev.allocator.dram_top = max(dev.allocator.dram_top, 1 << 32)
  for page in (576, 1088, 6144):
    data = np.arange(page * 10 // 2, dtype="<u2")
    src = dev.allocator._alloc(page + data.nbytes, page) + page
    dev.allocator._copyin(src, data)
    got = np.empty_like(data)
    if page == 6144:
      kernel = build(f"""grid 1
param source: bf16[], page=3
param target: bf16[], page=3
l1 staging: bf16[{data.size}]
fn ncrisc() {{
  noc.read staging, source[0], n={data.size}, wait
  noc.write target[0], staging, n={data.size}, wait
}}""")
      target = dev.allocator._alloc(page + data.nbytes, page) + page
      program = kernel.install(dev)
      args = dev.allocator.upload(kernel.arguments(dict(source=src, target=target)))
      BlackholeComputeQueue().exec(program, args).signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
      dev.synchronize()
      src = target
    dev.allocator._copyout(got, src)
    np.testing.assert_array_equal(got, data)
  print("irregular DRAM pages above 4 GiB: exact", flush=True)


def device_protocols(dev):
  source = """grid 2
l1 payload: u32[16]
l1 inbox: u32[16]
l1 arrived: u32[4]
l1 response: u32[4]
fn compute(a: u32, b: u32) { return a+b, a*b }
fn brisc() {
  if core.id == 0 {
    sum, product = compute(20, 11)
    payload[0] = sum + product
    noc.mcast rect(0,1,0,1,inbox), payload, n=16, wait
    noc.inc remote(0,1,arrived), by=7, ret=response, wait
  }
}
"""
  kernel = build(source)
  program = kernel.install(dev)
  storage = kernel.manifest["storage"]
  for item in storage.values():
    for core in dev.workers[:2]:
      dev.iface.write(core, item["address"], bytes(item["size"]))
  BlackholeComputeQueue().exec(program).signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
  dev.synchronize()
  core = dev.workers[1]
  assert dev.iface.read32(core, storage["inbox"]["address"]) == 251
  assert dev.iface.read32(core, storage["arrived"]["address"]) == 7
  print("multicast and remote atomic: exact", flush=True)


def persistent_storage(dev):
  kernel = build("""grid 3
l1 visits: u32[2], keep
fn brisc() {
  visits[0] += 1
  visits[1] = core.id + core.x * 100 + core.y * 1000
}""")
  first, second = kernel.install(dev), kernel.install(dev)
  queue = BlackholeComputeQueue()
  for program in (first, second, first):
    queue.exec(program)
  queue.signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
  dev.synchronize()
  for program, count in ((first, 2), (second, 1)):
    base = program.manifest["storage"]["visits"]["address"]
    for i, core in enumerate(dev.workers[:3]):
      assert dev.iface.read32(core, base) == count
      assert dev.iface.read32(core, base + 4) == 1001 * i
  print("persistent L1 and worker coordinates: exact", flush=True)


def block_formats(dev):
  for fmt, code in (("bfp8", 0x40), ("bfp4", 0x44), ("e4m3", 0x38)):
    for n in (128, 1024):
      source = f"""grid 1
l1 out: {fmt}[{n}]
fn trisc1() {{
  math.fmt dst=fp32
  sfp.li l1, 1.0
  repeat i in 0..32 {{ sfp.store dst[i*2], l1, fmt=fp32; sfp.nop }}
  tensix.stall sync, math|sfpu
  sem.inc math_pack
}}
fn trisc2() {{
  pack.fmt in={"fp16" if fmt == "e4m3" else "fp32"}, out={fmt}
  sem.stall tdma|pack|sync, math_pack, nonzero
  pack.move out, dst[0], n={n}
  tensix.stall sync, pack0
  tensix.wait
}}"""
      kernel = build(source)
      program = kernel.install(dev)
      BlackholeComputeQueue().exec(program).signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
      dev.synchronize()
      item = kernel.manifest["storage"]["out"]
      got = dev.iface.read(dev.workers[0], item["address"], item["size"])
      exps = bytes([127]) * (n // 16) if fmt.startswith("bfp") else b""
      mantissa = got[(len(exps) + 15) & -16 :]
      assert got[: len(exps)] == exps and mantissa == bytes([code]) * len(mantissa), (
        fmt,
        n,
        got[:20].hex(),
        mantissa[:32].hex(),
      )
    print(f"{fmt} pack: exact", flush=True)


def gather_macro(dev):
  source = """grid 1
l1 out: fp32[32]
sfpmacro twice, slot=0 {
  mad: sfp.mul x, l6, x, delay=0
  store: sfp.store dst[x], x, fmt=fp32, delay=2
}
fn trisc1() {
  math.fmt dst=fp32
  sfp.li l6, 2.0
  sfpmacro.load twice
  sfp.li l1, 3.0
  repeat i in 0..4 { sfp.store dst[i*2], l1, fmt=fp32; sfp.nop }
  repeat i in 0..4 { sfpmacro.run twice, l0, dst[i*2], fmt=fp32; repeat 4 { sfp.nop } }
  tensix.stall sync, math|sfpu
  sem.inc math_pack
}
fn trisc2() {
  pack.fmt in=fp32, out=fp32
  sem.stall tdma|pack|sync, math_pack, nonzero
  pack.gather out+1, dst[0,3], n=3, step=2
  tensix.stall sync, pack0
  tensix.wait
}
"""
  kernel = build(source)
  program = kernel.install(dev)
  BlackholeComputeQueue().exec(program).signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
  dev.synchronize()
  raw = dev.iface.read(dev.workers[0], kernel.manifest["storage"]["out"]["address"], 16)
  np.testing.assert_array_equal(np.frombuffer(raw, "<f4"), [0, 6, 6, 6])
  print("SFPMACRO multiply/store and unaligned pack.gather: exact", flush=True)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--device", type=int, default=0)
  parser.add_argument("--tiles", type=int, nargs="+", default=[2, 4])
  args = parser.parse_args()
  dev = BlackholeDevice(f"BLACKHOLE:{args.device}")
  try:
    persistent_storage(dev)
    paged_transfer(dev)
    device_protocols(dev)
    gather_macro(dev)
    block_formats(dev)
    for tiles in args.tiles:
      projection(dev, tiles)
  finally:
    dev.close()
