import functools, hashlib, os, re, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")  # ROLE_* in hw.h
L1_SIZE = 0x180000

# Worker L1 header (hw.h). 0x0 holds `jal CODE_BASE`.
LEADER_COORD = 0x1C
NUM_WORKERS = 0x2C  # followed by the DRAM bank count and the Tensix column count
ROLE_PC = 0x60
CODE_BASE = 0x100

# DMA core L1 layout (hw.h)
PACKET, DMA_DEPTH = 0x20, 4
DMA_STATE, DMA_STATE_SIZE = 0x80, 0x100  # host-initialised block
DMA_WPTR, DMA_SIGNAL = 0x80, 0x88
DMA_BRISC_BASE, DMA_BRISC_SIZE = 0x200, 0x3E00
DMA_NCRISC_BASE, DMA_NCRISC_SIZE = 0x4000, 0x4000
DMA_PACKETS = 0x9000

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "blackhole-py-rewrite"
CFLAGS = [
  "--target=riscv32-none-unknown-elf", "-march=rv32im_zicsr", "-mabi=ilp32", "-std=c11", "-Os", "-Wall", "-Wextra",
  "-Werror", "-ffreestanding", "-fno-builtin", "-fno-pic", "-fno-common", "-fno-jump-tables", "-fno-stack-protector",
  "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-fno-delete-null-pointer-checks", "-fno-ident",
  "-msmall-data-limit=0", "-ffunction-sections", "-fdata-sections", "-mllvm", "-enable-machine-outliner=never",
  "-nostdlib", "-static", "-fuse-ld=lld", "-Wl,--gc-sections,--no-relax,--build-id=none", "-I", str(HERE),
]

def _deps(srcs: list[Path]) -> list[Path]:
  seen, todo = set(), list(srcs)
  while todo:
    if (p := todo.pop()) in seen: continue
    seen.add(p)
    for inc in re.findall(rb'^\s*#\s*include\s*"([^"]+)"', p.read_bytes(), re.M):
      todo += [q for d in (p.parent, HERE) if (q := (d / inc.decode()).resolve()).is_file()][:1]
  return sorted(seen)

def compile(srcs: list, base: int, size: int, flags: tuple[str, ...] = (), ld: str = "link.ld") -> bytes:
  srcs = [(HERE / s).resolve() for s in srcs]
  key = hashlib.sha256(repr((CFLAGS, flags, base, size, ld)).encode())
  for p in [HERE / ld, *_deps(srcs)]: key.update(p.read_bytes())
  if (out := CACHE / f"{key.hexdigest()[:24]}.bin").exists(): return out.read_bytes()
  CACHE.mkdir(parents=True, exist_ok=True)
  with tempfile.TemporaryDirectory(dir=CACHE) as d:
    for cmd in (
      ["clang", *CFLAGS, *flags, f"-Wl,--defsym=BASE={base:#x},--defsym=SIZE={size:#x}", "-T", str(HERE / ld),
       *map(str, srcs), "-o", f"{d}/fw.elf"],
      ["llvm-objcopy", "--set-section-flags", ".data=contents,alloc,load,data", "-O", "binary", f"{d}/fw.elf", f"{d}/fw.bin"],
    ):
      if (r := subprocess.run(cmd, capture_output=True, text=True)).returncode: raise RuntimeError(r.stderr or r.stdout)
    os.replace(f"{d}/fw.bin", out)
  return out.read_bytes()

@functools.cache
def dma_images(dram_banks: int) -> tuple[bytes, bytes]:
  return tuple(
    compile(["dma.c", "noc.c"], *slot, [f"-DDMA_ENGINE={i}", f"-DBANKS={dram_banks}"])
    for i, slot in enumerate(((DMA_BRISC_BASE, DMA_BRISC_SIZE), (DMA_NCRISC_BASE, DMA_NCRISC_SIZE)))
  )

def _piece(srcs: list, role: str, flags: tuple[str, ...] = ()) -> bytes:
  return compile(srcs, 0, L1_SIZE, ("-mcmodel=medany", f"-DROLE={ROLES.index(role)}", *flags), ld="boot.ld")

@functools.cache
def boot_stub(role: str) -> bytes: return _piece(["boot.c"], role)

@functools.cache
def park_epilogue(role: str) -> bytes: return _piece(["boot.c"], role, ("-DPARK",))

def pack_megakernel(images: dict[str, bytes]) -> tuple[bytes, dict[str, int], int]:
  if unknown := set(images) - set(ROLES): raise ValueError(f"unknown RISC roles: {unknown}")
  for role, code in images.items():
    if len(code) % 4: raise ValueError(f"{role} image size {len(code)} is not 4-byte aligned")
  out, pcs = bytearray(), {}
  for role in ROLES:
    body = images.get(role, b"")
    if role != "brisc" and not body: continue
    out.extend(bytes(-len(out) % 16))
    pcs[role] = CODE_BASE + len(out)
    out += boot_stub(role) + body + park_epilogue(role)
  out.extend(bytes(-len(out) % 16))
  return bytes(out), pcs, (CODE_BASE + len(out) + 63) & ~63
