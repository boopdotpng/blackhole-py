"""Build the llama3 firmware with its original assembler and fusion enabled.

The build runs in a separate interpreter so its assembler/TTK dependencies do
not replace the current kernel assembler or import the experimental TTK model.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
import sys
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
from fw.cq import build_prefetch, build_dispatch
from fw.dram_cq import build_dram_brisc, build_dram_ncrisc
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
images = [build_brisc(), build_ncrisc(), *(build_trisc(i) for i in range(3)),
          build_prefetch(options['pcie_mid']), build_dispatch(options['pcie_mid']),
          build_dram_brisc(options['endpoints']), build_dram_ncrisc(options['endpoints'])]
lowered = [image.lower() for image in images]
from fw.consts import Firmware
for (role, (_, size)), image in zip(Firmware.TEXT.items(), lowered):
    assert len(image) <= size, f'{role} firmware exceeds its slot: {len(image)} > {size}'
print(json.dumps([image.hex() for image in lowered]))
'''

def build(pcie_mid, dram_endpoints):
  result = subprocess.run([sys.executable, '-I', '-c', _SCRIPT, str(SOURCE),
    json.dumps({'pcie_mid': pcie_mid, 'endpoints': dram_endpoints,
      'l1_abi': {name: getattr(TensixL1, name) for name in (
        'PARAM_BASE', 'PARAM_SIZE', 'PARAM_SLOTS', 'KERNEL_CACHE_END',
        'PARAM_TEMPLATE_STRIDE', 'PARAM_TEMPLATE_MAX_PARAMS',
        'PARAM_TEMPLATE_IDS', 'PARAM_TEMPLATE_KERNELS', 'DATA_BUFFER_SPACE_BASE')}})],
    check=True, capture_output=True, text=True)
  images = tuple(bytes.fromhex(value) for value in json.loads(result.stdout))
  return FirmwareImages(images[:5], *images[5:])
