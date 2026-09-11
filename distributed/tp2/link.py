"""Lifecycle for diagnostic and persistent collective E1 TT-link services.

Queue 1 and its firmware-configured headers/classifier are preserved. The CLI
verifies payloads from the host; its timing is not a wire-bandwidth measurement.
"""
import argparse
import json
from pathlib import Path
import secrets
import time
from distributed.tp2.erisc import Tile, RESET, RESET_PC, END_PC, E0_RESET, E1_RESET, MAILBOX, CODE

TX_BUFFER, RX_BUFFER, CAPACITY = 0x50000, 0x54000, 16384
TXQ, RXQ = 0xffb91000, 0xffb95000


def until(predicate, timeout=2.):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise TimeoutError('Ethernet operation timed out')
        time.sleep(.0001)


class Link:
    def __init__(self, logical=9, *, service='transfer', producers=96):
        if logical not in (9, 11):
            raise ValueError('validated cabled endpoints are 9 and 11')
        if service not in ('transfer', 'collective') or not 1 <= producers <= 117:
            raise ValueError('invalid service configuration')
        image = (Path(__file__).parents[2] / f'fw/erisc/tp2/build/{service}.bin').read_bytes()
        if not image or len(image) > 4096:
            raise ValueError('invalid transfer image; run make -C fw/erisc')
        self.tiles, self.saved, self.resets = [], [], []
        self.sequence = [0, 0]
        self.pending = False
        try:
            for device in (0, 1):
                self.tiles.append(Tile(device, logical))
            for tile in self.tiles:
                reset = tile.u32(RESET)
                if not reset & E1_RESET or reset & E0_RESET or tile.u32(0x7cc04) != 1:
                    raise RuntimeError('expected trained link with idle E1 and running E0')
                if not tile.u32(TXQ) & 1 or not tile.u32(RXQ) & 2:
                    raise RuntimeError('queue 1 must already be configured for TT-link')
                if tile.u32(TXQ+8) & (1 << 16):
                    raise RuntimeError('queue 1 is busy')
                if tile.u32(TXQ+0x80) != 0x111:
                    raise RuntimeError('unexpected queue 1 header configuration')
                counter = tile.u32(TXQ+0x30)
                time.sleep(.02)
                if tile.u32(TXQ+0x30) != counter:
                    raise RuntimeError('another queue 1 producer is active')
                self.resets.append(reset)
            # Firmware peer identity must be reciprocal before sending anything.
            for index, tile in enumerate(self.tiles):
                peer = self.tiles[1-index]
                if (tile.read(0x7cfe4, 8) != peer.read(0x7cfc4, 8) or
                        tile.read(0x7cfe3, 1)[0] != logical):
                    raise RuntimeError('firmware peer identity mismatch')
                if (tile.u32(RXQ+0x44) & 255) != (peer.u32(RXQ+0x40) & 255):
                    raise RuntimeError('a previous transfer remains unacknowledged')
            for tile, reset in zip(self.tiles, self.resets):
                saved = {addr: tile.read(addr, size) for addr, size in (
                    (CODE, len(image)), (MAILBOX, 2048), (RESET_PC, 4), (END_PC, 4),
                    (TX_BUFFER, CAPACITY), (RX_BUFFER, CAPACITY),
                    (TXQ+0x14, 4), (TXQ+0x18, 4), (TXQ+0x1c, 4))}
                self.saved.append(saved)
                tile.write(MAILBOX, bytes(2048))
                tile.write(MAILBOX+24, producers)
                tile.write(CODE, image)
                tile.write(RESET_PC, CODE)
                tile.write(END_PC, CODE + len(image))
                tile.write(RESET, reset & ~E1_RESET)
                until(lambda: tile.u32(MAILBOX+16) == 0xe1000001)
        except BaseException:
            self.close()
            raise

    def transfer(self, source, payload):
        if source not in (0, 1) or not payload or len(payload) % 16 or len(payload) > CAPACITY:
            raise ValueError('source must be 0/1; payload must be 16..16384 bytes, aligned to 16')
        if self.pending: raise RuntimeError('an unacknowledged slot cannot be reused')
        if self.sequence[source] == 0xffffffff: raise RuntimeError('start a new session before sequence wrap')
        sender, receiver = self.tiles[source], self.tiles[1-source]
        receiver.write(RX_BUFFER, bytes(value ^ 255 for value in payload))
        sender.write(TX_BUFFER, payload)
        before_sequence = receiver.u32(RXQ+0x40) & 255
        self.sequence[source] += 1
        sequence = self.sequence[source]
        sender.write(MAILBOX+4, len(payload))
        started = time.perf_counter()
        self.pending = True
        sender.write(MAILBOX, sequence)
        def accepted():
            if sender.u32(MAILBOX+12):
                raise RuntimeError('E1 transfer service reported an error')
            return sender.u32(MAILBOX+8) == sequence
        until(accepted)
        # The raw-mode byte counter stays zero for TT-link on this firmware.
        # Require a fresh sequence, committed L1 and an exact payload match.
        until(lambda: (receiver.u32(RXQ+0x40) & 255) != before_sequence
              and receiver.u32(RXQ+0x50) == 0
              and receiver.read(RX_BUFFER, len(payload)) == payload)
        # Keep sender storage intact until its queue observes peer acknowledgement.
        ack = receiver.u32(RXQ+0x40) & 255
        until(lambda: (sender.u32(RXQ+0x44) & 255) == ack)
        self.pending = False
        return dict(source=source, destination=1-source, bytes=len(payload),
                    sequence=sequence, verified=True,
                    host_observed_us=(time.perf_counter()-started)*1e6)

    def close(self):
        try:
            for tile, reset, saved in zip(self.tiles, self.resets, self.saved):
                tile.write(RESET, reset)
                for addr, data in saved.items():
                    # A timed-out packet may still be retried by hardware. Retain
                    # its source/destination buffers until external recovery.
                    if self.pending and addr in (TX_BUFFER, RX_BUFFER, TXQ+0x14, TXQ+0x18, TXQ+0x1c):
                        continue
                    tile.write(addr, data)
        finally:
            for tile in self.tiles: tile.close()
            self.tiles = []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--logical', type=int, default=9)
    parser.add_argument('--output', type=Path, default=Path('validation/tp2-link.json'))
    args = parser.parse_args()
    link = Link(args.logical)
    rows = []
    try:
        for size in (16, 64, 4096, 8192, 16384):
            for source in (0, 1):
                rows.append(link.transfer(source, secrets.token_bytes(size)))
                print(json.dumps(rows[-1]), flush=True)
    finally:
        link.close()
    args.output.write_text(json.dumps(dict(logical=args.logical,
        transport='E1 C service / hardware TT-link queue 1',
        timing='host command/verification/ack polling; not wire latency', rows=rows), indent=2)+'\n')


if __name__ == '__main__': main()
