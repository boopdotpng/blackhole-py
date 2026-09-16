from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import struct
import tempfile
import sys
from fw import abi
from fw.consts import CQConfig, FirmwareControl, TensixMMIO

from fw.consts import Firmware, KERNEL_ROLES, TensixL1


SOURCE_DIR = Path(__file__).resolve().parent
LINKER_SCRIPT = SOURCE_DIR / "firmware.ld"


@dataclass(frozen=True)
class FirmwareImages:
  workers: tuple[bytes, ...]
  prefetch: bytes
  dispatch: bytes
  dram_brisc: bytes
  dram_ncrisc: bytes


def _tool(env_name, candidates):
  configured = os.getenv(env_name)
  if configured:
    if path := shutil.which(configured): return path
    raise RuntimeError(f"{env_name} names unavailable executable {configured!r}")
  for candidate in candidates:
    if path := shutil.which(candidate): return path
  raise RuntimeError(
    f"C firmware requires one of: {', '.join(candidates)}; "
    f"set {env_name} to override the executable"
  )


def _image_layout(
  elf, base, capacity, text_capacity, data_capacity, entry_offset,
):
  if len(elf) < 52 or elf[:4] != b"\x7fELF" or elf[4:6] != b"\x01\x01":
    raise RuntimeError("firmware compiler did not produce a little-endian ELF32 file")
  section_offset = struct.unpack_from("<I", elf, 32)[0]
  section_size, section_count, names_index = struct.unpack_from("<HHH", elf, 46)
  if (
    section_size < 40 or names_index >= section_count or
    section_offset + section_size * section_count > len(elf)
  ):
    raise RuntimeError("firmware compiler produced malformed ELF section headers")
  raw_sections = [
    struct.unpack_from("<IIIIIIIIII", elf, section_offset + i * section_size)
    for i in range(section_count)
  ]
  names_header = raw_sections[names_index]
  names = elf[names_header[4]:names_header[4] + names_header[5]]
  sections = []
  for section in raw_sections:
    name_start = section[0]
    name_end = names.find(b"\0", name_start)
    if name_start and name_end < 0:
      raise RuntimeError("firmware compiler produced a malformed ELF string table")
    name = names[name_start:name_end].decode() if name_start else ""
    sections.append((name, *section[1:]))

  write, alloc, execute, nobits = 0x1, 0x2, 0x4, 8
  expected_flags = {
    ".entry": alloc | execute,
    ".text": alloc | execute,
    ".rodata": alloc,
    ".data": alloc | write,
    ".bss": alloc | write,
  }
  image_end = content_end = base
  allocated = {}
  for section in sections:
    name, section_type, flags, address, _, size, *_ = section
    if size and section_type in (4, 9):
      raise RuntimeError(f"firmware contains unresolved relocation section {name!r}")
    if not size or not flags & alloc: continue
    if name not in expected_flags:
      raise RuntimeError(f"firmware contains unsupported allocated section {name!r}")
    if flags & (write | alloc | execute) != expected_flags[name]:
      raise RuntimeError(f"firmware section {name!r} has unsupported flags {flags:#x}")
    if name == ".bss" and section_type != nobits:
      raise RuntimeError("firmware .bss section must not occupy ELF file data")
    if not base <= address or address + size > base + capacity:
      raise RuntimeError(
        f"firmware section {name!r} at {address:#x}..{address + size:#x} "
        f"falls outside image {base:#x}..{base + capacity:#x}"
      )
    allocated[name] = (address, size)
    image_end = max(image_end, address + size)
    if section_type != nobits: content_end = max(content_end, address + size)
  for name in (".entry", ".text"):
    if name in allocated and allocated[name][0] + allocated[name][1] > base + text_capacity:
      raise RuntimeError(
        f"firmware section {name!r} exceeds its {text_capacity:#x}-byte "
        "program region"
      )
  data_sections = [
    allocated[name] for name in (".rodata", ".data", ".bss")
    if name in allocated
  ]
  if data_sections:
    data_start = min(address for address, _ in data_sections)
    if image_end - data_start > data_capacity:
      raise RuntimeError(
        f"firmware data uses {image_end - data_start:#x} bytes, exceeds "
        f"its {data_capacity:#x}-byte allowance"
      )

  expected_entry = base + entry_offset
  actual_entry = struct.unpack_from("<I", elf, 24)[0]
  if actual_entry != expected_entry:
    raise RuntimeError(
      f"firmware entry is {actual_entry:#x}, expected {expected_entry:#x}"
    )
  if allocated.get(".entry", (None,))[0] != base:
    raise RuntimeError("firmware .entry section is not at the image base")
  if allocated.get(".text", (None,))[0] != base + 0x10:
    raise RuntimeError("firmware .text section is not at image base + 0x10")
  if ".bss" in allocated and allocated[".bss"][0] < content_end:
    raise RuntimeError("firmware .bss must follow all initialized sections")
  return content_end - base, image_end - base


def _run(command, action, source):
  try:
    subprocess.run(command, check=True, capture_output=True, text=True)
  except FileNotFoundError as error:
    raise RuntimeError(f"failed to {action} {source.name}: {command[0]!r} is unavailable") from error
  except subprocess.CalledProcessError as error:
    detail = error.stderr.strip() or error.stdout.strip()
    raise RuntimeError(f"failed to {action} {source.name}: {detail}") from error


def _compile(
  source, base, capacity, defines=(), text_capacity=None, data_capacity=None,
):
  compiler = _tool(
    "CC",
    ("clang", "riscv32-unknown-elf-gcc", "riscv64-linux-gnu-gcc"),
  )
  linker = _tool(
    "TT_RISCV_LD",
    ("riscv32-unknown-elf-ld", "riscv64-linux-gnu-ld", "ld.lld"),
  )
  objcopy = _tool(
    "TT_RISCV_OBJCOPY",
    ("riscv32-unknown-elf-objcopy", "riscv64-linux-gnu-objcopy", "llvm-objcopy"),
  )
  resident = any(name == "TT_FW_RESIDENT" for name, _ in defines)
  entry_offset = 4 if resident else 0
  if text_capacity is None: text_capacity = capacity
  if data_capacity is None: data_capacity = capacity
  with tempfile.TemporaryDirectory(prefix="blackhole-fw-") as out_dir:
    header = Path(out_dir) / "abi.h"
    header.write_text(_abi_header())
    obj = Path(out_dir) / f"{source.stem}.o"
    elf = Path(out_dir) / f"{source.stem}.elf"
    binary = Path(out_dir) / f"{source.stem}.bin"
    compiler_target = (
      ["--target=riscv32-none-unknown-elf"]
      if "clang" in Path(compiler).name.lower() else []
    )
    target_flags = [
      *compiler_target, "-march=rv32im_zicsr", "-mabi=ilp32",
      *(["-mllvm", "-enable-machine-outliner=never"] if compiler_target else []),
    ]
    define_flags = [
      f"-D{name}={hex(value) if isinstance(value, int) else value}"
      for name, value in defines
    ]
    compile_command = [
      compiler, *target_flags, "-std=c11", "-Oz" if resident else "-Os", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
      "-I", out_dir, "-fno-delete-null-pointer-checks",
      "-finline-functions", "-ffreestanding", "-fno-builtin",
      "-fno-math-errno", "-fno-ident", "-fno-stack-protector",
      "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
      "-fno-pic", "-fno-pie", "-msmall-data-limit=0",
      "-ffunction-sections", "-fdata-sections", "-fno-jump-tables",
      "-fno-common",
      *define_flags,
      "-c", str(source), "-o", str(obj),
    ]
    link_command = [
      linker, "-m", "elf32lriscv", "-T", str(LINKER_SCRIPT),
      "--gc-sections", "--no-relax", "--build-id=none",
      f"--defsym=TT_IMAGE_BASE={base:#x}",
      "--defsym=TT_TEXT_OFFSET=0x10",
      f"--defsym=TT_IMAGE_CAPACITY={capacity:#x}",
      f"--defsym=TT_TEXT_CAPACITY={text_capacity:#x}",
      f"--defsym=TT_DATA_CAPACITY={data_capacity:#x}",
      str(obj), "-o", str(elf),
    ]
    _run(compile_command, "compile", source)
    _run(link_command, "link", source)
    _run([objcopy, "-O", "binary", str(elf), str(binary)], "extract", source)

    content_size, image_size = _image_layout(
      elf.read_bytes(), base, capacity, text_capacity, data_capacity,
      entry_offset,
    )
    image = binary.read_bytes()
    if len(image) != content_size:
      raise RuntimeError(
        f"firmware binary contains {len(image):#x} initialized bytes, "
        f"expected {content_size:#x}"
      )
    image = image.ljust(image_size, b"\0")
  return image


def source_files():
  return tuple(sorted(SOURCE_DIR.glob('*.py'))) + tuple(sorted(SOURCE_DIR.glob('*.c'))) + tuple(sorted(SOURCE_DIR.glob('*.h'))) + (LINKER_SCRIPT,)



def _abi_header():
  """Generate firmware constants from the host's packet and memory ABI."""
  values = {name: value for name, value in vars(abi).items() if name.isupper() and isinstance(value, int)}
  for cls, prefix in ((abi.Op, 'OP_'), (abi.PacketLayout, 'PACKET_'),
                      (TensixL1, 'L1_'), (FirmwareControl, ''), (CQConfig, ''), (TensixMMIO, 'MMIO_')):
    values.update({prefix + name: int(value) for name, value in vars(cls).items() if name.isupper() and isinstance(value, int)})
  for role, (base, _) in Firmware.TEXT.items(): values['FW_' + role.upper()] = base
  for role, base in TensixL1.WORKER_TEXT_BASE.items(): values['WORKER_' + role.upper()] = base
  return ''.join(f'#define {name} {value:#x}u\n' for name, value in sorted(values.items()))


def build(pcie_mid=None, dram_endpoints=None):
  # Legacy arguments are accepted; topology comes from the host at boot.
  workers = []
  for index, role in enumerate(KERNEL_ROLES):
    trisc = role.startswith('trisc')
    defines = [('TT_FW_RESIDENT', 1), ('TT_FW_STACK_TOP', Firmware.TRISC_STACK_TOP if trisc else Firmware.BRISC_STACK_TOP),
               ('TT_WORKER_INDEX', index)]
    if trisc: defines += [('TT_TRISC_ID', int(role[-1])), ('TT_FW_GLOBAL_POINTER', Firmware.TRISC_GLOBAL_POINTER)]
    workers.append(_compile(SOURCE_DIR / ('trisc.c' if trisc else role + '.c'), *Firmware.TEXT[role], defines))
  services = []
  for name, role, risc in (('prefetch', 'brisc', 0), ('dispatch', 'brisc', 0), ('dma', 'brisc', 0), ('dma', 'ncrisc', 1)):
    services.append(_compile(SOURCE_DIR / (name + '.c'), TensixL1.WORKER_TEXT_BASE[role], TensixL1.WORKER_TEXT_SIZE[role],
                             [('TT_FW_STACK_TOP', Firmware.BRISC_STACK_TOP), ('TT_FW_RISC', risc)]))
  return FirmwareImages(tuple(workers), *services)


def pack(images):
  blobs = (*images.workers, images.prefetch, images.dispatch, images.dram_brisc, images.dram_ncrisc)
  return struct.pack('<8s9I', b'BHCQ0002', *map(len, blobs)) + b''.join(blobs)


def unpack(blob):
  if len(blob) < 44 or blob[:8] != b'BHCQ0002': raise ValueError('invalid Blackhole firmware ABI')
  sizes, offset, images = struct.unpack_from('<9I', blob, 8), 44, []
  if 44 + sum(sizes) != len(blob) or not all(sizes): raise ValueError('invalid firmware image sizes')
  for size in sizes:
    images.append(blob[offset:offset+size]); offset += size
  return FirmwareImages(tuple(images[:5]), *images[5:])


if __name__ == '__main__':
  import hashlib
  output = Path(sys.argv[1] if len(sys.argv) > 1 else 'build/bh_hcq_v2.bin')
  output.parent.mkdir(parents=True, exist_ok=True)
  output.write_bytes(blob:=pack(build()))
  print(f'{hashlib.sha256(blob).hexdigest()}  {output} ({len(blob)} bytes)')
