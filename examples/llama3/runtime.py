"""Llama 3 decode runtime: DRAM layout, weight upload, and the per-token launch list.

Reading order:
  1. Llama3Decode._allocate         every DRAM buffer (weights, KV cache, activations)
  2. Llama3Decode._stage_weights    checkpoint tensor -> DRAM buffer
  3. Llama3Decode._create_programs  one device program per kernel, built once for layer 0
  4. Llama3Decode._queue_layer      the transformer layer: which program runs on which buffers
  5. Llama3Decode.decode            replay the captured trace for one token

Programs are compiled once against layer 0's buffers. Each launch rebinds the
weight and cache parameters to the current layer, so 16 (1B) or 32 (8B)
layers share the same five kernels.
"""

from dataclasses import dataclass, fields, replace
import math
import struct
import time

import numpy as np

from device import TensorDevice as Device
from pcie import P100_WORKER_CORES, TLBWindow
from program import Buffer, DType
from ttko.sfpu import LReg

from examples.llama3 import kernels
from examples.llama3.config import Llama3Config


@dataclass(frozen=True, eq=False)
class PagedProjectionWeight(Buffer):
  """FP8 only: raw projection storage with multiple logical tiles per DRAM page.

  Tensor row ownership remains in logical 1024-element tiles; only the
  physical upload and projection reader use the larger pages.
  """
  page_tiles: int = 2

  def __post_init__(self):
    super().__post_init__()
    if (self.dtype is not DType.FP8 or not self._raw_global or
        self.page_tiles not in (1, 2, 4) or self.tiles_per_item % self.page_tiles or
        (self.page_tiles != 1 and self.banks != 8)):
      raise ValueError("paged weights require whole aligned FP8 projection rows")

  @property
  def tile_size(self): return super().tile_size * self.page_tiles

  @property
  def physical_tiles(self): return super().physical_tiles // self.page_tiles

  @classmethod
  def from_buffer(cls, buffer, page_tiles):
    if page_tiles not in (1, 2, 4): raise ValueError("page tiles must be 1, 2, or 4")
    original_extent = math.ceil(buffer.physical_tiles / buffer.banks) * buffer.tile_size
    new_extent = math.ceil(buffer.tiles / (page_tiles * buffer.banks)) * buffer.dtype.itemsize * 1024 * page_tiles
    if new_extent > original_extent:
      raise ValueError("larger pages exceed the allocated per-bank storage")
    return cls(**{field.name: getattr(buffer, field.name) for field in fields(Buffer)}, page_tiles=page_tiles)


# Per-layer checkpoint tensors, in DRAM allocation order.
LAYER_NORMS = {
  "input_norm": "input_layernorm.weight",
  "post_norm": "post_attention_layernorm.weight",
}
LAYER_PROJECTIONS = {               # name: (checkpoint tensor, (rows, columns) as config fields)
  "q": ("self_attn.q_proj.weight", ("q_dim", "embed_dim")),
  "k": ("self_attn.k_proj.weight", ("kv_dim", "embed_dim")),
  "v": ("self_attn.v_proj.weight", ("kv_dim", "embed_dim")),
  "o": ("self_attn.o_proj.weight", ("embed_dim", "q_dim")),
  "gate": ("mlp.gate_proj.weight", ("mlp_dim", "embed_dim")),
  "up": ("mlp.up_proj.weight", ("mlp_dim", "embed_dim")),
  "down": ("mlp.down_proj.weight", ("embed_dim", "mlp_dim")),
}


class Llama3Decode:
  """Resident-weight, batch-1 decode runtime for one Llama3Config."""

  def __init__(self, cfg: Llama3Config, device_index=0, *, safetensor_path=None):
    self.cfg = cfg
    safetensor_path = cfg.checkpoint if safetensor_path is None else safetensor_path
    from st import Safetensor
    checkpoint = self._checkpoint = Safetensor(safetensor_path)
    # FP8: the published checkpoint stores one input and one weight scale per projection.
    self.published_fp8 = checkpoint is not None and "model.layers.0.self_attn.q_proj.input_scale" in checkpoint.tensors
    if cfg.weight_dtype.is_fp8 and not self.published_fp8:
      raise ValueError("FP8 mode requires an FP8 checkpoint with stored scales")
    self.checkpoint_scales = {}
    if self.published_fp8:
      if cfg.weight_dtype is not DType.FP8: raise ValueError("published FP8 checkpoint requires FP8 weights")
      for name in checkpoint.tensors:
        if name.endswith((".input_scale", ".weight_scale")):
          self.checkpoint_scales[name] = float(np.frombuffer(checkpoint.load(name)[1], dtype="<f4")[0])
    self.safetensor_path = str(safetensor_path)
    self.host_result_read_us = 0.0
    self.host_result_reads = 0
    self.profile = {
      "dram_upload_bytes": 0,
      "weight_prepare_s": 0.0,
      "weight_stage_s": 0.0,
      "upload_wait_s": 0.0,
      "upload_submit_s": 0.0,
    }
    total_started = time.perf_counter()
    started = time.perf_counter()
    self.device = Device(device_index, **({"sysmem_size": 2 << 30} if cfg.model == "8b" else {}))
    self.device.init_device()
    self.profile["device_init_s"] = time.perf_counter() - started
    try:
      started = time.perf_counter()
      self._allocate()
      self.profile["allocate_s"] = time.perf_counter() - started
      started = time.perf_counter()
      self._upload_weights()
      self.profile["weight_upload_total_s"] = time.perf_counter() - started
      started = time.perf_counter()
      self._build_programs()
      self.profile["program_build_s"] = time.perf_counter() - started
      self.profile["startup_total_s"] = time.perf_counter() - total_started
    except Exception:
      self.close()
      raise

  # 1. DRAM layout

  def _allocate(self):
    cfg, device = self.cfg, self.device
    available = device.dram.cores
    if cfg.projection_cores > len(available): raise ValueError("not enough projection workers")
    # Spread projection traffic across both sides of the chip at lower counts.
    cores = tuple(available[index] for index in np.linspace(0, len(available) - 1, cfg.projection_cores, dtype=int))

    def global_buffer(name, dtype, shape, axis=0, tilized=True):
      """One linear tile namespace, interleaved across all DRAM banks."""
      return device.dram.buffer(name, dtype, shape, axis=axis, global_address=True, tilized=tilized)

    def compact_buffer(name, features):
      """Projection output: each projection core owns one tile holding its rows."""
      return device.dram.buffer(name, DType.BF16, (cfg.projection_cores, math.ceil(features / cfg.projection_cores)),
                                axis=0, cores=cores)

    self._weight_upload_buffers = {}
    def weight_buffer(name, dtype, shape):
      """Checkpoint bytes stored row-major; each projection core owns a range of rows."""
      storage = global_buffer(name + "_storage", dtype, shape, 0, tilized=False)
      if dtype.is_fp8 and storage.banks == 8:
        storage = PagedProjectionWeight.from_buffer(storage, math.gcd(cfg.fp8_page_tiles, storage.tiles_per_item))
      view = replace(storage, name=name, cores=cores)
      self._weight_upload_buffers[view] = storage
      return view

    # Token IDs (prompt + generated) and the embedding table.
    self.token_history = global_buffer("e2e_token_history", DType.U32, (cfg.max_tokens,), None, tilized=False)
    self.embedding_weight = global_buffer("e2e_embedding_weight", DType.BF16, (cfg.vocab_size, cfg.embed_dim), tilized=False)

    # LM head. 1B ties it to the embedding table; 8B stores its own projection.
    # The LM head stays BF16 in FP8 mode: the checkpoint stores it in BF16.
    self.lm_storage = lm_storage = self.embedding_weight if cfg.model == "1b" else global_buffer(
      "e2e_lm_storage", DType.BF16, (cfg.vocab_size, cfg.embed_dim), tilized=False)
    self.lm_weight = Buffer(
      "e2e_lm_weight", lm_storage.addr, lm_storage.dtype, lm_storage.shape,
      0, cores, lm_storage.banks, global_address=True,
      tilized=False, dram_endpoints=lm_storage.dram_endpoints,
    )

    # RoPE tables, one row of head_dim values per position.
    self.cos = global_buffer("e2e_rope_cos", DType.BF16, (cfg.max_tokens, cfg.head_dim), None, tilized=False)
    self.sin = global_buffer("e2e_rope_sin", DType.BF16, (cfg.max_tokens, cfg.head_dim), None, tilized=False)

    # Activations for the one token in flight. The residual stream ping-pongs
    # between x_a and x_b: attention reads x_a and writes x_b, the MLP reads
    # x_b and writes x_a.
    self.x_a = global_buffer("e2e_x_a", DType.BF16, (1, cfg.embed_dim), tilized=False)
    self.x_b = global_buffer("e2e_x_b", DType.BF16, (1, cfg.embed_dim), tilized=False)
    self.normalized = global_buffer("e2e_normalized", DType.BF16, (1, cfg.embed_dim), tilized=False)
    self.q_compact = compact_buffer("e2e_q_compact", cfg.q_dim)
    self.k_compact = compact_buffer("e2e_k_compact", cfg.kv_dim)
    self.v_compact = compact_buffer("e2e_v_compact", cfg.kv_dim)
    self.q_heads = global_buffer("e2e_q_heads", DType.BF16, (cfg.q_heads, cfg.head_dim))
    self.k_heads = global_buffer("e2e_k_heads", DType.BF16, (cfg.kv_heads, cfg.head_dim))
    self.v_heads = global_buffer("e2e_v_heads", DType.BF16, (cfg.kv_heads, cfg.head_dim))
    self.context = global_buffer("e2e_context", DType.BF16, cfg.context_shape, tilized=False)
    self.gate = compact_buffer("e2e_gate", cfg.mlp_dim)
    self.up = compact_buffer("e2e_up", cfg.mlp_dim)
    self.hidden = compact_buffer("e2e_hidden", cfg.mlp_dim)
    self.hidden_dense = global_buffer("e2e_hidden_dense", DType.BF16, (1, cfg.mlp_dim), tilized=False)
    self.logits = device.dram.buffer("e2e_logits", DType.BF16, (cfg.projection_cores, self.lm_weight.items_per_core),
                                     axis=0, cores=cores)
    # 8B split attention: FP32 (O, m, l) state from each of 32 workers.
    self.attention_partials = device.dram.buffer(
      "e2e_attention_partials", DType.F32, (32, cfg.head_tiles + 2, 1024),
      axis=0, cores=P100_WORKER_CORES[:32],
    ) if cfg.split_attention else None

    # Per-layer weights and KV cache.
    self.layers = []
    for layer in range(cfg.layers):
      prefix = f"e2e_l{layer}"
      weights = {name: global_buffer(f"{prefix}_{name}", DType.BF16, (cfg.embed_dim,), None, tilized=False)
                 for name in LAYER_NORMS}
      for name, (_, (rows, columns)) in LAYER_PROJECTIONS.items():
        weights[name] = weight_buffer(f"{prefix}_{name}", cfg.weight_dtype, (getattr(cfg, rows), getattr(cfg, columns)))
      self.layers.append({
        "weights": weights,
        "key_cache": global_buffer(f"{prefix}_key_cache", DType.BF16, cfg.kv_cache_shape),
        "value_cache": global_buffer(f"{prefix}_value_cache", DType.BF16, cfg.kv_cache_shape),
      })
    self.final_norm = global_buffer("e2e_final_norm", DType.BF16, (cfg.embed_dim,), None, tilized=False)

  # 2. Weight upload

  def _stage_weights(self):
    cfg = self.cfg
    self._upload(self.embedding_weight, "model.embed_tokens.weight")

    if self.lm_storage is not self.embedding_weight:
      self._upload(self.lm_storage, "lm_head.weight")

    started = time.perf_counter()
    cos_values, sin_values = rope_table(cfg)
    cos_data = _bf16_rne_bytes(cos_values)
    sin_data = _bf16_rne_bytes(sin_values)
    self.profile["weight_prepare_s"] += time.perf_counter() - started
    self._stage_upload(self.cos, cos_data)
    self._stage_upload(self.sin, sin_data)
    del cos_values, sin_values

    cache_zeros = bytes(math.prod(cfg.kv_cache_shape) * DType.BF16.itemsize)
    for index, layer in enumerate(self.layers):
      weights = layer["weights"]
      prefix = f"model.layers.{index}"
      for name, tensor in LAYER_NORMS.items():
        self._upload(weights[name], f"{prefix}.{tensor}")
      for name, (tensor, _) in LAYER_PROJECTIONS.items():
        self._upload(weights[name], f"{prefix}.{tensor}")
      # A cleared cache has identical bytes in every layout.
      self._stage_upload(layer["key_cache"], cache_zeros, physical=True)
      self._stage_upload(layer["value_cache"], cache_zeros, physical=True)
    self._upload(self.final_norm, "model.norm.weight")

  def _upload_weights(self):
    with self.device.upload_stream() as uploads:
      self._uploads = uploads
      try:
        self._stage_weights()
      finally:
        del self._uploads
    self.profile["weight_stage_s"] = uploads.copy_s
    self.profile["upload_wait_s"] = uploads.wait_s
    self.profile["upload_submit_s"] = uploads.submit_s

  def _upload(self, buffer, tensor):
    buffer = self._weight_upload_buffers.get(buffer, buffer)
    started = time.perf_counter()
    buffer.check_safetensor(self._checkpoint.info(tensor))
    if not buffer._raw_global:
      raise ValueError("model uploads require exact global row-major storage")
    self.profile["weight_prepare_s"] += time.perf_counter() - started
    self._uploads.write_from(
      buffer, lambda target, offset: self._checkpoint.readinto(tensor, target, offset),
    )
    self.profile["dram_upload_bytes"] += buffer.size

  def _stage_upload(self, buffer, data, *, physical=False):
    if not physical and not buffer._raw_global:
      raise ValueError("model uploads require exact global row-major storage")
    if len(data) != buffer.size:
      raise ValueError("model upload byte length does not match its storage")
    self._uploads.write(buffer, data)
    self.profile["dram_upload_bytes"] += buffer.size

  # 3. Programs: one per kernel, compiled once against layer 0's buffers

  def _build_programs(self):
    self._create_programs()
    self.device.cache_kernels(self.programs.values())
    self._capture_decode_trace()

  def _create_programs(self):
    cfg = self.cfg
    weights = self.layers[0]["weights"]
    # The O projection is compiled with Q's weight as a placeholder; _queue_layer
    # binds the real o_proj weight at launch.
    o_projection = kernels.projection(
      cfg, self.context, ((weights["q"], self.q_compact),),
      residual=self.x_a, dense_output=self.x_b,
    )
    self.programs = {
      # x_a = embedding[token]
      "embedding": kernels.embedding(cfg, self.token_history, self.embedding_weight, self.x_a),
      # x_b = x_a + o_proj(context)
      "o": o_projection,
      # q, k, v = rmsnorm(x_a) @ Wq, Wk, Wv
      "qkv": kernels.projection(
        cfg, self.x_a, ((weights["q"], self.q_compact),
                        (weights["k"], self.k_compact),
                        (weights["v"], self.v_compact)),
        norm_weight=weights["input_norm"],
      ),
      # context = attention(rope(q), rope(k) -> cache, v -> cache)
      "attention": kernels.attention(
        cfg, self.q_heads, self.layers[0]["key_cache"],
        self.layers[0]["value_cache"], self.context,
        rope_inputs=(self.q_compact, self.k_compact, self.v_compact, self.cos, self.sin),
      ),
      # hidden = silu(rmsnorm(x_b) @ Wgate) * (rmsnorm(x_b) @ Wup)
      "gate": kernels.projection(cfg, self.x_b, (
        (weights["gate"], self.gate), (weights["up"], self.up),
      ), swiglu_output=self.hidden_dense, norm_weight=weights["post_norm"]),
      # x_a = x_b + hidden @ Wdown
      # Down keeps the spatial NoC split. With an even split it matches or
      # beats rotated NoC0 ports for this projection (p150a, 8B BF16 254 vs
      # 262 us, 8B FP8 142 vs 141 us, 1B 80 vs 83 us); every other projection
      # is faster rotated. See config.noc_split_x for why the split must be even.
      "down": kernels.projection(
        cfg, self.hidden_dense, ((weights["down"], self.q_compact),),
        residual=self.x_b, dense_output=self.x_a, rotate_ports=False,
      ),
      # logits = rmsnorm(x_a) @ Wlm
      "lm": kernels.projection(
        cfg, self.x_a, ((self.lm_weight, self.logits),), norm_weight=self.final_norm,
      ),
      # next token = argmax(logits), appended to token_history
      "argmax": kernels.argmax(
        cfg, self.logits, self.token_history,
        self.device.cq.noc + self.device.cq.live,
      ),
    }
    if self.attention_partials is not None:
      # 8B split attention: four workers per KV head, then a merge.
      self.programs["attention_split"] = kernels.attention(
        cfg, self.q_heads, self.layers[0]["key_cache"], self.layers[0]["value_cache"], self.context,
        rope_inputs=(self.q_compact, self.k_compact, self.v_compact, self.cos, self.sin),
        partial_output=self.attention_partials,
      )
      self.programs["attention_merge"] = kernels.attention_merge(cfg, self.attention_partials, self.context)
    # The O projection reads the attention context through its own token view.
    self.o_projection_input = o_projection.param(f"{self.context.name}_decode_token")
    self.context_projection_input = Buffer(
      "e2e_context_decode_token", self.context.addr, self.context.dtype,
      (cfg.embed_dim,), None, (self.context.cores[0],), self.context.banks,
      global_address=True, tilized=self.context.tilized,
      dram_endpoints=self.context.dram_endpoints,
    )

  # 4. One transformer layer

  def _queue_layer(self, index, position, *, split_attention=False):
    """Queue the five launches of one layer, bound to that layer's weights and cache."""
    layer = self.layers[index]
    weights = layer["weights"]
    template = self.layers[0]
    template_weights = template["weights"]
    blocks = position // self.cfg.kv_block + 1
    tail = position % self.cfg.kv_block + 1

    self._queue("qkv", (
      (template_weights["input_norm"], weights["input_norm"]),
      (template_weights["q"], weights["q"]),
      (template_weights["k"], weights["k"]),
      (template_weights["v"], weights["v"]),
    ), self._projection_scales(index, ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj")))
    self._queue("attention_split" if split_attention else "attention", (
      (template["key_cache"], layer["key_cache"]),
      (template["value_cache"], layer["value_cache"]),
    ), {"start_pos": position, "kv_blocks": blocks, "valid_columns": tail})
    if split_attention: self._queue("attention_merge")
    self._queue("o", (
      (self.o_projection_input, self.context_projection_input),
      (template_weights["q"], weights["o"]),
    ), self._projection_scales(index, ("self_attn.o_proj",)))
    self._queue("gate", (
      (template_weights["post_norm"], weights["post_norm"]),
      (template_weights["gate"], weights["gate"]),
      (template_weights["up"], weights["up"]),
    ), self._projection_scales(index, ("mlp.gate_proj", "mlp.up_proj")))
    self._queue("down", ((template_weights["down"], weights["down"]),), self._projection_scales(index, ("mlp.down_proj",)))

  def _queue(self, name, replacements=(), constants=None):
    params = {source: target for source, target in replacements}
    if constants: params.update(constants)
    self.device.queue(self.programs[name], params=params)

  def _projection_scales(self, layer, names):
    """FP8: per-layer scale parameters for a fused projection launch (BF16: none)."""
    if not self.published_fp8: return {}
    prefixes = [f"model.layers.{layer}.{name}" for name in names]
    inputs = [self.checkpoint_scales[f"{name}.input_scale"] for name in prefixes]
    if any(value != inputs[0] for value in inputs):
      raise ValueError("fused projections require identical calibrated input scales")
    values = {"input_scale": 1 / inputs[0]}
    values.update({f"output_scale_{i}": inputs[0] * self.checkpoint_scales[f"{name}.weight_scale"] for i, name in enumerate(prefixes)})
    return {f"{name}_{part}": word for name, value in values.items() for part, word in enumerate(kernels._sfpu_float_words(LReg.L6, value))}

  # 5. One token: replay embedding -> layers -> LM head -> argmax

  def _capture_decode_trace(self):
    for split in range(2 if self.attention_partials is not None else 1):
      self._queue("embedding")
      for layer in range(self.cfg.layers):
        self._queue_layer(layer, 0, split_attention=bool(split))
      self._queue("lm")
      self._queue("argmax")
      launch_count = len(self.device.program_queue)
      trace = self.device.capture_trace((
        "token_pos", "write_pos", "write_token", "start_pos", "kv_blocks", "valid_columns",
      ))
      if split:
        self.split_decode_trace, self.split_decode_launch_count = trace, launch_count
      else:
        self.decode_trace = self.short_decode_trace = trace
        self.decode_launch_count = self.short_decode_launch_count = launch_count

  def decode(self, position, *, logits=True, append=True):
    """Consume one token at ``position`` and optionally return greedy next ID."""
    cfg = self.cfg
    if not 0 <= position < cfg.max_tokens - 1:
      raise ValueError(f"decode position must be in 0..{cfg.max_tokens - 2}")
    started = time.perf_counter_ns()
    use_split = self.attention_partials is not None and position >= cfg.split_attention_from
    self.decode_trace = self.split_decode_trace if use_split else self.short_decode_trace
    self.decode_launch_count = self.split_decode_launch_count if use_split else self.short_decode_launch_count
    self.decode_trace.replay({
      "token_pos": position,
      "write_pos": position + 1,
      "write_token": int(append),
      "start_pos": position,
      "kv_blocks": position // cfg.kv_block + 1,
      "valid_columns": position % cfg.kv_block + 1,
    }, timeout=30.0)
    wall_us = (time.perf_counter_ns() - started) / 1e3

    if not logits: return None, wall_us
    return self._read_token(position + 1), wall_us

  def _read_token(self, write_position):
    read_started = time.perf_counter_ns()
    live = self.device.cq.live + write_position * 16
    token, = struct.unpack("<I", self.device.pcie.sysmem.read(live, 4))
    self.host_result_read_us += (time.perf_counter_ns() - read_started) / 1e3
    self.host_result_reads += 1
    return token

  def load_tokens(self, tokens, *, start=0):
    """Update token history from start, preserving the cached prefix in DRAM."""
    cfg = self.cfg
    tokens = np.asarray(tokens)
    if tokens.ndim != 1 or tokens.dtype.kind not in "iu":
      raise ValueError("prompt tokens must be a one-dimensional integer sequence")
    if not 0 < len(tokens) < cfg.max_tokens:
      raise ValueError(f"prompt token count must be in 1..{cfg.max_tokens - 1}")
    if np.any(tokens < 0) or np.any(tokens >= cfg.vocab_size):
      raise ValueError(f"prompt tokens must be in 0..{cfg.vocab_size - 1}")
    if not 0 <= start < len(tokens): raise ValueError("start must index a prompt token")
    self.device.run(timeout=30.0)
    history = self.token_history
    data = tokens[start:].astype("<u4", copy=False).tobytes()
    # Token IDs are flat uint32 values in bank-interleaved 4 KiB pages.
    with TLBWindow(self.device.pcie.fd, self.device.pcie.dram_endpoints[0][0]) as window:
      for page in range(start // 1024, (len(tokens) + 1023) // 1024):
        address = history.addr + page // history.banks * history.tile_size
        base = address & -TLBWindow.SIZE
        window.target(base, self.device.pcie.dram_endpoints[page % history.banks][0])
        position, end = max(start, page * 1024), min(len(tokens), (page + 1) * 1024)
        offset = (position % 1024) * 4
        window.write(address - base + offset, data[(position - start) * 4:(end - start) * 4])

  def close(self):
    if getattr(self, "device", None) is not None:
      self.device.close()
      self.device = None


# Host-side tables

def rope_table(cfg, max_seq_len=None, head_dim=None, rope_factor=None):
  """Build Llama 3 cosine and sine tables on the host in FP32.

  The returned ``[position, head_dim]`` arrays duplicate the half-width
  angles exactly as Llama's split-half ``rotate_half`` convention expects.
  They are quantized only when copied into the resident BF16 DRAM buffers.
  """
  max_seq_len = cfg.max_tokens if max_seq_len is None else max_seq_len
  head_dim = cfg.head_dim if head_dim is None else head_dim
  rope_factor = cfg.rope_factor if rope_factor is None else rope_factor
  low, high = cfg.rope_low_freq_factor, cfg.rope_high_freq_factor
  dimensions = np.divide(np.arange(0, head_dim, 2, dtype=np.float32), np.float32(head_dim), dtype=np.float32)
  inv_freq = np.reciprocal(np.power(np.float32(cfg.rope_theta), dimensions, dtype=np.float32), dtype=np.float32)
  # Llama 3 frequency scaling: long wavelengths are divided by rope_factor,
  # short ones kept, and the band between is interpolated smoothly.
  wavelen = np.divide(np.float32(2.0 * math.pi), inv_freq, dtype=np.float32)
  cycles = np.divide(np.float32(cfg.rope_original_max_position_embeddings), wavelen, dtype=np.float32)
  smooth = np.clip(
    np.divide(cycles - np.float32(low), np.float32(high - low), dtype=np.float32),
    np.float32(0.0), np.float32(1.0),
  )
  inverse_factor = np.float32(1.0 / rope_factor)
  inv_freq = np.multiply(inv_freq, inverse_factor + smooth * (np.float32(1.0) - inverse_factor), dtype=np.float32)
  angles = np.multiply(np.arange(max_seq_len, dtype=np.float32)[:, None], inv_freq[None, :], dtype=np.float32)
  angles = np.tile(angles, (1, 2))
  return (
    np.ascontiguousarray(np.cos(angles), dtype=np.float32),
    np.ascontiguousarray(np.sin(angles), dtype=np.float32),
  )


def _bf16_rne_bytes(values):
  """Cast finite FP32 values to BF16 with round-to-nearest-even."""
  words = np.ascontiguousarray(values, dtype="<f4").view(np.uint32)
  rounded = words + np.uint32(0x7fff) + ((words >> 16) & np.uint32(1))
  return (rounded >> 16).astype("<u2").tobytes()
