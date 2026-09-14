"""Build topology-independent HCQ firmware and the resident workers.

The build runs in a separate interpreter so its assembler/TTK dependencies do
not replace the current kernel assembler or import the experimental TTK model.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
import sys
import struct
from fw.consts import TensixL1

SOURCE = Path(__file__).with_name('llama3')

@dataclass(frozen=True)
class FirmwareImages:
  workers: tuple[bytes, ...]
  prefetch: bytes
  dispatch: bytes
  dram_brisc: bytes
  dram_ncrisc: bytes

_SCRIPT = '''
import json, sys
sys.path.insert(0, sys.argv[1])
from fw.core import build_brisc, build_ncrisc, build_trisc
import fw
fw.__path__ = [sys.argv[3], *fw.__path__]
from fw.queue import build_prefetch, build_dispatch
from fw.dma import build_dram_brisc, build_dram_ncrisc
from asm import Asm, scoped
from isa import R
from fw.consts import TensixMMIO
import fw.core as core

# Keep the reference snapshot intact. Its startup sets DisTriscCache;
# override that policy without growing the fixed-size TRISC image slots.
reference_configure_csr = Asm.configure_csr
@scoped
def configure_csr(self):
    if not self.role.startswith('trisc'):
        return reference_configure_csr(self)
    value = self.reg()
    self.li(value, 2)
    self.csrrs(R.ZERO, value, 0x7c0)
    self.li(value, 1)
    self.slli(value, value, 18)
    self.fence()
    self.csrrc(R.ZERO, value, 0x7c0)
    self.li(value, 2)
    self.csrrc(R.ZERO, value, 0x7c0)
    self.fence()
    self.fence()
    self.li(value, 8)
    self.csrrs(R.ZERO, value, 0x7c0)
    return self
Asm.configure_csr = configure_csr
# The reference clears all backend config on boot AND each kernel launch.
# Enable prefetch for T0/T1/T2/B/NC with up to eight outstanding requests.
reference_reset_tensix = core._reset_tensix
def reset_tensix(fw):
    reference_reset_tensix(fw)
    fw.write(TensixMMIO.CFG_BASE + 208*4, 0x1f | (8 << 5))
    return fw
core._reset_tensix = reset_tensix
options = json.loads(sys.argv[2])
# Apply the central ABI without editing the reference source snapshot.
from fw.consts import TensixL1
for name, value in options['l1_abi'].items():
    setattr(TensixL1, name, value)
from fw.consts import Firmware, FirmwareControl
Firmware.TEXT = {role: tuple(slot) for role, slot in options['firmware_text'].items()}
def run_worker(fw, role):
    index = list(TensixL1.WORKER_TEXT_BASE).index(role)
    fw.lw(R.T0, R.ZERO, TensixL1.WORKER_ENTRY_BASE + index * 4)
    fw.jalr(R.ZERO, R.T0)
    return fw.label('worker_done')
core._run_worker = run_worker
# Cached launches install direct entry addresses, matching run_worker.
@scoped
def load_param_template(fw):
  (
    go, template, count, values, ids, dst, param_id, value, scratch,
  ) = fw.reg(9)
  done = fw._new_label("param_template_done")
  loop = fw._new_label("param_template_loop")
  kernels = fw._new_label("param_template_kernels")
  literal = fw._new_label("param_template_literal")
  store = fw._new_label("param_template_store")

  fw.read(go, FirmwareControl.GO_SIGNAL & -4)
  fw.li(scratch, (1 << 24) - 1)
  fw.and_(template, go, scratch)
  fw.beq(template, R.ZERO, done)
  fw.lw(count, template, 0)
  fw.addi(values, template, TensixL1.PARAM_TEMPLATE_VALUES)
  fw.addi(ids, template, TensixL1.PARAM_TEMPLATE_IDS)
  fw.li(dst, TensixL1.PARAM_BASE)

  fw.label(loop)
  fw.beq(count, R.ZERO, kernels)
  fw.lbu(param_id, ids, 0)
  fw.li(scratch, 0xFF)
  fw.beq(param_id, scratch, literal)
  fw.slli(param_id, param_id, 2)
  fw.li(scratch, TensixL1.RUNTIME_PARAM_BASE)
  fw.add(param_id, param_id, scratch)
  fw.lw(value, param_id, 0)
  fw.j(store)
  fw.label(literal)
  fw.lw(value, values, 0)
  fw.label(store)
  fw.sw(value, dst, 0)
  fw.addi(values, values, 4)
  fw.addi(ids, ids, 1)
  fw.addi(dst, dst, 4)
  fw.addi(count, count, -1)
  fw.j(loop)
  fw.label(kernels)
  for index, role in enumerate(TensixL1.WORKER_TEXT_BASE):
    skip = fw._new_label(f"param_template_{role}_skip")
    fw.lw(value, template, TensixL1.PARAM_TEMPLATE_KERNELS + index * 4)
    fw.beq(value, R.ZERO, skip)
    fw.li(dst, TensixL1.WORKER_ENTRY_BASE + index * 4)
    fw.sw(value, dst, 0)
    fw.label(skip)
  fw.label(done)
  return fw

core._load_param_template = load_param_template
reference_enable_clock_gating = core._enable_clock_gating
def enable_clock_gating(fw):
    reference_enable_clock_gating(fw)
    # Initialize direct entries on every tile at boot, including service tiles
    # and clients that load firmware without using the Python Device wrapper.
    for index, address in enumerate(TensixL1.WORKER_TEXT_BASE.values()):
        fw.li(R.T0, address)
        fw.sw(R.T0, R.ZERO, TensixL1.WORKER_ENTRY_BASE + index * 4)
    return fw
core._enable_clock_gating = enable_clock_gating
images = [build_brisc(), build_ncrisc(), *(build_trisc(i) for i in range(3)),
          build_prefetch(), build_dispatch(), build_dram_brisc(), build_dram_ncrisc()]
lowered = [image.lower() for image in images]
from fw.consts import Firmware
for (role, (_, size)), image in zip(Firmware.TEXT.items(), lowered):
    assert len(image) <= size, f'{role} firmware exceeds its slot: {len(image)} > {size}'
for role, image in zip(('brisc', 'brisc', 'brisc', 'ncrisc'), lowered[5:]):
    assert len(image) <= TensixL1.WORKER_TEXT_SIZE[role], f'{role} service image exceeds its slot'
print(json.dumps([image.hex() for image in lowered]))
'''

def build(pcie_mid=None, dram_endpoints=None):
  from fw.consts import Firmware
  result = subprocess.run([sys.executable, '-I', '-c', _SCRIPT, str(SOURCE),
    json.dumps({'pcie_mid': pcie_mid, 'endpoints': dram_endpoints, 'firmware_text': Firmware.TEXT,
      'l1_abi': {name: getattr(TensixL1, name) for name in (
        'PARAM_BASE', 'PARAM_SIZE', 'PARAM_SLOTS', 'KERNEL_CACHE_END', 'WORKER_ENTRY_BASE',
        'PARAM_TEMPLATE_STRIDE', 'PARAM_TEMPLATE_MAX_PARAMS',
        'PARAM_TEMPLATE_IDS', 'PARAM_TEMPLATE_KERNELS', 'DATA_BUFFER_SPACE_BASE')}}), str(Path(__file__).resolve().parent)],
    capture_output=True, text=True)
  if result.returncode: raise RuntimeError(result.stderr)
  images = tuple(bytes.fromhex(value) for value in json.loads(result.stdout))
  return FirmwareImages(images[:5], *images[5:])


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
