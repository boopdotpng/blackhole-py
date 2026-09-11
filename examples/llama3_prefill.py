"""Chunked BS=1 BF16 prefill sharing Llama3Decode's weights and KV cache.

The Q/K/V and gate/up kernels load each weight row once per prompt chunk.
Attention remains the validated causal, streaming GQA implementation. Scratch
is bounded by chunk size; the sequence dimension is not a request batch.
"""
from dataclasses import replace
from copy import copy
import math
import time

from examples import llama3_8b as d
from ttko.program import Buffer, Const, DType, Program
from fw.consts import KERNEL_ROLES, TensixL1
from ttko.isa import R, RV32
from ttko.cb import CB
from ttko.shard import specialize
from ttko.sync import Sem, SemWait, Stall, sem_wait
from ttko.unpack import UnpackTarget


class SequenceBuffer:
  """Bank-aligned token slabs with byte-identical decode buffer views."""
  def __init__(self, device, prototype, capacity):
    self.prototype = prototype
    self.stride = math.ceil(prototype.physical_tiles / prototype.banks) * prototype.banks
    self.storage = device.dram.buffer(
      "prefill_" + prototype.name, prototype.dtype,
      (capacity, self.stride * 1024), axis=0, global_address=True,
      tilized=False,
    )
    self.capacity = capacity

  def view(self, index, prototype=None):
    if not 0 <= index < self.capacity: raise ValueError("token outside scratch capacity")
    prototype = self.prototype if prototype is None else prototype
    return replace(prototype, addr=self.storage.addr +
                   index * self.stride // prototype.banks * prototype.tile_size)


def prefill_projection(x, weight, output, count):
  """Compute count independent BF16 matrix-vector products, reusing weights.

  x contains bank-aligned, row-major token slabs; output contains the existing
  per-worker compact fragments in token slabs. Dot products accumulate FP32
  and round to BF16 exactly where decode rounds its projection output.
  """
  return prefill_projections(x, ((weight, output),), count)


def prefill_projections(x, projections, count, norm_weight=None):
  """Grouped QKV or gate/up with one local RMSNorm per token and worker."""
  projections = tuple(projections)
  if not 1 <= len(projections) <= 3:
    raise ValueError("prefill supports one to three grouped projections")
  if type(count) is not int or not 1 <= count <= x.capacity:
    raise ValueError("invalid prefill token count")
  weights = tuple(weight for weight, _ in projections)
  for weight, output in projections:
    if (weight.dtype is not DType.BF16 or not weight.global_address or weight.tilized or
        x.prototype.dtype is not DType.BF16 or x.prototype.tilized):
      raise ValueError("prefill requires global row-major BF16 weights and inputs")
    if weight.shape[1] != x.prototype.shape[-1] or weight.shape[1] % 1024:
      raise ValueError("projection input dimension must match complete BF16 pages")
    if (weight.cores != weights[0].cores or output.prototype.cores != weight.cores or
        output.prototype.dtype is not DType.BF16 or not output.prototype.tilized or
        output.prototype.tiles_per_core != 1 or weight.items_per_core > 1024 or
        count > output.capacity):
      raise ValueError("invalid prefill projection output layout or capacity")
  if norm_weight is not None and (norm_weight.shape != (d.EMBED_DIM,) or
      norm_weight.dtype is not DType.BF16 or norm_weight.tilized):
    raise ValueError("prefill RMSNorm requires a row-major BF16 scale vector")
  keys = tuple((tuple(weight.item_counts[i] for weight in weights),
                int(core[0] >= d.PROJECTION_NOC_SPLIT_X),
                tuple((weight.item_starts[i] * weight.tiles_per_item) % weight.banks
                      if weight.banks == 8 else None for weight in weights))
               for i, core in enumerate(weights[0].cores))
  return specialize(lambda key: _projection_program(x, projections, count, norm_weight, *key),
                    weights[0].cores, keys)


def _projection_program(x, projections, count, norm_weight, rows, read_noc, rotations):
  input_tiles = projections[0][0].shape[1] // 1024
  row_starts = tuple(Const(weight.name + "_prefill_row_start", weight.item_starts)
                     for weight, _ in projections)
  out_tile = Const("prefill_output_tile", tuple(range(len(projections[0][0].cores))))
  params = tuple(param for (weight, output), start in zip(projections, row_starts)
                 for param in (weight, output.storage, start))
  p = Program(projections[0][0].cores, x.storage, *params, out_tile,
              *((norm_weight,) if norm_weight is not None else ()), fp32_dst=True)
  inputs = p.cb(DType.BF16, depth=count * input_tiles)
  weights = p.cb(DType.BF16, depth=2 * input_tiles)
  scalar = p.cb(DType.BF16, depth=2)
  compact = p.l1(count * 2048, alignment=16)
  # Hold normalized input rows in L1 while streaming the entire weight group.
  operands = p.cb(DType.BF16, depth=2 * input_tiles) if norm_weight is not None else inputs
  for token in p.brisc.range(count):
    for tile in range(input_tiles):
      with p.brisc.scope():
        index, stride = p.brisc.reg(2, exclude=token)
        p.brisc.li(stride, x.stride)
        p.brisc.mul(index, token, stride)
        if tile: p.brisc.addi(index, index, tile)
        p.brisc.noc_at(read_noc).read_into_cb(x.storage, index, operands)
    if norm_weight is not None:
      p.brisc.noc_at(read_noc).read_tiles_into_cb(norm_weight, tuple(range(input_tiles)), operands)
  if norm_weight is not None:
    if input_tiles != d.EMBEDDING_TILES: raise ValueError("fused RMSNorm requires 4096 features")
    for _ in p.trisc0.range(count):
      for _ in range(2 * input_tiles): p.unpack.move(operands, UnpackTarget.SRCA)
    d._rms_setup_apply_macro(p.sfpu)
    for _ in p.trisc1.range(count):
      p.fpu.copy_a_tiles(dst_tiles=range(2 * input_tiles))
      d._rmsnorm_one_token(p.sfpu)
    for _ in p.trisc2.range(count):
      p.pack.move_tiles(inputs, tiles=tuple(range(input_tiles)))
  expanded = tuple((weight, output.prototype, size)
                   for (weight, output), size in zip(projections, rows))
  d._projection_read_weights(p, expanded, row_starts, rotations, read_noc, weights, input_tiles)
  CB.wait_front(p.trisc0, inputs, count * input_tiles)
  p.unpack.prepare_l1_pair_formats(DType.BF16)
  for _ in p.trisc0.range(sum(rows)):
    CB.wait_front(p.trisc0, weights, input_tiles)
    for token in p.trisc0.range(count):
      for tile in range(input_tiles):
        with p.trisc0.scope():
          address, stride = p.trisc0.reg(2, exclude=token)
          p.trisc0.li(stride, input_tiles * 2048)
          p.trisc0.mul(address, token, stride)
          d._add_constant(p.trisc0, address, inputs.addr + tile * 2048)
          p.unpack.move_l1_pair(weights, address,
            configure_format=False, tile_offset=tile, pop=False)
    CB.pop_front(p.trisc0, weights, input_tiles)
  d._projection_dot_math(p, ((projections[0][0], projections[0][1].prototype, sum(rows) * count),), input_tiles)
  p.pack._configure(scalar, True, True)
  for _ in p.trisc2.range(sum(rows) * count):
    sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
    p.pack._move_acquired(scalar, 0, True, configure=False)
    p.pack._release_dst()
  for (_, output), size in zip(projections, rows):
    d._zero_l1_words(p.ncrisc, compact, count * 512)
    for row in p.ncrisc.range(size):
      for token in p.ncrisc.range(count):
        CB.wait_front(p.ncrisc, scalar)
        with p.ncrisc.scope():
          source, value, target, offset = p.ncrisc.reg(4, exclude=(row, token))
          CB.get_read_ptr(p.ncrisc, scalar, source)
          p.ncrisc.read(value, source, bytes=2)
          d._tile_offset(p.ncrisc, row, target)
          p.ncrisc.slli(offset, token, 11)
          p.ncrisc.add(target, target, offset)
          d._add_constant(p.ncrisc, target, compact)
          p.ncrisc.write(target, value, bytes=2)
        CB.pop_front(p.ncrisc, scalar)
    for token in p.ncrisc.range(count):
      with p.ncrisc.scope():
        tile, stride, offset, source = p.ncrisc.reg(4, exclude=token)
        p.ncrisc.read(tile, p.param_addr(out_tile))
        p.ncrisc.li(stride, output.stride)
        p.ncrisc.mul(offset, token, stride)
        p.ncrisc.add(tile, tile, offset)
        p.ncrisc.slli(source, token, 11)
        d._add_constant(p.ncrisc, source, compact)
        address, coordinate = p.ncrisc.noc_at(1-read_noc)._dram_tile(output.storage, tile)
        p.ncrisc.noc_at(1-read_noc).write(source, address, coordinate, 2048, posted=False)
  return p


def prefill_swiglu(gate, up, output):
  """SwiGLU and compact-to-dense scatter in a single launch."""
  counts = d._token_counts(d.MLP_DIM, len(gate.cores))
  starts, start = [], 0
  for count in counts:
    starts.append(start)
    start += count
  def build(count):
    p = Program(gate.cores, gate, up, output, Const("dense_start", tuple(starts)), fp32_dst=True)
    a, b, result = (p.cb(DType.BF16, depth=1) for _ in range(3))
    p.brisc.noc.read_into_cb(gate, 0, a)
    p.brisc.noc.read_into_cb(up, 0, b)
    p.unpack.move(a, UnpackTarget.SRCA)
    p.unpack.move(b, UnpackTarget.SRCA)
    d._swiglu_math(p)
    p.pack.move(result, tile=0)
    d._scatter_dense(p, result, output, count, read_noc=1)
    return p
  return specialize(build, gate.cores, counts)


class Prefill:
  """Bounded scratch and layer-major prompt scheduling for one decode runtime."""
  def __init__(self, runtime, chunk_size=4):
    if type(chunk_size) is not int or not 1 <= chunk_size <= 8:
      raise ValueError("prefill chunk size must be in 1..8")
    self.runtime, self.chunk_size = runtime, chunk_size
    self.slabs = {getattr(runtime, name).addr: SequenceBuffer(runtime.device, getattr(runtime, name), chunk_size)
                  for name in ("x_a", "x_b", "q_compact", "k_compact", "v_compact",
                               "context", "gate", "up", "hidden_dense")}
    self.swiglu = prefill_swiglu(runtime.gate, runtime.up, runtime.hidden_dense)
    self.projections = {}
    self.profile = {}
    self._cached = False
    self.resident = {}
    for program in runtime.programs.values():
      launch = copy(program)
      launch._kernels = {
        core: {role: RV32().jal(R.ZERO, address - TensixL1.WORKER_TEXT_BASE[role]).to_bytes(4, "little")
               for role, address in zip(KERNEL_ROLES, entries)}
        for core, entries in runtime.device._resident_programs[program].items()
      }
      self.resident[program] = launch

  def _projection(self, name, count):
    key = name, count
    if key not in self.projections:
      r = self.runtime
      names = ("q", "k", "v") if name == "qkv" else ("gate", "up")
      source = r.x_a if name == "qkv" else r.x_b
      norm = "input_norm" if name == "qkv" else "post_norm"
      self.projections[key] = prefill_projections(self.slabs[source.addr], tuple(
        (r.layers[0]["weights"][part], self.slabs[getattr(r, part + "_compact" if name == "qkv" else part).addr])
        for part in names), count, r.layers[0]["weights"][norm])
    return self.projections[key]

  def _cache(self):
    if self._cached: return
    r = self.runtime
    programs = [self._projection(name, count)
                for count in range(1, self.chunk_size + 1)
                for name in ("qkv", "gate_up")]
    programs += [self.swiglu, *self.resident.values()]
    # Keep decode's resident kernels/templates intact. Prefill's larger family
    # of sequence variants lives in the existing DRAM command-record cache.
    if r.device._kernel_cache_buffer is None:
      r.device.cache_programs(programs)
    self._cached = True

  def _queue(self, program, token, replacements=(), constants=None):
    program = self.resident.get(program, program)
    params = dict(replacements)
    # Apply explicit bindings first, then move activation aliases into their
    # token slab. Attention and O projection expose differently named views.
    for source in program.params.values():
      target = params.get(source, source)
      if isinstance(target, Buffer) and target.addr in self.slabs:
        params[source] = self.slabs[target.addr].view(token, target)
    if constants: params.update(constants)
    self.runtime.device.queue(program, params=params, report=False)

  def run(self, tokens, *, append=True):
    r = self.runtime
    started = time.perf_counter()
    # load_tokens validates before modifying device state.
    r.load_tokens(tokens)
    count = len(tokens)
    self._cache()
    execution_started = time.perf_counter()
    launches = 0
    template = r.layers[0]
    tw = template["weights"]
    for start in range(0, count, self.chunk_size):
      live = min(self.chunk_size, count - start)
      for token in range(live):
        self._queue(r.programs["embedding"], token, constants={"token_pos": start + token})
      for layer in r.layers:
        w = layer["weights"]
        r.device.queue(self._projection("qkv", live),
          params={tw[name]: w[name] for name in ("q", "k", "v", "input_norm")}, report=False)
        for token in range(live):
          position = start + token
          self._queue(r.programs["attention"], token,
            ((template["key_cache"], layer["key_cache"]), (template["value_cache"], layer["value_cache"])),
            {"start_pos": position, "kv_blocks": position // 32 + 1, "valid_columns": position % 32 + 1})
          self._queue(r.programs["o"], token,
            ((r.o_projection_input, r.context_projection_input), (tw["q"], w["o"])))
        r.device.queue(self._projection("gate_up", live),
          params={tw[name]: w[name] for name in ("gate", "up", "post_norm")}, report=False)
        for token in range(live):
          self._queue(self.swiglu, token)
          self._queue(r.programs["down"], token, ((tw["down"], w["down"]),))
        # Bound CQ staging and keep kernel uploads out of a giant host queue.
        launches += len(r.device.program_queue)
        r.device.run(timeout=30.0)
      if start + live == count:
        self._queue(r.programs["lm"], live - 1)
        self._queue(r.programs["argmax"], live - 1,
                    constants={"write_pos": count, "write_token": int(append)})
        launches += 2
        r.device.run(timeout=30.0)
    token = r._read_token(count)
    elapsed = (time.perf_counter() - started) * 1e6
    self.profile = {"tokens": count, "chunk_size": self.chunk_size,
                    "launches": launches, "wall_us": elapsed,
                    "execution_us": (time.perf_counter() - execution_started) * 1e6}
    return token, elapsed
