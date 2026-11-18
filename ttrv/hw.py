"""Blackhole worker MMIO and firmware ABI used by TTRV lowering (fw/abi.h and fw/hw.h)."""

PRIVATE, CONFIG, FIFO = 0xFFB00000, 0xFFEF0000, 0xFFE40000
PC_BUFFER = 0xFFE80000
SYNC, MOP_SYNC, SEMAPHORE = PC_BUFFER + 4, PC_BUFFER + 8, PC_BUFFER + 32
UNPACK_CREDIT = SEMAPHORE + 5 * 4
STREAM = 0xFFB40000
NOC = {"brisc": 0xFFB20000, "ncrisc": 0xFFB30000}
CORE = {"x": 0x770, "y": 0x774, "id": 0x778}


def bases(role):
  """Center each base in its block so signed RV32 load/store offsets reach 4 KiB."""
  second = NOC.get(role, CONFIG if role == "trisc0" else PC_BUFFER)
  return {3: PRIVATE + 2048, 4: second + 2048} | ({5: PC_BUFFER + 2048} if role == "trisc0" else {})
