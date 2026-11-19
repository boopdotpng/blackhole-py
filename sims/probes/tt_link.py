"""TT-link between two p150a cards: bandwidth and round-trip latency of ERISC1 data transfers on TX queue 2, with the
vendor base firmware running on ERISC0 (eth/e1_link.c, eth/e1.py). Needs both cards free and the QSFP-DD cables that
join them; nothing changes queue, MAC or PCS configuration, and every ERISC1 is parked again when the probe exits.

  python3 sims/probes/tt_link.py --output sims/results/<date>-tt-link.jsonl

Cases:
  size sweep   one direction (card 1 -> card 0, ch 11), 1 KiB .. 128 KiB per transfer, ~64 MiB per point
  duplex       both directions on ch 11 at once
  two links    one direction on ch 11 and ch 13 at once, then all four (both links, both directions)
  ping-pong    16-byte round trips card 1 -> card 0 -> card 1 on ch 11
Each data point checks the last transfer's bytes on the receiving card. E1 cycles are converted to time with a
clock rate calibrated against the host clock over the whole run (reported).
"""
import argparse, json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "eth"))
from e1 import E1, build
from system import PCIIface

# Sources and destinations must not overlap: in duplex runs a card's DST is written while its own SRC is being sent.
# Up to 128 KiB: SRC [0x40000, 0x60000), DST [0x50000, 0x70000); the base firmware owns 0x70000 and up.
BOX, SRC, DST, SCRATCH, PING = 0x30000, 0x40000, 0x50000, 0x30200, 0x30100
OP_SEND, OP_PING, OP_PONG = 1, 3, 4
MAGIC = 0xE1A11E4C
SIZES = [1 << 10, 4 << 10, 16 << 10, 64 << 10, 128 << 10]
TOTAL = 64 << 20


class Link:
  """E1 command loops on (card, ch) pairs. Peer of (card, ch) is (1 - card, ch)."""
  def __init__(self, devs, ends):
    self.devs, self.e1 = devs, {}
    image = build("e1_link.c")
    for card, ch in ends:
      e = E1(devs[card], ch)
      devs[card].write(e.core, BOX, bytes(64))
      e.start(image)
      self.e1[card, ch] = e
    for (card, ch), e in self.e1.items():
      t = time.time()
      while devs[card].read32(e.core, BOX) != MAGIC:
        if time.time() - t > 1: raise RuntimeError(f"E1 card {card} ch {ch} did not start")
    self.req = {k: 0 for k in self.e1}

  def issue(self, end, op, src, dst, n, rep):
    card, _ = end
    d, c = self.devs[card], self.e1[end].core
    for i, v in enumerate((op, src, dst, n, rep)): d.write32(c, BOX + 16 + 4 * i, v)
    self.req[end] += 1
    d.write32(c, BOX + 8, self.req[end])

  def wait(self, end, timeout=30):
    card, _ = end
    d, c, t = self.devs[card], self.e1[end].core, time.time()
    while d.read32(c, BOX + 12) != self.req[end]:
      if time.time() - t > timeout: raise RuntimeError(f"E1 {end} timed out")
    return d.read32(c, BOX + 36)

  def close(self):
    for e in self.e1.values(): e.stop()


def pattern(size, salt):
  return bytes((i * 131 + salt * 17 + (i >> 8)) & 0xFF for i in range(size))


def stream(link, devs, ends, size, salt):
  """Every end in ends sends TOTAL bytes (in size-byte transfers) to its peer at the same time."""
  rep = max(1, TOTAL // size)
  for card, ch in ends:
    devs[card].write(link.e1[card, ch].core, SRC, pattern(size, salt + card * 7 + ch))
    devs[1 - card].write(link.e1[card, ch].core, DST, bytes(size))
  t0 = time.perf_counter()
  for end in ends: link.issue(end, OP_SEND, SRC, DST, size, rep)
  cycles = {end: link.wait(end) for end in ends}
  host = time.perf_counter() - t0
  ok = all(devs[1 - card].read(link.e1[card, ch].core, DST, size) == pattern(size, salt + card * 7 + ch) for card, ch in ends)
  return rep, cycles, host, ok


def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--output", type=Path)
  a = ap.parse_args()
  devs = [PCIIface(0), PCIIface(1)]
  ends = [(c, ch) for c in (0, 1) for ch in (11, 13)]
  link = Link(devs, ends)
  rows = []
  def record(case, **kw):
    rows.append(dict(case=case, **kw))
    print(json.dumps(rows[-1]))
  try:
    # E1 clock: a long one-direction run, E1 cycles vs host seconds
    global TOTAL
    TOTAL, total = 1 << 30, TOTAL       # ~23 ms, so host-side issue and polling are well under 0.1%
    rep, cyc, host, ok = stream(link, devs, [(1, 11)], 64 << 10, 0)
    TOTAL = total
    hz = cyc[1, 11] / host
    record("clock", e1_cycles=cyc[1, 11], host_s=host, e1_mhz=hz / 1e6)
    for size in SIZES:
      rep, cyc, host, ok = stream(link, devs, [(1, 11)], size, 1)
      s = cyc[1, 11] / hz
      record("one_way", ch=11, src_card=1, size=size, transfers=rep, e1_cycles=cyc[1, 11], seconds=s,
             gbyte_s=rep * size / s / 1e9, cycles_per_transfer=cyc[1, 11] / rep, data_ok=ok)
    for size in (16 << 10, 64 << 10):  # duplex sizes stay within the 64 KiB SRC/DST split
      for name, group in (("duplex", [(1, 11), (0, 11)]), ("two_links", [(1, 11), (1, 13)]),
                          ("two_links_duplex", ends)):
        rep, cyc, host, ok = stream(link, devs, group, size, 2)
        per = {f"card{c}_ch{ch}": rep * size / (cyc[c, ch] / hz) / 1e9 for c, ch in group}
        record(name, size=size, transfers=rep, gbyte_s=per, total_gbyte_s=sum(per.values()), data_ok=ok)
    # ping-pong: card 1 pings, card 0 echoes
    n = 10000
    for c in (0, 1): devs[c].write(link.e1[c, 11].core, PING, bytes(16))
    link.issue((0, 11), OP_PONG, SCRATCH, PING, 0, n)
    link.issue((1, 11), OP_PING, SCRATCH, PING, 0, n)
    cyc = link.wait((1, 11)); link.wait((0, 11))
    record("ping_pong", ch=11, round_trips=n, e1_cycles=cyc, round_trip_us=cyc / n / hz * 1e6)
  finally:
    link.close()
    for d in devs: d.close()
  if a.output:
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with open(a.output, "a") as f:
      for r in rows: f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
  main()
