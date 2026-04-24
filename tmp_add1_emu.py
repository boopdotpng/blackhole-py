#!/usr/bin/env python3
"""Scratch emulator-native dispatch harness.

This intentionally avoids checked-in tt-metal firmware/kernel disasms.  The
firmware below is tiny RV32 code built with dsl.py:

* BRISC polls the emulator mailbox GO byte.
* BRISC wakes NCRISC/TRISC0/TRISC1/TRISC2 through SUBORDINATE_SYNC.
* All five cores call fixed kernel entry points.
* Subordinates clear their sync byte when their kernel returns.
* BRISC waits for all sync bytes to clear, then writes RUN_MSG_DONE.

The first scratch kernels are no-ops.  This gives us a stable, version-free
place to translate add1 objdump snippets into dsl.py instructions next.
"""

import argparse
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

import dsl
from emu.device import Device, RUN_MSG_DONE, RUN_MSG_GO, _make_jal
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
  cb_tiles_received_addr,
)


SOFT_RESET_RELEASE_ALL = 0
TILE_BYTES = 32 * 32 * 2
DRAM_WRITE_OFFSET = 0x40
DRAM_ALIGNMENT = 64

BRISC_KERNEL_BASE = 0x00009000
NCRISC_KERNEL_BASE = 0x00009100
TRISC0_KERNEL_BASE = 0x00009200
TRISC1_KERNEL_BASE = 0x00009300
TRISC2_KERNEL_BASE = 0x00009400

RAW_TRISC_KERNEL_BASES = {
  "trisc0": 0x000070B0,
  "trisc1": 0x0000750C,
  "trisc2": 0x000083C8,
}
RAW_TRISC2_FW_BASE = 0x00009500
FMT_BF16 = 5

BRISC_RTA_BASE = KERNEL_CONFIG_BASE + 0x000
NCRISC_RTA_BASE = KERNEL_CONFIG_BASE + 0x040
TRISC_RTA_BASE = KERNEL_CONFIG_BASE + 0x080
CB_CONFIG_BASE = KERNEL_CONFIG_BASE + 0x100

DISASMS = ROOT / "firmware" / "disasms"
TRISC_STACK_TOP = LDM_BASE + 0x0FF0
DM_STACK_TOP = LDM_BASE + 0x1FF0
TRISC0_CB_INTERFACE = 0x20
TRISC2_CB_INTERFACE = 0x20


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

  def bank_addr(self, buf: ScratchDramBuffer, tile_id: int) -> tuple[int, int]:
    bank = tile_id % self.dram.num_banks
    slot = tile_id // self.dram.num_banks
    return bank, buf.addr + slot * buf.page_size


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


def seed_src_tiles(num_tiles: int, pattern: str = "fractional") -> bytes:
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


def bf16_words(data: bytes, count: int = 16) -> list[int]:
  return [
    int.from_bytes(data[i:i + 2], "little")
    for i in range(0, min(len(data), count * 2), 2)
  ]


def format_bf16_words(data: bytes, count: int = 16) -> str:
  return " ".join(f"{word:04x}" for word in bf16_words(data, count))


def format_bf16_floats(data: bytes, count: int = 16) -> str:
  return " ".join(f"{f32_from_bf16(word):g}" for word in bf16_words(data, count))


def setup_add1_runtime(dev: Device, tile, num_tiles: int,
                       input_pattern: str = "fractional"):
  alloc = ScratchDramAllocator(dev)
  src_data = seed_src_tiles(num_tiles, input_pattern)
  src = alloc.alloc_write(src_data, name="src")
  dst = alloc.alloc(num_tiles, name="dst")

  write_rtas(tile, src, dst, tile_offset=0, num_tiles=num_tiles)
  write_cb_config(tile)

  return alloc, src, dst, src_data, expected_add1(src_data)


def verify_runtime_setup(alloc: ScratchDramAllocator, src: ScratchDramBuffer,
                         src_data: bytes):
  got = alloc.read(src)
  if got != src_data:
    raise AssertionError("interleaved DRAM source readback mismatch")


def verify_tile_runtime(tile, src: ScratchDramBuffer, dst: ScratchDramBuffer,
                        num_tiles: int):
  expected_rtas = {
    BRISC_RTA_BASE: [src.addr, 0, num_tiles],
    NCRISC_RTA_BASE: [dst.addr, 0, num_tiles],
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
    tiles_received=num_tiles,
  )
  write_trisc_cb_interface(
    tile.trisc2, 16, DATA_BUFFER_SPACE_BASE + cb_size, cb_size, 2, TILE_BYTES,
  )


def seed_raw_compute_l1(tile, src_data: bytes, num_tiles: int):
  pages = min(num_tiles, 2)
  for i in range(pages):
    start = i * TILE_BYTES
    tile.l1.load(DATA_BUFFER_SPACE_BASE + start,
                 src_data[start:start + TILE_BYTES])
  tile.trisc0.mem.write32(cb_tiles_received_addr(0), num_tiles)


def seed_raw_compute_tensix_config(tile):
  cfg = tile.tensix.config_unit.cfg[0]

  # SrcA unpacker: BF16 input tile, four 16x16 faces.  The unpacker model
  # applies the standard 16-byte tile-header skip, while our scratch CB stores
  # raw datums, so point REG3 one 16-byte word before CB0.
  cfg[64] = FMT_BF16 | (1 << 4) | (256 << 16)
  cfg[65] = 1 | (4 << 16)
  cfg[66] = 1
  cfg[72] = FMT_BF16
  cfg[76] = (DATA_BUFFER_SPACE_BASE >> 4) - 1
  cfg[49] = 128

  # Packer: BF16 Dest -> BF16 L1 output.  Raw TRISC2 writes the destination
  # address dynamically, but this scratch path has to provide the data formats.
  cfg[70] = (FMT_BF16 << 8) | (FMT_BF16 << 4)

  # Full-tile pack path: all columns enabled, all rows use edge mask 0.
  cfg[20] = 0xFFFF
  cfg[24] = 0


def load_raw_compute_kernels(tile, num_tiles: int, src_data: bytes):
  for role in ("trisc0", "trisc1", "trisc2"):
    load_raw_kernel_segments(tile, role)
  seed_raw_compute_tensix_config(tile)
  patch_raw_compute_ldm(tile, num_tiles)
  seed_raw_compute_l1(tile, src_data, num_tiles)


def read_l1(tile, addr: int, size: int) -> bytes:
  return bytes(tile.l1.read8(addr + i) for i in range(size))


def tensix_idle(tile) -> bool:
  for thread in tile.tensix.threads:
    if len(thread.fifo):
      return False
    if thread.mop.busy or thread.replay.busy:
      return False
    if thread._replay_word is not None:
      return False
  return True


def _cfg_word(tile, state_id: int, addr32: int) -> str:
  cfg = tile.tensix.config_unit.cfg
  if 0 <= state_id < len(cfg) and 0 <= addr32 < len(cfg[state_id]):
    return f"cfg{state_id}[{addr32}]=0x{cfg[state_id][addr32]:08x}"
  return f"cfg{state_id}[{addr32}]=<oob>"


def _t1_cfg_deps(tile, d, thread_id: int) -> str:
  state_id = tile.tensix.config_unit.thread_cfg[thread_id][42] & 1
  name = d.name
  if name in {"WRCFG", "WRCFG32"}:
    return f"writes {_cfg_word(tile, state_id, d.CfgReg & 0x1FF)} from gpr{d.GprAddress}"
  if name == "RDCFG":
    return f"reads {_cfg_word(tile, state_id, d.CfgReg & 0x1FF)} into gpr{d.GprAddress}"
  if name == "SETC16":
    return f"writes thread_cfg[{thread_id}][{d.setc16_reg}]=0x{d.setc16_value:04x}"
  if name.startswith("RMWCIB"):
    return f"updates {_cfg_word(tile, 0, d.CfgRegAddr)} mask=0x{d.Mask:02x} data=0x{d.Data:02x}"
  if name == "CFGSHIFTMASK":
    return f"updates {_cfg_word(tile, state_id, d.cfg_reg)}"
  if name == "STREAMWAIT":
    hi_addr = 57 if d.target_sel == 0 else 58
    return f"reads thread_cfg[{thread_id}][{hi_addr}]=0x{tile.tensix.config_unit.thread_cfg[thread_id][hi_addr]:08x}"
  if name == "MOP":
    words = ", ".join(
      f"{i}:0x{tile.tensix.threads[thread_id].mop.cfg[i]:08x}"
      for i in range(len(tile.tensix.threads[thread_id].mop.cfg))
      if tile.tensix.threads[thread_id].mop.cfg[i]
    )
    return f"reads mop_cfg[{thread_id}] {{{words or 'all zero'}}}"
  if name in {
      "MOVA2D", "MOVB2D", "MOVD2A", "MOVD2B", "SFPLOAD", "SFPSTORE",
      "SFPLOADI", "SFPADD", "SFPMUL", "SFPMAD", "SFPMULI", "SFPADDI",
      "SFPIADD", "SFPMOV", "SFPCAST", "SFPSHFT", "SFPSHFT2",
      "SFPEXEXP", "SFPEXMAN", "SFPSETEXP", "SFPDIVP2", "SFPSETCC",
      "SFPGT", "SFPABS", "SFPSETSGN", "SFPAND", "SFPOR", "SFPNOT",
      "SFPXOR", "SFPLZ", "SFPPUSHC", "SFPPOPC", "SFPENCC",
      "SFPCOMPC", "SFPTRANSP", "SFPNOP", "SFPCONFIG", "ZEROACC", "ZEROSRC", "SETRWC",
      "INCRWC", "CLEARDVALID",
  }:
    return "cfg: none"
  if name in {"STALLWAIT", "SEMWAIT", "SEMINIT", "SEMPOST", "SEMGET"}:
    return "cfg: none"
  return "cfg: unknown"


def _t1_live_deps(tile, d, thread_id: int) -> str:
  t = tile.tensix
  rwc = t.rwc[thread_id]
  if d.name in {"MOVA2D", "MOVB2D", "SFPLOAD", "SFPSTORE", "SETRWC", "INCRWC"}:
    srca_owners = ",".join(bank.allowed_client for bank in t.srca.banks)
    dest_valid0 = "".join("1" if t.dest.valid[i] else "0" for i in range(8))
    return (
      f"rwc=(a={rwc.a},b={rwc.b},d={rwc.d},cr={rwc.cr}) "
      f"srca=(fpu={t.srca.fpu_bank},unp={t.srca.unpack_bank},owners={srca_owners}) "
      f"dest_valid[0:8]={dest_valid0}"
    )
  if d.name == "STALLWAIT":
    return f"stall_res=0x{d.stall_res:x} wait_res=0x{d.wait_res:x}"
  if d.name == "SEMWAIT":
    sems = ",".join(
      f"{i}:{t.semaphores.value[i]}/{t.semaphores.max[i]}"
      for i in range(8)
      if d.sem_sel & (1 << i)
    )
    return f"stall_res=0x{d.stall_res:x} sem_sel=0x{d.sem_sel:x} sems={sems or 'none'}"
  return ""


def install_t1_push_trace(tile, limit: int | None, verbose: bool = False):
  orig_push = tile.tensix.push_instruction
  count = 0

  def traced_push(thread_id, word):
    nonlocal count
    if thread_id == 1 and (limit is None or count < limit):
      count += 1
      d = dsl.decode_tensix(word)
      if verbose:
        cfg = _t1_cfg_deps(tile, d, thread_id)
        live = _t1_live_deps(tile, d, thread_id)
        suffix = f" | {live}" if live else ""
        print(
          f"T1_PUSH[{count:04d}] word=0x{word & 0xFFFFFFFF:08x} {d!r} | {cfg}{suffix}",
          flush=True,
        )
      else:
        print(f"T1_PUSH[{count:04d}] word=0x{word & 0xFFFFFFFF:08x} {d!r}", flush=True)
    return orig_push(thread_id, word)

  tile.tensix.push_instruction = traced_push


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


def build_brisc_fw() -> bytes:
  a = Asm(BRISC_FW_BASE)
  a.label("loop")
  a.li32(dsl.t0, GO_MESSAGES + 3)
  a.label("wait_go")
  a.emit(dsl.LBU(dsl.t1, dsl.t0, 0))
  a.emit(dsl.ADDI(dsl.t2, dsl.zero, RUN_MSG_GO))
  a.bne_label(dsl.t1, dsl.t2, "wait_go")

  a.li32(dsl.t0, SUBORDINATE_SYNC)
  a.li32(dsl.t1, 0x80808080)
  a.emit(dsl.SW(dsl.t0, dsl.t1, 0))
  a.call_abs(BRISC_KERNEL_BASE)

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
  a.emit(dsl.SB(dsl.s0, dsl.zero, 0))
  a.j_label("wait_go")
  return a.bytes()


def build_ret_kernel() -> bytes:
  return dsl.pack([dsl.RET()])


def scratch_boot(dev: Device, kernel_bases: dict[str, int] | None = None,
                 fw_bases: dict[str, int] | None = None):
  if kernel_bases is None:
    kernel_bases = {}
  if fw_bases is None:
    fw_bases = {}
  brisc_kernel = kernel_bases.get("brisc", BRISC_KERNEL_BASE)
  ncrisc_kernel = kernel_bases.get("ncrisc", NCRISC_KERNEL_BASE)
  trisc0_kernel = kernel_bases.get("trisc0", TRISC0_KERNEL_BASE)
  trisc1_kernel = kernel_bases.get("trisc1", TRISC1_KERNEL_BASE)
  trisc2_kernel = kernel_bases.get("trisc2", TRISC2_KERNEL_BASE)
  trisc2_fw = fw_bases.get("trisc2", TRISC2_FW_BASE)

  tile = next(iter(dev.tiles.values()))
  l1 = tile.l1
  mmio = tile.mmio

  l1.load(BOOT_JAL, _make_jal(BRISC_FW_BASE))
  l1.load(BRISC_FW_BASE, build_brisc_fw())
  l1.load(NCRISC_FW_BASE, build_subordinate_fw(
    NCRISC_FW_BASE, 0, ncrisc_kernel, DM_STACK_TOP))
  l1.load(TRISC0_FW_BASE, build_subordinate_fw(
    TRISC0_FW_BASE, 1, trisc0_kernel, TRISC_STACK_TOP))
  l1.load(TRISC1_FW_BASE, build_subordinate_fw(
    TRISC1_FW_BASE, 2, trisc1_kernel, TRISC_STACK_TOP))
  l1.load(trisc2_fw, build_subordinate_fw(
    trisc2_fw, 3, trisc2_kernel, TRISC_STACK_TOP))

  for addr in (
      BRISC_KERNEL_BASE,
      NCRISC_KERNEL_BASE,
      TRISC0_KERNEL_BASE,
      TRISC1_KERNEL_BASE,
      TRISC2_KERNEL_BASE,
  ):
    l1.load(addr, build_ret_kernel())

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
  ap = argparse.ArgumentParser()
  ap.add_argument("--tiles", type=int, default=1)
  ap.add_argument("--max-run-steps", type=int, default=20_000)
  ap.add_argument(
    "--raw-compute",
    action="store_true",
    help="call add1 TRISC compute kernels copied from the checked-in objdump",
  )
  ap.add_argument(
    "--input-pattern",
    choices=("fractional", "ordered"),
    default="ordered",
    help="source tile pattern; ordered (0,1,2,...) makes unpack/pack "
         "ordering mismatches obvious — expected output is just i+1",
  )
  ap.add_argument(
    "--trace-t1-pushes",
    action="store_true",
    help="print Tensix operations pushed to TRISC1's T1 FIFO",
  )
  ap.add_argument(
    "--trace-t1-limit",
    type=int,
    default=80,
    help="maximum T1 FIFO pushes to print; use 0 for unlimited",
  )
  ap.add_argument(
    "--trace-t1-verbose",
    action="store_true",
    help="include config/register dependency state in --trace-t1-pushes output",
  )
  args = ap.parse_args()

  dev = Device(tensix_x=(1,), tensix_y=(2,))
  kernel_bases = RAW_TRISC_KERNEL_BASES if args.raw_compute else None
  fw_bases = {"trisc2": RAW_TRISC2_FW_BASE} if args.raw_compute else None
  tile = scratch_boot(dev, kernel_bases=kernel_bases, fw_bases=fw_bases)
  alloc, src, dst, src_data, exp_data = setup_add1_runtime(
    dev, tile, args.tiles, args.input_pattern)
  verify_runtime_setup(alloc, src, src_data)
  verify_tile_runtime(tile, src, dst, args.tiles)
  if args.raw_compute:
    load_raw_compute_kernels(tile, args.tiles, src_data)
  if args.trace_t1_pushes:
    install_t1_push_trace(
      tile,
      None if args.trace_t1_limit == 0 else args.trace_t1_limit,
      verbose=args.trace_t1_verbose,
    )

  print("scratch firmware booted", flush=True)
  print(
    "runtime: "
    f"src=0x{src.addr:x} dst=0x{dst.addr:x} tiles={args.tiles} "
    f"banks={dev.dram.num_banks} "
    f"rta=[brisc=0x{BRISC_RTA_BASE:x}, ncrisc=0x{NCRISC_RTA_BASE:x}, "
    f"trisc=0x{TRISC_RTA_BASE:x}] cb=0x{CB_CONFIG_BASE:x}",
    flush=True,
  )
  if args.raw_compute:
    print(
      "raw compute: "
      f"trisc0=0x{RAW_TRISC_KERNEL_BASES['trisc0']:x} "
      f"trisc1=0x{RAW_TRISC_KERNEL_BASES['trisc1']:x} "
      f"trisc2=0x{RAW_TRISC_KERNEL_BASES['trisc2']:x}",
      flush=True,
    )
  tile.l1.write8(GO_MESSAGES + 3, RUN_MSG_GO)
  print(f"running scratch dispatch (max {args.max_run_steps} steps)...",
        flush=True)
  try:
    dev._step_loop([tile],
                   lambda: (
                     tile.l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE
                     and tensix_idle(tile)
                   ),
                   args.max_run_steps)
  except TimeoutError as e:
    print(f"RUN TIMEOUT: {e}", file=sys.stderr, flush=True)
    return 1
  except Exception as e:
    print(f"RUN ERROR: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    return 1

  sync = tile.l1.read32(SUBORDINATE_SYNC)
  if sync != 0:
    print(f"FAIL: subordinate sync is 0x{sync:08x}", file=sys.stderr)
    return 1

  if len(exp_data) != dst.size:
    print("FAIL: expected output size mismatch", file=sys.stderr)
    return 1

  if args.raw_compute:
    cb16_addr = DATA_BUFFER_SPACE_BASE + TILE_BYTES * 2
    got = read_l1(tile, cb16_addr, min(TILE_BYTES, len(exp_data)))
    exp = exp_data[:len(got)]
    if got != exp:
      print(
        "RAW COMPUTE OUTPUT MISMATCH: "
        f"cb16 first32={got[:32].hex()} expected first32={exp[:32].hex()}",
        file=sys.stderr,
        flush=True,
      )
      print(f"  got bf16:      {format_bf16_words(got)}", file=sys.stderr)
      print(f"  expected bf16: {format_bf16_words(exp)}", file=sys.stderr)
      print(f"  got float:     {format_bf16_floats(got)}", file=sys.stderr)
      print(f"  expected float:{format_bf16_floats(exp)}", file=sys.stderr)
      return 1
    print("PASS raw compute", flush=True)
    return 0

  print("PASS scratch dispatch", flush=True)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
