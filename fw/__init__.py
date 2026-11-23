import functools, hashlib, os, re, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

def _defines(*headers:str) -> dict[str, int]:
  """Object-like integer #defines from the firmware headers, so Python and C share one layout."""
  out = {}
  for h in headers:
    for name, expr in re.findall(r"^#define\s+(\w+)\s+([\w\s()+*<>|&~-]+?)\s*(?://.*)?$", (HERE / h).read_text(), re.M):
      try: out[name] = eval(re.sub(r"(?<=[0-9a-fA-F])u\b", "", expr), {}, dict(out))
      except (NameError, SyntaxError): pass
  return out

globals().update(DEFINES := _defines("abi.h", "hw.h"))

ROLE_FLAGS = {"brisc": "-DROLE_BRISC", "ncrisc": "-DROLE_NCRISC", **{f"trisc{i}": f"-DROLE_TRISC={i}" for i in range(3)}}
ROLES = tuple(ROLE_FLAGS)

DRAM_BANK_SIZE, DRAM_PAGE_MAX = 0xFF000000, 4096
ARC = (8, 0)
AICLK_MHZ = 1350
TELEMETRY_DATA, TELEMETRY_PTR, TAG_ENABLED_TENSIX_COL = 0x80030430, 0x80030434, 34
NOC_NODE_ID = 0xFFB20044  # physical NoC0 coords; NOC_ID_LOGICAL (0xFFB20148) is the translated one

def noc(core:tuple[int, int]) -> int: return core[0] | core[1] << 6

def jal(offset:int) -> int:
  return (offset >> 20 & 1) << 31 | (offset >> 1 & 0x3FF) << 21 | (offset >> 11 & 1) << 20 | (offset >> 12 & 0xFF) << 12 | 0x6F

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "blackhole-py-rewrite"
CFLAGS = ["--target=riscv32-none-unknown-elf", "-march=rv32im_zicsr", "-mabi=ilp32", "-std=c11", "-Os", "-Wall", "-Wextra",
          "-Werror", "-ffreestanding", "-fno-builtin", "-fno-pic", "-fno-common", "-fno-jump-tables", "-fno-stack-protector",
          "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-fno-delete-null-pointer-checks", "-fno-ident",
          "-msmall-data-limit=0", "-ffunction-sections", "-fdata-sections", "-mllvm", "-enable-machine-outliner=never",
          "-nostdlib", "-static", "-fuse-ld=lld", "-Wl,--gc-sections,--no-relax,--build-id=none", "-I", str(HERE)]

def _deps(srcs:list[Path]) -> list[Path]:
  seen, todo = set(), list(srcs)
  while todo:
    if (p := todo.pop()) in seen: continue
    seen.add(p)
    for inc in re.findall(rb'^\s*#\s*include\s*"([^"]+)"', p.read_bytes(), re.M):
      todo += [q for d in (p.parent, HERE) if (q := (d / inc.decode()).resolve()).is_file()][:1]
  return sorted(seen)

def compile(srcs:list, base:int, size:int, flags:list[str]=[]) -> bytes:
  srcs = [(HERE / s).resolve() for s in srcs]
  key = hashlib.sha256(repr((CFLAGS, flags, base, size)).encode())
  for p in [HERE / "link.ld", *_deps(srcs)]: key.update(p.read_bytes())
  if (out := CACHE / f"{key.hexdigest()[:24]}.bin").exists(): return out.read_bytes()
  CACHE.mkdir(parents=True, exist_ok=True)
  with tempfile.TemporaryDirectory(dir=CACHE) as d:
    for cmd in (["clang", *CFLAGS, *flags, f"-Wl,--defsym=BASE={base:#x},--defsym=SIZE={size:#x}", "-T", str(HERE / "link.ld"),
                 *map(str, srcs), "-o", f"{d}/fw.elf"],
                ["llvm-objcopy", "--set-section-flags", ".data=contents,alloc,load,data", "-O", "binary", f"{d}/fw.elf", f"{d}/fw.bin"]):
      if (r := subprocess.run(cmd, capture_output=True, text=True)).returncode: raise RuntimeError(r.stderr or r.stdout)
    os.replace(f"{d}/fw.bin", out)
  return out.read_bytes()

@functools.cache
def service_images(dram_banks:int) -> tuple[bytes, bytes]:
  return tuple(compile(["service.c", "noc.c"], *slot, [f"-DSVC_ENGINE={i}", f"-DBANKS={dram_banks}"])
               for i, slot in enumerate(((SVC_BRISC_BASE, SVC_BRISC_SIZE), (SVC_NCRISC_BASE, SVC_NCRISC_SIZE))))

def build_worker(srcs:list, roles=("brisc",), dram_banks:int=8, max_size:int=0x40000) -> tuple[bytes, dict[str, int], int]:
  assert "brisc" in roles
  image, pcs = bytearray(), {}
  for role in (r for r in ROLES if r in roles):
    pcs[role] = base = CODE_BASE + len(image)
    image += compile([*srcs, "noc.c"], base, CODE_BASE + max_size - base, [f"-DBANKS={dram_banks}", ROLE_FLAGS[role]])
    image += bytes(-len(image) % 16)
  return bytes(image), pcs, (CODE_BASE + len(image) + 63) & ~63

# TTRV kernels preload gp at the midpoint of private memory. The worker call
# trampoline stores its return PC there before entering the register allocator's ABI.
DRAM_BANKS = 8
def ret(role):
  return bytes.fromhex("83a20100 67800200")  # lw t0,0(gp); jr t0
