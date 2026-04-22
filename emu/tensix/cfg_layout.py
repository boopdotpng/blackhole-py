"""Typed dataclass getters that decode bit fields from the Tensix ConfigUnit cfg array.

All getters read live cfg state — no caching.  Callers re-read as needed.
Every offset is cross-checked against emu/clauses/pack-unpack-registers.md;
discrepancies are noted with # TODO: spec ambiguity comments.

Sources:
  emu/specs/pack-unpack-registers.md  (authoritative)
  emu/clauses/pack-unpack-registers.md (cross-check)
  tt-metal/…/blackhole/cfg_defines.h  (hardware register map)

ADDR32 layout (state-relative):
  THCON_SEC0 = Unpacker 0 / Pack config context 0, base ADDR32 64
  THCON_SEC1 = Unpacker 1, base ADDR32 112
  Each THCON register group (REGn) occupies 4 consecutive ADDR32 words.
  REGn base = SEC_base + n * 4.

  Pack Config:   ADDR32 68–71 (packer context 0),  96–99 (packer context 1)
  Unpack TD:     ADDR32 64–67 (UNP0),              112–115 (UNP1)
  Unpack Cfg:    ADDR32 72–75 (UNP0),              120–123 (UNP1)
  Unpack REG3:   ADDR32 76–79 (UNP0),              124–127 (UNP1)
  Unpack REG5:   ADDR32 84–87 (UNP0),              132–135 (UNP1)
  Unpack REG7:   ADDR32 92–93 (UNP0),              140–141 (UNP1)

  Packer addr strides:    ADDR32 12–17
  Unpacker addr strides:  ADDR32 44–50, 60–62
  AddrMod pack:           ADDR32 37–40
  ALU format spec:        ADDR32 0–1
  STACC_RELU:             ADDR32 2
  PCK_DEST_RD_CTRL:       ADDR32 18
  Pack counters:          ADDR32 28–31
  Edge offset:            ADDR32 24–27
  Tile row set mapping:   ADDR32 20–23
  Dest target reg:        ADDR32 180–183
"""

from __future__ import annotations
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Bit-field extraction helpers
# ---------------------------------------------------------------------------

def _bits(word: int, hi: int, lo: int) -> int:
    """Extract bits [hi:lo] from word (inclusive on both ends)."""
    mask = (1 << (hi - lo + 1)) - 1
    return (word >> lo) & mask

def _bit(word: int, pos: int) -> int:
    """Extract single bit at pos."""
    return (word >> pos) & 1


# ---------------------------------------------------------------------------
# ADDR32 base offsets (state-relative)
# ---------------------------------------------------------------------------

# Packer config contexts
_PACK_CFG_ADDR32 = {0: 68, 1: 96}   # packer_idx 0 → ADDR32 68; 1 → 96

# Unpacker THCON sections
_UNP_SEC_BASE = {0: 64, 1: 112}     # unp_idx 0 → SEC0 base; 1 → SEC1 base

# Each REGn offset within a SEC is REGn_index * 4
def _thcon_reg(unp_idx: int, reg_num: int) -> int:
    """ADDR32 of THCON_SEC{unp_idx}_REG{reg_num}."""
    return _UNP_SEC_BASE[unp_idx] + reg_num * 4

# Fixed ADDR32 positions
_ADDR_ALU_FMT0       = 0
_ADDR_ALU_FMT1       = 1
_ADDR_STACC_RELU     = 2
_ADDR_PCK_ADDR_XY0   = 12
_ADDR_PCK_ADDR_ZW0   = 13
_ADDR_PCK_ADDR_XY1   = 14
_ADDR_PCK_ADDR_ZW1   = 15
_ADDR_PCK_BASE0      = 16
_ADDR_PCK_BASE1      = 17
_ADDR_DEST_RD_CTRL   = 18
_ADDR_TILE_ROW_MAP0  = 20   # TILE_ROW_SET_MAPPING[0:3] = ADDR32 20-23
_ADDR_PCK_EDGE_OFF0  = 24   # PCK_EDGE_OFFSET_SEC[0:3]  = ADDR32 24-27
_ADDR_PACK_CTR_BASE  = 28   # PACK_COUNTERS_SEC[0:3]    = ADDR32 28-31
_ADDR_ADDRMOD_PACK0  = 37   # ADDR_MOD_PACK_SEC[0:3]    = ADDR32 37-40

# Unpacker stride registers
_ADDR_UNP0_CTRL_XY0  = 44
_ADDR_UNP0_CTRL_ZW0  = 45
_ADDR_UNP1_CTRL_XY0  = 46
_ADDR_UNP1_CTRL_ZW0  = 47
_ADDR_UNP0_BASE0     = 48
_ADDR_UNP0_BASE1     = 49
_ADDR_UNP0_ADD_CNTR  = 50
_ADDR_UNP1_BASE0     = 60
_ADDR_UNP1_BASE1     = 61
_ADDR_UNP1_ADD_CNTR  = 62

_ADDR_DEST_TGT_BASE  = 180   # DEST_TARGET_REG_CFG_PACK_SEC[0:3] = ADDR32 180-183


def _cfg(cfg_unit, state_id: int, addr32: int) -> int:
    """Read one ADDR32 word from the live cfg array."""
    return cfg_unit.cfg[state_id][addr32]


# ===========================================================================
# Packer dataclasses and getters
# ===========================================================================

@dataclass(frozen=True)
class PackConfig:
    """Decoded pack configuration for one packer context.

    Source: THCON_SEC0_REG1 (ADDR32 68–71) for packer 0 context 0;
            THCON_SEC0_REG8 (ADDR32 96–99) for packer 0 context 1.
    """
    # Word 0 (ADDR32 68/96)
    row_ptr_section_size: int        # [15:0]
    exp_section_size: int            # [31:16]
    # Word 1 (ADDR32 69/97)
    l1_dest_addr: int                # [31:0]
    # Word 2 (ADDR32 70/98)
    uncompress: int                  # [0]
    add_l1_dest_addr_offset: int     # [1]
    disable_pack_zero_flag: int      # [2]
    out_data_format: int             # [7:4] — 4-bit DataFormat
    in_data_format: int              # [11:8] — 4-bit DataFormat
    dis_shared_exp_assembler: int    # [12]
    auto_set_last_pacr_intf_sel: int # [13]
    enable_out_fifo: int             # [14]
    sub_l1_tile_header_size: int     # [15]
    src_if_sel: int                  # [16]
    pack_start_intf_pos: int         # [20:17]
    all_pack_disable_zero_compress_ovrd: int  # [21]
    add_tile_header_size: int        # [22]
    pack_dis_y_pos_start_offset: int # [23]
    l1_src_addr: int                 # [31:24]
    # Word 3 (ADDR32 71/99)
    pack_l1_acc: int                 # [19]
    exp_threshold_en: int            # [20]
    unp_lf8_4b_exp: int             # [22]
    pac_lf8_4b_exp: int             # [23]
    exp_threshold: int               # [31:24]


def pack_config(cfg_unit, packer_idx: int, state_id: int) -> PackConfig:
    """Decode pack configuration for the given packer context.

    packer_idx: 0 or 1 (selects ADDR32 68–71 vs 96–99)
    state_id:   0 or 1 (config state bank)
    """
    base = _PACK_CFG_ADDR32[packer_idx]
    w0 = _cfg(cfg_unit, state_id, base)
    w1 = _cfg(cfg_unit, state_id, base + 1)
    w2 = _cfg(cfg_unit, state_id, base + 2)
    w3 = _cfg(cfg_unit, state_id, base + 3)

    return PackConfig(
        row_ptr_section_size          = _bits(w0, 15, 0),
        exp_section_size              = _bits(w0, 31, 16),
        l1_dest_addr                  = w1,
        uncompress                    = _bit(w2, 0),
        add_l1_dest_addr_offset       = _bit(w2, 1),
        disable_pack_zero_flag        = _bit(w2, 2),
        out_data_format               = _bits(w2, 7, 4),
        in_data_format                = _bits(w2, 11, 8),
        dis_shared_exp_assembler      = _bit(w2, 12),
        auto_set_last_pacr_intf_sel   = _bit(w2, 13),
        enable_out_fifo               = _bit(w2, 14),
        sub_l1_tile_header_size       = _bit(w2, 15),
        src_if_sel                    = _bit(w2, 16),
        pack_start_intf_pos           = _bits(w2, 20, 17),
        all_pack_disable_zero_compress_ovrd = _bit(w2, 21),
        add_tile_header_size          = _bit(w2, 22),
        pack_dis_y_pos_start_offset   = _bit(w2, 23),
        l1_src_addr                   = _bits(w2, 31, 24),
        pack_l1_acc                   = _bit(w3, 19),
        exp_threshold_en              = _bit(w3, 20),
        unp_lf8_4b_exp                = _bit(w3, 22),
        pac_lf8_4b_exp                = _bit(w3, 23),
        exp_threshold                 = _bits(w3, 31, 24),
    )


@dataclass(frozen=True)
class PckDestRdCtrl:
    """Decoded PCK_DEST_RD_CTRL register — ADDR32 18.

    Controls how the packer reads values from the Dest accumulator register.
    """
    read_32b_data: int    # [0]: 1 = read 32-bit from Dest
    read_unsigned: int    # [1]: 1 = treat data as unsigned (UInt8 output)
    read_int8: int        # [2]: 1 = Read_raw — bypass early conversion
    round_10b_mant: int   # [3]: 1 = round to 10-bit mantissa


def pck_dest_rd_ctrl(cfg_unit, state_id: int) -> PckDestRdCtrl:
    """Decode PCK_DEST_RD_CTRL — ADDR32 18."""
    w = _cfg(cfg_unit, state_id, _ADDR_DEST_RD_CTRL)
    return PckDestRdCtrl(
        read_32b_data  = _bit(w, 0),
        read_unsigned  = _bit(w, 1),
        read_int8      = _bit(w, 2),
        round_10b_mant = _bit(w, 3),
    )


@dataclass(frozen=True)
class StaccRelu:
    """Decoded STACC_RELU register — ADDR32 2.

    Shares register with ALU_ACC_CTRL_Zero_Flag_*.

    ApplyRelu mode enum:
      0 = NO_RELU (identity)
      1 = ZERO_RELU (standard ReLU)
      2 = MIN_THRESHOLD_RELU
      3 = MAX_THRESHOLD_RELU
    """
    zero_flag_disabled_src: int  # [0]
    zero_flag_disabled_dst: int  # [1]
    apply_relu: int              # [5:2] — 4-bit mode enum
    relu_threshold: int          # [21:6] — 16-bit BF16 threshold value


def stacc_relu(cfg_unit, state_id: int) -> StaccRelu:
    """Decode STACC_RELU — ADDR32 2."""
    w = _cfg(cfg_unit, state_id, _ADDR_STACC_RELU)
    return StaccRelu(
        zero_flag_disabled_src = _bit(w, 0),
        zero_flag_disabled_dst = _bit(w, 1),
        apply_relu             = _bits(w, 5, 2),
        relu_threshold         = _bits(w, 21, 6),
    )


@dataclass(frozen=True)
class PackCounters:
    """Decoded PACK_COUNTERS_SEC register — ADDR32 28+packer_idx."""
    pack_per_xy_plane: int          # [7:0]
    pack_reads_per_xy_plane: int    # [15:8]
    pack_xys_per_tile: int          # [22:16]
    pack_yz_transposed: int         # [23]
    auto_ctxt_inc_xys_cnt: int      # [31:24]


def pack_counters(cfg_unit, packer_idx: int, state_id: int) -> PackCounters:
    """Decode PACK_COUNTERS_SEC[packer_idx] — ADDR32 (28 + packer_idx)."""
    addr = _ADDR_PACK_CTR_BASE + packer_idx
    w = _cfg(cfg_unit, state_id, addr)
    return PackCounters(
        pack_per_xy_plane       = _bits(w, 7, 0),
        pack_reads_per_xy_plane = _bits(w, 15, 8),
        pack_xys_per_tile       = _bits(w, 22, 16),
        pack_yz_transposed      = _bit(w, 23),
        auto_ctxt_inc_xys_cnt   = _bits(w, 31, 24),
    )


def pck_edge_offset(cfg_unit, packer_idx: int, state_id: int) -> int:
    """Read PCK_EDGE_OFFSET_SEC[packer_idx] mask — ADDR32 (24 + packer_idx).

    Returns the 16-bit column enable mask (bits [15:0]).
    """
    addr = _ADDR_PCK_EDGE_OFF0 + packer_idx
    w = _cfg(cfg_unit, state_id, addr)
    return _bits(w, 15, 0)


@dataclass(frozen=True)
class TileRowSetMapping:
    """Decoded TILE_ROW_SET_MAPPING register — ADDR32 20+n.

    Encodes 16 rows × 2-bit mapping into 4 PCK_EDGE_OFFSET_SEC slots.
    Each 2-bit pair selects one of 4 edge offset masks for a face row.
    """
    raw_word: int  # the full 32-bit word (16 × 2-bit fields)

    def row_mapping(self, row_idx: int) -> int:
        """Get the 2-bit edge offset index for face row [0..15]."""
        return (self.raw_word >> (row_idx * 2)) & 0x3


def tile_row_set_mapping(cfg_unit, mapping_idx: int, state_id: int) -> TileRowSetMapping:
    """Decode TILE_ROW_SET_MAPPING[mapping_idx] — ADDR32 (20 + mapping_idx)."""
    addr = _ADDR_TILE_ROW_MAP0 + mapping_idx
    w = _cfg(cfg_unit, state_id, addr)
    return TileRowSetMapping(raw_word=w)


@dataclass(frozen=True)
class PckAddrCtrl:
    """Decoded packer ADC address stride registers — ADDR32 12–17."""
    # Channel 0 (input / Dest)
    ch0_x_stride: int   # ADDR32 12 [15:0]  — Xstride
    ch0_y_stride: int   # ADDR32 12 [31:16] — Ystride
    ch0_z_stride: int   # ADDR32 13 [15:0]  — Zstride
    ch0_w_stride: int   # ADDR32 13 [31:16] — Wstride
    # Channel 1 (output / L1)
    ch1_x_stride: int   # ADDR32 14 [15:0]
    ch1_y_stride: int   # ADDR32 14 [31:16]
    ch1_z_stride: int   # ADDR32 15 [15:0]
    ch1_w_stride: int   # ADDR32 15 [31:16]
    # Base registers
    base_reg_0: int     # ADDR32 16
    base_reg_1: int     # ADDR32 17


def pck_addr_ctrl(cfg_unit, state_id: int) -> PckAddrCtrl:
    """Decode packer address stride and base registers — ADDR32 12–17."""
    w12 = _cfg(cfg_unit, state_id, _ADDR_PCK_ADDR_XY0)
    w13 = _cfg(cfg_unit, state_id, _ADDR_PCK_ADDR_ZW0)
    w14 = _cfg(cfg_unit, state_id, _ADDR_PCK_ADDR_XY1)
    w15 = _cfg(cfg_unit, state_id, _ADDR_PCK_ADDR_ZW1)
    w16 = _cfg(cfg_unit, state_id, _ADDR_PCK_BASE0)
    w17 = _cfg(cfg_unit, state_id, _ADDR_PCK_BASE1)
    return PckAddrCtrl(
        ch0_x_stride = _bits(w12, 15, 0),
        ch0_y_stride = _bits(w12, 31, 16),
        ch0_z_stride = _bits(w13, 15, 0),
        ch0_w_stride = _bits(w13, 31, 16),
        ch1_x_stride = _bits(w14, 15, 0),
        ch1_y_stride = _bits(w14, 31, 16),
        ch1_z_stride = _bits(w15, 15, 0),
        ch1_w_stride = _bits(w15, 31, 16),
        base_reg_0   = w16,
        base_reg_1   = w17,
    )


@dataclass(frozen=True)
class DestTargetRegCfgPack:
    """Decoded DEST_TARGET_REG_CFG_PACK_SEC — ADDR32 180+packer_idx.

    Selects which portion of Dest to read from (double-buffering support).

    # TODO: spec ambiguity — field breakdown within ADDR32 180-183 not fully specified
    # in clauses file.  Treating the full 32-bit word as raw; downstream agent should
    # decode Offset and ZOffset fields when the ISA doc field layout is confirmed.
    """
    raw_word: int


def dest_target_reg_cfg_pack(cfg_unit, packer_idx: int, state_id: int) -> DestTargetRegCfgPack:
    """Decode DEST_TARGET_REG_CFG_PACK_SEC[packer_idx] — ADDR32 (180 + packer_idx)."""
    addr = _ADDR_DEST_TGT_BASE + packer_idx
    w = _cfg(cfg_unit, state_id, addr)
    return DestTargetRegCfgPack(raw_word=w)


@dataclass(frozen=True)
class AddrModPack:
    """Decoded ADDR_MOD_PACK_SEC entry — ADDR32 37+idx.

    Encodes Y/Z source and destination counter increments/clears applied
    after each PACR instruction.
    """
    y_src_incr: int    # [3:0]
    y_src_cr: int      # [4]
    y_src_clear: int   # [5]
    y_dst_incr: int    # [9:6]
    y_dst_cr: int      # [10]
    y_dst_clear: int   # [11]
    z_src_incr: int    # [12]
    z_src_clear: int   # [13]
    z_dst_incr: int    # [14]
    z_dst_clear: int   # [15]


def addr_mod_pack(cfg_unit, addrmod_idx: int, state_id: int) -> AddrModPack:
    """Decode ADDR_MOD_PACK_SEC[addrmod_idx] — ADDR32 (37 + addrmod_idx)."""
    addr = _ADDR_ADDRMOD_PACK0 + addrmod_idx
    w = _cfg(cfg_unit, state_id, addr)
    return AddrModPack(
        y_src_incr  = _bits(w, 3, 0),
        y_src_cr    = _bit(w, 4),
        y_src_clear = _bit(w, 5),
        y_dst_incr  = _bits(w, 9, 6),
        y_dst_cr    = _bit(w, 10),
        y_dst_clear = _bit(w, 11),
        z_src_incr  = _bit(w, 12),
        z_src_clear = _bit(w, 13),
        z_dst_incr  = _bit(w, 14),
        z_dst_clear = _bit(w, 15),
    )


# ===========================================================================
# Unpacker dataclasses and getters
# ===========================================================================

@dataclass(frozen=True)
class UnpackTileDescriptor:
    """Decoded THCON_SEC{n}_REG0 tile descriptor.

    UNP0: ADDR32 64–67, UNP1: ADDR32 112–115.
    """
    # Word 0
    in_data_format: int       # [3:0]  — 4-bit DataFormat
    uncompressed: int         # [4]
    blobs_per_xy_plane: int   # [11:8]
    x_dim: int                # [31:16]
    # Word 1
    y_dim: int                # [15:0]
    z_dim: int                # [31:16]
    # Word 2
    w_dim: int                # [15:0]
    blobs_y_start_lo: int     # [31:16]
    # Word 3
    blobs_y_start_hi: int     # [15:0]


def unpack_tile_descriptor(cfg_unit, unp_idx: int, state_id: int) -> UnpackTileDescriptor:
    """Decode THCON_SEC{unp_idx}_REG0 tile descriptor.

    unp_idx: 0 (SrcA / ADDR32 64) or 1 (SrcB / ADDR32 112)
    state_id: 0 or 1

    Spec ref: PUKREG — §2.1 Tile Descriptor (THCON_SEC0/1_REG0) — ADDR32 64–67 / 112–115
    """
    base = _thcon_reg(unp_idx, 0)  # REG0
    w0 = _cfg(cfg_unit, state_id, base)
    w1 = _cfg(cfg_unit, state_id, base + 1)
    w2 = _cfg(cfg_unit, state_id, base + 2)
    w3 = _cfg(cfg_unit, state_id, base + 3)
    return UnpackTileDescriptor(
        in_data_format    = _bits(w0, 3, 0),
        uncompressed      = _bit(w0, 4),
        blobs_per_xy_plane = _bits(w0, 11, 8),
        x_dim             = _bits(w0, 31, 16),
        y_dim             = _bits(w1, 15, 0),
        z_dim             = _bits(w1, 31, 16),
        w_dim             = _bits(w2, 15, 0),
        blobs_y_start_lo  = _bits(w2, 31, 16),
        blobs_y_start_hi  = _bits(w3, 15, 0),
    )


@dataclass(frozen=True)
class UnpackConfig:
    """Decoded THCON_SEC{n}_REG2 unpack configuration.

    UNP0: ADDR32 72–75, UNP1: ADDR32 120–123.
    """
    # Word 0
    out_data_format: int          # [3:0]
    throttle_mode: int            # [5:4]
    context_count: int            # [7:6]
    haloize_mode: int             # [8]
    tileize_mode: int             # [9]
    unpack_src_reg_set_upd: int   # [10]
    unpack_if_sel: int            # [11]
    upsample_rate: int            # [13:12]
    upsample_and_interleave: int  # [15]
    shift_amount: int             # [31:16]
    # Word 1
    uncompress_cntx0_3: int       # [3:0]
    unpack_if_sel_cntx0_3: int    # [7:4]
    force_shared_exp: int         # [8]
    uncompress_cntx4_7: int       # [19:16]
    unpack_if_sel_cntx4_7: int    # [23:20]
    # Word 2
    limit_addr: int               # [16:0]
    # Word 3
    fifo_size: int                # [16:0]


def unpack_config(cfg_unit, unp_idx: int, state_id: int) -> UnpackConfig:
    """Decode THCON_SEC{unp_idx}_REG2 unpack configuration.

    unp_idx: 0 (ADDR32 72) or 1 (ADDR32 120)
    state_id: 0 or 1

    Spec ref: §2.2 Unpack Config (THCON_SEC0/1_REG2) — ADDR32 72–75 / 120–123
    """
    base = _thcon_reg(unp_idx, 2)  # REG2
    w0 = _cfg(cfg_unit, state_id, base)
    w1 = _cfg(cfg_unit, state_id, base + 1)
    w2 = _cfg(cfg_unit, state_id, base + 2)
    w3 = _cfg(cfg_unit, state_id, base + 3)
    return UnpackConfig(
        out_data_format        = _bits(w0, 3, 0),
        throttle_mode          = _bits(w0, 5, 4),
        context_count          = _bits(w0, 7, 6),
        haloize_mode           = _bit(w0, 8),
        tileize_mode           = _bit(w0, 9),
        unpack_src_reg_set_upd = _bit(w0, 10),
        unpack_if_sel          = _bit(w0, 11),
        upsample_rate          = _bits(w0, 13, 12),
        upsample_and_interleave = _bit(w0, 15),
        shift_amount           = _bits(w0, 31, 16),
        uncompress_cntx0_3     = _bits(w1, 3, 0),
        unpack_if_sel_cntx0_3  = _bits(w1, 7, 4),
        force_shared_exp       = _bit(w1, 8),
        uncompress_cntx4_7     = _bits(w1, 19, 16),
        unpack_if_sel_cntx4_7  = _bits(w1, 23, 20),
        limit_addr             = _bits(w2, 16, 0),
        fifo_size              = _bits(w3, 16, 0),
    )


def unpack_l1_base(cfg_unit, unp_idx: int, state_id: int) -> tuple[int, int]:
    """Read THCON_SEC{unp_idx}_REG3 L1 base addresses.

    Returns (base_addr_cntx0, base_addr_cntx1).

    THCON_SEC0_REG3 = ADDR32 76–79, THCON_SEC1_REG3 = ADDR32 124–127.

    # TODO: spec ambiguity — the spec says REG3 has Base_address at REG3_base
    # and Base_cntx1_address at REG3_base+1, but does not provide explicit ADDR32
    # numbers for SEC0_REG3.  Deriving as SEC_base + REG_num*4 = 64 + 3*4 = 76 (SEC0),
    # 112 + 3*4 = 124 (SEC1).  Cross-checking: SEC0_REG5 = 84 = 64+5*4 ✓ per spec.
    # Trust this derivation.
    """
    base = _thcon_reg(unp_idx, 3)  # REG3
    ctx0 = _cfg(cfg_unit, state_id, base)
    ctx1 = _cfg(cfg_unit, state_id, base + 1)
    return ctx0, ctx1


def unpack_dest_addr(cfg_unit, unp_idx: int, state_id: int) -> dict:
    """Read THCON_SEC{unp_idx}_REG5 per-context dest addresses.

    Returns dict with keys: dest_cntx0..3, tile_x_dim_cntx0..3.

    THCON_SEC0_REG5 = ADDR32 84–87.
    THCON_SEC1_REG5 = ADDR32 132–135.

    Spec ref: §2.4 Per-Context Dest Address (THCON_SEC0_REG5) — ADDR32 84–87
    """
    base = _thcon_reg(unp_idx, 5)  # REG5
    w0 = _cfg(cfg_unit, state_id, base)      # ADDR32 84/132
    w1 = _cfg(cfg_unit, state_id, base + 1)  # ADDR32 85/133
    w2 = _cfg(cfg_unit, state_id, base + 2)  # ADDR32 86/134
    w3 = _cfg(cfg_unit, state_id, base + 3)  # ADDR32 87/135
    return {
        'dest_cntx0_address':   _bits(w0, 15, 0),
        'dest_cntx1_address':   _bits(w0, 31, 16),
        'dest_cntx2_address':   _bits(w1, 15, 0),
        'dest_cntx3_address':   _bits(w1, 31, 16),
        'tile_x_dim_cntx0':     _bits(w2, 15, 0),
        'tile_x_dim_cntx1':     _bits(w2, 31, 16),
        'tile_x_dim_cntx2':     _bits(w3, 15, 0),
        'tile_x_dim_cntx3':     _bits(w3, 31, 16),
    }


def unpack_format_override(cfg_unit, unp_idx: int, state_id: int) -> dict:
    """Read THCON_SEC{unp_idx}_REG7 per-context format overrides.

    Returns dict with offset_address, data_format per context, out_data_format per context.

    THCON_SEC0_REG7 = ADDR32 92–93.
    THCON_SEC1_REG7 = ADDR32 140–141.

    Spec ref: §2.5 Per-Context Format Override (THCON_SEC0_REG7) — ADDR32 92–93
    """
    base = _thcon_reg(unp_idx, 7)  # REG7
    w0 = _cfg(cfg_unit, state_id, base)      # ADDR32 92/140
    w1 = _cfg(cfg_unit, state_id, base + 1)  # ADDR32 93/141
    return {
        'offset_address':              _bits(w0, 15, 0),
        'unpack_data_format_cntx0':    _bits(w0, 19, 16),
        'unpack_out_data_format_cntx0': _bits(w0, 23, 20),
        'unpack_data_format_cntx4':    _bits(w0, 27, 24),
        'unpack_out_data_format_cntx4': _bits(w0, 31, 28),
        'offset_cntx1_address':        _bits(w1, 15, 0),
    }


@dataclass(frozen=True)
class UnpAddrCtrl:
    """Decoded unpacker address stride and base registers.

    UNP0: ADDR32 44–50, UNP1: ADDR32 46–47, 60–62.
    """
    # UNP0 channel 0 strides
    unp0_ch0_x_stride: int   # ADDR32 44 [15:0]
    unp0_ch0_y_stride: int   # ADDR32 44 [31:16]
    unp0_ch0_z_stride: int   # ADDR32 45 [15:0]
    unp0_ch0_w_stride: int   # ADDR32 45 [31:16]
    # UNP1 channel 0 strides
    unp1_ch0_x_stride: int   # ADDR32 46 [15:0]
    unp1_ch0_y_stride: int   # ADDR32 46 [31:16]
    unp1_ch0_z_stride: int   # ADDR32 47 [15:0]
    unp1_ch0_w_stride: int   # ADDR32 47 [31:16]
    # UNP0 base and dest counter
    unp0_base_reg_0: int     # ADDR32 48
    unp0_base_reg_1: int     # ADDR32 49
    unp0_add_dest_addr_cntr: int  # ADDR32 50 [8]
    # UNP1 base and dest counter
    unp1_base_reg_0: int     # ADDR32 60
    unp1_base_reg_1: int     # ADDR32 61
    unp1_add_dest_addr_cntr: int  # ADDR32 62 [8]


def unp_addr_ctrl(cfg_unit, state_id: int) -> UnpAddrCtrl:
    """Decode unpacker address stride and base registers — ADDR32 44–50, 60–62."""
    w44 = _cfg(cfg_unit, state_id, _ADDR_UNP0_CTRL_XY0)
    w45 = _cfg(cfg_unit, state_id, _ADDR_UNP0_CTRL_ZW0)
    w46 = _cfg(cfg_unit, state_id, _ADDR_UNP1_CTRL_XY0)
    w47 = _cfg(cfg_unit, state_id, _ADDR_UNP1_CTRL_ZW0)
    w48 = _cfg(cfg_unit, state_id, _ADDR_UNP0_BASE0)
    w49 = _cfg(cfg_unit, state_id, _ADDR_UNP0_BASE1)
    w50 = _cfg(cfg_unit, state_id, _ADDR_UNP0_ADD_CNTR)
    w60 = _cfg(cfg_unit, state_id, _ADDR_UNP1_BASE0)
    w61 = _cfg(cfg_unit, state_id, _ADDR_UNP1_BASE1)
    w62 = _cfg(cfg_unit, state_id, _ADDR_UNP1_ADD_CNTR)
    return UnpAddrCtrl(
        unp0_ch0_x_stride       = _bits(w44, 15, 0),
        unp0_ch0_y_stride       = _bits(w44, 31, 16),
        unp0_ch0_z_stride       = _bits(w45, 15, 0),
        unp0_ch0_w_stride       = _bits(w45, 31, 16),
        unp1_ch0_x_stride       = _bits(w46, 15, 0),
        unp1_ch0_y_stride       = _bits(w46, 31, 16),
        unp1_ch0_z_stride       = _bits(w47, 15, 0),
        unp1_ch0_w_stride       = _bits(w47, 31, 16),
        unp0_base_reg_0         = w48,
        unp0_base_reg_1         = w49,
        unp0_add_dest_addr_cntr = _bit(w50, 8),
        unp1_base_reg_0         = w60,
        unp1_base_reg_1         = w61,
        unp1_add_dest_addr_cntr = _bit(w62, 8),
    )


# ===========================================================================
# ALU format spec / stochastic rounding — ADDR32 0–1
# ===========================================================================

@dataclass(frozen=True)
class AluFormatSpec:
    """Decoded ALU_FORMAT_SPEC and ALU_ACC_CTRL registers — ADDR32 0–1.

    ADDR32 0: SrcA/SrcB/Dstacc format override values.
    ADDR32 1: Stochastic rounding enables, src unsigned flags, format selects,
              fp32 accumulation mode.
    """
    # ADDR32 0
    srca_val: int          # [3:0]
    srcb_val: int          # [8:5]
    dstacc_val: int        # [13:10]
    # ADDR32 1
    fpu_srnd_en: int       # [0]
    gasket_srnd_en: int    # [1]
    packer_srnd_en: int    # [2]
    gs_lf: int             # [13]
    bfp8_hf: int           # [14]
    srca_unsigned: int     # [15]
    srcb_unsigned: int     # [16]
    srca_fmt: int          # [20:17]
    srcb_fmt: int          # [24:21]
    dstacc_fmt: int        # [28:25]
    fp32_enabled: int      # [29]
    sfpu_fp32_enabled: int # [30]
    int8_math_enabled: int # [31]


def alu_format_spec(cfg_unit, state_id: int) -> AluFormatSpec:
    """Decode ALU_FORMAT_SPEC + ALU_ACC_CTRL — ADDR32 0–1.

    Spec ref: §3 ALU Format / Stochastic Rounding — ADDR32 0–2
    """
    w0 = _cfg(cfg_unit, state_id, _ADDR_ALU_FMT0)
    w1 = _cfg(cfg_unit, state_id, _ADDR_ALU_FMT1)
    return AluFormatSpec(
        srca_val          = _bits(w0, 3, 0),
        srcb_val          = _bits(w0, 8, 5),
        dstacc_val        = _bits(w0, 13, 10),
        fpu_srnd_en       = _bit(w1, 0),
        gasket_srnd_en    = _bit(w1, 1),
        packer_srnd_en    = _bit(w1, 2),
        gs_lf             = _bit(w1, 13),
        bfp8_hf           = _bit(w1, 14),
        srca_unsigned     = _bit(w1, 15),
        srcb_unsigned     = _bit(w1, 16),
        srca_fmt          = _bits(w1, 20, 17),
        srcb_fmt          = _bits(w1, 24, 21),
        dstacc_fmt        = _bits(w1, 28, 25),
        fp32_enabled      = _bit(w1, 29),
        sfpu_fp32_enabled = _bit(w1, 30),
        int8_math_enabled = _bit(w1, 31),
    )
