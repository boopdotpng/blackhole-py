import functools, hashlib, os, re, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")  # ROLE_* in hw.h

# hw.h is the one copy of the L1 layout and MMIO addresses; its plain numeric #defines become fw.NAME here.
for _name, _value in re.findall(r"^#define (\w+) +(0x[0-9A-F]+|\d+|\(1u << \d+\))u? *(?://.*)?$", (HERE / "hw.h").read_text(), re.M):
  globals()[_name] = eval(_value.replace("u", ""), {})

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "blackhole-py-rewrite"
# Pieces are concatenated without relocation (boot.ld rejects any data); -fno-jump-tables keeps switch tables out.
CFLAGS = [
  "--target=riscv32-none-unknown-elf", "-march=rv32im_zicsr", "-mabi=ilp32", "-Os", "-Wall", "-Wextra", "-Werror",
  "-ffunction-sections", "-fno-jump-tables", "-nostdlib", "-fuse-ld=lld", "-Wl,--gc-sections,--no-relax,--build-id=none",
  "-I", str(HERE),
]
SOURCES = sorted(p for p in HERE.iterdir() if p.suffix in (".c", ".h", ".ld"))  # all of it goes in the cache key

def compile(srcs: list, base: int, size: int, flags: tuple[str, ...] = (), ld: str = "link.ld") -> bytes:
  srcs = [HERE / s for s in srcs]
  key = hashlib.sha256(repr((CFLAGS, flags, srcs, base, size, ld)).encode())
  for p in SOURCES: key.update(p.read_bytes())
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
def park_epilogue(role: str) -> bytes: return _piece(["park.c"], role)

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
