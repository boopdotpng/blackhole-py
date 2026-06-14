#!/usr/bin/env python3
"""Reproducer for the Blackhole packer L1-accumulation fp16 path.

This is the new-style version of the old tt-metal C++ repro: it reuses the
hand-written Python matmul kernels from matmul_peak, then switches the operand,
output, and partial-CB24 formats to exercise the bad fp16 L1-acc path and the
known controls.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np

from device import Device
from program import Dtype
import matmul_peak as mp


DEFAULT_M = 256
DEFAULT_N = 192
DEFAULT_K = 896


@dataclass(frozen=True)
class Case:
  name: str
  input_dtype: Dtype
  output_dtype: Dtype
  intermediate_dtype: Dtype
  packer_l1_acc: bool
  fp32_dest_acc: bool = False


CASES = {
  "bad": Case("Float16 + fp16 partials + L1 acc", Dtype.Float16, Dtype.Float16, Dtype.Float16, True),
  "bf16": Case("Float16_b + L1 acc", Dtype.Float16_b, Dtype.Float16_b, Dtype.Float16_b, True),
  "reload": Case("Float16 + reload, no packer L1 acc", Dtype.Float16, Dtype.Float16, Dtype.Float16, False),
  "f32acc": Case(
    "Float16 + fp32 dest acc + fp32 partials",
    Dtype.Float16, Dtype.Float16, Dtype.Float32, True, True,
  ),
}


def configure_old_geometry() -> None:
  mp.SUPPORTED_IN0_BLOCK_WS = (4,)
  mp.SUPPORTED_OUT_SUBBLOCK_H = 8
  mp.SUPPORTED_OUT_SUBBLOCK_W = 1
  mp.K_GROUP = 1
  mp.STREAM_PARTIAL_CB24 = False
  mp.SKIP_PADDED_N = False


def summarize_output(raw: bytes, dtype: Dtype, shape: tuple[int, int]) -> tuple[np.ndarray, list[str]]:
  values = mp.from_device_bytes(raw, dtype, shape).reshape(-1)
  bad_positions = np.where(~np.isfinite(values))[0]
  lines: list[str] = []
  if bad_positions.size:
    raw_u16 = np.frombuffer(raw, dtype=np.uint16)
    for pos in bad_positions[:8]:
      row = int(pos // shape[1])
      col = int(pos % shape[1])
      lines.append(f"    ({row:4d}, {col:4d}) raw=0x{int(raw_u16[pos]):04x}")
    if bad_positions.size > len(lines):
      lines.append(f"    ... and {bad_positions.size - len(lines)} more")
  return values, lines


def parse_case_list(text: str) -> list[str]:
  names = [name.strip() for name in text.split(",") if name.strip()]
  unknown = [name for name in names if name not in CASES]
  if unknown:
    raise argparse.ArgumentTypeError(f"unknown case(s): {', '.join(unknown)}")
  return names


def main() -> None:
  parser = argparse.ArgumentParser(description="Reproduce/debug the fp16 packer L1 accumulation issue.")
  parser.add_argument("--M", type=int, default=DEFAULT_M)
  parser.add_argument("--N", type=int, default=DEFAULT_N)
  parser.add_argument("--K", type=int, default=DEFAULT_K)
  parser.add_argument("--core-count", type=int, default=1)
  parser.add_argument("--runs", type=int, default=1)
  parser.add_argument("--cases", type=parse_case_list, default=list(CASES),
                      help=f"comma-separated subset of: {','.join(CASES)}")
  parser.add_argument("--validate", action="store_true", help="also run sampled PCC/rel-L2 validation for finite outputs")
  args = parser.parse_args()

  configure_old_geometry()
  device = Device()
  try:
    cores = sorted(device.cores, key=lambda xy: (xy[1], xy[0]))[:args.core_count]
    if not cores:
      raise SystemExit("no dispatchable cores available")

    print("l1_acc_bug:")
    print(f"  shape: {args.M}x{args.K}x{args.N}")
    print(f"  cores: {len(cores)}")
    print("  requested plan: in0_block_w=4, out_subblock=8x1")
    print()

    for case_name in args.cases:
      case = CASES[case_name]
      mp.configure_numeric_path(
        input_dtype=case.input_dtype,
        output_dtype=case.output_dtype,
        intermediate_dtype=case.intermediate_dtype,
        packer_l1_acc=case.packer_l1_acc,
        fp32_dest_acc=case.fp32_dest_acc,
      )
      result = mp.run_matmul(
        args.M, args.N, args.K,
        device=device,
        cores=cores,
        runs=args.runs,
        validate_result=False,
      )
      plan = result["chunks"][0].plan
      values, bad_lines = summarize_output(
        result["c_raw"],
        case.output_dtype,
        (result["Mp"], result["Np"]),
      )
      nonfinite = int(values.size - np.count_nonzero(np.isfinite(values)))
      avg = result["avg_us"]
      timing = f", {avg:,.1f} us avg" if avg is not None else ""
      print(f"{case.name}:{timing}")
      print(f"  plan: per_core={plan.per_core_m}x{plan.per_core_n} tiles, "
            f"K-blocks={plan.num_blocks}, block_w={plan.in0_block_w}, "
            f"out_subblock={plan.out_subblock_h}x{plan.out_subblock_w}")
      print(f"  non-finite outputs: {nonfinite} / {values.size}")
      if bad_lines:
        print("  first bad values:")
        print("\n".join(bad_lines))
      elif args.validate:
        pcc, rel_l2 = mp.validate(
          result["a_ref"], result["b_ref"], result["c_raw"],
          args.M, args.N, result["Mp"], result["Np"], case.output_dtype,
        )
        print(f"  validation: PCC={pcc:.6f}, rel_l2={rel_l2:.6f}")
      print()

    print("Historic signal: the Float16 + L1-acc case showed non-finite fp16 outputs; "
          "the bf16 and reload cases are controls.")
  finally:
    device.close()


if __name__ == "__main__":
  main()
