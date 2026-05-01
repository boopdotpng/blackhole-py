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
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

import dsl
from dram import tilize
from emu.device import Device
from emu.memory import (
  BOOT_JAL,
  BRISC_FW_BASE,
  CB_CONFIG_BYTES,
  DATA_BUFFER_SPACE_BASE,
  GO_MESSAGES,
  KERNEL_CONFIG_BASE,
  LDM_BASE,
  NCRISC_FW_BASE,
  NCRISC_RESET_PC,
  NCRISC_RESET_PC_OVR,
  SOFT_RESET_0,
  SUBORDINATE_SYNC,
  TRISC0_FW_BASE,
  TRISC0_RESET_PC,
  TRISC1_FW_BASE,
  TRISC1_RESET_PC,
  TRISC2_FW_BASE,
  TRISC2_RESET_PC,
  TRISC_RESET_PC_OVR,
)
from emu.tensix.formats import bf16_to_fp32 as f32_from_bf16
from emu.tensix.formats import fp32_to_bf16 as bf16


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
  a.label("wait_go")
  a.emit(dsl.ADDI(dsl.t2, dsl.zero, RUN_MSG_GO))
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
