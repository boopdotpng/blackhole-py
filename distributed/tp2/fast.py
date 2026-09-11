"""Resident two-card decode with Tensix/ERISC L1 exchanges over the cable."""
import struct
import time
from ttko.program import Program, Const, DType
from ttko import Dst
from ttko.fpu import Fpu
from ttko.pack import Pack
from ttko.cb import CB
from ttko.shard import specialize
from ttko.unpack import UnpackTarget
from ttko.sync import Sem, SemWait, Stall, sem_post, sem_wait, sem_get
from ttko.sfpu import SfpuFormat
from ttko.isa import R
from distributed.tp2.runtime import Rank, TensorParallelDecode, k
from distributed.tp2.link import Link, until

ETH = (29, 25)
TX_BUFFER, RX_BUFFER = 0x50000, 0x54000
PRODUCED, CONSUMED, READY = 0x60200, 0x60400, 0x60060


def _reduction(residual, output, head):
    p = Program(k.P100_WORKER_CORES[:32], residual, output,
                Const('collective_base', 0), Const('collective_offset', 1), fp32_dst=True)
    a, b = p.cb(DType.F32, depth=1), p.cb(DType.F32, depth=1)
    rounded, skip, result = [p.cb(DType.BF16, depth=1) for _ in range(3)]
    flag = p.l1(16, alignment=16)
    reader = p.brisc.noc_at(0)
    with p.brisc.scope():
        expected, offset, got = p.brisc.reg(3)
        p.brisc.read(expected, p.param_addr(p.param('collective_base')))
        p.brisc.read(offset, p.param_addr(p.param('collective_offset')))
        p.brisc.add(expected, expected, offset)
        loop = p.brisc._new_label('wait_peer_vector')
        p.brisc.label(loop)
        reader.read(READY, reader.coordinate(*ETH), flag, 4)
        p.brisc.read(got, flag)
        p.brisc.bne(got, expected, loop)
    for cb, address in ((a, TX_BUFFER), (b, RX_BUFFER)):
        CB.reserve_back(p.brisc, cb)
        k._zero_l1_words(p.brisc, cb.addr, cb.tile_size // 4)
        reader.read(address + head * 512, reader.coordinate(*ETH), cb.addr, 512)
        CB.push_back(p.brisc, cb)
    CB.reserve_back(p.brisc, skip)
    k._zero_l1_words(p.brisc, skip.addr, skip.tile_size // 4)
    with p.brisc.scope():
        address, coordinate = reader._dram_tile(residual, head // 8)
        k._add_constant(p.brisc, address, (head % 8) * 256)
        reader.read(address, coordinate, skip.addr, 256)
    CB.push_back(p.brisc, skip)
    # SrcA/SrcB unpack converts F32 to BF16. Load Dst directly so the
    # two partials retain FP32 precision until after their SUM.
    p.unpack.move(a, UnpackTarget.DST, tile=0)
    p.unpack.move(b, UnpackTarget.DST, tile=1)
    p.unpack.move_pair(rounded, skip)
    for _ in range(2):
        sem_post(p.trisc1, Sem.MATH_DONE)
        sem_wait(p.trisc1, Sem.UNPACK_TO_DEST, SemWait.STALL_ON_ZERO, Stall.SYNC)
        sem_get(p.trisc1, Sem.UNPACK_TO_DEST)
    add = p.sfpu.program()
    left = add.load(format=SfpuFormat.FP32, offset=0)
    right = add.load(format=SfpuFormat.FP32, offset=64)
    value = add.add(left, right)
    add.store(value, format=SfpuFormat.FP32, offset=0)
    p.sfpu.map(add.finish(), tile=0).publish()
    Fpu(p.trisc1, Dst(False)).binary('add', dst_tile=0).publish()
    p.pack.move(rounded, tile=0)
    Pack(p.trisc2, Dst(False)).move(result, tile=0)
    CB.wait_front(p.ncrisc, result)
    writer = p.ncrisc.noc_at(1)
    with p.ncrisc.scope():
        address, coordinate = writer._dram_tile(output, head // 8)
        k._add_constant(p.ncrisc, address, (head % 8) * 256)
        writer.write(result.addr, address, coordinate, 256, posted=False)
    CB.pop_front(p.ncrisc, result)
    # This worker has consumed both slots; return its generation-tagged credit.
    with p.ncrisc.scope():
        sequence, offset = p.ncrisc.reg(2)
        p.ncrisc.read(sequence, p.param_addr(p.param('collective_base')))
        p.ncrisc.read(offset, p.param_addr(p.param('collective_offset')))
        p.ncrisc.add(sequence, sequence, offset)
        credit_source = flag + (head % 4) * 4
        p.ncrisc.write(credit_source, sequence)
        p.ncrisc.noc_at(0).write(credit_source, CONSUMED + head * 4,
                               reader.coordinate(*ETH), 4, posted=False)
    return p


def reduction(residual, output):
    return specialize(lambda head: _reduction(residual, output, head),
                      k.P100_WORKER_CORES[:32], tuple(range(32)))


class FastRank(Rank):
    def _build_programs(self):
        w = self.layers[0]['weights']
        projection = k._decode_fused_projections
        endpoint = (*ETH, TX_BUFFER, PRODUCED)
        self.programs = {
            'qkv': projection(self.x_a, ((w['q'], self.q_compact),
                (w['k'], self.k_compact), (w['v'], self.v_compact)), norm_weight=w['input_norm']),
            'attention': k.gqa_attention_fused(self.q_heads, self.layers[0]['key_cache'],
                self.layers[0]['value_cache'], self.context,
                rope_inputs=(self.q_compact, self.k_compact, self.v_compact, self.cos, self.sin),
                attention_cores=16),
            'o': projection(self.context, ((w['o'], self.partial_compact),),
                dense_output=self.partial, eth_output=endpoint),
            'gate': projection(self.x_b, ((w['gate'], self.gate), (w['up'], self.up)),
                swiglu_output=self.hidden_dense, norm_weight=w['post_norm']),
            'down': projection(self.hidden_dense, ((w['down'], self.partial_compact),),
                dense_output=self.partial, eth_output=endpoint),
            'reduce': reduction(self.x_a, self.x_b),
        }
        if self.rank == 0:
            self.programs.update(lm=projection(self.x_a, ((self.lm_weight, self.logits),), norm_weight=self.final_norm),
                argmax=k.decode_argmax(self.logits, self.token_history, self.device.cq.noc + self.device.cq.live))
        self.device.cache_kernels(self.programs.values())
        for index, layer in enumerate(self.layers):
            weights = layer['weights']
            self._queue('qkv', tuple((w[n], weights[n]) for n in ('input_norm','q','k','v')),
                self._projection_scales(index, ('self_attn.q_proj','self_attn.k_proj','self_attn.v_proj')))
            self._queue('attention', ((self.layers[0]['key_cache'], layer['key_cache']),
                (self.layers[0]['value_cache'], layer['value_cache'])))
            self._queue('o', ((w['o'], weights['o']),),
                dict(self._projection_scales(index, ('self_attn.o_proj',)), collective_offset=index*2+1))
            self._queue('reduce', constants=dict(collective_offset=index*2+1))
            self._queue('gate', tuple((w[n], weights[n]) for n in ('post_norm','gate','up')),
                self._projection_scales(index, ('mlp.gate_proj','mlp.up_proj')))
            self._queue('down', ((w['down'], weights['down']),),
                dict(self._projection_scales(index, ('mlp.down_proj',)), collective_offset=index*2+2))
            self._queue('reduce', ((self.x_a, self.x_b), (self.x_b, self.x_a)),
                dict(collective_offset=index*2+2))
        params = ('start_pos', 'kv_blocks', 'valid_columns', 'collective_base')
        if self.rank == 0:
            self._queue('lm')
            self._queue('argmax', constants=dict(write_token=0))
            params += ('write_pos',)
        self.decode_launch_count = len(self.device.program_queue)
        self.trace = self.device.capture_trace(params)

    def run_token(self, position, embedding):
        self.device.write(self.x_a, embedding)
        self.device.run(timeout=30)
        params = dict(start_pos=position, kv_blocks=position//32+1,
                      valid_columns=position%32+1, collective_base=position*64)
        if self.rank == 0: params['write_pos'] = position+1
        return self.trace.replay(params, timeout=30, wait=False)


class L1TensorParallelDecode(TensorParallelDecode):
    rank_type = FastRank

    def __init__(self, path='weights/llama3-8b-fp8', devices=(0, 1)):
        if tuple(devices) != (0, 1):
            raise ValueError('L1 transport is validated for rank 0/card 0 and rank 1/card 1')
        self.link = None
        super().__init__(path, devices)
        try: self.link = Link(service='collective', producers=k.LLAMA_CORES)
        except BaseException:
            self.close()
            raise

    def decode(self, token, position, *, return_logits=False):
        if type(token) is not int or not 0 <= token < 128256:
            raise ValueError('invalid token')
        if position != self.next_position or not 0 <= position < 8191:
            raise ValueError('positions must be contiguous, starting at zero, below 8191')
        embedding = self.embedding[token*8192:(token+1)*8192]
        started = time.perf_counter()
        self.link.pending = True
        # Submit both devices before waiting; Python polling must not delay the
        # peer's first launch by a GIL scheduling interval.
        events = [(rank, rank.run_token(position, embedding)) for rank in self.ranks]
        errors = []
        for rank, event in events:
            try: rank.device.cq.wait(event, timeout=30, poll_interval=0.)
            except BaseException as error: errors.append(error)
        if errors:
            status = [tile.u32(0x6000c) for tile in self.link.tiles]
            raise RuntimeError(f'collective trace failed; ERISC errors={status}') from errors[0]
        for tile in self.link.tiles:
            until(lambda: tile.u32(0x60008) == (position+1)*64)
        self.link.pending = False
        rank = self.ranks[0]
        live = rank.device.cq.live + (position+1)*16
        result, = struct.unpack('<I', rank.device.pcie.sysmem.read(live, 4))
        elapsed = time.perf_counter()-started
        logits = None
        if return_logits:
            from distributed.tp2.runtime import bf16_float
            import numpy as np
            compact = bf16_float(rank.device.read(rank.logits)).reshape(rank.logits.shape)
            logits = np.concatenate([row[:n] for row, n in zip(compact, rank.lm_weight.item_counts)])
        self.next_position += 1
        return dict(token=result, seconds=elapsed, host_sum_seconds=0., logits=logits)

    def close(self):
        try: super().close()
        finally:
            if self.link is not None:
                self.link.close()
                self.link = None
