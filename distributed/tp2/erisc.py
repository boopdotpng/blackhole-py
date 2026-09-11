"""Minimal E1 lifecycle test, preserving trained E0 firmware and queue state.

Uses the reset/PC register interface documented by Tenstorrent's local
tt-isa-documentation/BlackholeA0/EthernetTile/Samples/ethdump sample.
The machine code is generated here; it only increments a counter in L1.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import time
from ttko.isa import RV32, R
from pcie import TLBWindow

RESET, RESET_PC, END_PC = 0xffb121b0, 0xffb14008, 0xffb1400c
E0_RESET, E1_RESET = 0x800, 0x1000
MAILBOX, CODE = 0x60000, 0x61000


class Tile:
    def __init__(self, device, logical):
        if device not in (0, 1) or not 0 <= logical < 12:
            raise ValueError('invalid device/endpoint')
        card = Path(f'/sys/class/tenstorrent/tenstorrent!{device}/tt_card_type').read_text().strip()
        if card not in ('p150a', 'p150b', 'p150c'):
            raise ValueError('P150 required')
        self.fd = os.open(f'/dev/tenstorrent/{device}', os.O_RDWR | os.O_CLOEXEC)
        try: self.window = TLBWindow(self.fd, (20 + logical, 25))
        except BaseException:
            os.close(self.fd)
            raise

    def read(self, addr, size=4):
        base = addr & -self.window.SIZE
        if addr - base + size > self.window.SIZE:
            raise ValueError('read crosses TLB window')
        self.window.target(base)
        return self.window.read(addr - base, size)

    def u32(self, addr): return int.from_bytes(self.read(addr), 'little')

    def write(self, addr, data):
        if isinstance(data, int): data = struct.pack('<I', data)
        base = addr & -self.window.SIZE
        if addr - base + len(data) > self.window.SIZE:
            raise ValueError('write crosses TLB window')
        self.window.target(base)
        self.window.write(addr - base, data)
        self.window.read(addr - base, min(4, len(data)))  # complete posted write

    def close(self):
        self.window.close()
        os.close(self.fd)


def heartbeat_image():
    rv = RV32()
    words = [rv.lui(R.T0, MAILBOX), rv.addi(R.T1, R.ZERO, 0),
             rv.addi(R.T1, R.T1, 1), rv.sw(R.T1, R.T0), rv.fence(),
             rv.jal(R.ZERO, -12)]
    return struct.pack(f'<{len(words)}I', *words)


def heartbeat(device, logical=9):
    tile = Tile(device, logical)
    try:
        reset = tile.u32(RESET)
        if not reset & E1_RESET or reset & E0_RESET:
            raise RuntimeError('expected idle E1 in reset and running E0')
        if tile.u32(0x7cc04) != 1:
            raise RuntimeError('expected trained endpoint')
        image = heartbeat_image()
        saved = {addr: tile.read(addr, size) for addr, size in
                 ((CODE, len(image)), (MAILBOX, 4), (RESET_PC, 4), (END_PC, 4))}
        before = tile.read(0x7cc70, 16)
        try:
            tile.write(MAILBOX, 0)
            tile.write(CODE, image)
            tile.write(RESET_PC, CODE)
            tile.write(END_PC, CODE + len(image))
            tile.write(RESET, reset & ~E1_RESET)
            time.sleep(.02)
            first = tile.u32(MAILBOX)
            time.sleep(.02)
            second = tile.u32(MAILBOX)
            if first == second or not first:
                raise RuntimeError(f'E1 did not advance: {first}, {second}')
        finally:
            tile.write(RESET, reset)
            for addr, data in saved.items(): tile.write(addr, data)
        result = dict(device=device, logical=logical, first=first, second=second,
                      e1_heartbeat_pass=True, reset_restored=tile.u32(RESET) == reset,
                      e0_heartbeat_changed=before != tile.read(0x7cc70, 16),
                      link_up=tile.u32(0x7cc04) == 1,
                      packet_transfer_tested=False)
        if not all(result[n] for n in ('reset_restored','e0_heartbeat_changed','link_up')):
            raise RuntimeError(f'E1 restoration check failed: {result}')
        return result
    finally:
        tile.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', type=int, choices=(0, 1), required=True)
    parser.add_argument('--logical', type=int, default=9)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(heartbeat(args.device, args.logical), indent=2) + '\n'
    if args.output: args.output.write_text(result)
    print(result, end='')


if __name__ == '__main__': main()
