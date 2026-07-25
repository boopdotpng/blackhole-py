"""Bit-exact hardware check for fused versus separate decode Q/K/V."""

import numpy as np

from device import Device
from examples.llama3 import (
  EMBED_DIM, KV_PROJ_DIM, LLAMA_CORES, Q_PROJ_DIM,
  decode_projection, decode_qkv_projection,
)
from ttk import DType


def random_bf16(buffer, rng):
  values = rng.standard_normal(buffer.shape, dtype=np.float32) * 0.02
  return buffer.from_numpy(values)


def first_difference(expected, actual):
  left = np.frombuffer(expected, dtype="<u2")
  right = np.frombuffer(actual, dtype="<u2")
  different = np.flatnonzero(left != right)
  if not len(different):
    return None
  index = int(different[0])
  return index, int(left[index]), int(right[index])


def main():
  device = Device()
  device.init_device()
  try:
    cores = device.dram.cores[:LLAMA_CORES]
    x = device.dram.buffer(
      "qkv_check_x", DType.BF16, (1, EMBED_DIM),
      axis=0, global_address=True,
    )
    q_weight = device.dram.buffer(
      "qkv_check_q_weight", DType.BF16, (Q_PROJ_DIM, EMBED_DIM),
      axis=0, cores=cores,
    )
    k_weight = device.dram.buffer(
      "qkv_check_k_weight", DType.BF16, (KV_PROJ_DIM, EMBED_DIM),
      axis=0, cores=cores,
    )
    v_weight = device.dram.buffer(
      "qkv_check_v_weight", DType.BF16, (KV_PROJ_DIM, EMBED_DIM),
      axis=0, cores=cores,
    )
    q_output = device.dram.buffer(
      "qkv_check_q_output", DType.BF16,
      (LLAMA_CORES, q_weight.items_per_core),
      axis=0, cores=cores,
    )
    k_output = device.dram.buffer(
      "qkv_check_k_output", DType.BF16,
      (LLAMA_CORES, k_weight.items_per_core),
      axis=0, cores=cores,
    )
    v_output = device.dram.buffer(
      "qkv_check_v_output", DType.BF16,
      (LLAMA_CORES, v_weight.items_per_core),
      axis=0, cores=cores,
    )

    rng = np.random.default_rng(20260725)
    for buffer in (x, q_weight, k_weight, v_weight):
      device.write(buffer, random_bf16(buffer, rng))
    device.run(timeout=60.0)

    q = decode_projection(x, q_weight, q_output)
    k = decode_projection(x, k_weight, k_output)
    v = decode_projection(x, v_weight, v_output)
    qkv = decode_qkv_projection(
      x, q_weight, k_weight, v_weight,
      q_output, k_output, v_output,
    )
    device.cache_kernels((q, k, v, qkv))

    separate_stamps = device.run(q, k, v, timeout=60.0)
    reference = tuple(
      device.read(output, timeout=30.0)
      for output in (q_output, k_output, v_output)
    )

    fused_stamp, = device.run(qkv, timeout=60.0)
    fused = tuple(
      device.read(output, timeout=30.0)
      for output in (q_output, k_output, v_output)
    )

    failed = False
    for name, expected, actual in zip(("Q", "K", "V"), reference, fused):
      difference = first_difference(expected, actual)
      if difference is None:
        print(f"{name}: PASS ({len(actual)} bytes)")
      else:
        index, left, right = difference
        print(
          f"{name}: FAIL element {index}: "
          f"separate=0x{left:04x}, fused=0x{right:04x}",
        )
        failed = True
    if failed:
      raise SystemExit(1)
    separate_us = sum(stamp.us for stamp in separate_stamps)
    print(f"separate Q + K + V kernels: {separate_us:.2f} us")
    print(f"fused QKV kernel: {fused_stamp.us:.2f} us")
  finally:
    device.close()


if __name__ == "__main__":
  main()
