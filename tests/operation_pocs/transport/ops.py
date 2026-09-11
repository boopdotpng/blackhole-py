"""Allocation-scoped transport emitters; lengths are runtime element counts."""
from asm import Asm
from isa import R, Reg, Tensix as TT, is_reg
from tests.movement.unpacker import unpack as u
from tests.movement.packer.pack import emit_pack_dst_to_cb


def copy_bytes(k: Asm, source: int, destination: int, count: Reg):
  """Exact byte copy, disjoint L1 ranges. No loads beyond count."""
  src, dst, value = k.reg(3)
  k.li(src, source)
  k.li(dst, destination)
  for _ in k.range(count):
    k.lbu(value, src)
    k.sb(value, dst)
    k.addi(src, src, 1)
    k.addi(dst, dst, 1)
  k.fence()


def stage_prefix(k: Asm, source: int, scratch: int, count: Reg, *, input_format=u.F32, capacity=128):
  """Own capacity*4+64 bytes scratch. Exact-N read and device zero fill.

  Scratch retains the input BF16/FP32 representation; the unpack engine
  converts it for source registers. Extra 64 bytes are initialized read padding.
  """
  if input_format not in (u.BF16, u.F32): raise ValueError("BF16 or FP32 required")
  if capacity not in (128, 256): raise ValueError("capacity must be 128 or 256")
  if not is_reg(count): raise TypeError("runtime element count required")
  if scratch % 16: raise ValueError("scratch must be 16-byte aligned")
  size = 2 if input_format == u.BF16 else 4
  ptr = k.reg()
  k.li(ptr, scratch)
  for _ in k.range((capacity * size + 64) // 4):
    k.sw(R.ZERO, ptr)
    k.addi(ptr, ptr, 4)
  byte_count = k.reg()
  k.slli(byte_count, count, 1 if size == 2 else 2)
  copy_bytes(k, source, scratch, byte_count)


def pack_exact(k: Asm, *, dst_slot: int, output: int, count: Reg,
               scratch: int, output_format=u.F32, profile=None):
  """FP32 Dst slot (0..63) -> exact N (1..128) elements in L1 CB.

  Caller owns a disjoint 576-byte aligned scratch page. Consumes MATH_PACK
  publication once; configuration, pack drain, exact final copy are included.
  Dst is read only. Output address may be byte aligned; scratch must be 16 aligned.
  """
  if type(dst_slot) is not int or not 0 <= dst_slot < 64: raise ValueError("Dst slot 0..63 required")
  if scratch % 16: raise ValueError("scratch must be 16-byte aligned")
  if not is_reg(count): raise TypeError("runtime element count required")
  emit_pack_dst_to_cb(k, dst_slot // 8, scratch, count,
                     dst_element_offset=(dst_slot % 8) * 128,
                     output_format=output_format)
  if profile is not None: profile.record('exact final copy')
  byte_count = k.reg()
  k.slli(byte_count, count, 1 if output_format == u.BF16 else 2)
  copy_bytes(k, scratch, output, byte_count)
  if profile is not None: profile.record('exact final copy')


def unpack_source(k: Asm, *, target: u.UnpackTarget, slot: int, source: int,
                  count: Reg, scratch: int, input_format=u.BF16, capacity=128,
                  publish=True, profile=None):
  """Staged selected SrcA/B allocation; zero-fill to capacity.

  Bank must be unpack-owned with source row counter zero. publish=False permits
  further writes in this bank; publish=True hands it to math. No implicit clears.
  FP32 input is narrowed to BF16 by unpacker (truncate low 16 mantissa bits).
  """
  if target not in (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB): raise ValueError("source bank required")
  if type(slot) is not int or not 0 <= slot < 8: raise ValueError("source slot 0..7 required")
  if capacity == 256 and (target != u.UnpackTarget.SRCA or slot % 2): raise ValueError("aligned A pair required")
  if profile is not None: profile.record('stage and zero fill')
  stage_prefix(k, source, scratch, count, input_format=input_format, capacity=capacity)
  if profile is not None: profile.record('stage and zero fill')
  engine = int(target == u.UnpackTarget.SRCB)
  u.configure_unpacker(k, engine, scratch, input_format, target)
  # Disable SrcRow progression; position each operation explicitly.
  k.write(u._engine_cfg(u.UnpackCfg.OPTIONS, engine), 0x20 | u.BF16)
  k.write(u._engine_cfg(u.UnpackCfg.ADDRESS_XY1, engine), 2 | 32 << 16)
  k.write(u._engine_cfg(u.UnpackCfg.ADDRESS_ZW1, engine), 512)
  if engine == 0:
    destination = 64 + slot * 128
    k.write(u._engine_cfg(u.UnpackCfg.DESTINATION, engine), destination | destination << 16)
  else:
    k.write(u.ADDR_BASE1[engine], slot * 128 * 2)
  k.emit(TT.TTSETADCXX(engine + 1, capacity - 1, 0))
  k.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  u.stall(k, u.Stall.UNPACK, u.Wait.TRISC_CFG)
  k.emit(TT.TTUNPACR(engine, 1, 0, 0, 0, 1, int(publish), 0, 0, 0, 0, 0, 1))
  u.stall(k, u.Stall.UNPACK, u.Wait.UNPACK1 if engine else u.Wait.UNPACK0)
  u.sem_get(k, u.Sem.UNPACK_SYNC)
  u.pc_sync(k)


def unpack_source_scatter(k: Asm, *, target, source, slots, input_format=u.BF16, capacity=128):
  """Direct dense full blocks -> scattered source allocations, one publication.

  Configure once; retain bank ownership across all segments. Completion drains
  protect each destination/base replacement. Short prefixes use unpack_source.
  """
  if target not in (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB): raise ValueError('source bank required')
  if capacity not in (128, 256) or not slots: raise ValueError('nonempty full blocks required')
  if any(type(slot) is not int or not 0 <= slot <= 8 - capacity // 128 for slot in slots):
    raise ValueError('source allocation outside bank')
  if capacity == 256 and (target != u.UnpackTarget.SRCA or any(slot % 2 for slot in slots)):
    raise ValueError('aligned A pairs required')
  engine = int(target == u.UnpackTarget.SRCB)
  u.configure_unpacker(k, engine, source, input_format, target)
  k.write(u._engine_cfg(u.UnpackCfg.OPTIONS, engine), 0x20 | u.BF16)
  k.write(u._engine_cfg(u.UnpackCfg.ADDRESS_XY1, engine), 2 | 32 << 16)
  k.write(u._engine_cfg(u.UnpackCfg.ADDRESS_ZW1, engine), 512)
  k.emit(TT.TTSETADCXX(engine + 1, capacity - 1, 0))
  for index, slot in enumerate(slots):
    u._set_unpack_base(k, engine, source + index * capacity * (2 if input_format == u.BF16 else 4))
    if engine == 0:
      destination = 64 + slot * 128
      k.write(u._engine_cfg(u.UnpackCfg.DESTINATION, engine), destination | destination << 16)
    else:
      k.write(u.ADDR_BASE1[engine], slot * 128 * 2)
    k.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    u.stall(k, u.Stall.UNPACK, u.Wait.TRISC_CFG)
    k.emit(TT.TTUNPACR(engine, 1, 0, 0, 0, 1, int(index == len(slots) - 1), 0, 0, 0, 0, 0, 1))
    u.stall(k, u.Stall.UNPACK, u.Wait.UNPACK1 if engine else u.Wait.UNPACK0)
    u.pc_sync(k)
  u.sem_get(k, u.Sem.UNPACK_SYNC)
  u.pc_sync(k)
