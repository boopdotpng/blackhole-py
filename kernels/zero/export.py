"""Export startup KV-cache zeroing: python3 kernels/zero/export.py [path/to/blackhole-py-old]."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import fw
sys.path.insert(0, str(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT.parent / 'blackhole-py-old'))
from asm import Asm
from ttko.isa import R
from ttko.noc import NoC
from pcie import P150_DRAM_ENDPOINTS

# One worker per bank. Params: per-bank address, per-bank bytes (multiple of 16 KiB).
# DATA_BASE is scratch here: run before installing the model's resident per-core tables.
for bank, endpoints in enumerate(P150_DRAM_ENDPOINTS):
  k = Asm("brisc", physical_regs=True)
  with k.scope():
    k.zero_words(fw.DATA_BASE, 16384 // 4)
    addr, remaining, step = k.reg(3)
    k.read(addr, fw.L1_PARAM_BASE)
    k.read(remaining, fw.L1_PARAM_BASE + 4)
    k.li(step, 16384)
    noc = NoC(k, 0)
    with noc.transaction() as tx:
      k.label('zero')
      k.beq(remaining, R.ZERO, 'done')
      tx.write(fw.DATA_BASE, addr, NoC.coordinate(*endpoints[0]), 16384, posted=False)
      k.add(addr, addr, step)
      k.sub(remaining, remaining, step)
      k.j('zero')
      k.label('done')
  body = k.lower()[:-4]  # replace the old runtime return with this runtime's absolute return
  k.base += fw.SLOT_STRIDE
  assert k.assemble()[:-4] == body, "kernel must run from either code slot"
  image = body + fw.ret("brisc")
  assert len(image) <= fw.CODE_SIZE['brisc']
  out = Path(__file__).parent / f'brisc{bank}.bin'
  out.write_bytes(image)
  print(f'{out.name}: {len(image)} bytes')
