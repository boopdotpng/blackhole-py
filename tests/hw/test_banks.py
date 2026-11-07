"""Hardware probe: the two Config banks, ConfigDualWrite and ThreadConfig addresses on Blackhole.

  cd ../blackhole-py && tt-device-queue run --device 0 --cwd "$PWD" -- \
    '../.venv/bin/python -m pytest -p tests.conftest ../blackhole-py-rewrite/tests/hw/test_banks.py --bh-hardware -q -s'
"""
import sys, pathlib
from struct import unpack

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))  # after blackhole-py, which owns pcie.py
from config import Bank, CFG_BASE, CFG_BANK_STRIDE, THREAD_CFG_BASE, cfg_address, thread_cfg_address
sys.path.append(str(pathlib.Path(__file__).resolve().parent)); from cfg_apply import apply
import test_unpacker1_contexts as P

from asm import Asm, Cond
from ttko.isa import Tensix as TT
from firmware.consts import TensixL1
from tests.movement.unpacker.unpack import pc_sync

OUT = TensixL1.DATA_BUFFER_SPACE_BASE
WORD, GLOBAL_WORD = 91, 209  # THCON_SEC0_REG6_Metadata_misc (mover, unused) and SCRATCH_SEC0 (global)

def test_bank_addresses(bh):
  k = Asm("trisc0")
  v = k.reg()
  def store(i, addr): k.read(v, addr); k.write(OUT + 4 * i, v)
  k.write(cfg_address(WORD, Bank.B0), 0x11111111)
  k.write(cfg_address(WORD, Bank.B1), 0x22222222)
  store(0, cfg_address(WORD, Bank.B0)); store(1, cfg_address(WORD, Bank.B1))
  k.write(cfg_address(WORD, Bank.BOTH), 0x33333333)
  store(2, cfg_address(WORD, Bank.B0)); store(3, cfg_address(WORD, Bank.B1)); store(4, cfg_address(WORD, Bank.BOTH))
  k.write(CFG_BASE + 4 * GLOBAL_WORD, 0x44444444)  # one copy: bank 1's address range should show it too
  store(5, CFG_BASE + 4 * GLOBAL_WORD); store(6, CFG_BASE + CFG_BANK_STRIDE + 4 * GLOBAL_WORD)
  k.emit(TT.TTSETC16(41, 0x0102))  # ThreadConfig[thread 0][41], read back through the RISC mapping
  pc_sync(k)
  store(7, THREAD_CFG_BASE + 4 * 41)
  k.emit(TT.TTSETC16(41, 0))
  k.write(cfg_address(WORD, Bank.BOTH), 0)
  pc_sync(k)
  bh.launch({"trisc0": k.lower()}, l1={OUT: b"\xA5" * 32})
  got = unpack("<8I", bh.read_l1(bh.core, OUT, 32))
  print("\nBANKS", [hex(g) for g in got], flush=True)
  assert got[:2] == (0x11111111, 0x22222222), "bank 0 and bank 1 are separate words"
  assert got[2:5] == (0x33333333,) * 3, "ConfigDualWrite writes both banks; reading it returns bank 0"
  assert got[5:7] == (0x44444444,) * 2, "global registers have one copy"
  assert got[7] & 0xFFFF == 0x0102, "ThreadConfig is mapped at THREAD_CFG_BASE, 4 bytes per register"

def test_thread_reads_its_bank(bh):
  for state_id, want in ((0, [0]), (1, [1])):
    hits, first = P.run(bh, 1, configure_ctx=False, bank_state=state_id)
    print(f"\nBANKS unpack thread state_id={state_id}: source {hits} first {first}", flush=True)
    assert hits == want

def test_partial_stores(bh):
  """Config is documented as sw-only. sb / sh still write the whole word: the byte or halfword is replicated across all 32 bits."""
  k = Asm("trisc0")
  v = k.reg()
  def store(i, addr): k.read(v, addr); k.write(OUT + 4 * i, v)
  def reset(): k.write(cfg_address(WORD, Bank.B0), 0xAAAAAAAA); k.write(cfg_address(WORD, Bank.B1), 0xBBBBBBBB)
  cases = [("sb bank0 byte1", cfg_address(WORD, Bank.B0) + 1, 0x5C, 1), ("sh bank0 half1", cfg_address(WORD, Bank.B0) + 2, 0x1234, 2),
           ("sb dual byte1", cfg_address(WORD, Bank.BOTH) + 1, 0x5C, 1), ("sh dual half1", cfg_address(WORD, Bank.BOTH) + 2, 0x1234, 2), ("sb dual byte0", cfg_address(WORD, Bank.BOTH), 0x7E, 1),
           ("sw dual", cfg_address(WORD, Bank.BOTH), 0x5C5C5C5C, 4)]
  for i, (_, addr, value, size) in enumerate(cases):
    reset()
    k.write(addr, value, bytes=size)
    store(2 * i, cfg_address(WORD, Bank.B0)); store(2 * i + 1, cfg_address(WORD, Bank.B1))
  k.write(cfg_address(WORD, Bank.BOTH), 0)
  bh.launch({"trisc0": k.lower()}, l1={OUT: b"\xA5" * 8 * len(cases)})
  got = unpack(f"<{2 * len(cases)}I", bh.read_l1(bh.core, OUT, 8 * len(cases)))
  for i, (name, *_) in enumerate(cases): print(f"\nPARTIAL {name}: bank0 {got[2 * i]:#010x} bank1 {got[2 * i + 1]:#010x}", flush=True)
  want = [(0x5C5C5C5C, 0xBBBBBBBB), (0x12341234, 0xBBBBBBBB), (0x5C5C5C5C,) * 2, (0x12341234,) * 2, (0x7E7E7E7E,) * 2, (0x5C5C5C5C,) * 2]
  assert [got[2 * i: 2 * i + 2] for i in range(len(cases))] == want

def test_thread_config_per_thread(bh):
  """Each Tensix thread's ThreadConfig sits at thread_cfg_address(thread, reg): THREAD_CFG_BASE + 68 * 4 * thread."""
  images = {}
  for t in range(3):
    k = Asm(f"trisc{t}")
    v = k.reg()
    k.emit(TT.TTSETC16(41, 0x0100 * (t + 1) + 0x11 * t))
    pc_sync(k)
    k.read(v, thread_cfg_address(t, 41)); k.write(OUT + 4 * t, v)
    k.emit(TT.TTSETC16(41, 0))
    pc_sync(k)
    images[f"trisc{t}"] = k.lower()
  bh.launch(images, l1={OUT: b"\xA5" * 12})
  got = unpack("<3I", bh.read_l1(bh.core, OUT, 12))
  print("\nTHREADCFG", [hex(g) for g in got], flush=True)
  assert [g & 0xFFFF for g in got] == [0x0100 * (t + 1) + 0x11 * t for t in range(3)]
