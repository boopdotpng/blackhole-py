from enum import Enum, auto

class Allocator:
  def __init__(self, blocks:int):
    self.blocks = [False] * blocks
    self.allocs: dict[str, list[int]] = {}

  def alloc(self, name:str, blocks:int, group_size:int) -> str:
    selected = []
    for start in range(0, len(self.blocks), group_size):
      if not any(self.blocks[start:start + group_size]):
        selected.extend(range(start, start + group_size))
      if len(selected) == blocks:
        break
    if len(selected) != blocks:
      raise MemoryError("no more blocks to allocate")
    for block in selected:
      self.blocks[block] = True
    self.allocs[name] = selected
    return name

  def release(self, allocation:str):
    for block in self.allocs.pop(allocation):
      self.blocks[block] = False

# Source blocks hold 128 elements. Dst blocks hold 128 physical 16-bit words;
# an aligned pair holds 128 f32 elements (high halves, then low halves).
srcA = Allocator(8)
srcB = Allocator(8)
dst = Allocator(128)

class Dtype(Enum):
  bfloat16 = 2
  float32 = 4

class Fidelity(Enum):
  lofi = (0,)
  hifi2 = (0, 1)

class Broadcast(Enum):
  none = 0
  column = 1
  row = 2
  scalar = 3

class FPU:
  def __init__(self):
    self.ops = []
    self._broadcast = Broadcast.none

  def broadcast(self, mode:Broadcast=Broadcast.none):
    # Persistent ELW srcB selection; other instruction families are unaffected.
    self._broadcast = mode
    return self

  @staticmethod
  def _groups(space:Allocator, allocation:str, size:int):
    blocks = space.allocs[allocation]
    groups = tuple(tuple(blocks[i:i + size]) for i in range(0, len(blocks), size))
    if any(len(g) != size or g[0] % size or g != tuple(range(g[0], g[0] + size)) for g in groups):
      raise ValueError(f"{allocation} needs aligned groups of {size} blocks")
    return groups

  def _record(self, op, a, b, output, dtype, phases=(), count=None):
    d = self._groups(dst, output, dtype.value // 2)
    if count is None:
      count = len(a) if a else len(b)
    if len(d) < count:
      raise ValueError(f"{output} needs space for {count * 128} {dtype.name} elements")
    # Snapshot physical groups. Multiplications lower phase-first across groups.
    mode = self._broadcast if op in ("elwadd", "elwsub", "elwmul") else Broadcast.none
    self.ops.append((op, a, b, d[:count], dtype, phases, mode))
    return output

  def _binary(self, op, a, b, output, dtype, a_group=1, phases=()):
    a = self._groups(srcA, a, a_group)
    b = self._groups(srcB, b, 1)
    if op in ("elwadd", "elwsub", "elwmul") and self._broadcast is not Broadcast.none and len(b) == 1:
      b = b * len(a)  # Reuse one B block's row/column/scalar for every A block.
    if op in ("gapool", "gmpool") and len(b) == 1:
      b = b * len(a)  # Both pools can retain one scaler row across A faces.
    if len(a) != len(b):
      raise ValueError("each A group needs one B block")
    return self._record(op, a, b, output, dtype, phases)

  # Elementwise operations accumulate into Dst; each group produces 128 elements.
  def elwadd(self, a:str, b:str, output:str, dtype:Dtype=Dtype.float32):
    return self._binary("elwadd", a, b, output, dtype)

  def elwsub(self, a:str, b:str, output:str, dtype:Dtype=Dtype.float32):
    return self._binary("elwsub", a, b, output, dtype)

  def elwmul(self, a:str, b:str, output:str, dtype:Dtype=Dtype.float32):
    return self._binary("elwmul", a, b, output, dtype, phases=(0, 1))

  # Full A/B tiles mean D[32x32] += B[32x32] @ A[32x32].
  # Smaller matching groups retain the independent 8x16 @ 16x16 behavior.
  def mvmul(self, a:str, b:str, output:str, dtype:Dtype=Dtype.float32,
            fidelity:Fidelity=Fidelity.hifi2):
    a = self._groups(srcA, a, 2)
    b = self._groups(srcB, b, 1)
    full_tile = len(a) == 4 and len(b) == 8
    if not full_tile and len(a) != len(b):
      raise ValueError("mvmul needs full A/B tiles or one B block per A pair")
    return self._record("mvmul", a, b, output, dtype, fidelity.value,
                        count=8 if full_tile else len(a))

  def _stage_pool_scaler(self, b:str, scratch:str):
    """Record SFPU -> FP32 Dst scratch -> BF16 SrcB reduction weights.

    Both GMPOOL and GAPOOL use a ROW of sixteen ones. GAPOOL also reads
    three more rows, which must be zero to produce only one partial row.
    The caller reserves one B block and one FP32 Dst group as scratch, and
    may reuse B until it is overwritten/released. This is a composition
    record, not executable lowering. Lowering must preserve the caller's
    SFPU predicate, enable all lanes for initialization, fence SFPU stores
    before MOVD2B, and establish/retain math ownership and BF16 format of B.
    """
    if len(self._groups(srcB, b, 1)) != 1:
      raise ValueError("pool scaler needs one SrcB block")
    if len(self._groups(dst, scratch, 2)) != 1:
      raise ValueError("pool scaler needs one FP32 Dst scratch group")
    sfpu = SFPU()
    sfpu.predicate()
    # Fully define scratch before masked stores; ZEROACC is not sufficient.
    for position in range(4):
      sfpu.zero.store(scratch, position=position)
    # Positions 0/1 cover even/odd columns of rows 0..3. Their first eight
    # lanes are row 0; positions 2/3 cover rows 4..7 and stay zero.
    sfpu.predicate(0xff)
    for position in (0, 1):
      sfpu.one.store(scratch, position=position)
    self.ops.append(("stage_pool_scaler", tuple(sfpu.ops)))
    return self.move(dst, scratch, b, destination=srcB, rows=8)

  # Writes the first 64 elements of each reserved 128-element Dst group.
  # _stage_pool_scaler supplies a row of ones plus zero rows for column sums;
  # mean scales the final SFPU sum by 1/N, retaining FP32 partial precision.
  def gapool(self, a:str, b:str, output:str, dtype:Dtype=Dtype.float32):
    return self._binary("gapool", a, b, output, dtype, a_group=2, phases=(0, 1))

  # Planned fpu.sum() composition (not implemented by this recorder yet):
  #   SrcA -> GAPOOL column sums in FP32 Dst -> SFPU horizontal sum -> FP32 Dst.
  # Use _stage_pool_scaler for SrcB weights, and accumulate all
  # 16x16 A blocks into one Dst partial row before the SFPU finish. Lowering
  # owns weight/scratch setup, source precision/fidelity, and FPU/SFPU fences.
  # Keep FP32 partials in Dst/SFPU: Dst -> SrcA/SrcB moves narrow them (BF16
  # in this model's move path, TF32 in the raw benchmark). More GAPOOL/MVMUL
  # fidelity phases cannot recover bits discarded by that transfer. The FPU
  # finish can be faster, but is not equivalent when preserving FP32 partials.
  # SFPLOAD reads even/odd columns of four rows into separate 32-lane LRegs.
  # Add those vectors, then sum the useful eight-lane group using additions
  # of copies rotated by 4, 2, 1 lanes. Rotations may lower to repeated native
  # SFPSHFT2 instructions. The total is replicated within the group; consume
  # one copy, not a sum of those replicas. Other Dst rows must be initialized.
  # For mean, divide the final SFPU sum by the total element count before
  # storing it (multiply by 1/N for a fixed N; powers of two are exact scalers).
  # This preserves accumulator precision, not bits lost on initial unpack.
  # Evidence: tests/compute/fpu/test_sum_finish.py and docs/sum-finish-cycles.md.

  # Max with the first Dst row, clears the next three rows; remaining rows untouched.
  # _stage_pool_scaler disables scaling. ZEROACC the output for a fresh max;
  # numerical zero would win over negative inputs. ELW broadcast is unrelated.
  def gmpool(self, a:str, b:str, output:str, dtype:Dtype=Dtype.float32):
    return self._binary("gmpool", a, b, output, dtype, a_group=2)

  def move(self, source:Allocator, allocation:str, output:str, dtype:Dtype=Dtype.float32,
           *, destination:Allocator=dst, source_row:int=0, destination_row:int=0,
           rows:int | None=None, broadcast:Broadcast=Broadcast.none):
    # Offsets are logical rows within allocations; each row has 16 elements.
    # dtype describes Dst in either direction; Dst-to-source moves produce BF16.
    operations = {(srcA, dst): "mova2d", (srcB, dst): "movb2d",
                  (dst, srcA): "movd2a", (dst, srcB): "movd2b"}
    op = operations.get((source, destination))
    if op is None:
      raise ValueError("move supports srcA/srcB to Dst and Dst to srcA/srcB")
    if broadcast is not Broadcast.none and op != "movb2d":
      raise ValueError("move broadcasting requires srcB to Dst")

    def row_addresses(space, name):
      size = dtype.value // 2 if space is dst else 1
      groups = self._groups(space, name, size)
      return tuple(g[0] // size * 8 + row for g in groups for row in range(8))

    src_rows = row_addresses(source, allocation)
    dst_rows = row_addresses(destination, output)
    repeat_row = broadcast in (Broadcast.row, Broadcast.scalar)
    if rows is None:
      rows = 8 if repeat_row else len(src_rows) - source_row
    read_rows = 1 if repeat_row else rows
    if rows <= 0 or source_row < 0 or source_row + read_rows > len(src_rows):
      raise ValueError("move reads outside the source allocation")
    if destination_row < 0 or destination_row + rows > len(dst_rows):
      raise ValueError("move writes outside the destination allocation")
    reads = src_rows[source_row:source_row + read_rows]
    if repeat_row:
      reads *= rows
    writes = dst_rows[destination_row:destination_row + rows]
    # Hardware-row snapshots let lowering combine aligned runs and preserve gaps.
    # Row/scalar modes repeat a selected row; column/scalar read only column zero.
    self.ops.append((op, reads, writes, dtype, broadcast))
    return output

  def zero(self, output:str, dtype:Dtype=Dtype.float32):
    self.ops.append(("zero", (), (), self._groups(dst, output, dtype.value // 2), dtype, (), Broadcast.none))
    return output

class SFPURegister:
  def __init__(self, sfpu, index:int):
    self.sfpu, self.index = sfpu, index

  def _transfer(self, op, allocation, block, position, dtype):
    if op == "load" and self.index >= 8:
      raise ValueError("SFPLOAD writes only l0-l7")
    if not 0 <= position < 4:
      raise ValueError("a 128-element block has four SFPU vector positions")
    physical = FPU._groups(dst, allocation, dtype.value // 2)[block]
    self.sfpu.ops.append((op, self.index, physical, position, dtype))
    return self

  def load(self, allocation:str, block:int=0, position:int=0, dtype:Dtype=Dtype.float32):
    return self._transfer("load", allocation, block, position, dtype)

  def store(self, allocation:str, block:int=0, position:int=0, dtype:Dtype=Dtype.float32):
    return self._transfer("store", allocation, block, position, dtype)

  # Lowering preserves the FP32 value, using two 16-bit loads when necessary.
  def loadi(self, value:float):
    if self.index >= 8:
      raise ValueError("SFPLOADI writes only l0-l7")
    self.sfpu.ops.append(("loadi", self.index, value))
    return self

  def _op(self, op, *args):
    if self.index >= 8:
      raise ValueError("arithmetic writes only l0-l7; config destinations record macros")
    self.sfpu.ops.append((op, self.index, *(x.index if isinstance(x, SFPURegister) else x for x in args)))
    return self

  def load_bits(self, bits:int): return self._op("load_bits", bits)

  # In-place vector operations: self is both an input and the destination.
  def copy(self, other): return self._op("copy", other)
  def add(self, other): return self._op("add", other)
  def sub(self, other): return self._op("sub", other)
  def mul(self, other): return self._op("mul", other)
  def mad(self, multiplier, addend): return self._op("mad", multiplier, addend)
  def add_scalar(self, value:float): return self._op("add_scalar", value)
  def mul_scalar(self, value:float): return self._op("mul_scalar", value)
  def neg(self): return self._op("neg")
  def abs(self): return self._op("abs")

  # compare overwrites self with a 0/1 lane mask; select computes mask ? self : other.
  def compare(self, other, comparison:str): return self._op("compare", other, comparison)
  def select(self, mask, other): return self._op("select", mask, other)
  def integer(self, other, op:str="add", signed:bool=False): return self._op("integer", other, op, signed)
  def integer_compare(self, other, comparison:str, signed:bool=False):
    return self._op("integer_compare", other, comparison, signed)
  def mul23(self, other, part:str="low"): return self._op("mul23", other, part)
  def bitwise(self, op:str, other=None): return self._op("bitwise", op, other)
  def bitshift(self, direction:str, bits:int): return self._op("bitshift", direction, bits)
  def exponent(self): return self._op("exponent")
  def mantissa(self): return self._op("mantissa")
  def set_exponent(self, other): return self._op("set_exponent", other)
  def set_mantissa(self, other): return self._op("set_mantissa", other)
  def set_sign(self, other): return self._op("set_sign", other)
  def scale_pow2(self, exponent:int): return self._op("scale_pow2", exponent)
  def cast(self, conversion:str, rounding:str="nearest_even"):
    return self._op("cast", conversion, rounding)

  # These refer to SFPU lane order, not flattened row-major tensor order.
  # Widths/distance may need multiple native instructions during lowering.
  def rotate(self, shift:int, group_width:int=8): return self._op("rotate", shift, group_width)
  def shift_lanes_right(self, shift:int=1, group_width:int=8):
    return self._op("shift_lanes_right", shift, group_width)
  def broadcast(self, other, lane:int): return self._op("broadcast", other, lane)
  def butterfly(self, distance:int, group_width:int=8): return self._op("butterfly", distance, group_width)

  def reciprocal_estimate(self): return self._op("reciprocal_estimate")
  def rng_bits(self): return self._op("rng_bits")

  # Library compositions, recorded here and expanded by future lowering.
  # Like the primitives above, these mutate self and return it. They are NOT
  # native opcodes or implemented numerical kernels yet. Lowering owns scratch
  # allocation/spills and must preserve other live registers and inactive lanes.
  # Accuracy and special-value handling remain to be specified per composition.
  # Estimate y, then refine with y <- y * (2 - x*y).
  def reciprocal(self): return self._op("reciprocal")
  def div(self, other): return self._op("div", other)

  def rsqrt(self):
    """Record 1/sqrt(self); Blackhole composition, not a native instruction.

    Candidate fast core for positive normal FP32 x (see llama3_row_major.py):
      y = as_float(0x5f1110a0 - (as_uint(x) >> 1))
      c = (x * y) * y
      y = y * (2.2825186 - c * (2.2533049 - c))
      y = y + (0.5 * y) * (1 - (x * y) * y)

    as_uint/as_float reinterpret bits; they are not numeric casts. Lowering
    must separately handle subnormals, signed zero, negative inputs, inf/NaN,
    active predicates, scratch registers and instruction dependency delays.
    No accuracy guarantee is implied until the lowering is tested on device.
    """
    return self._op("rsqrt")

  def sqrt(self): return self._op("sqrt")
  # exp2: split x = n + f, approximate 2**f, then scale by 2**n.
  # exp: exp2(x * log2(e)). log2: exponent + log2(normalized mantissa).
  def exp2(self): return self._op("exp2")
  def exp(self): return self._op("exp")
  def log2(self): return self._op("log2")
  def log(self): return self._op("log")
  def expm1(self): return self._op("expm1")
  def log1p(self): return self._op("log1p")
  def pow(self, other): return self._op("pow", other)
  def sin(self): return self._op("sin")
  def cos(self): return self._op("cos")
  def tanh(self): return self._op("tanh")
  def sigmoid(self): return self._op("sigmoid")
  def silu(self): return self._op("silu")
  def erf(self): return self._op("erf")

  def gelu(self, approximation:str="tanh"):
    # Explicit formula choice: tanh approximation or x/2 * (1 + erf(x/sqrt(2))).
    if approximation not in ("tanh", "erf"):
      raise ValueError("gelu approximation must be tanh or erf")
    return self._op("gelu", approximation)

  def relu(self): return self._op("relu")
  def clamp(self, lower:float, upper:float):
    if not lower <= upper:
      raise ValueError("clamp requires lower <= upper")
    return self._op("clamp", lower, upper)

  # Floating-point outputs; integer conversion is still a separate cast.
  def floor(self): return self._op("floor")
  def ceil(self): return self._op("ceil")
  def trunc(self): return self._op("trunc")
  def round(self): return self._op("round")  # nearest, ties to even
  def isnan(self): return self._op("isnan")  # integer 0/1 mask
  def isinf(self): return self._op("isinf")
  def isfinite(self): return self._op("isfinite")

  # Register-local collectives in consecutive SFPU lane groups, NOT tensor axes.
  # These are compositions, not native horizontal-reduce instructions:
  # SFPADD is lane-wise; lowering must move values between lanes before adding.
  # An eight-lane sum can add rotated copies at distances 4, 2, 1. Wider groups
  # need additional movement between the hardware's eight-lane subgroups.
  # Reduction broadcasts the result to active lanes of each group. Inactive
  # inputs contribute the operation's identity; inactive destinations retain
  # their old values. Scan follows increasing lane number within each group.
  def reduce(self, op:str="sum", group_width:int=32):
    return self._collective("reduce", op, group_width)

  def scan(self, op:str="sum", group_width:int=32, inclusive:bool=True):
    return self._collective("scan", op, group_width, inclusive)

  @staticmethod
  def _check_group_width(group_width):
    if type(group_width) is not int or group_width not in (1, 2, 4, 8, 16, 32):
      raise ValueError("group_width must be a power of two from 1 to 32")

  def _collective(self, name, op, group_width, *args):
    if op not in ("sum", "max", "min", "product"):
      raise ValueError("collective op must be sum, max, min or product")
    self._check_group_width(group_width)
    return self._op(name, op, group_width, *args)

class SFPU:
  SCALE, ZERO, ONE, NEG_ONE = 8, 9, 10, 11
  CONFIG0, CONFIG1, CONFIG2, LANE_ID = 12, 13, 14, 15
  # Exact FP32 bits for fixed scalar constants; L15 instead holds integer 2*lane.
  CONSTANT_BITS = {8: 0x3F56594B, 9: 0x00000000, 10: 0x3F800000}
  LANE_VALUES = tuple(range(0, 64, 2))
  # Installed by SFPCONFIG's default mode, not guaranteed initial contents.
  CONFIG_DEFAULT_BITS = {11: 0xBF800000, 12: 0x3B000000, 13: 0xBF2CC4C7, 14: 0xBEB08FF9}

  def __init__(self):
    self.ops = []
    self.regs = tuple(SFPURegister(self, i) for i in range(16))
    for reg in self.regs:
      setattr(self, f"l{reg.index}", reg)
    self.scale, self.zero, self.one, self.neg_one = self.regs[8:12]
    self.config0, self.config1, self.config2, self.lane_id = self.regs[12:16]

  def configure(self, register:SFPURegister, default:bool=False):
    # Otherwise copy l0 lanes 0-7, repeated across the four SFPU rows.
    if register.index not in self.CONFIG_DEFAULT_BITS:
      raise ValueError("configurable vector registers are l11-l14")
    self.ops.append(("configure", register.index, default))
    return self

  def minmax(self, left:SFPURegister, right:SFPURegister):
    # Two outputs: left becomes min, right becomes max (native float ordering).
    self.ops.append(("minmax", left.index, right.index))
    return left, right

  def transpose(self):
    # SFPTRANSP changes BOTH l0-l3 and l4-l7, independently, within each column.
    self.ops.append(("transpose", tuple(range(8))))
    return self.regs[:8]

  def compare_exchange(self, left, right, left_index, right_index):
    # Descending values, ascending original index for ties; multiple outputs.
    self.ops.append(("compare_exchange", left.index, right.index, left_index.index, right_index.index))
    return left, right, left_index, right_index

  def lut(self, value:SFPURegister, coefficients, table_format:str, retain_sign:bool=False):
    # Coefficients are LRegs; lowering arranges the native instruction's fixed operands.
    self.ops.append(("lut", value.index, tuple(r.index for r in coefficients), table_format, retain_sign))
    return value

  def seed(self, value:int):
    self.ops.append(("seed", value))
    return self

  def predicate(self, mask:int | SFPURegister | None=None):
    # Bit i enables lane i for subsequent loads, stores, and arithmetic.
    # A register mask enables lanes with nonzero values; None enables all lanes.
    # This replaces the previous predicate rather than intersecting it.
    # Lowering materializes the mask; it is not an immediate on SFPLOAD/SFPSTORE.
    self.ops.append(("predicate_register", mask.index) if isinstance(mask, SFPURegister)
                    else ("predicate", mask))
    return self

# min allocation is 128 elements
# 128 f16 slots or 64 f32 slots
class Dst:
  def __init__(self):
    pass

class CB:
  def __init__(self, page_elems:int=1024, depth:int=2,
               dtype:Dtype=Dtype.bfloat16):
    self.page_elems, self.depth, self.dtype = page_elems, depth, dtype
    self.page_bytes = page_elems * dtype.value
    self.size_bytes = depth * self.page_bytes
    # (direction, page, DRAM buffer, buffer byte offset, valid byte count).
    self.ops = []

  def page(self, index:int, elems:int | None=None):
    return CBPage(self, index, self.page_elems if elems is None else elems)

  def pages(self, elements:int):
    for index, start in enumerate(range(0, elements, self.page_elems)):
      yield self.page(index, min(self.page_elems, elements - start))

class CBPage:
  def __init__(self, cb:CB, index:int, elems:int):
    self.cb, self.index, self.elems = cb, index, elems

  @property
  def offset_bytes(self):
    return (self.index % self.cb.depth) * self.cb.page_bytes

  @property
  def valid_bytes(self):
    return self.elems * self.cb.dtype.value

  def _transfer(self, direction:str, dram, offset_bytes:int | None):
    if offset_bytes is None:
      offset_bytes = self.index * self.cb.page_bytes
    self.cb.ops.append((direction, self, dram, offset_bytes, self.valid_bytes))
    return self

  def read_from(self, dram, offset_bytes:int | None=None):
    # Lowering reserves a ring slot, reads valid bytes, then publishes the page.
    return self._transfer("read", dram, offset_bytes)

  def write_to(self, dram, offset_bytes:int | None=None):
    # Lowering waits for the page, writes valid bytes, then releases the ring slot.
    return self._transfer("write", dram, offset_bytes)

class Unpack:
  def __init__(self):
    # (page, space, allocation name, physical blocks, output dtype).
    # Lowering handles queue waits, bank handoff, and operation-specific padding.
    self.ops = []

  def _to(self, page:CBPage, space:Allocator, allocation:str, dtype:Dtype):
    self.ops.append((page, space, allocation, tuple(space.allocs[allocation]), dtype))
    return allocation

  def to_srca(self, page:CBPage, allocation:str, dtype:Dtype=Dtype.bfloat16):
    return self._to(page, srcA, allocation, dtype)

  def to_srcb(self, page:CBPage, allocation:str, dtype:Dtype=Dtype.bfloat16):
    return self._to(page, srcB, allocation, dtype)

  def to_dst(self, page:CBPage, allocation:str, dtype:Dtype | None=None):
    return self._to(page, dst, allocation, page.cb.dtype if dtype is None else dtype)

class Pack:
  def __init__(self):
    # Same record layout as Unpack; dtype describes Dst, page.cb.dtype the output.
    self.ops = []

  def to_cb(self, allocation:str, page:CBPage, dtype:Dtype=Dtype.float32):
    self.ops.append((page, dst, allocation, tuple(dst.allocs[allocation]), dtype))
    return page

class Device:
  def __init__(self, banks:int=8):
    pass
  def alloc():
    pass
