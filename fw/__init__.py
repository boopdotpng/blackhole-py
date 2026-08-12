from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Literal
import os
import shutil
import subprocess
import tempfile


Core = tuple[int, int]
KernelRole = Literal["brisc", "ncrisc", "trisc0", "trisc1", "trisc2"]
KERNEL_ROLES: tuple[KernelRole, ...] = (
  "brisc", "ncrisc", "trisc0", "trisc1", "trisc2",
)


class TensixL1:
  SIZE = 0x180000
  BOOT = 0
  BOOT_SIZE = 4
  MEM_ZEROS_BASE = 0x2BB8
  MEM_ZEROS_SIZE = 0x200
  PARAM_BASE = 0x3FD0
  PARAM_SIZE = 0x30
  PARAM_SLOTS = PARAM_SIZE // 4

  WORKER_TEXT_BASE = {
    "brisc": 0x04000,
    "ncrisc": 0x0A000,
    "trisc0": 0x0C000,
    "trisc1": 0x0F000,
    "trisc2": 0x11000,
  }
  WORKER_TEXT_SIZE = {
    "brisc": 0x6000,
    "ncrisc": 0x2000,
    "trisc0": 0x3000,
    "trisc1": 0x2000,
    "trisc2": 0x1000,
  }
  KERNEL_CACHE_BASE = 0x12000
  KERNEL_CACHE_END = 0x42000
  WORKER_ENTRY_BASE = SIZE - 0x20
  DATA_BUFFER_SPACE_BASE = KERNEL_CACHE_END
  DATA_BUFFER_SPACE_END = WORKER_ENTRY_BASE


class Firmware:
  BRISC_STACK_TOP = NCRISC_STACK_TOP = 0xFFB01FF0
  TRISC_STACK_TOP = 0xFFB00FF0
  TRISC_GLOBAL_POINTER = 0xFFB007F0
  NOC_COORDINATE_BASE = {
    "brisc": (0xFFB00008, 0xFFB00004),
    "ncrisc": (0xFFB00030, 0xFFB0002C),
  }
  LOCAL_MEMORY = {
    "brisc": (0xFFB00878, 0xFFB01F00),
    "ncrisc": (0xFFB00864, 0xFFB01F00),
    "trisc0": (0xFFB00820, 0xFFB00F40),
    "trisc1": (0xFFB00140, 0xFFB00F40),
    "trisc2": (0xFFB008C0, 0xFFB00F00),
  }
  ELF_DATA_SIZE = 0x100
  TEXT_CODE_SIZE = {
    "brisc": 0x07C0,
    "ncrisc": 0x00D8,
    "trisc0": 0x0180,
    "trisc1": 0x0180,
    "trisc2": 0x0180,
  }
  TEXT = {
    "brisc": (0x2DB8, TEXT_CODE_SIZE["brisc"] + ELF_DATA_SIZE),
    "ncrisc": (0x3678, TEXT_CODE_SIZE["ncrisc"] + ELF_DATA_SIZE),
    "trisc0": (0x3850, TEXT_CODE_SIZE["trisc0"] + ELF_DATA_SIZE),
    "trisc1": (0x3AD0, TEXT_CODE_SIZE["trisc1"] + ELF_DATA_SIZE),
    "trisc2": (0x3D50, TEXT_CODE_SIZE["trisc2"] + ELF_DATA_SIZE),
  }


class RunState(IntEnum):
  DONE = 0x00
  BOOT_READY = 0x02
  GO = 0x80
  ALL_INIT = 0x40404040


class FirmwareControl:
  SUBORDINATE_SYNC = 0x0068
  GO_SIGNAL = 0x0373


class TensixMMIO:
  LOCAL_RAM_START = 0xFFB00000
  LOCAL_RAM_END = 0xFFB01FFF
  REGFILE_BASE = 0xFFE00000
  INSTRN_BUF_BASE = 0xFFE40000
  PC_BUF_SYNC = 0xFFE80004
  PC_BUF_MOP_SYNC = 0xFFE80008
  CFG_BASE = 0xFFEF0000
  ECC_SCRUBBER = CFG_BASE + 0xC
  PRNG_SEED_SEED_VAL = CFG_BASE + 186 * 4
  RISCV_IC_INVALIDATE = CFG_BASE + 185 * 4
  RISCV_IC_ALL_MASK = 0x1F
  NCRISC_HALT_RESUME_ADDR = 0x60
  RISCV_DEBUG_REG_SOFT_RESET_0 = 0xFFB121B0
  RISCV_TDMA_REG_CLK_GATE_EN = 0xFFB11024
  RISCV_DEBUG_REG_TRISC0_RESET_PC = 0xFFB12228
  RISCV_DEBUG_REG_TRISC1_RESET_PC = 0xFFB1222C
  RISCV_DEBUG_REG_TRISC2_RESET_PC = 0xFFB12230
  RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE = 0xFFB12234
  RISCV_DEBUG_REG_NCRISC_RESET_PC = 0xFFB12238
  RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE = 0xFFB1223C
  RISCV_DEBUG_REG_DEST_CG_CTRL = 0xFFB12240
  SOFT_RESET_ALL = 0x47800
  SOFT_RESET_BRISC_ONLY_RUN = 0x47000


@dataclass(frozen=True)
class FirmwareImages:
  workers: tuple[bytes, ...]
  prefetch: bytes
  dispatch: bytes
  dma_brisc: bytes
  dma_ncrisc: bytes


_ROOT = Path(__file__).parent
_LINKER_SCRIPT = _ROOT / "firmware.ld"


def _tool(environment, candidates):
  if configured := os.getenv(environment):
    if path := shutil.which(configured): return path
    raise RuntimeError(f"{environment} names unavailable executable {configured!r}")
  for candidate in candidates:
    if path := shutil.which(candidate): return path
  raise RuntimeError(f"firmware build requires one of: {', '.join(candidates)}")


def _run(command, action, source):
  try:
    subprocess.run(command, check=True, capture_output=True, text=True)
  except (FileNotFoundError, subprocess.CalledProcessError) as error:
    detail = getattr(error, "stderr", "").strip() or getattr(error, "stdout", "").strip()
    raise RuntimeError(
      f"failed to {action} {source.name}: {detail or str(error)}",
    ) from error


def _compile(source, base, capacity, defines=(), *, text_capacity=None,
             data_capacity=None):
  compiler = _tool("CC", (
    "clang", "riscv32-unknown-elf-gcc", "riscv64-linux-gnu-gcc",
  ))
  linker = _tool("TT_RISCV_LD", (
    "riscv32-unknown-elf-ld", "riscv64-linux-gnu-ld", "ld.lld",
  ))
  objcopy = _tool("TT_RISCV_OBJCOPY", (
    "riscv32-unknown-elf-objcopy", "riscv64-linux-gnu-objcopy", "llvm-objcopy",
  ))
  text_capacity = capacity if text_capacity is None else text_capacity
  data_capacity = capacity if data_capacity is None else data_capacity
  with tempfile.TemporaryDirectory(prefix="blackhole-fw-") as directory:
    output = Path(directory)
    obj, elf, binary = (
      output / f"{source.stem}.o",
      output / f"{source.stem}.elf",
      output / f"{source.stem}.bin",
    )
    target = ["--target=riscv32-none-unknown-elf"] if "clang" in Path(compiler).name.lower() else []
    flags = [
      *target, "-march=rv32im_zicsr", "-mabi=ilp32", "-std=c11", "-Os",
      "-finline-functions", "-ffreestanding", "-fno-builtin",
      "-fno-math-errno", "-fno-ident", "-fno-stack-protector",
      "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
      "-fno-pic", "-fno-pie", "-msmall-data-limit=0",
      "-ffunction-sections", "-fdata-sections", "-fjump-tables",
      "-fno-common",
    ]
    definitions = [
      f"-D{name}={hex(value) if isinstance(value, int) else value}"
      for name, value in defines
    ]
    _run([
      compiler, *flags, *definitions, "-c", str(source), "-o", str(obj),
    ], "compile", source)
    _run([
      linker, "-m", "elf32lriscv", "-T", str(_LINKER_SCRIPT),
      "--gc-sections", "--no-relax", "--build-id=none",
      f"--defsym=TT_IMAGE_BASE={base:#x}",
      "--defsym=TT_TEXT_OFFSET=0x10",
      f"--defsym=TT_IMAGE_CAPACITY={capacity:#x}",
      f"--defsym=TT_TEXT_CAPACITY={text_capacity:#x}",
      f"--defsym=TT_DATA_CAPACITY={data_capacity:#x}",
      str(obj), "-o", str(elf),
    ], "link", source)
    _run([objcopy, "-O", "binary", str(elf), str(binary)], "extract", source)
    image = binary.read_bytes()
  if not image or len(image) > capacity:
    raise RuntimeError(
      f"firmware {source.name} produced invalid {len(image):#x}-byte image",
    )
  return image


def build(pcie_mid, dram_tiles):
  """Compile fixed-address firmware immediately before device upload."""
  dram_tiles = tuple(dram_tiles)
  dram_banks = len(dram_tiles)
  if dram_banks not in (7, 8):
    raise ValueError(f"unsupported Blackhole DRAM bank count {dram_banks}")
  prefetch_coord = 14 | 2 << 6
  dispatch_coord = 14 | 3 << 6
  sources = {
    "brisc": "brisc.c", "ncrisc": "ncrisc.c",
    "trisc0": "trisc.c", "trisc1": "trisc.c", "trisc2": "trisc.c",
  }
  workers = []
  for role_index, role in enumerate(KERNEL_ROLES):
    stack = Firmware.TRISC_STACK_TOP if role.startswith("trisc") else Firmware.BRISC_STACK_TOP
    defines = [
      ("TT_FW_RESIDENT", 1), ("TT_FW_STACK_TOP", stack),
      ("TT_WORKER_ENTRY_SLOT", TensixL1.WORKER_ENTRY_BASE + role_index * 4),
    ]
    if role == "brisc": defines += [
      ("TT_FW_INVALIDATE_ON_BOOT", 1),
      ("TT_DISPATCH_COORD", dispatch_coord),
    ]
    if role.startswith("trisc"): defines += [
      ("TT_TRISC_ID", int(role[-1])),
      ("TT_FW_GLOBAL_POINTER", Firmware.TRISC_GLOBAL_POINTER),
    ]
    workers.append(_compile(
      _ROOT / sources[role], Firmware.TEXT[role][0], Firmware.TEXT[role][1],
      defines, text_capacity=Firmware.TEXT_CODE_SIZE[role],
      data_capacity=Firmware.ELF_DATA_SIZE,
    ))

  common = (
    ("TT_PCIE_MID", pcie_mid),
    ("TT_FW_STACK_TOP", Firmware.BRISC_STACK_TOP),
    ("TT_FW_INVALIDATE_ON_BOOT", 1),
  )
  prefetch = _compile(
    _ROOT / "prefetch.c", TensixL1.WORKER_TEXT_BASE["brisc"],
    TensixL1.WORKER_TEXT_SIZE["brisc"],
    common + (("TT_DISPATCH_COORD", dispatch_coord),),
  )
  dispatch = _compile(
    _ROOT / "dispatch.c", TensixL1.WORKER_TEXT_BASE["brisc"],
    TensixL1.WORKER_TEXT_SIZE["brisc"],
    common + (("TT_PREFETCH_COORD", prefetch_coord),),
  )

  dram_defines = [("TT_DRAM_BANKS", dram_banks)]
  for bank, (x, y) in enumerate(dram_tiles):
    dram_defines.append((f"TT_DRAM_{bank}", x | y << 6))

  dma_brisc = _compile(
    _ROOT / "dma.c", TensixL1.WORKER_TEXT_BASE["brisc"],
    TensixL1.WORKER_TEXT_SIZE["brisc"], dram_defines + [
      ("TT_FW_RISC", 0), ("TT_FW_STACK_TOP", Firmware.BRISC_STACK_TOP),
      ("TT_FW_INVALIDATE_ON_BOOT", 1),
    ],
  )
  dma_ncrisc = _compile(
    _ROOT / "dma.c", TensixL1.WORKER_TEXT_BASE["ncrisc"],
    TensixL1.WORKER_TEXT_SIZE["ncrisc"], dram_defines + [
      ("TT_FW_RISC", 1), ("TT_FW_STACK_TOP", Firmware.NCRISC_STACK_TOP),
    ],
  )
  return FirmwareImages(
    tuple(workers), prefetch, dispatch, dma_brisc, dma_ncrisc,
  )
