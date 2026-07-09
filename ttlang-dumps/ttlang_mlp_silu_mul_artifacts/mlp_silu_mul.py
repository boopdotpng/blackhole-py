#!/usr/bin/env python3
"""TT-Lang dump workload for the Llama MLP elementwise epilogue.

This models the post-projection operation:

    hidden = gate.silu() * up

The shape is a 1x4 tile slice of the Llama MLP hidden dimension.  Keeping the
block compact makes the generated compute kernel easy to mine while preserving
the fused SiLU plus multiply expression that TT-Lang naturally lowers.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("TTLANG_COMPILE_ONLY", "1")
os.environ.setdefault("TTLANG_DUMP_ARTIFACTS_DIR", str(Path(__file__).resolve().parent))

import torch  # noqa: E402
import ttl  # noqa: E402
import ttnn  # noqa: E402


TILE = 32
BLOCK_N_TILES = 4


@ttl.operation(grid=(1, 1))
def mlp_silu_mul_kernel(gate, up, hidden):
  gate_dfb = ttl.make_dataflow_buffer_like(gate, shape=(1, BLOCK_N_TILES), block_count=2)
  up_dfb = ttl.make_dataflow_buffer_like(up, shape=(1, BLOCK_N_TILES), block_count=2)
  hidden_dfb = ttl.make_dataflow_buffer_like(hidden, shape=(1, BLOCK_N_TILES), block_count=2)

  @ttl.compute()
  def compute():
    with gate_dfb.wait() as gate_blk, up_dfb.wait() as up_blk:
      with hidden_dfb.reserve() as hidden_blk:
        hidden_blk.store(ttl.silu(gate_blk) * up_blk)

  @ttl.datamovement()
  def dm_read():
    with gate_dfb.reserve() as gate_blk:
      ttl.copy(gate[0:1, 0:BLOCK_N_TILES], gate_blk).wait()
    with up_dfb.reserve() as up_blk:
      ttl.copy(up[0:1, 0:BLOCK_N_TILES], up_blk).wait()

  @ttl.datamovement()
  def dm_write():
    with hidden_dfb.wait() as hidden_blk:
      ttl.copy(hidden_blk, hidden[0:1, 0:BLOCK_N_TILES]).wait()


def main() -> None:
  shape = (TILE, BLOCK_N_TILES * TILE)
  to_host_ttnn = lambda tensor: ttnn.from_torch(
    tensor,
    dtype=ttnn.bfloat16,
    layout=ttnn.TILE_LAYOUT,
  )
  gate = to_host_ttnn(torch.zeros(shape, dtype=torch.bfloat16))
  up = to_host_ttnn(torch.zeros(shape, dtype=torch.bfloat16))
  hidden = to_host_ttnn(torch.zeros(shape, dtype=torch.bfloat16))

  mlp_silu_mul_kernel(gate, up, hidden)
  print("compiled mlp_silu_mul_kernel")


if __name__ == "__main__":
  main()
