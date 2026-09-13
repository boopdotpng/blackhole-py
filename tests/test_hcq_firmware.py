import struct, threading
import pytest
from cq import Dma, Indirect, Signal, Wait
from fw.build import build, pack, unpack


def test_firmware_reproducible():
  blob = pack(build())
  assert pack(unpack(blob)) == blob
  assert pack(build(0x12345678, ())) == blob # topology is supplied at boot, not compiled into code
  for bad in (blob[:20], b'INVALID!'+blob[8:], b'BHCQ0001'+blob[8:], blob+b'\0'):
    with pytest.raises(ValueError): unpack(bad)


def test_wait_and_indirect(bh):
  d = bh.device
  offset = d.cq.dram
  addr = d.pcie.sysmem.noc_addr + offset
  d.pcie.sysmem.write(offset, bytes(256))
  value = (1<<32)+7
  commands = Wait(addr,value,eq=True).lower()+Signal(addr+16,123).lower()
  d.pcie.sysmem.write(offset+256,commands)
  timer = threading.Timer(0.02,lambda: d.pcie.sysmem.write(offset,struct.pack('<Q',value)))
  timer.start()
  try: d.cq.submit((Indirect(addr+256,len(commands)),))
  finally: timer.join()
  assert int.from_bytes(d.pcie.sysmem.read(offset+16,8),'little')==123
  assert int.from_bytes(d.pcie.sysmem.read(offset+24,8),'little')>0
  assert d.pcie.sysmem.read(offset+32,8)==bytes(8)


def test_byte_dma_and_large_address(bh):
  d = bh.device
  offset, size = d.cq.dram, 8195
  addr = d.pcie.sysmem.noc_addr+offset
  data = bytes(i%251 for i in range(size))
  # Exercise 64-bit logical address arithmetic, nonzero starting bank and partial pages.
  dram = (1<<63)+(1<<32)+2047
  d.pcie.sysmem.write(offset,data)
  d.cq.submit((Dma(dram,addr,size),))
  d.pcie.sysmem.write(offset,bytes(size))
  d.cq.submit((Dma(addr,dram,size),))
  assert d.pcie.sysmem.read(offset,size)==data
