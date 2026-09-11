"""Validate the exact checkpoint contract before opening a Blackhole device."""
import json
from pathlib import Path
from st import Safetensor

CONFIG = {
  'model_type': 'llama', 'hidden_size': 4096, 'intermediate_size': 14336,
  'num_hidden_layers': 32, 'num_attention_heads': 32, 'num_key_value_heads': 8,
  'vocab_size': 128256, 'max_position_embeddings': 8192,
  'rope_theta': 500000.0, 'rope_scaling': None, 'rms_norm_eps': 1e-5,
  'tie_word_embeddings': False, 'hidden_act': 'silu',
}


def expected_shapes():
  shapes = {
    'model.embed_tokens.weight': (128256, 4096),
    'lm_head.weight': (128256, 4096), 'model.norm.weight': (4096,),
  }
  for layer in range(32):
    for name, shape in {
      'input_layernorm': (4096,), 'post_attention_layernorm': (4096,),
      'self_attn.q_proj': (4096, 4096), 'self_attn.k_proj': (1024, 4096),
      'self_attn.v_proj': (1024, 4096), 'self_attn.o_proj': (4096, 4096),
      'mlp.gate_proj': (14336, 4096), 'mlp.up_proj': (14336, 4096),
      'mlp.down_proj': (4096, 14336),
    }.items():
      shapes[f'model.layers.{layer}.{name}.weight'] = shape
  return shapes


def validate_checkpoint(path='weights'):
  path = Path(path)
  config = json.loads(((path if path.is_dir() else path.parent) / 'config.json').read_text())
  for name, expected in CONFIG.items():
    if name not in config or config[name] != expected:
      raise ValueError(f'unsupported {name}: {config.get(name)!r}; expected {expected!r}')
  for name in ('attention_bias', 'mlp_bias'):
    if config.get(name, False):
      raise ValueError(f'{name} is unsupported')
  checkpoint = Safetensor(path)
  if config.get("quantization_config") == {"quant_method": "fp8", "activation_scheme": "static"}:
    import numpy as np
    shapes = expected_shapes()
    quantized = {name for name in shapes if name.startswith("model.layers.") and "_proj.weight" in name}
    scale_names = {name.removesuffix("weight") + suffix for name in quantized for suffix in ("input_scale", "weight_scale")}
    if set(checkpoint.tensors) != set(shapes) | scale_names:
      raise ValueError("published FP8 checkpoint tensor names do not match Llama 3 8B")
    for name, shape in shapes.items():
      info = checkpoint.info(name)
      dtype = "F8_E4M3" if name in quantized else "BF16"
      if info.shape != shape or info.dtype != dtype: raise ValueError(f"invalid published tensor {name}")
    for name in scale_names:
      info, data = checkpoint.load(name)
      if info.dtype != "F32" or info.shape not in ((), (1,)) or info.nbytes != 4:
        raise ValueError(f"invalid scale tensor {name}")
      value = float(np.frombuffer(data, dtype="<f4")[0])
      if not np.isfinite(value) or value <= 0: raise ValueError(f"invalid scale value {name}")
    return checkpoint
  if config.get('quantization_config'):
    raise ValueError('only the published calibrated FP8 checkpoint is supported')
  shapes = expected_shapes()
  if set(checkpoint.tensors) != set(shapes):
    raise ValueError('checkpoint tensor names do not match Llama 3 8B')
  for name, shape in shapes.items():
    info = checkpoint.info(name)
    if info.shape != shape or info.dtype != 'BF16':
      raise ValueError(f'{name}: expected BF16{shape}, got {info.dtype}{info.shape}')
  return checkpoint
