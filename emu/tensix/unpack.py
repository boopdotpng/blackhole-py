# =============================================================================
# T0 (unpack) pipeline — Phase 1A datapath implementation.
#
# Implements the full UNPACR execution path: L1 reads, format conversion,
# ADC-driven address generation, and row iteration into SrcA/SrcB banks.
#
# Format conversions are routed through emu.tensix.formats where possible;
# a small set of register-layout helpers that formats.py does not export are
# defined locally here (WriteSrc*/WriteDst*).  Config decoding is routed
# through emu.tensix.cfg_layout.
# =============================================================================

from __future__ import annotations
import math as _math

from ..memory import Memory
from . import formats as _fmt
from .formats import (
  FMT_BF16, FMT_BFP, FMT_BFP2, FMT_BFP2A, FMT_BFP4, FMT_BFP4A, FMT_BFP8,
  FMT_BFP8A, FMT_FP16, FMT_FP32, FMT_FP8, FMT_INT16, FMT_INT32, FMT_INT8,
  FMT_TF32,
)
from .cfg_layout import (
  unpack_tile_descriptor as _unpack_tile_descriptor,
  unpack_config          as _unpack_config,
  unpack_l1_base         as _unpack_l1_base,
  unpack_dest_addr       as _unpack_dest_addr,
  unpack_format_override as _unpack_format_override,
  unp_addr_ctrl          as _unp_addr_ctrl,
  alu_format_spec        as _alu_format_spec,
)

M32 = 0xFFFFFFFF


# Address register constants (from pack-unpack-registers.md §2.6)
# Used by test helpers that set up config directly.
_THCON_SEC_BASE = [64, 112]   # UNP0 → SEC0 (base 64), UNP1 → SEC1 (base 112)
_UNP_ADDR_CTRL_XY = [44, 46]  # UNP0: ADDR32 44, UNP1: ADDR32 46
_UNP_ADDR_CTRL_ZW = [45, 47]  # UNP0: ADDR32 45, UNP1: ADDR32 47
_UNP_BASE_REG_1   = [49, 61]  # UNP0: ADDR32 49, UNP1: ADDR32 61


# ---------------------------------------------------------------------------
# Register-layout helpers (WriteSrc* / WriteDst*)
#
# These rearrange IEEE bit-fields into the shuffled 19-bit Src cell format
# or the shuffled Dest cell format.  formats.py has ieee_to_shuffled/
# shuffled_to_ieee but not the BF16/FP16/TF32 variants needed by the
# unpacker; define them locally.
# ---------------------------------------------------------------------------

def _write_src_tf32(x: int) -> int:
  """TF32 19-bit → Src register layout: {Sign[18], Man[17:8], Exp[7:0]}.

  Input x has: bit18=Sign, bits[17:8]=Exp(8-bit), bits[7:0]=Man(10-bit low bits).
  Actually the convention (matching branch code): input is a 19-bit value where
  bit18=Sign, bits[17:8]=Exp, bits[7:0]=Man (the low-order 10 mantissa bits),
  and the output shuffles these as: Sign | (Man<<8) | (Exp>>10).

  Spec ref: DTC.19BIT.SHUFFLED_TO_IEEE (reverse: ieee_to_shuffled)
  """
  sign = x & 0x40000   # bit 18
  exp  = x & 0x3FC00   # bits 17:10 ... wait, spec uses bits[17:8] as Exp(8-bit).
  # From branch code: exp = x & 0x3fc00 (bits 17:8 is 10 bits, mask 0x3FC00 is bits[17:10]).
  # But in the branch code: exp is 0x3fc00 and then Exp>>10 → 8-bit result.
  # So the input encoding is: bit18=Sign, bits[17:10]=Exp(8-bit), bits[7:0]=Man(10-bit).
  # Wait: 0x3FC00 = 0b0 0011 1111 1100 0000 0000 → bits 17:10. That's 8 bits. Yes.
  man  = x & 0x003FF   # bits 9:0 ... but mask 0x003FF = 10 bits
  # Actually looking at branch code exactly:
  #   sign = x & 0x40000   → bit 18
  #   exp  = x & 0x3fc00   → bits 17:10 (8 bits at positions 17..10)
  #   man  = x & 0x003ff   → bits 9:0 (10 bits)
  # But that leaves bit 9 ambiguous. Let's match the branch code exactly.
  return sign | (man << 8) | (exp >> 10)


def _write_src_bf16(x: int) -> int:
  """BF16 16-bit → Src register layout (TF32 form with zero-extended mantissa)."""
  return _write_src_tf32(x << 3)


def _write_src_fp16(x: int) -> int:
  """FP16 16-bit → Src register layout.

  FP16: Sign[15], Exp[14:10](5-bit), Man[9:0].
  Maps to 19-bit input: Sign→bit18, rest packed in lower bits for WriteSrcTF32.
  """
  sign = (x & 0x8000) << 3   # bit 15 → bit 18
  rest = x & 0x7FFF
  return _write_src_tf32(sign | rest)


def _write_dst_fp16(x: int) -> int:
  """FP16 16-bit → Dst register layout: {Sign, Man[9:0], Exp[4:0]}."""
  sign = x & 0x8000
  exp  = x & 0x7C00
  man  = x & 0x03FF
  return sign | (man << 5) | (exp >> 10)


def _write_dst_bf16(x: int) -> int:
  """BF16 16-bit → Dst register layout: {Sign, Man[6:0], Exp[7:0]}."""
  sign = x & 0x8000
  exp  = x & 0x7F80
  man  = x & 0x007F
  return sign | (man << 8) | (exp >> 7)


def _write_dst_fp32(x: int) -> int:
  """FP32 32-bit → Dst register layout: WriteDstBF16(high16) | low16."""
  hi = _write_dst_bf16((x >> 16) & 0xFFFF)
  lo = x & 0xFFFF
  return (hi << 16) | lo


# ---------------------------------------------------------------------------
# Format conversion — full datum transform per spec §3.2
# ---------------------------------------------------------------------------

def _fp32_to_fp16_bits(fp32: int) -> int:
  """Convert FP32 bit-pattern to FP16 bit-pattern (overflow to max finite)."""
  sign = (fp32 >> 31) & 1
  exp32 = (fp32 >> 23) & 0xFF
  man32 = fp32 & 0x7FFFFF
  if exp32 == 0xFF:
    return (sign << 15) | 0x7BFF  # NaN/Inf → max finite (hardware behaviour)
  exp16 = exp32 - 127 + 15
  if exp16 <= 0:
    return sign << 15
  if exp16 >= 31:
    return (sign << 15) | 0x7BFF  # overflow → saturate (not inf)
  man16 = man32 >> 13
  return (sign << 15) | (exp16 << 10) | man16


def _fp8e4m3_to_fp16_bits(fp8: int) -> int:
  """FP8 E4M3 → FP16 bit-pattern.

  # TODO(spec-ambiguity): FP8 E4M3 exact conversion table not fully specified.
  # Using linear rebias: E4M3 bias=7, FP16 bias=15.
  """
  sign = (fp8 >> 7) & 1
  exp8 = (fp8 >> 3) & 0xF
  man8 = fp8 & 0x7
  if exp8 == 0 and man8 == 0:
    return sign << 15
  if exp8 == 0xF:   # NaN in E4M3
    return (sign << 15) | 0x7FFF
  exp16 = exp8 - 7 + 15
  if exp16 <= 0:
    return sign << 15
  if exp16 >= 31:
    return (sign << 15) | 0x7BFF
  man16 = man8 << 7   # 3-bit → 10-bit (zero-pad)
  return (sign << 15) | (exp16 << 10) | man16


def _format_conversion(in_fmt: int, out_fmt: int, datum: int, exp: int,
                        which_unpacker: int, unpack_to_dst: bool,
                        is_unsigned: bool) -> int:
  """Full format conversion per spec §3.2.

  Returns:
    - 19-bit value (masked to 0x7FFFF) for SrcA/SrcB path
    - 16 or 32-bit value for Dst path
  """
  # ---- FP32 input ----
  if in_fmt == FMT_FP32:
    if out_fmt == FMT_TF32:
      if unpack_to_dst:
        return _write_dst_fp32(datum)
      else:
        return _write_src_tf32(datum >> 13)   # drop low 13 bits → 19-bit
    elif out_fmt == FMT_BF16:
      # Flush denormals to ±0 before truncating to BF16
      if not (datum & 0x7F800000):
        datum &= 0x80000000   # keep only sign
      datum >>= 16
      in_fmt = FMT_BF16   # fall through to BF16 layout
    elif out_fmt == FMT_FP16:
      datum = _fp32_to_fp16_bits(datum)
      in_fmt = FMT_FP16   # fall through to FP16 layout
    elif out_fmt == FMT_FP32:
      if unpack_to_dst:
        return _write_dst_fp32(datum)
      else:
        # TODO(spec-ambiguity): FP32→SrcA path not well-defined; treat as TF32
        return _write_src_tf32(datum >> 13)
    else:
      return 0   # undefined behaviour

  else:
    # ---- BFP expansion ----
    if in_fmt in FMT_BFP:
      if in_fmt == FMT_BFP8:
        datum = _fmt.bfp_to_bf16(datum, exp)
        in_fmt = FMT_BF16
      elif in_fmt == FMT_BFP4:
        datum = _fmt.bfp_to_bf16((datum << 4) & 0xFF, exp)
        in_fmt = FMT_BF16
      elif in_fmt == FMT_BFP2:
        datum = _fmt.bfp_to_bf16((datum << 6) & 0xFF, exp)
        in_fmt = FMT_BF16
      elif in_fmt == FMT_BFP8A:
        datum = _fmt.bfpa_to_fp16(datum, exp)
        in_fmt = FMT_FP16
      elif in_fmt == FMT_BFP4A:
        datum = _fmt.bfpa_to_fp16((datum << 4) & 0xFF, exp)
        in_fmt = FMT_FP16
      elif in_fmt == FMT_BFP2A:
        datum = _fmt.bfpa_to_fp16((datum << 6) & 0xFF, exp)
        in_fmt = FMT_FP16
    elif in_fmt == FMT_FP8:
      # FP8 E5M2: shift left 8 to align in FP16 position
      # TODO(spec-ambiguity): when lf8_4b_exp config bit is set, E4M3 mode is
      # used instead of E5M2.  Defaulting to E5M2 here.
      datum = (datum << 8) & 0xFFFF
      in_fmt = FMT_FP16
    elif in_fmt == FMT_INT8:
      sign = datum & 0x80
      mag  = datum - sign   # unsigned magnitude
      if mag:
        mag |= (16 << 10)   # dummy FP16 exponent "8"
      datum = mag | (sign << 8)
      in_fmt = FMT_FP16
    elif in_fmt == FMT_TF32:
      if unpack_to_dst:
        return _write_dst_fp32(datum)
      else:
        return 0   # TF32 source → SrcA undefined

  # ---- Final layout rearrangement ----
  if in_fmt == FMT_INT16:
    if unpack_to_dst:
      return datum & 0xFFFF
    else:
      return ((datum & 0xFF00) << 3) | (datum & 0xFF)
  elif in_fmt == FMT_INT32:
    if unpack_to_dst:
      return _write_dst_fp32(datum)
    else:
      return 0
  elif in_fmt == FMT_FP32:
    if unpack_to_dst:
      return _write_dst_fp32(datum)
    else:
      return 0
  elif in_fmt == FMT_BF16:
    if unpack_to_dst:
      return _write_dst_bf16(datum)
    else:
      return _write_src_bf16(datum)
  elif in_fmt == FMT_FP16:
    if unpack_to_dst:
      return _write_dst_fp16(datum)
    else:
      return _write_src_fp16(datum)
  return datum


# ---------------------------------------------------------------------------
# Helper: read live cfg word (config_unit.cfg[state_id][addr32])
# ---------------------------------------------------------------------------

def _cfg_read(cfg_unit, state_id: int, addr32: int) -> int:
  cfg = cfg_unit.cfg[state_id]
  return cfg[addr32] if 0 <= addr32 < len(cfg) else 0


def _read_forced_shared_exp(cfg_unit, state_id: int, which: int) -> int:
  """Read FORCED_SHARED_EXP_shared_exp from unpacker config.

  # TODO(spec-ambiguity): exact ADDR32 for forced shared exp register not
  # found in pack-unpack-registers.md. Using sec_base + 16 as a placeholder
  # (no hardware source confirmed). This allows tests to inject the value.
  """
  sec_base = _THCON_SEC_BASE[which]
  return _cfg_read(cfg_unit, state_id, sec_base + 16) & 0xFF


# ---------------------------------------------------------------------------
# Per-unpacker runtime state
# ---------------------------------------------------------------------------

class UnpackerState:
  """Runtime state for one hardware unpacker (0=SrcA, 1=SrcB).

  Tracks per-thread SrcRow offsets and context counters across UNPACR calls.
  """
  def __init__(self):
    # SrcRow offset per thread (3 threads × 1 unpacker)
    self.src_row = [0, 0, 0]
    # Context counter per thread (used in MultiContextMode)
    self.context_counter = [0, 0, 0]


def _read_datum_from_l1(mem: Memory, addr: int, fmt: int) -> int:
  """Read a single datum from L1 at byte address for the given format."""
  if fmt in (FMT_FP32, FMT_INT32, FMT_TF32):
    return mem.read32(addr)
  elif fmt in (FMT_FP16, FMT_BF16, FMT_INT16):
    return mem.read16(addr)
  else:
    return mem.read8(addr)   # 1-byte; fractional formats handled by caller


def _ceil16(n: int) -> int:
  """Round n up to the next multiple of 16."""
  return (n + 15) & ~15


# ---------------------------------------------------------------------------
# Unpacker — the T0 pipeline backend
# ---------------------------------------------------------------------------

class Unpacker:
  def __init__(self, srca, srcb, l1: Memory = None, config_unit=None):
    self.srca = srca
    self.srcb = srcb
    # L1 reference — injected by the Tensix frontend; may be None for NOP-only use.
    self._l1 = l1
    self._cfg = config_unit

  def handle_unpacr(self, d, thread_id: int = 0, coproc=None):
    """Execute UNPACR: read L1, convert format, write SrcA/SrcB or Dest.

    When called from the cycle frontend dispatch, `coproc` is always provided.
    The old signature (just `d`) is kept for backward compat in NOP-only callers.
    """
    if coproc is not None:
      _execute_unpacr(d, thread_id, coproc)
    else:
      # Legacy path: only bank flip side-effect (Phase 0 behaviour)
      if d.SetDatValid:
        (self.srca if d.Unpack_block_selection == 0 else self.srcb).flip_to_fpu()

  def handle_unpacr_nop(self, d):
    """Execute UNPACR_NOP: bank flip and/or Src bank clear (no L1 access)."""
    if d.Set_Dvalid & 1:
      (self.srca if d.Unpacker_Select == 0 else self.srcb).flip_to_fpu()
    clr = d.Src_ClrVal_Ctrl
    if clr & 1: _clear_src_bank(self.srca)
    if clr & 2: _clear_src_bank(self.srcb)


def _clear_src_bank(srcregfile):
  """Zero all rows in the current unpack bank."""
  bank = srcregfile.banks[srcregfile.unpack_bank]
  for r in range(64):
    for c in range(16):
      bank.rows[r][c] = 0


# ---------------------------------------------------------------------------
# Full UNPACR datapath (Phase 1A)
# ---------------------------------------------------------------------------

def _execute_unpacr(d, thread_id: int, coproc) -> None:
  """Execute the UNPACR instruction datapath — 6 phases per spec §2.

  d           — decoded UNPACR instruction
  thread_id   — calling thread (TRISC0 = thread 0 for unpackers)
  coproc      — Tensix frontend (provides l1, config_unit, srca, srcb,
                dest, adc, unpackers)
  """
  which_unp = d.Unpack_block_selection  # 0=SrcA/Dst, 1=SrcB
  flip_src  = bool(d.SetDatValid)
  zero_all  = bool(d.ZeroWrite2)       # AllDatumsAreZero

  # AddrMode encodes: Ch1YInc[7:6] | Ch1ZInc[5:4] | Ch0YInc[3:2] | Ch0ZInc[1:0]
  addr_mode = d.AddrMode
  ch0z_inc  = (addr_mode >> 0) & 0x3
  ch0y_inc  = (addr_mode >> 2) & 0x3
  ch1z_inc  = (addr_mode >> 4) & 0x3
  ch1y_inc  = (addr_mode >> 6) & 0x3

  # AutoIncContextID: if set, use context counter (MultiContextMode)
  multi_ctx   = bool(d.AutoIncContextID)
  use_counter = bool(d.AutoIncContextID)
  ctx_number  = d.CfgContextId
  ctx_adc     = d.AddrCntContextId

  # ------------------------------------------------------------------
  # Phase 1: Config selection
  # ------------------------------------------------------------------
  cfg_unit = coproc.config_unit
  cfg_state_id = cfg_unit._state_id(thread_id)
  mem = coproc.l1

  # Decode tile descriptor and unpack config via cfg_layout
  td = _unpack_tile_descriptor(cfg_unit, which_unp, cfg_state_id)
  uc = _unpack_config(cfg_unit, which_unp, cfg_state_id)

  unp_state = coproc.unpackers[which_unp]

  # Context selection
  if multi_ctx:
    if use_counter:
      which_ctx = unp_state.context_counter[thread_id]
    else:
      which_ctx = ctx_number
    which_adc = ctx_adc
  else:
    which_ctx = coproc.config_unit.thread_cfg[thread_id][41] & 1
    which_adc = thread_id   # ADC set = current thread

  # IsUncompressed
  if multi_ctx:
    ctx_bit = (uc.uncompress_cntx0_3 >> which_ctx) & 1
    is_uncompressed = bool(ctx_bit)
  else:
    is_uncompressed = bool(td.uncompressed)

  dest_cfg = _unpack_dest_addr(cfg_unit, which_unp, cfg_state_id)

  # Tile dimensions (minimum 1).  LLK sets SrcA descriptor x_dim to 0 and
  # supplies the active per-context face size through REG5.
  tile_x_dims = (
    dest_cfg['tile_x_dim_cntx0'],
    dest_cfg['tile_x_dim_cntx1'],
    dest_cfg['tile_x_dim_cntx2'],
    dest_cfg['tile_x_dim_cntx3'],
  )
  x_dim = tile_x_dims[which_ctx] if which_ctx < len(tile_x_dims) else 0
  if x_dim == 0:
    x_dim = td.x_dim
  y_dim = max(td.y_dim, 1)
  z_dim = max(td.z_dim, 1)
  w_dim = max(td.w_dim, 1)

  in_fmt  = td.in_data_format
  out_fmt = uc.out_data_format

  dsz = _fmt.datum_size_bytes(in_fmt)

  # ------------------------------------------------------------------
  # Phase 2: Input address computation
  # ------------------------------------------------------------------
  # REG3 holds L1 base addresses for contexts 0 and 1
  ctx0_base, ctx1_base = _unpack_l1_base(cfg_unit, which_unp, cfg_state_id)
  base_addr = ctx1_base if which_ctx == 1 else ctx0_base

  # REG7 offset address
  fmt_ovrd = _unpack_format_override(cfg_unit, which_unp, cfg_state_id)
  offset_addr = (
    fmt_ovrd['offset_cntx1_address'] if which_ctx == 1
    else fmt_ovrd['offset_address'])

  in_addr = base_addr + (offset_addr & 0xFFFF)

  # Skip tile header: (base + offset + 1 + digest_size) * 16
  # digest_size defaults to 0 (TODO: spec does not expose DigestSize explicitly)
  digest_size = 0
  in_addr = (in_addr + 1 + digest_size) * 16   # now in bytes

  # For compressed tiles: RSI section
  in_addr_row_start = None
  if not is_uncompressed:
    in_addr_row_start = in_addr
    if td.blobs_per_xy_plane:
      num_rows = td.blobs_per_xy_plane * z_dim * w_dim
    else:
      num_rows = y_dim * z_dim * w_dim
    in_addr += _ceil16((num_rows + 1) * 2)

  # For BFP: exponent section
  in_addr_exp = None
  force_shared = bool(uc.force_shared_exp)
  if in_fmt in FMT_BFP and not force_shared:
    in_addr_exp = in_addr
    # BFP8/BFP8A always have exp section; BFP4/BFP2 only if not NoBFPExpSection.
    # TODO(spec-ambiguity): NoBFPExpSection bit location not found in cfg_layout
    # definitions.  Treating it as always False (exp section always present for
    # all BFP formats when force_shared_exp=0).  Hardware may skip the exp
    # section for BFP4/BFP2 under certain tile-descriptor conditions.
    no_bfp_exp_section = False
    if not no_bfp_exp_section:
      num_elems = x_dim * y_dim * z_dim * w_dim
      num_exps  = _math.ceil(num_elems / 16.0)
      in_addr  += _ceil16(num_exps)

  # ADC channels
  adc_in  = coproc.adc[which_adc].unpackers[which_unp].channels[0]   # input ch0
  adc_zw  = coproc.adc[thread_id].unpackers[which_unp].channels[0]   # Z/W from thread
  adc_out = coproc.adc[thread_id].unpackers[which_unp].channels[1]   # output ch1

  # FirstDatum computation
  if is_uncompressed:
    x_pos  = adc_in.x.val
    y_pos  = adc_in.y.val
    x_end  = adc_out.x.val + 1
    first_datum      = ((adc_zw.w.val * z_dim + adc_zw.z.val) * y_dim + y_pos) * x_dim + x_pos
    input_num_datums = x_end - x_pos
  else:
    # Compressed: RSI table lookup
    if in_addr_row_start is not None:
      row_start    = in_addr_row_start + (adc_zw.w.val * z_dim + adc_zw.z.val) * y_dim * 2
      row_idx      = adc_in.y.val & 0xFF
      first_datum  = mem.read16(row_start + row_idx * 2)
      next_datum   = mem.read16(row_start + (row_idx + 1) * 2)
      input_num_datums = next_datum - first_datum
    else:
      first_datum      = 0
      input_num_datums = x_dim

  # Datum byte pointer
  in_addr_datums = in_addr + int(first_datum * dsz)

  # Exponent pointer (fractional: one byte shared per 16 datums)
  in_addr_exp_frac = None
  if in_addr_exp is not None:
    in_addr_exp_frac = float(in_addr_exp) + first_datum / 16.0

  # FIFO circular wrap
  limit_addr = uc.limit_addr * 16
  fifo_size  = uc.fifo_size  * 16

  def _wrap(addr_int: int) -> int:
    if limit_addr and addr_int > limit_addr:
      return addr_int - fifo_size
    return addr_int

  def _wrap_frac(addr_frac: float) -> float:
    floor_addr = int(addr_frac)
    if limit_addr and floor_addr > limit_addr:
      return addr_frac - fifo_size
    return addr_frac

  if in_addr_exp_frac is not None:
    in_addr_exp_frac = _wrap_frac(in_addr_exp_frac)
  in_addr_datums = _wrap(in_addr_datums)

  # ------------------------------------------------------------------
  # Phase 3: Output address computation
  # ------------------------------------------------------------------
  addr_ctrl = _unp_addr_ctrl(cfg_unit, cfg_state_id)

  if which_unp == 0:
    dest_addrs = (
      dest_cfg['dest_cntx0_address'],
      dest_cfg['dest_cntx1_address'],
      dest_cfg['dest_cntx2_address'],
      dest_cfg['dest_cntx3_address'],
    )
    out_base = dest_addrs[which_ctx] if which_ctx < len(dest_addrs) else 0
    out_base *= int(_fmt.datum_size_bytes(out_fmt))
    y_stride = addr_ctrl.unp0_ch0_y_stride
    z_stride = addr_ctrl.unp0_ch0_z_stride
    w_stride = addr_ctrl.unp0_ch0_w_stride
  else:
    dest_addrs = (
      dest_cfg['dest_cntx0_address'],
      dest_cfg['dest_cntx1_address'],
      dest_cfg['dest_cntx2_address'],
      dest_cfg['dest_cntx3_address'],
    )
    out_base = dest_addrs[which_ctx] if which_ctx < len(dest_addrs) else 0
    out_base *= int(_fmt.datum_size_bytes(out_fmt))
    y_stride = addr_ctrl.unp1_ch0_y_stride
    z_stride = addr_ctrl.unp1_ch0_z_stride
    w_stride = addr_ctrl.unp1_ch0_w_stride

  out_addr = (out_base
              + adc_out.y.val * y_stride
              + adc_out.z.val * z_stride
              + adc_out.w.val * w_stride)

  # Scale by output element size
  if out_fmt in (FMT_FP32, FMT_TF32, FMT_INT32):
    out_addr >>= 2
  elif out_fmt in (FMT_FP16, FMT_BF16, FMT_INT16):
    out_addr >>= 1
  # else byte-addressed (FP8, INT8)

  # Detect unpack-to-dest path (unpacker 0, 32-bit output)
  unpack_to_dst = (which_unp == 0 and out_fmt in (FMT_FP32, FMT_TF32, FMT_INT32))

  # ColShift: TODO(spec-ambiguity) — exact register source for ColShift is not
  # specified in pack-unpack-registers.md. Treating as 0.
  col_shift = 0

  # ------------------------------------------------------------------
  # Phase 4: Row stride computation
  # ------------------------------------------------------------------
  if uc.tileize_mode:
    # TileizeMode: RowStride = shift_amount << 4 bytes
    row_stride_bytes = uc.shift_amount << 4
  else:
    # Contiguous: one face row of 16 elements
    row_stride_bytes = int(dsz * 16)

  # Transpose flag (haloize_mode = XY transpose)
  do_transpose = bool(uc.haloize_mode)

  # SrcA address override is programmed by the matmul LLK with
  # TTI_SETC16(SRCA_SET_Base_ADDR32, 0x4).  On Blackhole that value is the
  # SetOvrdWithAddr bit, not a 4-row base field.  When it is set, ch1's
  # per-context destination address is an addressing aid; normalize it back
  # to SrcA row zero instead of treating the leading rows as tile data.
  srca_addr_override = bool(coproc.config_unit.thread_cfg[thread_id][5] & 0x4)
  srca_row_rebase = 0
  if which_unp == 0 and srca_addr_override:
    srca_row_rebase = (dest_addrs[which_ctx] if which_ctx < len(dest_addrs) else 0) // 16

  # SrcRow base: SRCA_SET_Base/SRCB_SET_Base are separate low bits.  Matmul
  # leaves them at zero while using SetOvrdWithAddr above.
  src_row_base = 0

  # Unsigned mode from ALU_FORMAT_SPEC
  alu = _alu_format_spec(cfg_unit, cfg_state_id)
  is_unsigned = bool(alu.srca_unsigned if which_unp == 0 else alu.srcb_unsigned)

  # ------------------------------------------------------------------
  # Phase 5: Main unpack loop
  # ------------------------------------------------------------------
  bank = (coproc.srca if which_unp == 0 else coproc.srcb).unpack_bank

  cur_out_addr = out_addr
  exp_frac     = in_addr_exp_frac

  # Sub-byte tracking for BFP4 (4 bits/datum) and BFP2 (2 bits/datum)
  byte_addr  = in_addr_datums
  bit_offset = 0

  for i in range(input_num_datums):
    # Read datum from L1
    if dsz >= 1.0:
      datum_bits = _read_datum_from_l1(mem, byte_addr, in_fmt)
      byte_addr += int(dsz)
    elif dsz == 0.5:
      # BFP4: 2 datums per byte; high nibble first
      raw_byte = mem.read8(byte_addr)
      if bit_offset == 0:
        datum_bits = (raw_byte >> 4) & 0xF
        bit_offset = 4
      else:
        datum_bits = raw_byte & 0xF
        bit_offset = 0
        byte_addr += 1
    else:
      # BFP2: 4 datums per byte; MSB first
      raw_byte = mem.read8(byte_addr)
      datum_bits = (raw_byte >> (6 - bit_offset)) & 0x3
      bit_offset += 2
      if bit_offset >= 8:
        bit_offset = 0
        byte_addr += 1

    # Row stride advance every 16 elements (at the boundary, before reading the next)
    if (i + 1) % 16 == 0 and i + 1 < input_num_datums:
      if dsz >= 1.0:
        # Jump from end of this row to start of next: back out 16-element stride,
        # then add RowStride bytes.
        byte_addr -= int(dsz * 16)
        byte_addr += int(row_stride_bytes)
        byte_addr = _wrap(byte_addr)
      # TODO(spec-ambiguity): row stride wrap for fractional datum sizes (BFP4/BFP2)

    # Read BFP shared exponent
    exp_bits = 0
    if in_fmt in FMT_BFP:
      if force_shared:
        exp_bits = _read_forced_shared_exp(cfg_unit, cfg_state_id, which_unp)
      elif exp_frac is not None:
        exp_bits = mem.read8(int(exp_frac))
        exp_frac += 1.0 / 16.0
        # Wrap fractional exponent pointer
        exp_frac = _wrap_frac(exp_frac)

    # Format conversion
    datum = _format_conversion(in_fmt, out_fmt, datum_bits, exp_bits,
                               which_unp, unpack_to_dst, is_unsigned)

    # AllDatumsAreZero override
    if zero_all:
      datum = 0

    row = cur_out_addr // 16
    col = cur_out_addr & 15
    cur_out_addr += 1

    if which_unp == 1:
      # SrcB path: no header-row skip; src_row offset applied directly
      eff_row = (row + unp_state.src_row[thread_id]) & 0x3F
      coproc.srcb.banks[bank].rows[eff_row][col] = datum & 0x7FFFF

    else:
      # SrcA or Dest path
      if not unpack_to_dst:
        # SrcA path: apply the configured address override/rebase and ColShift.
        # This is not skipping tile header rows; tile headers are handled on
        # the L1 input side by the base+offset+1 computation above.
        if row < srca_row_rebase or col < col_shift:
          continue
        row -= srca_row_rebase
        col -= col_shift
        row += unp_state.src_row[thread_id]
        if do_transpose:
          row_low = row & 0xF
          row_low, col = col, row_low
          row = (row & ~0xF) | row_low
        eff_row = row & 0x3F
        coproc.srca.banks[bank].rows[eff_row][col] = datum & 0x7FFFF
      else:
        # Unpack-to-Dest path
        row -= 4
        row &= 0x3FF
        dest_row = row % coproc.dest.ROWS
        dest_col = col
        if out_fmt in (FMT_FP32, FMT_TF32, FMT_INT32):
          coproc.dest.bits[dest_row][dest_col] = datum & M32
        else:
          coproc.dest.bits[dest_row][dest_col] = datum & 0xFFFF
        coproc.dest.valid[dest_row] = True

  # ------------------------------------------------------------------
  # Phase 6: Post-instruction counter updates
  # ------------------------------------------------------------------

  # Context counter increment (MultiContextMode)
  if multi_ctx and use_counter:
    ctx_limit = 1 << uc.context_count
    next_ctx = (which_ctx + 1) % ctx_limit
    unp_state.context_counter[thread_id] = next_ctx

  # ADC Y and Z increments (applies to both thread ADC sets involved)
  for adc_thread in sorted({thread_id, which_adc}):
    adc_unit = coproc.adc[adc_thread].unpackers[which_unp]
    adc_unit.channels[0].y.val = (adc_unit.channels[0].y.val + ch0y_inc) & M32
    adc_unit.channels[0].z.val = (adc_unit.channels[0].z.val + ch0z_inc) & M32
    adc_unit.channels[1].y.val = (adc_unit.channels[1].y.val + ch1y_inc) & M32
    adc_unit.channels[1].z.val = (adc_unit.channels[1].z.val + ch1z_inc) & M32

  # Bank flip / SrcRow advance
  if flip_src:
    (coproc.srca if which_unp == 0 else coproc.srcb).flip_to_fpu()
    unp_state.src_row[thread_id] = src_row_base
  elif uc.unpack_src_reg_set_upd:
    unp_state.src_row[thread_id] = (unp_state.src_row[thread_id] + 16 + src_row_base) & M32
