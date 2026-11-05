"""Every number that differs between Llama 3.2 1B, Llama 3 8B BF16, and 8B FP8.

The kernels are identical for all three models. 1B and 8B differ only in the
dimensions below; FP8 additionally changes data types and enables the FP8
steps marked ``# FP8`` in kernels.py.

                      1B BF16        8B BF16        8B FP8
  embed_dim           2048           4096           4096
  head_dim            64             128            128
  layers              16             32             32
  mlp_dim             8192           14336          14336
  rope_factor         32.0           1.0            1.0
  LM head             = embedding    own weight     own weight (BF16, or FP8 per-row)
  projection_cores    88             88             96
  attention_cores     16             32             32
  weight_dtype        BF16           BF16           FP8 (E4M3, per-tensor scales)
  8B-only options     -              split          FP8 KV cache, FP8 LM head
                                     attention

Shared by all: 32 query heads, 8 KV heads (GQA groups of 4), 128256-token
vocabulary, 8192-token context, KV cache in 32-token blocks.
"""

from dataclasses import dataclass
import os

from program import DType


@dataclass(frozen=True)
class Llama3Config:
  model: str                   # "1b" or "8b"
  dtype: str                   # checkpoint weight format: "bf16" or "fp8"
  checkpoint: str

  # Model shape
  embed_dim: int
  head_dim: int
  layers: int
  mlp_dim: int
  rope_factor: float
  eos_token_ids: frozenset

  # Placement on the chip
  projection_cores: int        # workers that split every projection's output rows
  attention_cores: int         # 8/16/32 workers; each owns 32/cores query heads
  noc_split_x: int             # without port rotation: columns >= x read on NoC 1
  rotate_dram_ports: bool      # read weights on NoC 0 over all 3 ports per DRAM bank

  # Formats (all BF16 except in 8B FP8 mode)
  weight_dtype: DType
  attention_dtype: DType       # KV cache and attention operands
  lm_head_dtype: DType
  fp8_fidelity: int            # FPU fidelity phases for FP8 operands
  fp8_page_tiles: int          # FP8 weights: 1024-element tiles per DRAM page
  split_attention: bool        # 8B BF16: four workers per KV head for long contexts

  vocab_size = 128256
  q_heads = 32
  kv_heads = 8
  max_tokens = 8192            # RoPE table and KV cache length
  kv_block = 32                # attention streams the KV cache 32 tokens at a time
  rope_theta = 500000.0
  rope_low_freq_factor = 1.0
  rope_high_freq_factor = 4.0
  rope_original_max_position_embeddings = 8192

  @classmethod
  def create(cls, model="1b", dtype="bf16", *, projection_cores=None, attention_dtype=None,
             fp8_fidelity=None, noc_split_x=None, lm_head_dtype=None, split_attention=None):
    """Build a config; unset switches come from LLAMA_* environment variables."""
    env = os.environ.get
    if model not in ("1b", "8b"): raise ValueError("model must be 1b or 8b")
    if dtype not in ("bf16", "fp8"): raise ValueError("dtype must be bf16 or fp8")
    if model == "1b" and dtype == "fp8": raise ValueError("FP8 requires the published 8B checkpoint")
    fp8 = dtype == "fp8"

    if projection_cores is None and env("LLAMA_PROJECTION_CORES") is not None:
      projection_cores = int(env("LLAMA_PROJECTION_CORES"))
    if projection_cores is None: projection_cores = 96 if fp8 else 88
    if projection_cores not in (80, 88, 96, 104, 112, 117):
      raise ValueError("projection cores must be 80, 88, 96, 104, 112, or 117")
    if noc_split_x is None and env("LLAMA_NOC_SPLIT_X") is not None:
      noc_split_x = int(env("LLAMA_NOC_SPLIT_X"))
    # Columns 1-7 and 10-14 hold the workers, so x >= 7 puts about half the
    # cores on each NoC. Down is fastest when the split is even, for both dtypes
    # (8B FP8 down: 40% on NoC 1 154 us, 47% 142 us, 56% 158 us).
    if noc_split_x is None: noc_split_x = 7

    if attention_dtype is None: attention_dtype = env("LLAMA_ATTENTION_DTYPE", "bf16") if fp8 else "bf16"
    if attention_dtype not in ("bf16", "fp8"): raise ValueError("attention dtype must be bf16 or fp8")
    if not fp8 and attention_dtype == "fp8": raise ValueError("FP8 attention requires FP8 mode")
    if fp8_fidelity is None: fp8_fidelity = int(env("LLAMA_FP8_FIDELITY", "1")) if fp8 else 1
    if fp8_fidelity not in (1, 2): raise ValueError("FP8 fidelity must be 1 or 2")
    lm_head_dtype = lm_head_dtype or env("LLAMA_LM_HEAD_DTYPE", "bf16")
    if lm_head_dtype not in ("bf16", "fp8"): raise ValueError("LM head dtype must be bf16 or fp8")
    if lm_head_dtype == "fp8" and (model != "8b" or not fp8):
      raise ValueError("FP8 LM head requires 8B FP8 mode")
    fp8_page_tiles = int(env("LLAMA_FP8_PAGE_TILES", "2"))
    if fp8_page_tiles not in (1, 2, 4): raise ValueError("FP8 page tiles must be 1, 2, or 4")
    if split_attention is None: split_attention = env("LLAMA_SPLIT_ATTENTION", "0") == "1"
    if split_attention and (model != "8b" or attention_dtype != "bf16"):
      raise ValueError("split attention requires 8B with BF16 attention")

    small = model == "1b"
    as_dtype = lambda name: DType.FP8 if name == "fp8" else DType.BF16
    return cls(
      model=model, dtype=dtype,
      checkpoint="weights/llama3-1b" if small else f"weights/llama3-8b-{dtype}",
      embed_dim=2048 if small else 4096,
      head_dim=64 if small else 128,
      layers=16 if small else 32,
      mlp_dim=8192 if small else 14336,
      rope_factor=32.0 if small else 1.0,
      eos_token_ids=frozenset((128001, 128008, 128009) if small else (128001, 128009)),
      projection_cores=projection_cores,
      attention_cores=16 if small else 32,
      noc_split_x=noc_split_x,
      rotate_dram_ports=env("LLAMA_DRAM_PORTS", "1") != "0",
      weight_dtype=as_dtype(dtype),
      attention_dtype=as_dtype(attention_dtype),
      lm_head_dtype=as_dtype(lm_head_dtype),
      fp8_fidelity=fp8_fidelity,
      fp8_page_tiles=fp8_page_tiles,
      split_attention=bool(split_attention),
    )

  # Derived sizes. A "tile" is 1024 elements (32x32), the unit of every DRAM
  # page, circular buffer slot, and FPU operation.
  @property
  def embed_tiles(self): return self.embed_dim // 1024          # 2 (1B) / 4 (8B)
  @property
  def embed_tiles_shift(self): return self.embed_tiles.bit_length() - 1
  @property
  def q_dim(self): return self.embed_dim                         # 32 heads * head_dim
  @property
  def kv_dim(self): return self.kv_heads * self.head_dim         # 512 (1B) / 1024 (8B)
  @property
  def head_tiles(self): return self.head_dim // 32               # 32-wide feature tiles per head
  @property
  def cache_tiles_per_head(self): return self.max_tokens // self.kv_block * self.head_tiles
  @property
  def kv_cache_shape(self): return (self.kv_heads, self.cache_tiles_per_head, 1024)
  @property
  def context_shape(self): return (1, self.embed_dim)
