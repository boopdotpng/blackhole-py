"""Llama 3 batch-1 decode on one Blackhole card: 3.2 1B BF16, 3 8B BF16, 3 8B FP8.

Read in this order:
  config.py    the numbers that differ between 1B, 8B BF16, and 8B FP8 (one table)
  kernels.py   the device kernels, in the order one token flows through them:
                 embedding -> [RMSNorm + Q/K/V projection -> RoPE + KV cache +
                 attention -> O projection + residual -> RMSNorm + gate/up +
                 SwiGLU -> down projection + residual] x layers ->
                 RMSNorm + LM head -> argmax
  runtime.py   DRAM layout, weight upload, and the launch list for one token
  generate.py  tokenizer + greedy generation loop + CLI

All three models run the same kernels. 1B vs 8B is only dimensions; FP8-only
steps are marked ``# FP8`` and can be skipped when reading the BF16 path.
"""

from examples.llama3.config import Llama3Config
from examples.llama3.runtime import Llama3Decode, PagedProjectionWeight
from examples.llama3.generate import generate, main
from examples.llama3 import kernels
