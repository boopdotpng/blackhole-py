import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Cond, KernelBuilder
from program import Buffer, DType, DramAllocator, KernelBundle, Param, Program
from ttk.noc import NoC

CORE = (1, 2)
VALUE_L1 = 0x10000
DATA_READY = VALUE_L1 + 4
RESULT_READY = VALUE_L1 + 8
CB_ADDR = 0x37000

def wait_flag(k: KernelBuilder, addr: int):
  with k.scope():
    flag = k.reg()
    with k.loop():
      k.load(flag, addr)
      k.break_(Cond(flag, "!=", 0))
  k.fence()

def trisc1(k: KernelBuilder):
  wait_flag(k, DATA_READY)
  with k.scope():
    value = k.reg()
    k.load(value, VALUE_L1)
    k.addi(value, value, 1)
    k.store(VALUE_L1, value)
  k.fence()
  k.store(RESULT_READY, 1)

def lower_add1(src: Buffer, dst: Buffer, *, core=CORE, dram_coord=0) -> Program:
  src_param, dst_param = Param("src", src), Param("dst", dst)

  def brisc(k: KernelBuilder):
    src_addr = k.param(src_param)
    noc = k.noc(0)
    noc.initialize(NoC.static_coord(*k.core))
    k.store(DATA_READY, 0)
    k.store(RESULT_READY, 0)
    with k.scope():
      with noc.read_batch() as reads:
        reads.issue(src_addr, dram_coord, VALUE_L1, 4)
    k.fence()
    k.store(DATA_READY, 1)

  def ncrisc(k: KernelBuilder):
    dst_addr = k.param(dst_param)
    noc = k.noc(1)
    noc.initialize(NoC.static_coord(*k.core))
    wait_flag(k, RESULT_READY)
    with k.scope():
      with noc.write_batch() as writes:
        writes.issue(VALUE_L1, dst_addr, dram_coord, 4)

  bundle = KernelBundle(
    (core,), params=(src_param, dst_param),
    brisc=brisc, ncrisc=ncrisc, trisc1=trisc1,
  )

  # CB configuration is shared program metadata. The scalar example uses L1
  # directly, but declaring one shows where tiled lowering records its CBs.
  bundle.cb(DType.BF16, pages=2, addr=CB_ADDR)

  return bundle.lower()

def main():
  dram = DramAllocator()
  src = dram.alloc("src", DType.BF16, (32, 32), (32, 32))
  dst = dram.alloc("dst", DType.BF16, (32, 32), (32, 32))
  program = lower_add1(src, dst)

  print(f"cores: {program.cores}")
  print(f"CBs:   {program.cbs}")
  print(f"params: {[(param.name, hex(program.param_addr(param)), hex(param.initial.addr)) for param in program.params]}")
  for core in program.cores:
    for role, text in program.kernels[core].items():
      print(f"{core} {role:7s}: {len(text):4d} bytes")

if __name__ == "__main__": main()
