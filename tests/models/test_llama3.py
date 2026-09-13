"""Host-side coverage of the shared Llama model configuration and CLI."""
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from examples.llama3 import Llama3Decode, Llama3Kernels, main
from ttko.program import DType, Dram


def test_fp8_checkpoint_loading_flushes_subnormals_only():
  weight = Dram().buffer('weight', DType.FP8, (1, 1024), global_address=True, tilized=False)
  data = bytes(range(256)) * 4
  info = SimpleNamespace(dtype='F8_E4M3', shape=weight.shape)
  expected = bytes(value & 128 if value & 127 < 8 else value for value in data)
  with patch('st.load', return_value=(info, data)):
    assert weight.from_safetensor('weight', 'checkpoint') == expected


@pytest.mark.parametrize('model,dtype', [('1b', 'bf16'), ('8b', 'bf16'), ('8b', 'fp8')])
def test_model_allocation_and_programs(model, dtype):
  runtime = Llama3Decode.__new__(Llama3Decode)
  runtime.kernels = Llama3Kernels(model, dtype)
  runtime.device = SimpleNamespace(dram=Dram(), cq=SimpleNamespace(noc=0, live=0))
  runtime.attention_cores = runtime.kernels.attention_cores
  runtime._allocate()
  assert (runtime.lm_storage is runtime.embedding_weight) == (model == '1b')
  assert runtime.lm_weight.dtype is DType.BF16
  for layer in runtime.layers:
    assert layer['weights']['q'].dtype is (DType.FP8 if dtype == 'fp8' else DType.BF16)
    assert not layer['weights']['q'].tilized
    assert layer['key_cache'].shape == runtime.kernels.KV_CACHE_STORAGE_SHAPE
  runtime._create_programs()
  for program in runtime.programs.values():
    program.lower()


def test_model_instances_keep_independent_rope_defaults():
  small = Llama3Kernels('1b')
  expected = small.rope_table(16)
  large = Llama3Kernels('8b')
  assert large.rope_table(16)[0].shape == (16, 128)
  assert small.rope_table(16)[0].shape == (16, 64)
  for actual, reference in zip(small.rope_table(16), expected):
    np.testing.assert_array_equal(actual, reference)


@pytest.mark.parametrize('args', [[], ['--model', '8b'], ['--model', '8b', '--dtype', 'fp8'],
                                  ['--model', '8b', '--prefill']])
def test_cli_dispatch(args):
  with patch.object(Llama3Kernels, 'run_decode_e2e', autospec=True) as run:
    main(args)
  kernels = run.call_args.args[0]
  assert kernels.model == ('8b' if args else '1b')
  assert kernels.dtype == ('fp8' if 'fp8' in args else 'bf16')
  assert run.call_args.kwargs['prefill'] == ('--prefill' in args)


@pytest.mark.parametrize('args', [['--dtype', 'fp8'], ['--prefill'],
  ['--model', '8b', '--dtype', 'fp8', '--prefill'], ['--steps', '0']])
def test_cli_rejects_unsupported_combinations_before_device_access(args):
  with patch('examples.llama3.Device') as device, pytest.raises(SystemExit) as error:
    main(args)
  assert error.value.code == 2
  device.assert_not_called()


@pytest.mark.parametrize('tokens', [[-1], [128256], [1.5], [[1, 2]], []])
def test_invalid_tokens_rejected_before_upload(tokens):
  runtime = Llama3Decode.__new__(Llama3Decode)
  runtime.kernels = Llama3Kernels()
  with pytest.raises(ValueError):
    runtime.load_tokens(tokens)
