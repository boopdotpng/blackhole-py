from __future__ import annotations
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import FIRMWARE_SCRATCH_BASE, Kernel
from dsl import Reg, gp, ra, sp, t0, t1, t2, t3, t4, t5, t6, zero

TRISC_GLOBAL_POINTER = 0xFFB007F0
TRISC_STACK_TOP = 0xFFB00FF0
SUBORDINATE_SYNC = 0x68
RUN_SYNC_MSG_GO = 0x80
RUN_SYNC_MSG_INIT_SYNC_REGISTERS = 0x03
RUN_SYNC_MSG_DONE = 0x00

LAUNCH = 0x70
LAUNCH_KERNEL_CONFIG_BASE = 0
LAUNCH_SEM_OFFSET = 12
LAUNCH_LOCAL_CB_OFFSET = 18
LAUNCH_REMOTE_CB_OFFSET = 20
LAUNCH_RTA_OFFSET = 22
LAUNCH_KERNEL_TEXT_OFFSET = 44
LAUNCH_LOCAL_CB_MASK = 64
LAUNCH_ENABLES = 76
LAUNCH_MIN_REMOTE_CB_START_INDEX = 70
LAUNCH_SUB_DEVICE_ORIGIN_X = 92
LAUNCH_SUB_DEVICE_ORIGIN_Y = 93

CORE_INFO_ABSOLUTE_LOGICAL_X = 0x940
CORE_INFO_ABSOLUTE_LOGICAL_Y = 0x941
REGFILE_BASE = 0xFFE00000
TENSIX_CFG_BASE = 0xFFEF0000
PRNG_SEED_Seed_Val_ADDR32 = 186
PC_BUF_SYNC = 0xFFE80004
CB_SYNC_TILES_ACKED_BASE = 0xFFB40020
CB_SYNC_TILES_RECEIVED_BASE = 0xFFB40028
CB_SYNC_STRIDE = 0x1000
NUM_CIRCULAR_BUFFERS = 64
LOCAL_CB_INTERFACE_SIZE = 32
LOCAL_CB_CONFIG_SIZE = 16

TRISC_DATA_COMMON = {
  "dest_offset_id": 0xFFB00000,
  "op_info_offset": 0xFFB00004,
  "my_relative_y": 0xFFB0000C,
  "my_relative_x": 0xFFB0000D,
  "crta_l1_base": 0xFFB00010,
  "rta_l1_base": 0xFFB00014,
  "my_logical_y": 0xFFB00018,
  "my_logical_x": 0xFFB00019,
  "cfg_state_id": 0xFFB0001C,
  "cb_interface": 0xFFB00020,
}

TRISC1_DATA = {
  "dest_offset_id": 0xFFB00000,
  "op_info_offset": 0xFFB00004,
  "my_relative_y": 0xFFB00008,
  "my_relative_x": 0xFFB00009,
  "crta_l1_base": 0xFFB0000C,
  "rta_l1_base": 0xFFB00010,
  "my_logical_y": 0xFFB00014,
  "my_logical_x": 0xFFB00015,
  "cfg_state_id": 0xFFB00018,
}

TRISC_LOCAL_END = {
  0: 0xFFB00820,
  1: 0xFFB0001C,
  2: 0xFFB00820,
}

TRISC_LOCAL_DATA_SIZE = {
  0: 1056,
  1: 28,
  2: 1056,
}


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


def wait8(fw: Kernel, addr: int, value: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  fw.li(ptr, addr)
  fw.li(expected, value)
  start = fw._new_label("wait8")
  fw.label(start)
  fw.lbu(actual, ptr, 0)
  fw.bne(actual, expected, start)
  return fw


def setup_stack(fw: Kernel):
  return fw.li(sp, TRISC_STACK_TOP)


def setup_gp(fw: Kernel):
  return fw.li(gp, TRISC_GLOBAL_POINTER)


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


def zero_regfile(fw: Kernel, *, ptr: Reg = t0, count: Reg = t1):
  fw.li(ptr, REGFILE_BASE)
  fw.li(count, 64)
  loop = fw._new_label("zero_regfile")
  done = fw._new_label("zero_regfile_done")
  fw.label(loop)
  fw.beq(count, zero, done)
  fw.sw(zero, ptr, 0)
  fw.addi(ptr, ptr, 4)
  fw.addi(count, count, -1)
  fw.j(loop)
  fw.label(done)
  return fw


def zero_words(fw: Kernel, start: int, end: int, *, ptr: Reg = t0, limit: Reg = t1):
  fw.li(ptr, start)
  fw.li(limit, end)
  loop = fw._new_label("zero_words")
  done = fw._new_label("zero_words_done")
  fw.label(loop)
  fw.bgeu(ptr, limit, done)
  fw.sw(zero, ptr, 0)
  fw.addi(ptr, ptr, 4)
  fw.j(loop)
  fw.label(done)
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


def wait_cycles(fw: Kernel, cycles: int, *, count: Reg = t0):
  fw.li(count, cycles)
  loop = fw._new_label("wait_cycles")
  done = fw._new_label("wait_cycles_done")
  fw.label(loop)
  fw.beq(count, zero, done)
  fw.addi(count, count, -1)
  fw.j(loop)
  fw.label(done)
  return fw


def init_local_data(fw: Kernel, trisc_id: int):
  return copy_words(
    fw,
    0xFFB00000,
    FIRMWARE_SCRATCH_BASE[f"trisc{trisc_id}"],
    TRISC_LOCAL_DATA_SIZE[trisc_id],
  )


def init_common_state(fw: Kernel, data: dict[str, int]):
  write32(fw, data["dest_offset_id"], 0)
  write32(fw, data["op_info_offset"], 0)
  write32(fw, data["cfg_state_id"], 0)
  write32(fw, TENSIX_CFG_BASE + PRNG_SEED_Seed_Val_ADDR32 * 4, 0)
  wait_cycles(fw, 600)
  read8(fw, t1, CORE_INFO_ABSOLUTE_LOGICAL_X, tmp_addr=t0)
  write8(fw, data["my_logical_x"], t1, tmp_addr=t0)
  read8(fw, t1, CORE_INFO_ABSOLUTE_LOGICAL_Y, tmp_addr=t0)
  write8(fw, data["my_logical_y"], t1, tmp_addr=t0)
  return fw


def signal_subordinate_done(fw: Kernel, role: int):
  return write8(fw, SUBORDINATE_SYNC + role - 1, RUN_SYNC_MSG_DONE)


def wait_trisc_message(fw: Kernel, trisc_id: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  loop = fw._new_label("wait_trisc")
  done = fw._new_label("trisc_go")
  init_sync = fw._new_label("trisc_init_sync")
  fw.li(ptr, SUBORDINATE_SYNC + trisc_id + 1)
  fw.label(loop)
  fw.lbu(actual, ptr, 0)
  fw.li(expected, RUN_SYNC_MSG_GO)
  fw.beq(actual, expected, done)
  if trisc_id == 0:
    fw.li(expected, RUN_SYNC_MSG_INIT_SYNC_REGISTERS)
    fw.beq(actual, expected, init_sync)
  fw.fence()
  fw.j(loop)
  if trisc_id == 0:
    fw.label(init_sync)
    init_sync_registers(fw)
    fw.li(ptr, SUBORDINATE_SYNC + trisc_id + 1)
    write8(fw, ptr, RUN_SYNC_MSG_DONE, tmp_addr=actual, tmp_val=expected)
    fw.j(loop)
  fw.label(done)
  return fw


def run_launch_kernel(fw: Kernel, trisc_id: int, *, launch: Reg = t0, config_base: Reg = t1,
                      offset: Reg = t2, entry: Reg = t3):
  role = 2 + trisc_id
  fw.li(launch, LAUNCH)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)
  fw.lw(offset, launch, LAUNCH_KERNEL_TEXT_OFFSET + 4 * role)
  fw.add(entry, config_base, offset)
  fw.jalr(ra, entry, 0)
  return fw


def init_sync_registers(fw: Kernel, *, recv: Reg = t0, ack: Reg = t1, count: Reg = t2, stride: Reg = t3):
  fw.li(recv, CB_SYNC_TILES_RECEIVED_BASE)
  fw.li(ack, CB_SYNC_TILES_ACKED_BASE)
  fw.li(count, NUM_CIRCULAR_BUFFERS)
  fw.li(stride, CB_SYNC_STRIDE)
  loop = fw._new_label("init_cb_sync")
  done = fw._new_label("init_cb_sync_done")
  fw.label(loop)
  fw.beq(count, zero, done)
  fw.sw(zero, recv, 0)
  fw.sw(zero, ack, 0)
  fw.add(recv, recv, stride)
  fw.add(ack, ack, stride)
  fw.addi(count, count, -1)
  fw.j(loop)
  fw.label(done)
  return fw


def setup_local_cbs_from_mask(fw: Kernel, trisc_id: int, cb_config: Reg, cb_if: Reg, mask: Reg, *,
                              size: Reg = t5, fifo: Reg = t6, page: Reg = t0, tmp: Reg = t1):
  loop = fw._new_label("setup_cb")
  skip = fw._new_label("skip_cb")
  done = fw._new_label("done_cb")
  fw.label(loop)
  fw.beq(mask, zero, done)
  fw.andi(tmp, mask, 1)
  fw.beq(tmp, zero, skip)
  fw.lw(size, cb_config, 4)
  fw.lw(fifo, cb_config, 0)
  fw.lw(page, cb_config, 12)
  fw.srli(size, size, 4)
  fw.srli(fifo, fifo, 4)
  fw.srli(page, page, 4)
  fw.sw(size, cb_if, 0)
  fw.add(size, fifo, size)
  fw.sw(size, cb_if, 4)
  fw.sw(page, cb_if, 8)
  if trisc_id == 0:
    fw.sw(fifo, cb_if, 16)
  else:
    fw.lw(tmp, cb_config, 8)
    fw.sw(tmp, cb_if, 12)
    fw.sw(fifo, cb_if, 20)
  fw.sw(zero, cb_if, 24)
  if trisc_id == 2:
    fw.sw(zero, cb_if, 28)
  fw.label(skip)
  fw.addi(cb_config, cb_config, LOCAL_CB_CONFIG_SIZE)
  fw.addi(cb_if, cb_if, LOCAL_CB_INTERFACE_SIZE)
  fw.srli(mask, mask, 1)
  fw.j(loop)
  fw.label(done)
  return fw


def setup_local_cbs(fw: Kernel, trisc_id: int, data: dict[str, int], *, launch: Reg = t0, config_base: Reg = t1,
                    cb_config: Reg = t2, cb_if: Reg = t3, mask: Reg = t4):
  fw.li(launch, LAUNCH)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)
  fw.lhu(cb_config, launch, LAUNCH_LOCAL_CB_OFFSET)
  fw.add(cb_config, config_base, cb_config)
  fw.li(cb_if, data["cb_interface"])
  fw.lw(mask, launch, LAUNCH_LOCAL_CB_MASK)
  setup_local_cbs_from_mask(fw, trisc_id, cb_config, cb_if, mask)
  return fw


def init_trisc_kernel_config(fw: Kernel, trisc_id: int, data: dict[str, int], *,
                             launch: Reg = t0, config_base: Reg = t1, off: Reg = t2,
                             addr: Reg = t3, value: Reg = t4, origin: Reg = t5):
  fw.li(launch, LAUNCH)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)

  rta_slot = 2 + trisc_id
  fw.lhu(off, launch, LAUNCH_RTA_OFFSET + 4 * rta_slot)
  fw.add(addr, config_base, off)
  write32(fw, data["rta_l1_base"], addr, tmp_addr=value)

  fw.lhu(off, launch, LAUNCH_RTA_OFFSET + 4 * rta_slot + 2)
  fw.add(addr, config_base, off)
  write32(fw, data["crta_l1_base"], addr, tmp_addr=value)

  read8(fw, value, data["my_logical_x"], tmp_addr=addr)
  fw.lbu(origin, launch, LAUNCH_SUB_DEVICE_ORIGIN_X)
  fw.sub(value, value, origin)
  write8(fw, data["my_relative_x"], value, tmp_addr=addr)

  read8(fw, value, data["my_logical_y"], tmp_addr=addr)
  fw.lbu(origin, launch, LAUNCH_SUB_DEVICE_ORIGIN_Y)
  fw.sub(value, value, origin)
  write8(fw, data["my_relative_y"], value, tmp_addr=addr)
  return fw


def tensix_sync(fw: Kernel):
  write32(fw, PC_BUF_SYNC, 0)
  read32(fw, t0, PC_BUF_SYNC)
  fw.and_(zero, zero, t0)
  return fw


def build(trisc_id: int) -> Kernel:
  if trisc_id not in (0, 1, 2):
    raise ValueError(f"unknown TRISC id {trisc_id!r}")
  role = 2 + trisc_id
  data = TRISC1_DATA if trisc_id == 1 else TRISC_DATA_COMMON
  fw = Kernel.firmware(f"trisc{trisc_id}")
  setup_gp(fw)
  setup_stack(fw)
  configure_csr(fw)
  init_local_data(fw, trisc_id)
  zero_regfile(fw)
  init_common_state(fw, data)
  signal_subordinate_done(fw, role)
  fw.label("run_loop")
  wait_trisc_message(fw, trisc_id)
  if trisc_id in (0, 2):
    setup_local_cbs(fw, trisc_id, data)
  init_trisc_kernel_config(fw, trisc_id, data)
  run_launch_kernel(fw, trisc_id)
  tensix_sync(fw)
  signal_subordinate_done(fw, role)
  fw.j("run_loop")
  return fw

def build_trisc0() -> Kernel:
  return build(0)

def build_trisc1() -> Kernel:
  return build(1)

def build_trisc2() -> Kernel:
  return build(2)


def write_artifacts(out_dir: Path | str | None = None) -> list[Path]:
  out = Path(__file__).resolve().parent / "build" if out_dir is None else Path(out_dir)
  out.mkdir(parents=True, exist_ok=True)
  paths = []
  for trisc_id in range(3):
    kind = f"trisc{trisc_id}"
    segments = build(trisc_id).compile()
    manifest = {"kind": kind, "segments": []}
    for i, seg in enumerate(segments):
      name = f"{kind}.seg{i}.bin"
      (out / name).write_bytes(seg.data)
      manifest["segments"].append({
        "label": seg.label,
        "addr": f"0x{seg.addr:x}",
        "bin": name,
        "filesz": len(seg.data),
        "memsz": len(seg.data),
        "flags": 5 if seg.label.endswith(".text") else 6,
      })
    manifest_path = out / f"{kind}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    paths.append(manifest_path)
  return paths


if __name__ == "__main__":
  for path in write_artifacts():
    print(path)
