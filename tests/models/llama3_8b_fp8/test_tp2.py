from tests.models.topology import P150_WORKER_CORES
import unittest
from types import SimpleNamespace
import numpy as np
from st import TensorInfo
from distributed.tp2.checkpoint import shard_bytes
from distributed.tp2.runtime import Rank, reduce_residual, bf16_float, k
from distributed.tp2.fast import FastRank
from ttko.device import Device
from ttko.program import Dram
from pcie import P150_DRAM_ENDPOINTS
from fw.consts import TensixL1


class TP2Test(unittest.TestCase):
    def test_projection_reconstruction(self):
        rng = np.random.default_rng(18)
        for name, shape, axis in (
            ('q_proj', (32, 16), 0), ('k_proj', (8, 16), 0),
            ('v_proj', (8, 16), 0), ('o_proj', (16, 32), 1),
            ('gate_proj', (56, 16), 0), ('up_proj', (56, 16), 0),
            ('down_proj', (16, 56), 1),
        ):
            weight = rng.normal(size=shape).astype('<f4')
            info = TensorInfo(name + '.weight', 'F32', shape, 0, weight.nbytes)
            parts = [shard_bytes(info, weight.tobytes(), r) for r in (0, 1)]
            arrays = [np.frombuffer(data, '<f4').reshape(meta.shape) for meta, data in parts]
            np.testing.assert_array_equal(np.concatenate(arrays, axis=axis), weight)
            x = rng.normal(size=shape[1]).astype('f4')
            result = (np.concatenate([a @ x for a in arrays]) if axis == 0 else
                      sum(a @ v for a, v in zip(arrays, np.split(x, 2))))
            np.testing.assert_allclose(result, weight @ x, atol=1e-5)

    def test_fp8_bytes_and_scales(self):
        for dtype, itemsize in (('F8_E4M3', 1), ('BF16', 2)):
            data = bytes(range(128)) * itemsize
            info = TensorInfo('self_attn.o_proj.weight', dtype, (8, 16), 0, len(data))
            arrays = []
            for rank in (0, 1):
                meta, part = shard_bytes(info, data, rank)
                arrays.append(np.frombuffer(part, dtype=f'V{itemsize}').reshape(meta.shape))
            self.assertEqual(np.concatenate(arrays, axis=1).tobytes(), data)
        scale = np.array([0.02], '<f4').tobytes()
        info = TensorInfo('self_attn.q_proj.input_scale', 'F32', (1,), 0, 4)
        for rank in (0, 1): self.assertEqual(shard_bytes(info, scale, rank), (info, scale))
        with self.assertRaises(ValueError): shard_bytes(info, scale, 2)

    def test_reduction_rounds_after_sum_and_adds_residual_once(self):
        # Individually rounding these partials to BF16 loses the small result.
        a = np.full(4096, 256.25, '<f4').tobytes()
        b = np.full(4096, -256., '<f4').tobytes()
        residual = k._bf16_rne_bytes(np.ones(4096, 'f4'))
        np.testing.assert_array_equal(bf16_float(reduce_residual([a, b], residual)), 1.25)
        with self.assertRaises(ValueError): reduce_residual([a], residual)

    def make_rank(self, rank_type=Rank, rank_id=0):
        device = Device.__new__(Device)
        device.dram = Dram(8, P150_WORKER_CORES, P150_DRAM_ENDPOINTS)
        device.pcie = SimpleNamespace(cores=P150_WORKER_CORES)
        device.cq = SimpleNamespace(submit=lambda *a, **kw: None, noc=0, live=0)
        device.program_queue, device.read_queue = [], []
        device._resident_programs, device._param_templates = {}, {}
        def capture(params=None):
            if params:
                device._install_param_templates(tuple(device.program_queue), params)
            device.program_queue.clear()
        device.capture_trace = capture
        rank = rank_type.__new__(rank_type)
        rank.rank = rank_id
        rank.device, rank.published_fp8, rank.attention_cores = device, True, 16
        rank.checkpoint_scales = {
            f'model.layers.{i}.{module}.{kind}_scale': .01
            for i in range(32) for module in ('self_attn.q_proj','self_attn.k_proj',
                'self_attn.v_proj','self_attn.o_proj','mlp.gate_proj','mlp.up_proj','mlp.down_proj')
            for kind in ('input', 'weight')}
        rank._allocate()
        w = rank.layers[0]['weights']
        self.assertEqual(w['q'].shape, (2048, 4096))
        self.assertEqual(w['k'].shape, (512, 4096))
        self.assertEqual(w['o'].shape, (4096, 2048))
        self.assertEqual(w['gate'].shape, (7168, 4096))
        self.assertEqual(w['down'].shape, (4096, 7168))
        rank._build_programs()

        for program in rank.programs.values():
            self.assertLessEqual(program._l1.next, TensixL1.DATA_BUFFER_SPACE_END)
        self.assertLessEqual(device._param_template_next, TensixL1.KERNEL_CACHE_END)
        return rank

    def test_p150_lowering(self):
        rank = self.make_rank()
        self.assertEqual(len(rank.attention_traces), 32)
        self.assertEqual(len(rank.mlp_traces), 32)

    def test_resident_l1_ranks(self):
        for rank_id in (0, 1):
            rank = self.make_rank(FastRank, rank_id)
            self.assertEqual(rank.decode_launch_count, 226 if rank_id == 0 else 224)
            self.assertIn("collective_base", rank.programs["o"].params)
            self.assertIn("tp_worker_index", rank.programs["down"].params)


if __name__ == '__main__': unittest.main()
