"""Probe: which tiles does NIU ``NOC_BRCST_EXCLUDE`` (+0x2C) carve out of a multicast?

Port of the retired ``microbenching/noc/riscv_noc_mcast_exclude_probe.py``
(blackhole-py 20e7bef) to the tt-kmd runtime. One BRISC on ``source`` posts a
4-byte multicast write over ``rect`` with a given exclusion word; every rect
tile's scratch word is cleared at launch, then read back to see who got it.

Two candidate bit layouts are tested because the sources disagree:
  quad: stride_x[3:0] stride_y[7:4] x[13:8] y[19:14] dir_x[20] dir_y[21] en[22]
        (older NOC.mcast_exclude_quad)
  spec: x[7:0] y[13:8] dir_x[20] dir_y[21] en[22]  (boop-docs emulator spec)

Run: pytest tests/probes/test_mcast_exclude.py --bh-hardware -s
Knobs (env): PROBE_NOC=0|1, PROBE_RECT=x0,y0:x1,y1, PROBE_ANCHOR=x,y,
PROBE_SOURCE=x,y, PROBE_EXCLUDE=comma-separated raw words (overrides cases).
"""
import os

from asm import Asm, Cond
from firmware.consts import TensixL1
from ttko.noc import TidCounters, _endpoint, _packet

SCRATCH = TensixL1.DATA_BUFFER_SPACE_BASE
SOURCE_WORD = SCRATCH + 64
SETTLE_LOOPS = 4096


def _pair(text): return tuple(int(v, 0) for v in text.split(","))


def _rect(text):
  lo, hi = text.split(":")
  return _pair(lo), _pair(hi)


def quad(x, y, dx, dy, sx=1, sy=1):
  return (sx & 0xF) | (sy & 0xF) << 4 | (x & 0x3F) << 8 | (y & 0x3F) << 14 | dx << 20 | dy << 21 | 1 << 22


def spec(x, y, dx, dy):
  return (x & 0xFF) | (y & 0x3F) << 8 | dx << 20 | dy << 21 | 1 << 22


def sender_image(noc_index, start, end, marker, exclude):
  k = Asm("brisc", physical_regs=True)
  noc = k.noc_at(noc_index)
  k.write(SOURCE_WORD, marker)
  k.fence()
  with noc.transaction() as t:
    t._source_pending = True
    noc._wait_issue_safe(TidCounters.writes_outgoing(t.tid), 4)
    with k.scope():
      local, targets = k.reg(2)
      noc._local_coordinate(local)
      noc._rectangle(targets, noc.coordinate(*start), noc.coordinate(*end))
      noc._submit(
        _endpoint(SOURCE_WORD, local), _endpoint(SCRATCH, targets),
        _packet(t.tid, noc._packet_options("write", posted=True, multicast=True), 4,
                exclusions=exclude),
      )
  # Posted write: give delivery time before the host reads receivers.
  with k.scope():
    count = k.reg()
    k.li(count, SETTLE_LOOPS)
    with k.loop():
      k.addi(count, count, -1)
      k.break_(Cond(count, "==", 0))
  return {"brisc": k.lower()}


def run_case(bh, noc_index, source, start, end, marker, exclude):
  rect = [(x, y) for y in range(start[1], end[1] + 1) for x in range(start[0], end[0] + 1)]
  images = {source: sender_image(noc_index, start, end, marker, exclude)}
  images.update((core, {}) for core in rect)
  bh.launch_many_mapped(images, l1={SCRATCH: bytes(4), SOURCE_WORD: bytes(4)})
  return {core for core in rect
          if int.from_bytes(bh.read_l1(core, SCRATCH, 4), "little") == marker}


def grid(start, end, hits, source, anchor):
  rows = []
  for y in range(start[1], end[1] + 1):
    cells = []
    for x in range(start[0], end[0] + 1):
      c = "#" if (x, y) in hits else "."
      if (x, y) == anchor: c = "A" if c == "#" else "a"
      cells.append(c)
    rows.append(f"    y={y:2d} " + " ".join(cells))
  rows.insert(0, "         " + " ".join(f"{x % 10}" for x in range(start[0], end[0] + 1)))
  return "\n".join(rows)


def test_mcast_exclude(bh):
  dev = bh.device
  noc_index = int(os.environ.get("PROBE_NOC", "0"))
  start, end = _rect(os.environ.get("PROBE_RECT", "2,3:6,7"))
  anchor = _pair(os.environ.get("PROBE_ANCHOR", "4,5"))
  source = _pair(os.environ.get("PROBE_SOURCE", "%d,%d" % dev.cores[0]))
  rect = [(x, y) for y in range(start[1], end[1] + 1) for x in range(start[0], end[0] + 1)]
  missing = [c for c in (*rect, source) if c not in dev.cores]
  assert not missing, f"rect/source must be worker tiles; not workers: {missing}"
  assert source not in rect, "source must sit outside the rectangle"

  # Translated coordinates are what we target. For NoC1 the raw anchor mirrors.
  ax, ay = anchor
  anchors = {"translated": anchor}
  if noc_index == 1: anchors["noc1-raw"] = (16 - ax, 11 - ay)

  if "PROBE_EXCLUDE" in os.environ:
    cases = [(f"raw 0x{int(v, 0):06x}", int(v, 0)) for v in os.environ["PROBE_EXCLUDE"].split(",")]
  else:
    cases = [("none", 0)]
    for label, (x, y) in anchors.items():
      for layout, enc in (("quad", quad), ("spec", spec)):
        for dx in (0, 1):
          for dy in (0, 1):
            cases.append((f"{layout} {label} anchor=({x},{y}) dir_x={dx} dir_y={dy}", enc(x, y, dx, dy)))

  print(f"\nmcast exclude probe: tensix_enabled=0x{dev.pcie.tensix_enabled:x} noc={noc_index} "
        f"source={source} rect={start}->{end} ({len(rect)} tiles) anchor={anchor}")
  print("legend: # received  . excluded  A/a anchor tile (received/excluded)")
  for index, (name, exclude) in enumerate(cases):
    marker = 0x4D430000 | index
    hits = run_case(bh, noc_index, source, start, end, marker, exclude)
    missed = sorted(set(rect) - hits)
    print(f"\n[{name}] BRCST_EXCLUDE=0x{exclude:06x}  received {len(hits)}/{len(rect)}"
          f"  excluded: {' '.join(f'{x},{y}' for x, y in missed) or '-'}")
    print(grid(start, end, hits, source, anchor))
  assert run_case(bh, noc_index, source, start, end, 0x4D43FFFF, 0) == set(rect), \
    "baseline multicast must reach every tile"
