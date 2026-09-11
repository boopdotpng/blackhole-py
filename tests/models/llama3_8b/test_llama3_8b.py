"""CPU checks for the 8B shape, tiling, RoPE, and sharded checkpoint contract."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from examples import llama3_8b as llama3
from llama_checkpoint import validate_checkpoint
from ttko.program import Buffer, DType
from st import Safetensor


class Llama8BTest(unittest.TestCase):
  def test_rope_matches_transformers(self):
    import torch
    from transformers import LlamaConfig
    from transformers.models.llama.modeling_llama import LlamaRotaryEmbedding
    config = LlamaConfig(hidden_size=4096, num_attention_heads=32,
                         rope_theta=500000.0, max_position_embeddings=8192)
    positions = torch.tensor([[0, 1, 7, 8, 15, 16, 31, 32, 4095, 8191]])
    reference = LlamaRotaryEmbedding(config=config)
    cos, sin = reference(torch.zeros(1, 1, 4096), positions)
    actual_cos, actual_sin = llama3.rope_table()
    np.testing.assert_allclose(actual_cos[positions[0]], cos[0].numpy(), atol=6e-4, rtol=0)
    np.testing.assert_allclose(actual_sin[positions[0]], sin[0].numpy(), atol=6e-4, rtol=0)

  def test_compact_offsets_match_face_layout(self):
    # The 8B Q shard crosses 32 elements; MLP shards cross several rows.
    for count in (9, 36, 123):
      buffer = Buffer('compact', 64, DType.BF16, (1, count), 0, ((1, 2),), 7)
      values = np.arange(count, dtype='<u2')
      # Independent layout reference, confined to tests. Runtime conversion is on device.
      raw = np.frombuffer(buffer.pad_data(values.tobytes()), dtype='<u2')
      packed = raw.reshape(-1, 2, 16, 2, 16).transpose(0, 1, 3, 2, 4).tobytes()
      for slot, expected in enumerate(values):
        offset = llama3._compact_slot_byte_offset(slot)
        self.assertEqual(struct.unpack_from('<H', packed, offset)[0], expected)

  def test_sharded_reader(self):
    with tempfile.TemporaryDirectory() as folder:
      root = Path(folder)
      mapping = {}
      for n in range(2):
        name, filename = f'tensor{n}', f'shard{n}.safetensors'
        header = json.dumps({name: {'dtype': 'BF16', 'shape': [2], 'data_offsets': [0, 4]}}).encode()
        (root / filename).write_bytes(struct.pack('<Q', len(header)) + header + bytes([n] * 4))
        mapping[name] = filename
      (root / 'model.safetensors.index.json').write_text(json.dumps({'weight_map': mapping}))
      reader = Safetensor(root)
      self.assertEqual(reader.load('tensor1')[1], bytes([1] * 4))
      (root / 'shard1.safetensors').write_bytes(b'truncated')
      with self.assertRaises(ValueError): Safetensor(root)

  def test_wrong_model_rejected_before_device_access(self):
    with tempfile.TemporaryDirectory() as folder:
      (Path(folder) / 'config.json').write_text('{"model_type": "llama", "hidden_size": 2048}')
      with patch('examples.llama3_8b.Device') as device:
        with self.assertRaisesRegex(ValueError, 'hidden_size'):
          llama3.Llama3Decode(folder)
        device.assert_not_called()


if __name__ == '__main__':
  unittest.main()
