"""Unit tests for emu/tensix/cfg_layout.py.

Constructs a ConfigUnit, pokes specific ADDR32 words via direct cfg[] writes,
and verifies decoders return the expected dataclass values.
"""

import pytest

from emu.tensix.thcon import ConfigUnit
from emu.tensix.state import GPRFile
from emu.tensix.cfg_layout import (
    pack_config,
    pck_dest_rd_ctrl,
    stacc_relu,
    pack_counters,
    pck_edge_offset,
    tile_row_set_mapping,
    pck_addr_ctrl,
    dest_target_reg_cfg_pack,
    addr_mod_pack,
    unpack_tile_descriptor,
    unpack_config,
    unpack_l1_base,
    unpack_dest_addr,
    unpack_format_override,
    unp_addr_ctrl,
    alu_format_spec,
    # ADDR32 constants for test assertions
    _PACK_CFG_ADDR32, _UNP_SEC_BASE, _thcon_reg,
    _ADDR_DEST_RD_CTRL, _ADDR_STACC_RELU, _ADDR_ALU_FMT0, _ADDR_ALU_FMT1,
    _ADDR_PCK_ADDR_XY0, _ADDR_PCK_ADDR_ZW0, _ADDR_PCK_ADDR_XY1, _ADDR_PCK_ADDR_ZW1,
    _ADDR_PCK_BASE0, _ADDR_PCK_BASE1,
    _ADDR_TILE_ROW_MAP0, _ADDR_PCK_EDGE_OFF0, _ADDR_PACK_CTR_BASE,
    _ADDR_ADDRMOD_PACK0, _ADDR_DEST_TGT_BASE,
    _ADDR_UNP0_CTRL_XY0, _ADDR_UNP0_CTRL_ZW0, _ADDR_UNP1_CTRL_XY0, _ADDR_UNP1_CTRL_ZW0,
    _ADDR_UNP0_BASE0, _ADDR_UNP0_BASE1, _ADDR_UNP0_ADD_CNTR,
    _ADDR_UNP1_BASE0, _ADDR_UNP1_BASE1, _ADDR_UNP1_ADD_CNTR,
)


# ---------------------------------------------------------------------------
# Fixture: fresh ConfigUnit with zeroed cfg state
# ---------------------------------------------------------------------------

@pytest.fixture
def cu():
    """A ConfigUnit with all cfg words zeroed (both state banks)."""
    gpr = GPRFile()
    return ConfigUnit(gpr)


def poke(cu, state_id: int, addr32: int, val: int):
    """Write a 32-bit value directly to cfg[state_id][addr32]."""
    cu.cfg[state_id][addr32] = val & 0xFFFFFFFF


# ===========================================================================
# Pack Config (ADDR32 68-71)
# ===========================================================================

class TestPackConfig:
    def test_out_data_format_packer0(self, cu):
        # ADDR32 70, bits [7:4] = out_data_format
        # Set out_data_format=5 (BF16), in_data_format=0 (FP32)
        poke(cu, 0, 68, 0)     # word 0
        poke(cu, 0, 69, 0)     # word 1
        poke(cu, 0, 70, 5 << 4)  # bits[7:4]=5
        poke(cu, 0, 71, 0)     # word 3
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.out_data_format == 5

    def test_in_data_format_packer0(self, cu):
        # ADDR32 70, bits [11:8] = in_data_format
        poke(cu, 0, 70, 4 << 8)  # in_data_format=4 (TF32)
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.in_data_format == 4

    def test_l1_dest_addr(self, cu):
        # ADDR32 69 = l1_dest_addr
        poke(cu, 0, 69, 0xDEADBEEF)
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.l1_dest_addr == 0xDEADBEEF

    def test_exp_section_size(self, cu):
        # ADDR32 68, bits [31:16]
        poke(cu, 0, 68, 4 << 16)  # exp_section_size=4
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.exp_section_size == 4

    def test_row_ptr_section_size(self, cu):
        # ADDR32 68, bits [15:0]
        poke(cu, 0, 68, 0x00FF)
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.row_ptr_section_size == 0xFF

    def test_dis_shared_exp_assembler(self, cu):
        # ADDR32 70, bit [12]
        poke(cu, 0, 70, 1 << 12)
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.dis_shared_exp_assembler == 1

    def test_pack_l1_acc(self, cu):
        # ADDR32 71, bit [19]
        poke(cu, 0, 71, 1 << 19)
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.pack_l1_acc == 1

    def test_exp_threshold_en(self, cu):
        # ADDR32 71, bit [20]
        poke(cu, 0, 71, 1 << 20)
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.exp_threshold_en == 1

    def test_pac_lf8_4b_exp(self, cu):
        # ADDR32 71, bit [23]
        poke(cu, 0, 71, 1 << 23)
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.pac_lf8_4b_exp == 1

    def test_unp_lf8_4b_exp(self, cu):
        # ADDR32 71, bit [22]
        poke(cu, 0, 71, 1 << 22)
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.unp_lf8_4b_exp == 1

    def test_exp_threshold(self, cu):
        # ADDR32 71, bits [31:24] = threshold (113 is typical for FP32→BFP-A)
        poke(cu, 0, 71, 113 << 24)
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.exp_threshold == 113

    def test_packer1_uses_addr96(self, cu):
        # packer_idx=1 uses ADDR32 96-99
        poke(cu, 0, 98, 6 << 4)  # out_data_format=6 (BFP8) at word 2 of ctx1
        cfg = pack_config(cu, packer_idx=1, state_id=0)
        assert cfg.out_data_format == 6

    def test_state_id_1(self, cu):
        # State bank 1 is independent
        poke(cu, 1, 70, 2 << 4)  # out_data_format=2 in state 1
        cfg0 = pack_config(cu, packer_idx=0, state_id=0)
        cfg1 = pack_config(cu, packer_idx=0, state_id=1)
        assert cfg0.out_data_format == 0   # state 0 untouched
        assert cfg1.out_data_format == 2

    def test_all_zero_is_defaults(self, cu):
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.out_data_format == 0
        assert cfg.in_data_format == 0
        assert cfg.l1_dest_addr == 0
        assert cfg.pack_l1_acc == 0
        assert cfg.exp_threshold_en == 0

    def test_combined_word2_fields(self, cu):
        # Pack multiple fields into word 2 and verify all extracted correctly
        val = (5 << 4) | (3 << 8) | (1 << 12) | (1 << 16)
        poke(cu, 0, 70, val)
        cfg = pack_config(cu, packer_idx=0, state_id=0)
        assert cfg.out_data_format == 5
        assert cfg.in_data_format == 3
        assert cfg.dis_shared_exp_assembler == 1
        assert cfg.src_if_sel == 1


# ===========================================================================
# PCK_DEST_RD_CTRL (ADDR32 18)
# ===========================================================================

class TestPckDestRdCtrl:
    def test_all_zero(self, cu):
        rd = pck_dest_rd_ctrl(cu, state_id=0)
        assert rd.read_32b_data == 0
        assert rd.read_unsigned == 0
        assert rd.read_int8 == 0
        assert rd.round_10b_mant == 0

    def test_read_32b_data(self, cu):
        poke(cu, 0, _ADDR_DEST_RD_CTRL, 1)
        rd = pck_dest_rd_ctrl(cu, state_id=0)
        assert rd.read_32b_data == 1

    def test_read_unsigned(self, cu):
        poke(cu, 0, _ADDR_DEST_RD_CTRL, 1 << 1)
        rd = pck_dest_rd_ctrl(cu, state_id=0)
        assert rd.read_unsigned == 1

    def test_read_int8(self, cu):
        poke(cu, 0, _ADDR_DEST_RD_CTRL, 1 << 2)
        rd = pck_dest_rd_ctrl(cu, state_id=0)
        assert rd.read_int8 == 1

    def test_round_10b_mant(self, cu):
        poke(cu, 0, _ADDR_DEST_RD_CTRL, 1 << 3)
        rd = pck_dest_rd_ctrl(cu, state_id=0)
        assert rd.round_10b_mant == 1

    def test_all_bits_set(self, cu):
        poke(cu, 0, _ADDR_DEST_RD_CTRL, 0xF)
        rd = pck_dest_rd_ctrl(cu, state_id=0)
        assert rd.read_32b_data == 1
        assert rd.read_unsigned == 1
        assert rd.read_int8 == 1
        assert rd.round_10b_mant == 1


# ===========================================================================
# STACC_RELU (ADDR32 2)
# ===========================================================================

class TestStaccRelu:
    def test_all_zero(self, cu):
        s = stacc_relu(cu, state_id=0)
        assert s.apply_relu == 0
        assert s.relu_threshold == 0

    def test_apply_relu_mode_1(self, cu):
        # bits [5:2] = 1 → ApplyRelu=1
        poke(cu, 0, _ADDR_STACC_RELU, 1 << 2)
        s = stacc_relu(cu, state_id=0)
        assert s.apply_relu == 1

    def test_apply_relu_mode_3(self, cu):
        poke(cu, 0, _ADDR_STACC_RELU, 3 << 2)
        s = stacc_relu(cu, state_id=0)
        assert s.apply_relu == 3

    def test_relu_threshold(self, cu):
        # bits [21:6] = threshold; use 0x3FFF (all 1s in 16-bit field)
        threshold = 0x3FFF
        poke(cu, 0, _ADDR_STACC_RELU, threshold << 6)
        s = stacc_relu(cu, state_id=0)
        assert s.relu_threshold == threshold

    def test_zero_flag_bits(self, cu):
        poke(cu, 0, _ADDR_STACC_RELU, 0x3)
        s = stacc_relu(cu, state_id=0)
        assert s.zero_flag_disabled_src == 1
        assert s.zero_flag_disabled_dst == 1

    def test_threshold_bf16_value(self, cu):
        # BF16 for 0.0 is 0x0000 (all zeros)
        poke(cu, 0, _ADDR_STACC_RELU, 0)
        s = stacc_relu(cu, state_id=0)
        assert s.relu_threshold == 0


# ===========================================================================
# Pack Counters (ADDR32 28)
# ===========================================================================

class TestPackCounters:
    def test_all_zero(self, cu):
        c = pack_counters(cu, packer_idx=0, state_id=0)
        assert c.pack_reads_per_xy_plane == 0
        assert c.pack_yz_transposed == 0

    def test_pack_reads_per_xy_plane(self, cu):
        # bits [15:8] = pack_reads_per_xy_plane (= 16 for normal tiles)
        poke(cu, 0, _ADDR_PACK_CTR_BASE, 16 << 8)
        c = pack_counters(cu, packer_idx=0, state_id=0)
        assert c.pack_reads_per_xy_plane == 16

    def test_pack_yz_transposed(self, cu):
        poke(cu, 0, _ADDR_PACK_CTR_BASE, 1 << 23)
        c = pack_counters(cu, packer_idx=0, state_id=0)
        assert c.pack_yz_transposed == 1

    def test_pack_per_xy_plane(self, cu):
        poke(cu, 0, _ADDR_PACK_CTR_BASE, 0xAB)
        c = pack_counters(cu, packer_idx=0, state_id=0)
        assert c.pack_per_xy_plane == 0xAB

    def test_packer1_separate_register(self, cu):
        poke(cu, 0, _ADDR_PACK_CTR_BASE + 1, 8 << 8)
        c0 = pack_counters(cu, packer_idx=0, state_id=0)
        c1 = pack_counters(cu, packer_idx=1, state_id=0)
        assert c0.pack_reads_per_xy_plane == 0
        assert c1.pack_reads_per_xy_plane == 8


# ===========================================================================
# Edge offset (ADDR32 24)
# ===========================================================================

class TestPckEdgeOffset:
    def test_all_enabled(self, cu):
        # Default all-pass mask = 0xFFFF
        poke(cu, 0, _ADDR_PCK_EDGE_OFF0, 0xFFFF)
        mask = pck_edge_offset(cu, packer_idx=0, state_id=0)
        assert mask == 0xFFFF

    def test_partial_mask(self, cu):
        poke(cu, 0, _ADDR_PCK_EDGE_OFF0, 0x00FF)
        mask = pck_edge_offset(cu, packer_idx=0, state_id=0)
        assert mask == 0x00FF

    def test_packer1_separate(self, cu):
        poke(cu, 0, _ADDR_PCK_EDGE_OFF0 + 1, 0xAAAA)
        assert pck_edge_offset(cu, packer_idx=0, state_id=0) == 0
        assert pck_edge_offset(cu, packer_idx=1, state_id=0) == 0xAAAA


# ===========================================================================
# Tile Row Set Mapping (ADDR32 20)
# ===========================================================================

class TestTileRowSetMapping:
    def test_all_zero_maps_all_to_0(self, cu):
        m = tile_row_set_mapping(cu, mapping_idx=0, state_id=0)
        for row in range(16):
            assert m.row_mapping(row) == 0

    def test_row_mapping_fields(self, cu):
        # Set row 0 → 1, row 1 → 2, row 2 → 3, rest = 0
        val = 0b_11_10_01  # rows 2, 1, 0 with values 3, 2, 1
        poke(cu, 0, _ADDR_TILE_ROW_MAP0, val)
        m = tile_row_set_mapping(cu, mapping_idx=0, state_id=0)
        assert m.row_mapping(0) == 1
        assert m.row_mapping(1) == 2
        assert m.row_mapping(2) == 3
        assert m.row_mapping(3) == 0

    def test_mapping1_independent(self, cu):
        poke(cu, 0, _ADDR_TILE_ROW_MAP0 + 1, 0x55555555)  # pattern 01 alternating
        m0 = tile_row_set_mapping(cu, mapping_idx=0, state_id=0)
        m1 = tile_row_set_mapping(cu, mapping_idx=1, state_id=0)
        assert m0.raw_word == 0
        assert m1.raw_word == 0x55555555


# ===========================================================================
# Packer Address Control (ADDR32 12-17)
# ===========================================================================

class TestPckAddrCtrl:
    def test_all_zero(self, cu):
        a = pck_addr_ctrl(cu, state_id=0)
        assert a.ch0_x_stride == 0
        assert a.ch0_y_stride == 0
        assert a.base_reg_0 == 0

    def test_ch0_xy_strides(self, cu):
        # Typical: Xstride=0, Ystride=32 (BF16, 16 elements × 2 bytes)
        poke(cu, 0, _ADDR_PCK_ADDR_XY0, (32 << 16) | 0)
        a = pck_addr_ctrl(cu, state_id=0)
        assert a.ch0_x_stride == 0
        assert a.ch0_y_stride == 32

    def test_ch0_zw_strides(self, cu):
        poke(cu, 0, _ADDR_PCK_ADDR_ZW0, (0x1234 << 16) | 0xABCD)
        a = pck_addr_ctrl(cu, state_id=0)
        assert a.ch0_z_stride == 0xABCD
        assert a.ch0_w_stride == 0x1234

    def test_ch1_strides(self, cu):
        poke(cu, 0, _ADDR_PCK_ADDR_XY1, (100 << 16) | 4)
        a = pck_addr_ctrl(cu, state_id=0)
        assert a.ch1_x_stride == 4
        assert a.ch1_y_stride == 100

    def test_base_registers(self, cu):
        poke(cu, 0, _ADDR_PCK_BASE0, 0xCAFEBABE)
        poke(cu, 0, _ADDR_PCK_BASE1, 0x12345678)
        a = pck_addr_ctrl(cu, state_id=0)
        assert a.base_reg_0 == 0xCAFEBABE
        assert a.base_reg_1 == 0x12345678


# ===========================================================================
# Dest Target Reg Cfg Pack (ADDR32 180-183)
# ===========================================================================

class TestDestTargetRegCfgPack:
    def test_packer0_at_180(self, cu):
        poke(cu, 0, _ADDR_DEST_TGT_BASE, 0xDEAD)
        d = dest_target_reg_cfg_pack(cu, packer_idx=0, state_id=0)
        assert d.raw_word == 0xDEAD

    def test_packer1_at_181(self, cu):
        poke(cu, 0, _ADDR_DEST_TGT_BASE + 1, 0xBEEF)
        d0 = dest_target_reg_cfg_pack(cu, packer_idx=0, state_id=0)
        d1 = dest_target_reg_cfg_pack(cu, packer_idx=1, state_id=0)
        assert d0.raw_word == 0
        assert d1.raw_word == 0xBEEF

    def test_state_id_separation(self, cu):
        poke(cu, 0, _ADDR_DEST_TGT_BASE, 0xAAAA)
        poke(cu, 1, _ADDR_DEST_TGT_BASE, 0xBBBB)
        d0 = dest_target_reg_cfg_pack(cu, packer_idx=0, state_id=0)
        d1 = dest_target_reg_cfg_pack(cu, packer_idx=0, state_id=1)
        assert d0.raw_word == 0xAAAA
        assert d1.raw_word == 0xBBBB


# ===========================================================================
# AddrMod Pack (ADDR32 37-40)
# ===========================================================================

class TestAddrModPack:
    def test_all_zero(self, cu):
        a = addr_mod_pack(cu, addrmod_idx=0, state_id=0)
        assert a.y_src_incr == 0
        assert a.y_dst_incr == 0

    def test_y_src_incr(self, cu):
        # bits [3:0] = y_src_incr
        poke(cu, 0, _ADDR_ADDRMOD_PACK0, 0b0111)
        a = addr_mod_pack(cu, addrmod_idx=0, state_id=0)
        assert a.y_src_incr == 7

    def test_y_dst_incr(self, cu):
        # bits [9:6] = y_dst_incr; value 4 = 0b100 in bits 9:6
        poke(cu, 0, _ADDR_ADDRMOD_PACK0, 4 << 6)
        a = addr_mod_pack(cu, addrmod_idx=0, state_id=0)
        assert a.y_dst_incr == 4

    def test_z_flags(self, cu):
        # z_src_incr [12], z_src_clear [13], z_dst_incr [14], z_dst_clear [15]
        poke(cu, 0, _ADDR_ADDRMOD_PACK0, (1 << 12) | (1 << 14))
        a = addr_mod_pack(cu, addrmod_idx=0, state_id=0)
        assert a.z_src_incr == 1
        assert a.z_src_clear == 0
        assert a.z_dst_incr == 1
        assert a.z_dst_clear == 0

    def test_y_clear_flags(self, cu):
        poke(cu, 0, _ADDR_ADDRMOD_PACK0, (1 << 5) | (1 << 11))
        a = addr_mod_pack(cu, addrmod_idx=0, state_id=0)
        assert a.y_src_clear == 1
        assert a.y_dst_clear == 1

    def test_addrmod1_is_independent(self, cu):
        poke(cu, 0, _ADDR_ADDRMOD_PACK0 + 1, 0x3)
        a0 = addr_mod_pack(cu, addrmod_idx=0, state_id=0)
        a1 = addr_mod_pack(cu, addrmod_idx=1, state_id=0)
        assert a0.y_src_incr == 0
        assert a1.y_src_incr == 3


# ===========================================================================
# Unpack Tile Descriptor (ADDR32 64-67 / 112-115)
# ===========================================================================

class TestUnpackTileDescriptor:
    def test_unp0_base_addr(self, cu):
        # UNP0 REG0 at ADDR32 64
        base = _thcon_reg(0, 0)
        assert base == 64

    def test_unp1_base_addr(self, cu):
        # UNP1 REG0 at ADDR32 112
        base = _thcon_reg(1, 0)
        assert base == 112

    def test_in_data_format_unp0(self, cu):
        # ADDR32 64, bits [3:0]
        poke(cu, 0, 64, 5)  # BF16 = 5
        td = unpack_tile_descriptor(cu, unp_idx=0, state_id=0)
        assert td.in_data_format == 5

    def test_uncompressed_flag(self, cu):
        poke(cu, 0, 64, 1 << 4)
        td = unpack_tile_descriptor(cu, unp_idx=0, state_id=0)
        assert td.uncompressed == 1

    def test_x_dim(self, cu):
        # ADDR32 64, bits [31:16]
        poke(cu, 0, 64, 256 << 16)  # x_dim=256 for 16×16 face
        td = unpack_tile_descriptor(cu, unp_idx=0, state_id=0)
        assert td.x_dim == 256

    def test_y_dim(self, cu):
        # ADDR32 65, bits [15:0]
        poke(cu, 0, 65, 1)
        td = unpack_tile_descriptor(cu, unp_idx=0, state_id=0)
        assert td.y_dim == 1

    def test_z_dim(self, cu):
        # ADDR32 65, bits [31:16]
        poke(cu, 0, 65, 4 << 16)  # z_dim=4 for 4 faces
        td = unpack_tile_descriptor(cu, unp_idx=0, state_id=0)
        assert td.z_dim == 4

    def test_w_dim(self, cu):
        poke(cu, 0, 66, 1)
        td = unpack_tile_descriptor(cu, unp_idx=0, state_id=0)
        assert td.w_dim == 1

    def test_unp1_at_addr112(self, cu):
        poke(cu, 0, 64, 0)   # UNP0 zero
        poke(cu, 0, 112, 6)  # UNP1 BFP8
        td0 = unpack_tile_descriptor(cu, unp_idx=0, state_id=0)
        td1 = unpack_tile_descriptor(cu, unp_idx=1, state_id=0)
        assert td0.in_data_format == 0
        assert td1.in_data_format == 6

    def test_blobs_per_xy_plane(self, cu):
        # bits [11:8]
        poke(cu, 0, 64, 3 << 8)
        td = unpack_tile_descriptor(cu, unp_idx=0, state_id=0)
        assert td.blobs_per_xy_plane == 3

    def test_full_tile_descriptor(self, cu):
        # Pack a full tile descriptor
        w0 = (5) | (1 << 4) | (256 << 16)  # fmt=5, uncompressed, x_dim=256
        w1 = (1) | (4 << 16)                 # y_dim=1, z_dim=4
        w2 = 1                                 # w_dim=1
        poke(cu, 0, 64, w0)
        poke(cu, 0, 65, w1)
        poke(cu, 0, 66, w2)
        td = unpack_tile_descriptor(cu, unp_idx=0, state_id=0)
        assert td.in_data_format == 5
        assert td.uncompressed == 1
        assert td.x_dim == 256
        assert td.y_dim == 1
        assert td.z_dim == 4
        assert td.w_dim == 1


# ===========================================================================
# Unpack Config (ADDR32 72-75 / 120-123)
# ===========================================================================

class TestUnpackConfig:
    def test_unp0_base_at_72(self, cu):
        assert _thcon_reg(0, 2) == 72

    def test_unp1_base_at_120(self, cu):
        assert _thcon_reg(1, 2) == 120

    def test_out_data_format(self, cu):
        # ADDR32 72, bits [3:0]
        poke(cu, 0, 72, 5)
        uc = unpack_config(cu, unp_idx=0, state_id=0)
        assert uc.out_data_format == 5

    def test_haloize_mode(self, cu):
        poke(cu, 0, 72, 1 << 8)
        uc = unpack_config(cu, unp_idx=0, state_id=0)
        assert uc.haloize_mode == 1

    def test_tileize_mode(self, cu):
        poke(cu, 0, 72, 1 << 9)
        uc = unpack_config(cu, unp_idx=0, state_id=0)
        assert uc.tileize_mode == 1

    def test_unpack_src_reg_set_upd(self, cu):
        poke(cu, 0, 72, 1 << 10)
        uc = unpack_config(cu, unp_idx=0, state_id=0)
        assert uc.unpack_src_reg_set_upd == 1

    def test_force_shared_exp(self, cu):
        # ADDR32 73, bit [8]
        poke(cu, 0, 73, 1 << 8)
        uc = unpack_config(cu, unp_idx=0, state_id=0)
        assert uc.force_shared_exp == 1

    def test_limit_addr(self, cu):
        # ADDR32 74, bits [16:0]
        poke(cu, 0, 74, 0x1ABCD)
        uc = unpack_config(cu, unp_idx=0, state_id=0)
        assert uc.limit_addr == 0x1ABCD

    def test_fifo_size(self, cu):
        # ADDR32 75, bits [16:0]
        poke(cu, 0, 75, 0x10000)
        uc = unpack_config(cu, unp_idx=0, state_id=0)
        assert uc.fifo_size == 0x10000

    def test_context_count(self, cu):
        # ADDR32 72, bits [7:6]
        poke(cu, 0, 72, 2 << 6)
        uc = unpack_config(cu, unp_idx=0, state_id=0)
        assert uc.context_count == 2

    def test_uncompress_cntx0_3(self, cu):
        # ADDR32 73, bits [3:0]
        poke(cu, 0, 73, 0xF)
        uc = unpack_config(cu, unp_idx=0, state_id=0)
        assert uc.uncompress_cntx0_3 == 0xF

    def test_unp1_independent(self, cu):
        poke(cu, 0, 72, 0)   # UNP0
        poke(cu, 0, 120, 1)  # UNP1 out_data_format=1
        uc0 = unpack_config(cu, unp_idx=0, state_id=0)
        uc1 = unpack_config(cu, unp_idx=1, state_id=0)
        assert uc0.out_data_format == 0
        assert uc1.out_data_format == 1


# ===========================================================================
# Unpack L1 Base (THCON_SEC{n}_REG3)
# ===========================================================================

class TestUnpackL1Base:
    def test_reg3_addr(self, cu):
        # REG3 for UNP0 = 64 + 3*4 = 76
        assert _thcon_reg(0, 3) == 76

    def test_reg3_addr_unp1(self, cu):
        # REG3 for UNP1 = 112 + 3*4 = 124
        assert _thcon_reg(1, 3) == 124

    def test_context0_address(self, cu):
        poke(cu, 0, 76, 0x1000)
        ctx0, ctx1 = unpack_l1_base(cu, unp_idx=0, state_id=0)
        assert ctx0 == 0x1000

    def test_context1_address(self, cu):
        poke(cu, 0, 77, 0x2000)
        ctx0, ctx1 = unpack_l1_base(cu, unp_idx=0, state_id=0)
        assert ctx1 == 0x2000

    def test_unp1_at_124(self, cu):
        poke(cu, 0, 124, 0xABCD)
        ctx0, ctx1 = unpack_l1_base(cu, unp_idx=1, state_id=0)
        assert ctx0 == 0xABCD


# ===========================================================================
# Unpack Dest Address (THCON_SEC{n}_REG5)
# ===========================================================================

class TestUnpackDestAddr:
    def test_reg5_addr(self, cu):
        # REG5 for UNP0 = 64 + 5*4 = 84
        assert _thcon_reg(0, 5) == 84

    def test_dest_cntx0_address(self, cu):
        # ADDR32 84, bits [15:0]
        poke(cu, 0, 84, 0x1234)
        d = unpack_dest_addr(cu, unp_idx=0, state_id=0)
        assert d['dest_cntx0_address'] == 0x1234

    def test_dest_cntx1_address(self, cu):
        # ADDR32 84, bits [31:16]
        poke(cu, 0, 84, 0x5678 << 16)
        d = unpack_dest_addr(cu, unp_idx=0, state_id=0)
        assert d['dest_cntx1_address'] == 0x5678

    def test_tile_x_dim_cntx0(self, cu):
        # ADDR32 86, bits [15:0]
        poke(cu, 0, 86, 256)
        d = unpack_dest_addr(cu, unp_idx=0, state_id=0)
        assert d['tile_x_dim_cntx0'] == 256

    def test_unp1_reg5_at_132(self, cu):
        assert _thcon_reg(1, 5) == 132
        poke(cu, 0, 132, 0xABCD)
        d = unpack_dest_addr(cu, unp_idx=1, state_id=0)
        assert d['dest_cntx0_address'] == 0xABCD


# ===========================================================================
# Unpack Format Override (THCON_SEC{n}_REG7)
# ===========================================================================

class TestUnpackFormatOverride:
    def test_reg7_addr(self, cu):
        # REG7 for UNP0 = 64 + 7*4 = 92
        assert _thcon_reg(0, 7) == 92

    def test_offset_address(self, cu):
        # ADDR32 92, bits [15:0]
        poke(cu, 0, 92, 0x0100)
        fo = unpack_format_override(cu, unp_idx=0, state_id=0)
        assert fo['offset_address'] == 0x0100

    def test_data_format_cntx0(self, cu):
        # ADDR32 92, bits [19:16]
        poke(cu, 0, 92, 5 << 16)
        fo = unpack_format_override(cu, unp_idx=0, state_id=0)
        assert fo['unpack_data_format_cntx0'] == 5

    def test_out_data_format_cntx0(self, cu):
        # ADDR32 92, bits [23:20]
        poke(cu, 0, 92, 3 << 20)
        fo = unpack_format_override(cu, unp_idx=0, state_id=0)
        assert fo['unpack_out_data_format_cntx0'] == 3

    def test_data_format_cntx4(self, cu):
        # ADDR32 92, bits [27:24]
        poke(cu, 0, 92, 7 << 24)
        fo = unpack_format_override(cu, unp_idx=0, state_id=0)
        assert fo['unpack_data_format_cntx4'] == 7

    def test_offset_cntx1_address(self, cu):
        # ADDR32 93, bits [15:0]
        poke(cu, 0, 93, 0x0200)
        fo = unpack_format_override(cu, unp_idx=0, state_id=0)
        assert fo['offset_cntx1_address'] == 0x0200

    def test_unp1_reg7_at_140(self, cu):
        assert _thcon_reg(1, 7) == 140
        poke(cu, 0, 140, 6 << 16)
        fo = unpack_format_override(cu, unp_idx=1, state_id=0)
        assert fo['unpack_data_format_cntx0'] == 6


# ===========================================================================
# Unpack Address Control (ADDR32 44-50, 60-62)
# ===========================================================================

class TestUnpAddrCtrl:
    def test_all_zero(self, cu):
        a = unp_addr_ctrl(cu, state_id=0)
        assert a.unp0_ch0_x_stride == 0
        assert a.unp0_base_reg_0 == 0

    def test_unp0_xy_strides(self, cu):
        poke(cu, 0, _ADDR_UNP0_CTRL_XY0, (16 << 16) | 2)
        a = unp_addr_ctrl(cu, state_id=0)
        assert a.unp0_ch0_x_stride == 2
        assert a.unp0_ch0_y_stride == 16

    def test_unp0_zw_strides(self, cu):
        poke(cu, 0, _ADDR_UNP0_CTRL_ZW0, (32 << 16) | 256)
        a = unp_addr_ctrl(cu, state_id=0)
        assert a.unp0_ch0_z_stride == 256
        assert a.unp0_ch0_w_stride == 32

    def test_unp1_strides(self, cu):
        poke(cu, 0, _ADDR_UNP1_CTRL_XY0, (8 << 16) | 1)
        a = unp_addr_ctrl(cu, state_id=0)
        assert a.unp1_ch0_x_stride == 1
        assert a.unp1_ch0_y_stride == 8

    def test_unp0_base_registers(self, cu):
        poke(cu, 0, _ADDR_UNP0_BASE0, 0x10000)
        poke(cu, 0, _ADDR_UNP0_BASE1, 0x20000)
        a = unp_addr_ctrl(cu, state_id=0)
        assert a.unp0_base_reg_0 == 0x10000
        assert a.unp0_base_reg_1 == 0x20000

    def test_unp1_base_registers(self, cu):
        poke(cu, 0, _ADDR_UNP1_BASE0, 0x30000)
        poke(cu, 0, _ADDR_UNP1_BASE1, 0x40000)
        a = unp_addr_ctrl(cu, state_id=0)
        assert a.unp1_base_reg_0 == 0x30000
        assert a.unp1_base_reg_1 == 0x40000

    def test_dest_addr_cntr_enable(self, cu):
        # bit [8] of ADDR32 50
        poke(cu, 0, _ADDR_UNP0_ADD_CNTR, 1 << 8)
        a = unp_addr_ctrl(cu, state_id=0)
        assert a.unp0_add_dest_addr_cntr == 1

    def test_unp1_dest_addr_cntr(self, cu):
        poke(cu, 0, _ADDR_UNP1_ADD_CNTR, 1 << 8)
        a = unp_addr_ctrl(cu, state_id=0)
        assert a.unp1_add_dest_addr_cntr == 1


# ===========================================================================
# ALU Format Spec (ADDR32 0-1)
# ===========================================================================

class TestAluFormatSpec:
    def test_all_zero(self, cu):
        a = alu_format_spec(cu, state_id=0)
        assert a.fpu_srnd_en == 0
        assert a.fp32_enabled == 0
        assert a.srca_unsigned == 0

    def test_fpu_srnd_en(self, cu):
        poke(cu, 0, _ADDR_ALU_FMT1, 1)
        a = alu_format_spec(cu, state_id=0)
        assert a.fpu_srnd_en == 1

    def test_gasket_srnd_en(self, cu):
        poke(cu, 0, _ADDR_ALU_FMT1, 1 << 1)
        a = alu_format_spec(cu, state_id=0)
        assert a.gasket_srnd_en == 1

    def test_packer_srnd_en(self, cu):
        poke(cu, 0, _ADDR_ALU_FMT1, 1 << 2)
        a = alu_format_spec(cu, state_id=0)
        assert a.packer_srnd_en == 1

    def test_srca_unsigned(self, cu):
        # bit [15]
        poke(cu, 0, _ADDR_ALU_FMT1, 1 << 15)
        a = alu_format_spec(cu, state_id=0)
        assert a.srca_unsigned == 1

    def test_srcb_unsigned(self, cu):
        poke(cu, 0, _ADDR_ALU_FMT1, 1 << 16)
        a = alu_format_spec(cu, state_id=0)
        assert a.srcb_unsigned == 1

    def test_fp32_enabled(self, cu):
        poke(cu, 0, _ADDR_ALU_FMT1, 1 << 29)
        a = alu_format_spec(cu, state_id=0)
        assert a.fp32_enabled == 1

    def test_sfpu_fp32_enabled(self, cu):
        poke(cu, 0, _ADDR_ALU_FMT1, 1 << 30)
        a = alu_format_spec(cu, state_id=0)
        assert a.sfpu_fp32_enabled == 1

    def test_int8_math_enabled(self, cu):
        poke(cu, 0, _ADDR_ALU_FMT1, 1 << 31)
        a = alu_format_spec(cu, state_id=0)
        assert a.int8_math_enabled == 1

    def test_srca_fmt(self, cu):
        # bits [20:17]
        poke(cu, 0, _ADDR_ALU_FMT1, 5 << 17)
        a = alu_format_spec(cu, state_id=0)
        assert a.srca_fmt == 5

    def test_srcb_fmt(self, cu):
        # bits [24:21]
        poke(cu, 0, _ADDR_ALU_FMT1, 6 << 21)
        a = alu_format_spec(cu, state_id=0)
        assert a.srcb_fmt == 6

    def test_dstacc_fmt(self, cu):
        # bits [28:25]
        poke(cu, 0, _ADDR_ALU_FMT1, 0 << 25)
        a = alu_format_spec(cu, state_id=0)
        assert a.dstacc_fmt == 0

    def test_srca_val_from_addr0(self, cu):
        # ADDR32 0, bits [3:0]
        poke(cu, 0, _ADDR_ALU_FMT0, 4)  # srca_val=4 (TF32)
        a = alu_format_spec(cu, state_id=0)
        assert a.srca_val == 4

    def test_srcb_val_from_addr0(self, cu):
        # ADDR32 0, bits [8:5]
        poke(cu, 0, _ADDR_ALU_FMT0, 5 << 5)  # srcb_val=5 (BF16)
        a = alu_format_spec(cu, state_id=0)
        assert a.srcb_val == 5

    def test_dstacc_val_from_addr0(self, cu):
        # ADDR32 0, bits [13:10]
        poke(cu, 0, _ADDR_ALU_FMT0, 1 << 10)  # dstacc_val=1
        a = alu_format_spec(cu, state_id=0)
        assert a.dstacc_val == 1

    def test_state_id_1_independent(self, cu):
        poke(cu, 0, _ADDR_ALU_FMT1, 0)
        poke(cu, 1, _ADDR_ALU_FMT1, 1 << 29)
        a0 = alu_format_spec(cu, state_id=0)
        a1 = alu_format_spec(cu, state_id=1)
        assert a0.fp32_enabled == 0
        assert a1.fp32_enabled == 1


# ===========================================================================
# ADDR32 offset sanity checks
# ===========================================================================

class TestAddr32Layout:
    """Verify computed ADDR32 offsets match spec table values."""

    def test_pack_config_ctx0_at_68(self):
        assert _PACK_CFG_ADDR32[0] == 68

    def test_pack_config_ctx1_at_96(self):
        assert _PACK_CFG_ADDR32[1] == 96

    def test_unp0_sec_base_at_64(self):
        assert _UNP_SEC_BASE[0] == 64

    def test_unp1_sec_base_at_112(self):
        assert _UNP_SEC_BASE[1] == 112

    def test_unp0_reg2_at_72(self):
        # THCON_SEC0_REG2 = 64 + 2*4 = 72
        assert _thcon_reg(0, 2) == 72

    def test_unp1_reg2_at_120(self):
        # THCON_SEC1_REG2 = 112 + 2*4 = 120
        assert _thcon_reg(1, 2) == 120

    def test_unp0_reg5_at_84(self):
        # Spec says ADDR32 84–87 for THCON_SEC0_REG5
        assert _thcon_reg(0, 5) == 84

    def test_unp0_reg7_at_92(self):
        # Spec says ADDR32 92–93 for THCON_SEC0_REG7
        assert _thcon_reg(0, 7) == 92

    def test_dest_rd_ctrl_at_18(self):
        assert _ADDR_DEST_RD_CTRL == 18

    def test_stacc_relu_at_2(self):
        assert _ADDR_STACC_RELU == 2

    def test_pack_counters_at_28(self):
        assert _ADDR_PACK_CTR_BASE == 28

    def test_edge_offset_at_24(self):
        assert _ADDR_PCK_EDGE_OFF0 == 24

    def test_tile_row_map_at_20(self):
        assert _ADDR_TILE_ROW_MAP0 == 20

    def test_addrmod_pack_at_37(self):
        assert _ADDR_ADDRMOD_PACK0 == 37

    def test_dest_target_reg_at_180(self):
        assert _ADDR_DEST_TGT_BASE == 180

    def test_unp_ctrl_xy0_at_44(self):
        assert _ADDR_UNP0_CTRL_XY0 == 44

    def test_unp1_ctrl_xy0_at_46(self):
        assert _ADDR_UNP1_CTRL_XY0 == 46

    def test_unp0_base0_at_48(self):
        assert _ADDR_UNP0_BASE0 == 48

    def test_unp1_base0_at_60(self):
        assert _ADDR_UNP1_BASE0 == 60
