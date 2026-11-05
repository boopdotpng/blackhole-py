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
  LM head             = embedding    own weight     own weight (BF16)
  projection_cores    88             88             96
  attention_cores     16             32             32
  weight_dtype        BF16           BF16           FP8 (E4M3, per-tensor scales)
  split attention     -              from 511       from 511

Split attention (8B): from position 511 on, four workers per KV head each
attend to every fourth cache block, then a merge launch combines their FP32
(O, m, l) states. Shorter positions replay the unsplit trace.

Shared by all: 32 query heads, 8 KV heads (GQA groups of 4), 128256-token
vocabulary, 8192-token context, BF16 KV cache in 32-token blocks.
"""

from dataclasses import dataclass

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

  weight_dtype: DType          # BF16, or FP8 (E4M3, per-tensor scales) in 8B FP8 mode

  vocab_size = 128256
  q_heads = 32
  kv_heads = 8
  max_tokens = 8192            # RoPE table and KV cache length
  kv_block = 32                # attention streams the KV cache 32 tokens at a time
  rope_theta = 500000.0
  rope_low_freq_factor = 1.0
  rope_high_freq_factor = 4.0
  rope_original_max_position_embeddings = 8192
  # Projections read weights on NoC 0 and rotate across all three ports of
  # each DRAM bank (~483 -> 498 GB/s). The down projection instead splits
  # cores spatially: columns >= 7 read on NoC 1, about half the workers,
  # which measured fastest for it (8B FP8 down: 40% on NoC 1 154 us,
  # 47% 142 us, 56% 158 us).
  noc_split_x = 7
  fp8_page_tiles = 2           # FP8 weights: 1024-element tiles per 2 KiB DRAM page
  split_attention_from = 511   # first position decoded with split attention

  @classmethod
  def create(cls, model="1b", dtype="bf16", *, projection_cores=None):
    if model not in ("1b", "8b"): raise ValueError("model must be 1b or 8b")
    if dtype not in ("bf16", "fp8"): raise ValueError("dtype must be bf16 or fp8")
    if model == "1b" and dtype == "fp8": raise ValueError("FP8 requires the published 8B checkpoint")
    # DRAM bandwidth saturates around 88 cores; each extra core re-reads the
    # activation. 104 and 117 measured slower on both models.
    if projection_cores is None: projection_cores = 96 if dtype == "fp8" else 88
    if projection_cores not in (80, 88, 96, 104, 112, 117):
      raise ValueError("projection cores must be 80, 88, 96, 104, 112, or 117")

    small = model == "1b"
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
      weight_dtype=DType.FP8 if dtype == "fp8" else DType.BF16,
    )

  @property
  def split_attention(self): return self.model == "8b"   # long contexts: four workers per KV head

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
