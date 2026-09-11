from ttk.model import (Dtype, Buffer, trace, kernel, loop, dst, l1, noc, unpack, pack, sfpu)

N = 2048
BLOCKS = N // 128
EPS = 1e-5

def rmsnorm_embedding(emb: Buffer, gamma: Buffer,
                      residual: Buffer, normalized: Buffer) -> None:
  token = kernel.param("token_id", dtype=Dtype.u32)
  embedding_l1 = noc.read(emb, offset=token * (N * 2), nbytes=N * 2, resident=True)
  gamma_l1 = noc.read(gamma, resident=True)
  noc.write(embedding_l1, residual)

  # One Dst allocation split into two named ranges of 128-element blocks.
  dst_registers = dst.alloc(2 * BLOCKS, dtype=Dtype.f32)
  embedding_dst = dst_registers.blocks(offset=0, count=BLOCKS)
  gamma_dst = dst_registers.blocks(offset=BLOCKS, count=BLOCKS)
  unpack(embedding_l1, into=embedding_dst)
  unpack(gamma_l1, into=gamma_dst)
  embedding_l1.free()
  gamma_l1.free()

  def reduce_block(block, acc):
    for lanes in sfpu.lanes(embedding_dst[block]):
      value = sfpu.load(lanes)
      acc = sfpu.mad(value, value, acc)
    return acc

  acc = loop(BLOCKS, reduce_block, carry=sfpu.const(0.0), name='block')
  scale = sfpu.rsqrt(sfpu.lane_sum(acc) * (1.0 / N) + EPS)

  def normalize_block(block):
    for x_lanes, g_lanes in zip(sfpu.lanes(embedding_dst[block]), sfpu.lanes(gamma_dst[block])):
      value = sfpu.load(x_lanes)
      weight = sfpu.load(g_lanes)
      sfpu.store(value * weight * scale, x_lanes)

  loop(BLOCKS, normalize_block, name='block')

  output = l1.alloc(N * 2, dtype=Dtype.bf16)
  pack(embedding_dst, into=output)
  dst_registers.free()
  noc.write(output, normalized)
  output.free()


if __name__ == '__main__':
  buffers = (Buffer('embedding', Dtype.bf16, 128256 * N * 2),
             Buffer('gamma', Dtype.bf16, N * 2), Buffer('residual', Dtype.bf16, N * 2),
             Buffer('normalized', Dtype.bf16, N * 2))
  print(trace(rmsnorm_embedding, *buffers).dump())
