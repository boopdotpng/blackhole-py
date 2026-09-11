import ctypes
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib

import numpy as np
from distributed.llama3.protocol import Packet, Sender, Receiver, DATA, ACK, MAX_PAYLOAD
from distributed.llama3.probe import decode_status, probe
from distributed.llama3.tp import column_parallel, row_parallel, plan, estimate


class ProtocolTest(unittest.TestCase):
    def test_sizes_and_corruption(self):
        for n in (0, 1, 16, 4096, MAX_PAYLOAD):
            p = Packet(DATA, 42, 1, 0, 1, payload=bytes(i%251 for i in range(n)))
            wire = p.encode()
            self.assertEqual(len(wire), 32+n)
            self.assertEqual(Packet.decode(wire), p)
            bad = bytearray(wire)
            bad[-1] ^= 1
            with self.assertRaises(ValueError): Packet.decode(bad)
            with self.assertRaises(ValueError): Packet.decode(wire[:-1])
        with self.assertRaises(ValueError): Packet(DATA, 1, 1, 0, 1, payload=bytes(8193)).encode()

    def test_loss_duplicate_and_timeout(self):
        s, r = Sender(0, 1, 42), Receiver(1, 0, 42, {3: 4096})
        wire = s.start(b'abc', 3, 0)
        self.assertIsNone(s.poll(0.001))
        self.assertEqual(s.poll(.02), wire)  # lost first DATA
        ack, delivered = r.receive(wire)
        self.assertEqual(delivered, b'abc')
        self.assertEqual(s.poll(.04), wire)  # lost ACK
        self.assertEqual(r.receive(wire), (ack, None))
        s.acknowledge(ack)
        with self.assertRaises(ValueError): s.acknowledge(ack)
        next_wire = s.start(b'next', 3, .05)
        self.assertEqual(r.receive(next_wire)[1], b'next')
        for t in (.1, .2, .3): s.poll(t)
        with self.assertRaises(TimeoutError): s.poll(.4)

    def test_wrong_session_rank_order_slot_and_wrap(self):
        r = Receiver(1, 0, 42, {3: 4})
        for p in (Packet(DATA, 43, 1, 0, 1, 3), Packet(DATA, 42, 1, 2, 1, 3),
                  Packet(DATA, 42, 2, 0, 1, 3), Packet(DATA, 42, 1, 0, 1, 4),
                  Packet(DATA, 42, 1, 0, 1, 3, payload=b'12345')):
            with self.assertRaises(ValueError): r.receive(p.encode())
        r.receive(Packet(DATA, 42, 1, 0, 1, 3, payload=b'a').encode())
        with self.assertRaises(ValueError): r.receive(Packet(DATA, 42, 1, 0, 1, 3, payload=b'b').encode())
        with self.assertRaises(ValueError): Packet(DATA, 42, 2**32, 0, 1).encode()

    @unittest.skipUnless(shutil.which('cc'), 'host C compiler unavailable')
    def test_c_python_interop(self):
        root = Path(__file__).resolve().parents[3]
        class CPacket(ctypes.Structure):
            _fields_ = [(n, ctypes.c_uint32) for n in ('epoch','sequence','length')] + [
                (n,ctypes.c_uint16) for n in ('source','destination','slot')] + [
                ('kind',ctypes.c_uint8),('hops',ctypes.c_uint8),('payload',ctypes.c_void_p)]
        with tempfile.TemporaryDirectory() as d:
            so = Path(d)/'bhp.so'
            subprocess.run(['cc','-shared','-fPIC','-Wall','-Wextra','-Werror',str(root/'fw/erisc/llama3/bhp.c'),'-o',str(so)], check=True)
            lib = ctypes.CDLL(str(so))
            lib.bhp_decode.argtypes = [ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(CPacket)]
            lib.bhp_encode.argtypes = [ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(CPacket)]
            for n in (0,1,4096,8192):
                wire = Packet(DATA,0x12345678,9,0,1,3,payload=bytes(i%251 for i in range(n))).encode()
                buf = ctypes.create_string_buffer(wire)
                p = CPacket()
                self.assertEqual(lib.bhp_decode(buf,len(wire),ctypes.byref(p)),0)
                out = ctypes.create_string_buffer(len(wire))
                self.assertEqual(lib.bhp_encode(out,len(wire),ctypes.byref(p)),len(wire))
                self.assertEqual(out.raw,wire)
                corrupt = bytearray(wire); corrupt[-1] ^= 1
                self.assertEqual(lib.bhp_decode(bytes(corrupt),len(wire),ctypes.byref(p)),-1)


class PlanTest(unittest.TestCase):
    def test_tp_math(self):
        rng = np.random.default_rng(3)
        x = rng.normal(size=(1,16)).astype(np.float32)
        up = rng.normal(size=(32,16)).astype(np.float32)
        down = rng.normal(size=(16,32)).astype(np.float32)
        parts = column_parallel(x, up)
        np.testing.assert_allclose(np.concatenate(parts,axis=-1),x@up.T,atol=1e-5)
        # Nonlinearity remains local to intermediate feature partitions.
        result = row_parallel([np.maximum(p,0) for p in parts],down) + x
        np.testing.assert_allclose(result,np.maximum(x@up.T,0)@down.T+x,rtol=1e-5,atol=1e-5)
        self.assertEqual(plan(0)['kv_heads'],[0,4])
        self.assertEqual(plan(1)['q_heads'],[16,32])
        e = estimate()
        self.assertEqual(e['sent_activation_bytes_per_rank'],262144)
        self.assertEqual(e['projection_weight_bytes'],2471493632)
        self.assertLess(estimate(latency_us=50)['baseline_scaled_steps_per_second'],e['baseline_scaled_steps_per_second'])

    def test_probe_guard_and_decode(self):
        with self.assertRaises(ValueError): probe(0)
        data = struct.pack('<32I',0xc0dea000,1,2,400,*([0]*28))
        self.assertEqual(decode_status(data)['port_status'],'up')
        with self.assertRaises(ValueError): decode_status(b'')

class MeshTest(unittest.TestCase):
    def test_routes_and_invalid_links(self):
        from distributed.llama3.mesh import routes
        topology = dict(version=1,epoch=42,ranks=[0,1,2],links=[
            dict(a=[0,4],b=[1,5]),dict(a=[1,6],b=[2,7])])
        table = routes(topology)
        self.assertEqual(table[0][2],dict(next_rank=1,port=4))
        self.assertEqual(table[2][0],dict(next_rank=1,port=7))
        topology['links'].append(dict(a=[0,4],b=[2,8]))
        with self.assertRaises(ValueError): routes(topology)
        topology['links'] = topology['links'][:1]
        with self.assertRaises(ValueError): routes(topology)
