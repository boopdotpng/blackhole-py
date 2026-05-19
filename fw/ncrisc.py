from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel
from dsl import Reg, ra, sp, t0, t1, t2, t3, t4, t5, t6, zero

NCRISC_STACK_TOP = 0xFFB01FF0
SUBORDINATE_SYNC = 0x68
LAUNCH_MSG_RD_PTR = 0x6C
CORE_INFO_ABSOLUTE_LOGICAL_X = 0x940
CORE_INFO_ABSOLUTE_LOGICAL_Y = 0x941
RUN_SYNC_MSG_GO = 0x80
RUN_SYNC_MSG_LOAD = 0x01
RUN_SYNC_MSG_DONE = 0x00

LAUNCH = 0x70
LAUNCH_MSG_SIZE = 96
LAUNCH_KERNEL_CONFIG_BASE = 0
LAUNCH_SEM_OFFSET = 12
LAUNCH_LOCAL_CB_OFFSET = 18
LAUNCH_REMOTE_CB_OFFSET = 20
LAUNCH_RTA_OFFSET = 22
LAUNCH_KERNEL_TEXT_OFFSET = 44
LAUNCH_LOCAL_CB_MASK = 64
LAUNCH_ENABLES = 76
LAUNCH_MIN_REMOTE_CB_START_INDEX = 82
LAUNCH_SUB_DEVICE_ORIGIN_X = 92
LAUNCH_SUB_DEVICE_ORIGIN_Y = 93

# NCRISC firmware symbol addresses from the C++ NCRISC ELF used for kernel
# linking in blackhole-py-old.
MY_Y = 0xFFB0002C
MY_X = 0xFFB00030
MY_RELATIVE_Y = 0xFFB00032
MY_RELATIVE_X = 0xFFB00033
CRTA_L1_BASE_PTR = 0xFFB00034
RTA_L1_BASE_PTR = 0xFFB00038
MY_LOGICAL_Y = 0xFFB0003C
MY_LOGICAL_X = 0xFFB0003D
DRAM_BANK_TO_NOC_XY = 0xFFB00040
L1_BANK_TO_NOC_XY = 0xFFB0005C
BANK_TO_DRAM_OFFSET = 0xFFB0023C
BANK_TO_L1_OFFSET = 0xFFB00258
SEM_L1_BASE = 0xFFB00458
CB_INTERFACE = 0xFFB00464

NOC_REGS_START_ADDR = 0xFFB20000
NOC_CMD_BUF_OFFSET_BIT = 11
NOC_INSTANCE_OFFSET_BIT = 16
NOC_CFG_BASE = NOC_REGS_START_ADDR + 0x100
NOC_ID_LOGICAL = 0x12
NOC_NODE_ID_MASK = 0x3F
NOC_ADDR_NODE_ID_BITS = 6
MEM_BANK_TO_NOC_SCRATCH = 0x112B0
P100_NUM_DRAM_BANKS = 7
P100_NUM_L1_BANKS = 120
P100_DRAM_BANK_TO_NOC_SIZE = 2 * P100_NUM_DRAM_BANKS * 2
P100_L1_BANK_TO_NOC_SIZE = 2 * P100_NUM_L1_BANKS * 2
P100_BANK_TO_DRAM_OFFSET_SIZE = P100_NUM_DRAM_BANKS * 4
P100_BANK_TO_L1_OFFSET_SIZE = P100_NUM_L1_BANKS * 4

LOCAL_CB_INTERFACE_SIZE = 32
LOCAL_CB_CONFIG_SIZE = 16
CB_SYNC_TILES_ACKED_BASE = 0xFFB48020
CB_SYNC_TILES_RECEIVED_BASE = 0xFFB48028
CB_SYNC_STRIDE = 0x1000


def write8(fw: Kernel, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sb(value, addr, 0)


def write32(fw: Kernel, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sw(value, addr, 0)


def read32(fw: Kernel, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  return fw.lw(rd, addr, 0)


def read8(fw: Kernel, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  return fw.lbu(rd, addr, 0)


def current_launch_ptr(fw: Kernel, launch: Reg = t0, tmp: Reg = t1):
  return fw.li(launch, LAUNCH)


def wait8(fw: Kernel, addr: int, value: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  fw.li(ptr, addr)
  fw.li(expected, value)
  start = fw._new_label("wait8")
  done = fw._new_label("wait8_done")
  fw.label(start)
  fw.lbu(actual, ptr, 0)
  fw.beq(actual, expected, done)
  fw.fence()
  fw.j(start)
  fw.label(done)
  fw.fence()
  return fw


def setup_stack(fw: Kernel):
  return fw.li(sp, NCRISC_STACK_TOP)


def configure_csr(fw: Kernel, *, value: Reg = t0):
  fw.li(value, 2)
  fw.csrrs(zero, value, 0x7C0)
  fw.li(value, 1)
  fw.slli(value, value, 18)
  fw.fence()
  fw.csrrs(zero, value, 0x7C0)
  fw.li(value, 2)
  fw.csrrc(zero, value, 0x7C0)
  fw.fence()
  fw.fence()
  fw.li(value, 8)
  fw.csrrs(zero, value, 0x7C0)
  return fw


def signal_subordinate_done(fw: Kernel, role: int):
  return write8(fw, SUBORDINATE_SYNC + role - 1, RUN_SYNC_MSG_DONE)


def wait_subordinate_load_or_go(fw: Kernel, role: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  loop = fw._new_label("wait_subordinate")
  done = fw._new_label("subordinate_ready")
  fw.li(ptr, SUBORDINATE_SYNC + role - 1)
  fw.label(loop)
  fw.lbu(actual, ptr, 0)
  fw.li(expected, RUN_SYNC_MSG_GO)
  fw.beq(actual, expected, done)
  fw.li(expected, RUN_SYNC_MSG_LOAD)
  fw.beq(actual, expected, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  fw.fence()
  return fw


def launch_kernel_enabled(fw: Kernel, role: int, *, enabled: Reg = t0, mask: Reg = t1):
  current_launch_ptr(fw, launch=enabled, tmp=mask)
  fw.lw(enabled, enabled, LAUNCH_ENABLES)
  fw.li(mask, 1 << role)
  return fw.and_(enabled, enabled, mask)


def run_launch_kernel(fw: Kernel, role: int, *, launch: Reg = t0, config_base: Reg = t1,
                      offset: Reg = t2, entry: Reg = t3, enabled: Reg = t4):
  skip = fw._new_label("skip_kernel")
  launch_kernel_enabled(fw, role, enabled=enabled, mask=offset)
  fw.beq(enabled, zero, skip)
  current_launch_ptr(fw, launch=launch, tmp=enabled)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)
  fw.lw(offset, launch, LAUNCH_KERNEL_TEXT_OFFSET + 4 * role)
  fw.add(entry, config_base, offset)
  fw.jalr(ra, entry, 0)
  fw.label(skip)
  return fw


def noc_cmd_buf_addr(noc: int, cmd_buf: int, reg: int) -> int:
  return reg + (cmd_buf << NOC_CMD_BUF_OFFSET_BIT) + (noc << NOC_INSTANCE_OFFSET_BIT)


def init_risc_noc_coords(fw: Kernel, *, noc_id: Reg = t0, coord: Reg = t1, tmp: Reg = t2):
  for noc in range(2):
    read32(fw, noc_id, noc_cmd_buf_addr(noc, 0, NOC_CFG_BASE + NOC_ID_LOGICAL * 4), tmp_addr=tmp)
    fw.andi(coord, noc_id, NOC_NODE_ID_MASK)
    write8(fw, MY_X + noc, coord, tmp_addr=tmp)
    fw.srli(coord, noc_id, NOC_ADDR_NODE_ID_BITS)
    fw.andi(coord, coord, NOC_NODE_ID_MASK)
    write8(fw, MY_Y + noc, coord, tmp_addr=tmp)
  return fw


def copy_words(fw: Kernel, dst: int, src: int, byte_count: int, *,
               dst_reg: Reg = t0, src_reg: Reg = t1, value: Reg = t2,
               count: Reg = t3):
  fw.li(dst_reg, dst)
  fw.li(src_reg, src)
  fw.li(count, byte_count // 4)
  loop = fw._new_label("copy_words")
  done = fw._new_label("copy_done")
  fw.label(loop)
  fw.beq(count, zero, done)
  fw.lw(value, src_reg, 0)
  fw.sw(value, dst_reg, 0)
  fw.addi(src_reg, src_reg, 4)
  fw.addi(dst_reg, dst_reg, 4)
  fw.addi(count, count, -1)
  fw.j(loop)
  fw.label(done)
  return fw


def init_bank_tables(fw: Kernel):
  src = MEM_BANK_TO_NOC_SCRATCH
  copy_words(fw, DRAM_BANK_TO_NOC_XY, src, P100_DRAM_BANK_TO_NOC_SIZE)
  src += P100_DRAM_BANK_TO_NOC_SIZE
  copy_words(fw, L1_BANK_TO_NOC_XY, src, P100_L1_BANK_TO_NOC_SIZE)
  src += P100_L1_BANK_TO_NOC_SIZE
  copy_words(fw, BANK_TO_DRAM_OFFSET, src, P100_BANK_TO_DRAM_OFFSET_SIZE)
  src += P100_BANK_TO_DRAM_OFFSET_SIZE
  copy_words(fw, BANK_TO_L1_OFFSET, src, P100_BANK_TO_L1_OFFSET_SIZE)
  return fw


def init_ncrisc_mailbox_globals(fw: Kernel, *, value: Reg = t0, tmp: Reg = t1):
  read8(fw, value, CORE_INFO_ABSOLUTE_LOGICAL_X, tmp_addr=tmp)
  write8(fw, MY_LOGICAL_X, value, tmp_addr=tmp)
  read8(fw, value, CORE_INFO_ABSOLUTE_LOGICAL_Y, tmp_addr=tmp)
  write8(fw, MY_LOGICAL_Y, value, tmp_addr=tmp)
  return fw


def init_ncrisc_kernel_config(fw: Kernel, *, launch: Reg = t0, config_base: Reg = t1,
                              off: Reg = t2, addr: Reg = t3, tmp: Reg = t4):
  current_launch_ptr(fw, launch=launch, tmp=tmp)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)

  for i in range(3):
    fw.lhu(off, launch, LAUNCH_SEM_OFFSET + 2 * i)
    fw.add(addr, config_base, off)
    write32(fw, SEM_L1_BASE + 4 * i, addr, tmp_addr=tmp)

  fw.lhu(off, launch, LAUNCH_RTA_OFFSET + 4)
  fw.add(addr, config_base, off)
  write32(fw, RTA_L1_BASE_PTR, addr, tmp_addr=tmp)

  fw.lhu(off, launch, LAUNCH_RTA_OFFSET + 6)
  fw.add(addr, config_base, off)
  write32(fw, CRTA_L1_BASE_PTR, addr, tmp_addr=tmp)
  return fw


def init_ncrisc_launch_globals(fw: Kernel, *, launch: Reg = t0, value: Reg = t1,
                               tmp: Reg = t2, origin: Reg = t3):
  current_launch_ptr(fw, launch=launch, tmp=tmp)
  read8(fw, value, MY_LOGICAL_X, tmp_addr=tmp)
  fw.lbu(origin, launch, LAUNCH_SUB_DEVICE_ORIGIN_X)
  fw.sub(value, value, origin)
  write8(fw, MY_RELATIVE_X, value, tmp_addr=tmp)
  read8(fw, value, MY_LOGICAL_Y, tmp_addr=tmp)
  fw.lbu(origin, launch, LAUNCH_SUB_DEVICE_ORIGIN_Y)
  fw.sub(value, value, origin)
  write8(fw, MY_RELATIVE_Y, value, tmp_addr=tmp)
  return fw


def setup_local_cbs_from_mask(fw: Kernel, cb_config: Reg, cb_if: Reg, mask: Reg, *,
                              size: Reg = t5, fifo: Reg = t6, tmp: Reg = t0):
  fw.li(tmp, CB_SYNC_TILES_ACKED_BASE)
  fw.li(t1, CB_SYNC_TILES_RECEIVED_BASE)
  loop = fw._new_label("setup_cb")
  skip = fw._new_label("skip_cb")
  done = fw._new_label("done_cb")
  fw.label(loop)
  fw.beq(mask, zero, done)
  fw.andi(size, mask, 1)
  fw.beq(size, zero, skip)
  fw.lw(size, cb_config, 4)
  fw.lw(fifo, cb_config, 0)
  fw.sw(size, cb_if, 0)
  fw.add(size, fifo, size)
  fw.sw(size, cb_if, 4)
  fw.lw(size, cb_config, 12)
  fw.sw(size, cb_if, 8)
  fw.lw(size, cb_config, 8)
  fw.sw(size, cb_if, 12)
  fw.sw(fifo, cb_if, 16)
  fw.sw(fifo, cb_if, 20)
  fw.sw(zero, cb_if, 24)
  fw.sw(zero, cb_if, 28)
  fw.sw(zero, tmp, 0)
  fw.sw(zero, t1, 0)
  fw.label(skip)
  fw.addi(cb_config, cb_config, LOCAL_CB_CONFIG_SIZE)
  fw.addi(cb_if, cb_if, LOCAL_CB_INTERFACE_SIZE)
  fw.li(size, CB_SYNC_STRIDE)
  fw.add(tmp, tmp, size)
  fw.add(t1, t1, size)
  fw.srli(mask, mask, 1)
  fw.j(loop)
  fw.label(done)
  return fw


def setup_local_cbs(fw: Kernel, *, launch: Reg = t0, config_base: Reg = t1,
                    cb_config: Reg = t2, cb_if: Reg = t3, mask: Reg = t4):
  current_launch_ptr(fw, launch=launch, tmp=mask)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)
  fw.lhu(cb_config, launch, LAUNCH_LOCAL_CB_OFFSET)
  fw.add(cb_config, config_base, cb_config)
  fw.li(cb_if, CB_INTERFACE)
  fw.lw(mask, launch, LAUNCH_LOCAL_CB_MASK)
  setup_local_cbs_from_mask(fw, cb_config, cb_if, mask)
  return fw


def build() -> Kernel:
  fw = Kernel.firmware("ncrisc")
  setup_stack(fw)
  configure_csr(fw)
  init_bank_tables(fw)
  init_risc_noc_coords(fw)
  init_ncrisc_mailbox_globals(fw)
  signal_subordinate_done(fw, 1)
  fw.label("run_loop")
  wait_subordinate_load_or_go(fw, 1)
  init_ncrisc_kernel_config(fw)
  setup_local_cbs(fw)
  init_ncrisc_launch_globals(fw)
  wait8(fw, SUBORDINATE_SYNC, RUN_SYNC_MSG_GO)
  run_launch_kernel(fw, 1)
  signal_subordinate_done(fw, 1)
  fw.j("run_loop")
  return fw


def write_artifacts(out_dir: Path | str | None = None) -> Path:
  out = Path(__file__).resolve().parent / "build" if out_dir is None else Path(out_dir)
  out.mkdir(parents=True, exist_ok=True)
  segments = build().compile()
  manifest = {"kind": "ncrisc", "segments": []}
  for i, seg in enumerate(segments):
    name = f"ncrisc.seg{i}.bin"
    (out / name).write_bytes(seg.data)
    manifest["segments"].append({
      "label": seg.label,
      "addr": f"0x{seg.addr:x}",
      "bin": name,
      "filesz": len(seg.data),
      "memsz": len(seg.data),
      "flags": 5 if seg.label.endswith(".text") else 6,
    })
  manifest_path = out / "ncrisc.json"
  manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
  return manifest_path


if __name__ == "__main__":
  print(write_artifacts())
