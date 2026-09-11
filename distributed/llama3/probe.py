"""Read card 1 ERISC firmware status without starting the compute runtime.

Only allocates a per-file PCIe TLB and reads L1; no reset, power-state ioctl,
firmware upload, TX command, classifier update, or link reinitialization.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import struct
import time

from pcie import TLBWindow

BOOT = 0x7CC00
PORT = {0: "unknown", 1: "up", 2: "down", 3: "unused"}
TRAIN = ["training", "skip", "pass", "internal_loopback", "external_loopback",
         "timeout_manual_eq", "timeout_anlt", "timeout_cdr_lock",
         "timeout_bist_lock", "timeout_link_up", "timeout_chip_info"]


def decode_status(raw):
    if len(raw) != 128:
        raise ValueError("expected the 128-byte eth_status_t")
    words = struct.unpack("<32I", raw)
    return dict(postcode=hex(words[0]), port_status=PORT.get(words[1], f"invalid:{words[1]}"),
                train_status=TRAIN[words[2]] if words[2] < len(TRAIN) else f"invalid:{words[2]}",
                train_speed_raw=words[3], heartbeat=list(words[28:32]), raw_words=list(words))


def probe(device=1, interval=0.1):
    # Deliberately do not make card 0 selectable while it is in use.
    if device != 1:
        raise ValueError("this bring-up probe is restricted to card 1")
    if not 0 < interval <= 10:
        raise ValueError("interval must be in (0, 10] seconds")
    sysfs = Path(f"/sys/class/tenstorrent/tenstorrent!{device}")
    card = (sysfs / "tt_card_type").read_text().strip()
    if card not in ("p150a", "p150b", "p150c"):
        raise ValueError(f"unsupported Ethernet topology: {card}")
    result = dict(device=device, card=card, timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  firmware=(sysfs / "tt_fw_bundle_ver").read_text().strip(),
                  coordinate_system="translated NoC0; 12 logical ETH endpoints (20..31,25)",
                  interval_seconds=interval, endpoints=[])
    fd = os.open(f"/dev/tenstorrent/{device}", os.O_RDWR | os.O_CLOEXEC)
    try:
        with TLBWindow(fd, (20, 25)) as win:
            def sample():
                out = []
                for logical in range(12):
                    win.target(0, (20 + logical, 25))
                    out.append(decode_status(win.read(BOOT, 128)))
                return out
            before = sample()
            time.sleep(interval)
            after = sample()
            for logical, (a, b) in enumerate(zip(before, after)):
                result["endpoints"].append(dict(logical=logical, noc=[20 + logical, 25],
                    before=a, after=b, heartbeat_changed=a["heartbeat"] != b["heartbeat"]))
    finally:
        os.close(fd)
    result["up_count"] = sum(e["after"]["port_status"] == "up" for e in result["endpoints"])
    result["interpretation"] = "Local firmware status only; no peer payload or reachability test performed."
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", type=int, choices=[1], default=1)
    parser.add_argument("--interval", type=float, default=0.1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(probe(args.device, args.interval), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")


if __name__ == "__main__":
    main()
