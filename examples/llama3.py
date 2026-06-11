#!/usr/bin/env python3
"""Llama 3.2 1B batch-1 decode on Blackhole (p100a) — end-to-end host driver.

Loads the .l3cu checkpoint (the llama3-cuda flat-bf16 format), uploads all
weights tilized to GDDR once, then decodes greedily one token at a time.
Prompt prefill runs on the host by default to avoid turning long chat prompts
into thousands of tiny CQ submissions before the first generated token.

What runs on DEVICE today (all validated pieces, see llama3plan.md):
  - projection GEMVs at M=1 via examples/matmul_peak (skinny-GEMV regime):
    fused Wq/Wk/Wv, then Wo, Wgate/Wup, Wdown per layer + tied logits head.
    This is ~99.7% of the bytes moved per token (decode is memory-bound).
  - QKV's V slice is also scattered into a per-layer device V cache from the
    GEMV output-writer tail.
  - QKV's K slice is staged from the QKV output buffer into the RoPE footprint,
    then RoPE-rotated and scattered into a per-layer device K cache in one
    composite program.
  - Wo/Wdown projection residual adds run as separate device eltwise ADD
    programs after their GEMVs. In the device-attention path the next activation
    stays in row-tiled device buffers; fallback paths may still read it back.
  - RMSNorm feeding QKV, Wgate/Wup, and logits runs as staged device programs:
    inv_rms reduction, norm-weight scaling, activation scaling, then GEMV.
  - The decode token id is gathered from a row-major device embedding table into
    layer-0 QKV's staged RMSNorm/GEMV input buffers; QKV no longer consumes a
    host-materialized embedding vector.
  - SwiGLU runs as a staged device bridge after Wgate/Wup and writes Wdown's
    row-tiled input buffer directly.
  - Decode attention runs as a staged device chain over all Q heads and writes
    the assembled context directly into Wo's GEMV input buffer. For positions
    0..31, each GQA group uses the compact block-local score/softmax/weighted-V
    chain. For later positions, device attention switches to a conservative
    full-history chain over all live 32-token tiles: per-tile scores, global
    softmax stats/probabilities, per-tile weighted-V, device ADD accumulation,
    then a copy into Wo's input buffer.
  - Later layer QKV RMSNorms consume the previous layer's Wdown result directly
    from device memory; Wgate consumes Wo's post-residual result; tied logits
    consumes the final Wdown result. These are intentionally separate programs
    with resident activation handoffs.

What is still HOST-side numpy:
  - device-attention keeps per-layer decode activations device-resident, but
    fallback paths still keep numpy activation mirrors for host attention and
    residual paths.
  - host prefill is still the default; its KV cache is copied to the device
    before decode so staged device attention can consume it.
  - full-model long-run stability for the full-history attention path still
    needs longer soaks past the first tile.
  - argmax: host only for now.

Each host fallback is tagged TODO(device) at its definition.

Usage:
  python examples/llama3.py --tokens 128000,791,6864,315,9822,374 --steps 16
  python examples/llama3.py --prompt "The capital of France is" --steps 16   # needs transformers
  python examples/llama3.py --host --steps 4          # pure-numpy golden, no device
  python examples/llama3.py --check --steps 4         # device vs host logits PCC per token
  python examples/llama3.py --device-prefill --steps 4 # CQ stress/debug path
  python examples/llama3.py --device-attention --steps 40
  python examples/llama3.py --device-attention --allow-block-local-attention --steps 40 # debug: block-local past pos31
  python examples/llama3.py --fast --steps 260 --max-seq 512 --ignore-eos  # ~11 tok/s, 260-token soak

Fast path (--fast): host does all small math (RMSNorm, RoPE, KV cache,
attention, SwiGLU, residuals, argmax); the device runs only the 4 projection
GEMVs/layer (QKV, Wo, fused Gate+Up, Wdown) + tied logits. Each projection is
ONE pre-encoded CQ submission: fill x from pinned sysmem -> GEMV -> drain out
row, replayed per token (65 submissions, 198 launches/token, ~11 tok/s at
pcc 0.9996). The rare Tensix relaunch wedge is auto-recovered by a full CQ
reset + bundle replay (~0.7s, weights stay resident).
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "microbenching" / "matmul"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "microbenching" / "noc"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "microbenching" / "tensix"))

import matmul_peak as mm
import microbench_rmsnorm_gemv as normbridge
import microbench_qkv_kstage_rope_scatter as kstage
import microbench_swiglu_bridge as swiglu_bridge
import microbench_embedding_gather_tilized as embed_gather
from microbench_qkv_vscatter_gemv import make_vscatter_hook
from microbench_residual_gemv import build_two_source_binary
from matmul_peak import TILE, TensorLayout, from_bf16_device_bytes, to_bf16_device_bytes
from program import Dtype

DEFAULT_MODEL = Path(__file__).resolve().parents[1] / "llama3-cuda/models/llama3.2-1b-instruct-bf16.l3cu"
DEFAULT_TOKENIZER = Path(__file__).resolve().parents[1] / "llama3-cuda/models/llama3.2-1b-instruct-tokenizer"
EOS_TOKENS = {128001, 128008, 128009}


# --------------------------------------------------------------------------
# Checkpoint loading (.l3cu: magic "L32CU001", header, flat bf16 tensors)
# --------------------------------------------------------------------------

HEADER_FMT = "<8s9i6fQ"


@dataclass(frozen=True)
class Config:
  dim: int
  hidden_dim: int
  n_layers: int
  n_heads: int
  n_kv_heads: int
  vocab_size: int
  max_pos: int
  head_dim: int
  norm_eps: float
  rope_theta: float
  rope_factor: float
  rope_low: float
  rope_high: float
  rope_orig_ctx: float

  @property
  def kv_dim(self) -> int:
    return self.n_kv_heads * self.head_dim


def bf16_to_f32(u16: np.ndarray) -> np.ndarray:
  return (u16.astype(np.uint32) << 16).view(np.float32)


class Model:
  """Memory-maps the checkpoint; tensors come out as fp32 views on demand."""

  def __init__(self, path: Path):
    raw = path.open("rb").read(struct.calcsize(HEADER_FMT))
    (magic, version, dim, hidden, n_layers, n_heads, n_kv, vocab, max_pos, rope_dim,
     eps, theta, factor, low, high, orig_ctx, tensor_bytes) = struct.unpack(HEADER_FMT, raw)
    assert magic == b"L32CU001", f"bad magic {magic!r}"
    assert version == 2, f"need bf16 .l3cu (version 2), got {version}"
    self.cfg = Config(dim, hidden, n_layers, n_heads, n_kv, vocab, max_pos, rope_dim,
                      eps, theta, factor, low, high, orig_ctx)
    self.data = np.memmap(path, dtype=np.uint16, mode="r", offset=struct.calcsize(HEADER_FMT))
    assert self.data.size * 2 == tensor_bytes, "tensor payload size mismatch"
    self._off = 0
    self.offsets: dict[str, tuple[int, tuple[int, int]]] = {}
    c = self.cfg
    self._reg("embed", (c.vocab_size, c.dim))
    for i in range(c.n_layers):
      self._reg(f"l{i}.attn_norm", (c.dim,))
      self._reg(f"l{i}.wq", (c.dim, c.dim))
      self._reg(f"l{i}.wk", (c.kv_dim, c.dim))
      self._reg(f"l{i}.wv", (c.kv_dim, c.dim))
      self._reg(f"l{i}.wo", (c.dim, c.dim))
      self._reg(f"l{i}.ffn_norm", (c.dim,))
      self._reg(f"l{i}.wgate", (c.hidden_dim, c.dim))
      self._reg(f"l{i}.wup", (c.hidden_dim, c.dim))
      self._reg(f"l{i}.wdown", (c.dim, c.hidden_dim))
    self._reg("final_norm", (c.dim,))
    assert self._off == self.data.size, "tensor map does not cover payload"

  def _reg(self, name: str, shape: tuple[int, ...]) -> None:
    n = int(np.prod(shape))
    self.offsets[name] = (self._off, shape)
    self._off += n

  def f32(self, name: str) -> np.ndarray:
    off, shape = self.offsets[name]
    return bf16_to_f32(np.asarray(self.data[off:off + int(np.prod(shape))])).reshape(shape)

  def embed_row(self, token: int) -> np.ndarray:
    off, (_, dim) = self.offsets["embed"]
    return bf16_to_f32(np.asarray(self.data[off + token * dim: off + (token + 1) * dim]))


# --------------------------------------------------------------------------
# Host kernels (each mirrors a llama3-cuda kernel; fp32 like the CUDA)
# --------------------------------------------------------------------------

def rope_tables(cfg: Config) -> tuple[np.ndarray, np.ndarray]:
  """HF llama3 rope scaling (model_format.cpp::make_rope_table)."""
  half = cfg.head_dim // 2
  inv = 1.0 / cfg.rope_theta ** (np.arange(half, dtype=np.float64) * 2 / cfg.head_dim)
  if cfg.rope_factor != 1.0:
    low_wl = cfg.rope_orig_ctx / cfg.rope_low
    high_wl = cfg.rope_orig_ctx / cfg.rope_high
    wl = 2 * np.pi / inv
    smooth = np.clip((cfg.rope_orig_ctx / wl - cfg.rope_low) / (cfg.rope_high - cfg.rope_low), 0, 1)
    interp = (1 - smooth) * inv / cfg.rope_factor + smooth * inv
    inv = np.where(wl > low_wl, inv / cfg.rope_factor, np.where(wl >= high_wl, interp, inv))
  ang = np.arange(cfg.max_pos)[:, None] * inv[None, :]
  return np.cos(ang).astype(np.float32), np.sin(ang).astype(np.float32)


def rmsnorm_inv(x: np.ndarray, eps: float) -> float:
  # TODO(device): SFPU sum-reduce + rsqrt (both microbenched), fp32 dest-acc.
  return float(1.0 / np.sqrt(np.mean(x.astype(np.float32) ** 2) + eps))


def normed(x: np.ndarray, w: np.ndarray, inv: float) -> np.ndarray:
  return x * w * inv  # broadcast mul — TODO(device): bcast eltwise (microbenched)


def rope_rotate(t: np.ndarray, cos: np.ndarray, sin: np.ndarray, n_h: int, hd: int) -> np.ndarray:
  # TODO(device): ttk.sfpu.rope_rotate_row_seq composite + kv scatter.
  t = t.reshape(n_h, hd)
  h = hd // 2
  x1, x2 = t[:, :h], t[:, h:]
  return np.concatenate([x1 * cos - x2 * sin, x2 * cos + x1 * sin], axis=1).reshape(-1)


def attention(q, k_cache, v_cache, pos, n_heads, n_kv, hd):
  # TODO(device): per-head dot + softmax composite; KV cache then moves on-device.
  group = n_heads // n_kv
  out = np.empty(n_heads * hd, dtype=np.float32)
  q = q.reshape(n_heads, hd)
  scale = 1.0 / np.sqrt(hd)
  for qh in range(n_heads):
    K, V = k_cache[qh // group, :pos + 1], v_cache[qh // group, :pos + 1]
    s = (K @ q[qh]) * scale
    p = np.exp(s - s.max())
    p /= p.sum()
    out[qh * hd:(qh + 1) * hd] = p @ V
  return out


def swiglu(gate: np.ndarray, up: np.ndarray) -> np.ndarray:
  # TODO(device): SFPU silu + eltwise mul (both microbenched).
  return gate / (1.0 + np.exp(-gate)) * up


def argmax(logits: np.ndarray) -> int:
  return int(np.argmax(logits))  # device argmax MISSING (plan #11); host is fine


def quant_bf16(x: np.ndarray) -> np.ndarray:
  """Round-trip through bf16 so host fallbacks match device storage dtype."""
  return from_bf16_device_bytes(to_bf16_device_bytes(x), x.shape)


def vector_to_row_tiles(vec: np.ndarray, n_padded: int) -> np.ndarray:
  tiles = np.zeros((n_padded // TILE, TILE, TILE), dtype=np.float32)
  v = np.zeros(n_padded, dtype=np.float32)
  v[:vec.size] = vec
  for tile in range(n_padded // TILE):
    tiles[tile, 0, :] = v[tile * TILE:(tile + 1) * TILE]
  return tiles


def row_tiles_to_vector(raw: bytes, tiles: int, n: int) -> np.ndarray:
  data = from_bf16_device_bytes(raw, (tiles, TILE, TILE))
  return data[:, 0, :].reshape(-1)[:n]


def run_programs(device, programs, stats: dict) -> None:
  programs = tuple(programs)
  if not programs:
    return
  for prog in programs:
    device.queue(prog)
  try:
    timings = device.run()
  except Exception:
    names = ", ".join(getattr(prog, "name", prog.__class__.__name__) for prog in programs)
    print(
        f"[run_programs] FAILED after launches={stats.get('launches', 0)} "
        f"submissions={stats.get('submissions', 0)} programs=[{names}]",
        flush=True,
    )
    raise
  us_by_name: dict[str, float] = {}
  for timing in timings:
    us_by_name[timing.get("name", "")] = us_by_name.get(timing.get("name", ""), 0.0) + timing["us"]
  stats["device_us"] += sum(t["us"] for t in timings)
  stats["launches"] += len(programs)
  stats["submissions"] = stats.get("submissions", 0) + 1
  by_name = stats.setdefault("launch_by", {})
  by_us = stats.setdefault("device_us_by", {})
  for prog in programs:
    name = getattr(prog, "name", prog.__class__.__name__)
    by_name[name] = by_name.get(name, 0) + 1
    by_us[name] = by_us.get(name, 0.0) + us_by_name.get(name, 0.0)


def run_program(device, prog, stats: dict) -> None:
  run_programs(device, (prog,), stats)


def load_tokenizer(path: Path = DEFAULT_TOKENIZER):
  from transformers import PreTrainedTokenizerFast

  tok = PreTrainedTokenizerFast(
      tokenizer_file=str(path / "tokenizer.json"),
      bos_token="<|begin_of_text|>",
      eos_token="<|eot_id|>",
      pad_token="<|finetune_right_pad_id|>",
      model_max_length=131072,
      padding_side="left",
  )
  template = path / "chat_template.jinja"
  if template.exists():
    tok.chat_template = template.read_text()
  return tok


# --------------------------------------------------------------------------
# Device GEMV: x[1,K] @ W[K,N] via matmul_peak's planner (skinny regime)
# --------------------------------------------------------------------------

class DeviceGemv:
  """Weights resident in GDDR; programs prebuilt; relaunch per token."""

  def __init__(
      self,
      device,
      name: str,
      w_out_in: np.ndarray,
      xbufs: dict,
      grid_rows: int = 1,
      output_tile_hook=None,
      writer_arg_extra=None,
  ):
    K, N = w_out_in.shape[1], w_out_in.shape[0]
    self.device, self.name, self.K, self.N = device, name, K, N
    num_banks = len(device.dram.bank_tiles)
    ys = sorted({y for _, y in device.cores})[:grid_rows]
    cores = [c for c in device.cores if c[1] in ys]
    chunks = mm.plan_output_chunks(1, K, N, cores, num_banks)
    self.Mp, self.Kp, self.Np = mm.global_padded_shape(1, K, N, chunks)

    w = np.zeros((self.Kp, self.Np), dtype=np.float32)
    w[:K, :N] = w_out_in.T
    self.w_buf = device.alloc_write(to_bf16_device_bytes(w), dtype=Dtype.Float16_b,
                                    shape=(self.Kp, self.Np), name=f"{name}.w")
    key = (self.Mp, self.Kp)
    if key not in xbufs:
      xbufs[key] = device.dram.alloc((self.Mp // TILE) * (self.Kp // TILE), dtype=Dtype.Float16_b,
                                     shape=(self.Mp, self.Kp), name=f"x{key}")
      xbufs[key]._host = None  # last-written x, to skip redundant uploads
    self.x_buf = xbufs[key]
    self.c_buf = device.dram.alloc((self.Mp // TILE) * (self.Np // TILE), dtype=Dtype.Float16_b,
                                   shape=(self.Mp, self.Np), name=f"{name}.c")
    base = dict(a_row_stride=self.Kp // TILE, b_row_stride=self.Np // TILE, c_row_stride=self.Np // TILE)
    self.programs = []
    for i, ch in enumerate(chunks):
      lay = TensorLayout(m_tile_offset=ch.m_tile_offset, n_tile_offset=ch.n_tile_offset, **base)
      prog = mm.build_program(
          ch.plan, self.x_buf.addr, self.w_buf.addr, self.c_buf.addr, num_banks, lay,
          output_tile_hook=output_tile_hook,
          writer_arg_extra=writer_arg_extra,
      )
      prog.name = f"{name}_c{i}"
      self.programs.append(prog)

  def run(self, x: np.ndarray, stats: dict, pos: int | None = None) -> None:
    del pos
    key = x.tobytes()
    if self.x_buf._host != key:  # q/k/v (and gate/up) share one upload
      xp = np.zeros((self.Mp, self.Kp), dtype=np.float32)
      xp[0, :self.K] = x
      self.device.dram_write_from(self.x_buf, to_bf16_device_bytes(xp))
      self.x_buf._host = key
    run_programs(self.device, self.programs, stats)
    stats["weight_bytes"] += self.Kp * self.Np * 2

  def run_prefilled(self, stats: dict) -> None:
    """Run GEMV from self.x_buf after another device program has filled it."""
    self.x_buf._host = None
    run_programs(self.device, self.programs, stats)
    stats["weight_bytes"] += self.Kp * self.Np * 2

  def read_output(self) -> np.ndarray:
    out = from_bf16_device_bytes(self.device.dram_read(self.c_buf), (self.Mp, self.Np))
    return out[0, :self.N].astype(np.float32)

  def __call__(self, x: np.ndarray, stats: dict, pos: int | None = None) -> np.ndarray:
    self.run(x, stats, pos=pos)
    return self.read_output()


class DeviceResidualGemv(DeviceGemv):
  """Projection GEMV followed by a device-side residual add."""

  def __init__(
      self,
      device,
      name: str,
      w_out_in: np.ndarray,
      xbufs: dict,
      grid_rows: int = 1,
  ):
    super().__init__(device, name, w_out_in, xbufs, grid_rows=grid_rows)
    self.out_tiles = self.Np // TILE
    self.residual_buf = device.dram.alloc(
        self.out_tiles, dtype=Dtype.Float16_b,
        shape=(self.out_tiles, TILE, TILE), name=f"{name}.residual")
    self.next_buf = device.dram.alloc(
        self.out_tiles, dtype=Dtype.Float16_b,
        shape=(self.out_tiles, TILE, TILE), name=f"{name}.next")
    self.add_prog = build_two_source_binary(
        "add", self.c_buf.addr, self.residual_buf.addr, self.next_buf.addr,
        len(device.dram.bank_tiles), core=device.cores[0], tiles=self.out_tiles)
    self.add_prog.name = f"{name}_residual_add"
    self.device_residual_buf = None

  def set_device_residual_source(self, buf, suffix: str = "device") -> None:
    """Use a row-tiled device activation buffer as the residual source."""
    self.device_residual_buf = buf
    self.add_prog = build_two_source_binary(
        "add", self.c_buf.addr, buf.addr, self.next_buf.addr,
        len(self.device.dram.bank_tiles), core=self.device.cores[0], tiles=self.out_tiles)
    self.add_prog.name = f"{self.name}_{suffix}_residual_add"

  def __call__(
      self,
      x: np.ndarray,
      stats: dict,
      pos: int | None = None,
      residual: np.ndarray | None = None,
  ) -> np.ndarray:
    if residual is None:
      return super().__call__(x, stats, pos=pos)

    del pos
    key = x.tobytes()
    if self.x_buf._host != key:
      xp = np.zeros((self.Mp, self.Kp), dtype=np.float32)
      xp[0, :self.K] = x
      self.device.dram_write_from(self.x_buf, to_bf16_device_bytes(xp))
      self.x_buf._host = key
    if self.device_residual_buf is None:
      self.write_residual(residual)
    run_programs(self.device, (*self.programs, self.add_prog), stats)
    stats["weight_bytes"] += self.Kp * self.Np * 2
    return self.read_next()

  def run_prefilled(
      self,
      stats: dict,
      residual: np.ndarray | None = None,
      read_next: bool = True,
  ) -> np.ndarray | None:
    has_residual = residual is not None or self.device_residual_buf is not None
    if not has_residual:
      super().run_prefilled(stats)
      return self.read_output()
    self.x_buf._host = None
    if self.device_residual_buf is None:
      if residual is None:
        raise ValueError(f"{self.name}: host residual required without a device residual source")
      self.write_residual(residual)
    run_programs(self.device, (*self.programs, self.add_prog), stats)
    stats["weight_bytes"] += self.Kp * self.Np * 2
    return self.read_next() if read_next else None

  def write_residual(self, residual: np.ndarray) -> None:
    residual_tiles = vector_to_row_tiles(quant_bf16(residual), self.Np)
    self.device.dram_write_from(self.residual_buf, to_bf16_device_bytes(residual_tiles))

  def read_next(self) -> np.ndarray:
    return row_tiles_to_vector(
        self.device.dram_read(self.next_buf), self.out_tiles, self.N).astype(np.float32)

  def add_residual(self, stats: dict, residual: np.ndarray) -> np.ndarray:
    self.write_residual(residual)
    run_program(self.device, self.add_prog, stats)
    return self.read_next()


class DeviceNormGemv(DeviceGemv):
  """Device RMSNorm(x, norm_w) feeding a resident-weight GEMV."""

  def __init__(
      self,
      device,
      name: str,
      w_out_in: np.ndarray,
      norm_w: np.ndarray,
      norm_eps: float,
      xbufs: dict,
      grid_rows: int = 1,
      output_tile_hook=None,
      writer_arg_extra=None,
      rms_input_scale: float = 1.0,
      fuse_row_to_rms: bool = False,
  ):
    super().__init__(
        device, name, w_out_in, xbufs, grid_rows=grid_rows,
        output_tile_hook=output_tile_hook, writer_arg_extra=writer_arg_extra)
    if self.K % (TILE * TILE):
      raise ValueError(f"{name}: staged RMSNorm bridge expects K multiple of 1024")

    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    self.core = core
    self.num_banks = num_banks
    self.norm_eps = norm_eps
    # Keep scaled-square disabled by default. Fixed scales improve tiny model
    # rows, but large activations can go non-finite; use only for controlled
    # experiments until there is a bounded/adaptive device-side scale.
    self.rms_input_scale = rms_input_scale
    self.fuse_row_to_rms = fuse_row_to_rms
    self.k_tiles = self.Kp // TILE
    partials = self.K // TILE
    partial1_tiles = partials // TILE

    self.x_rms_buf = device.dram.alloc(
        partials, dtype=Dtype.Float16_b, shape=(partials, TILE, TILE), name=f"{name}.x_rms")
    self.x_row_buf = device.dram.alloc(
        self.k_tiles, dtype=Dtype.Float16_b, shape=(self.k_tiles, TILE, TILE), name=f"{name}.x_row")
    norm_w_bf16 = quant_bf16(norm_w.astype(np.float32))
    self.norm_w_buf = device.alloc_write(
        to_bf16_device_bytes(vector_to_row_tiles(norm_w_bf16, self.Kp)),
        dtype=Dtype.Float16_b,
        shape=(self.k_tiles, TILE, TILE),
        name=f"{name}.norm_w",
    )
    self.partial1_buf = device.dram.alloc(partial1_tiles, dtype=Dtype.Float16_b, name=f"{name}.rms_partial1")
    self.partial2_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, name=f"{name}.rms_partial2")
    self.inv_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, shape=(1, TILE, TILE), name=f"{name}.rms_inv")
    self.scale_buf = device.dram.alloc(
        self.k_tiles, dtype=Dtype.Float16_b, shape=(self.k_tiles, TILE, TILE), name=f"{name}.norm_scale")
    device.dram_write(self.x_buf, b"\0" * self.x_buf.size)

    self.rms_programs = [
      normbridge.rms.build_reduce_program(
          self.x_rms_buf.addr, self.partial1_buf.addr, num_banks, core=core,
          tiles=partials, square=True, compact=True,
          square_scale=self.rms_input_scale),
      normbridge.rms.build_reduce_program(
          self.partial1_buf.addr, self.partial2_buf.addr, num_banks, core=core,
          tiles=partial1_tiles, square=False, compact=True),
      normbridge.rms.build_reduce_program(
          self.partial2_buf.addr, self.inv_buf.addr, num_banks, core=core,
          tiles=1, square=False, compact=False, final=True, k=self.K,
          eps=norm_eps * self.rms_input_scale * self.rms_input_scale,
          final_output_scale=self.rms_input_scale),
    ]
    for suffix, prog in zip(("sumsq", "reduce", "inv"), self.rms_programs):
      prog.name = f"{name}_rms_{suffix}"
    self.scale_prog = normbridge.build_two_source_bcast(
        "mul", "scalar", self.norm_w_buf.addr, self.inv_buf.addr, self.scale_buf.addr,
        num_banks, core=core, tiles=self.k_tiles, b_fixed=True)
    self.scale_prog.name = f"{name}_norm_w_times_inv"
    self.norm_prog = normbridge.build_two_source_bcast(
        "mul", "row", self.x_row_buf.addr, self.scale_buf.addr, self.x_buf.addr,
        num_banks, core=core, tiles=self.k_tiles, b_fixed=False)
    self.norm_prog.name = f"{name}_x_times_scale"
    self.device_input_row_buf = None
    self.device_input_row_to_fp_prog = None

  def set_device_input_source(self, row_buf, suffix: str = "device") -> None:
    """Use a row-tiled device activation as the RMSNorm input source."""
    self.device_input_row_buf = row_buf
    if self.fuse_row_to_rms:
      self.device_input_row_to_fp_prog = None
      self.rms_programs[0] = normbridge.rms.build_reduce_program(
          self.x_rms_buf.addr, self.partial1_buf.addr, self.num_banks, core=self.core,
          tiles=self.K // TILE, square=True, compact=True,
          square_scale=self.rms_input_scale,
          reader_preamble=swiglu_bridge.emit_row_to_footprint_preamble_from_rta,
          reader_arg_extra=lambda _x, _y: [row_buf.addr])
      self.rms_programs[0].name = f"{self.name}_rms_sumsq"
    else:
      self.device_input_row_to_fp_prog = swiglu_bridge.build_convert_program(
          "row_to_fp", row_buf.addr, self.x_rms_buf.addr, self.num_banks,
          tiles=self.k_tiles, core=self.core)
      self.device_input_row_to_fp_prog.name = f"{self.name}_{suffix}_row_to_rms_fp"
    self.norm_prog = normbridge.build_two_source_bcast(
        "mul", "row", row_buf.addr, self.scale_buf.addr, self.x_buf.addr,
        self.num_banks, core=self.core, tiles=self.k_tiles, b_fixed=False)
    self.norm_prog.name = f"{self.name}_{suffix}_times_scale"

  def run(self, x: np.ndarray, stats: dict, pos: int | None = None) -> None:
    del pos
    x_bf16 = quant_bf16(x)
    self.device.dram_write_from(
        self.x_rms_buf,
        normbridge.rms.to_bf16_bytes(normbridge.vector_to_footprint_tiles(x_bf16)),
    )
    self.device.dram_write_from(
        self.x_row_buf,
        to_bf16_device_bytes(vector_to_row_tiles(x_bf16, self.Kp)),
    )
    self.device.dram_write(self.partial2_buf, b"\0" * self.partial2_buf.size)
    self.x_buf._host = None

    run_programs(self.device, (*self.rms_programs, self.scale_prog, self.norm_prog, *self.programs), stats)
    stats["weight_bytes"] += self.Kp * self.Np * 2

  def run_prefilled_norm(self, stats: dict) -> None:
    """Run staged RMSNorm+GEMV after x_rms_buf and x_row_buf are device-filled."""
    self.device.dram_write(self.partial2_buf, b"\0" * self.partial2_buf.size)
    self.x_buf._host = None

    prefix = (self.device_input_row_to_fp_prog,) if self.device_input_row_to_fp_prog is not None else ()
    run_programs(self.device, (*prefix, *self.rms_programs, self.scale_prog, self.norm_prog, *self.programs), stats)
    stats["weight_bytes"] += self.Kp * self.Np * 2


class HostGemv:
  """Drop-in golden replacement (bf16-quantized like the device path)."""

  def __init__(self, w_out_in: np.ndarray):
    self.w = quant_bf16(w_out_in.astype(np.float32))

  def __call__(self, x: np.ndarray, stats: dict, pos: int | None = None) -> np.ndarray:
    del pos
    return quant_bf16(self.w @ quant_bf16(x))


# --------------------------------------------------------------------------
# Fast host-math decode path: device runs only the projection GEMVs.
#
# Per projection the host submits ONE pre-encoded CQ submission containing
# [fill x from sysmem] -> [GEMV chunk programs] -> [drain c to sysmem], then
# reads row 0 of the output tiles straight out of pinned sysmem. All CQ
# payloads are lowered/encoded once at init and replayed per token, so the
# host cost per token is a handful of memcpys and ring writes. Everything
# else (RMSNorm, RoPE, KV cache, attention, SwiGLU, residuals, argmax) runs
# in numpy.
# --------------------------------------------------------------------------

# The fast path bakes sysmem NOC addresses into fill/drain RTAs, so the
# sysmem mapping must be pinned at its final size before any program is
# encoded. Weight upload also streams through the same sysmem (largest single
# buffer is the 525 MB tied logits weight). Pin the 1 GB max once; staging
# regions for activations live in the first 64 MB and are only used at decode.
FAST_SYSMEM_SIZE = 1 << 30
FAST_STAGING_LIMIT = 64 << 20


class FastGemv:
  """One pre-encoded fill+GEMV+drain submission per call; row I/O via sysmem."""

  _x_regions: dict[tuple[int, int], tuple[int, "object"]] = {}

  def __init__(self, device, name: str, w_out_in: np.ndarray, sysmem_alloc, xbufs: dict):
    from cq import lower_programs as cq_lower_programs

    K, N = w_out_in.shape[1], w_out_in.shape[0]
    self.device, self.name, self.K, self.N = device, name, K, N
    num_banks = len(device.dram.bank_tiles)
    ys = sorted({y for _, y in device.cores})[:1]
    cores = [c for c in device.cores if c[1] in ys]
    chunks = mm.plan_output_chunks(1, K, N, cores, num_banks)
    self.Mp, self.Kp, self.Np = mm.global_padded_shape(1, K, N, chunks)

    w = np.zeros((self.Kp, self.Np), dtype=np.float32)
    w[:K, :N] = w_out_in.T
    self.w_buf = device.alloc_write(to_bf16_device_bytes(w), dtype=Dtype.Float16_b,
                                    shape=(self.Kp, self.Np), name=f"{name}.w")
    self.weight_bytes = self.Kp * self.Np * 2

    key = (self.Mp, self.Kp)
    if key not in xbufs:
      xbufs[key] = device.dram.alloc((self.Mp // TILE) * (self.Kp // TILE), dtype=Dtype.Float16_b,
                                     shape=(self.Mp, self.Kp), name=f"fastx{key}")
      xbufs[key]._host = None
    self.x_buf = xbufs[key]
    self.c_buf = device.dram.alloc((self.Mp // TILE) * (self.Np // TILE), dtype=Dtype.Float16_b,
                                   shape=(self.Mp, self.Np), name=f"{name}.c")
    base = dict(a_row_stride=self.Kp // TILE, b_row_stride=self.Np // TILE, c_row_stride=self.Np // TILE)
    gemv_progs = []
    for i, ch in enumerate(chunks):
      lay = TensorLayout(m_tile_offset=ch.m_tile_offset, n_tile_offset=ch.n_tile_offset, **base)
      prog = mm.build_program(ch.plan, self.x_buf.addr, self.w_buf.addr, self.c_buf.addr, num_banks, lay)
      prog.name = f"{name}_c{i}"
      gemv_progs.append(prog)

    self.x_tiles = self.Kp // TILE  # M=1: only the first tile row is live
    self.out_tiles = self.Np // TILE  # drain only the first output tile row

    # Shared per-K x staging region in sysmem (qkv/wo/gate share K=2048).
    if key not in FastGemv._x_regions or FastGemv._x_regions[key][1] is not device:
      FastGemv._x_regions[key] = (sysmem_alloc(self.x_buf.num_tiles * self.x_buf.page_size), device)
    self.x_off = FastGemv._x_regions[key][0]
    self.out_off = sysmem_alloc(self.out_tiles * self.c_buf.page_size)

    fill = build_fast_transfer_program(device, self.x_buf, self.x_off, drain=False,
                                       name=f"{name}_fill")
    drain = build_fast_transfer_program(device, self.c_buf, self.out_off, drain=True,
                                        name=f"{name}_drain", n_tiles=self.out_tiles)
    programs = [fill, *gemv_progs, drain]
    self.n_programs = len(programs)
    cores_all = device.cores
    irs = [p.lower(cores_all, dispatch_mode=fast_devmsgs().DISPATCH_MODE_DEV, host_assigned_id=i)
           for i, p in enumerate(programs)]
    ts = [device.cq.timestamp_noc_addr(i) for i in range(2 * len(programs))]
    payloads = cq_lower_programs(irs, device._go_word(), timestamps=ts)
    self.records = [fast_relay_inline(p) for p in payloads]

    # Zeroed x template: tiles laid out in face format; row 0 of a tile lives
    # at u16 [0:16] (face 0) and [256:272] (face 1).
    self.x_tpl = np.zeros((self.x_buf.num_tiles, 1024), dtype=np.uint16)

  def __call__(self, x: np.ndarray, stats: dict, pos: int | None = None,
               skip_upload: bool = False) -> np.ndarray:
    del pos
    sm = self.device._dram_sysmem
    if not skip_upload:
      u16 = (np.ascontiguousarray(x[:self.K], dtype=np.float32).view(np.uint32) >> 16).astype(np.uint16)
      lanes = np.zeros(self.Kp, dtype=np.uint16)
      lanes[:self.K] = u16
      lanes = lanes.reshape(self.x_tiles, 2, 16)
      self.x_tpl[:self.x_tiles, 0:16] = lanes[:, 0]
      self.x_tpl[:self.x_tiles, 256:272] = lanes[:, 1]
      data = self.x_tpl.tobytes()
      sm.mapping.copy_from(self.x_off, data, len(data))
      sm.mapping.flush(self.x_off, len(data))
    fast_submit(self.device, self.records, stats, self.n_programs)
    stats["weight_bytes"] += self.weight_bytes
    raw = sm.mapping.read(self.out_off, self.out_tiles * 2048)
    u = np.frombuffer(raw, dtype=np.uint16).reshape(self.out_tiles, 1024)
    row = np.empty(self.Np, dtype=np.uint16)
    row.reshape(-1, 32)[:, :16] = u[:, 0:16]
    row.reshape(-1, 32)[:, 16:] = u[:, 256:272]
    return bf16_to_f32(row[:self.N])


def fast_devmsgs():
  from program import DevMsgs
  return DevMsgs


def fast_relay_inline(payload: bytes) -> bytes:
  import cq as cqmod
  return cqmod._relay_inline(payload)


import os as _os
# A short submit throttle markedly reduces the rare relaunch-wedge frequency
# (and recovery replays cover the remainder); ~10 ms/token at 150 us.
FAST_SUBMIT_DELAY_S = float(_os.environ.get("FAST_SUBMIT_DELAY_US", "150")) / 1e6


def fast_submit(device, records: list[bytes], stats: dict, n_programs: int,
                retries: int = 2) -> None:
  import cq as cqmod
  sysm = device.cq.sysmem
  if FAST_SUBMIT_DELAY_S:
    time.sleep(FAST_SUBMIT_DELAY_S)
  issue_before = sysm.issue_wr
  event_id = sysm.event_id + 1
  try:
    for rec in records:
      sysm._issue_write(rec)
    event_id = sysm.next_event_id()
    sysm._issue_write(cqmod._relay_inline(cqmod._host_event(event_id)))
    # Decode bundles complete in <50 ms; a short deadline keeps the rare
    # wedge recovery cheap.
    sysm.wait_completion(event_id, timeout_s=0.7)
  except (TimeoutError, RuntimeError):
    if retries <= 0:
      raise
    print(f"[fast_recover] wedge at event {event_id} (issue_wr=0x{issue_before:x}); "
          "full CQ recovery + bundle replay", flush=True)
    device.recover_dispatch()
    stats["recoveries"] = stats.get("recoveries", 0) + 1
    fast_submit(device, records, stats, n_programs, retries=retries - 1)
    return
  start = device.cq.read_timestamp(0)
  end = device.cq.read_timestamp(2 * n_programs - 1)
  stats["device_us"] += max(0.0, (end - start) / 1350)
  stats["launches"] += n_programs
  stats["submissions"] = stats.get("submissions", 0) + 1


def build_fast_transfer_program(device, buf, sysmem_off: int, *, drain: bool, name: str,
                                n_tiles: int | None = None):
  from fw.dram import build_drain, build_fill
  from pcie import NOC_PCIE_OFFSET, PCIE_NOC_XY
  from program import Program
  from ttk.noc import NOC as TTNOC

  n_tiles = buf.num_tiles if n_tiles is None else n_tiles
  sm = device._dram_sysmem
  noc_local = sm.noc_addr - NOC_PCIE_OFFSET + sysmem_off
  cores = device.cores[:min(len(device.cores), n_tiles)]
  tiles_per_core = (n_tiles + len(cores) - 1) // len(cores)
  core_index = {core: i for i, core in enumerate(cores)}
  bank_count = len(device.dram.bank_tiles)
  sysmem_lo = noc_local & 0xFFFFFFFF
  sysmem_mid = TTNOC.PCIE_MID | ((noc_local >> 32) & 0xF)
  if (noc_local & 0xFFFFFFFF) + n_tiles * buf.page_size > (1 << 32):
    raise RuntimeError("fast transfer region crossed a 4GB NOC window")

  kernel = build_drain() if drain else build_fill()
  kernel.rta(lambda x, y: [
    buf.addr, (1 << 24) | PCIE_NOC_XY, sysmem_lo, sysmem_mid,
    core_index[(x, y)] * tiles_per_core,
    max(0, min(tiles_per_core, n_tiles - core_index[(x, y)] * tiles_per_core)),
    buf.page_size, bank_count,
  ])
  from asm import KernelBase
  empty = KernelBase()
  prog = Program(brisc=empty, ncrisc=kernel, trisc0=empty, trisc1=empty, trisc2=empty,
                 cbs=[(0, buf.page_size, 2)], num_cores=len(cores))
  prog.name = name
  return prog


class FastLlama:
  """Host-math decode; device does projection GEMVs only (fast path)."""

  def __init__(self, model: Model, device, max_seq: int = 512, n_layers: int | None = None):
    self.m, self.cfg, self.device = model, model.cfg, device
    self.n_layers = n_layers or self.cfg.n_layers
    self.max_seq = max_seq
    c = self.cfg
    self.cos, self.sin = rope_tables(c)
    self.k_cache = np.zeros((self.n_layers, c.n_kv_heads, max_seq, c.head_dim), dtype=np.float32)
    self.v_cache = np.zeros_like(self.k_cache)
    self.norms = {n: model.f32(n).copy() for n in model.offsets if "norm" in n}

    device._ensure_dram_sysmem(FAST_SYSMEM_SIZE)
    self._sysmem_next = 0

    def sysmem_alloc(size: int) -> int:
      off = self._sysmem_next
      self._sysmem_next = (off + size + 4095) & ~4095
      if self._sysmem_next > FAST_STAGING_LIMIT:
        raise RuntimeError("fast sysmem staging overflow")
      return off

    xbufs: dict = {}
    self.gemv = {}
    t0 = time.time()
    for i in range(self.n_layers):
      qkv = np.concatenate([model.f32(f"l{i}.wq"), model.f32(f"l{i}.wk"), model.f32(f"l{i}.wv")], axis=0)
      self.gemv[f"l{i}.qkv"] = FastGemv(device, f"l{i}.qkv", qkv, sysmem_alloc, xbufs)
      self.gemv[f"l{i}.wo"] = FastGemv(device, f"l{i}.wo", model.f32(f"l{i}.wo"), sysmem_alloc, xbufs)
      gateup = np.concatenate([model.f32(f"l{i}.wgate"), model.f32(f"l{i}.wup")], axis=0)
      self.gemv[f"l{i}.gateup"] = FastGemv(device, f"l{i}.gateup", gateup, sysmem_alloc, xbufs)
      self.gemv[f"l{i}.wdown"] = FastGemv(device, f"l{i}.wdown", model.f32(f"l{i}.wdown"), sysmem_alloc, xbufs)
    self.gemv["logits"] = FastGemv(device, "logits", model.f32("embed"), sysmem_alloc, xbufs)
    print(f"[init] fast path: {self.n_layers} layers + tied head, "
          f"{self._sysmem_next / 1e6:.1f} MB sysmem staging, in {time.time() - t0:.1f}s")

  def forward(self, token: int, pos: int, stats: dict, want_logits: bool = True):
    c = self.cfg
    x = self.m.embed_row(token).copy()
    cosp, sinp = self.cos[pos], self.sin[pos]
    h = c.hidden_dim
    for i in range(self.n_layers):
      xn = normed(x, self.norms[f"l{i}.attn_norm"], rmsnorm_inv(x, c.norm_eps))
      qkv = self.gemv[f"l{i}.qkv"](xn, stats)
      q_end, k_end = c.dim, c.dim + c.kv_dim
      q = rope_rotate(qkv[:q_end], cosp, sinp, c.n_heads, c.head_dim)
      k = rope_rotate(qkv[q_end:k_end], cosp, sinp, c.n_kv_heads, c.head_dim)
      self.k_cache[i, :, pos] = k.reshape(c.n_kv_heads, c.head_dim)
      self.v_cache[i, :, pos] = qkv[k_end:].reshape(c.n_kv_heads, c.head_dim)
      attn = attention(q, self.k_cache[i], self.v_cache[i], pos, c.n_heads, c.n_kv_heads, c.head_dim)
      x = x + self.gemv[f"l{i}.wo"](attn, stats)
      xn = normed(x, self.norms[f"l{i}.ffn_norm"], rmsnorm_inv(x, c.norm_eps))
      gu = self.gemv[f"l{i}.gateup"](xn, stats)
      x = x + self.gemv[f"l{i}.wdown"](swiglu(gu[:h], gu[h:]), stats)
    if not want_logits:
      return None
    return self.gemv["logits"](normed(x, self.norms["final_norm"], rmsnorm_inv(x, c.norm_eps)), stats)


class DeviceQkvGemv(DeviceNormGemv):
  """Device RMSNorm + QKV GEMV with a fused V-cache scatter tail."""

  def __init__(
      self,
      device,
      name: str,
      w_out_in: np.ndarray,
      norm_w: np.ndarray,
      norm_eps: float,
      xbufs: dict,
      cfg: Config,
      max_seq: int,
      v_cache_buf,
      rms_input_scale: float = 1.0,
      fuse_row_to_rms: bool = False,
  ):
    if cfg.head_dim != 64:
      raise ValueError("fused V-cache scatter currently expects head_dim=64")
    self._pos = 0
    hook = make_vscatter_hook(
        v_start_tile=(cfg.dim + cfg.kv_dim) // TILE,
        v_tiles=cfg.kv_dim // TILE,
        max_seq=max_seq,
        head_dim=cfg.head_dim,
    )

    def writer_extra(_x, _y):
      return [v_cache_buf.addr, self._pos]

    super().__init__(
        device, name, w_out_in, norm_w, norm_eps, xbufs,
        output_tile_hook=hook,
        writer_arg_extra=writer_extra,
        rms_input_scale=rms_input_scale,
        fuse_row_to_rms=fuse_row_to_rms,
    )
    self.v_cache_buf = v_cache_buf

  def run(self, x: np.ndarray, stats: dict, pos: int | None = None) -> None:
    if pos is None:
      raise ValueError("DeviceQkvGemv needs decode pos for V-cache scatter")
    self._pos = pos
    super().run(x, stats)

  def __call__(self, x: np.ndarray, stats: dict, pos: int | None = None) -> np.ndarray:
    self.run(x, stats, pos=pos)
    return self.read_output()

  def run_prefilled_norm(self, stats: dict, pos: int) -> None:
    self._pos = pos
    super().run_prefilled_norm(stats)


class DeviceKCacheUpdater:
  """Stage QKV K output through RoPE and scatter it into the device K cache."""

  def __init__(
      self,
      device,
      name: str,
      qkv_gemv: DeviceQkvGemv,
      cos_buf,
      sin_buf,
      k_cache_buf,
      cfg: Config,
      max_seq: int,
  ):
    self.device = device
    if cfg.head_dim != kstage.HEAD_DIM:
      raise ValueError("K-cache updater currently expects head_dim=64")
    self._pos = 0
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    self.rope_src_buf = device.dram.alloc(
        cfg.n_kv_heads, dtype=Dtype.Float16_b,
        shape=(cfg.n_kv_heads, TILE, TILE), name=f"{name}.rope_src")
    device.dram_write(self.rope_src_buf, b"\0" * self.rope_src_buf.size)
    self.prog = kstage.build_stage_rope_program(
        qkv_gemv.c_buf.addr, cos_buf.addr, sin_buf.addr, self.rope_src_buf.addr,
        k_cache_buf.addr, lambda: self._pos, max_seq, num_banks, core=core,
        heads=cfg.n_kv_heads, k_start_tile=cfg.dim // TILE,
    )
    self.prog.name = f"{name}_k_stage_rope_scatter"


  def __call__(self, stats: dict, pos: int) -> None:
    self._pos = pos
    run_program(self.device, self.prog, stats)


def make_attention_wo_input_hook(*, q_head: int):
  """Copy weighted-V row 0 into the matching head slice of Wo's input buffer."""
  from dsl import a0, a1, a2, a5, s8, s11, t0, t2, t6
  from ttk.mailbox import NcriscMailbox as NM

  row_half_bytes = 16 * Dtype.Float16_b.bpe
  tile_row0_col16_off = 16 * 16 * Dtype.Float16_b.bpe
  head_tile = q_head * (kstage.HEAD_DIM // TILE)

  def hook(fw, plan, *, tile_page, l1_tile):
    del plan
    done = fw._new_label("wo_input_hook_done")
    fw.li(t0, kstage.HEAD_DIM // TILE)
    fw.bgeu(tile_page, t0, done)

    fw.li(a1, head_tile)
    fw.add(a1, a1, tile_page)
    fw.rta_ptr(NM.RTA_L1_BASE_PTR, out=t2)
    fw.arg(a0, 31, ptr=t2)
    fw.mv(a2, s11)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, 0)

    fw.mv(t6, l1_tile)
    fw.li(a5, row_half_bytes)
    fw.noc_write(mm.OUTPUT_NOC, 0, t6, a0, 0, a2, a5, a=t0, v=t2)
    fw.li(t6, tile_row0_col16_off)
    fw.add(t6, l1_tile, t6)
    fw.addi(a0, a0, tile_row0_col16_off)
    fw.li(a5, row_half_bytes)
    fw.noc_write(mm.OUTPUT_NOC, 0, t6, a0, 0, a2, a5, a=t0, v=t2)
    fw.addi(s8, s8, 2)
    mm.emit_output_write_state_setup(fw)
    fw.label(done)

  return hook


def make_attention_group_wo_input_hook(*, q_base: int, group: int):
  """Copy grouped weighted-V rows 0,2,4,6 into matching Wo input head slices."""
  from dsl import a0, a1, a2, a5, s8, s11, t0, t2, t6
  from ttk.mailbox import NcriscMailbox as NM
  import microbench_attention_k_stage as attn_kv_stage

  row_half_bytes = 16 * Dtype.Float16_b.bpe
  tile_row0_col16_off = 16 * 16 * Dtype.Float16_b.bpe

  def hook(fw, plan, *, tile_page, l1_tile):
    del plan
    done = fw._new_label("wo_group_input_hook_done")
    fw.li(t0, kstage.HEAD_DIM // TILE)
    fw.bgeu(tile_page, t0, done)

    for row in range(group):
      src_row = row * 2
      head_tile = (q_base + row) * (kstage.HEAD_DIM // TILE)
      for half, src_col in enumerate((0, 16)):
        fw.li(a1, head_tile)
        fw.add(a1, a1, tile_page)
        fw.rta_ptr(NM.RTA_L1_BASE_PTR, out=t2)
        fw.arg(a0, 31, ptr=t2)
        fw.mv(a2, s11)
        fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, 0)
        if half:
          fw.addi(a0, a0, tile_row0_col16_off)
        fw.li(t6, attn_kv_stage.packed_elem_offset(src_row, src_col))
        fw.add(t6, l1_tile, t6)
        fw.li(a5, row_half_bytes)
        fw.noc_write(mm.OUTPUT_NOC, 0, t6, a0, 0, a2, a5, a=t0, v=t2)
      fw.addi(s8, s8, 2)
    mm.emit_output_write_state_setup(fw)
    fw.label(done)

  return hook


def make_attention_score_mirror_hook(*, dst_page: int):
  """Mirror a score GEMV output tile into the full-history score tile list."""
  from dsl import a0, a1, a2, a5, s8, s11, t0, t2, t6
  from ttk.mailbox import NcriscMailbox as NM

  def hook(fw, plan, *, tile_page, l1_tile):
    del plan, tile_page
    fw.rta_ptr(NM.RTA_L1_BASE_PTR, out=t2)
    fw.arg(a0, 31, ptr=t2)
    fw.li(a1, dst_page)
    fw.mv(a2, s11)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, 0)
    fw.mv(t6, l1_tile)
    fw.li(a5, Dtype.Float16_b.tile_size)
    fw.noc_write(mm.OUTPUT_NOC, 0, t6, a0, 0, a2, a5, a=t0, v=t2)
    fw.addi(s8, s8, 1)
    mm.emit_output_write_state_setup(fw)

  return hook


ATTN_KV_SCORE_SYNC_SEM = 2


def emit_wait_for_attention_kv_score_preamble(fw, _plan) -> None:
  from dsl import t0, t6
  from ttk.mailbox import BriscMailbox as BM

  fw.li(t0, ATTN_KV_SCORE_SYNC_SEM)
  fw.sem_addr(BM.SEM_L1_BASE, t0, out=t6)
  fw.noc_semaphore_wait(t6, 1)
  fw.noc_semaphore_set(t6, 0)


def emit_signal_attention_kv_score_preamble(fw) -> None:
  from dsl import t0, t6
  from ttk.mailbox import NcriscMailbox as NM

  fw.li(t0, ATTN_KV_SCORE_SYNC_SEM)
  fw.sem_addr(NM.SEM_L1_BASE, t0, out=t6)
  fw.noc_semaphore_set(t6, 1)


def build_attention_group_q_assemble_program(tmp_addrs: list[int], dst_addr: int,
                                             num_banks: int, *, core):
  """Pack four row-0 temporary Q A buffers into rows 0..3 of grouped A."""
  from asm import KernelBase
  from dsl import a0, a1, a2, a5, s0, s1, s2, s3, s4, s5, t0, t1, t2, t4, t5, t6, zero
  from examples.add1 import Brisc
  from program import Program
  from ttk.mailbox import BriscMailbox as BM
  from ttk.noc import NOC
  from ttk.tensix import TensixL1
  import microbench_attention_k_stage as attn_kv_stage

  if len(tmp_addrs) != 4:
    raise ValueError("expected four temporary Q buffers for a GQA group")

  page = Dtype.Float16_b.tile_size
  src_l1 = TensixL1.DATA_BUFFER_SPACE_BASE
  dst_l1 = src_l1 + page

  def read_tmp_page(fw: Brisc, *, base_reg, page_idx: int) -> None:
    fw.mv(a0, base_reg)
    fw.li(a1, page_idx)
    fw.mv(a2, s5)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
    fw.local_noc0_coord(a5)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    fw.addi(t4, t4, 1)
    fw.li(t2, src_l1)
    fw.li(t6, page)
    fw.noc_read(0, 1, a0, 0, a2, t2, t6, ret_coord=a5, a=t0, v=t1)
    fw.noc_reads_flushed(0, t4, addr=t0, val=t1)

  def write_group_page(fw: Brisc, *, page_idx: int, l1_src: int) -> None:
    fw.mv(a0, s4)
    fw.li(a1, page_idx)
    fw.mv(a2, s5)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
    fw.local_noc0_coord(a5)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED)
    fw.addi(t4, t4, 1)
    fw.li(t2, l1_src)
    fw.li(t6, page)
    fw.noc_write(0, 0, t2, a0, 0, a2, t6, a=t0, v=t1)
    fw.noc_write_barrier(0, t4, addr=t0, val=t1)

  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5))
  fw.li(t0, dst_l1)
  fw.li(t1, dst_l1 + (kstage.HEAD_DIM // TILE) * page)
  zero_loop = fw._new_label("attn_group_q_asm_zero")
  fw.label(zero_loop)
  fw.sw(zero, t0, 0)
  fw.addi(t0, t0, 4)
  fw.bltu(t0, t1, zero_loop)

  for row, src_reg in enumerate((s0, s1, s2, s3)):
    for page_idx in range(kstage.HEAD_DIM // TILE):
      read_tmp_page(fw, base_reg=src_reg, page_idx=page_idx)
      for lane in range(TILE):
        fw.li(t5, src_l1)
        fw.lhu(t0, t5, attn_kv_stage.packed_elem_offset(0, lane))
        fw.li(t2, dst_l1 + page_idx * page + attn_kv_stage.packed_elem_offset(row, lane))
        fw.sh(t0, t2, 0)

  for page_idx in range(kstage.HEAD_DIM // TILE):
    write_group_page(fw, page_idx=page_idx, l1_src=dst_l1 + page_idx * page)
  fw.ret()
  fw.rta(lambda _x, _y: [*tmp_addrs, dst_addr, num_banks])
  prog = Program(brisc=fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_group_q_rows_to_a"
  return prog


def build_attention_copy_tile_program(src_addr: int, dst_addr: int, num_banks: int, *,
                                      core, src_page: int = 0, dst_page: int = 0,
                                      name: str = "attn_copy_tile"):
  """Copy one logical DRAM tile page, preserving allocator page interleave."""
  from asm import KernelBase
  from dsl import s0, s1, s3, t2
  from examples.add1 import Brisc
  from program import Program
  from ttk.mailbox import BriscMailbox as BM
  import microbench_attention_k_stage as attn_kv_stage

  fw = Brisc()
  # RTAs: source base, destination base, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s3))
  fw.li(t2, src_page)
  attn_kv_stage.emit_read_page(fw, base_reg=s0, page_reg=t2, l1_dst=attn_kv_stage.SRC_L1)
  attn_kv_stage.emit_write_l1_page(fw, page=dst_page, l1_src=attn_kv_stage.SRC_L1)
  fw.ret()
  fw.rta(lambda _x, _y: [src_addr, dst_addr, num_banks])
  prog = Program(brisc=fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = name
  return prog


def build_attention_ctx_to_wo_program(ctx_addr: int, wo_addr: int, num_banks: int, *,
                                      core, q_base: int, group: int,
                                      name: str = "attn_ctx_to_wo"):
  """Copy grouped context rows 0..group-1 into the matching Wo input slices."""
  from asm import KernelBase
  from dsl import a0, a1, a2, a5, s0, s1, s3, t0, t1, t2, t4, t5, t6
  from examples.add1 import Brisc
  from program import Program
  from ttk.mailbox import BriscMailbox as BM
  from ttk.noc import NOC
  import microbench_attention_k_stage as attn_kv_stage

  row_half_bytes = 16 * Dtype.Float16_b.bpe
  tile_row0_col16_off = 16 * 16 * Dtype.Float16_b.bpe
  fw = Brisc()
  # RTAs: accumulated context base, Wo input base, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s3))
  for tile_page in range(kstage.HEAD_DIM // TILE):
    fw.li(t2, tile_page)
    attn_kv_stage.emit_read_page(fw, base_reg=s0, page_reg=t2, l1_dst=attn_kv_stage.SRC_L1)
    for row in range(group):
      head_tile = (q_base + row) * (kstage.HEAD_DIM // TILE) + tile_page
      for half, src_col in enumerate((0, 16)):
        fw.mv(a0, s1)
        fw.li(a1, head_tile)
        fw.mv(a2, s3)
        fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
        if half:
          fw.addi(a0, a0, tile_row0_col16_off)
        fw.local_noc0_coord(a5)
        fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED)
        fw.addi(t4, t4, 1)
        fw.li(t5, attn_kv_stage.SRC_L1 + attn_kv_stage.packed_elem_offset(row, src_col))
        fw.li(t6, row_half_bytes)
        fw.noc_write(0, 0, t5, a0, 0, a2, t6, a=t0, v=t1)
        fw.noc_write_barrier(0, t4, addr=t0, val=t1)
  fw.ret()
  fw.rta(lambda _x, _y: [ctx_addr, wo_addr, num_banks])
  prog = Program(brisc=fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = name
  return prog


class DeviceAttention:
  """One-tile decode attention chain feeding Wo.x_buf from device-resident Q/K/V."""

  def __init__(
      self,
      device,
      name: str,
      qkv_gemv: DeviceQkvGemv,
      cos_buf,
      sin_buf,
      k_cache_buf,
      v_cache_buf,
      wo_gemv: DeviceResidualGemv,
      cfg: Config,
      max_seq: int,
      allow_block_local: bool = False,
  ):
    import microbench_attention_k_stage as attn_kv_stage
    import microbench_attention_q_rope_stage as qrope_stage
    import microbench_attention_gqa_multitile_scores as gqa_multitile
    import microbench_attention_global_softmax_stats as attn_stats
    import microbench_attention_global_softmax_combine as attn_combine
    import microbench_attention_global_softmax_probs as attn_probs
    from ttk.mailbox import NcriscMailbox as NM

    if cfg.head_dim != attn_kv_stage.HEAD_DIM:
      raise ValueError("device attention currently expects head_dim=64")
    if max_seq % attn_kv_stage.ROWS_PER_PAGE:
      raise ValueError("device attention expects row-major KV heads to be page-aligned")
    if cfg.n_heads % cfg.n_kv_heads:
      raise ValueError("device attention expects GQA groups to divide evenly")
    group = cfg.n_heads // cfg.n_kv_heads
    if group != 4:
      raise ValueError("device attention grouped path currently expects four Q heads per KV head")

    self.device = device
    self._pos = 0
    self.cfg = cfg
    self.group = group
    self.max_seq = max_seq
    self.allow_block_local = allow_block_local
    self.seq_tiles = max_seq // TILE
    self.wo_gemv = wo_gemv
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    cores = [core]

    score_chunks = mm.plan_output_chunks(group, cfg.head_dim, TILE, cores, num_banks)
    v_chunks = mm.plan_output_chunks(group, TILE, cfg.head_dim, cores, num_banks)
    if len(score_chunks) != 1 or len(v_chunks) != 1:
      raise ValueError("device attention currently expects one score chunk and one V chunk")
    score_chunk = score_chunks[0]
    v_chunk = v_chunks[0]
    self.Mp, self.Kp, self.Np = mm.global_padded_shape(group, cfg.head_dim, TILE, score_chunks)
    self.VMp, self.VKp, self.VNp = mm.global_padded_shape(group, TILE, cfg.head_dim, v_chunks)
    if self.Kp != cfg.head_dim or self.VMp != self.Mp or self.VKp > self.Np:
      raise ValueError(f"unexpected attention shapes score={(self.Mp, self.Kp, self.Np)} "
                       f"v={(self.VMp, self.VKp, self.VNp)}")
    if wo_gemv.Mp != self.Mp or wo_gemv.Kp < cfg.dim:
      raise ValueError(f"Wo GEMV input shape {(wo_gemv.Mp, wo_gemv.Kp)} cannot hold attention")

    score_tiles = (self.Mp // TILE) * (self.Np // TILE)
    a_pages = (self.Mp // TILE) * (self.Kp // TILE)
    k_t_pages = (self.Kp * self.Np * Dtype.Float16_b.bpe) // Dtype.Float16_b.tile_size
    v_pages = (self.VKp * self.VNp * Dtype.Float16_b.bpe) // Dtype.Float16_b.tile_size
    ctx_pages = (self.VMp // TILE) * (self.VNp // TILE)

    self.q_rope_src_buf = device.dram.alloc(
        1, dtype=Dtype.Float16_b, shape=(1, TILE, TILE), name=f"{name}.attn_q_rope_src")
    self.a_buf = device.dram.alloc(
        a_pages, dtype=Dtype.Float16_b, shape=(self.Mp, self.Kp), name=f"{name}.attn_q_a")
    self.k_t_buf = device.dram.alloc(
        k_t_pages, dtype=Dtype.Float16_b, shape=(self.Kp, self.Np), name=f"{name}.attn_k_t")
    self.v_buf = device.dram.alloc(
        v_pages, dtype=Dtype.Float16_b, shape=(self.VKp, self.VNp), name=f"{name}.attn_v")
    self.scores_buf = device.dram.alloc(
        score_tiles, dtype=Dtype.Float16_b, shape=(self.Mp, self.Np), name=f"{name}.attn_scores")
    self.probs_buf = device.dram.alloc(
        score_tiles, dtype=Dtype.Float16_b, shape=(score_tiles, TILE, TILE), name=f"{name}.attn_probs")
    self.ctx_buf = device.dram.alloc(
        ctx_pages, dtype=Dtype.Float16_b, shape=(self.VMp, self.VNp), name=f"{name}.attn_ctx")
    for buf in (self.q_rope_src_buf, self.a_buf, self.k_t_buf, self.v_buf,
                self.scores_buf, self.probs_buf, self.ctx_buf):
      device.dram_write(buf, b"\0" * buf.size)

    self.q_group_stage_rope = []
    for kv_head in range(cfg.n_kv_heads):
      q_base = kv_head * group
      prog = qrope_stage.build_q_rope_group_stage_to_a_program(
          qkv_gemv.c_buf.addr, cos_buf.addr, sin_buf.addr,
          self.q_rope_src_buf.addr, self.a_buf.addr,
          q_base, lambda: self._pos, num_banks, core=core, group=group)
      prog.name = f"{name}_attn_q{q_base}_q{q_base + group - 1}_stage_rope_to_a"
      self.q_group_stage_rope.append(prog)

    score_layout = TensorLayout(
        m_tile_offset=score_chunk.m_tile_offset,
        n_tile_offset=score_chunk.n_tile_offset,
        a_row_stride=self.Kp // TILE,
        b_row_stride=self.Np // TILE,
        c_row_stride=self.Np // TILE,
    )
    score_writer_rta_count = len(mm.writer_args(
        score_chunk.plan, self.k_t_buf.addr, self.scores_buf.addr,
        core, num_banks, score_layout))
    self.score_prog = []
    for seq_tile in range(self.seq_tiles):
      tile_programs = []
      for kv_head in range(cfg.n_kv_heads):
        seq_start = seq_tile * TILE

        def _score_writer_preamble(fw, _plan, seq_start=seq_start):
          attn_kv_stage.emit_rowmajor_kv_stage_preamble(
              fw, seq=TILE, max_seq=max_seq,
              k_n_cols=self.Np, v_n_cols=self.VNp,
              k_dst_pages=k_t_pages, v_dst_pages=v_pages,
              rta_offset=score_writer_rta_count,
              seq_start=seq_start,
              k_scale_pow2_down=3,
              rta_ptr_addr=NM.RTA_L1_BASE_PTR,
              bank_table=NM.DRAM_BANK_TO_NOC_XY,
              noc_id=1,
              x_addr=NM.MY_X,
              y_addr=NM.MY_Y)
          emit_signal_attention_kv_score_preamble(fw)

        prog = mm.build_program(
            score_chunk.plan, self.a_buf.addr, self.k_t_buf.addr, self.scores_buf.addr,
            num_banks, score_layout,
            reader_preamble=emit_wait_for_attention_kv_score_preamble,
            writer_preamble=_score_writer_preamble,
            writer_arg_extra=lambda _x, _y, kv_head=kv_head: [
                k_cache_buf.addr, self.k_t_buf.addr, kv_head, num_banks,
                v_cache_buf.addr, self.v_buf.addr,
            ])
        prog.name = f"{name}_attn_t{seq_tile}_kv{kv_head}_score_gemv_kv_preamble"
        tile_programs.append(prog)
      self.score_prog.append(tile_programs)

    self.softmax_by_pos = []
    for pos in range(TILE):
      prog = attn_kv_stage.build_masked_softmax_program(
          self.scores_buf.addr, self.probs_buf.addr, num_banks,
          core=core, tiles=score_tiles, pos=pos, mask_rows=group,
          score_scale_pow2_down=0)
      prog.name = f"{name}_attn_masked_softmax_p{pos}"
      self.softmax_by_pos.append(prog)

    v_layout = TensorLayout(
        m_tile_offset=v_chunk.m_tile_offset,
        n_tile_offset=v_chunk.n_tile_offset,
        a_row_stride=self.Np // TILE,
        b_row_stride=self.VNp // TILE,
        c_row_stride=self.VNp // TILE,
    )
    self.v_gemv = []
    for kv_head in range(cfg.n_kv_heads):
      prog = mm.build_program(
          v_chunk.plan, self.probs_buf.addr, self.v_buf.addr, self.ctx_buf.addr,
          num_banks, v_layout,
          output_tile_hook=make_attention_group_wo_input_hook(q_base=kv_head * group, group=group),
          writer_arg_extra=lambda _x, _y: [wo_gemv.x_buf.addr],
      )
      prog.name = f"{name}_attn_kv{kv_head}_weighted_v_to_wo"
      self.v_gemv.append(prog)

    self.name = name
    self.core = core
    self.num_banks = num_banks
    self.score_chunk = score_chunk
    self.v_chunk = v_chunk
    self.score_tiles = score_tiles
    self.k_t_pages = k_t_pages
    self.v_pages = v_pages
    self.ctx_pages = ctx_pages
    self.score_layout = score_layout
    self.v_layout = v_layout
    self.k_cache_buf = k_cache_buf
    self.v_cache_buf = v_cache_buf
    self._full_history_ready = False

    # Full-history path for pos >= 32. Keep this as a conservative program
    # chain: per-history-tile score+KV-stage, global softmax, per-tile
    # weighted-V, device ADD accumulation, then a small copy into Wo.x_buf.
    self.full_score_tiles = self.seq_tiles
    self.full_score_hist_buf = device.dram.alloc(
        self.full_score_tiles, dtype=Dtype.Float16_b,
        shape=(self.full_score_tiles, TILE, TILE), name=f"{name}.attn_full_scores")
    self.full_prob_hist_buf = device.dram.alloc(
        self.full_score_tiles, dtype=Dtype.Float16_b,
        shape=(self.full_score_tiles, TILE, TILE), name=f"{name}.attn_full_probs")
    self.full_stats_buf = device.dram.alloc(
        self.full_score_tiles, dtype=Dtype.Float16_b,
        shape=(self.full_score_tiles, TILE, TILE), name=f"{name}.attn_full_stats")
    self.full_compact_stats_buf = device.dram.alloc(
        1, dtype=Dtype.Float16_b, shape=(TILE, TILE), name=f"{name}.attn_full_compact_stats")
    self.full_global_stats_buf = device.dram.alloc(
        1, dtype=Dtype.Float16_b, shape=(TILE, TILE), name=f"{name}.attn_full_global_stats")
    self.full_score_tmp_bufs = [
        device.dram.alloc(score_tiles, dtype=Dtype.Float16_b,
                          shape=(self.Mp, self.Np), name=f"{name}.attn_full_score_tmp_t{tile}")
        for tile in range(self.full_score_tiles)
    ]
    self.full_v_bufs = [
        device.dram.alloc(v_pages, dtype=Dtype.Float16_b,
                          shape=(self.VKp, self.VNp), name=f"{name}.attn_full_v_t{tile}")
        for tile in range(self.full_score_tiles)
    ]
    self.full_ctx_bufs = [
        device.dram.alloc(ctx_pages, dtype=Dtype.Float16_b,
                          shape=(self.VMp, self.VNp), name=f"{name}.attn_full_ctx_t{tile}")
        for tile in range(self.full_score_tiles)
    ]
    self.full_acc_bufs = [
        device.dram.alloc(ctx_pages, dtype=Dtype.Float16_b,
                          shape=(self.VMp, self.VNp), name=f"{name}.attn_full_acc_t{tile}")
        for tile in range(max(1, self.full_score_tiles - 1))
    ]
    for buf in (self.full_score_hist_buf, self.full_prob_hist_buf, self.full_stats_buf,
                self.full_compact_stats_buf, self.full_global_stats_buf,
                *self.full_score_tmp_bufs, *self.full_v_bufs,
                *self.full_ctx_bufs, *self.full_acc_bufs):
      device.dram_write(buf, b"\0" * buf.size)

    full_score_layout = TensorLayout(
        m_tile_offset=score_chunk.m_tile_offset,
        n_tile_offset=score_chunk.n_tile_offset,
        a_row_stride=self.Kp // TILE,
        b_row_stride=self.Np // TILE,
        c_row_stride=self.Np // TILE,
    )
    full_score_writer_rta_counts = [
        len(mm.writer_args(score_chunk.plan, self.k_t_buf.addr, self.full_score_tmp_bufs[tile].addr,
                           core, num_banks, full_score_layout))
        for tile in range(self.full_score_tiles)
    ]
    self.full_score_prog = []
    for tile in range(self.full_score_tiles):
      tile_programs = []
      seq_start = tile * TILE
      for kv_head in range(cfg.n_kv_heads):
        def _full_score_writer_preamble(fw, _plan, seq_start=seq_start, tile=tile):
          attn_kv_stage.emit_rowmajor_kv_stage_preamble(
              fw, seq=TILE, max_seq=max_seq,
              k_n_cols=self.Np, v_n_cols=self.VNp,
              k_dst_pages=k_t_pages, v_dst_pages=v_pages,
              rta_offset=full_score_writer_rta_counts[tile] + 1,
              seq_start=seq_start,
              dst_seq_start=0,
              k_scale_pow2_down=3,
              rta_ptr_addr=NM.RTA_L1_BASE_PTR,
              bank_table=NM.DRAM_BANK_TO_NOC_XY,
              noc_id=1,
              x_addr=NM.MY_X,
              y_addr=NM.MY_Y)
          emit_signal_attention_kv_score_preamble(fw)

        prog = mm.build_program(
            score_chunk.plan, self.a_buf.addr, self.k_t_buf.addr, self.full_score_tmp_bufs[tile].addr,
            num_banks, full_score_layout,
            reader_preamble=emit_wait_for_attention_kv_score_preamble,
            writer_preamble=_full_score_writer_preamble,
            output_tile_hook=make_attention_score_mirror_hook(dst_page=tile),
            writer_arg_extra=lambda _x, _y, kv_head=kv_head, tile=tile: [
                self.full_score_hist_buf.addr,
                k_cache_buf.addr, self.k_t_buf.addr, kv_head, num_banks,
                v_cache_buf.addr, self.full_v_bufs[tile].addr,
            ])
        prog.name = f"{name}_attn_full_t{tile}_kv{kv_head}_score_gemv_kv_preamble"
        tile_programs.append(prog)
      self.full_score_prog.append(tile_programs)

    self.full_mask_by_tile_pos = [
        [
          gqa_multitile.build_causal_score_mask_program(
              self.full_score_hist_buf.addr, num_banks, core=core, pos=pos,
              mask_rows=group, page=tile)
          for pos in range(TILE)
        ]
        for tile in range(self.full_score_tiles)
    ]
    for tile, progs in enumerate(self.full_mask_by_tile_pos):
      for pos, prog in enumerate(progs):
        prog.name = f"{name}_attn_full_t{tile}_causal_score_mask_p{pos}"

    self.full_stats_prog = []
    self.full_compact_prog = []
    self.full_combine_prog = []
    self.full_prob_prog = []
    for live_tiles in range(self.full_score_tiles + 1):
      if live_tiles == 0:
        self.full_stats_prog.append(None)
        self.full_compact_prog.append(None)
        self.full_combine_prog.append(None)
        self.full_prob_prog.append(None)
        continue
      stats_prog = attn_stats.build_program(
          self.full_score_hist_buf.addr, self.full_stats_buf.addr, num_banks,
          core=core, tiles=live_tiles, timed=False)
      stats_prog.name = f"{name}_attn_full_softmax_stats_{live_tiles}t"
      compact_prog = attn_combine.build_compact_stats_program(
          self.full_stats_buf.addr, self.full_compact_stats_buf.addr, num_banks,
          core=core, tiles=live_tiles)
      compact_prog.name = f"{name}_attn_full_softmax_compact_{live_tiles}t"
      combine_prog = attn_combine.build_combine_program(
          self.full_compact_stats_buf.addr, self.full_global_stats_buf.addr, num_banks,
          core=core, timed=False)
      combine_prog.name = f"{name}_attn_full_softmax_combine_{live_tiles}t"
      prob_prog = attn_probs.build_program(
          self.full_score_hist_buf.addr, self.full_global_stats_buf.addr,
          self.full_prob_hist_buf.addr, num_banks, core=core, tiles=live_tiles, timed=False)
      prob_prog.name = f"{name}_attn_full_softmax_probs_{live_tiles}t"
      self.full_stats_prog.append(stats_prog)
      self.full_compact_prog.append(compact_prog)
      self.full_combine_prog.append(combine_prog)
      self.full_prob_prog.append(prob_prog)

    self.full_v_gemv = []
    for tile in range(self.full_score_tiles):
      full_v_layout = TensorLayout(
          m_tile_offset=v_chunk.m_tile_offset,
          n_tile_offset=v_chunk.n_tile_offset,
          a_row_stride=self.Np // TILE,
          b_row_stride=self.VNp // TILE,
          c_row_stride=self.VNp // TILE,
          a_m_tile_offset=tile,
      )
      prog = mm.build_program(
          v_chunk.plan, self.full_prob_hist_buf.addr, self.full_v_bufs[tile].addr,
          self.full_ctx_bufs[tile].addr, num_banks, full_v_layout)
      prog.name = f"{name}_attn_full_weighted_v_t{tile}"
      self.full_v_gemv.append(prog)

    self.full_add_chain = [[] for _ in range(self.full_score_tiles + 1)]
    self.full_final_ctx_buf = [self.full_ctx_bufs[0] for _ in range(self.full_score_tiles + 1)]
    if self.full_score_tiles >= 2:
      for live_tiles in range(2, self.full_score_tiles + 1):
        chain = []
        prog = build_two_source_binary(
            "add", self.full_ctx_bufs[0].addr, self.full_ctx_bufs[1].addr,
            self.full_acc_bufs[0].addr, num_banks, core=core, tiles=ctx_pages)
        prog.name = f"{name}_attn_full_ctx_acc_0_1_{live_tiles}t"
        chain.append(prog)
        final_buf = self.full_acc_bufs[0]
        for tile in range(2, live_tiles):
          dst = self.full_acc_bufs[tile - 1]
          prog = build_two_source_binary(
              "add", final_buf.addr, self.full_ctx_bufs[tile].addr, dst.addr,
              num_banks, core=core, tiles=ctx_pages)
          prog.name = f"{name}_attn_full_ctx_acc_t{tile}_{live_tiles}t"
          chain.append(prog)
          final_buf = dst
        self.full_add_chain[live_tiles] = chain
        self.full_final_ctx_buf[live_tiles] = final_buf

    self.full_ctx_to_wo = []
    for live_tiles in range(self.full_score_tiles + 1):
      per_head = []
      final_buf = self.full_final_ctx_buf[live_tiles]
      for kv_head in range(cfg.n_kv_heads):
        prog = build_attention_ctx_to_wo_program(
            final_buf.addr, wo_gemv.x_buf.addr, num_banks, core=core,
            q_base=kv_head * group, group=group,
            name=f"{name}_attn_full_kv{kv_head}_ctx_to_wo_{live_tiles}t")
        per_head.append(prog)
      self.full_ctx_to_wo.append(per_head)
    self._full_history_ready = True

  def _ensure_full_history_programs(self) -> None:
    if not self._full_history_ready:
      raise RuntimeError("full-history attention programs were not constructed")

  def __call__(self, stats: dict, pos: int) -> None:
    if pos >= self.max_seq:
      raise ValueError("device attention position exceeds max_seq")
    self._pos = pos
    seq_tile = pos // TILE
    local_pos = pos % TILE
    # Each GQA group writes its four head slices into row 0 before Wo runs, and
    # Wo's M=1 output only consumes that row. Avoid a per-layer host zero fill.
    self.wo_gemv.x_buf._host = None

    if pos >= TILE and not self.allow_block_local:
      self._ensure_full_history_programs()
      live_tiles = seq_tile + 1
      for kv_head in range(self.cfg.n_kv_heads):
        programs = [self.q_group_stage_rope[kv_head]]
        for tile in range(live_tiles):
          programs.append(self.full_score_prog[tile][kv_head])
          if tile == seq_tile:
            programs.append(self.full_mask_by_tile_pos[tile][local_pos])
        programs.extend((
          self.full_stats_prog[live_tiles],
          self.full_compact_prog[live_tiles],
          self.full_combine_prog[live_tiles],
          self.full_prob_prog[live_tiles],
        ))
        for tile in range(live_tiles):
          programs.append(self.full_v_gemv[tile])
        programs.extend(self.full_add_chain[live_tiles])
        programs.append(self.full_ctx_to_wo[live_tiles][kv_head])
        run_programs(self.device, programs, stats)
      return

    for kv_head in range(self.cfg.n_kv_heads):
      run_programs(self.device, (
        self.q_group_stage_rope[kv_head],
        self.score_prog[seq_tile][kv_head],
        self.softmax_by_pos[local_pos],
        self.v_gemv[kv_head],
      ), stats)


class DeviceTokenEmbeddingNormInputs:
  """Gather token embedding into a DeviceNormGemv's staged input buffers."""

  def __init__(self, device, model: Model, target: DeviceNormGemv):
    cfg = model.cfg
    dim_tiles = cfg.dim // TILE
    if target.K != cfg.dim or target.k_tiles < dim_tiles:
      raise ValueError("embedding bridge target must consume model-dim inputs")
    off, shape = model.offsets["embed"]
    if shape != (cfg.vocab_size, cfg.dim):
      raise ValueError(f"unexpected embed shape {shape}")
    raw = np.asarray(model.data[off:off + cfg.vocab_size * cfg.dim], dtype=np.uint16)
    pages = raw.nbytes // Dtype.Float16_b.tile_size
    if pages * Dtype.Float16_b.tile_size != raw.nbytes:
      raise ValueError("embedding table must be page-aligned")

    self.device = device
    self.target = target
    self.token_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, name="decode_token_id")
    self.table_buf = device.dram.alloc(pages, dtype=Dtype.Float16_b, name="embed_table_rowmajor")
    device.dram_write(self.table_buf, raw.tobytes())
    device.dram_write(self.token_buf, b"\0" * self.token_buf.size)
    device.dram_write(target.x_row_buf, b"\0" * target.x_row_buf.size)
    device.dram_write(target.x_rms_buf, b"\0" * target.x_rms_buf.size)

    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    pages_per_row = cfg.dim * Dtype.Float16_b.bpe // Dtype.Float16_b.tile_size
    target.set_device_input_source(target.x_row_buf, suffix="embed")
    self.gather_prog = embed_gather.build_program(
        self.table_buf.addr, self.token_buf.addr, target.x_row_buf.addr, 1, nb,
        1, dim_tiles, pages_per_row, core=core)
    self.gather_prog.name = "embed_token_to_qkv_x_row"

  def __call__(self, token: int, stats: dict) -> None:
    self.device.dram_write(self.token_buf, struct.pack("<I", token).ljust(self.token_buf.size, b"\0"))
    run_programs(self.device, (self.gather_prog,), stats)


class DeviceSwiGLU:
  """Staged device SiLU(gate) * up bridge feeding Wdown's input buffer."""

  def __init__(self, device, name: str, gate_gemv: DeviceNormGemv,
               up_gemv: DeviceNormGemv, out_buf):
    if gate_gemv.Np != up_gemv.Np:
      raise ValueError("SwiGLU gate/up outputs must have the same padded width")
    self.device = device
    self.out_buf = out_buf
    self.tiles = gate_gemv.Np // TILE
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    self.silu_fp = device.dram.alloc(
        self.tiles, dtype=Dtype.Float16_b,
        shape=(self.tiles, TILE, TILE), name=f"{name}.silu_fp")
    self.silu_row = device.dram.alloc(
        self.tiles, dtype=Dtype.Float16_b,
        shape=(self.tiles, TILE, TILE), name=f"{name}.silu_row")
    self.programs = [
      swiglu_bridge.build_row_silu_program(
          gate_gemv.c_buf.addr, self.silu_fp.addr, num_banks,
          core=core, tiles=self.tiles),
      swiglu_bridge.build_convert_program(
          "fp_to_row", self.silu_fp.addr, self.silu_row.addr, num_banks,
          core=core, tiles=self.tiles),
      build_two_source_binary(
          "mul", self.silu_row.addr, up_gemv.c_buf.addr, out_buf.addr,
          num_banks, core=core, tiles=self.tiles),
    ]
    for prog, suffix in zip(self.programs, ("row_silu", "fp_to_row", "mul")):
      prog.name = f"{name}_swiglu_{suffix}"

  def __call__(self, stats: dict) -> None:
    self.out_buf._host = None
    run_programs(self.device, self.programs, stats)


# --------------------------------------------------------------------------
# Full model
# --------------------------------------------------------------------------

class Llama:
  def __init__(
      self,
      model: Model,
      device=None,
      max_seq: int = 256,
      n_layers: int | None = None,
      device_attention: bool = False,
      fuse_row_to_rms: bool = False,
      allow_block_local_attention: bool = False,
  ):
    self.m, self.cfg, self.device = model, model.cfg, device
    self.n_layers = n_layers or self.cfg.n_layers
    self.max_seq = max_seq
    self.device_attention = bool(device is not None and device_attention)
    self.fuse_row_to_rms = bool(device is not None and fuse_row_to_rms)
    self.allow_block_local_attention = bool(allow_block_local_attention)
    c = self.cfg
    self.cos, self.sin = rope_tables(c)
    self.k_cache = np.zeros((self.n_layers, c.n_kv_heads, max_seq, c.head_dim), dtype=np.float32)
    self.v_cache = np.zeros_like(self.k_cache)
    self.k_cache_dev = []
    self.v_cache_dev = []
    self.k_updaters = {}
    self.attentions = {}
    self.embed_norm_inputs = None
    if device is not None:
      row_bytes = c.head_dim * Dtype.Float16_b.bpe
      if max_seq * row_bytes % Dtype.Float16_b.tile_size != 0:
        raise ValueError("device KV-cache scatter needs each KV head stride page-aligned")
      if c.head_dim // 2 != TILE:
        raise ValueError("device K updater expects RoPE cos/sin rows of 32 values")
      cache_tiles = c.n_kv_heads * max_seq * row_bytes // Dtype.Float16_b.tile_size
      self.cos_dev = device.alloc_write(
          kstage.rope.to_bf16_bytes(kstage.row_tile_table(self.cos[:max_seq])),
          dtype=Dtype.Float16_b,
          shape=(max_seq, TILE, TILE),
          name="rope_cos_rows",
      )
      self.sin_dev = device.alloc_write(
          kstage.rope.to_bf16_bytes(kstage.row_tile_table(self.sin[:max_seq])),
          dtype=Dtype.Float16_b,
          shape=(max_seq, TILE, TILE),
          name="rope_sin_rows",
      )
      for i in range(self.n_layers):
        k_buf = device.dram.alloc(cache_tiles, dtype=Dtype.Float16_b, name=f"l{i}.k_cache")
        device.dram_write(k_buf, b"\0" * k_buf.size)
        self.k_cache_dev.append(k_buf)
        buf = device.dram.alloc(cache_tiles, dtype=Dtype.Float16_b, name=f"l{i}.v_cache")
        device.dram_write(buf, b"\0" * buf.size)
        self.v_cache_dev.append(buf)
    self.norms = {n: model.f32(n).copy() for n in model.offsets if "norm" in n}
    mk_norm = (
        (lambda n, w, nw, xb: DeviceNormGemv(
            device, n, w, nw, c.norm_eps, xb,
            fuse_row_to_rms=self.fuse_row_to_rms))
        if device else
        (lambda n, w, _nw, _xb: HostGemv(w)))
    xbufs: dict = {}
    self.gemv = {}
    self.swiglus = {}
    t0 = time.time()
    for i in range(self.n_layers):
      qkv = np.concatenate([model.f32(f"l{i}.wq"), model.f32(f"l{i}.wk"), model.f32(f"l{i}.wv")], axis=0)
      if device is not None:
        self.gemv[f"l{i}.qkv"] = DeviceQkvGemv(
            device, f"l{i}.qkv", qkv, self.norms[f"l{i}.attn_norm"],
            c.norm_eps, xbufs, c, max_seq, self.v_cache_dev[i],
            fuse_row_to_rms=self.fuse_row_to_rms)
        if self.device_attention and i > 0:
          self.gemv[f"l{i}.qkv"].set_device_input_source(
              self.gemv[f"l{i - 1}.wdown"].next_buf, suffix="prev_wdown")
        self.k_updaters[i] = DeviceKCacheUpdater(
            device, f"l{i}", self.gemv[f"l{i}.qkv"], self.cos_dev, self.sin_dev,
            self.k_cache_dev[i], c, max_seq)
        if i == 0:
          self.embed_norm_inputs = DeviceTokenEmbeddingNormInputs(
              device, model, self.gemv[f"l{i}.qkv"])
      else:
        self.gemv[f"l{i}.qkv"] = HostGemv(qkv)
      self.gemv[f"l{i}.wo"] = (
          DeviceResidualGemv(device, f"l{i}.wo", model.f32(f"l{i}.wo"), xbufs)
          if device is not None else HostGemv(model.f32(f"l{i}.wo")))
      if device is not None:
        qkv_residual_src = self.gemv[f"l{i}.qkv"].device_input_row_buf or self.gemv[f"l{i}.qkv"].x_row_buf
        self.gemv[f"l{i}.wo"].set_device_residual_source(
            qkv_residual_src, suffix="qkv_x")
      if self.device_attention:
        self.attentions[i] = DeviceAttention(
            device, f"l{i}", self.gemv[f"l{i}.qkv"], self.cos_dev, self.sin_dev,
            self.k_cache_dev[i], self.v_cache_dev[i], self.gemv[f"l{i}.wo"], c, max_seq,
            allow_block_local=self.allow_block_local_attention)
      for w in ("wgate", "wup"):
        self.gemv[f"l{i}.{w}"] = mk_norm(
            f"l{i}.{w}", model.f32(f"l{i}.{w}"), self.norms[f"l{i}.ffn_norm"], xbufs)
      if self.device_attention:
        self.gemv[f"l{i}.wgate"].set_device_input_source(
            self.gemv[f"l{i}.wo"].next_buf, suffix="wo_next")
      self.gemv[f"l{i}.wdown"] = (
          DeviceResidualGemv(device, f"l{i}.wdown", model.f32(f"l{i}.wdown"), xbufs)
          if device is not None else HostGemv(model.f32(f"l{i}.wdown")))
      if device is not None:
        ffn_residual_src = self.gemv[f"l{i}.wgate"].device_input_row_buf or self.gemv[f"l{i}.wgate"].x_row_buf
        self.gemv[f"l{i}.wdown"].set_device_residual_source(
            ffn_residual_src, suffix="wgate_x")
        self.swiglus[i] = DeviceSwiGLU(
            device, f"l{i}", self.gemv[f"l{i}.wgate"], self.gemv[f"l{i}.wup"],
            self.gemv[f"l{i}.wdown"].x_buf)
    self.gemv["logits"] = mk_norm("logits", model.f32("embed"), self.norms["final_norm"], xbufs)  # tied head
    if self.device_attention:
      self.gemv["logits"].set_device_input_source(
          self.gemv[f"l{self.n_layers - 1}.wdown"].next_buf, suffix="last_wdown")
    where = "device (tilized GDDR)" if device else "host"
    print(f"[init] {self.n_layers} layers + tied head on {where} in {time.time() - t0:.1f}s")

  def sync_device_caches_from_host(self) -> None:
    """Upload host-prefill KV mirrors into the row-major device caches."""
    if self.device is None:
      return
    for i in range(self.n_layers):
      self.device.dram_write(self.k_cache_dev[i], to_bf16_device_bytes(self.k_cache[i]))
      self.device.dram_write(self.v_cache_dev[i], to_bf16_device_bytes(self.v_cache[i]))

  def forward(self, token: int, pos: int, stats: dict, want_logits: bool = True):
    c = self.cfg
    device_attention = self.device is not None and self.device_attention
    # The device-attention path gathers the token embedding and RoPE rows on
    # device. Keep host x/cos/sin only for fallback paths that still use them.
    x = None if device_attention else self.m.embed_row(token).copy()
    if not device_attention:
      cosp, sinp = self.cos[pos], self.sin[pos]
    for i in range(self.n_layers):
      if self.device is not None:
        if i == 0 and self.embed_norm_inputs is not None:
          self.embed_norm_inputs(token, stats)
          self.gemv[f"l{i}.qkv"].run_prefilled_norm(stats, pos=pos)
          qkv = None if self.device_attention else self.gemv[f"l{i}.qkv"].read_output()
        else:
          if self.device_attention:
            self.gemv[f"l{i}.qkv"].run_prefilled_norm(stats, pos=pos)
            qkv = None
          else:
            assert x is not None
            qkv = self.gemv[f"l{i}.qkv"](x, stats, pos=pos)
        self.k_updaters[i](stats, pos)
        if self.device_attention:
          self.attentions[i](stats, pos)
          self.gemv[f"l{i}.wo"].run_prefilled(stats, read_next=False)
        else:
          q_end, k_end = c.dim, c.dim + c.kv_dim
          q, k, v = qkv[:q_end], qkv[q_end:k_end], qkv[k_end:]
          q = rope_rotate(q, cosp, sinp, c.n_heads, c.head_dim)
          k = rope_rotate(k, cosp, sinp, c.n_kv_heads, c.head_dim)
          self.k_cache[i, :, pos] = quant_bf16(k.reshape(c.n_kv_heads, c.head_dim))
          self.v_cache[i, :, pos] = quant_bf16(v.reshape(c.n_kv_heads, c.head_dim))
          attn = attention(q, self.k_cache[i], self.v_cache[i], pos, c.n_heads, c.n_kv_heads, c.head_dim)
          x = self.gemv[f"l{i}.wo"](quant_bf16(attn), stats, residual=x)
      else:
        assert x is not None
        inv = rmsnorm_inv(x, c.norm_eps)
        xn = normed(x, self.norms[f"l{i}.attn_norm"], inv)
        qkv = self.gemv[f"l{i}.qkv"](xn, stats, pos=pos)
        q_end, k_end = c.dim, c.dim + c.kv_dim
        q, k, v = qkv[:q_end], qkv[q_end:k_end], qkv[k_end:]
        q = rope_rotate(q, cosp, sinp, c.n_heads, c.head_dim)
        k = rope_rotate(k, cosp, sinp, c.n_kv_heads, c.head_dim)
        self.k_cache[i, :, pos] = quant_bf16(k.reshape(c.n_kv_heads, c.head_dim))
        self.v_cache[i, :, pos] = quant_bf16(v.reshape(c.n_kv_heads, c.head_dim))
        attn = attention(q, self.k_cache[i], self.v_cache[i], pos, c.n_heads, c.n_kv_heads, c.head_dim)
        x = x + self.gemv[f"l{i}.wo"](quant_bf16(attn), stats)
      if self.device is not None:
        if self.device_attention:
          self.gemv[f"l{i}.wgate"].run_prefilled_norm(stats)
        else:
          self.gemv[f"l{i}.wgate"].run(x, stats)
        self.gemv[f"l{i}.wup"].run_prefilled(stats)
        self.swiglus[i](stats)
        if self.device_attention:
          self.gemv[f"l{i}.wdown"].run_prefilled(stats, read_next=False)
        else:
          x = self.gemv[f"l{i}.wdown"].run_prefilled(stats, residual=x)
      else:
        inv = rmsnorm_inv(x, c.norm_eps)
        xn = normed(x, self.norms[f"l{i}.ffn_norm"], inv)
        gate = self.gemv[f"l{i}.wgate"](xn, stats)
        up = self.gemv[f"l{i}.wup"](xn, stats)
        tmp = swiglu(gate, up)
        x = x + self.gemv[f"l{i}.wdown"](quant_bf16(tmp), stats)
    if not want_logits:
      return None
    if self.device is not None:
      if self.device_attention:
        self.gemv["logits"].run_prefilled_norm(stats)
        return self.gemv["logits"].read_output()
      return self.gemv["logits"](x, stats)
    inv = rmsnorm_inv(x, c.norm_eps)
    return self.gemv["logits"](normed(x, self.norms["final_norm"], inv), stats)


def fresh_stats() -> dict:
  return {
    "device_us": 0.0,
    "launches": 0,
    "submissions": 0,
    "weight_bytes": 0,
    "launch_by": {},
    "device_us_by": {},
  }


def summarize_launches(stats: dict, limit: int = 12) -> str:
  items = sorted(stats["launch_by"].items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
  return ", ".join(
      f"{name}:{count}/{stats['device_us_by'].get(name, 0.0) / 1e3:.2f}ms"
      for name, count in items)


def launch_category(name: str) -> str:
  if name.startswith("embed_"):
    return "embed"
  if "_attn_" in name:
    return "attention"
  if "_rms_" in name:
    return "rms_reduce"
  if name.endswith("_row_to_rms_fp"):
    return "row_to_rms"
  if name.endswith("_norm_w_times_inv") or name.endswith("_x_times_scale") or name.endswith("_times_scale"):
    return "norm_scale"
  if re.search(r"_c\d+$", name):
    return "gemv"
  if name.endswith("_residual_add"):
    return "residual_add"
  if name.endswith("_k_stage_rope_scatter"):
    return "k_stage_rope_scatter"
  if name.endswith("_k_stage_rope_src"):
    return "k_stage"
  if name.endswith("_rope_k_scatter"):
    return "k_rope_scatter"
  if "_swiglu_" in name:
    return "swiglu"
  return "other"


def summarize_launch_categories(stats: dict) -> str:
  counts: dict[str, int] = {}
  times: dict[str, float] = {}
  for name, count in stats["launch_by"].items():
    cat = launch_category(name)
    counts[cat] = counts.get(cat, 0) + count
    times[cat] = times.get(cat, 0.0) + stats["device_us_by"].get(name, 0.0)
  items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
  return ", ".join(f"{cat}:{count}/{times.get(cat, 0.0) / 1e3:.1f}ms" for cat, count in items)


def generate(
    llm: Llama,
    prompt: list[int],
    steps: int,
    check: Llama | None = None,
    prefill: Llama | None = None,
    launch_breakdown: bool = False,
    ignore_eos: bool = False,
) -> list[int]:
  out = list(prompt)
  decode_s, decode_n = 0.0, 0
  device_cache_synced = False
  for pos in range(len(prompt) + steps - 1):
    if pos >= llm.max_seq:
      print("[stop] max_seq reached")
      break
    tok, last_prefill = out[pos] if pos < len(out) else out[-1], pos >= len(prompt) - 1

    if prefill is not None and not last_prefill:
      prefill.forward(tok, pos, fresh_stats(), want_logits=False)
      llm.k_cache[:, :, pos] = prefill.k_cache[:, :, pos]
      llm.v_cache[:, :, pos] = prefill.v_cache[:, :, pos]
      if check is not None and check is not prefill:
        check.forward(tok, pos, fresh_stats(), want_logits=False)
      continue

    if (prefill is not None and not device_cache_synced and
        getattr(llm, "device_attention", False)):
      llm.sync_device_caches_from_host()
      device_cache_synced = True

    stats = fresh_stats()
    t0 = time.time()
    logits = llm.forward(tok, pos, stats, want_logits=last_prefill)
    wall = time.time() - t0
    if check is not None:
      ref = check.forward(tok, pos, fresh_stats(), want_logits=last_prefill)
      if last_prefill:
        pcc = float(np.corrcoef(logits, ref)[0, 1])
        match = "ok" if argmax(logits) == argmax(ref) else f"MISMATCH host={argmax(ref)}"
        print(f"  [check] pos {pos}: logits pcc={pcc:.5f} argmax {match}")
    if not last_prefill:
      continue
    nxt = argmax(logits)
    gbs = stats["weight_bytes"] / 1e9 / wall if wall else 0
    print(f"  pos {pos:3d} -> {nxt:6d}  {wall * 1e3:7.1f} ms ({1 / wall:5.2f} tok/s, "
          f"{gbs:5.1f} GB/s eff, {stats['launches']} launches/{stats.get('submissions', 0)} submits, "
          f"dev {stats['device_us'] / 1e3:.1f} ms)")
    if launch_breakdown:
      print(f"    launch groups: {summarize_launch_categories(stats)}")
      print(f"    launches: {summarize_launches(stats)}")
    decode_s += wall
    decode_n += 1
    if pos + 1 >= len(out):
      out.append(nxt)
    if nxt in EOS_TOKENS and not ignore_eos:
      break
  if decode_n:
    print(f"[tokens per second] {decode_n / decode_s:.2f} tok/s ({decode_n} tokens in {decode_s:.1f}s)")
  return out


# --------------------------------------------------------------------------

def main() -> int:
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("text", nargs="?", default="", help="chat message, e.g. llama3.py \"hello, how are you\"")
  ap.add_argument("--model", type=Path, default=DEFAULT_MODEL)
  ap.add_argument("--tokens", default="", help="comma-separated prompt token ids (bos included)")
  ap.add_argument("--prompt", default="", help="raw completion prompt (no chat template)")
  ap.add_argument("--steps", type=int, default=16)
  ap.add_argument("--max-seq", type=int, default=256)
  ap.add_argument("--layers", type=int, default=0, help="cap layer count (debug)")
  ap.add_argument("--host", action="store_true", help="pure-numpy golden run, no device")
  ap.add_argument("--fast", action="store_true",
                  help="host-math decode; device runs only GEMVs as one cached submission each")
  ap.add_argument("--ignore-eos", action="store_true", help="keep generating past EOS tokens")
  ap.add_argument("--check", action="store_true", help="run host golden alongside device, compare logits")
  ap.add_argument("--device-prefill", action="store_true", help="run prompt prefill on device too (CQ stress/debug)")
  ap.add_argument("--device-attention", action="store_true",
                  help="experimental: run first-tile decode attention on device instead of host attention")
  ap.add_argument("--allow-block-local-attention", action="store_true",
                  help="debug: allow device attention past pos 31 using block-local, not full-history, attention")
  ap.add_argument("--fuse-row-to-rms", action="store_true",
                  help="experimental: fold resident row-to-RMS conversion into the first RMS reduction")
  ap.add_argument("--launch-breakdown", action="store_true", help="print per-program launch counts per decode token")
  args = ap.parse_args()

  model = Model(args.model)
  print(f"[model] {args.model.name}: dim={model.cfg.dim} layers={model.cfg.n_layers} "
        f"vocab={model.cfg.vocab_size} theta={model.cfg.rope_theta} factor={model.cfg.rope_factor}")

  tokenizer = None
  if args.text:
    tokenizer = load_tokenizer()
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": args.text}], add_generation_prompt=True, return_dict=False)
    if isinstance(prompt, dict):
      prompt = prompt["input_ids"]
  elif args.prompt:
    tokenizer = load_tokenizer()
    prompt = [128000] + tokenizer.encode(args.prompt, add_special_tokens=False)
  elif args.tokens:
    prompt = [int(t) for t in args.tokens.split(",")]
  else:
    prompt = [128000, 791, 6864, 315, 9822, 374]  # "<bos>The capital of France is"
  print(f"[prompt] {prompt}")
  n_layers = args.layers or None

  if args.host:
    llm = Llama(model, None, args.max_seq, n_layers)
    out = generate(llm, prompt, args.steps, launch_breakdown=args.launch_breakdown,
                   ignore_eos=args.ignore_eos)
  else:
    from device import Device
    device = Device()
    try:
      if args.fast:
        llm = FastLlama(model, device, args.max_seq, n_layers)
      else:
        llm = Llama(
            model, device, args.max_seq, n_layers,
            device_attention=args.device_attention,
            fuse_row_to_rms=args.fuse_row_to_rms,
            allow_block_local_attention=args.allow_block_local_attention)
      host_prefill = None if args.device_prefill else Llama(model, None, args.max_seq, n_layers)
      check = host_prefill if args.check and host_prefill is not None else (
          Llama(model, None, args.max_seq, n_layers) if args.check else None)
      out = generate(llm, prompt, args.steps, check, host_prefill, args.launch_breakdown,
                     ignore_eos=args.ignore_eos)
    finally:
      device.close()

  print(f"[out] {out}")
  if tokenizer is None:
    try:
      tokenizer = load_tokenizer()
    except Exception:
      tokenizer = None
  if tokenizer is not None:
    print(f"[prompt_text] {tokenizer.decode(prompt, skip_special_tokens=True)}")
    print(f"[answer] {tokenizer.decode(out[len(prompt):], skip_special_tokens=True)}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
