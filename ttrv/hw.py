"""Blackhole (p150) hardware facts used by TTRV lowering: memory map, Tensix configuration fields, sync and semaphore
MMIO, NoC command buffers, chip topology, data formats, and the firmware/compiler ABI.

Everything here is a fact about the chip or the firmware, never a choice the compiler makes. Names follow the source
they come from, so they can be grepped there:
  tt-metal  tt_metal/hw/inc/internal/tt-1xx/blackhole/{tensix.h, cfg_defines.h, noc/noc_parameters.h,
            noc/noc_overlay_parameters.h, tensix_types.h}
  tt-llk    tt_llk_blackhole/common/inc/{cunpack_common.h, ckernel_structs.h}
  tt-isa-documentation/BlackholeA0/TensixTile  (BabyRISCV/*.md, TensixCoprocessor/*.md)
  fw/       this repo's firmware (hw.h, noc.c, abi.h); fw/__init__.py mirrors its L1 layout

Configuration fields (all 820, plus the TileDescriptor's parts) are generated into cfg.py by gen_cfg.py, one module
attribute per field: cfg.ALU_FORMAT_SPEC_REG2_Dstacc. The per-unit views below (UNPACKER[i], ADDR_MOD[slot], ...)
index the families that differ only by a section or context number."""

from enum import IntEnum
from typing import NamedTuple
import fw
from . import cfg
from .field import Field

# ---------------------------------------------------------------------------------------------------------------------
# Memory map (tensix.h). Addresses as seen by a worker's RISC-V cores.

L1_SIZE = 0x180000                # 1.5 MiB of worker L1, from 0
LOCAL_MEM = 0xFFB00000            # each RISC's private data RAM ("PRIVATE"); the ABI section below says how TTRV uses it
NOC0_REGS = 0xFFB20000            # NIU of NoC 0 (NOC_REGS_START_ADDR); NoC 1 at +NOC_INSTANCE_OFFSET
NOC_INSTANCE_OFFSET = 0x10000
OVERLAY_STREAMS = 0xFFB40000      # NOC_OVERLAY_START_ADDR: 64 streams, NOC_STREAM_REG_SPACE_SIZE apart
STREAM_STRIDE = 0x1000
MOP_CFG = 0xFFB80000              # TENSIX_MOP_CFG_BASE: this thread's MOP expander template, MOP_CFG_WORDS u32
REGFILE = 0xFFE00000              # REGFILE_BASE: this thread's 64 Tensix GPRs, u32 each
INSTRN_BUF = 0xFFE40000           # INSTRN_BUF_BASE: a store pushes one Tensix instruction to this RISC's thread
PC_BUF = 0xFFE80000               # PC_BUF_BASE: TTSync and semaphore access for TRISCs (see "Sync" below)
TENSIX_CFG = 0xFFEF0000           # TENSIX_CFG_BASE: Config words, u32 each (word w at TENSIX_CFG + 4 * w)

# ---------------------------------------------------------------------------------------------------------------------
# Tensix configuration: fields are in cfg.py (generated). Field families that differ only by a section number (the two
# unpackers are THCON_SEC0/UNP0 and THCON_SEC1/UNP1), a context or an address-modifier slot are grouped here, so
# lowering indexes UNPACKER[i].out_data_format instead of building a name. These views look names up once, at import:
# a wrong name fails when the module loads.

UNPACK_A_CONTEXTS, UNPACK_B_CONTEXTS = 8, 2   # unpacker B on contexts 2..7 hangs the card


class Unpacker(NamedTuple):
  in_data_format: Field        # TileDescriptor: L1 format
  x_dim: Field                 # datums per row of a face
  y_dim: Field
  z_dim: Field                 # faces
  out_data_format: Field       # Src register format
  throttle_mode: Field
  haloize_mode: Field          # transpose (unpacker A only)
  ovrd_data_format: Field
  force_shared_exp: Field
  shared_exp: Field
  lf8_e4m3: Field              # LF8 input is E4M3 rather than E5M2
  row_stride: Field            # bytes per Src row
  face_stride: Field           # bytes per face
  alu_format: Field            # the math engine's view of this Src's format
  context_count: Field         # contexts in use - 1 ...
  context_count_en: Field      # ... when enabled
  context_reset: Field         # ThreadConfig: reset the context counter
  disable_zero_compress: tuple[Field, ...]   # per context, 0..7
  context_in_format: tuple[Field, ...]       # per context
  context_out_format: tuple[Field, ...]      # per context
  base_address: tuple[Field, ...]            # per context: L1 address in 16-byte words, minus one
  dest_address: tuple[Field, ...]            # per context & 3 (unpacker A)
  tile_x_dim: tuple[Field, ...]              # per context & 3 (unpacker A)


def _unpacker(i):
  get = lambda name: getattr(cfg, name)
  sec, unp = f"THCON_SEC{i}", f"UNP{i}"
  contexts = range(UNPACK_B_CONTEXTS if i else UNPACK_A_CONTEXTS)
  base = lambda c: (f"{sec}_REG3_Base_address" if c == 0 else
                    f"{sec}_REG3_Base_cntx{c}_address" if c < 4 else f"{sec}_REG4_Base_cntx{c}_address")
  return Unpacker(
    in_data_format=get(f"{sec}_REG0_TileDescriptor_in_data_format"),
    x_dim=get(f"{sec}_REG0_TileDescriptor_x_dim"),
    y_dim=get(f"{sec}_REG0_TileDescriptor_y_dim"),
    z_dim=get(f"{sec}_REG0_TileDescriptor_z_dim"),
    out_data_format=get(f"{sec}_REG2_Out_data_format"),
    throttle_mode=get(f"{sec}_REG2_Throttle_mode"),
    haloize_mode=get(f"{sec}_REG2_Haloize_mode"),
    ovrd_data_format=get(f"{sec}_REG2_Ovrd_data_format"),
    force_shared_exp=get(f"{sec}_REG2_Force_shared_exp"),
    shared_exp=get(f"{unp}_FORCED_SHARED_EXP_shared_exp"),
    lf8_e4m3=get(f"{sec}_REG1_Unp_LF8_4b_exp"),
    row_stride=get(f"{unp}_ADDR_CTRL_XY_REG_1_Ystride"),
    face_stride=get(f"{unp}_ADDR_CTRL_ZW_REG_1_Zstride"),
    alu_format=cfg.ALU_FORMAT_SPEC_REG1_SrcB if i else cfg.ALU_FORMAT_SPEC_REG0_SrcA,
    context_count=get(f"{sec}_REG2_Context_count_non_log2"),
    context_count_en=get(f"{sec}_REG2_Context_count_non_log2_en"),
    context_reset=get(f"UNPACK_MISC_CFG_CfgContextCntReset_{i}"),
    disable_zero_compress=tuple(get(f"{sec}_REG2_Disable_zero_compress_cntx{c}") for c in range(8)),
    context_in_format=tuple(get(f"{sec}_REG7_Unpack_data_format_cntx{c}") for c in contexts),
    context_out_format=tuple(get(f"{sec}_REG7_Unpack_out_data_format_cntx{c}") for c in contexts),
    base_address=tuple(get(base(c)) for c in contexts),
    dest_address=tuple(get(f"{sec}_REG5_Dest_cntx{c}_address") for c in range(4)),
    tile_x_dim=tuple(get(f"{sec}_REG5_Tile_x_dim_cntx{c}") for c in range(4)),
  )


UNPACKER = (_unpacker(0), _unpacker(1))


class AddrMod(NamedTuple):
  """Math address modifier slot: ADDR_MOD_AB_SEC{slot}, ADDR_MOD_AB2_SEC{slot} and ADDR_MOD_DST_SEC{slot}. Counters
  are indexed srca, srcb, dst, fidelity."""
  incr: tuple[Field, ...]
  clear: tuple[Field, ...]
  cr: tuple[Field, ...]        # srca, srcb, dst
  c_to_cr: Field               # dst only
  words: tuple[int, ...]       # the AB, AB2 and DST words: SETC16 rewrites all three


def _addr_mod(slot):
  get = lambda reg, name: getattr(cfg, f"ADDR_MOD_{reg}_SEC{slot}_{name}")
  units = (("AB", "SrcA"), ("AB", "SrcB"), ("DST", "Dest"), ("DST", "Fidelity"))
  return AddrMod(
    incr=tuple(get(reg, u + "Incr") for reg, u in units),
    clear=tuple(get(reg, u + "Clear") for reg, u in units),
    cr=tuple(get(reg, u + "CR") for reg, u in units[:3]),
    c_to_cr=get("DST", "DestCToCR"),
    words=(get("AB", "SrcAIncr").word, get("AB2", "SrcAIncr").word, get("DST", "DestIncr").word),
  )


ADDR_MODS = 8   # slot 0 is TTRV's reserved `hold`
ADDR_MOD = tuple(_addr_mod(s) for s in range(ADDR_MODS))


class PackAddrMod(NamedTuple):
  ysrc_incr: Field
  ysrc_clear: Field
  ydst_incr: Field
  ydst_clear: Field
  zsrc_incr: Field
  zsrc_clear: Field


PACK_ADDR_MOD = tuple(PackAddrMod(*(getattr(cfg, f"ADDR_MOD_PACK_SEC{s}_{n}") for n in (
  "YsrcIncr", "YsrcClear", "YdstIncr", "YdstClear", "ZsrcIncr", "ZsrcClear"))) for s in range(4))


# ---------------------------------------------------------------------------------------------------------------------
# Sync (BabyRISCV/ManualTTSync.md, TensixCoprocessor/SyncUnit.md). TRISC-only MMIO at PC_BUF.
# Each must be written (to order earlier stores) then loaded, and the load's result consumed by an ALU instruction
# before any other load from PC_BUF (hardware bug: otherwise the next load can return garbage or hang).

COPROCESSOR_DONE_CHECK = PC_BUF + 4   # load returns once every Tensix instruction from this thread has finished
MOP_EXPANDER_DONE_CHECK = PC_BUF + 8  # load returns once the MOP expander is idle (safe to rewrite MOP_CFG)
SEMAPHORE_ACCESS = PC_BUF + 32        # PC_BUF_SEMAPHORE_BASE: Semaphores[8], u32 each
SEM_POST, SEM_GET = 0, 1              # store to SemaphoreAccess[i]: even = SEMPOST (+1), odd = SEMGET (-1)


class Sem(IntEnum):
  """Tensix semaphore indices, as tt-llk names them (ckernel_structs.h semaphore::)."""
  FPU_SFPU = 0
  MATH_PACK = 1
  UNPACK_TO_DEST = 2
  UNPACK_OPERAND_SYNC = 3
  PACK_DONE = 4
  UNPACK_SYNC = 5       # TTRV: the unpack credit (unpack.acquire / post / release); firmware SEMINITs it each launch
  UNPACK_MATH_DONE = 6
  MATH_DONE = 7


def semaphore(i): return SEMAPHORE_ACCESS + 4 * i


MOP_CFG_WORDS = 9  # MOP expander template: outer, inner, start, end0, end1, loop0, loop1, last_inner (loop1 last), last
# The mask-mode layout reuses the same nine words (TensixCoprocessor/MOPExpander.md).

# Tensix GPRs (REGFILE) the TTRV lowering reserves. SETDMAREG addresses 16-bit halves (index 2g, 2g+1 = GPR g).
GPR_PACK_L1_ADDRESS = 12  # packer L1 destination, copied to THCON_SEC0_REG1_L1_Dest_addr by WRCFG
GPR_UNPACK_BASE = (13, 14)  # unpacker A / B L1 base for `unpack.base ..., stream`, copied to REG3 by WRCFG

# ---------------------------------------------------------------------------------------------------------------------
# Overlay streams as circular-buffer counters (fw/hw.h). CB n uses stream CB_STREAM0 + n; the producer bumps register
# CB_PUSHED, the consumer CB_POPPED. Only the low 16 bits count. (tt-metal reuses STREAM_REMOTE_DEST_BUF_START /
# _BUF_SIZE, registers 8 and 10, the same way.)

CBS = 32
CB_STREAM0 = 8
CB_PUSHED, CB_POPPED = 8, 10


def stream_reg(stream, reg): return OVERLAY_STREAMS + stream * STREAM_STRIDE + 4 * reg
def cb_pushed(cb): return stream_reg(CB_STREAM0 + cb, CB_PUSHED)
def cb_popped(cb): return stream_reg(CB_STREAM0 + cb, CB_POPPED)


# ---------------------------------------------------------------------------------------------------------------------
# NoC (noc/noc_parameters.h, fw/noc.c). BRISC uses NoC 0 and NCRISC NoC 1 (fw/noc.c's niu argument).

NIU = {"brisc": NOC0_REGS, "ncrisc": NOC0_REGS + NOC_INSTANCE_OFFSET}
CMD_BUF_STRIDE = 0x800   # NOC_CMD_BUF_OFFSET: four command buffers per NIU
NOC_MAX_BURST = 0x4000   # bytes per request
NOC_TIDS = 16            # transaction IDs per NIU


class CmdBuf(IntEnum):
  """Command buffers. TTRV gives each kind of request its own, so their fixed registers are set once per launch."""
  MCAST = 0
  READ = 1
  WRITE = 2   # also posted writes
  ATOMIC = 3


class Cmd(IntEnum):
  """Command buffer registers, byte offsets (NOC_TARG_ADDR_LO ...). For writes TARG is the local source and RET the
  remote destination; for reads and atomics TARG is the remote. *_COORD is the 'HI' register: the endpoint's NoC
  coordinate (and for DRAM/PCIe, address bits above 32)."""
  TARG_LO = 0x00
  TARG_MID = 0x04
  TARG_COORD = 0x08
  RET_LO = 0x0C
  RET_MID = 0x10
  RET_COORD = 0x14
  PACKET_TAG = 0x18
  CTRL = 0x1C
  AT_LEN_BE = 0x20        # length in bytes, or the atomic instruction
  AT_LEN_BE_1 = 0x24
  AT_DATA = 0x28          # atomic operand
  BRCST_EXCLUDE = 0x2C
  CMD_CTRL = 0x40         # write 1 to send; reads nonzero while the buffer is busy


# NOC_CTRL bits (NOC_CMD_*)
CTRL_ATOMIC = 1 << 0
CTRL_WRITE = 1 << 1
CTRL_RESP_MARKED = 1 << 4     # count completion in the transaction's OUTSTANDING counter
CTRL_BRCST_PACKET = 1 << 5    # multicast
CTRL_VC_STATIC = 1 << 7
CTRL_BRCST_SRC_INCLUDE = 1 << 17


def ctrl_static_vc(vc): return CTRL_VC_STATIC | vc << 13


def packet_tag(tid): return tid << 10   # NOC_PACKET_TAG_TRANSACTION_ID


AT_INCR_GET = 1                              # NOC_AT_INS_INCR_GET
def at_instruction(ins, wrap=31, index=0): return ins << 12 | wrap << 2 | index   # NOC_AT_INS | NOC_AT_WRAP | IND_32


NOC_ID_LOGICAL = 0x148                          # NIU register: this node's {y[11:6], x[5:0]}, NOC_CFG(0x12)
def outstanding(tid): return 0x240 + 4 * tid    # NIU_MST_REQS_OUTSTANDING_ID: reads and write acks in flight
def outgoing(tid): return 0x280 + 4 * tid       # NIU_MST_WRITE_REQS_OUTGOING_ID: writes not yet sent out of L1


def coord(x, y): return y << 6 | x   # a NoC coordinate word


# ---------------------------------------------------------------------------------------------------------------------
# p150 topology, in translated NoC coordinates (fw/noc.c). TTRV's remote(x, y, p) takes worker grid coordinates: x 0..13
# over the Tensix columns, y 0..9 over the rows.

WORKER_COLUMNS = (*range(1, 8), *range(10, 17))   # Tensix columns; DRAM and the L2CPU sit at 0, 8, 9
WORKER_ROW0 = 2
WORKER_X_GAP = 7                                  # grid x >= 7 skips the two non-Tensix columns


def worker_coord(x, y): return coord(WORKER_COLUMNS[x], WORKER_ROW0 + y)


DRAM_BANKS = fw.DRAM_BANKS
DRAM_X0 = 17          # banks 0..3 at x 17, banks 4..7 at x 18
DRAM_Y0 = 12
# Each bank has three NoC endpoints ("ports"), listed by y. Banks 4..7 list theirs in the reverse order.
DRAM_PORTS = ((14, 13, 12), (15, 16, 17), (18, 19, 20), (21, 22, 23), (14, 13, 12), (17, 16, 15), (20, 19, 18), (23, 22, 21))


def dram_coord(bank, port): return coord(DRAM_X0 + bank // 4, DRAM_PORTS[bank][port])


PCIE_COORD = 1 << 24 | coord(19, 24)   # the PCIe endpoint; bit 24 of the coordinate word selects host memory

# ---------------------------------------------------------------------------------------------------------------------
# Data formats (tensix_types.h DataFormat). Format fields are 4 bits; E4M3 is LF8 plus an extra flag
# (THCON_SEC*_REG1_Unp_LF8_4b_exp / Pac_LF8_4b_exp).


class DataFormat(IntEnum):
  FLOAT32 = 0
  FLOAT16 = 1
  BFP8 = 2
  BFP4 = 3
  TF32 = 4
  FLOAT16_B = 5
  BFP8_B = 6
  BFP4_B = 7
  INT32 = 8
  UINT16 = 9
  LF8 = 10
  BFP2 = 11
  INT8 = 14
  BFP2_B = 15


FORMAT = {  # TTRV type name -> DataFormat
  "fp32": DataFormat.FLOAT32, "fp16": DataFormat.FLOAT16, "bf16": DataFormat.FLOAT16_B,
  "bfp8": DataFormat.BFP8_B, "bfp4": DataFormat.BFP4_B, "e4m3": DataFormat.LF8, "e5m2": DataFormat.LF8,
}

# ---------------------------------------------------------------------------------------------------------------------
# Worker identity, published by fw/init.c into L1.

CORE = {"x": fw.WORKER_X, "y": fw.WORKER_Y, "id": fw.WORKER_ID}

# ---------------------------------------------------------------------------------------------------------------------
# TTRV ABI: how compiled kernels use LOCAL_MEM and the integer registers. Shared with the firmware, which owns the top
# half of LOCAL_MEM.
#
#   LOCAL_MEM + 0     .. +512    CB cursors: CB n at 16 * n. +0 consumer {pointer, count}, +8 producer {pointer, count}
#   LOCAL_MEM + 512   .. +2048   register spill frame, SPILL_SLOTS u32
#   LOCAL_MEM + 2048  ..         firmware
#
# Base registers hold addresses at the middle of a 4 KiB block, so a signed 12-bit load/store offset reaches all of it.

CB_CURSORS = LOCAL_MEM
CB_CURSOR_STRIDE = 16
CB_CONSUMER, CB_PRODUCER = 0, 8   # cursor offsets: +0 pointer, +4 count
SPILL_FRAME = LOCAL_MEM + 512
SPILL_SLOTS = 384
FIRMWARE_LOCAL = LOCAL_MEM + 2048


def cb_cursor(cb, producer): return CB_CURSORS + CB_CURSOR_STRIDE * cb + (CB_PRODUCER if producer else CB_CONSUMER)


LOCAL_BASE_REG = 3   # x3 (gp) = LOCAL_MEM + 2048, every RISC


def bases(role):
  """Integer registers preloaded with block-centered addresses: x3 private memory, x4 the NIU (data movement), Config
  (TRISC0) or PC_BUF (other TRISCs), x5 PC_BUF on TRISC0."""
  second = NIU.get(role, TENSIX_CFG if role == "trisc0" else PC_BUF)
  return {LOCAL_BASE_REG: LOCAL_MEM + 2048, 4: second + 2048} | ({5: PC_BUF + 2048} if role == "trisc0" else {})
