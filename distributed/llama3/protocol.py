"""BHP1: our raw-Ethernet payload, with a stop-and-wait reference transport.

This module never opens hardware. CRC is for bring-up validation, not security.
"""
from dataclasses import dataclass
import struct
import zlib

MAGIC = b"BHP1"
VERSION = 1
DATA, ACK, PING = 1, 2, 3
MAX_PAYLOAD = 8192
HEADER = struct.Struct("<4sBBHIIHHHBBII")


@dataclass(frozen=True)
class Packet:
    kind: int
    epoch: int
    sequence: int
    source: int
    destination: int
    slot: int = 0
    hops: int = 1
    payload: bytes = b""

    def encode(self):
        if self.kind not in (DATA, ACK, PING) or not 0 < self.epoch < 2**32:
            raise ValueError("invalid kind or epoch")
        if not 0 < self.sequence < 2**32 or not 1 <= self.hops <= 255:
            raise ValueError("invalid sequence or hop limit")
        if any(not 0 <= v < 65536 for v in (self.source, self.destination, self.slot)):
            raise ValueError("rank/slot must be uint16")
        if len(self.payload) > MAX_PAYLOAD or (self.kind == ACK and self.payload):
            raise ValueError("invalid payload length")
        header = HEADER.pack(MAGIC, VERSION, self.kind, 0, self.epoch, self.sequence,
                             self.source, self.destination, self.slot, self.hops, 0,
                             len(self.payload), 0)
        crc = zlib.crc32(header[:28] + self.payload)
        return header[:28] + struct.pack("<I", crc) + self.payload

    @classmethod
    def decode(cls, data):
        if len(data) < HEADER.size:
            raise ValueError("short header")
        magic, version, kind, flags, epoch, seq, src, dst, slot, hops, reserved, size, crc = HEADER.unpack_from(data)
        if magic != MAGIC or version != VERSION or flags or reserved:
            raise ValueError("unsupported header")
        if size > MAX_PAYLOAD or len(data) != HEADER.size + size:
            raise ValueError("length mismatch")
        if zlib.crc32(data[:28] + data[32:]) != crc:
            raise ValueError("CRC mismatch")
        result = cls(kind, epoch, seq, src, dst, slot, hops, data[32:])
        result.encode()  # Apply exactly the same semantic checks on RX and TX.
        return result


class Receiver:
    """One ordered peer stream, session installed out of band by the host.

    ACK means staged into owned memory, not reduced. Duplicate DATA must never
    trigger a second reduction. The caller must consume `delivered` before
    invoking receive again; the device implementation must enforce slot credit.
    """
    def __init__(self, rank, peer, epoch, slots):
        self.rank, self.peer, self.epoch = rank, peer, epoch
        self.slots = dict(slots)  # slot -> owned capacity, not remote addresses
        self.expected = 1
        self.last = None

    def receive(self, wire):
        packet = Packet.decode(wire)
        if (packet.destination, packet.source, packet.epoch) != (self.rank, self.peer, self.epoch):
            raise ValueError("wrong peer or stale session")
        if packet.kind not in (DATA, PING):
            raise ValueError("expected DATA or PING")
        if packet.slot not in self.slots or len(packet.payload) > self.slots[packet.slot]:
            raise ValueError("unregistered slot or capacity exceeded")
        delivered = None
        if packet.sequence == self.expected:
            delivered = packet.payload
            self.last = packet
            self.expected += 1
        elif packet != self.last:
            raise ValueError("out of order or conflicting duplicate")
        ack = Packet(ACK, self.epoch, packet.sequence, self.rank, self.peer, packet.slot)
        return ack.encode(), delivered


class Sender:
    def __init__(self, rank, peer, epoch, timeout=0.01, max_retries=3):
        if timeout <= 0 or max_retries < 0:
            raise ValueError("invalid retry policy")
        self.rank, self.peer, self.epoch = rank, peer, epoch
        self.timeout, self.max_retries = timeout, max_retries
        self.sequence, self.pending = 1, None

    def start(self, payload, slot, now, kind=DATA):
        if self.pending is not None:
            raise RuntimeError("one outstanding packet per peer")
        if kind not in (DATA, PING):
            raise ValueError("sender accepts DATA or PING")
        packet = Packet(kind, self.epoch, self.sequence, self.rank, self.peer, slot, payload=payload)
        wire = packet.encode()
        self.pending, self.deadline, self.retries = packet, now + self.timeout, 0
        return wire

    def acknowledge(self, wire):
        packet = Packet.decode(wire)
        p = self.pending
        if p is None or packet != Packet(ACK, p.epoch, p.sequence, p.destination, p.source, p.slot):
            raise ValueError("unexpected ACK")
        self.pending = None
        self.sequence += 1  # encode rejects wrap: install a new epoch before wrap.

    def poll(self, now):
        if self.pending is None or now < self.deadline:
            return None
        if self.retries >= self.max_retries:
            raise TimeoutError("peer ACK timeout; abort session, do not recycle live buffers")
        self.retries += 1
        self.deadline = now + self.timeout
        return self.pending.encode()
