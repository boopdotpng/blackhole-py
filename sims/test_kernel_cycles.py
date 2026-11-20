"""Offline checks for per-tile timing, launch inputs and the two Blackhole NoCs."""

import heapq
from pathlib import Path
import struct

import pytest

from ttrv import build
from ttrv.cycles import Simulation, estimate
from ttrv.cycle_noc import route


def test_tile_role_intervals():
  kernel = build("""grid 2
fn brisc() {
  n = core.id + 1
  for i in 0..n { fence }
}
fn ncrisc() { fence }
""")
  report = estimate(kernel, startup="simultaneous")
  a, b = report["tiles"]
  assert [(t["x"], t["y"]) for t in (a, b)] == [(1, 2), (1, 3)]
  assert a["inactive"] == ["trisc0", "trisc1", "trisc2"]
  assert b["cores"]["brisc"]["cycles"] > a["cores"]["brisc"]["cycles"]
  for tile in (a, b):
    assert tile["cycles"] == tile["finish"] - tile["start"]
    for row in tile["cores"].values():
      assert sum(row["breakdown"].values()) == row["cycles"] == row["finish"] - row["start"]
    assert tile["cycles"] == max(row["cycles"] for row in tile["cores"].values())
  assert report["cycles"] == max(t["finish"] for t in (a, b))


def test_input_page_crossing():
  kernel = build("""grid 1
param input: u32[]
l1 data: u32[32]
fn brisc() {
  noc.read data, input[1008], n=32, wait
  for i in 0..data[16] { fence }
}
""")
  bindings = {"input": (1 << 63) | (12 << 56) | (7 * 4096)}

  def run(value):
    inputs = {"input": bytes(4096) + struct.pack("<I", value)}
    return estimate(kernel, bindings=bindings, inputs=inputs)["tiles"][0]["cores"]["brisc"]

  short, long = run(0), run(30)
  assert long["instructions"] > short["instructions"] + 30
  assert long["noc"]["read_bytes"] == 128
  assert long["noc"]["read_requests"] == 2
  noc = long["noc"]
  assert (
    sum(
      noc["read_" + stage + "_cycles_sum"]
      for stage in ("issue", "request_network", "credit_wait", "bank_queue", "endpoint_service", "return_network")
    )
    == noc["read_completion_cycles_sum"]
  )
  with pytest.raises(ValueError, match="missing launch bindings"):
    estimate(kernel)
  with pytest.raises(ValueError, match="exceeded"):
    estimate(kernel, bindings=bindings, max_cycles=10)


def test_noc_round_robin_chain():
  # arb.py chain4 on card 1 measured 7.6 / 7.6 / 15.3 / 30.5 bytes/cycle.
  sim = Simulation()
  counts = [0] * 4

  def offer(i):
    def delivered():
      counts[i] += 1

    sim.network.packet(0, (1 + i, 5), ((5, 6, 7, 10)[i], 5), 8192, delivered)
    sim.after(135, lambda: offer(i))

  for i in range(4):
    offer(i)
  while sim.time < 100000:
    sim.time, _, callback = heapq.heappop(sim.events)
    callback()
  rates = [n * 8192 / sim.time for n in counts]
  assert rates == pytest.approx([7.6, 7.6, 15.3, 30.5], rel=0.05)
  assert [link[-1] for link in route(0, (16, 11), (1, 2))] == [0, 0, 1, 1, 1]
  assert [link[-1] for link in route(1, (1, 2), (16, 11))] == [1, 1, 1, 0, 0]


def test_startup_refresh_and_inactive_roles(tmp_path, monkeypatch):
  import json
  from ttrv.cycles import firmware_fingerprint, startup_profile

  path = tmp_path / "firmware.json"
  path.write_text(
    json.dumps(
      dict(
        firmware_sha256=firmware_fingerprint(), role_offsets=dict(brisc=0, ncrisc=5, trisc0=15, trisc1=20, trisc2=25)
      )
    )
  )
  kernel = build("grid 1\nfn brisc() { fence }\nfn trisc1() { fence }")
  first = estimate(kernel, startup=path)["tiles"][0]
  second = estimate(kernel, startup="simultaneous", samples=3)["tiles"][0]
  assert first["cores"]["trisc1"]["start"] == 20
  assert second["cores"]["trisc1"]["start"] == 0
  assert first["cores"]["trisc1"]["cycles"] == second["cores"]["trisc1"]["cycles"]
  assert second["sampled_cycles"]["median"] == second["cycles"]
  data = json.loads(path.read_text())
  data["firmware_sha256"] = "old"
  path.write_text(json.dumps(data))
  with pytest.raises(ValueError, match="different worker firmware"):
    startup_profile(path)
  monkeypatch.setattr("ttrv.cycles.DEFAULT_STARTUP", path)
  offsets, source = startup_profile()
  assert set(offsets.values()) == {0}
  assert "unmeasured" in source


@pytest.mark.parametrize("noc", [0, 1])
def test_multicast_copies_only_the_addressed_rectangle(noc):
  from types import SimpleNamespace
  from ttrv import hw

  sim = Simulation()
  src = (1, 2)
  lo, hi = hw.coord(1, 2), hw.coord(2, 3)
  rect = hi << 12 | lo if noc else lo << 12 | hi
  sim.network.multicast(SimpleNamespace(xy=src), noc, rect, 0, 128, b"word", lambda: None)
  while sim.events:
    sim.time, _, cb = heapq.heappop(sim.events)
    cb()
  assert sim.memory(src).read(128, 4) == bytes(4)
  assert all(sim.memory(xy).read(128, 4) == b"word" for xy in [(1, 3), (2, 2), (2, 3)])
  assert sim.memory((2, 4)).read(128, 4) == bytes(4)


@pytest.mark.parametrize("operation", ["read", "write"])
def test_isolated_multipage_transfers(operation):
  import gzip
  import json
  from pathlib import Path

  path = Path(__file__).parent / "results" / f"2026-11-19-multipage-{operation}-card0.jsonl.gz"
  with gzip.open(path, "rt") as rows:
    for row in map(json.loads, rows):
      role = row["role"]
      width = row["size"] // 2
      operands = "local, input[0]" if operation == "read" else "input[0], local"
      kernel = build(
        f"grid 1\nparam input: bf16[]\nl1 local: bf16[{width}]\nfn {role}() {{ noc.{operation} {operands}, n={width}, wait }}"
      )
      pred = estimate(kernel, bindings=row["bindings"], samples=row["trials"])["tiles"][0]["cores"][role]
      assert pred["sampled_cycles"]["median"] == pytest.approx(row["cores"][0]["measured"], rel=0.03)


def test_worker_local_input():
  kernel = build("grid 2\nl1 retained: u32[4], keep\nfn brisc() { for i in 0..retained[0] { fence } }")
  a, b = estimate(kernel, tile_inputs={(1, 3, "retained"): struct.pack("<I", 16)})["tiles"]
  assert b["cores"]["brisc"]["instructions"] > a["cores"]["brisc"]["instructions"] + 16
  with pytest.raises(ValueError, match="outside the launch grid"):
    estimate(kernel, tile_inputs={(1, 4, "retained"): b"data"})
  with pytest.raises(ValueError, match="oversized L1 input"):
    estimate(kernel, tile_inputs={(1, 2, "retained"): bytes(17)})


def test_argmax_pack_values_against_hardware(monkeypatch):
  import gzip
  import json
  from pathlib import Path

  import numpy as np
  from ttrv.cycle_argmax import candidates, scan_vocab

  root = Path(__file__).resolve().parents[1]
  path = root / "examples/llama3/argmax.ttrv"
  kernel = build(path.read_text(), file=str(path))
  vocab = scan_vocab(kernel)
  assert vocab == 128256
  floats = np.random.default_rng(42).standard_normal(vocab, dtype=np.float32)
  random_bf16 = (floats.view(np.uint32) >> 16).astype("<u2").tobytes()
  with gzip.open(root / "sims/results/2026-11-19-argmax-edge-card0.jsonl.gz") as src:
    for row in map(json.loads, src):
      data = random_bf16 if row["case"] == "random" else bytes(2 * vocab)
      if row["case"].startswith("bits-"):
        data = struct.pack("<H", int(row["case"][5:], 16)) * vocab
      for i, captured in enumerate(row["candidates"]):
        first, end = i * vocab // 88, (i + 1) * vocab // 88
        page = data[2 * (first & ~31) : 2 * end]
        assert candidates(page, first % 32, end - first) == bytes.fromhex(captured)

      if row["case"] == "random":
        sim = Simulation()
        monkeypatch.setattr("ttrv.cycles.Simulation", lambda: sim)
        result = estimate(kernel, bindings=row["bindings"], inputs={"logits": data})
        assert result["tensor_values"] == "BF16 argmax candidate values"
        host_slot = row["bindings"]["tokens"] + 16
        assert sim.memory(("host", 0)).read(host_slot, 4) == struct.pack("<I", row["winner"])


def test_local_l0_coherence():
  from ttrv.cycles import Risc

  sim = Simulation()
  core = Risc(sim, (1, 2), "brisc", ())
  addr = 0x20000
  assert core.memory_op(addr, "lw", 0)[:2] == (0, 8)
  sim.memory((1, 2)).write(addr, struct.pack("<I", 17))
  assert core.memory_op(addr, "lw", 0)[:2] == (0, 2)
  core.memory_op(addr + 4, "sw", 3)
  assert core.memory_op(addr, "lw", 0)[:2] == (17, 8)


def test_clock_high_word_is_latched_by_low_read():
  from ttrv.cycles import Risc

  sim = Simulation()
  core = Risc(sim, (1, 2), "brisc", ())
  sim.time = (3 << 32) - 1
  assert core.memory_op(0xFFB121F0, "lw", 0)[:2] == (0xFFFFFFFF, 7)
  sim.time += 2
  assert core.memory_op(0xFFB121F8, "lw", 0)[0] == 2
  assert core.memory_op(0xFFB121F0, "lw", 0)[0] == 1
  assert core.memory_op(0xFFB121F8, "lw", 0)[0] == 3


@pytest.mark.parametrize("vocab", [166912, 248320])
def test_compiled_argmax_variants(vocab):
  from pathlib import Path
  from ttrv.cycle_argmax import scan_vocab

  p = Path(__file__).resolve().parents[1] / "examples/llama3/argmax.ttrv"
  kernel = build(p.read_text(), {"VOCAB": vocab}, str(p))
  assert scan_vocab(kernel) == vocab
  kernel.images["trisc1"] += bytes(4)
  assert scan_vocab(kernel) is None


def test_ncrisc_store_marker_preserves_payload_and_return(monkeypatch):
  import fw
  from sims.probes.role_cycles import instrument, mark_ncrisc_instruction
  from ttrv import hw, isa

  kernel = build("grid 1\nparam out: u32[]\nl1 data: u32[4]\nfn ncrisc() { noc.write out[0],data,n=4,wait }")
  stores = []
  for i, (word,) in enumerate(struct.iter_unpack("<I", kernel.images["ncrisc"])):
    ins = isa.rv_decode(word)
    if ins and ins[0] == "sw" and ins[1]["imm"] == hw.Cmd.CMD_CTRL:
      stores.append(4 * i)
  assert len(stores) == 1
  addr = fw.PROFILE_RECORD + 40
  stamped = instrument(mark_ncrisc_instruction(kernel, stores[0], addr), ordered=True)
  sim = Simulation()
  monkeypatch.setattr("ttrv.cycles.Simulation", lambda: sim)
  payload = bytes(range(16))
  estimate(stamped, bindings={"out": (1 << 63) | (12 << 56)}, tile_inputs={(1, 2, "data"): payload})
  mem = sim.memory((1, 2))
  begin, end = struct.unpack("<II", mem.read(fw.PROFILE_RECORD + 8, 8))
  (mid,) = struct.unpack("<I", mem.read(addr, 4))
  assert begin < mid < end
  assert sim.memory(("dram", 0)).read(0, 16) == payload


def test_simultaneous_ncrisc_small_writes():
  import gzip
  import json
  from pathlib import Path

  path = Path(__file__).parent / "results/2026-11-19-ncrisc-state-burst-card0.jsonl.gz"
  with gzip.open(path) as rows:
    row = next(r for r in map(json.loads, rows) if r["size"] == 64 and r["grid"] == 96)
  kernel = build("""grid 96
param input: u32[]
l1 result: u32[16]
fn ncrisc() {
  noc.write input[core.id * 4096], result, n=16, wait
}
""")
  prediction = estimate(kernel, bindings=row["bindings"], samples=3)
  for tile, measured in zip(prediction["tiles"], row["cores"], strict=True):
    assert (tile["x"], tile["y"]) == (measured["x"], measured["y"])
    cycles = tile["cores"]["ncrisc"]["sampled_cycles"]["median"]
    assert abs(cycles / measured["measured"] - 1) <= 0.03


# Steady iterations without DRAM traffic, whose per-iteration cost the sampled runs must reproduce.
SAMPLED_KERNEL = """grid 4
l1 data: u32[64]
shared { first, count = split(1024) }
fn brisc() {
  for row in first..first + count {
    data[row & 63] = data[0] + row
    fence
  }
}
fn ncrisc() {
  loop count { fence }
}
"""


def test_trip_count_metadata():
  kernel = build(SAMPLED_KERNEL)
  assert kernel.timing["trip_counts"] == ["count"]
  for role in ("brisc", "ncrisc"):
    assert "count" in kernel.timing["shared"][role]
  attention = build(
    (Path(__file__).resolve().parents[1] / "examples/llama3/attention.ttrv").read_text(),
    {"HEAD_TILES": 2},
    str(Path(__file__).resolve().parents[1] / "examples/llama3/attention.ttrv"),
  )
  assert {"live", "visits"} <= set(attention.timing["trip_counts"])


def test_sampled_estimate_matches_full_simulation():
  kernel = build(SAMPLED_KERNEL)
  full = estimate(kernel, sample_iterations=None)
  sampled = estimate(kernel, sample_iterations=16)
  assert "sampling" in sampled and "sampling" not in full
  for a, b in zip(full["tiles"], sampled["tiles"]):
    assert b["trip_counts"] == {"count": 256}
    for role, row in a["cores"].items():
      other = b["cores"][role]
      assert abs(other["cycles"] / row["cycles"] - 1) < 0.01, (a["x"], a["y"], role, row["cycles"], other["cycles"])
      assert sum(other["breakdown"].values()) == other["cycles"] == other["finish"] - other["start"]
      assert abs(other["instructions"] / row["instructions"] - 1) < 0.01
