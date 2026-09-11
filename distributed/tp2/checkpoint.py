"""Byte-preserving TP=2 projection views of the calibrated FP8 checkpoint.

Embeddings, normalization, scalar calibration and (initially) LM head replicate.
Heads stay whole: Q 16/rank, KV 4/rank, with the original GQA ratio of four.
"""
from dataclasses import replace
import numpy as np
from llama_checkpoint import validate_checkpoint


def shard_axis(name):
    if name.endswith(('q_proj.weight', 'k_proj.weight', 'v_proj.weight',
                      'gate_proj.weight', 'up_proj.weight')):
        return 0
    if name.endswith(('o_proj.weight', 'down_proj.weight')):
        return 1
    return None


def shard_bytes(info, data, rank):
    if type(rank) is not int or rank not in (0, 1):
        raise ValueError('TP rank must be 0 or 1')
    axis = shard_axis(info.name)
    if axis is None:
        return info, data
    if len(info.shape) != 2 or info.shape[axis] % 2:
        raise ValueError(f'cannot split {info.name}: {info.shape}')
    itemsize = info.nbytes // int(np.prod(info.shape))
    array = np.frombuffer(data, dtype=f'V{itemsize}').reshape(info.shape)
    selection = [slice(None)] * 2
    size = info.shape[axis] // 2
    selection[axis] = slice(rank * size, (rank + 1) * size)
    array = array[tuple(selection)]
    result = array.tobytes()
    return replace(info, shape=array.shape, start=0, end=len(result)), result


class ShardedCheckpoint:
    def __init__(self, path, rank):
        if type(rank) is not int or rank not in (0, 1):
            raise ValueError('TP rank must be 0 or 1')
        self.source = validate_checkpoint(path)
        if 'model.layers.0.self_attn.q_proj.input_scale' not in self.source.tensors:
            raise ValueError('TP bring-up requires the calibrated published FP8 checkpoint')
        self.rank = rank

    def load(self, name):
        return shard_bytes(*self.source.load(name), self.rank)

    def manifest(self):
        tensors = {}
        for name, info in self.source.tensors.items():
            axis = shard_axis(name)
            shape = list(info.shape)
            if axis is not None:
                shape[axis] //= 2
            tensors[name] = dict(shape=shape, dtype=info.dtype, axis=axis,
                                 bytes=info.nbytes if axis is None else info.nbytes // 2)
        return dict(world_size=2, rank=self.rank, q_heads=16, kv_heads=4,
                    mlp_width=7168, tensors=tensors,
                    weight_bytes=sum(t['bytes'] for t in tensors.values()))
