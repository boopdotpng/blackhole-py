"""Read total-board and ASIC watts with tt-smi's backend in a separate process.

Use the parent workspace's Python (tt-umd/tt-smi dependencies) and local tt-smi
source, whose INPUT_POWER support is newer than the installed CLI. No resets
are issued. The sampler releases only its own KMD power votes after discovery;
inference retains its independent votes. Records use the host monotonic clock.
"""
import argparse
import json
import fcntl
import os
from pathlib import Path
import signal
import struct
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--interval', type=float, default=.1)
    parser.add_argument('--smi-source', type=Path, default=Path(__file__).resolve().parents[2]/'tt-smi')
    args = parser.parse_args()
    if args.interval <= 0: parser.error('interval must be positive')
    sys.path.insert(0, str(args.smi_source))
    from tt_umd import TopologyDiscovery
    from tt_smi.constants import get_default_discovery_options
    from tt_smi.backend import TTSMIBackend
    descriptor, devices = TopologyDiscovery.discover(options=get_default_discovery_options())
    # UMD's legacy opens keep otherwise idle boards awake. KMD aggregates power
    # flags across open files (tt-kmd/chardev.c); zeroing OUR vote cannot remove
    # the inference process's flags. Validity=15 marks all flags as specified.
    # This is the KMD 2.9 SET_POWER_STATE layout, not an ARC global power command.
    for entry in Path('/proc/self/fd').iterdir():
        try: target = os.readlink(entry)
        except FileNotFoundError: continue
        if target.startswith('/dev/tenstorrent/'):
            payload = bytearray(struct.pack('<IIBBH14H',40,0,0,15,0,*([0]*14)))
            fcntl.ioctl(int(entry.name),0xfa0f,payload,True)
    backend = TTSMIBackend(devices=devices, umd_cluster_descriptor=descriptor,
                          fully_init=False, pretty_output=False)
    running = True
    def stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', buffering=1) as output:
        deadline = time.monotonic()
        while running:
            readings = []
            for index in devices:
                start = time.monotonic()
                telemetry = backend.get_smbus_board_info(index)
                def watts(key):
                    value = telemetry.get(key)
                    return int(value, 16) if value is not None else None
                readings.append(dict(device=int(backend.get_pci_device_id(index)),
                    bdf=backend.get_pci_bdf(index), monotonic=(start+time.monotonic())/2,
                    board_watts=watts('INPUT_POWER'), asic_watts=watts('TDP')))
            output.write(json.dumps(dict(monotonic=time.monotonic(), cards=readings))+'\n')
            deadline += args.interval
            time.sleep(max(0, deadline-time.monotonic()))


if __name__ == '__main__': main()
