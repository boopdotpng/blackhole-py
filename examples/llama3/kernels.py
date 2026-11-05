"""Llama 3 decode kernels, in the order one token flows through them.

  1. embedding           x = embedding_table[token]
  2. projection          used five times per token (see runtime._create_programs):
                           qkv   q, k, v = rmsnorm(x) @ Wq, Wk, Wv
                           o     x2 = x + context @ Wo
                           gate  hidden = silu(rmsnorm(x2) @ Wgate) * (rmsnorm(x2) @ Wup)
                           down  x = x2 + hidden @ Wdown
                           lm    logits = rmsnorm(x) @ Wlm
  3. attention           RoPE(q, k), append k/v to the cache, softmax(q k^T / sqrt(d)) v
  4. attention_merge     8B split attention only: combine four partial attentions
  5. argmax              next token = argmax(logits)
  Appendix               small SFPU programs and address helpers shared by the above

Hardware model, enough to read the kernels:

  A program runs on a set of Tensix worker cores. Every core runs five RISC-V
  processors, each with its own instruction stream (``p.brisc``, ``p.trisc0``...):

    BRISC   reads DRAM into L1 over the NoC (the reader)
    TRISC0  "unpack": moves L1 tiles into the FPU source registers SrcA/SrcB
    TRISC1  "math": FPU (matrix/elementwise ops) and SFPU (32-lane vector unit)
            computing into the Dst register file
    TRISC2  "pack": moves Dst tiles back to L1
    NCRISC  writes L1 to DRAM over the NoC (the writer)

  They hand data to each other through circular buffers (CBs) in L1: the
  producer does reserve_back/push_back, the consumer wait_front/pop_front.
  Everything moves in 1024-element tiles (32x32, stored as four 16x16 faces).

  Kernels are Python functions that *generate* these instruction streams; a
  Python ``for`` unrolls at build time, ``k.range(n)`` emits a device loop.
  ``specialize`` builds one program variant per distinct per-core shape (row
  count, head index, ...) and launches them together.

  Constants (``Const``) and buffers are launch parameters: the runtime can
  rebind them per launch (layer weights, token position) without rebuilding.

FP8-only code (8B FP8 mode) is marked ``# FP8``; the BF16 path skips it.
"""

import math
import struct

from asm import Cond
from cq import UnicastWrite, mcast_coords, noc_coord
from firmware.consts import CQConfig, TensixL1, TensixMMIO
from pcie import P100_WORKER_CORES
from program import Buffer, Const, DType, TensorProgram as Program, rectangles
from ttko import Dst, l1
from ttko.argmax import load_bf16, scan_bf16, physical_to_logical
from ttko.cb import CB
from ttko.fpu import Fpu
from ttko.isa import R, Tensix as TT
from ttko.mop import LoopTemplate
from ttko.pack import Pack
from ttko.sfpu import LaneConfig, LReg, SfpuFormat, SfpuProgram, SfpuProgramBuilder
from ttko.shard import specialize
from ttko.sync import Sem, SemWait, Stall, Wait, sem_get, sem_wait, stall
from ttko.unpack import UnpackTarget

FP8_ACTIVATION = DType.FP8       # FP8: activations are quantized to E4M3 before FP8 matmuls


# ---------------------------------------------------------------------------
# 1. Embedding: x = embedding_table[token]
# ---------------------------------------------------------------------------

def embedding(cfg, token_id: Buffer, embedding_weight: Buffer, output: Buffer) -> Program:
  """Gather one embedding row on one core.

    token_id          flat U32[8192]                 global; `token_pos` selects the ID
    embedding_weight  BF16[128256, embed_dim]        global, embed_tiles tiles per vocabulary row
    output            BF16[1, embed_dim]             global, embed_tiles tiles

  Logical operation:
    output[0, :] = embedding_weight[token_id[token_pos], :]
  """
  token_pos = Const("token_pos", 0)
  p = Program(
    output.cores, token_id, embedding_weight, output, token_pos,
  )
  ids_l1 = p.l1(token_id.tile_size, alignment=16)
  embedding_cb = p.cb(DType.BF16, depth=cfg.embed_tiles)
  # BRISC: look up the token ID, then read its embedding row into embedding_cb.
  with p.brisc.scope():
    position, tile, within, token = p.brisc.reg(4)
    p.brisc.read(position, p.param_addr(token_pos))
    p.brisc.srli(tile, position, 10)          # 1024 flat token IDs per DRAM page
    p.brisc.andi(within, position, 1023)
    p.brisc.noc.read_tile(token_id, tile, ids_l1)
    p.brisc.slli(within, within, 2)
    _add_constant(p.brisc, within, ids_l1)
    p.brisc.read(token, within)
    for row_tile in range(cfg.embed_tiles):
      with p.brisc.scope():
        # weight tile index = token * embed_tiles + row_tile
        source_tile = p.brisc.reg(exclude=token)
        p.brisc.slli(source_tile, token, cfg.embed_tiles_shift)
        if row_tile: p.brisc.addi(source_tile, source_tile, row_tile)
        p.brisc.noc.read_into_cb(
          embedding_weight, source_tile, embedding_cb,
        )
  # NCRISC: write the row to x.
  p.ncrisc.noc.write_tiles_from_cb(
    embedding_cb, output, tuple(range(cfg.embed_tiles)),
  )
  return p


# ---------------------------------------------------------------------------
# 2. Projection: y = W @ x, optionally with RMSNorm before and an epilogue after
# ---------------------------------------------------------------------------
#
# Every projection core owns a contiguous range of W's rows (output features)
# and computes one dot product per row (8B O projection: 4096 rows on 88
# cores -> 46 or 47 rows each).
#
# Output layouts:
#   compact  each core writes its rows as one tile in its own DRAM shard
#            (qkv and lm). Attention and argmax read these shards directly.
#   dense    the plain [features] vector; cores scatter their rows into it
#            (o/down after the residual add, gate/up after SwiGLU).

def projection(cfg, x, projections, *, norm_weight=None, swiglu_output=None,
               residual=None, dense_output=None, rotate_ports=True):
  """Build y_i = W_i @ x for 1-3 weights that share one input (Q/K/V, gate/up).

    x               dense input vector [input_dim]
    projections     ((weight, compact_output), ...), weight = [rows, input_dim]
    norm_weight     RMSNorm gamma: x is normalized first (qkv, gate, lm)
    swiglu_output   dense silu(y_0) * y_1 (gate/up)
    residual        with dense_output: dense_output = residual + y_0 (o, down)
    rotate_ports    read weights over all three DRAM ports per bank
  """
  if dense_output is not None and residual is None:
    raise ValueError("a dense projection output requires a residual input")
  weights = tuple(weight for weight, _ in projections)
  # Each core differs in: how many rows it owns, which NoC/DRAM port it reads
  # from, and (8 DRAM banks) at which bank its first weight row starts.
  keys = tuple(
    (tuple(weight.item_counts[index] for weight in weights),
     _projection_route(cfg, index, core, weights, rotate_ports),
     tuple(((weight.item_starts[index] * (weight.tiles_per_item // getattr(weight, "page_tiles", 1)))
            if weight.global_address else weight.tile_starts[index]) % weight.banks
           if weight.banks == 8 else None for weight in weights))
    for index, core in enumerate(weights[0].cores)
  )
  return specialize(
    lambda key: _projection_program(
      cfg, x, tuple((weight, output, count) for (weight, output), count in zip(projections, key[0])),
      key[1], key[2], norm_weight=norm_weight, swiglu_output=swiglu_output,
      residual=residual, dense_output=dense_output,
    ),
    weights[0].cores, keys,
  )


def _projection_route(cfg, index, core, weights, rotate_ports=True):
  """(read NoC, DRAM port phase) for one projection core; writes use the other NoC.

  The writer uses the other NoC so its transaction IDs cannot collide with
  the reader's. Never mix the two policies inside one program: spatially
  split NoCs with rotated ports hung both p150a cards. Programs run one
  after another, so mixing policies across programs is fine.
  """
  if rotate_ports and all(
      len(endpoints) >= 3 for weight in weights for endpoints in weight.dram_endpoints):
    return 0, index % 3
  return int(core[0] >= cfg.noc_split_x), None


def _projection_program(cfg, x, projections, route, rotations, *, norm_weight,
                        swiglu_output, residual, dense_output):
  """One core's projection program. ``projections`` is ((weight, output, rows), ...)."""
  read_noc, port = route
  write_noc = 1 - read_noc
  weight_dtype = projections[0][0].dtype
  fp8 = weight_dtype.is_fp8
  first_rows = projections[0][2]
  if any(weight.tilized != x.tilized for weight, _, _ in projections):
    raise ValueError("projection weights and activation must have the same element order")
  if norm_weight is not None and norm_weight.tilized != x.tilized:
    raise ValueError("projection norm and activation must have the same element order")
  input_dim = x.shape[1]
  input_tiles = input_dim // 1024

  # Launch parameters. Weights are global buffers; row_start tells each core
  # where its rows begin. The O projection reads x through this flat view.
  row_starts = tuple(
    Const(f"{weight.name}_row_start", weight.item_starts)
    if weight.global_address and len(weight.cores) > 1 else None
    for weight, _, _ in projections
  )
  token = Buffer(
    f"{x.name}_decode_token", x.addr, x.dtype, (input_dim,), None,
    (x.cores[0],), x.banks, global_address=True,
    tilized=x.tilized, dram_endpoints=x.dram_endpoints,
  )
  scatter_output = swiglu_output if swiglu_output is not None else dense_output
  p = Program(
    projections[0][0].cores, token,
    *(parameter for (weight, output, _), row_start in zip(projections, row_starts)
      for parameter in ((weight, output) if row_start is None else (weight, output, row_start))),
    # FP8: per-layer scales arrive as SFPU load-immediate instruction words.
    *(_scale_constants("input_scale", 1.) if fp8 else ()),
    *(param for i in range(len(projections)) for param in (_scale_constants(f"output_scale_{i}", 1/256) if fp8 else ())),
    *((scatter_output, Const("dense_start", projections[0][0].item_starts)) if scatter_output is not None else ()),
    *((residual,) if residual is not None else ()),
    *((norm_weight,) if norm_weight is not None else ()),
    fp32_dst=True,
  )

  # L1 working memory.
  weight_cb = p.cb(weight_dtype, depth=(16 if fp8 else 2) * input_tiles)   # BRISC -> TRISC0: weight rows
  scalar_dtype = projections[0][1].dtype
  scalar_cb = p.cb(scalar_dtype, depth=2)                                  # TRISC2 -> NCRISC: one dot product
  operand_dtype = FP8_ACTIVATION if fp8 else DType.BF16                    # format of x as the FPU sees it
  convert_input = operand_dtype.is_fp8 and not token.dtype.is_fp8          # FP8: quantize x without RMSNorm
  # x after RMSNorm / FP8 quantization. Without either, x is copied raw to token_l1.
  normalized_cb = p.cb(operand_dtype, depth=input_tiles) if norm_weight is not None or convert_input else None
  token_l1 = normalized_cb.addr if normalized_cb is not None else p.l1(input_tiles * token.tile_size, alignment=16)
  # This core's rows of each output, gathered into one tile ("compact").
  compact_cbs = tuple(p.cb(output.dtype, depth=output.tiles_per_item) for _, output, _ in projections)

  # Step 1 (all cores): bring x into token_l1, normalized and/or quantized.
  # BRISC's DRAM reads are collected here and issued together below.
  input_reads, input_publications = [], []
  if norm_weight is None and convert_input:
    # FP8: x * input_scale, rounded to E4M3 (O and down projections).
    incoming = p.cb(token.dtype, depth=input_tiles)
    CB.reserve_back(p.brisc, incoming, input_tiles)
    input_reads.extend((token, tile, incoming.addr + tile * token.tile_size) for tile in range(input_tiles))
    input_publications.append((incoming, input_tiles))
    for _ in p.trisc0.range(input_tiles): p.unpack.move(incoming, UnpackTarget.SRCA)
    for _ in p.trisc1.range(input_tiles):
      p.fpu.copy_a_tiles(dst_tiles=(0,))
      _scale_input(p, (0,))
      p.sfpu.map(_round_fp8_program(), tile=0).publish()
    for _ in p.trisc2.range(input_tiles): p.pack.move(normalized_cb, tile=0)
  elif norm_weight is None:
    # Raw x straight into token_l1 (BF16 O and down projections).
    input_reads.extend((token, tile, token_l1 + tile * token.tile_size) for tile in range(input_tiles))
  else:
    # RMSNorm: x and gamma -> Dst, normalized on the SFPU, packed to normalized_cb.
    if input_dim != cfg.embed_dim: raise ValueError(f"fused RMSNorm requires a {cfg.embed_dim}-element token")
    operands = p.cb(DType.BF16, depth=2 * cfg.embed_tiles)   # x tiles, then gamma tiles
    CB.reserve_back(p.brisc, operands, 2 * cfg.embed_tiles)
    for index, buffer in enumerate((token, norm_weight)):
      input_reads.extend((buffer, tile, operands.addr + (index * cfg.embed_tiles + tile) * operands.tile_size)
                         for tile in range(cfg.embed_tiles))
    input_publications.append((operands, 2 * cfg.embed_tiles))
    for tile in range(2 * cfg.embed_tiles): p.unpack.move(operands, UnpackTarget.SRCA, configure_format=tile == 0)
    _rms_setup_apply_macro(p.sfpu)
    p.fpu.copy_a_tiles(dst_tiles=range(2 * cfg.embed_tiles))
    _rmsnorm(cfg, p.sfpu, fp8=operand_dtype.is_fp8,
             scale=(lambda: _scale_input(p, range(cfg.embed_tiles))) if operand_dtype.is_fp8 else None)
    p.pack.move_tiles(normalized_cb, tiles=tuple(range(cfg.embed_tiles)))
  if residual is not None:
    residual_l1 = p.l1(residual.tiles * residual.tile_size, alignment=16)
    input_reads.extend((residual, tile, residual_l1 + tile * residual.tile_size) for tile in range(residual.tiles))
  # BRISC: x, gamma, and residual reads are independent. Publish the input
  # CBs after a single completion barrier, then stream weights immediately.
  if input_reads:
    with p.brisc.noc_at(read_noc, port).transaction() as transaction:
      for buffer, tile, target in input_reads:
        with p.brisc.scope():
          address, coordinate = p.brisc.noc_at(read_noc, port)._dram_tile(buffer, tile)
          transaction.read(address, coordinate, target, buffer.tile_size)
  for cb, count in input_publications: CB.push_back(p.brisc, cb, count)

  # Step 3 (BRISC): stream this core's weight rows into weight_cb.
  _projection_read_weights(p, projections, row_starts, rotations, route, weight_cb, input_tiles)

  # Step 4 (TRISC0): for every row, unpack (weight tile -> SrcA, x tile -> SrcB).
  # The unpacker needs the converted x; the DRAM reader can run ahead.
  if normalized_cb is not None: CB.wait_front(p.trisc0, normalized_cb, input_tiles)
  p.unpack.prepare_l1_pair_formats(weight_cb.dtype, operand_dtype)
  for _, _, local_rows in projections:
    for _ in p.trisc0.range(local_rows):
      for input_tile in range(input_tiles):
        p.unpack.move_l1_pair(
          weight_cb, token_l1 + input_tile * (1024 * operand_dtype.itemsize),
          configure_format=False, source_b_dtype=operand_dtype,
        )

  # Step 5 (TRISC1): elementwise multiply on the FPU, sum on the SFPU -> one scalar per row.
  _projection_dot_math(cfg, p, projections, input_tiles)

  # Step 6 (TRISC2): pack each row's scalar into scalar_cb.
  p.pack._configure(scalar_cb, True, True)
  for _, _, local_rows in projections:
    for _ in p.trisc2.range(local_rows):
      sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
      p.pack._move_acquired(scalar_cb, 0, True, configure=False)
      p.pack._release_dst()

  # Step 7 (NCRISC): place each scalar at its row's slot in the compact tile.
  # Without an epilogue, write the compact tile to this core's DRAM shard.
  for compact_cb, (_, output, local_rows) in zip(compact_cbs, projections):
    compact_l1 = compact_cb.addr
    _zero_l1_words(p.ncrisc, compact_l1, output.tiles_per_item * output.tile_size // 4)
    for local_row in p.ncrisc.range(local_rows):
      CB.wait_front(p.ncrisc, scalar_cb)
      with p.ncrisc.scope():
        source, value, byte_offset, target = p.ncrisc.reg(4, exclude=local_row)
        CB.get_read_ptr(p.ncrisc, scalar_cb, source)
        p.ncrisc.read(value, source, bytes=scalar_dtype.itemsize)
        _tile_offset(p.ncrisc, local_row, byte_offset, scalar_dtype)
        p.ncrisc.li(target, compact_l1)
        p.ncrisc.add(target, target, byte_offset)
        p.ncrisc.write(target, value, bytes=scalar_dtype.itemsize)
      CB.pop_front(p.ncrisc, scalar_cb)
    if scatter_output is not None:
      CB.push_back(p.ncrisc, compact_cb)       # handed to the epilogue below
      continue
    for tile in range(output.tiles_per_item):
      with p.ncrisc.scope():
        target_address, target_coordinate = p.ncrisc.noc_at(write_noc, port)._dram_tile(output, tile)
        p.ncrisc.noc_at(write_noc, port).write(
          compact_l1 + tile * output.tile_size, target_address, target_coordinate,
          output.tile_size, posted=False,
        )

  # Step 8, epilogue A (gate/up): hidden = silu(gate) * up, scattered dense.
  if swiglu_output is not None:
    output_cb = p.cb(swiglu_output.dtype, depth=1)
    for cb in compact_cbs: p.unpack.move(cb, UnpackTarget.SRCA)
    _swiglu_math(cfg, p, fp8=swiglu_output.dtype.is_fp8)
    p.pack.move(output_cb, tile=0)
    _scatter_dense(p, output_cb, swiglu_output, first_rows, read_noc=write_noc, port=port)

  # Step 8, epilogue B (o/down): x_out = residual + y, scattered dense.
  elif residual is not None:
    residual_cb = p.cb(DType.BF16, depth=1)
    output_cb = p.cb(DType.BF16, depth=1)
    # NCRISC gathers this core's residual features into the compact layout.
    # The reader finishes residual DMA before delivering any projection row;
    # consuming all scalar rows above makes that L1 data safe to read here.
    with p.ncrisc.scope():
      start = p.ncrisc.reg()
      p.ncrisc.read(start, p.param_addr(p.param("dense_start")))
      for index in p.ncrisc.range(first_rows):
        with p.ncrisc.scope():
          feature, src, dst, value = p.ncrisc.reg(4, exclude=(start, index))
          p.ncrisc.add(feature, start, index)
          _dense_offset(p.ncrisc, residual, feature, src)
          _add_constant(p.ncrisc, src, residual_l1)
          p.ncrisc.read(value, src, bytes=2)
          _tile_offset(p.ncrisc, index, dst)
          _add_constant(p.ncrisc, dst, residual_cb.addr)
          p.ncrisc.write(dst, value, bytes=2)
    CB.push_back(p.ncrisc, residual_cb)
    p.unpack.move_pair(compact_cbs[0], residual_cb)
    # Match the original residual kernel's BF16 destination arithmetic.
    Fpu(p.trisc1, Dst(False)).binary("add", dst_tile=0).publish()
    Pack(p.trisc2, Dst(False)).move(output_cb, tile=0)
    _scatter_dense(p, output_cb, dense_output, first_rows, read_noc=write_noc, port=port)
  return p


def _projection_read_weights(p, projections, row_starts, rotations, route, weight_cb, input_tiles):
  """BRISC: push this core's weight rows, one full row (input_tiles tiles) at a time.

  Weights are stored row-major and interleaved page by page across the DRAM
  banks. ``rotation`` is the bank holding this core's first page (8 banks),
  or None for the generic tile-at-a-time reader (7 banks).
  """
  read_noc, port = route
  for (weight, _, local_rows), row_start, rotation in zip(
    projections, row_starts, rotations,
  ):
    page_tiles = getattr(weight, "page_tiles", 1)
    row_pages = input_tiles // page_tiles
    if rotation is None:
      for local_row in p.brisc.range(local_rows):
        source_row = local_row
        if row_start is not None:
          source_row = p.brisc.reg(exclude=local_row)
          p.brisc.read(source_row, p.param_addr(row_start))
          p.brisc.add(source_row, source_row, local_row)
        with p.brisc.scope():
          first, scale = p.brisc.reg(2, exclude=source_row)
          p.brisc.li(scale, input_tiles)
          p.brisc.mul(first, source_row, scale)
          # One tile at a time bounds register use for the 14-tile MLP input.
          for index in range(input_tiles):
            with p.brisc.scope():
              tile = p.brisc.reg(exclude=first)
              p.brisc.addi(tile, first, index)
              p.brisc.noc_at(read_noc, port).read_tiles_into_cb(weight, (tile,), weight_cb)
    else:
      # Consecutive rows repeat their bank pattern after this many rows.
      # Unroll one period so every request's bank is a compile-time constant;
      # only its address within that bank advances at runtime.
      noc = p.brisc.noc_at(read_noc, port)
      period = weight.banks // math.gcd(row_pages, weight.banks)
      with p.brisc.scope():
        base = p.brisc.reg()
        p.brisc.read(base, p.param_addr(weight))
        p.brisc.andi(base, base, -8)
        if row_start is not None:
          with p.brisc.scope():
            start, divisor = p.brisc.reg(2, exclude=base)
            p.brisc.read(start, p.param_addr(row_start))
            p.brisc.li(divisor, row_pages)
            p.brisc.mul(start, start, divisor)
            p.brisc.li(divisor, weight.banks)
            p.brisc.divu(start, start, divisor)
            p.brisc.slli(start, start, weight.tile_size.bit_length() - 1)
            p.brisc.add(base, base, start)

        def read_row(row, group):
          CB.reserve_back(p.brisc, weight_cb, input_tiles)
          with noc.transaction() as transaction:
            for index in range(row_pages):
              offset = rotation + row * row_pages + index
              with p.brisc.scope():
                address, target, delta = p.brisc.reg(
                  3, exclude=(base, group) if isinstance(group, R) else base,
                )
                if isinstance(group, R):
                  p.brisc.li(
                    delta, period * row_pages // weight.banks * weight.tile_size,
                  )
                  p.brisc.mul(address, group, delta)
                  p.brisc.add(address, address, base)
                else:
                  p.brisc.mv(address, base)
                p.brisc.li(delta, (offset // weight.banks) * weight.tile_size)
                p.brisc.add(address, address, delta)
                CB.get_write_ptr(p.brisc, weight_cb, target)
                if index:
                  p.brisc.li(delta, index * weight.tile_size)
                  p.brisc.add(target, target, delta)
                coordinate = noc.coordinate(
                  *noc.dram_endpoint(weight.dram_endpoints, offset % weight.banks),
                )
                transaction.read(address, coordinate, target, weight.tile_size)
          CB.push_back(p.brisc, weight_cb, input_tiles)

        for group in p.brisc.range(local_rows // period):
          for row in range(period): read_row(row, group)
        for row in range(local_rows // period * period, local_rows):
          read_row(row, None)


def _projection_dot_math(cfg, p, projections, input_tiles):
  """TRISC1: for each row, multiply weight and x tiles, then sum all products.

  The FPU multiplies a (weight, x) tile pair elementwise into Dst tile 0. The
  SFPU then adds those 1024 FP32 products into 32 running lane sums (L7).
  After the last input tile, _dot_finalize reduces the 32 lanes to one value.
  The FPU and SFPU share Dst tile 0 throughout. The multiply MOP stays
  resident; the SFPU is driven by direct replay so the two engines do not
  rewrite their shared MOP configuration for every tile.
  """
  fpu, sfpu = p.fpu, p.sfpu
  fpu._configure_dst(0)
  sfpu._configure_dst(0, LaneConfig())
  fpu._set_addr_mod(0, srca=8, srcb=8, dest=8)
  fpu._set_addr_mod(1)
  fpu._set_addr_mod(2, srca_clear=True, srcb_clear=True,
                    dest_carry=True, fidelity_increment=1)
  fpu._set_addr_mod(3, srca_clear=True, srcb_clear=True, dest=8,
                    dest_carry_to_carry=True, fidelity_clear=True)
  # One MOP run multiplies one 16x16 face (BF16: 2 fidelity phases).
  fpu._mop.configure(LoopTemplate(
    outer=1 if projections[0][0].dtype is DType.FP8 else 2, inner=2, loop=TT.TTELWMUL(0, 0, 0, 0, 0),
    last=TT.TTELWMUL(3, 0, 0, 3, 0),
    outer_last=TT.TTELWMUL(0, 0, 0, 2, 0),
  ))
  accumulate = _dot_accumulate(reset=False)
  replay_start, replay_body = sfpu._prepare(accumulate)
  assert replay_start is not None
  finalize = _dot_finalize()
  for projection_index, (_, _, local_rows) in enumerate(projections):
    for local_row in p.trisc1.range(local_rows):
      fpu._wait_for_dst()
      for word in _sfpu_float_words(LReg.L7, 0.0): sfpu._issue(word)       # lane sums = 0
      for input_tile in range(input_tiles):
        # FPU: Dst[0] = weight_tile * x_tile, one face at a time.
        for face in range(4):
          fpu._issue(TT.TTZEROACC(1, 1, 0, 1, face))
        fpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
        stall(p.trisc1, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
        for _ in range(4): fpu._mop.run()
        fpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
        # SFPU: lane sums += Dst[0], 8 rows of 32 lanes per face.
        stall(p.trisc1, Stall.SFPU, Wait.MATH)
        for _ in range(4):
          for _ in range(8):
            sfpu._issue(TT.TTREPLAY(replay_start, len(replay_body), 0, 0))
          sfpu._issue(TT.TTSETRWC(0, 4, 8, 0, 0, 4))
          sfpu._issue(TT.TTSETRWC(0, 4, 8, 0, 0, 4))
        sfpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
        stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
      # Reduce the 32 lane sums to one value (stored last, after FP8 scaling).
      for word in finalize.words[:-2]: sfpu._issue(word)
      if projections[0][0].dtype.is_fp8:
        # FP8: undo the per-tensor weight/input quantization, y *= scale.
        _load_scale(p, f"output_scale_{projection_index}")
        words = []
        _sfpu_mul(words, LReg.L0, LReg.L6, LReg.L0)
        for word in words: sfpu._issue(word)
      for word in finalize.words[-2:]: sfpu._issue(word)
      sfpu.publish()


def _dot_accumulate(*, reset):
  """Accumulate one FP32 product tile into the persistent SFPU L7 lanes."""
  setup = _sfpu_float_words(LReg.L7, 0.0) if reset else ()
  return SfpuProgram(tuple(setup), (
    TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0),
    TT.TTSFPMAD(LReg.L0, LReg.ONE, LReg.L7, LReg.L7, 0),
  ))


def _dot_finalize():
  """Reduce the 32 SFPU accumulator lanes and store one scalar in Dst 0.

  The SFPU works on 4 rows x 8 lanes. A rotate-and-add butterfly sums each
  8-lane row; a transpose then lines the 4 row sums up so they can be added.
  The last two words (store + nop) are issued separately by the caller.
  """
  words = [TT.TTSFPMOV(0, LReg.L7, LReg.L0, 0)]
  for rotations in (4, 2, 1):
    words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
    for _ in range(rotations):
      words.extend((
        TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
      ))
    _sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
  for register in (LReg.L1, LReg.L2, LReg.L3):
    words.append(TT.TTSFPMOV(0, LReg.L0, register, 0))
  words.append(TT.TTSFPTRANSP(0, 0, 0, 0))
  for register in (LReg.L1, LReg.L2, LReg.L3):
    _sfpu_add(words, LReg.L0, register, LReg.L0)
  words.extend((
    TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0),
    TT.TTSFPNOP(),
  ))
  return SfpuProgram((), tuple(words))


# RMSNorm: x * gamma / sqrt(mean(x^2) + 1e-5), computed in FP32 on the SFPU.
# x occupies Dst tiles [0, embed_tiles), gamma the next embed_tiles tiles.

def _rmsnorm(cfg, sfpu, *, fp8=False, scale=None):
  """Normalize the token tiles and apply gamma, all in FP32."""
  sem_wait(
    sfpu.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
    Stall.SYNC | Stall.MATH | Stall.SFPU,
  )
  # sum(x^2) into the 32 lanes of L0, one tile at a time.
  for tile in range(cfg.embed_tiles):
    _select_dst_tile(sfpu, tile)
    _rms_map_acquired(sfpu, _rms_square_accumulate(reset=tile == 0))
  # L0 = 1 / sqrt(sum / embed_dim + eps), broadcast to every lane.
  for word in _rms_finalize_scale(cfg).words: sfpu._issue(word)
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)

  # x = x * L0 * gamma.
  apply = _rms_apply_weight_pair(cfg)
  for tile in range(cfg.embed_tiles):
    _select_dst_tile(sfpu, tile)
    _rms_map_acquired(sfpu, apply, iterations=4)
  if scale is not None: scale()                                             # FP8: x *= input_scale
  if fp8:
    for tile in range(cfg.embed_tiles): sfpu.map(_round_fp8_program(), tile=tile)   # FP8: round to E4M3
  sfpu.publish()


def _rms_square_accumulate(*, reset):
  """L0 += x * x for every value of the selected tile (32 lanes accumulate in parallel)."""
  # BF16 immediate zero expands to FP32 +0 in every enabled lane.
  setup = (TT.TTSFPLOADI(LReg.L0, 0, 0),) if reset else ()
  return SfpuProgram(tuple(setup), (
    TT.TTSFPLOAD(LReg.L1, SfpuFormat.FP32, 7, 0),
    TT.TTSFPMAD(LReg.L1, LReg.L1, LReg.L0, LReg.L0, 0),
  ))


def _rms_finalize_scale(cfg):
  """Reduce the 32 accumulator lanes in L0 and leave reciprocal RMS there."""
  words = []
  # Butterfly-reduce each independent eight-lane SFPU row. Cyclic rotations
  # make the final sum a broadcast, which the transpose below needs.
  for rotations in (4, 2, 1):
    words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
    for _ in range(rotations):
      words.extend((
        TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
      ))
    _sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
  # Copy the four eight-lane row sums, then transpose the four identical
  # registers. L0..L3 become broadcasts of rows 0..3 respectively.
  for register in (LReg.L1, LReg.L2, LReg.L3):
    words.append(TT.TTSFPMOV(0, LReg.L0, register, 0))
  words.append(TT.TTSFPTRANSP(0, 0, 0, 0))
  for register in (LReg.L1, LReg.L2, LReg.L3):
    _sfpu_add(words, LReg.L0, register, LReg.L0)

  words.extend(_sfpu_float_words(LReg.L4, 1.0 / cfg.embed_dim))
  words.append(TT.TTSFPMUL(LReg.L0, LReg.L4, LReg.ZERO, LReg.L0, 0))
  words.extend(_sfpu_float_words(LReg.L4, 1e-5))
  _sfpu_add(words, LReg.L0, LReg.L4, LReg.L0)

  # Accurate Blackhole reciprocal square root for finite positive FP32 L0.
  x, y, temporary, c1, c2, half = (
    LReg.L6, LReg.L1, LReg.L2, LReg.L3, LReg.L4, LReg.L5,
  )
  words.extend((
    TT.TTSFPMOV(0, LReg.L0, x, 0),
    TT.TTSFPMOV(0, x, y, 0),
    TT.TTSFPSHFT(0xfff, LReg.ZERO, y, 1),
  ))
  magic = 0x5f1110a0
  words.extend((
    TT.TTSFPLOADI(temporary, 10, magic & 0xffff),
    TT.TTSFPLOADI(temporary, 8, magic >> 16),
    TT.TTSFPIADD(0, temporary, y, 6),
  ))
  _sfpu_mul(words, x, y, temporary)
  words.append(TT.TTSFPMUL(y, temporary, LReg.ZERO, temporary, 1))
  words.extend(_sfpu_float_words(c1, 2.2825186))
  words.extend(_sfpu_float_words(c2, 2.2533049))
  _sfpu_add(words, c2, temporary, c2)
  words.extend((TT.TTSFPMAD(temporary, c2, c1, temporary, 0), TT.TTSFPNOP()))
  _sfpu_mul(words, y, temporary, y)
  _sfpu_mul(words, x, y, temporary)
  _sfpu_mul(words, y, temporary, temporary, 1)
  words.append(TT.TTSFPADD(
    LReg.ONE, LReg.ONE, temporary, temporary, 0,
  ))
  words.extend(_sfpu_float_words(half, 0.5))
  _sfpu_mul(words, y, half, half)
  words.append(TT.TTSFPMAD(temporary, half, y, LReg.L0, 0))
  return SfpuProgram((), tuple(words))


def _rms_apply_weight_pair(cfg):
  """Apply RMS scale and gamma to two independent 32-lane footprints."""
  return SfpuProgram((), (
    TT.TTSFPLOADMACRO(LReg.L1, SfpuFormat.DEFAULT, 7, 0),
    TT.TTSFPLOAD(LReg.L2, SfpuFormat.FP32, 7, cfg.embed_tiles * 64),
    TT.TTSFPLOADMACRO(LReg.L3, SfpuFormat.DEFAULT, 7, 2),
    TT.TTSFPLOAD(LReg.L4, SfpuFormat.FP32, 7, cfg.embed_tiles * 64 + 2),
    TT.TTSFPMUL(LReg.L1, LReg.L2, LReg.ZERO, LReg.L1, 0),
    TT.TTSFPMUL(LReg.L3, LReg.L4, LReg.ZERO, LReg.L3, 0),
    TT.TTSFPSTORE(LReg.L1, SfpuFormat.FP32, 7, 0),
    TT.TTSFPSTORE(LReg.L3, SfpuFormat.FP32, 7, 2),
    TT.TTINCRWC(0, 2, 0, 0),
  ))


def _rms_setup_apply_macro(sfpu):
  """Configure macro 0 to multiply each loaded value by the live L0 scale."""
  sfpu._issue(TT.TTSFPCONFIG(LaneConfig().word(), LReg.LANE_X2, 1))
  sfpu._issue(TT.TTSFPNOP())
  # Backdoor destination CONFIG0 installs this multiply as template slot 0.
  sfpu._issue(TT.TTSFPMUL(
    LReg.L0, LReg.L0, LReg.ZERO, LReg.CONFIG0, 0,
  ))
  # Macro sequence 0, MAD byte: selector 4, delay 0, replace VB with the
  # just-loaded LReg. Other sub-units are disabled.
  sfpu._issue(TT.TTSFPCONFIG(0x8400, 4, 1))
  sfpu._issue(TT.TTSFPCONFIG(0x0f00, 8, 1))


def _rms_map_acquired(sfpu, program, *, iterations=8):
  """Run an SFPU program over all four faces of the selected Dst tile."""
  start, body = sfpu._prepare(program)
  for word in program.setup_words: sfpu._issue(word)
  if start is not None:
    sfpu._configure_replay_mop(start, len(body), iterations)
  sfpu._run_faces(start, body, 4, iterations)
  sfpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def _select_dst_tile(sfpu, tile):
  """Point the SFPU at Dst tile ``tile`` once the FPU has finished writing it."""
  sfpu._configure_dst(tile, LaneConfig())
  stall(sfpu.k, Stall.SFPU, Wait.MATH)


def _swiglu_math(cfg, p, *, fp8=False):
  """Dst[0] = silu(gate) * up = gate / (1 + exp(-gate)) * up, from compact gate/up tiles."""
  p.fpu.copy_a_tiles(dst_tiles=(0, 1))

  exponent = p.sfpu.program()
  value = exponent.load(format=SfpuFormat.FP32, offset=0)
  exponent.store(value, format=SfpuFormat.FP32, offset=128)
  exponent.neg(value, into=value)
  exponent.exp(value, into=value)
  exponent.store(value, format=SfpuFormat.FP32, offset=0)
  p.sfpu.map(exponent.finish(), tile=0)

  combine = p.sfpu.program()
  denominator = combine.load(format=SfpuFormat.FP32, offset=0)
  combine.add_scalar(denominator, 1.0, into=denominator)
  combine.reciprocal(denominator, into=denominator)
  original = combine.load(format=SfpuFormat.FP32, offset=128)
  up_value = combine.load(format=SfpuFormat.FP32, offset=64)
  combine.mul(original, denominator, into=original)
  combine.mul(original, up_value, into=original)
  combine.store(original, format=SfpuFormat.FP32, offset=0)
  p.sfpu.map(combine.finish(), tile=0)
  if fp8: p.sfpu.map(_round_fp8_program(), tile=0)
  p.sfpu.publish()


def _scatter_dense(p, cb, output, count, *, read_noc=0, port=None):
  """NCRISC: write this core's ``count`` compact values into the dense output vector.

  The values sit in tilized order in ``cb``. They are first rearranged in L1
  at the same byte offsets they have in DRAM, then written as runs of at most
  16 values (one face row), so every NoC write is contiguous and aligned.
  ``read_noc`` is the NoC used for these writes.
  """
  k = p.ncrisc
  size = output.dtype.itemsize
  shift = size.bit_length() - 1
  noc = k.noc_at(read_noc, port)
  dense = p.l1(output.tiles * output.tile_size, alignment=16)
  CB.wait_front(k, cb)
  with k.scope():
    start, source = k.reg(2)
    k.read(start, p.param_addr(p.param("dense_start")))
    CB.get_read_ptr(k, cb, source)
    for index in k.range(count):
      with k.scope():
        feature, src, dst, value = k.reg(4, exclude=(start, source, index))
        k.add(feature, start, index)
        _tile_offset(k, index, src, output.dtype)
        k.add(src, source, src)
        k.read(value, src, bytes=size)
        _dense_offset(k, output, feature, dst)
        _add_constant(k, dst, dense)
        k.write(dst, value, bytes=size)
    with noc.transaction() as transaction:
      with k.scope():
        feature, end = k.reg(2, exclude=start)
        k.mv(feature, start)
        k.addi(end, start, count)
        loop = k._new_label("dense_scatter")
        k.label(loop)
        with k.scope():
          tile, offset, length, limit, src, dst = k.reg(6, exclude=(feature, end))
          k.srli(tile, feature, 10)
          address, coordinate = noc._dram_tile(output, tile)
          _dense_offset(k, output, feature, offset)
          k.li(src, dense)
          k.add(src, src, offset)
          if output.tile_size <= 2048:
            k.andi(offset, offset, output.tile_size - 1)
          else:
            k.slli(offset, offset, 20)
            k.srli(offset, offset, 20)
          k.add(dst, address, offset)
          k.andi(length, feature, 15)
          k.li(limit, 16)
          k.sub(length, limit, length)
          k.sub(limit, end, feature)
          enough = k._new_label("dense_chunk")
          k.bgeu(limit, length, enough)
          k.mv(length, limit)
          k.label(enough)
          k.add(feature, feature, length)
          k.slli(length, length, shift)
          transaction.write(src, dst, coordinate, length, posted=False)
        k.bltu(feature, end, loop)
  CB.pop_front(k, cb)


# FP8 scales. Scales are passed as two SFPLOADI instruction words that load
# the FP32 value into SFPU register L6: no CPU float work per token.

def _scale_constants(name, value):
  return tuple(Const(f"{name}_{part}", word) for part, word in enumerate(_sfpu_float_words(LReg.L6, value)))


def _load_scale(p, name):
  # Parameter words are complete SFPLOADI instructions: no CPU float work per token.
  stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
  with p.trisc1.scope():
    word = p.trisc1.reg()
    for part in range(2):
      p.trisc1.read(word, p.param_addr(p.param(f"{name}_{part}")))
      p.trisc1.write(TensixMMIO.INSTRN_BUF_BASE, word)


def _scale_input(p, tiles):
  _load_scale(p, "input_scale")
  words = [TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0)]
  _sfpu_mul(words, LReg.L0, LReg.L6, LReg.L0)
  words.append(TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0))
  for tile in tiles: p.sfpu.map(SfpuProgram((), tuple(words)), tile=tile)


# ---------------------------------------------------------------------------
# 3. Attention: RoPE, KV-cache append, and streaming grouped-query attention
# ---------------------------------------------------------------------------
#
# 32 query heads share 8 KV heads (groups of 4). Each attention core handles
# 32 / attention_cores query heads of one KV head: 2 heads on 16 cores (1B),
# 1 head on 32 cores (8B). Per core:
#
#   a. RoPE: gather its q/k/v rows from the projection cores' compact shards,
#      rotate q and k, and append k and v to the KV cache at this position.
#   b. For each 32-token block of the cache (flash-attention style):
#        scores = q @ K_block^T                          (FPU matmul)
#        update running max m, sum l, rescale O          (SFPU online softmax)
#        O += softmax_probabilities @ V_block            (FPU matmul)
#      The last block is masked beyond the current position.
#   c. O / l is written into the dense context vector.
#
# Dst tile layout during attention: 0 = scores/probabilities,
# 1..head_tiles = O, then m (max), l (sum), alpha (rescale factor).

# SFPU load/store offsets that together cover the four live query rows (one
# per head of the GQA group) across both column faces of a Dst tile.
GQA_ROW_CHUNKS = (0, 2, 16, 18)


def attention(cfg, q, key_cache, value_cache, context, *, rope_inputs=None, partial_output=None):
  """Build the fused attention launch, one program variant per attention core.

    rope_inputs     (q_compact, k_compact, v_compact, cos, sin): rotate the new
                    q/k and append k/v to the cache first (the decode path).
                    None: read already-rotated query heads from q (tests).
    partial_output  8B split attention: four cores per KV head each attend to
                    every fourth cache block and write FP32 (O, m, l) state for
                    attention_merge instead of the final context.
  """
  attention_cores = cfg.attention_cores
  if partial_output is not None:
    if any(buffer.dtype is not DType.BF16 for buffer in (q, key_cache, value_cache, context)):
      raise ValueError("split attention requires BF16 queries, caches, and context")
    if (partial_output.dtype is not DType.F32 or partial_output.global_address or partial_output.axis != 0 or
        partial_output.shape != (32, cfg.head_tiles + 2, 1024) or
        partial_output.cores != P100_WORKER_CORES[:32]):
      raise ValueError("split attention requires one FP32 partial state on each of 32 workers")
    attention_cores = 32
  group_size = 4 if partial_output is not None else cfg.q_heads // attention_cores
  inputs = None if rope_inputs is None else tuple(_global_tile_view(b, f"attention_{b.name}") for b in rope_inputs[:3]) + tuple(rope_inputs[3:])
  return specialize(
    lambda head: _attention_program(cfg, q, key_cache, value_cache, context, rope_inputs=inputs, head_index=head if partial_output is None else head // 4, group_size=group_size,
      split_index=None if partial_output is None else head % 4, partial_output=partial_output),
    P100_WORKER_CORES[:attention_cores], tuple(range(attention_cores)),
  )


def _attention_program(cfg, q: Buffer, key_cache: Buffer, value_cache: Buffer, context: Buffer,
  *, rope_inputs=None, head_index=None, group_size=4, split_index=None, partial_output=None,
) -> Program:
  """One attention core: query heads [head_index * group_size, +group_size) of one KV head."""
  # These chunks span both column faces as well as the live row pairs.
  # Retain the complete footprint even when fewer query rows are active.
  row_chunks = GQA_ROW_CHUNKS
  group_shift = group_size.bit_length() - 1
  kv_blocks = Const("kv_blocks", 1)
  valid_columns = Const("valid_columns", 1)
  kv_head = Const("kv_head", tuple(head // 4 for head in range(32)) if partial_output is not None
                  else tuple(range(cfg.q_heads // group_size)))
  start_pos = Const("start_pos", 0)
  p = Program(
    P100_WORKER_CORES[:32 if partial_output is not None else cfg.q_heads // group_size], q, key_cache, value_cache, context,
    *((partial_output,) if partial_output is not None else ()),
    kv_blocks, valid_columns,
    *((kv_head,) if rope_inputs is None else (*rope_inputs, start_pos)), fp32_dst=True,
  )
  # FPU matmul owns replay slots 16..31; SFPU shares the physical replay RAM.
  p.sfpu._mop.state.replay.used.update(range(16, 32))
  # L1 working memory. The query stays resident; K and V blocks stream through.
  query_cb = p.cb(key_cache.dtype, depth=cfg.head_tiles)
  key_cb = p.cb(key_cache.dtype, depth=2 * cfg.head_tiles)
  value_cb = p.cb(key_cache.dtype, depth=2 * cfg.head_tiles)
  probability_cb = p.cb(key_cache.dtype, depth=cfg.head_tiles)
  mask_cb = p.cb(DType.F32, depth=1)
  zero_cb = p.cb(DType.F32, depth=1)
  context_cb = p.cb(context.dtype if partial_output is None else DType.F32,
                    depth=cfg.head_tiles + (2 if partial_output is not None else 0))
  # a. Query (and, on the decode path, RoPE + KV-cache append).
  if rope_inputs is not None:
    _attention_rope(cfg, p, rope_inputs, key_cache, value_cache, start_pos, head_index, query_cb, group_size)
  else:
    query_heads_l1 = p.l1(group_size * q.tile_size, alignment=16)
    _zero_l1_words(p.brisc, query_cb.addr, query_cb.size // 4)
    for group_row in range(group_size):
      source = query_heads_l1 + group_row * q.tile_size
      p.brisc.noc.read_tile(q, head_index * group_size + group_row, source)
      for feature in range(cfg.head_tiles):
        for face in range(2):
          l1.copy_words(p.brisc, source,
            query_cb.addr + feature * query_cb.tile_size + _bf16_tile_byte_offset(group_row * 32 + face * 16),
            8, source_offset=_bf16_tile_byte_offset(feature * 32 + face * 16))

  def split_count(k, count, last=None):
    """Split attention: this core visits blocks split_index, split_index + 4, ..."""
    if split_index is None: return
    if last is not None:
      with k.scope():
        owner = k.reg()
        k.andi(owner, last, 3)
        k.srli(last, last, 2)
        masked = k._new_label("split_has_tail")
        k.li(count, split_index)
        k.beq(owner, count, masked)
        k.li(last, -1)
        k.label(masked)
        k.read(count, p.param_addr(kv_blocks))
    k.addi(count, count, 3 - split_index)
    k.srli(count, count, 2)

  # b. BRISC: a zero tile and the causal mask for the last block, then every
  #    32-token K and V block of this KV head's cache.
  with p.brisc.scope():
    head, block_count, tail = p.brisc.reg(3)
    if head_index is None: p.brisc.read(head, p.param_addr(kv_head))
    else: p.brisc.li(head, head_index)
    p.brisc.read(block_count, p.param_addr(kv_blocks))
    split_count(p.brisc, block_count)
    p.brisc.read(tail, p.param_addr(valid_columns))

    CB.reserve_back(p.brisc, zero_cb)
    with p.brisc.scope():
      target = p.brisc.reg()
      CB.get_write_ptr(p.brisc, zero_cb, target)
      _zero_l1_words(p.brisc, target, zero_cb.tile_size // 4)
    CB.push_back(p.brisc, zero_cb)

    # Mask: -inf for cache columns at or beyond valid_columns, 0 elsewhere.
    CB.reserve_back(p.brisc, mask_cb)
    with p.brisc.scope():
      target = p.brisc.reg()
      CB.get_write_ptr(p.brisc, mask_cb, target)
      _zero_l1_words(p.brisc, target, mask_cb.tile_size // 4)
      with p.brisc.scope():
        column, limit, negative_infinity = p.brisc.reg(3)
        p.brisc.mv(column, tail)
        p.brisc.li(limit, cfg.kv_block)
        p.brisc.li(negative_infinity, 0xff800000)
        with p.brisc.loop(Cond(column, "<u", limit)):
          with p.brisc.scope():
            face_offset, within_face, offset = p.brisc.reg(3)
            p.brisc.srli(face_offset, column, 4)
            p.brisc.slli(face_offset, face_offset, 10)
            p.brisc.andi(within_face, column, 15)
            p.brisc.slli(within_face, within_face, 2)
            p.brisc.add(offset, face_offset, within_face)
            for row in range(group_size):
              with p.brisc.scope():
                address = p.brisc.reg(exclude=(target, offset))
                p.brisc.add(address, target, offset)
                if row: p.brisc.addi(address, address, row * 64)
                p.brisc.sw(negative_infinity, address)
          p.brisc.addi(column, column, 1)
    CB.push_back(p.brisc, mask_cb)

    for block in p.brisc.range(block_count):
      CB.reserve_back(p.brisc, query_cb, cfg.head_tiles)
      CB.push_back(p.brisc, query_cb, cfg.head_tiles)
      with p.brisc.scope():
        first, block_offset = p.brisc.reg(2, exclude=(head, block))
        p.brisc.srli(first, head, 2 - group_shift)
        p.brisc.slli(first, first, cfg.cache_tiles_per_head.bit_length() - 1)
        if split_index is None:
          p.brisc.slli(block_offset, block, cfg.head_tiles.bit_length() - 1)
        else:
          p.brisc.slli(block_offset, block, 2)
          p.brisc.addi(block_offset, block_offset, split_index)
          p.brisc.slli(block_offset, block_offset, cfg.head_tiles.bit_length() - 1)
        p.brisc.add(first, first, block_offset)
        with p.brisc.noc.transaction() as transaction:
          for cache, cb in ((key_cache, key_cb), (value_cache, value_cb)):
            CB.reserve_back(p.brisc, cb, cfg.head_tiles)
            for feature in range(cfg.head_tiles):
              with p.brisc.scope():
                tile = p.brisc.reg(exclude=first)
                p.brisc.addi(tile, first, feature)
                source_address, source_coordinate = p.brisc.noc._dram_tile(cache, tile)
                target = p.brisc.reg(exclude=(source_address, source_coordinate, first))
                CB.get_write_ptr(p.brisc, cb, target)
                if feature:
                  offset = p.brisc.reg(exclude=(source_address, source_coordinate, target, first))
                  p.brisc.li(offset, feature * cb.tile_size)
                  p.brisc.add(target, target, offset)
                transaction.read(source_address, source_coordinate, target, cb.tile_size)
        for cb in (key_cb, value_cb): CB.push_back(p.brisc, cb, cfg.head_tiles)

  # b. TRISC0: per block, (q, K) pairs for the scores, the mask on the last
  #    block, then (probabilities, V) pairs for the output.
  with p.trisc0.scope():
    block_count, last_block = p.trisc0.reg(2)
    p.trisc0.read(block_count, p.param_addr(kv_blocks))
    p.trisc0.addi(last_block, block_count, -1)
    split_count(p.trisc0, block_count, last_block)
    # Each phase writes its invariant unpack modes once; per-tile moves
    # then update only CB addresses.
    for block in p.trisc0.range(block_count):
      p.unpack.prepare_matmul_formats(key_cache.dtype, right_transpose=True)
      for feature in range(cfg.head_tiles):
        p.unpack.move_matmul(query_cb, key_cb, right_transpose=True, configure_format=False)
      no_mask = p.trisc0._new_label("gqa_unpack_no_mask")
      p.trisc0.bne(block, last_block, no_mask)
      p.unpack.move_pair(zero_cb, mask_cb)
      p.trisc0.label(no_mask)
      p.unpack.prepare_matmul_formats(key_cache.dtype)
      for feature in range(cfg.head_tiles):
        p.unpack.move_matmul(probability_cb, value_cb, configure_format=False)

  # b. TRISC1: initialize O = 0, m = -inf, l = 0; then per block
  #    scores = q K^T (+ mask), online softmax update, O += P V.
  zero = p.sfpu.program()
  value = zero.load_float(0.0)
  zero.store(value, format=SfpuFormat.FP32)
  zero = zero.finish()
  one = p.sfpu.program()
  value = one.load_float(1.0)
  one.store(value, format=SfpuFormat.FP32)
  one = one.finish()
  with p.trisc1.scope():
    block_count, last_block = p.trisc1.reg(2)
    p.trisc1.read(block_count, p.param_addr(kv_blocks))
    p.trisc1.addi(last_block, block_count, -1)
    split_count(p.trisc1, block_count, last_block)
    # Context occupies one Dst tile per feature tile, followed by m, l, alpha.
    for tile in (*range(1, cfg.head_tiles + 2), cfg.head_tiles + 3): p.sfpu.map(zero, tile=tile)
    # Keep inactive rows finite when the row mapper traverses the top half.
    # Only the four live rows are overwritten with the online initial state.
    p.sfpu.map(one, tile=cfg.head_tiles + 2)
    _select_dst_tile(p.sfpu, 0)
    for word in _sfpu_float_words(LReg.L0, float("-inf")):
      p.sfpu._issue(word)
    for chunk in row_chunks:
      p.sfpu._issue(TT.TTSFPSTORE(
        LReg.L0, SfpuFormat.FP32, 7, (cfg.head_tiles + 1) * 64 + chunk,
      ))
    for word in _sfpu_float_words(LReg.L0, 0.0): p.sfpu._issue(word)
    for chunk in row_chunks:
      p.sfpu._issue(TT.TTSFPSTORE(
        LReg.L0, SfpuFormat.FP32, 7, (cfg.head_tiles + 2) * 64 + chunk,
      ))
    stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)

    for block in p.trisc1.range(block_count):
      for feature in range(cfg.head_tiles):
        p.fpu.matmul(dst_tile=0, accumulate=feature != 0, right_transpose=True, fidelity=2)
      unmasked = p.trisc1._new_label("gqa_score_unmasked")
      p.trisc1.bne(block, last_block, unmasked)
      p.fpu.binary("add", dst_tile=0, accumulate=True)
      p.trisc1.label(unmasked)
      _select_dst_tile(p.sfpu, 0)
      _softmax_online_update(cfg, p.sfpu, row_chunks)
      p.sfpu.publish()
      for tile in range(1, cfg.head_tiles + 1):
        p.fpu.matmul(dst_tile=tile, accumulate=True, fidelity=2)

    # c. O = O / l (split attention leaves this to attention_merge).
    _select_dst_tile(p.sfpu, 0)
    if partial_output is None:
      for output in range(64, (cfg.head_tiles + 1) * 64, 64):
        for chunk in row_chunks:
          _issue_sfpu_program(p.sfpu, _softmax_normalize_program(
            output_offset=output + chunk, sum_offset=(cfg.head_tiles + 2) * 64 + chunk,
          ))
    p.sfpu.publish()

  # TRISC2: per block, pack the probabilities for the P V matmul; at the end, pack O.
  # Pack one P copy per feature tile while retaining the online state.
  # Release Dst after all context tiles have been packed.
  with p.trisc2.scope():
    block_count = p.trisc2.reg()
    p.trisc2.read(block_count, p.param_addr(kv_blocks))
    split_count(p.trisc2, block_count)
    for _ in p.trisc2.range(block_count):
      sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
      for _ in range(cfg.head_tiles):
        p.pack._move_acquired(probability_cb, 0, False)
      sem_get(p.trisc2, Sem.MATH_PACK)
    p.pack.move_tiles(context_cb, tiles=tuple(range(1, cfg.head_tiles + (3 if partial_output is not None else 1))))

  if partial_output is not None:
    p.ncrisc.noc.write_tiles_from_cb(context_cb, partial_output, tuple(range(cfg.head_tiles + 2)))
    return p

  # c. NCRISC: each specialized worker scatters its query heads into the dense context.
  CB.wait_front(p.ncrisc, context_cb, cfg.head_tiles)
  with p.ncrisc.noc.transaction() as transaction:
    for group_row in range(group_size):
      for feature in range(cfg.head_tiles):
        first_element = (head_index * group_size + group_row) * cfg.head_dim + feature * 32
        with p.ncrisc.scope():
          target_address, target_coordinate = p.ncrisc.noc._dram_tile(context, first_element // 1024)
          for face in range(2):
            with p.ncrisc.scope():
              target = p.ncrisc.reg(exclude=target_address)
              p.ncrisc.mv(target, target_address)
              _add_constant(p.ncrisc, target, _dense_byte_offset(context, first_element % 1024 + face * 16))
              transaction.write(
                context_cb.addr + feature * context_cb.tile_size + _bf16_tile_byte_offset(group_row * 32 + face * 16) * context.dtype.itemsize // 2,
                target, target_coordinate, 16 * context.dtype.itemsize, posted=False,
              )
  CB.pop_front(p.ncrisc, context_cb, cfg.head_tiles)
  return p


def _attention_rope(cfg, p, inputs, key_cache, value_cache, start_pos, head, query_cb, group_size):
  """Rotate a worker's Q heads and their K in one tile; retain Q in L1.

  RoPE: x * cos + rotate_half(x) * sin, where rotate_half(x) = [-x2, x1]
  for the two halves x1, x2 of each head. BRISC gathers the head's values
  from the projection cores' compact shards and builds four tiles: x,
  rotate_half(x), cos, sin. Group rows 0..group_size-1 hold the query heads,
  row group_size holds the key head.

  At 16/32 workers, workers sharing a KV head write identical cache bytes.
  Each waits for its own acknowledged writes before reading that cache row.
  """
  q, k, v, cos, sin = inputs
  operands = p.cb(DType.BF16, depth=4)
  result = p.cb(DType.BF16, depth=1)
  ready = p.cb(DType.BF16, depth=1)
  # Fixed allocation sizes make CB addresses identical in all head variants.
  # A TP shard has fewer KV rows per worker, so one head spans more tiles.
  staging_tiles = max(20, math.ceil(cfg.head_dim / min(_token_counts(cfg.kv_dim, cfg.projection_cores))) + 1)
  source_l1 = p.l1(staging_tiles * q.tile_size, alignment=16)
  v_l1 = p.l1(staging_tiles * v.tile_size, alignment=16)
  v_head = p.l1(v.tile_size, alignment=16)
  cos_l1 = p.l1(cos.tile_size, alignment=16)
  sin_l1 = p.l1(sin.tile_size, alignment=16)
  with p.brisc.scope():
    position, tile, row = p.brisc.reg(3)
    p.brisc.read(position, p.param_addr(start_pos))
    p.brisc.srli(tile, position, (1024 // cfg.head_dim).bit_length() - 1)
    p.brisc.andi(row, position, (1024 // cfg.head_dim) - 1)
    p.brisc.slli(row, row, cfg.head_dim.bit_length() - 1)
    if cos.tilized:
      # A table token is four logical rows, or 128 BF16 elements.
      with p.brisc.scope():
        upper = p.brisc.reg(exclude=row)
        p.brisc.andi(upper, row, 512)
        p.brisc.slli(upper, upper, 1)
        p.brisc.andi(row, row, 511)
        p.brisc.add(row, row, upper)
    else:
      p.brisc.slli(row, row, 1)
    with p.brisc.noc.transaction() as transaction:
      for table, target in ((cos, cos_l1), (sin, sin_l1)):
        with p.brisc.scope():
          address, coordinate = p.brisc.noc._dram_tile(table, tile)
          transaction.read(address, coordinate, target, table.tile_size)
    for group in range(group_size + 1):
      is_query = group < group_size
      first = ((head * group_size + group) if is_query else head // (4 // group_size)) * cfg.head_dim
      locations = tuple(_compact_projection_location(cfg, first + i, query=is_query)
                        for i in range(cfg.head_dim))
      tiles = tuple(dict.fromkeys(t for t, _ in locations))
      source = q if is_query else k
      with p.brisc.noc.transaction() as transaction:
        for i, source_tile in enumerate(tiles):
          with p.brisc.scope():
            address, coordinate = p.brisc.noc._dram_tile(source, source_tile)
            transaction.read(address, coordinate, source_l1 + i * source.tile_size, source.tile_size)
          if not is_query:
            with p.brisc.scope():
              address, coordinate = p.brisc.noc._dram_tile(v, source_tile)
              transaction.read(address, coordinate, v_l1 + i * v.tile_size, v.tile_size)
      with p.brisc.scope():
        sign = p.brisc.reg()
        p.brisc.li(sign, 0x8000)
        for i, (source_tile, slot) in enumerate(locations):
          source_offset = tiles.index(source_tile) * source.tile_size + _compact_slot_byte_offset(slot)
          with p.brisc.scope():
            value = p.brisc.reg(exclude=sign)
            p.brisc.read(value, source_l1 + source_offset, bytes=2)
            p.brisc.write(operands.addr + _bf16_tile_byte_offset(group * cfg.head_dim + i), value, bytes=2)
            if i >= cfg.head_dim // 2: p.brisc.xor(value, value, sign)
            rotated = group * cfg.head_dim + (i + cfg.head_dim // 2 if i < cfg.head_dim // 2 else i - cfg.head_dim // 2)
            p.brisc.write(operands.addr + operands.tile_size + _bf16_tile_byte_offset(rotated), value, bytes=2)
            if not is_query:
              p.brisc.read(value, v_l1 + source_offset, bytes=2)
              p.brisc.write(v_head + _bf16_tile_byte_offset(i), value, bytes=2)
      for table, operand in ((cos_l1, 2), (sin_l1, 3)):
        for i in range(0, cfg.head_dim, 16):
          with p.brisc.scope():
            offset = p.brisc.reg(exclude=row)
            p.brisc.addi(offset, row, _dense_byte_offset(cos, i))
            l1.copy_words(p.brisc, table,
                          operands.addr + operand * operands.tile_size + _bf16_tile_byte_offset(group * cfg.head_dim + i),
                          8, source_offset=offset, unroll=8)
  CB.push_back(p.brisc, operands, 4)
  for _ in range(4): p.unpack.move(operands, UnpackTarget.SRCA)
  p.fpu.copy_a_tiles(dst_tiles=range(4))
  sfpu = p.sfpu.program()
  x = sfpu.load(offset=0)
  rotated = sfpu.load(offset=64)
  cosine = sfpu.load(offset=128)
  sine = sfpu.load(offset=192)
  product = sfpu.mul(x, cosine)
  value = sfpu.mad(rotated, sine, product)
  sfpu.round_bf16(value, into=value)
  sfpu.store(value, offset=0)
  p.sfpu.map(sfpu.finish(), tile=0)
  p.sfpu.publish()
  p.pack.move_tiles(result, tiles=(0,))
  CB.wait_front(p.ncrisc, result)
  _zero_l1_words(p.ncrisc, query_cb.addr, query_cb.size // 4)
  for group in range(group_size):
    for half in range(cfg.head_tiles):
      for face in range(2):
        l1.copy_words(p.ncrisc,
                      result.addr + _bf16_tile_byte_offset(group * cfg.head_dim + half * 32 + face * 16),
                      query_cb.addr + half * query_cb.tile_size + _bf16_tile_byte_offset(group * 32 + face * 16),
                      8, unroll=8)
  _append_cache_rows(cfg, p, result.addr + _bf16_tile_byte_offset(group_size * cfg.head_dim), v_head,
                     key_cache, value_cache, start_pos, head // (4 // group_size))
  CB.pop_front(p.ncrisc, result)
  CB.push_back(p.ncrisc, ready)
  # All dependencies are within this KV group; there is no global barrier.
  CB.wait_front(p.brisc, ready)


def _append_cache_rows(cfg, p, k_l1, v_l1, key_cache, value_cache, start_pos, head):
  """NCRISC: write this head's new K/V row into the caches at start_pos.

  Cache layout per KV head: [max_tokens / 32 blocks][head_tiles feature tiles],
  each tile = 32 tokens x 32 features; this token is one row of each tile.
  """
  size = key_cache.dtype.itemsize
  shift = size.bit_length() - 1
  k = p.ncrisc
  with k.scope():
    position, block, row = k.reg(3)
    k.read(position, p.param_addr(start_pos))
    k.srli(block, position, 5)
    k.slli(block, block, (cfg.head_tiles.bit_length() - 1))
    _add_constant(k, block, head * cfg.cache_tiles_per_head)
    k.andi(row, position, 15)
    k.slli(row, row, 4 + shift)
    with k.scope():
      bottom = k.reg(exclude=(position, row))
      k.andi(bottom, position, 16)
      k.slli(bottom, bottom, 5 + shift)
      k.add(row, row, bottom)
    with k.noc.transaction() as transaction:
      for half in range(cfg.head_tiles):
        with k.scope():
          tile = k.reg(exclude=(block, row))
          k.addi(tile, block, half)
          for cache, source in ((key_cache, k_l1), (value_cache, v_l1)):
            address, coordinate = k.noc._dram_tile(cache, tile)
            for face in range(2):
              with k.scope():
                target = k.reg(exclude=(address, row))
                k.add(target, address, row)
                if face: k.addi(target, target, 256 * size)
                transaction.write(source + half * 16 * size + face * 256 * size,
                                  target, coordinate, 16 * size, posted=False)


def _softmax_online_update(cfg, sfpu, row_chunks=GQA_ROW_CHUNKS):
  """Online softmax step for the four query rows after one score matmul.

    scores  *= 1 / sqrt(head_dim)
    m_new    = max(m_old, max(scores))
    alpha    = exp(m_old - m_new)
    P        = exp(scores - m_new)               (left in Dst tile 0)
    l        = l * alpha + sum(P)
    O       *= alpha                             (P V is added afterwards)
  """
  score = 0
  maximum, total, alpha = ((cfg.head_tiles + i) * 64 for i in (1, 2, 3))
  words = []
  words.extend(_sfpu_float_words(LReg.L4, cfg.head_dim ** -0.5))
  for register, chunk in zip(
    (LReg.L0, LReg.L1, LReg.L2, LReg.L3), row_chunks,
  ):
    words.append(TT.TTSFPLOAD(register, SfpuFormat.FP32, 7, score + chunk))
    _sfpu_mul(words, register, LReg.L4, register)
    words.append(TT.TTSFPSTORE(register, SfpuFormat.FP32, 7, score + chunk))

  # L0 becomes a broadcast maximum for each of the four live rows.
  for left, right in ((LReg.L0, LReg.L2), (LReg.L1, LReg.L3),
                      (LReg.L0, LReg.L1)):
    words.extend((TT.TTSFPSWAP(0, left, right, 1), TT.TTSFPNOP()))
  for rotations in (4, 2, 1):
    words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
    for _ in range(rotations):
      words.extend((
        TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
      ))
    words.extend((TT.TTSFPSWAP(0, LReg.L0, LReg.L1, 1), TT.TTSFPNOP()))

  words.append(TT.TTSFPLOAD(LReg.L2, SfpuFormat.FP32, 7, maximum))
  words.append(TT.TTSFPMOV(0, LReg.L2, LReg.L3, 0))
  # SFPSWAP leaves max(VC, VD) in VC, hence the new maximum remains in L0.
  words.extend((TT.TTSFPSWAP(0, LReg.L0, LReg.L2, 1), TT.TTSFPNOP()))
  for chunk in row_chunks:
    words.append(TT.TTSFPSTORE(
      LReg.L0, SfpuFormat.FP32, 7, maximum + chunk,
    ))
  words.extend((
    TT.TTSFPMAD(LReg.L0, LReg.NEG_ONE, LReg.L3, LReg.L5, 0),
    TT.TTSFPNOP(),
  ))
  for chunk in row_chunks:
    words.append(TT.TTSFPSTORE(
      LReg.L5, SfpuFormat.FP32, 7, alpha + chunk,
    ))
  for word in words: sfpu._issue(word)

  # Shift scores separately so the exp program can reuse its LRegs without a
  # load/subtract lifetime crossing the programmable-constant setup.
  words = []
  for chunk in row_chunks:
    words.extend((
      TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, score + chunk),
      TT.TTSFPLOAD(LReg.L1, SfpuFormat.FP32, 7, maximum + chunk),
      TT.TTSFPMAD(LReg.L1, LReg.NEG_ONE, LReg.L0, LReg.L0, 0),
      TT.TTSFPNOP(),
      TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, score + chunk),
    ))
  for word in words: sfpu._issue(word)

  # alpha = exp(m_old - m_new), and P = exp(score - m_new).
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)
  for chunk in row_chunks:
    _issue_sfpu_program(sfpu, _softmax_exp_program(value_offset=alpha + chunk))
  for chunk in row_chunks:
    _issue_sfpu_program(sfpu, _softmax_exp_program(value_offset=score + chunk))

  # l_new = l_old * alpha + sum(P).  Horizontal reduction is independent in
  # each eight-lane subgroup, one subgroup per live query row.
  words = [
    TT.TTSFPLOAD(register, SfpuFormat.FP32, 7, score + chunk)
    for register, chunk in zip(
      (LReg.L0, LReg.L1, LReg.L2, LReg.L3), row_chunks,
    )
  ]
  _sfpu_add(words, LReg.L0, LReg.L2, LReg.L0)
  _sfpu_add(words, LReg.L1, LReg.L3, LReg.L1)
  _sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
  for rotations in (4, 2, 1):
    words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
    for _ in range(rotations):
      words.extend((
        TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
      ))
    _sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
  words.extend((
    TT.TTSFPLOAD(LReg.L2, SfpuFormat.FP32, 7, total),
    TT.TTSFPLOAD(LReg.L3, SfpuFormat.FP32, 7, alpha),
    TT.TTSFPMAD(LReg.L2, LReg.L3, LReg.L0, LReg.L0, 0),
    TT.TTSFPNOP(),
  ))
  for chunk in row_chunks:
    words.append(TT.TTSFPSTORE(
      LReg.L0, SfpuFormat.FP32, 7, total + chunk,
    ))

  # Rescale the persistent FP32 context before accumulating this block's PV.
  for output in range(64, (cfg.head_tiles + 1) * 64, 64):
    for chunk in row_chunks:
      words.extend((
        TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, output + chunk),
        TT.TTSFPLOAD(LReg.L1, SfpuFormat.FP32, 7, alpha + chunk),
      ))
      _sfpu_mul(words, LReg.L0, LReg.L1, LReg.L0)
      words.append(TT.TTSFPSTORE(
        LReg.L0, SfpuFormat.FP32, 7, output + chunk,
      ))
  for word in words: sfpu._issue(word)
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def _softmax_exp_program(*, value_offset):
  builder = SfpuProgramBuilder()
  value = builder.load(format=SfpuFormat.FP32, offset=value_offset)
  builder.exp(value, into=value)
  builder.store(value, format=SfpuFormat.FP32, offset=value_offset)
  return builder.finish()


def _softmax_normalize_program(*, output_offset, sum_offset):
  builder = SfpuProgramBuilder()
  output = builder.load(format=SfpuFormat.FP32, offset=output_offset)
  denominator = builder.load(format=SfpuFormat.FP32, offset=sum_offset)
  builder.reciprocal(denominator, into=denominator)
  builder.mul(output, denominator, into=output)
  builder.store(output, format=SfpuFormat.FP32, offset=output_offset)
  return builder.finish()


def _issue_sfpu_program(sfpu, program):
  """Run one explicitly addressed 4x8 SFPU footprint."""
  _select_dst_tile(sfpu, 0)
  for word in (*program.setup_words, *program.words): sfpu._issue(word)
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


# ---------------------------------------------------------------------------
# 4. Attention merge (8B split attention only)
# ---------------------------------------------------------------------------

def attention_merge(cfg, partials, context):
  """Merge four FP32 (O, m, l) states per KV head with stable rescaling.

  One core per KV head. For each further partial (O', m', l'):
    m_new = max(m, m'),  alpha = exp(m - m_new),  beta = exp(m' - m_new)
    l = l * alpha + l' * beta,  O = O * alpha + O' * beta
  then context = O / l.
  """
  source = _global_tile_view(partials, "attention_partial_tiles")
  features = cfg.head_tiles
  state_tiles = features + 2

  def build(head):
    p = Program(P100_WORKER_CORES[:8], source, context, fp32_dst=True)
    incoming = p.cb(DType.F32, depth=2 * state_tiles)
    output = p.cb(context.dtype, depth=features)
    for split in range(4):
      order = tuple(range(state_tiles)) if split == 0 else (features, features + 1, *range(features))
      tiles = tuple((head * 4 + split) * state_tiles + tile for tile in order)
      p.brisc.noc.read_tiles_into_cb(source, tiles, incoming)
      for _ in order: p.unpack.move(incoming, UnpackTarget.SRCA)
    p.fpu.copy_a_tiles(dst_tiles=range(state_tiles))
    maximum, total = features * 64, (features + 1) * 64
    # Only four footprints contain live query rows. Other footprints of
    # the maximum tile safely hold alpha and beta during each merge.
    alpha, beta = maximum + 8, maximum + 32
    for _ in range(3):
      p.fpu.copy_a_tiles(dst_tiles=(features + 2, features + 3))
      _select_dst_tile(p.sfpu, 0)
      words = []
      for chunk in GQA_ROW_CHUNKS:
        words.extend((
          TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, maximum + chunk),
          TT.TTSFPLOAD(LReg.L1, SfpuFormat.FP32, 7, (features + 2) * 64 + chunk),
          TT.TTSFPMOV(0, LReg.L0, LReg.L2, 0),
          TT.TTSFPMOV(0, LReg.L1, LReg.L3, 0),
          TT.TTSFPSWAP(0, LReg.L0, LReg.L1, 1), TT.TTSFPNOP(),
          TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, maximum + chunk),
          TT.TTSFPMAD(LReg.L0, LReg.NEG_ONE, LReg.L2, LReg.L2, 0), TT.TTSFPNOP(),
          TT.TTSFPMAD(LReg.L0, LReg.NEG_ONE, LReg.L3, LReg.L3, 0), TT.TTSFPNOP(),
          TT.TTSFPSTORE(LReg.L2, SfpuFormat.FP32, 7, alpha + chunk),
          TT.TTSFPSTORE(LReg.L3, SfpuFormat.FP32, 7, beta + chunk),
        ))
      for word in words: p.sfpu._issue(word)
      stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
      for chunk in GQA_ROW_CHUNKS:
        for offset in (alpha, beta):
          _issue_sfpu_program(p.sfpu, _softmax_exp_program(value_offset=offset + chunk))
        builder = p.sfpu.program()
        old = builder.load(format=SfpuFormat.FP32, offset=total + chunk)
        a = builder.load(format=SfpuFormat.FP32, offset=alpha + chunk)
        old = builder.mul(old, a, into=old)
        builder.free(a)
        new = builder.load(format=SfpuFormat.FP32, offset=(features + 3) * 64 + chunk)
        b = builder.load(format=SfpuFormat.FP32, offset=beta + chunk)
        builder.mad(new, b, old, into=old)
        builder.store(old, format=SfpuFormat.FP32, offset=total + chunk)
        _issue_sfpu_program(p.sfpu, builder.finish())
      for feature in range(features):
        p.fpu.copy_a_tiles(dst_tiles=(features + 2,))
        for chunk in GQA_ROW_CHUNKS:
          builder = p.sfpu.program()
          old = builder.load(format=SfpuFormat.FP32, offset=feature * 64 + chunk)
          a = builder.load(format=SfpuFormat.FP32, offset=alpha + chunk)
          builder.mul(old, a, into=old)
          builder.free(a)
          new = builder.load(format=SfpuFormat.FP32, offset=(features + 2) * 64 + chunk)
          b = builder.load(format=SfpuFormat.FP32, offset=beta + chunk)
          builder.mad(new, b, old, into=old)
          builder.store(old, format=SfpuFormat.FP32, offset=feature * 64 + chunk)
          _issue_sfpu_program(p.sfpu, builder.finish())
    for feature in range(features):
      for chunk in GQA_ROW_CHUNKS:
        _issue_sfpu_program(p.sfpu, _softmax_normalize_program(
          output_offset=feature * 64 + chunk, sum_offset=total + chunk))
    p.sfpu.publish()
    p.pack.move_tiles(output, tiles=tuple(range(features)))
    CB.wait_front(p.ncrisc, output, features)
    with p.ncrisc.noc.transaction() as transaction:
      for row in range(4):
        for feature in range(features):
          first = (head * 4 + row) * cfg.head_dim + feature * 32
          with p.ncrisc.scope():
            address, coordinate = p.ncrisc.noc._dram_tile(context, first // 1024)
            for face in range(2):
              with p.ncrisc.scope():
                target = p.ncrisc.reg()
                p.ncrisc.mv(target, address)
                _add_constant(p.ncrisc, target, _dense_byte_offset(context, first % 1024 + face * 16))
                transaction.write(output.addr + feature * output.tile_size + _bf16_tile_byte_offset(row * 32 + face * 16),
                                  target, coordinate, 32, posted=False)
    CB.pop_front(p.ncrisc, output, features)
    return p
  return specialize(build, P100_WORKER_CORES[:8], tuple(range(8)))


# ---------------------------------------------------------------------------
# 5. Argmax: next token = argmax(logits)
# ---------------------------------------------------------------------------

def argmax(cfg, logits: Buffer, token_history: Buffer, host_output: int,
) -> Program:
  """SFPU-scan logits, reduce 32 candidates/core, and publish the winner.

  Every projection core scans its own compact logits shard (the LM head's
  output) on the SFPU, keeping 32 candidates. BRISC picks the best of
  them and sends (value, token) to core 0. Core 0 picks the global winner, then:
    - writes it to host memory (the token the host reads back),
    - appends it to token_history (the next embedding's input),
    - multicasts next-token runtime parameters for autonomous replay.
  Ties resolve to the lowest token ID.
  """
  local_counts = _token_counts(cfg.vocab_size, len(logits.cores))
  local_starts, cursor = [], 0
  for count in local_counts:
    local_starts.append(cursor)
    cursor += count
  starts = Const("argmax_start", tuple(local_starts))
  counts = Const("argmax_count", local_counts)
  indices = Const("argmax_core", tuple(range(len(logits.cores))))
  write_pos = Const("write_pos", 1)
  write_token = Const("write_token", 1)
  host_address = Const("argmax_host_address", host_output)
  p = Program(
    logits.cores, logits, token_history, host_address,
    starts, counts, indices, write_pos, write_token, fp32_dst=True,
  )
  incoming = p.cb(DType.BF16, depth=logits.tiles_per_item)
  logits_l1 = incoming.addr
  candidates = p.cb(DType.F32, depth=1)
  # Keep the full-page NoC transfer cache-line aligned.
  history_l1 = p.l1(token_history.tile_size, alignment=64)
  local = p.l1(16, alignment=16)
  runtime_l1 = p.l1(32, alignment=16)
  partials = p.l1(len(logits.cores) * 16, alignment=16)
  p.launch = (
    UnicastWrite(
      (logits.cores[0],), partials,
      (bytes(len(logits.cores) * 16),),
    ),
  )

  # BRISC: read this core's logits; overwrite padding beyond its valid
  # count with -inf so padding can never win.
  CB.reserve_back(p.brisc, incoming, logits.tiles_per_item)
  p.brisc.noc.read_tiles(logits, tuple(
    (tile, logits_l1 + tile * logits.tile_size)
    for tile in range(logits.tiles_per_item)
  ))
  with p.brisc.scope():
    count, start, core_index = p.brisc.reg(3)
    p.brisc.read(count, p.param_addr(counts))
    p.brisc.read(start, p.param_addr(starts))
    p.brisc.read(core_index, p.param_addr(indices))
    # Projection padding is unspecified (usually zero); exclude it even when
    # every valid logit is negative. Fill contiguous physical runs in L1.
    for valid in sorted(set(local_counts)):
      done = p.brisc._new_label("argmax_padding_done")
      with p.brisc.scope():
        size, address, value = p.brisc.reg(3)
        p.brisc.li(size, valid)
        p.brisc.bne(count, size, done)
        physical = sorted((i & ~1023) + (i & 512) + ((i & 16) << 4)
                          + ((i & 480) >> 1) + (i & 15)
                          for i in range(valid, logits.tiles_per_item * 1024))
        runs = []
        for index in physical:
          if runs and runs[-1][1] == index: runs[-1][1] += 1
          else: runs.append([index, index + 1])
        for first, end in runs:
          p.brisc.li(value, 0xff80ff80)
          if first & 1:
            p.brisc.write(logits_l1 + first * 2, value, bytes=2)
            first += 1
          p.brisc.li(address, logits_l1 + first * 2)
          for _ in p.brisc.range((end - first) // 2):
            p.brisc.sw(value, address)
            p.brisc.addi(address, address, 4)
          if end & 1: p.brisc.write(logits_l1 + (end - 1) * 2, value, bytes=2)
      p.brisc.label(done)
    p.brisc.fence()
    CB.push_back(p.brisc, incoming, logits.tiles_per_item)
    # BRISC: best of the SFPU's 32 candidates (key = order-preserving value bits).
    CB.wait_front(p.brisc, candidates)
    best_key, best_id, key, token, address, physical = p.brisc.reg(6)
    p.brisc.li(best_key, 0)
    p.brisc.li(best_id, 0x7fffffff)
    CB.get_read_ptr(p.brisc, candidates, address)
    for _ in p.brisc.range(32):
      p.brisc.lw(key, address)
      p.brisc.srli(key, key, 15)
      p.brisc.lw(physical, address, 4)
      physical_to_logical(p.brisc, physical, token, tilized=True)
      p.brisc.addi(address, address, 8)
      skip = p.brisc._new_label("argmax_skip")
      replace = p.brisc._new_label("argmax_replace")
      p.brisc.bgeu(token, count, skip)
      p.brisc.add(token, start, token)
      p.brisc.bltu(best_key, key, replace)
      p.brisc.bne(best_key, key, skip)
      p.brisc.bgeu(token, best_id, skip)
      p.brisc.label(replace)
      p.brisc.mv(best_key, key)
      p.brisc.mv(best_id, token)
      p.brisc.label(skip)
    CB.pop_front(p.brisc, candidates)

    p.brisc.write(local, best_key)
    p.brisc.write(local + 4, best_id)
    p.brisc.write(local + 8, 1)
    with p.brisc.scope():
      target, stride, base = p.brisc.reg(3, exclude=core_index)
      p.brisc.li(stride, 16)
      p.brisc.mul(target, core_index, stride)
      p.brisc.li(base, partials)
      p.brisc.add(target, target, base)
      p.brisc.noc.write(
        local, target, noc_coord(logits.cores[0]), 12, posted=False,
      )

    # Core 0 only: wait for every core's candidate and keep the best.
    reducer_done = p.brisc._new_label("argmax_reducer_done")
    p.brisc.bne(core_index, R.ZERO, reducer_done)
    p.brisc.li(best_key, 0)
    p.brisc.li(best_id, 0)
    for index in p.brisc.range(len(logits.cores)):
      with p.brisc.scope():
        address, stride, ready, candidate_key, candidate_id, base = (
          p.brisc.reg(6)
        )
        p.brisc.li(stride, 16)
        p.brisc.mul(address, index, stride)
        p.brisc.li(base, partials)
        p.brisc.add(address, address, base)
        wait = p.brisc._new_label("argmax_wait_partial")
        ready_label = p.brisc._new_label("argmax_partial_ready")
        p.brisc.label(wait)
        p.brisc.lw(ready, address, 8)
        p.brisc.bne(ready, R.ZERO, ready_label)
        p.brisc.fence()
        p.brisc.j(wait)
        p.brisc.label(ready_label)
        p.brisc.lw(candidate_key, address, 0)
        p.brisc.lw(candidate_id, address, 4)
        skip = p.brisc._new_label("argmax_skip_partial")
        p.brisc.bgeu(best_key, candidate_key, skip)
        p.brisc.mv(best_key, candidate_key)
        p.brisc.mv(best_id, candidate_id)
        p.brisc.label(skip)
    # Scalar NoC writes require a 16-byte-aligned source address.
    p.brisc.write(local, best_id)
    with p.brisc.scope():
      target_address, position, offset = p.brisc.reg(3)
      p.brisc.read(target_address, p.param_addr(host_address))
      p.brisc.read(position, p.param_addr(write_pos))
      p.brisc.slli(offset, position, 4)
      p.brisc.add(target_address, target_address, offset)
      p.brisc.noc.write(
        local, target_address, CQConfig.PCIE_COORD, 16,
        target_middle_address=CQConfig.PCIE_MID, posted=False,
      )
    history_done = p.brisc._new_label("argmax_history_done")
    with p.brisc.scope():
      position, tile, within, enabled = p.brisc.reg(4)
      p.brisc.read(enabled, p.param_addr(write_token))
      p.brisc.beq(enabled, R.ZERO, history_done)
      p.brisc.read(position, p.param_addr(write_pos))
      p.brisc.srli(tile, position, 10)
      p.brisc.andi(within, position, 1023)
      p.brisc.noc.read_tile(token_history, tile, history_l1)
      p.brisc.slli(within, within, 2)
      _add_constant(p.brisc, within, history_l1)
      p.brisc.write(within, best_id)
      target_address, target_coordinate = p.brisc.noc._dram_tile(
        token_history, tile,
      )
      p.brisc.noc.write(
        history_l1, target_address, target_coordinate,
        token_history.tile_size, posted=False,
      )
    p.brisc.label(history_done)

    # Prepare the next token's compact runtime state on device. Host-driven
    # replay may overwrite it, while autonomous replay can consume it directly.
    with p.brisc.scope():
      position, value = p.brisc.reg(2)
      p.brisc.read(position, p.param_addr(write_pos))
      p.brisc.write(runtime_l1, position)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE, position)
      p.brisc.addi(value, position, 1)
      p.brisc.write(runtime_l1 + 4, value)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 4, value)
      p.brisc.write(runtime_l1 + 8, 1)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 8, 1)
      p.brisc.write(runtime_l1 + 12, position)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 12, position)
      p.brisc.srli(value, position, 5)
      p.brisc.addi(value, value, 1)
      p.brisc.write(runtime_l1 + 16, value)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 16, value)
      p.brisc.andi(value, position, 31)
      p.brisc.addi(value, value, 1)
      p.brisc.write(runtime_l1 + 20, value)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 20, value)
      for rect in rectangles(logits.cores):
        start, end = mcast_coords(rect)
        p.brisc.noc.multicast_write(
          runtime_l1, TensixL1.RUNTIME_PARAM_BASE, start, end, 24,
        )
    p.brisc.label(reducer_done)
  # TRISC0/1/2: SFPU scan of the logits -> 32 (value, index) candidates.
  CB.wait_front(p.trisc0, incoming, logits.tiles_per_item)
  load_bf16(p, logits_l1, logits.tiles_per_item)
  CB.pop_front(p.trisc0, incoming, logits.tiles_per_item)
  scan_bf16(p.trisc1, logits.tiles_per_item)
  p.trisc1.emit(TT.TTSFPSTORE(0, 4, 0, 0))
  p.trisc1.emit(TT.TTSFPSTORE(4, 4, 0, 2))
  p.sfpu.publish()
  p.pack.move(candidates, tile=0)
  return p


# ---------------------------------------------------------------------------
# Appendix: SFPU instruction helpers
# ---------------------------------------------------------------------------

def _round_fp8_program(dtype=None):
  """Round FP32 mantissas to E4M3 before the truncating hardware packer."""
  dtype = FP8_ACTIVATION if dtype is None else dtype
  shift = 20
  maximum = 0x43e00000
  setup = []
  for reg, bits in ((LReg.L1, (1 << (shift - 1)) - 1), (LReg.L2, 1), (LReg.L3, (0xffffffff << shift) & 0xffffffff),
                    (LReg.L5, maximum), (LReg.L6, maximum | 0x80000000)):
    setup.extend((TT.TTSFPLOADI(reg, 10, bits & 0xffff), TT.TTSFPLOADI(reg, 8, bits >> 16)))
  return SfpuProgram(tuple(setup), (
    TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0),
    TT.TTSFPMOV(0, LReg.L0, LReg.L4, 0),
    TT.TTSFPSHFT((-shift) & 0xfff, 0, LReg.L4, 1),
    TT.TTSFPAND(0, LReg.L2, LReg.L4, 0),
    TT.TTSFPIADD(0, LReg.L1, LReg.L4, 4),
    TT.TTSFPIADD(0, LReg.L4, LReg.L0, 4),
    TT.TTSFPAND(0, LReg.L3, LReg.L0, 0),
    TT.TTSFPMOV(0, LReg.L5, LReg.L7, 0),
    TT.TTSFPSWAP(0, LReg.L7, LReg.L0, 1), TT.TTSFPNOP(),
    TT.TTSFPMOV(0, LReg.L6, LReg.L7, 0),
    TT.TTSFPSWAP(0, LReg.L0, LReg.L7, 1), TT.TTSFPNOP(),
    # Explicitly flush subnormals: the native unpacker is not IEEE there.
    TT.TTSFPABS(0, LReg.L0, LReg.L4, 1),
    TT.TTSFPLOADI(LReg.L7, 10, 0), TT.TTSFPLOADI(LReg.L7, 8, 0x3c80),
    TT.TTSFPIADD(0, LReg.L4, LReg.L7, 6),
    TT.TTSFPSHFT((-31) & 0xfff, 0, LReg.L7, 1),
    TT.TTSFPIADD(0xfff, LReg.L7, LReg.L7, 5),
    TT.TTSFPAND(0, LReg.L7, LReg.L0, 0),
    TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0),
  ))


def _sfpu_float_words(register, value):
  """Two SFPLOADI words that load the FP32 ``value`` into an SFPU register."""
  bits = struct.unpack("<I", struct.pack("<f", float(value)))[0]
  return (
    TT.TTSFPLOADI(register, 10, bits & 0xffff),
    TT.TTSFPLOADI(register, 8, bits >> 16),
  )


def _sfpu_add(words, left, right, output):
  words.extend((TT.TTSFPADD(LReg.ONE, left, right, output, 0), TT.TTSFPNOP()))


def _sfpu_mul(words, left, right, output, modifier=0):
  words.extend((TT.TTSFPMUL(left, right, LReg.ZERO, output, modifier), TT.TTSFPNOP()))


# ---------------------------------------------------------------------------
# Appendix: address and layout helpers
# ---------------------------------------------------------------------------
#
# A "tilized" BF16 tile stores element (row, col) of its 32x32 grid in face
# (row // 16) * 2 + col // 16, at offset (row % 16) * 16 + col % 16 within
# the face. Vectors of 1024 values are laid out as a tile's 32 rows.

def _token_counts(items, cores):
  """Split ``items`` over ``cores`` as evenly as possible, earlier cores first."""
  per_core, extra = divmod(items, cores)
  return tuple(per_core + (index < extra) for index in range(cores))


def _zero_l1_words(k, address, count):
  """Clear tile scratch with eight stores per loop iteration."""
  if count == 0: return
  if count % 8: raise ValueError("scratch clear requires a multiple of eight words")
  with k.scope():
    pointer, remaining = k.reg(2, exclude=address if isinstance(address, R) else ())
    if isinstance(address, R): k.mv(pointer, address)
    else: k.li(pointer, address)
    k.li(remaining, count)
    loop = k._new_label("clear_scratch")
    k.label(loop)
    for i in range(8): k.sw(R.ZERO, pointer, i * 4)
    k.addi(pointer, pointer, 32)
    k.addi(remaining, remaining, -8)
    k.bne(remaining, R.ZERO, loop)


def _add_constant(k, reg, value):
  """reg += value (value need not fit an addi immediate)."""
  with k.scope():
    delta = k.reg(exclude=reg)
    k.li(delta, value)
    k.add(reg, reg, delta)


def _dense_offset(k, buffer, index, output):
  """output = byte offset of element ``index`` (a register) in ``buffer``."""
  if buffer.tilized:
    _tile_offset(k, index, output, buffer.dtype)
  else:
    k.slli(output, index, buffer.dtype.itemsize.bit_length() - 1)


def _tile_offset(k, index, output, dtype=DType.BF16):
  """output = byte offset of element ``index`` (a register) in tilized storage."""
  # Logical feature -> byte offset in face-tilized BF16 storage.
  with k.scope():
    tmp = k.reg(exclude=(index, output))
    k.andi(output, index, 15)
    k.slli(output, output, 1)
    k.andi(tmp, index, 16)
    k.slli(tmp, tmp, 5)
    k.or_(output, output, tmp)
    k.andi(tmp, index, 480)
    k.or_(output, output, tmp)
    k.srli(tmp, index, 9)
    k.slli(tmp, tmp, 10)
    k.or_(output, output, tmp)
    if dtype.itemsize == 1: k.srli(output, output, 1)
    elif dtype.itemsize == 4: k.slli(output, output, 1)


def _bf16_tile_byte_offset(index):
  """Physical byte offset of a logical BF16 element in a face-tilized tile."""
  row, column = divmod(index, 32)
  face = (row // 16) * 2 + column // 16
  return face * 512 + (row % 16) * 32 + (column % 16) * 2


def _dense_byte_offset(buffer, index):
  """Address dense vectors independently of transient packed compute tiles."""
  return (_bf16_tile_byte_offset(index) // 2 if buffer.tilized else index) * buffer.dtype.itemsize


def _compact_feature_location(cfg, feature, total_features):
  """(projection core, slot) that holds output ``feature`` in a compact buffer."""
  counts = _token_counts(total_features, cfg.projection_cores)
  cursor = 0
  for core, count in enumerate(counts):
    if feature < cursor + count: return core, feature - cursor
    cursor += count
  raise ValueError("compact feature index is out of range")


def _compact_projection_location(cfg, feature, *, query):
  return _compact_feature_location(cfg, 
    feature, cfg.q_dim if query else cfg.kv_dim,
  )


def _compact_slot_byte_offset(slot):
  return _bf16_tile_byte_offset(slot)


def _global_tile_view(buffer, name):
  """View any buffer as a flat global array of tiles."""
  return Buffer(
    name, buffer.addr, buffer.dtype, (buffer.physical_tiles, 1024), 0,
    (buffer.cores[0],), buffer.banks, global_address=True,
    tilized=buffer.tilized, dram_endpoints=buffer.dram_endpoints,
  )
