import unittest
import numpy as np
import torch
from fp8 import encode, decode, encode_hardware
from ttko.program import Buffer, DType
from pcie import P150_DRAM_ENDPOINTS


class FP8Test(unittest.TestCase):
  def test_conversion_matches_torch(self):
    values = np.random.default_rng(0).uniform(-448,448,100000).astype(np.float32)
    expected = torch.from_numpy(values).to(torch.float8_e4m3fn).view(torch.uint8).numpy()
    np.testing.assert_array_equal(encode(values),expected)
    bits=np.arange(256,dtype=np.uint8)
    expected=torch.from_numpy(bits).view(torch.float8_e4m3fn).float().numpy()
    np.testing.assert_allclose(decode(bits),expected,rtol=0,atol=0,equal_nan=True)

  def test_ties_and_saturation(self):
    positive=decode(np.arange(127,dtype=np.uint8))
    midpoint=(positive[:-1]+positive[1:])/2
    low=np.arange(126,dtype=np.uint8)
    np.testing.assert_array_equal(encode(midpoint),low+(low&1))
    np.testing.assert_array_equal(encode(np.array([-1000,1000,0.,-0.])),[254,126,0,128])
    for value in (float('nan'),float('inf'),-float('inf')):
      with self.assertRaises(ValueError): encode([value])

  def test_fp8_tiling_roundtrip(self):
    b=Buffer('fp8',0x100000,DType.FP8,(3,2048),0,((1,2),(2,2)),8,dram_endpoints=P150_DRAM_ENDPOINTS)
    values=np.random.default_rng(3).normal(size=b.shape).astype(np.float32)
    data=b.from_numpy(values)
    self.assertEqual(len(data),3*2048)
    self.assertEqual(b.tile_size,1024)
    self.assertEqual(b.unpad_data(b.pad_data(data)),data)
    np.testing.assert_array_equal(b.to_numpy(data),decode(encode_hardware(values)))

class PublishedCheckpointTest(unittest.TestCase):
  def test_mixed_checkpoint_and_invalid_scales(self):
    import json, struct, tempfile
    from pathlib import Path
    from unittest.mock import patch
    from llama_checkpoint import CONFIG, validate_checkpoint
    name = 'model.layers.0.self_attn.q_proj.weight'
    shapes = {name:(1,1), 'lm_head.weight':(1,1)}
    def write(root, scale):
      tensors = [(name,'F8_E4M3',(1,1),b'\x38'), ('lm_head.weight','BF16',(1,1),b'\x80\x3f')]
      for suffix in ('input_scale','weight_scale'):
        tensors.append((name.removesuffix('weight')+suffix,'F32',(1,),struct.pack('<f',scale)))
      data, header = bytearray(), {}
      for key,dtype,shape,raw in tensors:
        start=len(data); data.extend(raw)
        header[key]={'dtype':dtype,'shape':shape,'data_offsets':[start,len(data)]}
      raw=json.dumps(header).encode()
      (root/'model.safetensors').write_bytes(struct.pack('<Q',len(raw))+raw+data)
    with tempfile.TemporaryDirectory() as folder, patch('llama_checkpoint.expected_shapes',return_value=shapes):
      root=Path(folder)
      (root/'config.json').write_text(json.dumps({**CONFIG,'quantization_config':{'quant_method':'fp8','activation_scheme':'static'}}))
      write(root,.125)
      self.assertEqual(validate_checkpoint(root).info('lm_head.weight').dtype,'BF16')
      for scale in (0.,-1.,float('nan'),float('inf')):
        write(root,scale)
        with self.assertRaisesRegex(ValueError,'invalid scale value'):validate_checkpoint(root)


if __name__=='__main__':unittest.main()
