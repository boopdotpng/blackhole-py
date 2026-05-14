
from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Callable

import dsl
import pytest
from emu.device import Device, RUN_MSG_DONE
from emu.kernel_runner import (
  RawKernelCase,
  export_raw_kernel_cases,
  run_add1_raw_kernel,
  run_raw_kernel_case,
)
from emu.matmul_peak_runner import run_matmul_peak
from emu.memory import (
  LAUNCH_MSG_RD_PTR,
  NIU_AT_DATA,
  NIU_AT_LEN_BE,
  NIU_CMD_BUF_STRIDE,
  NIU_CMD_CTRL,
  NIU_CTRL,
  NIU_L1_ACC_AT_INSTRN,
  NIU_MST_ATOMIC_RESP_RECEIVED,
  NIU_RET_ADDR_HI,
  NIU_RET_ADDR_LO,
  NIU_TARG_ADDR_HI,
  NIU_TARG_ADDR_LO,
  NOC0_BASE,
  NOC_CTRL_AT,
  NOC_CTRL_L1_ACC_AT_EN,
  NOC_CTRL_RESP_MARKED,
)
from emu.noc import noc_key
from emu.scratch import HARVESTED_DRAM_BANKS, bf16, f32_from_bf16
from program import Dtype
from dram import tilize, untilize


TILE_HEIGHT = 32
TILE_WIDTH = 32
TILE_ELEMS = TILE_HEIGHT * TILE_WIDTH
TILE_SHAPE = (1, TILE_HEIGHT, TILE_WIDTH)


def fp16_bits(x: float) -> int:
  return struct.unpack("<H", struct.pack("<e", float(x)))[0]


def f32_from_fp16(x: int) -> float:
  return struct.unpack("<e", struct.pack("<H", x & 0xFFFF))[0]


def pack_bf16(values: list[float]) -> bytes:
  return b"".join(bf16(v).to_bytes(2, "little") for v in values)


def pack_fp16(values: list[float]) -> bytes:
  return b"".join(fp16_bits(v).to_bytes(2, "little") for v in values)


def tile_values_bf16(data: bytes) -> list[float]:
  return [f32_from_bf16(int.from_bytes(data[i:i + 2], "little"))
          for i in range(0, len(data), 2)]


def tile_values_fp16(data: bytes) -> list[float]:
  return [f32_from_fp16(int.from_bytes(data[i:i + 2], "little"))
          for i in range(0, len(data), 2)]


def first_bad(got: list[float] | list[int], exp: list[float] | list[int],
              atol: float) -> int | None:
  for i, (g, e) in enumerate(zip(got, exp, strict=True)):
    if isinstance(g, float) or isinstance(e, float):
      if math.isnan(float(e)):
        if not math.isnan(float(g)):
          return i
      elif abs(float(g) - float(e)) > atol:
        return i
    elif g != e:
      return i
  return None


UNARY_COMPUTE_TEMPLATE = r"""
#include <cstdint>
#include "api/compute/common.h"
#include "api/compute/tile_move_copy.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"
#include "api/compute/eltwise_unary/binop_with_scalar.h"
{includes}

void kernel_main() {{
  uint32_t n = get_arg_val<uint32_t>(0);
  constexpr auto cb_in = tt::CBIndex::c_0;
  constexpr auto cb_out = tt::CBIndex::c_16;
  unary_op_init_common(cb_in, cb_out);
  copy_tile_init(cb_in);
  {init}
  for (uint32_t i = 0; i < n; ++i) {{
    tile_regs_acquire();
    cb_wait_front(cb_in, 1);
    copy_tile(cb_in, 0, 0);
    cb_pop_front(cb_in, 1);
    {body}
    tile_regs_commit();
    tile_regs_wait();
    cb_reserve_back(cb_out, 1);
    pack_tile(0, cb_out);
    cb_push_back(cb_out, 1);
    tile_regs_release();
  }}
}}
"""


BINARY_READER = r"""
#include <cstdint>
void kernel_main() {
  uint32_t a_addr = get_arg_val<uint32_t>(0);
  uint32_t b_addr = get_arg_val<uint32_t>(1);
  uint32_t off = get_arg_val<uint32_t>(2);
  uint32_t n = get_arg_val<uint32_t>(3);
  constexpr uint32_t cb0 = tt::CBIndex::c_0;
  constexpr uint32_t cb1 = tt::CBIndex::c_1;
  const InterleavedAddrGenFast<true> a = {
    .bank_base_address = a_addr, .page_size = get_tile_size(cb0), .data_format = DataFormat::Float16_b,
  };
  const InterleavedAddrGenFast<true> b = {
    .bank_base_address = b_addr, .page_size = get_tile_size(cb1), .data_format = DataFormat::Float16_b,
  };
  for (uint32_t i = 0; i < n; ++i) {
    cb_reserve_back(cb0, 1);
    cb_reserve_back(cb1, 1);
    noc_async_read_tile(off + i, a, get_write_ptr(cb0));
    noc_async_read_tile(off + i, b, get_write_ptr(cb1));
    noc_async_read_barrier();
    cb_push_back(cb0, 1);
    cb_push_back(cb1, 1);
  }
}
"""


BINARY_COMPUTE_TEMPLATE = r"""
#include <cstdint>
#include "api/compute/common.h"
#include "api/compute/eltwise_binary.h"

void kernel_main() {{
  uint32_t n = get_arg_val<uint32_t>(0);
  constexpr auto cb0 = tt::CBIndex::c_0;
  constexpr auto cb1 = tt::CBIndex::c_1;
  constexpr auto cb_out = tt::CBIndex::c_16;
  binary_op_init_common(cb0, cb1, cb_out);
  {init}
  for (uint32_t i = 0; i < n; ++i) {{
    tile_regs_acquire();
    cb_wait_front(cb0, 1);
    cb_wait_front(cb1, 1);
    {body}
    cb_pop_front(cb0, 1);
    cb_pop_front(cb1, 1);
    tile_regs_commit();
    tile_regs_wait();
    cb_reserve_back(cb_out, 1);
    pack_tile(0, cb_out);
    cb_push_back(cb_out, 1);
    tile_regs_release();
  }}
}}
"""


UNARY_COMPUTE_CB_TEMPLATE = r"""
#include <cstdint>
#include "api/compute/common.h"
#include "api/compute/tile_move_copy.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"

void kernel_main() {{
  uint32_t n = get_arg_val<uint32_t>(0);
  constexpr auto cb_in = tt::CBIndex::c_{cb_in};
  constexpr auto cb_out = tt::CBIndex::c_{cb_out};
  unary_op_init_common(cb_in, cb_out);
  copy_tile_init(cb_in);
  for (uint32_t i = 0; i < n; ++i) {{
    tile_regs_acquire();
    cb_wait_front(cb_in, 1);
    copy_tile(cb_in, 0, 0);
    cb_pop_front(cb_in, 1);
    tile_regs_commit();
    tile_regs_wait();
    cb_reserve_back(cb_out, 1);
    pack_tile(0, cb_out);
    cb_push_back(cb_out, 1);
    tile_regs_release();
  }}
}}
"""


DTYPE_READER_CB_TEMPLATE = r"""
#include <cstdint>
void kernel_main() {{
  uint32_t addr = get_arg_val<uint32_t>(0);
  uint32_t off  = get_arg_val<uint32_t>(1);
  uint32_t n    = get_arg_val<uint32_t>(2);
  constexpr uint32_t cb = tt::CBIndex::c_{cb};
  const InterleavedAddrGenFast<true> s = {{
    .bank_base_address = addr, .page_size = get_tile_size(cb), .data_format = DataFormat::{fmt},
  }};
  for (uint32_t i = 0; i < n; ++i) {{
    cb_reserve_back(cb, 1);
    noc_async_read_tile(off + i, s, get_write_ptr(cb));
    noc_async_read_barrier();
    cb_push_back(cb, 1);
  }}
}}
"""


DTYPE_WRITER_CB_TEMPLATE = r"""
#include <cstdint>
void kernel_main() {{
  uint32_t addr = get_arg_val<uint32_t>(0);
  uint32_t off  = get_arg_val<uint32_t>(1);
  uint32_t n    = get_arg_val<uint32_t>(2);
  constexpr uint32_t cb = tt::CBIndex::c_{cb};
  const InterleavedAddrGenFast<true> s = {{
    .bank_base_address = addr, .page_size = get_tile_size(cb), .data_format = DataFormat::{fmt},
  }};
  for (uint32_t i = 0; i < n; ++i) {{
    cb_wait_front(cb, 1);
    noc_async_write_tile(off + i, s, get_read_ptr(cb));
    noc_async_write_barrier();
    cb_pop_front(cb, 1);
  }}
}}
"""


DTYPE_READER_TEMPLATE = r"""
#include <cstdint>
void kernel_main() {{
  uint32_t addr = get_arg_val<uint32_t>(0);
  uint32_t off  = get_arg_val<uint32_t>(1);
  uint32_t n    = get_arg_val<uint32_t>(2);
  constexpr uint32_t cb = tt::CBIndex::c_0;
  const InterleavedAddrGenFast<true> s = {{
    .bank_base_address = addr, .page_size = get_tile_size(cb), .data_format = DataFormat::{fmt},
  }};
  for (uint32_t i = 0; i < n; ++i) {{
    cb_reserve_back(cb, 1);
    noc_async_read_tile(off + i, s, get_write_ptr(cb));
    noc_async_read_barrier();
    cb_push_back(cb, 1);
  }}
}}
"""


DTYPE_WRITER_TEMPLATE = r"""
#include <cstdint>
void kernel_main() {{
  uint32_t addr = get_arg_val<uint32_t>(0);
  uint32_t off  = get_arg_val<uint32_t>(1);
  uint32_t n    = get_arg_val<uint32_t>(2);
  constexpr uint32_t cb = tt::CBIndex::c_16;
  const InterleavedAddrGenFast<true> s = {{
    .bank_base_address = addr, .page_size = get_tile_size(cb), .data_format = DataFormat::{fmt},
  }};
  for (uint32_t i = 0; i < n; ++i) {{
    cb_wait_front(cb, 1);
    noc_async_write_tile(off + i, s, get_read_ptr(cb));
    noc_async_write_barrier();
    cb_pop_front(cb, 1);
  }}
}}
"""


@dataclass(frozen=True)
class Case:
  name: str
  dtype: Dtype
  src0: bytes
  expected: list[float] | list[int]
  compute_src: str
  src1: bytes | None = None
  reader_src: str | None = None
  writer_src: str | None = None
  decode: Callable[[bytes], list[float] | list[int]] = tile_values_bf16
  atol: float = 0.03125
  cb0: int = 0
  cb1: int = 1
  cb_out: int = 16
  cb_pages: int = 2

  @property
  def num_tiles(self) -> int:
    return len(self.src0) // self.dtype.tile_size

  def raw_kernel(self) -> RawKernelCase:
    return RawKernelCase(
      name=self.name,
      dtype=self.dtype,
      src0=self.src0,
      compute_src=self.compute_src,
      src1=self.src1,
      reader_src=self.reader_src,
      writer_src=self.writer_src,
      cb0=self.cb0,
      cb1=self.cb1,
      cb_out=self.cb_out,
      cb_pages=self.cb_pages,
    )


@dataclass(frozen=True)
class FirmwareBootResult:
  boot_cycles: int
  dispatch_cycles: int
  tile_state: tuple[tuple[tuple[int, int], int, int], ...]


def build_cases() -> list[Case]:
  vals = [((i % 31) - 15) / 8.0 for i in range(TILE_ELEMS)]
  a = [((i % 17) - 8) / 4.0 for i in range(TILE_ELEMS)]
  b = [((i % 19) - 3) / 5.0 for i in range(TILE_ELEMS)]
  def unary(name: str, body: str, expected_fn: Callable[[float], float],
            init: str = "binop_with_scalar_tile_init();",
            includes: str = "") -> Case:
    return Case(
      name=name,
      dtype=Dtype.Float16_b,
      src0=tilize(pack_bf16(vals), 2, TILE_SHAPE),
      expected=[expected_fn(v) for v in vals],
      compute_src=UNARY_COMPUTE_TEMPLATE.format(
        includes=includes, init=init, body=body),
    )

  def fpu_binary(name: str, init: str, body: str,
                 expected_fn: Callable[[float, float], float],
                 atol: float = 0.0625) -> Case:
    return Case(
      name=name,
      dtype=Dtype.Float16_b,
      src0=tilize(pack_bf16(a), 2, TILE_SHAPE),
      src1=tilize(pack_bf16(b), 2, TILE_SHAPE),
      expected=[expected_fn(x, y) for x, y in zip(a, b, strict=True)],
      compute_src=BINARY_COMPUTE_TEMPLATE.format(init=init, body=body),
      reader_src=BINARY_READER,
      writer_src=DTYPE_WRITER_TEMPLATE.format(fmt="Float16_b"),
      atol=atol,
    )

  fp16_vals = [((i % 23) - 9) / 4.0 for i in range(TILE_ELEMS)]

  return [
    unary("sfpu_add_scalar", "add_unary_tile(0, 0x40000000);",
          lambda x: x + 2.0),
    unary("sfpu_add_negative", "add_unary_tile(0, 0xbf000000);",
          lambda x: x - 0.5),
    unary("sfpu_mul_scalar", "mul_unary_tile(0, 0x40400000);",
          lambda x: x * 3.0),
    unary("sfpu_mul_half", "mul_unary_tile(0, 0x3f000000);",
          lambda x: x * 0.5),
    unary("sfpu_mul_negative", "mul_unary_tile(0, 0xbf800000);",
          lambda x: -x),
    unary("sfpu_affine", "add_unary_tile(0, 0x40000000); mul_unary_tile(0, 0x40400000);",
          lambda x: (x + 2.0) * 3.0),
    unary("sfpu_scale_bias", "mul_unary_tile(0, 0x3fc00000); add_unary_tile(0, 0x3f800000);",
          lambda x: x * 1.5 + 1.0),
    unary("sfpu_add_zero", "add_unary_tile(0, 0x00000000);",
          lambda x: x),
    fpu_binary("fpu_cb0_cb1_add", "add_tiles_init(cb0, cb1);",
               "add_tiles(cb0, cb1, 0, 0, 0);", lambda x, y: x + y),
    fpu_binary("fpu_cb0_cb1_sub", "sub_tiles_init(cb0, cb1);",
               "sub_tiles(cb0, cb1, 0, 0, 0);", lambda x, y: x - y),
    fpu_binary("fpu_cb0_cb1_mul", "mul_tiles_init(cb0, cb1);",
               "mul_tiles(cb0, cb1, 0, 0, 0);", lambda x, y: x * y),
    Case(
      name="packer_unpacker_bf16_copy",
      dtype=Dtype.Float16_b,
      src0=tilize(pack_bf16(vals), 2, TILE_SHAPE),
      expected=vals,
      compute_src=UNARY_COMPUTE_TEMPLATE.format(
        includes="", init="", body=""),
      decode=tile_values_bf16,
      atol=0.03125,
    ),
    Case(
      name="packer_unpacker_fp16_copy",
      dtype=Dtype.Float16,
      src0=tilize(pack_fp16(fp16_vals), 2, TILE_SHAPE),
      expected=fp16_vals,
      compute_src=UNARY_COMPUTE_TEMPLATE.format(
        includes="", init="", body=""),
      reader_src=DTYPE_READER_TEMPLATE.format(fmt="Float16"),
      writer_src=DTYPE_WRITER_TEMPLATE.format(fmt="Float16"),
      decode=tile_values_fp16,
      atol=0.03125,
    ),
  ]


def build_multi_tile_cases(num_tiles: int) -> list[Case]:
  shape = (num_tiles, TILE_HEIGHT, TILE_WIDTH)
  elems = num_tiles * TILE_ELEMS
  vals = [((i % 37) - 18) / 7.0 for i in range(elems)]
  a = [((i % 29) - 14) / 5.0 for i in range(elems)]
  b = [((i % 23) - 11) / 6.0 for i in range(elems)]
  return [
    Case(
      name=f"multi_tile_unary_add_n{num_tiles}",
      dtype=Dtype.Float16_b,
      src0=tilize(pack_bf16(vals), 2, shape),
      expected=[x + 2.0 for x in vals],
      compute_src=UNARY_COMPUTE_TEMPLATE.format(
        includes="",
        init="binop_with_scalar_tile_init();",
        body="add_unary_tile(0, 0x40000000);",
      ),
    ),
    Case(
      name=f"multi_tile_binary_add_n{num_tiles}",
      dtype=Dtype.Float16_b,
      src0=tilize(pack_bf16(a), 2, shape),
      src1=tilize(pack_bf16(b), 2, shape),
      expected=[x + y for x, y in zip(a, b, strict=True)],
      compute_src=BINARY_COMPUTE_TEMPLATE.format(
        init="add_tiles_init(cb0, cb1);",
        body="add_tiles(cb0, cb1, 0, 0, 0);",
      ),
      reader_src=BINARY_READER,
      writer_src=DTYPE_WRITER_TEMPLATE.format(fmt="Float16_b"),
      atol=0.0625,
    ),
  ]


def build_unary_copy_case(
    name: str,
    num_tiles: int,
    *,
    cb0: int = 0,
    cb_out: int = 16,
    cb_pages: int = 2,
) -> Case:
  shape = (num_tiles, TILE_HEIGHT, TILE_WIDTH)
  elems = num_tiles * TILE_ELEMS
  vals = [((i % 41) - 20) / 9.0 for i in range(elems)]
  return Case(
    name=name,
    dtype=Dtype.Float16_b,
    src0=tilize(pack_bf16(vals), 2, shape),
    expected=vals,
    compute_src=UNARY_COMPUTE_CB_TEMPLATE.format(
      cb_in=cb0,
      cb_out=cb_out,
    ),
    reader_src=DTYPE_READER_CB_TEMPLATE.format(fmt="Float16_b", cb=cb0),
    writer_src=DTYPE_WRITER_CB_TEMPLATE.format(fmt="Float16_b", cb=cb_out),
    cb0=cb0,
    cb_out=cb_out,
    cb_pages=cb_pages,
  )


def run_and_check(case: Case):
  result = run_raw_kernel_case(case.raw_kernel())
  shape = (case.num_tiles, TILE_HEIGHT, TILE_WIDTH)
  got = case.decode(untilize(result.output, case.dtype.bpe, shape))
  bad = first_bad(got, case.expected, case.atol)
  if bad is not None:
    raise AssertionError(
      f"{case.name}: mismatch at element {bad}: got {got[bad]!r}, "
      f"expected {case.expected[bad]!r}, atol={case.atol}")


def boot_firmware_and_dispatch_return_kernel() -> FirmwareBootResult:
  dev = Device(
    harvested_banks=HARVESTED_DRAM_BANKS,
    core_count=1,
    firmware_boot_max_cycles=200000,
  )
  ret = dsl.pack([dsl.RET()])
  dispatch_cycles = dev.dispatch(
    brisc=ret,
    ncrisc=ret,
    trisc=(ret, ret, ret),
    max_cycles=200000,
  )
  return FirmwareBootResult(
    boot_cycles=dev.firmware_boot_cycles,
    dispatch_cycles=dispatch_cycles,
    tile_state=tuple(
      (
        (tile.x, tile.y),
        tile.l1.read8(dev.go_messages_addr + 3),
        tile.l1.read32(LAUNCH_MSG_RD_PTR),
      )
      for tile in dev.tiles.values()
    ),
  )


def _program_atomic(tile, *, target_xy: tuple[int, int], target_addr: int,
                    ret_addr: int, length: int, data: int,
                    l1_acc_instrn: int = 0):
  buf = 3
  base = NOC0_BASE + buf * NIU_CMD_BUF_STRIDE
  ctrl = NOC_CTRL_AT | NOC_CTRL_RESP_MARKED
  if l1_acc_instrn:
    ctrl |= NOC_CTRL_L1_ACC_AT_EN
  tile.noc0.write32(base + NIU_TARG_ADDR_LO, target_addr)
  tile.noc0.write32(base + NIU_TARG_ADDR_HI, noc_key(*target_xy))
  tile.noc0.write32(base + NIU_RET_ADDR_LO, ret_addr)
  tile.noc0.write32(base + NIU_RET_ADDR_HI, noc_key(tile.x, tile.y))
  tile.noc0.write32(base + NIU_AT_LEN_BE, length)
  tile.noc0.write32(base + NIU_AT_DATA, data)
  tile.noc0.write32(base + NIU_L1_ACC_AT_INSTRN, l1_acc_instrn)
  tile.noc0.write32(base + NIU_CTRL, ctrl)
  tile.noc0.write32(base + NIU_CMD_CTRL, 1)


def _run_until_atomic_response(dev: Device, tile, expected: int = 1):
  def done() -> bool:
    return tile.noc0.read32(NOC0_BASE + NIU_MST_ATOMIC_RESP_RECEIVED) >= expected
  dev.run_until(done, 1000, tiles=[])


@pytest.mark.parametrize("case", build_cases(), ids=lambda c: c.name)
def test_single_tile_kernel_case(case: Case):
  run_and_check(case)


@pytest.mark.parametrize("num_tiles", [3, 5])
@pytest.mark.parametrize(
  "case_index",
  [0, 1],
  ids=["unary_add", "binary_add"],
)
def test_multi_tile_single_core_pipeline(num_tiles: int, case_index: int):
  run_and_check(build_multi_tile_cases(num_tiles)[case_index])


@pytest.mark.parametrize("cb_pages", [4, 8])
def test_unary_copy_larger_cb_page_count(cb_pages: int):
  run_and_check(build_unary_copy_case(
    f"unary_copy_cb_pages_{cb_pages}",
    num_tiles=5,
    cb_pages=cb_pages,
  ))


@pytest.mark.parametrize(
  ("cb0", "cb_out"),
  [(3, 19), (7, 31)],
  ids=["cb3_to_cb19", "cb7_to_cb31"],
)
def test_unary_copy_weird_cb_indices(cb0: int, cb_out: int):
  run_and_check(build_unary_copy_case(
    f"unary_copy_cb{cb0}_to_cb{cb_out}",
    num_tiles=5,
    cb0=cb0,
    cb_out=cb_out,
  ))


@pytest.mark.parametrize("cores", [1, 4], ids=lambda cores: f"cores_{cores}")
def test_add1_raw_kernel_smoke(cores: int):
  result = run_add1_raw_kernel(core_count=cores)
  assert result.output == result.expected
  assert result.steps > 0


def test_firmware_boot_dispatch_return_kernel():
  result = boot_firmware_and_dispatch_return_kernel()
  assert result.boot_cycles > 0
  assert result.dispatch_cycles > 0
  assert result.tile_state
  assert all(go == RUN_MSG_DONE for _, go, _ in result.tile_state)


def test_matmul_peak_default_grid_smoke():
  assert run_matmul_peak() == 0


@pytest.mark.parametrize(
  ("opcode", "initial", "length", "data", "expected"),
  [
    (0x1, 41, 0x1 << 12, 1, 42),
    (0x2, 3, (0x2 << 12) | (2 << 6) | (5 << 2), 0, 0),
    (0x4, 0xCAFE1234, 0x4 << 12, 0xBEEF1234, 0xCAFEBEEF),
    (0x6, 0x3000, 0x6 << 12, 0xA5A55A5A, 0x3000),
    (0x7, 0x11223344, 0x7 << 12, 0x55667788, 0x55667788),
  ],
  ids=["incr_get", "incr_get_ptr_wrap", "cas_low16", "store_ind", "swap_4b"],
)
def test_noc_atomic_opcodes(opcode: int, initial: int, length: int,
                            data: int, expected: int):
  dev = Device(harvested_banks=HARVESTED_DRAM_BANKS, core_count=1, boot_firmware=False)
  tile = next(iter(dev.tiles.values()))
  target_addr = 0x2000
  ret_addr = 0x2100
  tile.l1.write32(target_addr, initial)
  if opcode == 0x6:
    tile.l1.write32(initial, 0)

  _program_atomic(
    tile,
    target_xy=(tile.x, tile.y),
    target_addr=target_addr,
    ret_addr=ret_addr,
    length=length,
    data=data,
  )
  _run_until_atomic_response(dev, tile)

  if opcode == 0x6:
    assert tile.l1.read32(initial) == data
    assert tile.l1.read32(target_addr) == initial
  else:
    assert tile.l1.read32(target_addr) == expected
  assert tile.l1.read32(ret_addr) == initial


def test_noc_l1_acc_atomic_instruction_selects_opcode():
  dev = Device(harvested_banks=HARVESTED_DRAM_BANKS, core_count=1, boot_firmware=False)
  tile = next(iter(dev.tiles.values()))
  target_addr = 0x2200
  ret_addr = 0x2300
  tile.l1.write32(target_addr, 9)

  _program_atomic(
    tile,
    target_xy=(tile.x, tile.y),
    target_addr=target_addr,
    ret_addr=ret_addr,
    length=0,
    data=5,
    l1_acc_instrn=0x1 << 12,
  )
  _run_until_atomic_response(dev, tile)

  assert tile.l1.read32(target_addr) == 14
  assert tile.l1.read32(ret_addr) == 9


def test_export_raw_kernel_case_sources_and_cb_config(tmp_path):
  path = export_raw_kernel_cases(
    [build_cases()[0].raw_kernel(), build_unary_copy_case(
      "export_weird_cb", num_tiles=2, cb0=3, cb_out=19).raw_kernel()],
    tmp_path / "raw_kernel_cases.json",
  )
  data = path.read_text()
  assert "sfpu_add_scalar" in data
  assert "export_weird_cb" in data
  assert '"cb": 3' in data
  assert '"trisc0"' in data
