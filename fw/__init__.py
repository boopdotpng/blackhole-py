# Firmware build and the host <-> firmware ABI. Every uppercase int here is exported to the C side as abi.h.
#
# Two service cores run the queues, both entered as ordinary kernels through the worker firmware every core boots:
#   CQ_CORE   BRISC dispatch + NCRISC prefetch, the COMPUTE queue (EXEC, WAIT, STORE, TIMESTAMP)
#   DMA_CORE  BRISC + NCRISC both copy, the COPY queue (COPY, WAIT, STORE, TIMESTAMP)
# Each queue is a ring of 32-byte packets in sysmem, [op, a, b, c] as u64s, the same shape as tinygrad's NullQueue.
import functools, shutil, struct, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum
from pathlib import Path
from pcie import DRAM, jal

class Op(IntEnum): EXEC = 0; COPY = 1; WAIT = 2; STORE = 3; TIMESTAMP = 4  # noqa: E702  (tinygrad ops_null.py)

def noc(core): return core[0] | core[1] << 6

ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
CQ_CORE, DMA_CORE = (14, 3), (14, 4)
DISPATCH_COORD = noc(CQ_CORE)
PCIE_COORD = (1 << 24) | (24 << 6) | 19
DRAM_PAGE_MAX = 4096  # a DRAM page is one tile, 1024 elements: 1 KB fp8, 2 KB bf16, 4 KB fp32
NOC_MAX_BURST = 16 << 10
PACKET, RING_SIZE = 32, 64 << 10

# ---- L1, every core ----
# 0x0000    BRISC reset vector (hardware): pcie.boot puts a jal to FW["brisc"] here
# 0x0010    GO: a word, 0x80 launches the kernels, firmware zeroes it when they are done
# 0x0014    SUBORDINATE_SYNC: a byte per ncrisc, trisc0-2: 2 boot ready, 0x80 go, 0 done
# 0x0100    FW: resident worker firmware, one image per RISC. FW + 0 boots, FW + 4 is where a kernel returns to
# 0x1000    PARAMS: the kernel arguments EXEC writes, 4 KB
# 0x2000    ZEROS: 512 bytes of zeros
# 0x4000    KERNEL: one fixed slot per RISC, a kernel starts at its first byte
# 0x12000   free for data (on the service cores: STATE, the L1 ring copy, DMA staging)
GO_SIGNAL, SUBORDINATE_SYNC = 0x10, 0x14
FW = {"brisc": (0x100, 0x500), "ncrisc": (0x600, 0x100), "trisc0": (0x700, 0x100), "trisc1": (0x800, 0x100), "trisc2": (0x900, 0x100)}
RETURN = {role: base + 4 for role, (base, _) in FW.items()}
L1_PARAM_BASE, PARAM_SIZE = 0x1000, 0x1000
L1_MEM_ZEROS_BASE, L1_MEM_ZEROS_SIZE = 0x2000, 0x200
KERNEL = {"brisc": (0x4000, 0x6000), "ncrisc": (0xA000, 0x2000), "trisc0": (0xC000, 0x3000), "trisc1": (0xF000, 0x2000),
          "trisc2": (0x11000, 0x1000)}
DATA_BASE, L1_SIZE = 0x12000, 0x180000
STACK_TOP, TRISC_STACK_TOP, TRISC_GLOBAL_POINTER = 0xFFB01FF0, 0xFFB00FF0, 0xFFB007F0
MMIO_CFG_BASE = 0xFFEF0000
MMIO_RISCV_DEBUG_REG_WALL_CLOCK_L, MMIO_RISCV_DEBUG_REG_WALL_CLOCK_H = 0xFFB121F0, 0xFFB121F8

# ---- service L1 (CQ_CORE, DMA_CORE). the host zeroes STATE and fills RING_LO/HI before GO ----
STATE = DATA_BASE
WPTR = STATE + 0x00  # host -> fw: bytes pushed, the doorbell
RPTR = STATE + 0x04  # fw -> host: bytes retired
RING_LO, RING_HI = STATE + 0x08, STATE + 0x0C  # NoC address of this queue's sysmem ring
GO_WORD = STATE + GO_SIGNAL  # CQ: multicast source of GO, the same offset in its 64 bytes
FETCHED = STATE + 0x20  # CQ: prefetch -> dispatch, bytes copied into L1_RING
DMA_DONE = STATE + 0x24  # DMA: packets finished per engine, 2 words
DISPATCH_DONE_COUNT = STATE + 0x30  # CQ: workers atomic-increment this when their kernels return
SCRATCH = STATE + 0x40  # 0x80 per RISC: signal values and polled words
STATE_SIZE = 0x140
# CQ core. EXEC's args are [rect count, core count, 5 kernel sizes, up to 9 rects] padded to ARGS_HEADER, then the params
L1_RING = 0x20000
ARGS_HEADER, ARGS_SIZES, ARGS_RECTS = 64, 2, 7  # header bytes, then word offsets of the sizes and the rects
ARGS_L1, ARGS_MAX = 0x30000, ARGS_HEADER + PARAM_SIZE
PROG_L1, PROG_MAX = 0x34000, KERNEL["trisc2"][0] + KERNEL["trisc2"][1] - KERNEL["brisc"][0]
# DMA core, per engine: two staging halves, then the fetched packets
DMA_BATCH, DMA_PACKETS_MAX = 128 << 10, 0x800
DMA_STAGING, DMA_STAGING_STRIDE = 0x20000, 0x48000
assert DMA_STAGING + 2 * DMA_STAGING_STRIDE <= L1_SIZE and 2 * DMA_BATCH + 64 + DMA_PACKETS_MAX <= DMA_STAGING_STRIDE

HERE = Path(__file__).resolve().parent

def _tool(*names):
  for n in names:
    if path := shutil.which(n): return path
  raise RuntimeError(f"firmware needs one of {names}")

def _abi(banks):
  vals = {k: v for k, v in globals().items() if k.isupper() and type(v) is int}
  vals |= {f"OP_{o.name}": int(o) for o in Op} | {"BANKS": banks}
  for r in ROLES: vals |= {f"FW_{r.upper()}": FW[r][0], f"FW_{r.upper()}_RETURN": RETURN[r], f"KERNEL_{r.upper()}": KERNEL[r][0]}
  return "".join(f"#define {k} {v:#x}u\n" for k, v in sorted(vals.items())) + \
    f"#define DRAM_COORDS {{{', '.join(hex(noc(c)) for c in DRAM[:banks])}}}\n"

def compile(src, base, capacity, banks=len(DRAM), opt="-Os", **defines) -> bytes:
  """Link src at base. Whatever is in section .entry comes first: a kernel's entry, or a resident firmware's stubs."""
  cc, ld, objcopy = _tool("clang"), _tool("riscv64-linux-gnu-ld", "ld.lld"), _tool("llvm-objcopy", "riscv64-linux-gnu-objcopy")
  with tempfile.TemporaryDirectory(prefix="bh-fw-") as d:
    out = Path(d)
    (out / "abi.h").write_text(_abi(banks))
    flags = ["--target=riscv32-none-unknown-elf", "-march=rv32im_zicsr", "-mabi=ilp32", "-mllvm", "-enable-machine-outliner=never",
             "-std=c11", opt, "-Wall", "-Wextra", "-Werror", "-Wno-unused-function", "-I", d, "-I", str(HERE), "-ffreestanding",
             "-fno-builtin", "-fno-delete-null-pointer-checks", "-fno-stack-protector", "-fno-unwind-tables",
             "-fno-asynchronous-unwind-tables", "-fno-pic", "-msmall-data-limit=0", "-ffunction-sections", "-fdata-sections",
             "-fno-jump-tables", "-fno-common", "-fno-ident", *[f"-D{k}={v}" for k, v in defines.items()]]
    for cmd in ([cc, *flags, "-c", str(src), "-o", out / "fw.o"],
                [ld, "-m", "elf32lriscv", "-T", HERE / "link.ld", "--gc-sections", "--no-relax", "--build-id=none",
                 f"--defsym=BASE={base:#x}", f"--defsym=CAPACITY={capacity:#x}", out / "fw.o", "-o", out / "fw.elf"],
                [objcopy, "-O", "binary", out / "fw.elf", out / "fw.bin"]):
      if (r := subprocess.run(list(map(str, cmd)), capture_output=True, text=True)).returncode:
        raise RuntimeError(f"{Path(src).name}: {r.stderr or r.stdout}")
    return (out / "fw.bin").read_bytes()

def return_stub(role:str) -> bytes:  # a kernel that returns straight away: every RISC must return before BRISC reports done
  return struct.pack("<I", jal(RETURN[role] - KERNEL[role][0]))

@functools.cache
def build(banks=len(DRAM)) -> dict:
  """{"workers": the resident firmware for all five worker RISCs, loaded at FW["brisc"][0] and booted on BRISC,
      (core, risc): a service loop, loaded at KERNEL[risc][0] and launched on GO like any kernel}"""
  jobs = {}
  for i, role in enumerate(ROLES):
    trisc = role.startswith("trisc")
    d = dict(TT_WORKER_INDEX=i, TT_KERNEL=KERNEL[role][0], TT_FW_STACK_TOP=TRISC_STACK_TOP if trisc else STACK_TOP)
    if trisc: d |= dict(TT_TRISC_ID=i - 2, TT_FW_GLOBAL_POINTER=TRISC_GLOBAL_POINTER)
    jobs[role] = (HERE / "worker.c", *FW[role], banks, "-Oz"), d
  for core, src in ((CQ_CORE, "cq.c"), (DMA_CORE, "dram.c")):
    for risc, role in enumerate(("brisc", "ncrisc")): jobs[(core, role)] = (HERE / src, *KERNEL[role], banks), dict(TT_FW_RISC=risc)
  with ThreadPoolExecutor(len(jobs)) as ex: images = dict(zip(jobs, ex.map(lambda j: compile(*j[0], **j[1]), jobs.values())))
  workers = b""
  for role in ROLES: workers = workers.ljust(FW[role][0] - FW["brisc"][0], b"\0") + images.pop(role)
  return {"workers": workers, **images}
