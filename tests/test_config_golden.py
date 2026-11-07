# Golden check: blackhole-py's own config helpers vs config.py dataclasses, bit for bit, no hardware.
import sys, pathlib, itertools
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT.parent / "blackhole-py"), str(ROOT)]  # blackhole-py first: both have a pcie.py
from config import *
from ttko import DType, Dst
from ttko.unpack import Unpack, UnpackTarget
from ttko.pack import Pack

CFG, REGFILE, MOP = 0xFFEF0000, 0xFFE00000, 0xFFB80000

class Recorder:
  """Stands in for a kernel builder: records register state instead of emitting code."""
  def __init__(self, role, thread):
    self.role, self.thread, self.state = role, thread, {}
    self.mop_words, self.thread_cfg = None, {}  # build-time shadows a fresh Asm starts with
  def put(self, key, value, mask=0xFFFFFFFF):
    old = self.state.get(key, 0)
    self.state[key] = (old & ~mask) | (value & mask)
  def write(self, addr, value, *a, **k):
    if CFG <= addr < CFG + 0x10000:
      self.put((Space.MMIO, None, addr), value)
    elif REGFILE <= addr < REGFILE + 0x1000: self.put((Space.MMIO, None, REGFILE_BASE + REGFILE_STRIDE * self.thread + addr - REGFILE), value)
    elif MOP <= addr < MOP + 64: self.put((Space.MMIO, self.thread, addr), value)
  def write_block(self, writes, *a, **k):
    for addr, value in writes: self.write(int(addr), int(value) & 0xFFFFFFFF)
  def emit(self, word, *a, **k):
    word = int(word); op = word >> 24
    if op == 0xB2: self.put((Space.MMIO, None, thread_cfg_address(self.thread, word >> 16 & 0xFF)), word & 0xFFFF, 0xFFFF)  # SETC16
    elif 0xB3 <= op <= 0xB6:  # RMWCIBn: mask[23:16] data[15:8] addr32[7:0]
      byte = op - 0xB3; mask, data, a32 = word >> 16 & 0xFF, word >> 8 & 0xFF, word & 0xFF
      self.put((Space.MMIO, None, cfg_address(a32)), data << 8 * byte, mask << 8 * byte)
  def reg(self, n=1, *a, **k): return tuple(_Null() for _ in range(n)) if n > 1 else _Null()
  def __getattr__(self, name):  # scope(), li(), fence(), ... are code-emission details
    return lambda *a, **k: _Null()
class _Null:
  def __enter__(self): return self
  def __exit__(self, *a): return False
  def __getattr__(self, name): return lambda *a, **k: _Null()

def check(recorder, *configs):
  """Every bit a config sets must match what blackhole-py wrote; every word blackhole-py wrote must be fully explained."""
  merged: dict = {}
  for c in configs:
    for k, (v, m) in c.writes().items():
      ov, om = merged.get(k, (0, 0)); assert not (om & m & (ov ^ v)), f"configs disagree at {k}"
      merged[k] = (ov | v, om | m)
  for k, (v, m) in merged.items():
    got = recorder.state.get(k)
    assert got is not None, f"{k}: config writes {v:#x}, blackhole-py never wrote it"
    assert got & m == v, f"{k}: blackhole-py {got & m:#x} vs config {v:#x} (mask {m:#x})"
  unexplained = {k: v for k, v in recorder.state.items() if v & ~merged.get(k, (0, 0))[1]}
  assert not unexplained, "bits written by blackhole-py with no config field: " + ", ".join(f"{k}={v:#x}" for k, v in unexplained.items())

FORMATS = {DType.F32: DataFormat.FLOAT32, DType.F16: DataFormat.FLOAT16, DType.BF16: DataFormat.FLOAT16_B, DType.FP8: DataFormat.LF8}

def unpack_configs(engine, inp, out, target, tilize, tile, x_dim, transpose, dst):
  out = out.register_format
  dx = x_dim if x_dim is not None else 1024 if tilize else 0 if engine == 0 else 256
  size, shift = out.itemsize, 2 * inp.itemsize
  dest = (64 if engine == 0 else 0) + (dst.row_base(tile) * 16 if target == UnpackTarget.DST else 0)
  tx = x_dim if x_dim is not None else 1024 if tilize else 256
  cfg = UnpackerCfg(
    unpacker=engine, fp8_e4m3=inp is DType.FP8,
    src_format=FORMATS[inp], uncompressed=True, blobs_per_xy_plane=0, in_x_dim=dx, in_y_dim=1, in_z_dim=1 if tilize else 4, in_w_dim=0,
    dst_format=FORMATS[inp] if inp.is_fp8 else FORMATS[out], throttle_mode=2, transpose_xy=transpose, tilize=tilize,
    in_x_stride=0, in_y_stride=0, in_z_stride=0, in_w_stride=0,
    out_x_stride=size, out_y_stride=16 * size, out_z_stride=256 * size, out_w_stride=0,
    in_counter_base=0, out_counter_base=0, add_dest_addr_counter=engine == 0, forced_shared_exp=0, nop_clear_value=0)
  # blackhole-py writes contexts 0 and 1 identically
  ctx = [UnpackerContext(unpacker=engine, context=c, dest_address=dest, tile_x_dim=tx, offset_address=0,
                         shift_amount=shift if tilize else 0, disable_zero_compress=True, to_dest=target == UnpackTarget.DST)
         for c in (0, 1)]
  return cfg, *ctx

def test_unpack():
  n = 0
  for engine, inp, out, target, tilize, transpose, x_dim in itertools.product(
      (0, 1), (DType.BF16, DType.F32, DType.FP8, DType.F16), (DType.BF16, DType.F32), (UnpackTarget.SRCA, UnpackTarget.DST),
      (False, True), (False, True), (None, 32)):
    if engine == 1 and target == UnpackTarget.DST: continue
    dst = Dst(fp32=out is DType.F32); rec = Recorder("trisc0", Thread.UNPACK)
    Unpack(rec, dst)._write_mode(engine, inp, out, target, tilize, 1, x_dim=x_dim, transpose=transpose)
    check(rec, *unpack_configs(engine, inp, out, target, tilize, 1, x_dim, transpose, dst)); n += 1
  return n

def test_pack():
  class CB:
    def __init__(self, dtype): self.dtype, self.tile_size = dtype, dtype.tile_size
  n = 0
  for dtype, fp32_dest, scalar in itertools.product((DType.BF16, DType.F32, DType.FP8), (False, True), (False, True)):
    rec = Recorder("trisc2", Thread.PACK)
    Pack(rec, Dst(fp32=fp32_dest))._configure(CB(dtype), fp32_dest, scalar)
    src = DType.F32 if fp32_dest else dtype
    src = DType.F16 if dtype.is_fp8 else src
    size = src.itemsize
    check(rec,
      ThreadCfg(thread=Thread.PACK, state_id=0),
      PackerContext(context=0, fp8_e4m3=dtype is DType.FP8, exp_section_size=0 if dtype.is_fp8 else 4, row_start_section_size=0,
                disable_zero_compress=True, dst_format=FORMATS[dtype], src_format=FORMATS[src], disable_zero_flags=False,
                add_l1_dest_offset=False, packs_per_xy_plane=0, reads_per_xy_plane=16, xys_per_tile=0,
                **{k: False for k in ("disable_shared_exp_assembler", "enable_out_fifo", "sub_tile_header_size", "add_tile_header_size")},
                source_interface=0, l1_source_addr=0, yz_transposed=False, auto_context_inc_xys=0),
      AluCfg(dest_format=FORMATS[src], relu_mode=0, relu_threshold=0),
      PackCommonCfg(read_32b_dest=fp32_dest or src == DType.F32, read_unsigned=False, read_int8=False, round_10b_mantissa=dtype.is_fp8,
                    in_x_stride=0, in_y_stride=16 * size, in_z_stride=256 * size, in_w_stride=1024 * size,
                    row_set_mapping_0=0, row_set_mapping_1=int(scalar), edge_mask_0=0 if scalar else 0xFFFF, edge_mask_1=int(scalar),
                    edge_mode=False, row_set_select_0=int(scalar), row_set_select_1=0, row_set_select_2=0, row_set_select_3=0),
      Gpr(thread=Thread.PACK, reg=16, value=dtype.tile_size >> 4), Gpr(thread=Thread.PACK, reg=52, value=0x40000),
      PackAddrMod(slot=0, y_src_incr=4, y_dst_incr=4),
      PackAddrMod(slot=1, **decode_pack_addr_mod(0x2820)),
      PackAddrMod(slot=2, **decode_pack_addr_mod(0x1120)),
      MopLoop(thread=Thread.PACK, **mop_fields(rec)))
    n += 1
  return n

def decode_pack_addr_mod(word):
  out = {}
  for f in dataclasses.fields(PackAddrMod):
    if "at" in f.metadata:
      _, shift, width = PackAddrMod(slot=0).where(f.name)
      v = word >> shift & (1 << width) - 1
      out[f.name] = bool(v) if f.type == "bool" else v
  return out

def mop_fields(rec):
  names = [f.name for f in dataclasses.fields(MopLoop) if "at" in f.metadata]
  return {n: rec.state[(Space.MMIO, Thread.PACK, MOP + 4 * i)] for i, n in enumerate(names)}

import dataclasses, random

def test_addr_mod():
  from ttko.fpu import Fpu
  rng, n = random.Random(0), 0
  for _ in range(500):
    slot = rng.randrange(8)
    kw = dict(srca=rng.randrange(64), srcb=rng.randrange(64), dest=rng.randrange(1024), fidelity_increment=rng.randrange(4),
              **{k: rng.random() < .5 for k in ("srca_clear", "srca_carry", "srcb_clear", "srcb_carry", "dest_clear", "dest_carry",
                                                "dest_carry_to_carry", "fidelity_clear")})
    rec = Recorder("trisc1", Thread.MATH)
    fake = type("F", (), {"_set_thread_cfg": lambda self, r, v: rec.emit(int.from_bytes(b"", "little") | 0xB2 << 24 | int(r) << 16 | v)})()
    Fpu._set_addr_mod(fake, slot, **kw)
    check(rec, AddrMod(thread=Thread.MATH, slot=slot, srca_incr=kw["srca"], srcb_incr=kw["srcb"], dest_incr=kw["dest"],
                       fidelity_incr=kw["fidelity_increment"], srca_clear=kw["srca_clear"], srca_carry=kw["srca_carry"],
                       srcb_clear=kw["srcb_clear"], srcb_carry=kw["srcb_carry"], dest_clear=kw["dest_clear"], dest_carry=kw["dest_carry"],
                       dest_counter_to_carry=kw["dest_carry_to_carry"], fidelity_clear=kw["fidelity_clear"]))
    n += 1
  return n

def test_sfpu_lane():
  from ttko.sfpu import LaneConfig
  names = {"enable_fp16_infinity": "enable_fp16_infinity", "disable_backdoor_load": "disable_backdoor_load",
           "enable_destination_index": "enable_dest_index", "capture_default_destination_index": "capture_default_dest_index",
           "block_destination_write": "block_dest_write", "block_destination_read": "block_dest_read",
           "destination_read_column_exchange": "dest_read_column_exchange", "destination_write_column_exchange": "dest_write_column_exchange",
           "exchange_srcb_srcc": "exchange_srcb_srcc", "block_destination_move": "block_dest_move", "row_mask": "row_mask"}
  rng, n = random.Random(1), 0
  for _ in range(200):
    kw = {k: (rng.randrange(4) if k == "block_destination_move" else rng.randrange(16) if k == "row_mask" else rng.random() < .5) for k in names}
    want = LaneConfig(**kw).word()
    (k, (v, m)), = SfpuLaneCfg(**{names[a]: b for a, b in kw.items()}).writes().items()
    assert k == (Space.SFPU, None, 15) and v == want, (hex(v), hex(want)); n += 1
  return n

def test_noc_ctrl():
  """NOC_CTRL word vs both blackhole-py NoC paths."""
  from ttko.noc import NoC, NOC
  def ctrl(**kw):
    w = NocCmdBuf(noc=0, buf=0, **kw).writes()
    return w[(Space.MMIO, None, 0xFFB20000 + 0x1C)][0]
  policy = NoC.__new__(NoC)  # path A: the hardcoded request policy
  cases = [("read", {}, dict(cmd=NocCmd.READ)), ("atomic", {}, dict(cmd=NocCmd.ATOMIC)),
           ("write", dict(posted=True), dict(cmd=NocCmd.WRITE, posted=True)), ("write", dict(posted=False), dict(cmd=NocCmd.WRITE, posted=False)),
           ("write", dict(inline=True), dict(cmd=NocCmd.WRITE, inline=True)),
           ("write", dict(posted=True, multicast=True), dict(cmd=NocCmd.WRITE, posted=True, multicast=True, linked=False))]
  for op, a_kw, cfg in cases:
    assert policy._packet_options(op, **a_kw) == ctrl(**cfg), (op, a_kw, hex(policy._packet_options(op, **a_kw)), hex(ctrl(**cfg)))
  # path B constants (examples/matmul_peak_kernel)
  assert NOC.CMD_RD_FIELD == ctrl(cmd=NocCmd.READ)
  assert NOC.CMD_WR_FIELD == ctrl(cmd=NocCmd.WRITE, posted=False)
  assert NOC.CMD_WR_POSTED_FIELD == ctrl(cmd=NocCmd.WRITE, posted=True)
  assert NOC.CMD_INLINE_FIELD == ctrl(cmd=NocCmd.WRITE, inline=True, posted=False)
  assert NOC.CMD_AT_INC_FIELD == ctrl(cmd=NocCmd.ATOMIC)
  mcast = ctrl(cmd=NocCmd.WRITE, posted=False, multicast=True, linked=False)
  return len(cases) + 5, NOC.CMD_WR_MCAST_UNLINK_FIELD ^ mcast

if __name__ == "__main__":
  print("unpack cases:", test_unpack()); print("pack cases:", test_pack())
  print("addr mod cases:", test_addr_mod()); print("sfpu lane cases:", test_sfpu_lane())
  n, mcast_diff = test_noc_ctrl(); print("noc ctrl cases:", n, f"(matmul_peak multicast differs from ttko NoC policy in bits {mcast_diff:#x})")
  print("ok")
