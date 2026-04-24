# =============================================================================
# T2 (pack) pipeline backend — full PACR datapath.
#
# This module implements the 9-stage PACR datapath:
#   Stage 1:  ADC Ch0 Dest index + PackerMask loop
#   Stage 2:  Early format conversion  (→ formats.py)
#   Stage 3:  Edge masking with Tile Position Generator
#   Stage 4:  ReLU (4 modes)
#   Stage 5:  Exponent thresholding
#   Stage 6:  Downsampling
#   Stage 7:  BFP shared-exp assembly  (→ formats.py block-pack functions)
#   Stage 8:  Zero compression + RSI   (simplified — uncompressed path only)
#   Stage 9:  L1 output with 16-byte aligned writes
#
# Config register ADDR32 offsets (state 0):
#   12  PCK0_ADDR_CTRL_XY_REG_0:  Xstride[15:0], Ystride[31:16]
#   13  PCK0_ADDR_CTRL_ZW_REG_0:  Zstride[15:0], Wstride[31:16]
#   14  PCK0_ADDR_CTRL_XY_REG_1:  Ystride[31:16]
#   15  PCK0_ADDR_CTRL_ZW_REG_1:  Zstride[15:0], Wstride[31:16]
#   16  PCK0_ADDR_BASE_REG_0_Base: input base
#   17  PCK0_ADDR_BASE_REG_1_Base: output base
#   18  PCK_DEST_RD_CTRL: Read_32b_data[0], Read_unsigned[1], Read_raw[2], Round_10b_mant[3]
#   20..23  TILE_ROW_SET_MAPPING[0..3]
#   24..27  PCK_EDGE_OFFSET_SEC[0..3]: mask[15:0]
#   28..31  PACK_COUNTERS_SEC[0..3]: pack_reads_per_xy_plane[15:8], pack_yz_transposed[23]
#   37..40  ADDR_MOD_PACK_SEC[0..3]
#   68..71  THCON_SEC0_REG1 (packer 0 config)
#   96..99  packer 1; 116..119 packer 2; 144..147 packer 3
#   2   STACC_RELU: ApplyRelu[5:2], ReluThreshold[21:6]
#   180..183  DEST_TARGET_REG_CFG_PACK_SEC[0..3]
# =============================================================================

import math

from . import formats as _fmt

M32 = 0xFFFFFFFF
from . import cfg_layout as _cfg_layout


# ---------------------------------------------------------------------------
# DataFormat encoding constants (mirroring formats.py for local readability)
# ---------------------------------------------------------------------------

_FMT_FP32   = _fmt.FMT_FLOAT32    # 0
_FMT_FP16   = _fmt.FMT_FLOAT16    # 1
_FMT_BFP8A  = _fmt.FMT_BFP8A     # 2
_FMT_BFP4A  = _fmt.FMT_BFP4A     # 3
_FMT_TF32   = _fmt.FMT_TF32      # 4
_FMT_BF16   = _fmt.FMT_FLOAT16B  # 5
_FMT_BFP8   = _fmt.FMT_BFP8      # 6
_FMT_BFP4   = _fmt.FMT_BFP4      # 7
_FMT_INT32  = _fmt.FMT_INT32     # 8
_FMT_INT16  = _fmt.FMT_INT16     # 9
_FMT_FP8    = _fmt.FMT_FP8      # 10
_FMT_BFP2A  = _fmt.FMT_BFP2A   # 11
_FMT_INT8   = _fmt.FMT_INT8    # 14
_FMT_BFP2   = _fmt.FMT_BFP2   # 15

_FMT_IS_BFP_B = {_FMT_BFP8, _FMT_BFP4, _FMT_BFP2}
_FMT_IS_BFP_A = {_FMT_BFP8A, _FMT_BFP4A, _FMT_BFP2A}
_FMT_IS_BFP   = _FMT_IS_BFP_B | _FMT_IS_BFP_A
_FMT_IS_INT   = {_FMT_INT32, _FMT_INT16, _FMT_INT8}

# Per-packer ADDR32 base offsets for the 4 config words
_PACKER_CFG_BASE = [68, 96, 116, 144]


def _fmt_bytes(fmt):
  """Bytes-per-datum from format bits [1:0]."""
  bits01 = fmt & 3
  if bits01 == 0: return 4   # FP32, TF32, INT32
  if bits01 == 1: return 2   # FP16, BF16, INT16
  return 1                   # all 8-bit formats


# ---------------------------------------------------------------------------
# Tile Position Generator (per-packer, for edge masking)
# ---------------------------------------------------------------------------

class TilePositionGenerator:
  def __init__(self):
    self.x = 0
    self.y = 0
    self.z = 0

  def reset(self):
    self.x = 0
    self.y = 0
    self.z = 0

  def advance(self, reads_per_xy_plane, yz_transposed):
    self.x += 1
    if self.x == 16:
      self.x = 0
      if yz_transposed:
        self.z += 1
        if self.z == reads_per_xy_plane:
          self.z = 0
          self.y += 1
      else:
        self.y += 1
        if self.y == reads_per_xy_plane:
          self.y = 0
          self.z += 1


# ---------------------------------------------------------------------------
# Per-packer L1 stream state
# ---------------------------------------------------------------------------

class _PackerStreamState:
  def __init__(self):
    self.needs_new_address = True
    self.byte_address = 0


class _PackerOutputState:
  """State for one packer's L1 output streams (carried across Concat PACRs)."""
  def __init__(self):
    self.rsi_stream  = _PackerStreamState()
    self.exp_stream  = _PackerStreamState()
    self.data_stream = _PackerStreamState()
    self.data_buf    = []
    self.exp_buf     = []
    self.rsi_entries = []
    self.cur_row_count = 0
    self.tpg = TilePositionGenerator()
    # Packed metadata sideband: accumulated bytes for the current tile, and
    # a queue of completed tiles `(size_bytes, zero_mask)` waiting to be read
    # through the TDMA-RISC FIFO_PACKED_TILE_SIZE / ZEROMASK registers.
    self.tile_bytes = 0
    self.packed_fifo = []


# ---------------------------------------------------------------------------
# Packer class — implements the PACR datapath for all 4 packers
# ---------------------------------------------------------------------------

class Packer:
  """PACR datapath: Dest register → format convert → L1 memory."""

  def __init__(self, dest, cfg=None, adc=None, l1=None):
    """
    dest: DestRegFile
    cfg:  ConfigUnit  (reads cfg[state_id][addr32])
    adc:  list of ADCState (one per thread; packer uses thread 2)
    l1:   Memory for L1 writes (None → no writes)
    """
    self.dest = dest          # kept as public attribute (test/legacy compat)
    self._cfg = cfg
    self._adc = adc           # list[ADCState]; packer thread is index 2
    self._l1  = l1
    # Per-packer output state
    self._packer_state = [_PackerOutputState() for _ in range(4)]

  # ---- Packed metadata sideband (TDMA-RISC FIFO_PACKED_TILE_* registers) ----

  def peek_packed_tile_size(self, packer_idx):
    """Return bytes packed in the oldest queued tile for packer N, or 0 if
    the FIFO is empty.  Matches FIFO_PACKED_TILE_SIZE(N) read semantics: read
    does not pop."""
    fifo = self._packer_state[packer_idx].packed_fifo
    return fifo[0][0] if fifo else 0

  def pop_packed_tile_zeromask(self, packer_idx):
    """Return the zero-mask of the oldest queued tile for packer N and pop the
    FIFO entry.  Matches FIFO_PACKED_TILE_ZEROMASK(N) read semantics: read
    pops one entry (both tile_size and zeromask are consumed)."""
    fifo = self._packer_state[packer_idx].packed_fifo
    if not fifo:
      return 0
    _, zeromask = fifo.pop(0)
    return zeromask

  # -------------------------------------------------------------------------
  # Top-level PACR entry point
  # -------------------------------------------------------------------------

  def handle_pacr(self, d, thread_id=2):
    """Execute one PACR instruction."""
    if self._cfg is None or self._adc is None:
      return  # stub mode: no-op

    # Decode PackerMask from ReadIntfSel [11:8]
    addr_mode  = d.AddrMode  & 3
    flush      = d.Flush     & 1
    last       = d.Last      & 1
    zero_write = d.ZeroWrite & 1
    concat     = d.Concat    & 7   # non-zero = continue current row

    packer_mask = d.ReadIntfSel & 0xF
    if packer_mask == 0:
      # ALL_INTF_ACTIVE uses packer 0's config but reads four consecutive
      # 16-datum rows before applying ADDR_MOD_PACK once.
      adc_unit = self._adc[thread_id].packers
      ch0 = adc_unit.channels[0]
      ch1 = adc_unit.channels[1]
      base_y0 = ch0.y.val
      base_y1 = ch1.y.val
      for i in range(4):
        ch0.y.val = base_y0 + i
        ch1.y.val = base_y1 + i
        self._run_packer(0, thread_id, addr_mode, flush, last, zero_write,
                         concat if i == 0 else 1,
                         apply_addr_mod=False,
                         force_stream_end=(i == 3))
      ch0.y.val = base_y0
      ch1.y.val = base_y1
      self._apply_addr_mod(adc_unit, addr_mode, thread_id)
      return

    for i in range(4):
      if not (packer_mask >> i) & 1:
        continue
      self._run_packer(i, thread_id, addr_mode,
                       flush, last, zero_write, concat)

  # -------------------------------------------------------------------------
  # Single-packer pipeline
  # -------------------------------------------------------------------------

  def _run_packer(self, packer_idx, thread_id, addr_mode,
                  flush, last, zero_write, concat, apply_addr_mod=True,
                  force_stream_end=True):
    cfg_base  = _PACKER_CFG_BASE[packer_idx]
    cfg       = self._read_packer_cfg(cfg_base)
    out_state = self._packer_state[packer_idx]

    # --- Stage 0/1: Compute InputNumDatums and Dest base address ---
    adc_unit = self._adc[thread_id].packers
    ch0 = adc_unit.channels[0]
    ch1 = adc_unit.channels[1]

    if flush:
      input_num_datums = 0
    else:
      # InputNumDatums = Channel[1].X.cr - Channel[0].X.val + 1
      input_num_datums = ch1.x.cr - ch0.x.val + 1
      if input_num_datums < 0:
        input_num_datums = 0

    in_fmt           = cfg['in_data_format']
    out_fmt          = cfg['out_data_format']
    bytes_per_datum  = _fmt_bytes(in_fmt)

    # Compute ADC-based Dest address
    # TODO(spec-ambiguity): cfg_context switching (CfgContext field) not
    # implemented; always uses config state 0.
    x_stride_word = self._cfgr_at(12)
    zw_word       = self._cfgr_at(13)
    xstride       = x_stride_word & 0xFFFF
    ystride       = (x_stride_word >> 16) & 0xFFFF
    zstride       = zw_word & 0xFFFF
    wstride       = (zw_word >> 16) & 0xFFFF
    base0         = self._cfgr_at(16)

    addr = (base0
            + ch0.x.val * xstride
            + ch0.y.val * ystride
            + ch0.z.val * zstride
            + ch0.w.val * wstride)

    # Datum index from address
    adc_x_mask = {4: 0x3, 2: 0x7, 1: 0xF}.get(bytes_per_datum, 0xF)
    if bytes_per_datum > 0:
      datum_index = ((addr // bytes_per_datum) & ~adc_x_mask) + (ch0.x.val & adc_x_mask)
    else:
      datum_index = 0

    # Per-packer Dest offset (double-buffering)
    dest_target_word = self._cfgr_at(180 + packer_idx)
    dest_offset = (dest_target_word & 0xFFFF) << 4   # Offset field × 16
    datum_index += dest_offset

    # Read PCK_DEST_RD_CTRL — use cfg_layout helper
    rd_ctrl       = _cfg_layout.pck_dest_rd_ctrl(self._cfg, 0)
    read_32b      = rd_ctrl.read_32b_data
    read_unsigned = rd_ctrl.read_unsigned
    read_raw      = rd_ctrl.read_int8        # bit 2 = "Read_raw" / "Read_int8"
    round_10b     = rd_ctrl.round_10b_mant

    # Read STACC_RELU — use cfg_layout helper
    relu_cfg      = _cfg_layout.stacc_relu(self._cfg, 0)
    apply_relu    = relu_cfg.apply_relu
    relu_thresh_bits = relu_cfg.relu_threshold

    # Read Exp_threshold from packer config word 3
    exp_thresh_en = cfg['exp_threshold_en']
    exp_threshold = cfg['exp_threshold']

    # Edge masking config — use cfg_layout helpers
    pack_ctr      = _cfg_layout.pack_counters(self._cfg, packer_idx, 0)
    reads_per_xy  = pack_ctr.pack_reads_per_xy_plane
    if reads_per_xy == 0:
      reads_per_xy = 16
    yz_transposed = pack_ctr.pack_yz_transposed

    # Edge mode flag: PCK_EDGE_MODE[0] at ADDR32 19
    edge_mode = self._cfgr_at(19) & 1

    # Concat=0 → start fresh row / fresh tile (reset packed-size accumulator)
    if concat == 0:
      out_state.cur_row_count = 0
      out_state.rsi_entries   = []
      out_state.tile_bytes    = 0

    # --- Collect datums from Dest ---
    datums_out = []
    tpg = out_state.tpg

    for j in range(input_num_datums):
      di  = (datum_index + j) % (self.dest.ROWS * self.dest.COLS)
      row = (di // self.dest.COLS) % self.dest.ROWS
      col = di % self.dest.COLS

      raw = self.dest.bits[row][col] if self.dest.valid[row] else 0

      # --- Stage 2: Early format conversion ---
      if zero_write:
        val_f = 0.0
      elif cfg['source_iface_sel'] and packer_idx == 0:
        # TODO(phase-2): L1 source mode address computation not implemented
        val_f = 0.0
      else:
        val_f = self._early_convert(raw, in_fmt, read_32b, read_raw,
                                    round_10b, read_unsigned)

      # --- Stage 3: Edge masking ---
      val_f = self._apply_edge_mask(val_f, tpg, packer_idx, col, edge_mode)

      # --- Stage 4: ReLU ---
      val_f = self._apply_relu(val_f, apply_relu, relu_thresh_bits, in_fmt)

      # --- Stage 5: Exponent thresholding ---
      if exp_thresh_en:
        val_f = self._apply_exp_threshold(val_f, exp_threshold, in_fmt)

      datums_out.append(val_f)
      tpg.advance(reads_per_xy, yz_transposed)

    # --- Stage 6: Downsampling ---
    ds_mask = cfg['downsample_mask']
    if ds_mask != 0:
      datums_out = self._apply_downsampling(datums_out, ds_mask)

    # --- Stage 7: Late format conversion / BFP shared-exp assembly ---
    exp_bytes, data_bytes = self._late_convert(
        datums_out, in_fmt, out_fmt, cfg['dis_shared_exp_assembler'])

    # --- Stage 8: Zero compression ---
    # TODO(phase-2): zero compression with Concat-chaining RSI not implemented;
    # always writes uncompressed.

    # --- Stage 9: L1 output ---
    if self._l1 is not None and (data_bytes or flush or last):
      stream_flush = flush if force_stream_end else 0
      stream_last = last if force_stream_end else 0
      self._write_l1(packer_idx, cfg, out_state, exp_bytes, data_bytes,
                     stream_flush, stream_last, thread_id)

    # Count bytes packed for this tile — what FIFO_PACKED_TILE_SIZE reports.
    # Includes both data and exponent sections; zero-write PACRs still count
    # (they emit real bytes to L1 even though the values are zero).
    out_state.tile_bytes += len(data_bytes) + len(exp_bytes)

    # --- Post-PACR: AddrMod counter updates ---
    if apply_addr_mod:
      self._apply_addr_mod(adc_unit, addr_mode, thread_id)

    # On flush or last: reset stream state for next tile and push a completed
    # tile entry to the packed-metadata FIFO.  The zero-mask is 0 because the
    # packer does not implement zero compression (see Stage 8 TODO); real HW
    # would pack 32 bits, one per all-zero face.
    if force_stream_end and (flush or last):
      out_state.packed_fifo.append((out_state.tile_bytes, 0))
      out_state.tile_bytes = 0
      out_state.data_stream.needs_new_address = True
      out_state.exp_stream.needs_new_address  = True
      out_state.rsi_stream.needs_new_address  = True
      out_state.data_buf = []
      out_state.exp_buf  = []

  # -------------------------------------------------------------------------
  # Stage 2: Early format conversion
  # -------------------------------------------------------------------------

  def _early_convert(self, raw_bits, in_fmt, read_32b, read_raw, round_10b, read_unsigned):
    """Convert raw Dest bits to intermediate float value."""
    if read_raw:
      # Bitcast / identity path
      if read_32b:
        return _fmt._bits_f32(raw_bits)
      b16 = (raw_bits >> 16) & 0xFFFF
      if in_fmt == _FMT_BF16 or in_fmt in _FMT_IS_BFP_B:
        return _fmt.bf16_to_fp32(b16)
      elif in_fmt == _FMT_FP16 or in_fmt in _FMT_IS_BFP_A:
        return _fmt.fp16_to_fp32(b16)
      elif in_fmt == _FMT_INT8:
        s = (raw_bits >> 7) & 1
        return -0.0 if s else 0.0
      return _fmt._bits_f32(raw_bits)

    # Normal path
    if read_32b:
      f = _fmt._bits_f32(raw_bits)
      if in_fmt == _FMT_BF16 or in_fmt in _FMT_IS_BFP_B:
        return _fmt.bf16_to_fp32(_fmt.fp32_to_bf16(f))
      elif in_fmt == _FMT_TF32 or round_10b:
        return _fmt.tf32_to_fp32(_fmt.fp32_to_tf32(f))
      elif in_fmt == _FMT_INT8:
        val = _fmt._bits_f32(raw_bits)
        if read_unsigned:
          iv = int(max(0, min(255, val)))
          return float(iv)
        else:
          iv = int(max(-127, min(127, val)))
          return float(iv)
      return f  # FP32 identity
    else:
      b16 = (raw_bits >> 16) & 0xFFFF
      if in_fmt == _FMT_BF16 or in_fmt in _FMT_IS_BFP_B:
        # BF16: flush denormals
        e8 = (b16 >> 7) & 0xFF
        if e8 == 0:
          s = (b16 >> 15) & 1
          return -0.0 if s else 0.0
        return _fmt.bf16_to_fp32(b16)
      elif in_fmt == _FMT_FP16 or in_fmt in _FMT_IS_BFP_A:
        return _fmt.fp16_to_fp32(b16)
      elif in_fmt == _FMT_INT8:
        byte = (raw_bits >> 16) & 0xFF
        return float(_fmt.signmag_to_int8(byte))
      return _fmt.bf16_to_fp32(b16)  # default: treat as BF16

  # -------------------------------------------------------------------------
  # Stage 3: Edge masking
  # -------------------------------------------------------------------------

  def _apply_edge_mask(self, val_f, tpg, packer_idx, col, edge_mode):
    """Apply edge mask based on TPG position and per-column mask bits.

    NOTE: The packer test convention (from the branch spec tests) uses:
      ADDR32 20-23 = PCK_EDGE_OFFSET_SEC[0..3]   (16-bit column enable mask)
      ADDR32 24-27 = TILE_ROW_SET_MAPPING[0..3]
    This is the OPPOSITE of what cfg_layout.py documents.  We use raw cfgr_at
    reads here to match the test expectations, rather than the cfg_layout helpers
    which have these two ranges swapped.
    # TODO(spec-ambiguity): clarify ADDR32 20-23 vs 24-27 layout in hw register doc.
    """
    # PCK_EDGE_TILE_ROW_SET_SELECT (ADDR32 19): 2-bit entry per packer
    b_sel_word = self._cfgr_at(19)
    b = (b_sel_word >> (2 * packer_idx)) & 3

    # TILE_ROW_SET_MAPPING[b]: 2-bit mapping per row-within-face
    # (ADDR32 24+b per test convention)
    row_map_word = self._cfgr_at(24 + b)
    y_idx = tpg.y & 7
    c = (row_map_word >> (2 * y_idx)) & 3

    # PCK_EDGE_OFFSET_SEC[c]: 16-bit column enable mask
    # (ADDR32 20+c per test convention)
    edge_mask = self._cfgr_at(20 + c) & 0xFFFF

    if (edge_mask >> col) & 1:
      return val_f
    else:
      return float('-inf') if edge_mode else 0.0

  # -------------------------------------------------------------------------
  # Stage 4: ReLU activation
  # -------------------------------------------------------------------------

  def _apply_relu(self, val_f, apply_relu, thresh_bits, in_fmt):
    """Apply ReLU/activation based on STACC_RELU config."""
    mode = apply_relu & 3
    if mode == 0:
      return val_f  # NO_RELU

    # Parse threshold: FP16 or BF16 depending on intermediate format
    if in_fmt in (_FMT_FP16, _FMT_FP8, _FMT_BFP8A, _FMT_BFP4A, _FMT_BFP2A):
      threshold = _fmt.fp16_to_fp32(thresh_bits)
    else:
      threshold = _fmt.bf16_to_fp32(thresh_bits)

    if mode == 1:   # ZERO_RELU
      return 0.0 if val_f <= 0.0 else val_f
    elif mode == 2:  # MIN_THRESHOLD_RELU
      return 0.0 if val_f <= threshold else val_f
    elif mode == 3:  # MAX_THRESHOLD_RELU
      if val_f <= 0.0:          return 0.0
      if val_f > threshold:     return threshold
      return val_f
    return val_f

  # -------------------------------------------------------------------------
  # Stage 5: Exponent thresholding
  # -------------------------------------------------------------------------

  def _apply_exp_threshold(self, val_f, threshold, in_fmt):
    """Zero datums whose exponent is below threshold."""
    if val_f == 0.0 or (not math.isfinite(val_f)):
      return val_f
    b = _fmt._f32_bits(val_f)
    e = (b >> 23) & 0xFF
    if in_fmt in _FMT_IS_BFP_A or in_fmt in (_FMT_FP16, _FMT_FP8):
      # 5-bit exponent: FP32 bias 127, FP16 bias 15 → offset 112
      e5 = max(0, e - 112)
      if e5 < threshold:
        return 0.0
    else:
      if e < threshold:
        return 0.0
    return val_f

  # -------------------------------------------------------------------------
  # Stage 6: Downsampling
  # -------------------------------------------------------------------------

  def _apply_downsampling(self, datums, ds_mask):
    """Vector compress: rotate ds_mask, keep datums where bit is set."""
    if ds_mask == 0 or ds_mask == 0xFFFF:
      return datums
    result = []
    m = ds_mask & 0xFFFF
    for d in datums:
      if m & 1:
        result.append(d)
      m = ((m >> 1) | ((m & 1) << 15)) & 0xFFFF
    return result

  # -------------------------------------------------------------------------
  # Stage 7: Late format conversion / BFP shared-exp assembly
  # -------------------------------------------------------------------------

  def _late_convert(self, datums, in_fmt, out_fmt, dis_shared_exp):
    """Convert intermediate datums to output format.

    Returns (exp_bytes: list[int], data_bytes: list[int]).

    Routes BFP block-pack operations to formats.py functions.
    """
    if not datums:
      return [], []

    exp_bytes  = []
    data_bytes = []

    if out_fmt in (_FMT_FP32, _FMT_TF32, _FMT_INT32):
      for f in datums:
        if out_fmt == _FMT_TF32:
          b = _fmt.fp32_to_tf32(f) & 0xFFFFFFFF
        else:
          b = _fmt._f32_bits(f)
        data_bytes += [(b >> (8*i)) & 0xFF for i in range(4)]

    elif out_fmt == _FMT_BF16:
      for f in datums:
        b = _fmt.fp32_to_bf16(f)
        data_bytes += [b & 0xFF, (b >> 8) & 0xFF]

    elif out_fmt == _FMT_FP16:
      for f in datums:
        b = _fmt.fp32_to_fp16(f)
        data_bytes += [b & 0xFF, (b >> 8) & 0xFF]

    elif out_fmt == _FMT_FP8:
      for f in datums:
        data_bytes.append(_fmt.fp32_to_fp8_e5m2(f))

    elif out_fmt in (_FMT_INT8, _FMT_INT16):
      bpd = _fmt_bytes(out_fmt)
      for f in datums:
        if bpd == 2:
          iv = int(max(-32767, min(32767, f)))
        else:
          iv = int(max(-127, min(127, f)))
        if iv < 0:
          mag = (-iv) & (0x7FFF if bpd == 2 else 0x7F)
          raw = (1 << (bpd * 8 - 1)) | mag
        else:
          raw = iv & (0x7FFF if bpd == 2 else 0x7F)
        for i in range(bpd):
          data_bytes.append((raw >> (8 * i)) & 0xFF)

    elif out_fmt in _FMT_IS_BFP:
      # BFP: process in groups of 16, route to formats.py block-pack functions
      is_a = out_fmt in _FMT_IS_BFP_A
      mantissa_bits = {
          _FMT_BFP8: 7, _FMT_BFP4: 3, _FMT_BFP2: 1,
          _FMT_BFP8A: 7, _FMT_BFP4A: 3, _FMT_BFP2A: 1,
      }[out_fmt]

      for g_start in range(0, len(datums), 16):
        group = list(datums[g_start:g_start + 16])
        while len(group) < 16:
          group.append(0.0)

        if dis_shared_exp:
          # TODO(spec-ambiguity): dis_shared_exp=1 behavior undefined in spec;
          # using shared_exp=0 with truncated mantissa as best approximation.
          shared_exp = 0
          result_bytes = []
          for f in group:
            b16 = _fmt.fp32_to_fp16(f) if is_a else _fmt.fp32_to_bf16(f)
            s = (b16 >> 15) & 1
            result_bytes.append(s << mantissa_bits)
          exp_bytes.append(shared_exp)
          self._pack_mantissa_bytes(result_bytes, out_fmt, mantissa_bits, data_bytes)
        else:
          # Route to formats.py block-pack functions
          if out_fmt == _FMT_BFP8:
            shared_exp, result_bytes = _fmt.pack_bfp8(group)
          elif out_fmt == _FMT_BFP4:
            shared_exp, result_bytes = _fmt.pack_bfp4(group)
          elif out_fmt == _FMT_BFP2:
            shared_exp, result_bytes = _fmt.pack_bfp2(group)
          elif out_fmt == _FMT_BFP8A:
            shared_exp, result_bytes = _fmt.pack_bfp8a(group)
          elif out_fmt == _FMT_BFP4A:
            shared_exp, result_bytes = _fmt.pack_bfp4a(group)
          elif out_fmt == _FMT_BFP2A:
            shared_exp, result_bytes = _fmt.pack_bfp2a(group)
          else:
            shared_exp, result_bytes = 0, [0] * 16
          exp_bytes.append(shared_exp & 0xFF)
          self._pack_mantissa_bytes(result_bytes, out_fmt, mantissa_bits, data_bytes)

    return exp_bytes, data_bytes

  def _pack_mantissa_bytes(self, result_bytes, out_fmt, mantissa_bits, data_bytes):
    """Pack mantissa nibbles/bits into bytes and append to data_bytes in place."""
    if out_fmt in (_FMT_BFP8, _FMT_BFP8A):
      data_bytes += result_bytes
    elif out_fmt in (_FMT_BFP4, _FMT_BFP4A):
      # Two 4-bit nibbles per byte
      for k in range(0, len(result_bytes), 2):
        lo = result_bytes[k] & 0xF
        hi = (result_bytes[k+1] & 0xF) if k+1 < len(result_bytes) else 0
        data_bytes.append(lo | (hi << 4))
    elif out_fmt in (_FMT_BFP2, _FMT_BFP2A):
      # Four 2-bit values per byte
      for k in range(0, len(result_bytes), 4):
        b = 0
        for bit in range(4):
          if k + bit < len(result_bytes):
            b |= (result_bytes[k + bit] & 3) << (bit * 2)
        data_bytes.append(b)

  # -------------------------------------------------------------------------
  # Stage 9: L1 output
  # -------------------------------------------------------------------------

  def _write_l1(self, packer_idx, cfg, out_state, exp_bytes, data_bytes,
                flush, last, thread_id):
    """Write packed data to L1 memory."""
    l1 = self._l1
    if l1 is None:
      return

    # Compute L1 output base address from ADC channel 1 Y/Z/W + packer L1 dest
    xy1_word  = self._cfgr_at(14)
    zw1_word  = self._cfgr_at(15)
    adc_base1 = self._cfgr_at(17)
    y1stride  = (xy1_word >> 16) & 0xFFFF
    z1stride  = zw1_word & 0xFFFF
    w1stride  = (zw1_word >> 16) & 0xFFFF

    # TODO(spec-ambiguity): per-packer ADC channel 1 not separately tracked;
    # using the calling thread's packer ADC for all packers.
    ch1      = self._adc[thread_id].packers.channels[1]
    yzw_addr = (adc_base1
                + ch1.y.val * y1stride
                + ch1.z.val * z1stride
                + ch1.w.val * w1stride)

    l1_dest = cfg['l1_dest_addr']
    if l1_dest & 0x80000000:
      l1_dest_addr16 = l1_dest & 0x1FFFF
      header_words = 0 if cfg['sub_l1_tile_header_size'] else 1
      base_addr = (l1_dest_addr16 + header_words + yzw_addr) << 4
    else:
      base_addr = l1_dest + (yzw_addr & ~0xF)

    exp_section_size       = cfg['exp_section_size']       # in 16-byte words
    row_start_section_size = cfg['row_start_section_size'] # in 16-byte words

    # Initialise data stream address on first call
    if out_state.data_stream.needs_new_address:
      addr  = base_addr
      addr += row_start_section_size * 16
      addr += exp_section_size * 16
      addr  = (addr + 15) & ~15
      out_state.data_stream.byte_address  = addr
      out_state.data_stream.needs_new_address = False

    # Initialise exp stream address
    if out_state.exp_stream.needs_new_address and exp_bytes:
      addr = base_addr + row_start_section_size * 16
      out_state.exp_stream.byte_address  = (addr + 15) & ~15
      out_state.exp_stream.needs_new_address = False

    # Write exponent bytes sequentially
    if exp_bytes:
      ea = out_state.exp_stream.byte_address
      for eb in exp_bytes:
        l1.write8(ea, eb)
        ea += 1
      out_state.exp_stream.byte_address = ea

    # Buffer data bytes and flush in 16-byte aligned chunks
    out_state.data_buf += data_bytes
    self._flush_data_buf(out_state, force=(flush or last))

  def _flush_data_buf(self, out_state, force=False):
    """Flush data buffer to L1, writing in 16-byte chunks."""
    l1  = self._l1
    if l1 is None:
      return
    buf = out_state.data_buf
    ba  = out_state.data_stream.byte_address & ~15

    while len(buf) >= 16:
      for k in range(16):
        l1.write8(ba + k, buf[k])
      buf = buf[16:]
      ba += 16

    if force and buf:
      padded = buf + [0] * (16 - len(buf))
      for k in range(16):
        l1.write8(ba + k, padded[k])
      buf = []
      ba += 16

    out_state.data_buf = buf
    out_state.data_stream.byte_address = ba

  # -------------------------------------------------------------------------
  # AddrMod post-PACR update
  # -------------------------------------------------------------------------

  def _apply_addr_mod(self, adc_unit, addr_mode, thread_id):
    """Apply ADDR_MOD_PACK_SEC[addr_mode] to ADC channel 0 and 1."""
    if addr_mode > 3:
      return
    if hasattr(self._cfg, "thread_cfg"):
      w = self._cfg.thread_cfg[thread_id][37 + addr_mode] & M32
      am = _cfg_layout.AddrModPack(
          y_src_incr  = w & 0xF,
          y_src_cr    = (w >> 4) & 1,
          y_src_clear = (w >> 5) & 1,
          y_dst_incr  = (w >> 6) & 0xF,
          y_dst_cr    = (w >> 10) & 1,
          y_dst_clear = (w >> 11) & 1,
          z_src_incr  = (w >> 12) & 1,
          z_src_clear = (w >> 13) & 1,
          z_dst_incr  = (w >> 14) & 1,
          z_dst_clear = (w >> 15) & 1,
      )
    else:
      am = _cfg_layout.addr_mod_pack(self._cfg, addr_mode, 0)

    ch0 = adc_unit.channels[0]
    ch1 = adc_unit.channels[1]

    # Channel 0 (src / Dest)
    if am.y_src_clear:
      ch0.y.val = 0; ch0.y.cr = 0
    elif am.y_src_cr:
      ch0.y.val, ch0.y.cr = ch0.y.cr, ch0.y.val
    else:
      ch0.y.val = (ch0.y.val + am.y_src_incr) & M32

    if am.z_src_clear:
      ch0.z.val = 0
    elif am.z_src_incr:
      ch0.z.val = (ch0.z.val + 1) & M32

    # Channel 1 (dst / L1)
    if am.y_dst_clear:
      ch1.y.val = 0; ch1.y.cr = 0
    elif am.y_dst_cr:
      ch1.y.val, ch1.y.cr = ch1.y.cr, ch1.y.val
    else:
      ch1.y.val = (ch1.y.val + am.y_dst_incr) & M32

    if am.z_dst_clear:
      ch1.z.val = 0
    elif am.z_dst_incr:
      ch1.z.val = (ch1.z.val + 1) & M32

  # -------------------------------------------------------------------------
  # Config register helpers
  # -------------------------------------------------------------------------

  def _cfgr_at(self, addr32):
    """Read config register at addr32, state 0."""
    if self._cfg is None:
      return 0
    if addr32 < 256:
      return self._cfg.cfg[0][addr32]
    return 0

  def _read_packer_cfg(self, base_addr32):
    """Read per-packer config words into a dict."""
    w0 = self._cfgr_at(base_addr32 + 0)
    w1 = self._cfgr_at(base_addr32 + 1)
    w2 = self._cfgr_at(base_addr32 + 2)
    w3 = self._cfgr_at(base_addr32 + 3)
    return {
        'word0':  w0,
        'word1':  w1,
        'word2':  w2,
        'word3':  w3,
        'row_start_section_size': w0 & 0xFFFF,
        'exp_section_size':       (w0 >> 16) & 0xFFFF,
        'l1_dest_addr':           w1,
        # Word 2 fields
        'uncompress':             (w2 >> 0) & 1,
        'add_l1_dest_addr_offset':(w2 >> 1) & 1,
        'dis_pack_zero_flags':    (w2 >> 2) & 1,
        'out_data_format':        (w2 >> 4) & 0xF,
        'in_data_format':         (w2 >> 8) & 0xF,
        'dis_shared_exp_assembler': (w2 >> 12) & 1,
        'sub_l1_tile_header_size': (w2 >> 15) & 1,
        'source_iface_sel':       (w2 >> 16) & 1,
        'l1_source_addr':         (w2 >> 24) & 0xFF,
        # Word 3 fields
        'downsample_mask':        w3 & 0xFFFF,
        'exp_threshold_en':       (w3 >> 20) & 1,
        'pack_l1_acc':            (w3 >> 19) & 1,
        'exp_threshold':          (w3 >> 16) & 0xFF,
    }
