import functools, hashlib, os, re, subprocess, tempfile
from pathlib import Path
import hw

HERE = Path(__file__).resolve().parent

def _write_header():
  # fw/hw.h is hw/__init__.py as C: every int constant, the role indexes, and the NoC coordinate of each DRAM port.
  ports = ", ".join("{" + ", ".join(f"{hw.dram_coord(b, p):#x}" for p in range(3)) + "}" for b in range(hw.DRAM_BANKS))
  text = "// Generated from hw/__init__.py by fw/__init__.py. Do not edit.\n#pragma once\n" + "".join(
    f"#define {k} {v}\n" for k, v in (
      *((k, f"0x{v:X}") for k, v in vars(hw).items() if k.isupper() and type(v) is int),
      *((f"ROLE_{r.upper()}", i) for i, r in enumerate(hw.ROLES)),
      ("DRAM_PORT_COORDS", "{" + ports + "}"),
    ))
  if not (out := HERE / "hw.h").exists() or out.read_text() != text: out.write_text(text)


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
  _write_header()
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
def service_images(dram_banks: int) -> tuple[bytes, bytes]:
  return tuple(
    compile(["service.c", "noc.c"], *slot, [f"-DSVC_ENGINE={i}", f"-DBANKS={dram_banks}"])
    for i, slot in enumerate(((hw.SVC_BRISC_BASE, hw.SVC_BRISC_SIZE), (hw.SVC_NCRISC_BASE, hw.SVC_NCRISC_SIZE)))
  )


# ---- worker megakernels: [boot stub][kernel body][park epilogue] per launched role, see boot.c ----

def _piece(srcs: list, role: str, flags: tuple[str, ...] = ()) -> bytes:
  # Position independent: linked at 0, placed wherever pack_megakernel puts it.
  return compile(srcs, 0, hw.L1_SIZE, ("-mcmodel=medany", f"-DROLE={hw.ROLES.index(role)}", *flags), ld="boot.ld")


@functools.cache
def boot_stub(role: str) -> bytes: return _piece(["boot.c"], role)


@functools.cache
def park_epilogue(role: str) -> bytes: return _piece(["boot.c"], role, ("-DPARK",))


def pack_megakernel(images: dict[str, bytes]) -> tuple[bytes, dict[str, int], int]:
  # -> (image at CODE_BASE, boot pc per role, 64-aligned end of code in L1). BRISC always boots; it releases the
  # subordinates whose ROLE_PC (written by Device.run from these pcs) is nonzero.
  if unknown := set(images) - set(hw.ROLES): raise ValueError(f"unknown RISC roles: {unknown}")
  for role, code in images.items():
    if len(code) % 4: raise ValueError(f"{role} image size {len(code)} is not 4-byte aligned")
  out, pcs = bytearray(), {}
  for role in hw.ROLES:
    body = images.get(role, b"")
    if role != "brisc" and not body: continue
    out.extend(bytes(-len(out) % 16))
    pcs[role] = hw.CODE_BASE + len(out)
    out += boot_stub(role) + body + park_epilogue(role)
  out.extend(bytes(-len(out) % 16))
  return bytes(out), pcs, (hw.CODE_BASE + len(out) + 63) & ~63
