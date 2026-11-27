import functools, hashlib, os, re, struct, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")  # ROLE_* in hw.h

# hw.h is the one copy of the L1 layout and MMIO addresses; its plain numeric #defines become fw.NAME here.
for _name, _value in re.findall(r"^#define (\w+) +(0x[0-9A-F]+|\d+|\(1u << \d+\))u? *(?://.*)?$", (HERE / "hw.h").read_text(), re.M):
  globals()[_name] = eval(_value.replace("u", ""), {})

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "blackhole-py-rewrite"
CFLAGS = [
  "--target=riscv32-none-unknown-elf", "-march=rv32im_zicsr", "-mabi=ilp32", "-Os", "-Wall", "-Wextra", "-Werror",
  "-ffunction-sections", "-fno-jump-tables", "-msmall-data-limit=0", "-nostdlib", "-fuse-ld=lld",
  "-Wl,--gc-sections,--no-relax,--build-id=none", "-I", str(HERE),
]
SOURCES = sorted(p for p in HERE.iterdir() if p.suffix in (".c", ".S", ".h", ".ld"))  # all of it goes in the cache key

# 8-byte return stub appended to every compiled role body: lw t0, -16(gp); jr t0
RET_STUB = struct.pack("<II", 0xFF01A283, 0x00028067)

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
    compile(["dma.c", "noc.c"], *slot, (f"-DDMA_ENGINE={i}", f"-DBANKS={dram_banks}"))
    for i, slot in enumerate(((DMA_BRISC_BASE, DMA_BRISC_SIZE), (DMA_NCRISC_BASE, DMA_NCRISC_SIZE)))
  )

@functools.cache
def cp_image(dram_banks: int) -> bytes:
  return compile(["cp.c", "noc.c"], CP_BRISC_BASE, CP_BRISC_SIZE, (f"-DBANKS={dram_banks}",))

@functools.cache
def worker_images(dram_banks: int) -> tuple[bytes, dict[str, int]]:
  """Build the resident 5-RISC worker image linked sequentially into [WORKER_FW_BASE..WORKER_FW_END)."""
  out, pcs = bytearray(), {}
  for idx, role in enumerate(ROLES):
    out.extend(bytes(-len(out) % 16))
    base = WORKER_FW_BASE + len(out)
    pcs[role] = base
    srcs = ["worker.c", "call.S", "noc.c"] if idx < 2 else ["worker.c", "call.S"]
    part = compile(srcs, base, WORKER_FW_END - base, (f"-DROLE={idx}", f"-DBANKS={dram_banks}"))
    out += part
  out.extend(bytes(-len(out) % 64))
  if WORKER_FW_BASE + len(out) > WORKER_FW_END:
    raise MemoryError(f"resident worker firmware ({len(out)} B) exceeds WORKER_FW_END")
  return bytes(out), pcs

def _piece(srcs: list, role: str, flags: tuple[str, ...] = ()) -> bytes:
  return compile(srcs, 0, L1_SIZE, ("-mcmodel=medany", f"-DROLE={ROLES.index(role)}", *flags), ld="boot.ld")

@functools.cache
def boot_stub(role: str) -> bytes: return _piece(["boot.c", "noc.c"], role)

@functools.cache
def park_epilogue(role: str) -> bytes: return _piece(["park.c", "noc.c"], role)

def pack_kernel(images: dict[str, bytes], cb_mask: int = 0xFFFFFFFF) -> tuple[bytes, int]:
  """Pack per-role compiled bodies with RET_STUB + 64-byte HCQ2 program header; returns (blob, prog_key)."""
  return _pack_kernel(tuple(sorted(images.items())), cb_mask)

@functools.lru_cache(maxsize=512)
def _pack_kernel(items: tuple[tuple[str, bytes], ...], cb_mask: int) -> tuple[bytes, int]:
  images = dict(items)
  if unknown := set(images) - set(ROLES): raise ValueError(f"unknown RISC roles: {unknown}")
  for role, code in images.items():
    if len(code) % 4: raise ValueError(f"{role} image size {len(code)} is not 4-byte aligned")
  body, offs = bytearray(), [0] * 5
  for idx, role in enumerate(ROLES):
    code = images.get(role, b"")
    if not code: continue
    body.extend(bytes(-len(body) % 16))
    offs[idx] = PROG_HDR_BYTES + len(body)
    body += code + RET_STUB
  body.extend(bytes(-len(body) % 64))
  if len(body) > CODE_CACHE_END - CODE_CACHE_BASE:
    raise MemoryError(f"kernel code ({len(body)} B) exceeds L1 program cache")
  hdr = bytearray(PROG_HDR_BYTES)
  struct.pack_into("<6I", hdr, 0, *offs, cb_mask & 0xFFFFFFFF)
  blob = bytes(hdr) + bytes(body)
  key = int.from_bytes(hashlib.sha256(blob).digest()[:4], "little") or 1
  return blob, key

def pack_megakernel(images: dict[str, bytes]) -> tuple[bytes, dict[str, int], int]:
  return _pack_megakernel(tuple(images.items()))

@functools.lru_cache(maxsize=256)
def _pack_megakernel(items: tuple[tuple[str, bytes], ...]) -> tuple[bytes, dict[str, int], int]:
  images = dict(items)
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
  if CODE_BASE + len(out) > MCAST_CTRL_BASE: raise MemoryError("worker image overlaps multicast control words")
  return bytes(out), pcs, (CODE_BASE + len(out) + 63) & ~63
