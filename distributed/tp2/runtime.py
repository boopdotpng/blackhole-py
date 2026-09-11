"""Actual two-P150 tensor-parallel decode, with a diagnostic host collective.

Each rank owns half the projection weights and KV cache. Attention and MLP
execute concurrently. FP32 O/down partials are summed before BF16 rounding,
then the BF16 residual is added once. This transport is a correctness baseline,
not the Ethernet implementation and not expected to beat single-card decode.
"""
import importlib.util
from pathlib import Path
import struct
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from distributed.tp2.checkpoint import ShardedCheckpoint
from ttko.program import DType

# A separate module keeps local head/MLP dimensions out of the single-card API.
_spec = importlib.util.spec_from_file_location(
    '_llama3_tp2_kernels', Path(__file__).parents[2] / 'examples/llama3_8b_fp8.py')
k = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = k
_spec.loader.exec_module(k)
k.Q_PROJ_DIM, k.KV_PROJ_DIM, k.MLP_DIM = 2048, 512, 7168
k.Q_HEADS, k.KV_HEADS, k.ROPE_CORES = 16, 4, 20
k.GQA_CONTEXT_SHAPE = (1, 2048)
k.KV_CACHE_STORAGE_SHAPE = (4, k.KV_CACHE_TILES_PER_HEAD, 1024)


def bf16_float(data):
    return (np.frombuffer(data, dtype='<u2').astype(np.uint32) << 16).view('<f4')


def reduce_residual(partials, residual):
    if len(partials) != 2 or any(len(p) != 4096 * 4 for p in partials):
        raise ValueError('expected two FP32 partials of width 4096')
    if len(residual) != 4096 * 2:
        raise ValueError('expected a BF16 residual of width 4096')
    total = np.frombuffer(partials[0], '<f4') + np.frombuffer(partials[1], '<f4')
    # Idealized CPU reference: preserve the projection/residual boundary, but
    # use IEEE RNE instead of emulating hardware pack/FPU rounding exactly.
    projected = bf16_float(k._bf16_rne_bytes(total))
    return k._bf16_rne_bytes(projected + bf16_float(residual))


class Rank(k.Llama3Decode):
    def __init__(self, path, rank, device):
        self.shard = ShardedCheckpoint(path, rank)
        self.rank = rank
        super().__init__(path, device, attention_cores=16)

    def _allocate(self):
        super()._allocate()
        self.partial = self.device.dram.buffer(
            'tp_partial', DType.F32, (1, 4096), None,
            global_address=True, tilized=False)
        self.partial_compact = self.device.dram.buffer(
            'tp_partial_compact', DType.F32,
            (k.LLAMA_CORES, (4096 + k.LLAMA_CORES - 1) // k.LLAMA_CORES),
            axis=0, cores=self.layers[0]['weights']['o'].cores)

    def _upload(self, buffer, tensor):
        buffer = self._weight_upload_buffers.get(buffer, buffer)
        started = time.perf_counter()
        info, data = self.shard.load(tensor)
        expected = 'F8_E4M3' if buffer.dtype is DType.FP8 else 'BF16'
        if info.shape != buffer.shape or info.dtype != expected:
            raise ValueError(f'shard/buffer mismatch for {tensor}: {info.shape} vs {buffer.shape}')
        if info.dtype == 'F8_E4M3':
            bits = np.frombuffer(data, np.uint8).copy()
            bits[(bits & 127) < 8] &= np.uint8(128)
            data = bits.tobytes()
        self.profile['weight_prepare_s'] += time.perf_counter() - started
        self._stage_upload(buffer, data)

    def _build_programs(self):
        w = self.layers[0]['weights']
        projection = k._decode_fused_projections
        self.programs = {
            'qkv': projection(self.x_a, ((w['q'], self.q_compact),
                (w['k'], self.k_compact), (w['v'], self.v_compact)), norm_weight=w['input_norm']),
            'attention': k.gqa_attention_fused(self.q_heads, self.layers[0]['key_cache'],
                self.layers[0]['value_cache'], self.context,
                rope_inputs=(self.q_compact, self.k_compact, self.v_compact, self.cos, self.sin),
                attention_cores=16),
            'o': projection(self.context, ((w['o'], self.partial_compact),), dense_output=self.partial),
            'gate': projection(self.x_b, ((w['gate'], self.gate), (w['up'], self.up)),
                swiglu_output=self.hidden_dense, norm_weight=w['post_norm']),
            'down': projection(self.hidden_dense, ((w['down'], self.partial_compact),),
                dense_output=self.partial),
            'lm': projection(self.x_a, ((self.lm_weight, self.logits),), norm_weight=self.final_norm),
        }
        self.device.cache_kernels(self.programs.values())
        self.attention_traces, self.mlp_traces = [], []
        for index, layer in enumerate(self.layers):
            weights = layer['weights']
            self._queue('qkv', tuple((w[n], weights[n]) for n in ('input_norm','q','k','v')),
                self._projection_scales(index, ('self_attn.q_proj','self_attn.k_proj','self_attn.v_proj')))
            self._queue('attention', ((self.layers[0]['key_cache'], layer['key_cache']),
                (self.layers[0]['value_cache'], layer['value_cache'])))
            self._queue('o', ((w['o'], weights['o']),),
                self._projection_scales(index, ('self_attn.o_proj',)))
            self.attention_traces.append(self.device.capture_trace(('start_pos','kv_blocks','valid_columns')))
            self._queue('gate', tuple((w[n], weights[n]) for n in ('post_norm','gate','up')),
                self._projection_scales(index, ('mlp.gate_proj','mlp.up_proj')))
            self._queue('down', ((w['down'], weights['down']),),
                self._projection_scales(index, ('mlp.down_proj',)))
            self.mlp_traces.append(self.device.capture_trace((f"{self.x_b.name}_decode_token",)))
        self._queue('lm')
        self.lm_trace = self.device.capture_trace((f"{self.x_a.name}_decode_token",))

    def stage(self, layer, attention, position, residual):
        self.device.write(self.x_a if attention else self.x_b, residual)
        self.device.run(timeout=30)
        if attention:
            self.attention_traces[layer].replay(dict(start_pos=position,
                kv_blocks=position // 32 + 1, valid_columns=position % 32 + 1))
        else:
            self.mlp_traces[layer].replay()
        return self.device.read(self.partial)

    def output(self, residual):
        self.device.write(self.x_a, residual)
        self.device.run(timeout=30)
        self.lm_trace.replay()
        compact = bf16_float(self.device.read(self.logits)).reshape(self.logits.shape)
        return np.concatenate([row[:n] for row, n in zip(compact, self.lm_weight.item_counts)])


class TensorParallelDecode:
    rank_type = Rank
    def __init__(self, path='weights/llama3-8b-fp8', devices=(0, 1)):
        if len(devices) != 2 or len(set(devices)) != 2:
            raise ValueError('two distinct devices are required')
        if k.WEIGHT_DTYPE is not DType.FP8 or k.ATTENTION_DTYPE is not DType.BF16:
            raise ValueError('TP requires FP8 projections and BF16 attention')
        self.ranks = []
        self.pool = ThreadPoolExecutor(max_workers=2)
        try:
            # Sequential startup keeps peak host staging memory bounded.
            for rank, device in enumerate(devices):
                self.ranks.append(self.rank_type(path, rank, device))
                print(f'Rank {rank} ready on card {device}', flush=True)
            source = self.ranks[0].shard.source
            self.embedding = source.load('model.embed_tokens.weight')[1]
        except BaseException:
            self.close()
            raise
        self.next_position = 0

    def decode(self, token, position, *, return_logits=False):
        if type(token) is not int or not 0 <= token < 128256:
            raise ValueError('invalid token')
        if position != self.next_position or not 0 <= position < 8192:
            raise ValueError('positions must be contiguous, starting at zero')
        residual = self.embedding[token * 8192:(token + 1) * 8192]
        started = time.perf_counter()
        collective_s = 0.
        for layer in range(32):
            for attention in (True, False):
                futures = [self.pool.submit(rank.stage, layer, attention, position, residual)
                           for rank in self.ranks]
                # Drain both jobs even on failure, before caller closes either device.
                partials, errors = [], []
                for future in futures:
                    try: partials.append(future.result())
                    except BaseException as error: errors.append(error)
                if errors: raise errors[0]
                before = time.perf_counter()
                residual = reduce_residual(partials, residual)
                collective_s += time.perf_counter() - before
        logits = self.ranks[0].output(residual)
        self.next_position += 1
        return dict(token=int(logits.argmax()), seconds=time.perf_counter() - started,
                    host_sum_seconds=collective_s,
                    logits=logits if return_logits else None)

    def close(self):
        self.pool.shutdown(wait=True)
        for rank in self.ranks:
            rank.close()
