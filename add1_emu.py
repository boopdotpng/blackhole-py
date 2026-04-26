#!/usr/bin/env python3
"""Scratch emulator-native dispatch harness.

This uses tiny scratch RV32 firmware built with dsl.py to launch the raw
P100A add1 dataflow and compute kernels from firmware/disasms:

* BRISC polls the emulator mailbox GO byte.
* BRISC wakes NCRISC/TRISC0/TRISC1/TRISC2 through SUBORDINATE_SYNC.
* All five cores call fixed kernel entry points.
* Subordinates clear their sync byte when their kernel returns.
* BRISC waits for all sync bytes to clear, then writes RUN_MSG_DONE.

This intentionally bypasses the real firmware upload/init path: it loads raw
PT_LOAD/bin segments directly into emulated L1/LDM, then jumps into the real
kernel entry points.  CORES controls how many emulated Tensix cores to create;
the scratch workload is fixed at 10 tensor tiles.
"""

import json
import os
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

import dsl
from dram import tilize
from emu.device import Device
from emu.device import _build_bank_noc_table
from emu.memory import (
  BANK_TO_NOC_SCRATCH,
  BOOT_JAL,
  BRISC_FW_BASE,
  CB_CONFIG_BYTES,
  DATA_BUFFER_SPACE_BASE,
  GO_MESSAGE_INDEX,
  GO_MESSAGES,
  KERNEL_CONFIG_BASE,
  LDM_BASE,
  NCRISC_FW_BASE,
  NCRISC_RESET_PC,
  NCRISC_RESET_PC_OVR,
  SOFT_RESET_0,
  STREAM_STRIDE,
  STREAM_TILES_ACKED,
  STREAM_TILES_RECEIVED,
  SUBORDINATE_SYNC,
  TRISC0_FW_BASE,
  TRISC0_RESET_PC,
  TRISC1_FW_BASE,
  TRISC1_RESET_PC,
  TRISC2_FW_BASE,
  TRISC2_RESET_PC,
  TRISC_RESET_PC_OVR,
  cb_tiles_acked_addr,
  cb_tiles_received_addr,
)


SOFT_RESET_RELEASE_ALL = 0
TILE_BYTES = 32 * 32 * 2
DRAM_WRITE_OFFSET = 0x40
DRAM_ALIGNMENT = 64

RAW_TRISC_KERNEL_BASES = {
  "trisc0": 0x000070B0,
  "trisc1": 0x0000750C,
  "trisc2": 0x000083C8,
}
RAW_TRISC2_FW_BASE = 0x00009500
HARVESTED_DRAM_BANKS = [3]
DEFAULT_TENSOR_TILES = 10
MAX_RUN_STEPS = 100_000
INPUT_PATTERN = "ordered"
STATE_DUMP_PATH = "state.txt"
RUN_MSG_GO = 0x80
RUN_MSG_DONE = 0x00
DRAM_BANK_PORT = [[2, 1], [0, 1], [0, 1], [0, 1],
                  [2, 1], [2, 1], [2, 1], [2, 1]]


def _make_jal(target: int) -> bytes:
  return ((target & 0xFF000)
          | ((target & 0x800) << 9)
          | ((target & 0x7FE) << 20)
          | 0x6F).to_bytes(4, "little")

# Relocated raw add1 dataflow kernels.  PT_LOAD segments stay in
# firmware/disasms; the scratch harness only chooses their L1 load addresses.
RAW_DM_BRISC_KERNEL_BASE  = 0x00009600
RAW_DM_NCRISC_KERNEL_BASE = 0x00009C00
CB0_NUM_PAGES  = 2
CB16_NUM_PAGES = 2
CB0_BASE_L1    = DATA_BUFFER_SPACE_BASE
CB16_BASE_L1   = DATA_BUFFER_SPACE_BASE + TILE_BYTES * CB0_NUM_PAGES

BRISC_RTA_BASE = KERNEL_CONFIG_BASE + 0x000
NCRISC_RTA_BASE = KERNEL_CONFIG_BASE + 0x040
TRISC_RTA_BASE = KERNEL_CONFIG_BASE + 0x080
CB_CONFIG_BASE = KERNEL_CONFIG_BASE + 0x100

DISASMS = ROOT / "firmware" / "disasms"
TRISC_STACK_TOP = LDM_BASE + 0x0FF0
DM_STACK_TOP = LDM_BASE + 0x1FF0
TRISC0_CB_INTERFACE = 0x20
TRISC2_CB_INTERFACE = 0x20
RAW_DF_BRISC_TEXT_VADDR = 0x5460
RAW_DF_BRISC_KERNEL_MAIN = 0x5688
RAW_DF_NCRISC_TEXT_VADDR = 0x6170
RAW_DF_NCRISC_KERNEL_MAIN = 0x63CC
RAW_DF_BRISC_CB_INTERFACE_LDM = 0x488
RAW_DF_BRISC_DRAM_NOC_XY_LDM = 0x060
RAW_DF_BRISC_DRAM_OFFSET_LDM = 0x25C
RAW_DF_NCRISC_CB_INTERFACE_LDM = 0x46C
RAW_DF_NCRISC_DRAM_NOC_XY_LDM = 0x044
RAW_DF_NCRISC_DRAM_OFFSET_LDM = 0x240


def align_up(value: int, align: int = DRAM_ALIGNMENT) -> int:
  return (value + align - 1) // align * align


def bf16(x: float) -> int:
  return struct.unpack("<I", struct.pack("<f", x))[0] >> 16


def f32_from_bf16(x: int) -> float:
  return struct.unpack("<f", struct.pack("<I", (x & 0xFFFF) << 16))[0]


@dataclass
class ScratchDramBuffer:
  name: str
  addr: int
  num_tiles: int
  page_size: int = TILE_BYTES

  @property
  def size(self) -> int:
    return self.num_tiles * self.page_size


class ScratchDramAllocator:
  """Interleaved DRAM allocator matching dram.Allocator's page striping."""

  def __init__(self, dev: Device):
    self.dram = dev.dram
    self.next = DRAM_WRITE_OFFSET

  def alloc(self, num_tiles: int, name: str = "") -> ScratchDramBuffer:
    pages_per_bank = (num_tiles + self.dram.num_banks - 1) // self.dram.num_banks
    addr = self.next
    self.next = align_up(addr + pages_per_bank * TILE_BYTES)
    return ScratchDramBuffer(name=name, addr=addr, num_tiles=num_tiles)

  def alloc_write(self, data: bytes, name: str = "") -> ScratchDramBuffer:
    if len(data) % TILE_BYTES:
      raise ValueError(f"data length {len(data)} is not tile aligned")
    buf = self.alloc(len(data) // TILE_BYTES, name=name)
    self.write(buf, data)
    return buf

  def write(self, buf: ScratchDramBuffer, data: bytes):
    if len(data) > buf.size:
      raise ValueError(f"{buf.name}: data larger than buffer")
    for tile_id in range(buf.num_tiles):
      start = tile_id * buf.page_size
      chunk = data[start:start + buf.page_size]
      self.dram.write_interleaved(buf.addr, tile_id, buf.page_size, chunk)

  def read(self, buf: ScratchDramBuffer) -> bytes:
    return b"".join(
      self.dram.read_interleaved(buf.addr, tile_id, buf.page_size)
      for tile_id in range(buf.num_tiles)
    )

def pack_words(words: list[int]) -> bytes:
  return b"".join((word & 0xFFFFFFFF).to_bytes(4, "little") for word in words)


def write_rtas(tile, src: ScratchDramBuffer, dst: ScratchDramBuffer,
               tile_offset: int, num_tiles: int):
  tile.l1.load(BRISC_RTA_BASE, pack_words([src.addr, tile_offset, num_tiles]))
  tile.l1.load(NCRISC_RTA_BASE, pack_words([dst.addr, tile_offset, num_tiles]))
  tile.l1.load(TRISC_RTA_BASE, pack_words([num_tiles]))


def write_cb_config(tile):
  records = {
    0: (DATA_BUFFER_SPACE_BASE, TILE_BYTES * 2, 2, TILE_BYTES),
    16: (DATA_BUFFER_SPACE_BASE + TILE_BYTES * 2, TILE_BYTES * 2, 2, TILE_BYTES),
  }
  for idx, (addr, size, num_pages, page_size) in records.items():
    base = CB_CONFIG_BASE + idx * CB_CONFIG_BYTES
    tile.l1.write32(base + 0, addr)
    tile.l1.write32(base + 4, size)
    tile.l1.write32(base + 8, num_pages)
    tile.l1.write32(base + 12, page_size)


def seed_src_tensor(num_tiles: int, pattern: str = "fractional") -> bytes:
  words = []
  for i in range(num_tiles * 32 * 32):
    if pattern == "ordered":
      # Exact small integers make layout bugs obvious after add1:
      # expected output starts 1, 2, 3, ...
      words.append(bf16(float(i)))
    else:
      words.append(bf16((i % 251) / 251.0))
  return b"".join(x.to_bytes(2, "little") for x in words)


def expected_add1(src: bytes) -> bytes:
  out = bytearray(len(src))
  for i in range(0, len(src), 2):
    x = int.from_bytes(src[i:i + 2], "little")
    y = bf16(f32_from_bf16(x) + 1.0)
    out[i:i + 2] = y.to_bytes(2, "little")
  return bytes(out)


def compare_tile_prefixes(got: bytes, exp: bytes, num_tiles: int,
                          prefix_size: int) -> tuple[int, bytes, bytes] | None:
  for tile_id in range(num_tiles):
    base = tile_id * TILE_BYTES
    for off in range(prefix_size):
      idx = base + off
      if got[idx] != exp[idx]:
        start = max(base, idx - 16)
        end = min(base + prefix_size, idx + 48)
        return idx, got[start:end], exp[start:end]
  return None


def bf16_words(data: bytes, count: int = 16) -> list[int]:
  return [
    int.from_bytes(data[i:i + 2], "little")
    for i in range(0, min(len(data), count * 2), 2)
  ]


def format_bf16_words(data: bytes, count: int = 16) -> str:
  return " ".join(f"{word:04x}" for word in bf16_words(data, count))


def format_bf16_floats(data: bytes, count: int = 16) -> str:
  return " ".join(f"{f32_from_bf16(word):g}" for word in bf16_words(data, count))


def print_success_banner(dev: Device, num_tiles: int, core_count: int,
                         steps: int,
                         src: bytes, got: bytes):
  width = 68
  tile_bytes = num_tiles * TILE_BYTES
  harvested_text = ",".join(str(bank) for bank in HARVESTED_DRAM_BANKS) or "none"
  src_values = format_bf16_floats(src, 8)
  out_values = format_bf16_floats(got, 8)

  def border() -> str:
    return "+" + "-" * width + "+"

  def row(text: str = "") -> str:
    return f"| {text:<{width - 2}} |"

  lines = [
    border(),
    row("blackhole-py add1 raw-kernel emulation: pass"),
    border(),
    row("kernels : brisc + ncrisc + trisc0/1/2 raw disasms"),
    row(f"cores   : {core_count} tensix cores"),
    row(f"noc     : dram roundtrip across {dev.dram.num_banks} active banks"),
    row(f"harvest : dram bank(s) [{harvested_text}] excluded by bank table"),
    row(f"tensors : {num_tiles} tiles, {tile_bytes} bytes checked"),
    row(f"steps   : {steps} emulated device ticks"),
    row("layout  : host tilize -> cb -> sfpu/fpu -> pack -> dram"),
    row("verify  : full bf16 tile payload matched expected add1"),
    border(),
    row(f"bf16 input  first 8 : {src_values}"),
    row(f"bf16 output first 8 : {out_values}"),
    border(),
  ]
  print("\n".join(lines), flush=True)


def setup_add1_runtime(dev: Device, num_tiles: int,
                       input_pattern: str = "fractional"):
  alloc = ScratchDramAllocator(dev)
  src_rm = seed_src_tensor(num_tiles, input_pattern)
  src_data = tilize(src_rm, 2, (num_tiles, 32, 32))
  src = alloc.alloc_write(src_data, name="src")
  dst = alloc.alloc(num_tiles, name="dst")

  return alloc, src, dst, src_data, expected_add1(src_data)


def split_tile_work(num_tiles: int, core_count: int) -> list[tuple[int, int]]:
  base = num_tiles // core_count
  extra = num_tiles % core_count
  out = []
  offset = 0
  for core_idx in range(core_count):
    count = base + (1 if core_idx < extra else 0)
    out.append((offset, count))
    offset += count
  return out


def verify_runtime_setup(alloc: ScratchDramAllocator, src: ScratchDramBuffer,
                         src_data: bytes):
  got = alloc.read(src)
  if got != src_data:
    raise AssertionError("interleaved DRAM source readback mismatch")


def verify_tile_runtime(tile, src: ScratchDramBuffer, dst: ScratchDramBuffer,
                        tile_offset: int, num_tiles: int):
  expected_rtas = {
    BRISC_RTA_BASE: [src.addr, tile_offset, num_tiles],
    NCRISC_RTA_BASE: [dst.addr, tile_offset, num_tiles],
    TRISC_RTA_BASE: [num_tiles],
  }
  for base, words in expected_rtas.items():
    for i, word in enumerate(words):
      got = tile.l1.read32(base + i * 4)
      if got != word:
        raise AssertionError(
          f"RTA mismatch at 0x{base + i * 4:x}: expected 0x{word:x}, got 0x{got:x}")

  cb0 = [
    DATA_BUFFER_SPACE_BASE,
    TILE_BYTES * 2,
    2,
    TILE_BYTES,
  ]
  cb16 = [
    DATA_BUFFER_SPACE_BASE + TILE_BYTES * 2,
    TILE_BYTES * 2,
    2,
    TILE_BYTES,
  ]
  for idx, words in ((0, cb0), (16, cb16)):
    base = CB_CONFIG_BASE + idx * CB_CONFIG_BYTES
    for i, word in enumerate(words):
      got = tile.l1.read32(base + i * 4)
      if got != word:
        raise AssertionError(
          f"CB{idx} mismatch at 0x{base + i * 4:x}: expected 0x{word:x}, got 0x{got:x}")


def dram_noc_xy(dev: Device, bank_idx: int, noc_id: int = 0) -> int:
  active_banks = sorted(dev.bank_xy)
  bank_id = active_banks[bank_idx]
  x, y0 = dev.bank_xy[bank_id]
  return ((y0 + DRAM_BANK_PORT[bank_id][noc_id]) << 6) | x


def load_raw_kernel_segments(tile, role: str):
  stem = f"add1_compute_{role}.kernel"
  manifest = json.loads((DISASMS / f"{stem}.seg.json").read_text())
  core = getattr(tile, role)
  for seg in manifest["segments"]:
    data = (DISASMS / seg["bin"]).read_bytes()
    memsz = int(seg["memsz"])
    if len(data) < memsz:
      data += b"\0" * (memsz - len(data))

    vaddr = int(seg["vaddr"], 16)
    paddr = int(seg["paddr"], 16)
    if LDM_BASE <= vaddr < LDM_BASE + core.LDM_SIZE:
      core.ldm.load(vaddr - LDM_BASE, data)
    else:
      tile.l1.load(paddr, data)


def write_trisc_cb_interface(core, cb: int, addr: int, size: int,
                             num_pages: int, page_size: int,
                             tiles_received: int = 0):
  base = TRISC0_CB_INTERFACE + cb * 32
  addr16 = addr >> 4
  size16 = size >> 4
  page16 = page_size >> 4
  tiles_init = (tiles_received & 0xFFFF) << 16
  fields = [
    size16,
    addr16 + size16,
    page16,
    num_pages,
    addr16,
    addr16,
    tiles_init,
    0,
  ]
  for i, word in enumerate(fields):
    core.ldm.write32(base + i * 4, word)


def patch_raw_compute_ldm(tile, num_tiles: int):
  for core in (tile.trisc0, tile.trisc2):
    core.ldm.write32(0x08, CB_CONFIG_BASE)
    core.ldm.write32(0x10, KERNEL_CONFIG_BASE)
    core.ldm.write32(0x14, TRISC_RTA_BASE)
    core.ldm.write32(0x1C, 0)
  tile.trisc1.ldm.write32(0x0C, KERNEL_CONFIG_BASE)
  tile.trisc1.ldm.write32(0x10, TRISC_RTA_BASE)
  tile.trisc1.ldm.write32(0x18, 0)

  cb_size = TILE_BYTES * 2
  write_trisc_cb_interface(
    tile.trisc0, 0, DATA_BUFFER_SPACE_BASE, cb_size, 2, TILE_BYTES,
    tiles_received=0,
  )
  write_trisc_cb_interface(
    tile.trisc2, 16, DATA_BUFFER_SPACE_BASE + cb_size, cb_size, 2, TILE_BYTES,
  )


def raw_kernel_main_base(role: str) -> int:
  if role == "brisc":
    return RAW_DM_BRISC_KERNEL_BASE + (
      RAW_DF_BRISC_KERNEL_MAIN - RAW_DF_BRISC_TEXT_VADDR)
  if role == "ncrisc":
    return RAW_DM_NCRISC_KERNEL_BASE + (
      RAW_DF_NCRISC_KERNEL_MAIN - RAW_DF_NCRISC_TEXT_VADDR)
  raise ValueError(f"unsupported raw dataflow role {role!r}")


def load_raw_dataflow_kernel_text(tile):
  for role, stem, base in (
      ("brisc", "add1_reader_brisc.kernel", RAW_DM_BRISC_KERNEL_BASE),
      ("ncrisc", "add1_writer_ncrisc.kernel", RAW_DM_NCRISC_KERNEL_BASE),
  ):
    manifest = json.loads((DISASMS / f"{stem}.seg.json").read_text())
    rx_segments = [seg for seg in manifest["segments"] if "X" in seg["perms"]]
    if len(rx_segments) != 1:
      raise AssertionError(f"{role}: expected one RX segment, got {rx_segments}")
    seg = rx_segments[0]
    data = (DISASMS / seg["bin"]).read_bytes()
    memsz = int(seg["memsz"])
    if len(data) < memsz:
      data += b"\0" * (memsz - len(data))
    tile.l1.load(base, data)


def write_dm_cb_interface_to_ldm(core, base: int, cb: int, addr: int,
                                 size: int, num_pages: int, page_size: int):
  dst = base + cb * 32
  # Dataflow kernels keep CB pointers in byte addresses.  This is distinct
  # from the raw TRISC cb_interface scratch below, which uses 16-byte units.
  fields = [
    size,
    addr + size,
    page_size,
    num_pages,
    addr,
    addr,
    0,
    0,
  ]
  for i, word in enumerate(fields):
    core.ldm.write32(dst + i * 4, word)


def seed_raw_dataflow_ldm(dev: Device, tile):
  num_banks = dev.dram.num_banks
  # BRISC reader globals from the disasm's LDM addresses.
  tile.brisc.ldm.write32(0x10, BRISC_RTA_BASE)
  write_dm_cb_interface_to_ldm(
    tile.brisc, RAW_DF_BRISC_CB_INTERFACE_LDM, 0, CB0_BASE_L1,
    TILE_BYTES * CB0_NUM_PAGES,
    CB0_NUM_PAGES, TILE_BYTES)

  # NCRISC writer globals from the disasm's LDM addresses.
  tile.ncrisc.ldm.write32(0x34, NCRISC_RTA_BASE)
  write_dm_cb_interface_to_ldm(
    tile.ncrisc, RAW_DF_NCRISC_CB_INTERFACE_LDM, 16, CB16_BASE_L1,
    TILE_BYTES * CB16_NUM_PAGES,
    CB16_NUM_PAGES, TILE_BYTES)

  for bank_idx in range(num_banks):
    tile.brisc.ldm.write16(RAW_DF_BRISC_DRAM_NOC_XY_LDM + bank_idx * 2,
                           dram_noc_xy(dev, bank_idx, noc_id=0))
    tile.brisc.ldm.write32(RAW_DF_BRISC_DRAM_OFFSET_LDM + bank_idx * 4, 0)
    tile.ncrisc.ldm.write16(
      RAW_DF_NCRISC_DRAM_NOC_XY_LDM + (num_banks + bank_idx) * 2,
      dram_noc_xy(dev, bank_idx, noc_id=1))
    tile.ncrisc.ldm.write32(RAW_DF_NCRISC_DRAM_OFFSET_LDM + bank_idx * 4, 0)


def load_raw_dataflow_kernels(dev: Device, tile):
  load_raw_dataflow_kernel_text(tile)
  seed_raw_dataflow_ldm(dev, tile)


def upload_bank_noc_table(dev: Device, tile):
  tile.l1.load(
    BANK_TO_NOC_SCRATCH,
    _build_bank_noc_table(dev.harvested_banks, dev.core_xy),
  )


def load_raw_compute_kernels(tile, num_tiles: int):
  for role in ("trisc0", "trisc1", "trisc2"):
    load_raw_kernel_segments(tile, role)
  patch_raw_compute_ldm(tile, num_tiles)


def tensix_idle(tile) -> bool:
  for thread_id, thread in enumerate(tile.tensix.threads):
    if len(thread.fifo) or thread.held is not None:
      return False
    if thread.frontend_busy_until > tile.tensix.cycle:
      return False
    if not tile.tensix.thread_coprocessor_idle(thread_id):
      return False
  return True


def step_loop(dev: Device, tiles: list, done_check, max_steps: int):
  start = dev.elapsed_cycles
  for _ in range(max_steps):
    dev.run(1)
    if done_check():
      return dev.elapsed_cycles - start
  raise TimeoutError(
    f"emulated device did not complete within {max_steps} cycles "
    f"(elapsed={dev.elapsed_cycles}, sim={dev.sim_cycle})\n"
    + timeout_diagnostics(tiles)
  )


def timeout_diagnostics(tiles: list) -> str:
  lines = ["timeout diagnostics:"]
  for tile in tiles:
    sync = tile.l1.read32(SUBORDINATE_SYNC)
    go = tile.l1.read8(GO_MESSAGES + 3)
    lines.append(
      f"  tile ({tile.x},{tile.y}): go=0x{go:02x} sync=0x{sync:08x}")
    for name in ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2"):
      core = getattr(tile, name)
      try:
        word = core.mem.read32(core.pc)
      except Exception as e:
        word = f"{type(e).__name__}:{e}"
      lines.append(
        f"    {name:<6} reset={int(core.in_reset)} "
        f"cycles={core.cycles} blocked={core.blocked_cycles} "
        f"pc=0x{core.pc:08x} word={word if isinstance(word, str) else f'0x{word:08x}'} "
        f"ra=0x{core.regs[1]:08x} sp=0x{core.regs[2]:08x}")
    for thread_id, thread in enumerate(tile.tensix.threads):
      lines.append(
        f"    tensix t{thread_id}: fifo={len(thread.fifo)} "
        f"held={thread.held.name if thread.held else '-'} "
        f"frontend_busy_until={thread.frontend_busy_until} "
        f"inflight={tile.tensix._backend_inflight[thread_id]}")
  return "\n".join(lines)


RV_REG_NAMES = [
  "zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
  "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
  "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
  "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6",
]


def _mem_bytes(mem, addr: int, size: int) -> bytes:
  return bytes(mem.read8(addr + i) for i in range(size))


def _hex_words(mem, addr: int, count: int) -> str:
  return " ".join(f"{mem.read32(addr + i * 4):08x}" for i in range(count))


def _coalesced_sparse_ranges(mem):
  data = getattr(mem, "_data", {})
  if not data:
    return []
  addrs = sorted(data)
  ranges = []
  start = prev = addrs[0]
  for addr in addrs[1:]:
    if addr == prev + 1:
      prev = addr
      continue
    ranges.append((start, prev))
    start = prev = addr
  ranges.append((start, prev))
  return ranges


def _dump_sparse_memory(lines: list[str], name: str, mem, bytes_per_line: int = 32):
  ranges = _coalesced_sparse_ranges(mem)
  lines.append(f"{name}: sparse_ranges={len(ranges)}")
  for start, end in ranges:
    size = end - start + 1
    lines.append(f"  range 0x{start:08x}..0x{end:08x} ({size} bytes)")
    for addr in range(start, end + 1, bytes_per_line):
      chunk_end = min(addr + bytes_per_line - 1, end)
      chunk = _mem_bytes(mem, addr, chunk_end - addr + 1)
      lines.append(f"    0x{addr:08x}: {chunk.hex()}")


def _word_desc(core, pc: int) -> str:
  try:
    word = core.mem.read32(pc)
  except Exception as e:
    return f"{type(e).__name__}: {e}"
  try:
    decoded = dsl.decode_rv(word)
    return f"0x{word:08x} {decoded.name}"
  except Exception:
    if (word & 0x3) != 0x3:
      return f"0x{word:08x} TT_PUSH"
    return f"0x{word:08x}"


def _pc_region(name: str, pc: int) -> str:
  fw_ranges = {
    "brisc": (BRISC_FW_BASE, BRISC_FW_BASE + 0x600),
    "ncrisc": (NCRISC_FW_BASE, NCRISC_FW_BASE + 0x600),
    "trisc0": (TRISC0_FW_BASE, TRISC0_FW_BASE + 0x600),
    "trisc1": (TRISC1_FW_BASE, TRISC1_FW_BASE + 0x600),
    "trisc2": (RAW_TRISC2_FW_BASE, RAW_TRISC2_FW_BASE + 0x600),
  }
  kernel_ranges = {
    "brisc": (RAW_DM_BRISC_KERNEL_BASE, RAW_DM_BRISC_KERNEL_BASE + 0x900),
    "ncrisc": (RAW_DM_NCRISC_KERNEL_BASE, RAW_DM_NCRISC_KERNEL_BASE + 0x900),
    "trisc0": (0x00006990, 0x00007200),
    "trisc1": (0x00007210, 0x00007680),
    "trisc2": (0x00007C30, 0x00008480),
  }
  lo, hi = fw_ranges.get(name, (0, 0))
  if lo <= pc < hi:
    return f"scratch_fw+0x{pc - lo:x}"
  lo, hi = kernel_ranges.get(name, (0, 0))
  if lo <= pc < hi:
    return f"raw_kernel+0x{pc - lo:x}"
  return "unknown"


def _dump_core(lines: list[str], tile, name: str):
  core = getattr(tile, name)
  lines.append(
    f"  {name}: reset={int(core.in_reset)} cycles={core.cycles} "
    f"blocked={core.blocked_cycles} pc=0x{core.pc:08x} "
    f"region={_pc_region(name, core.pc)} instr={_word_desc(core, core.pc)}"
  )
  pending = getattr(core, "_pending", None)
  if pending is not None:
    pname = pending.decoded.name if pending.decoded is not None else "TT_PUSH"
    lines.append(
      f"    pending pc=0x{pending.pc:08x} word=0x{pending.word:08x} "
      f"name={pname} latency={pending.latency}"
    )
  lines.append(
    "    regs "
    + " ".join(f"{reg}=0x{core.regs[i]:08x}"
               for i, reg in enumerate(RV_REG_NAMES))
  )
  if core.csrs:
    lines.append(
      "    csrs "
      + " ".join(f"0x{k:x}=0x{v:08x}" for k, v in sorted(core.csrs.items()))
    )
  _dump_sparse_memory(lines, f"    {name}.ldm", core.ldm)


def _dump_stream_counters(lines: list[str], tile):
  lines.append("  stream counters:")
  for cb in (0, 16):
    stream = cb * STREAM_STRIDE
    recv = tile.stream_regs.read32(stream + STREAM_TILES_RECEIVED)
    ack = tile.stream_regs.read32(stream + STREAM_TILES_ACKED)
    bus_recv = tile.brisc.mem.read32(cb_tiles_received_addr(cb))
    bus_ack = tile.brisc.mem.read32(cb_tiles_acked_addr(cb))
    lines.append(
      f"    cb{cb}: stream_recv={recv} stream_ack={ack} "
      f"bus_recv={bus_recv} bus_ack={bus_ack}"
    )


def _dump_tensix(lines: list[str], tile):
  tensix = tile.tensix
  lines.append("  tensix:")
  lines.append(f"    cycle={tensix.cycle} backend_inflight={tensix._backend_inflight}")
  for thread in tensix.threads:
    fifo_words = [f"0x{insn.word:08x}:{insn.name}" for insn in list(thread.fifo._q)[:16]]
    lines.append(
      f"    thread{thread.thread_id}: fifo={len(thread.fifo)} "
      f"held={thread.held.name if thread.held else '-'} "
      f"frontend_busy_until={thread.frontend_busy_until} "
      f"mop_mask_hi=0x{thread.mop_mask_hi:04x} fifo_head={fifo_words}"
    )
  for tid in range(3):
    nonzero = [
      f"r{i}=0x{tensix.gpr.read32(tid, i):08x}"
      for i in range(64) if tensix.gpr.read32(tid, i)
    ]
    lines.append(f"    gpr t{tid}: {' '.join(nonzero) if nonzero else '-'}")
  for state_id, cfg in enumerate(tensix.config_unit.cfg):
    nonzero = [f"{i}=0x{v:08x}" for i, v in enumerate(cfg) if v]
    lines.append(f"    cfg state{state_id}: {' '.join(nonzero) if nonzero else '-'}")
  for tid, adc in enumerate(tensix.adc):
    chans = []
    for idx, ch in enumerate(adc.packers.channels):
      chans.append(
        f"ch{idx}(x={ch.x.val}/{ch.x.cr},y={ch.y.val}/{ch.y.cr},"
        f"z={ch.z.val}/{ch.z.cr},w={ch.w.val}/{ch.w.cr})"
      )
    lines.append(f"    adc packers t{tid}: {' '.join(chans)}")
    for unp_idx, unit in enumerate(adc.unpackers):
      chans = []
      for idx, ch in enumerate(unit.channels):
        chans.append(
          f"ch{idx}(x={ch.x.val}/{ch.x.cr},y={ch.y.val}/{ch.y.cr},"
          f"z={ch.z.val}/{ch.z.cr},w={ch.w.val}/{ch.w.cr})"
        )
      lines.append(f"    adc unpacker{unp_idx} t{tid}: {' '.join(chans)}")
  valid_rows = [i for i, valid in enumerate(tensix.dest.valid) if valid]
  nonzero_dest_rows = [
    i for i, row in enumerate(tensix.dest.bits) if any(row)
  ]
  lines.append(f"    dest valid_rows={valid_rows[:128]} count={len(valid_rows)}")
  lines.append(
    f"    dest nonzero_rows_head={nonzero_dest_rows[:128]} "
    f"count={len(nonzero_dest_rows)}"
  )
  for row in nonzero_dest_rows[:32]:
    lines.append(
      f"      dest[{row:04d}]: "
      + " ".join(f"{v:08x}" for v in tensix.dest.bits[row])
    )
  for src_name in ("srca", "srcb"):
    src = getattr(tensix, src_name)
    lines.append(
      f"    {src_name}: fpu_bank={src.fpu_bank} unpack_bank={src.unpack_bank}"
    )
    for bank_id, bank in enumerate(src.banks):
      rows = [i for i, row in enumerate(bank.rows) if any(row)]
      lines.append(
        f"      bank{bank_id}: allowed={bank.allowed_client} "
        f"nonzero_rows={rows[:64]} count={len(rows)}"
      )
      for row in rows[:16]:
        lines.append(
          f"        row[{row:02d}]: "
          + " ".join(f"{v:08x}" for v in bank.rows[row])
        )


def dump_emu_state(path: str, reason: str, dev: Device, tiles: list,
                   *, alloc: ScratchDramAllocator | None = None,
                   src: ScratchDramBuffer | None = None,
                   dst: ScratchDramBuffer | None = None,
                   got: bytes | None = None,
                   exp: bytes | None = None):
  lines = [
    f"reason: {reason}",
    f"elapsed_cycles: {dev.elapsed_cycles}",
    f"sim_cycle: {dev.sim_cycle}",
    f"core_xy: {dev.core_xy}",
    f"harvested_banks: {dev.harvested_banks}",
    "",
    timeout_diagnostics(tiles),
    "",
  ]
  if src is not None:
    lines.append(f"src buffer: addr=0x{src.addr:x} tiles={src.num_tiles} size={src.size}")
  if dst is not None:
    lines.append(f"dst buffer: addr=0x{dst.addr:x} tiles={dst.num_tiles} size={dst.size}")
  if got is not None:
    lines.append(f"got first64: {got[:64].hex()}")
    lines.append(f"got bf16 first32: {format_bf16_words(got, 32)}")
  if exp is not None:
    lines.append(f"expected first64: {exp[:64].hex()}")
    lines.append(f"expected bf16 first32: {format_bf16_words(exp, 32)}")
  lines.append("")
  for tile in tiles:
    lines.append(f"tile ({tile.x},{tile.y})")
    lines.append(
      f"  mailbox: go=0x{tile.l1.read8(GO_MESSAGES + 3):02x} "
      f"go_index=0x{tile.l1.read32(GO_MESSAGE_INDEX):08x} "
      f"sync=0x{tile.l1.read32(SUBORDINATE_SYNC):08x}"
    )
    lines.append(f"  rta words @0x{KERNEL_CONFIG_BASE:x}: {_hex_words(tile.l1, KERNEL_CONFIG_BASE, 36)}")
    for cb in (0, 16):
      base = CB_CONFIG_BASE + cb * CB_CONFIG_BYTES
      lines.append(f"  cb{cb} config @0x{base:x}: {_hex_words(tile.l1, base, 4)}")
    table_words = (dev.dram.num_banks * 2 + len(dev.core_xy) * 2 + 1) // 2
    lines.append(
      f"  bank_to_noc @0x{BANK_TO_NOC_SCRATCH:x}: "
      f"{_hex_words(tile.l1, BANK_TO_NOC_SCRATCH, table_words)}"
    )
    _dump_stream_counters(lines, tile)
    for name in ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2"):
      _dump_core(lines, tile, name)
    _dump_tensix(lines, tile)
    _dump_sparse_memory(lines, "  l1", tile.l1)
    _dump_sparse_memory(lines, "  mmio", tile.mmio)
    _dump_sparse_memory(lines, "  stream_regs", tile.stream_regs)
    _dump_sparse_memory(lines, "  noc0.regs", tile.noc0.regs)
    _dump_sparse_memory(lines, "  noc1.regs", tile.noc1.regs)
    lines.append("")
  for bank_id, bank in enumerate(dev.dram_banks):
    _dump_sparse_memory(lines, f"dram_bank{bank_id}", bank)
  Path(path).write_text("\n".join(lines) + "\n")


class Asm:
  def __init__(self, base: int):
    self.base = base
    self.items = []
    self.labels = {}

  def pc(self):
    return self.base + 4 * len(self.items)

  def label(self, name: str):
    self.labels[name] = self.pc()

  def emit(self, *insns):
    self.items.extend(insns)

  def li32(self, rd, imm):
    self.emit(*dsl.LI32(rd, imm))

  def bne_label(self, rs1, rs2, label: str):
    pc = self.pc()
    self.items.append(lambda labels: dsl.BNE(rs1, rs2, labels[label] - pc))

  def bnez_label(self, rs, label: str):
    pc = self.pc()
    self.items.append(lambda labels: dsl.BNE(rs, dsl.zero, labels[label] - pc))

  def beq_label(self, rs1, rs2, label: str):
    pc = self.pc()
    self.items.append(lambda labels: dsl.BEQ(rs1, rs2, labels[label] - pc))

  def bgeu_label(self, rs1, rs2, label: str):
    pc = self.pc()
    self.items.append(lambda labels: dsl.BGEU(rs1, rs2, labels[label] - pc))

  def bltu_label(self, rs1, rs2, label: str):
    pc = self.pc()
    self.items.append(lambda labels: dsl.BLTU(rs1, rs2, labels[label] - pc))

  def j_label(self, label: str):
    pc = self.pc()
    self.items.append(lambda labels: dsl.J(labels[label] - pc))

  def call_abs(self, addr: int):
    self.li32(dsl.t6, addr)
    self.emit(dsl.JALR(dsl.ra, dsl.t6, 0))

  def bytes(self):
    resolved = [item(self.labels) if callable(item) else item
                for item in self.items]
    return dsl.pack(resolved)


def build_brisc_fw(kernel_base: int) -> bytes:
  a = Asm(BRISC_FW_BASE)
  a.li32(dsl.sp, DM_STACK_TOP)
  a.label("loop")
  a.li32(dsl.t0, GO_MESSAGES + 3)
  a.label("wait_go")
  a.emit(dsl.LBU(dsl.t1, dsl.t0, 0))
  a.emit(dsl.ADDI(dsl.t2, dsl.zero, RUN_MSG_GO))
  a.bne_label(dsl.t1, dsl.t2, "wait_go")

  a.li32(dsl.t0, SUBORDINATE_SYNC)
  a.li32(dsl.t1, 0x80808080)
  a.emit(dsl.SW(dsl.t0, dsl.t1, 0))
  a.call_abs(kernel_base)

  a.li32(dsl.t0, SUBORDINATE_SYNC)
  a.label("wait_subordinates")
  a.emit(dsl.LW(dsl.t1, dsl.t0, 0))
  a.bnez_label(dsl.t1, "wait_subordinates")

  a.li32(dsl.t0, GO_MESSAGES + 3)
  a.emit(dsl.SB(dsl.t0, dsl.zero, 0))
  a.j_label("loop")
  return a.bytes()


def build_subordinate_fw(base: int, sync_offset: int, kernel_base: int,
                         stack_top: int) -> bytes:
  a = Asm(base)
  a.li32(dsl.sp, stack_top)
  a.li32(dsl.s0, SUBORDINATE_SYNC + sync_offset)
  a.emit(dsl.ADDI(dsl.t2, dsl.zero, RUN_MSG_GO))
  a.label("wait_go")
  a.emit(dsl.LBU(dsl.t1, dsl.s0, 0))
  a.bne_label(dsl.t1, dsl.t2, "wait_go")
  a.call_abs(kernel_base)
  a.li32(dsl.s0, SUBORDINATE_SYNC + sync_offset)
  a.emit(dsl.SB(dsl.s0, dsl.zero, 0))
  a.j_label("wait_go")
  return a.bytes()


def scratch_boot(tile, kernel_bases: dict[str, int],
                 fw_bases: dict[str, int] | None = None):
  if fw_bases is None:
    fw_bases = {}
  required = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
  missing = [role for role in required if role not in kernel_bases]
  if missing:
    raise ValueError(f"missing raw kernel base(s): {', '.join(missing)}")
  brisc_kernel = kernel_bases["brisc"]
  ncrisc_kernel = kernel_bases["ncrisc"]
  trisc0_kernel = kernel_bases["trisc0"]
  trisc1_kernel = kernel_bases["trisc1"]
  trisc2_kernel = kernel_bases["trisc2"]
  trisc2_fw = fw_bases.get("trisc2", TRISC2_FW_BASE)

  l1 = tile.l1
  mmio = tile.mmio

  l1.load(BOOT_JAL, _make_jal(BRISC_FW_BASE))
  l1.load(BRISC_FW_BASE, build_brisc_fw(brisc_kernel))
  l1.load(NCRISC_FW_BASE, build_subordinate_fw(
    NCRISC_FW_BASE, 0, ncrisc_kernel, DM_STACK_TOP))
  l1.load(TRISC0_FW_BASE, build_subordinate_fw(
    TRISC0_FW_BASE, 1, trisc0_kernel, TRISC_STACK_TOP))
  l1.load(TRISC1_FW_BASE, build_subordinate_fw(
    TRISC1_FW_BASE, 2, trisc1_kernel, TRISC_STACK_TOP))
  l1.load(trisc2_fw, build_subordinate_fw(
    trisc2_fw, 3, trisc2_kernel, TRISC_STACK_TOP))

  l1.write8(GO_MESSAGES + 3, RUN_MSG_DONE)
  l1.write32(SUBORDINATE_SYNC, 0)

  mmio.write32(NCRISC_RESET_PC, NCRISC_FW_BASE)
  mmio.write32(TRISC0_RESET_PC, TRISC0_FW_BASE)
  mmio.write32(TRISC1_RESET_PC, TRISC1_FW_BASE)
  mmio.write32(TRISC2_RESET_PC, trisc2_fw)
  mmio.write32(NCRISC_RESET_PC_OVR, 1)
  mmio.write32(TRISC_RESET_PC_OVR, 0b111)

  tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_RELEASE_ALL)
  return tile


def main():
  core_count = int(os.environ.get("CORES", "1"))
  num_tiles = DEFAULT_TENSOR_TILES
  dev = Device(
    harvested_banks=HARVESTED_DRAM_BANKS,
    core_count=core_count,
    boot_firmware=False,
  )
  tiles = list(dev.tiles.values())
  if num_tiles < len(tiles):
    print(
      f"FAIL: fixed tensor tile count {num_tiles} is smaller than CORES={len(tiles)}",
      file=sys.stderr,
    )
    return 1

  kernel_bases = {
    "brisc": raw_kernel_main_base("brisc"),
    "ncrisc": raw_kernel_main_base("ncrisc"),
    **RAW_TRISC_KERNEL_BASES,
  }
  fw_bases = {"trisc2": RAW_TRISC2_FW_BASE}
  alloc, src, dst, src_data, exp_data = setup_add1_runtime(
    dev, num_tiles, INPUT_PATTERN)
  verify_runtime_setup(alloc, src, src_data)
  work = split_tile_work(num_tiles, len(tiles))
  for tile, (tile_offset, tile_count) in zip(tiles, work, strict=True):
    scratch_boot(tile, kernel_bases=kernel_bases, fw_bases=fw_bases)
    upload_bank_noc_table(dev, tile)
    write_rtas(tile, src, dst, tile_offset=tile_offset, num_tiles=tile_count)
    write_cb_config(tile)
    verify_tile_runtime(tile, src, dst, tile_offset, tile_count)
    load_raw_dataflow_kernels(dev, tile)
    load_raw_compute_kernels(tile, tile_count)

  for tile in tiles:
    tile.l1.write8(GO_MESSAGES + 3, RUN_MSG_GO)
  try:
    steps = step_loop(
      dev,
      tiles,
      lambda: all(
        tile.l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE
        and tensix_idle(tile)
        for tile in tiles),
      MAX_RUN_STEPS,
    )
  except TimeoutError as e:
    state_path = os.environ.get("STATE_DUMP", STATE_DUMP_PATH)
    dump_emu_state(
      state_path,
      f"timeout after {MAX_RUN_STEPS} max steps",
      dev,
      tiles,
      alloc=alloc,
      src=src,
      dst=dst,
    )
    print(f"RUN TIMEOUT: {e}", file=sys.stderr, flush=True)
    print(f"EMU STATE DUMPED: {state_path}", file=sys.stderr, flush=True)
    return 1
  except Exception as e:
    state_path = os.environ.get("STATE_DUMP", STATE_DUMP_PATH)
    dump_emu_state(
      state_path,
      f"run error {type(e).__name__}: {e}",
      dev,
      tiles,
      alloc=alloc,
      src=src,
      dst=dst,
    )
    print(f"RUN ERROR: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    print(f"EMU STATE DUMPED: {state_path}", file=sys.stderr, flush=True)
    return 1

  for tile in tiles:
    sync = tile.l1.read32(SUBORDINATE_SYNC)
    if sync != 0:
      print(
        f"FAIL: tile ({tile.x},{tile.y}) subordinate sync is 0x{sync:08x}",
        file=sys.stderr,
      )
      return 1

  if len(exp_data) != dst.size:
    print("FAIL: expected output size mismatch", file=sys.stderr)
    return 1

  got = alloc.read(dst)
  exp = exp_data
  mismatch = compare_tile_prefixes(got, exp, num_tiles, TILE_BYTES)
  if mismatch is not None:
    idx, got_window, exp_window = mismatch
    state_path = os.environ.get("STATE_DUMP", STATE_DUMP_PATH)
    dump_emu_state(
      state_path,
      f"output mismatch at byte {idx}",
      dev,
      tiles,
      alloc=alloc,
      src=src,
      dst=dst,
      got=got,
      exp=exp,
    )
    print(
      "RAW OUTPUT DRAM MISMATCH: "
      f"byte={idx} got={got_window.hex()} expected={exp_window.hex()}",
      file=sys.stderr,
      flush=True,
    )
    print(f"  got bf16:      {format_bf16_words(got)}", file=sys.stderr)
    print(f"  expected bf16: {format_bf16_words(exp)}", file=sys.stderr)
    print(f"  got float:     {format_bf16_floats(got)}", file=sys.stderr)
    print(f"  expected float:{format_bf16_floats(exp)}", file=sys.stderr)
    print(f"EMU STATE DUMPED: {state_path}", file=sys.stderr, flush=True)
    return 1
  print_success_banner(dev, num_tiles, len(tiles), steps, src_data, got)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
