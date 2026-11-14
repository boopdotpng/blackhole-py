# Builds the firmware in this directory and mirrors the parts of fw/abi.h the host needs. Images are cached in
# ~/.cache/blackhole-py, keyed by a hash of the sources and flags.
import functools, hashlib, os, shutil, struct, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum
from pathlib import Path

class Op(IntEnum): EXEC = 0; COPY = 1; WAIT = 2; STORE = 3; TIMESTAMP = 4; CALL = 5  # noqa: E702

ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
GO_SIGNAL = 0x10
FW = {"brisc": (0x20, 0x360), "ncrisc": (0x380, 0x100), "trisc0": (0x480, 0x100), "trisc1": (0x580, 0x100),
      "trisc2": (0x680, 0x100)}
RETURN = {r: base + 4 for r, (base, _) in FW.items()}
L1_PARAM_BASE, PARAM_SIZE, LAUNCH = 0x780, 0x40, 0x7C0
assert all(a + n <= b for (a, n), (b, _) in zip(FW.values(), [*list(FW.values())[1:], (L1_PARAM_BASE, 0)])), "firmware slots overlap"
CODE = dict(zip(ROLES, (0x800, 0x2800, 0x4800, 0x6000, 0x7800)))
CODE_SIZE = dict(zip(ROLES, (0x2000, 0x2000, 0x1800, 0x1800, 0x1800)))
CODE_END = CODE["trisc2"] + CODE_SIZE["trisc2"]
SLOT_STRIDE, GO_SLOT_BIT = CODE_END - LAUNCH, 20  # slot 1 = slot 0 + SLOT_STRIDE, right after it; GO_SIGNAL bit GO_SLOT_BIT picks
DATA_BASE = CODE_END + SLOT_STRIDE  # worker L1 from here up belongs to kernels
assert L1_PARAM_BASE + PARAM_SIZE <= LAUNCH < CODE["brisc"] and (CODE_END, SLOT_STRIDE, DATA_BASE) == (0x9000, 0x8840, 0x11840)
DESCRIPTOR_L1, DESCRIPTOR_END, STAGE_SIZE = 0x40000, 0x80000, 0x10000
PACKET, RING_SIZE = 32, 64 << 10
STATE, STATE_SIZE = DATA_BASE, 0x140
WPTR, RPTR, RING_LO = STATE, STATE + 4, STATE + 8

DRAM_BANKS, DRAM_BANK_SIZE, DRAM_PAGE_MAX = 8, 4 << 30, 4096
ARC = (8, 0)
AICLK_MHZ = 1350  # set at boot and never changed; the Tensix wall clock counts these cycles
TELEMETRY_PTR, TAG_ENABLED_TENSIX_COL = 0x80030434, 34
SOFT_RESET, RESET_BRISC, RESET_ALL = 0xFFB121B0, 1 << 11, 0x47800  # brisc 11, trisc0-2 12-14, ncrisc 18

def noc(core): return core[0] | core[1] << 6

HERE = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "blackhole-py"
CFLAGS = ["--target=riscv32-none-unknown-elf", "-march=rv32im_zicsr", "-mabi=ilp32", "-std=c11", "-Wall", "-Wextra",
          "-Werror", "-ffreestanding", "-fno-builtin", "-fno-pic", "-fno-common", "-fno-jump-tables", "-fno-stack-protector",
          "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-fno-delete-null-pointer-checks", "-fno-ident",
          "-msmall-data-limit=0", "-ffunction-sections", "-fdata-sections", "-mllvm", "-enable-machine-outliner=never",
          "-nostdlib", "-static", "-fuse-ld=lld", "-Wl,--gc-sections,--no-relax,--build-id=none", "-I", str(HERE)]

SERVICE = ["queue.c", "noc.c"]
WORKERS = {  # resident firmware: name: (sources, slot, flags)
  "worker_brisc": (["worker_brisc.c", "noc.c"], FW["brisc"], ["-Oz"]),
  "worker_ncrisc": (["worker_ncrisc.c"], FW["ncrisc"], ["-Oz"]),
  **{f"worker_trisc{i}": (["worker_trisc.c"], FW[f"trisc{i}"], ["-Oz", f"-DTRISC={i}"]) for i in range(3)},
}
PROGRAMS = {  # ordinary programs, see program()
  "init": {"brisc": (["init.c"], ["-Os"])},
  "dispatch": {"brisc": (["dispatch.c", *SERVICE], ["-Os"])},
  "dma": {"brisc": (["dma.c", *SERVICE], ["-Os", "-DDMA_ENGINE=0"]), "ncrisc": (["dma.c", *SERVICE], ["-Os", "-DDMA_ENGINE=1"])},
}

def compile(srcs:list, slot:tuple[int, int], flags:list[str]=["-Os"]) -> bytes:
  """Link srcs (paths, or file names in fw/) so that section .entry starts at slot's base. Cached."""
  srcs = [Path(s) if Path(s).is_absolute() else HERE / s for s in srcs]
  deps = sorted({*srcs, *HERE.glob("*.h"), HERE / "link.ld"})
  key = hashlib.sha256(repr((CFLAGS, flags, slot, [str(p) for p in srcs])).encode() + b"".join(p.read_bytes() for p in deps))
  if (out := CACHE / f"{key.hexdigest()[:24]}.bin").exists(): return out.read_bytes()
  with tempfile.TemporaryDirectory() as d:
    cmd = [shutil.which("clang") or "clang", *CFLAGS, *flags, f"-Wl,--defsym=BASE={slot[0]:#x},--defsym=SIZE={slot[1]:#x}",
           "-T", str(HERE / "link.ld"), *map(str, srcs), "-o", f"{d}/fw.elf"]
    for c in (cmd, [shutil.which("llvm-objcopy") or "llvm-objcopy", "-O", "binary", f"{d}/fw.elf", f"{d}/fw.bin"]):
      if (r := subprocess.run(c, capture_output=True, text=True)).returncode: raise RuntimeError(r.stderr or r.stdout)
    CACHE.mkdir(parents=True, exist_ok=True)
    os.replace(shutil.copy(f"{d}/fw.bin", f"{out}.tmp"), out)
  return out.read_bytes()

def program(kernels:dict[str, tuple[list, list[str]]]) -> dict[str, bytes]:
  """Compile each role for its execution slot. A launch may run from either slot, so the image must be
  position-independent: it is linked at both and the two must match. Missing roles return immediately."""
  out = {}
  for role, (srcs, flags) in kernels.items():
    a, b = (compile(srcs, (CODE[role] + s, CODE_SIZE[role]), ["-mcmodel=medany", *flags]) for s in (0, SLOT_STRIDE))
    if a != b: raise RuntimeError(f"{role} kernel {srcs} is not position-independent")
    out[role] = a
  return out

@functools.cache
def images() -> dict:
  with ThreadPoolExecutor(len(WORKERS)) as ex: out = dict(zip(WORKERS, ex.map(lambda a: compile(*a), WORKERS.values())))
  return out | {name: program(k) for name, k in PROGRAMS.items()}

def ret(role:str) -> bytes:
  """jalr x0, RETURN[role](x0): back to the firmware from either slot. Append it to kernels that just fall off the end."""
  assert RETURN[role] < 0x800
  return (RETURN[role] << 20 | 0x67).to_bytes(4, "little")

def jal(offset:int) -> int:  # RISC-V jal x0, offset
  return (offset >> 20 & 1) << 31 | (offset >> 1 & 0x3FF) << 21 | (offset >> 11 & 1) << 20 | (offset >> 12 & 0xFF) << 12 | 0x6F
