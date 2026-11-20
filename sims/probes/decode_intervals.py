"""Capture isolated decode or prefill kernels from the model graph on card 0, with their actual argument blocks.

Capture uses the checkpoint and card. Replay uses only the recorded image and argument bytes.
The timing simulator's numerical data defaults apply on replay.
"""

import argparse
from collections import defaultdict
from contextlib import ExitStack
import csv
from copy import copy
from dataclasses import replace
import gzip
import json
from math import comb
from functools import lru_cache
from pathlib import Path
from statistics import median
import struct
import sys
from time import monotonic_ns
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ttrv.cycles import estimate, firmware_fingerprint


def model_graphs(a, dev):
  from examples.llama3 import ROOT, load
  from examples.nanbeige import DEFAULT, Nanbeige
  from examples.qwen38 import DEFAULT as QWEN, METADATA, Qwen38

  if a.model == "qwen38":
    model = Qwen38(QWEN, METADATA, dev, a.pos + max(1, a.rows))
  elif a.model == "nanbeige":
    model = Nanbeige(DEFAULT, dev, a.pos + max(1, a.rows))
  else:
    model = load(ROOT / "weights" / ("llama3-" + a.model), dev)
  graphs = [model.step] + ([model.readout] if hasattr(model, "readout") else [])
  for pos in range(a.pos):
    for graph in graphs:
      graph(**{k: pos if k == "pos" else 0 for k in graph.graph.vars}).wait()
  if a.rows:
    graphs = [model.make_prompt().capture(a.rows)]
  return graphs


def variable(name, position):
  if name.startswith("row_"):
    return position + int(name[4:])
  if name.startswith("p") and name[1:].isdigit():
    return position + int(name[1:])
  return {"pos": position, "write_token": 0}[name]


def bound_launch(launch, position):
  kernel, block, variables = launch
  data = bytearray(block)
  for var, offsets in variables.items():
    for offset in offsets:
      struct.pack_into("<I", data, offset, variable(var.name, position))
  return kernel, bytes(data), {}


def installed_kernel(runtime):
  from ttrv import compile_program

  c, m = runtime.compiled, runtime.program.manifest
  if c.manifest != m:
    keep = [v for v in m["storage"].values() if v.get("keep")]
    ceiling = max((v["address"] + v["size"] for v in keep), default=m["keep_base"])
    c = compile_program(c.program, ceiling)
    if c.manifest != m:
      raise ValueError(f"cannot reconstruct installed layout for {runtime.name}")
  return c


def capture_target(a):
  from role_cycles import Device, blackhole_build_grid_program, fw, instrument, mark_ncrisc_instruction, measure
  from ops_blackhole import dram
  from ttrv.cycle_argmax import scan_vocab
  from ttrv.runtime import Graph

  g, i = a.launch
  record = None
  addr = fw.PROFILE_RECORD
  for rep in range(a.repeats + 1):
    # Reconstruct the initial DRAM and persistent L1 state. Repeating just a residual
    # add or GDN update would change its inputs.
    dev = Device(a.device)
    try:
      graphs = model_graphs(a, dev)
      if not (0 <= g < len(graphs) and 0 <= i < len(graphs[g].launches)):
        raise ValueError("requested launch is outside the graph")
      graph = graphs[g]
      runtime, block, _ = bound_launch(graph.launches[i], a.pos)
      c = installed_kernel(runtime)
      m = c.manifest
      run = copy(runtime)
      if rep == 0:
        blank = replace(c, images={role: fw.ret(role) for role in c.images})
        raw, _ = measure(run, blank, block, a.repeats, ordered=True)
        overhead = {key: median(times) - 1 for key, times in raw.items()}
        record = dict(
          name=runtime.name,
          model=a.model,
          position=a.pos,
          rows=a.rows,
          measurement="graph prefix, fenced second clock read",
          graph_index=g,
          launch_index=i,
          card=a.device,
          firmware=firmware_fingerprint(),
          manifest=m,
          args=block.hex(),
          images={r: data.hex() for r, data in c.images.items()},
          tiles=[
            dict(x=x, y=y, roles={k: [] for k in c.images}, cycles=[]) for x, y in dev.dev.workers[: runtime.grid]
          ],
        )
        continue
      previous = bytearray.fromhex(record["args"])
      for param in m["params"].values():
        if param["kind"] == "host":
          offset = 4 * param["slot"]
          previous[offset : offset + 8] = block[offset : offset + 8]
      if bytes(previous) != block or record["images"] != {r: data.hex() for r, data in c.images.items()}:
        raise ValueError(f"installed image or device arguments changed across repetitions for {runtime.name}")
      vocab = scan_vocab(c)
      if a.mark_ncrisc_instruction is not None:
        c = mark_ncrisc_instruction(c, a.mark_ncrisc_instruction, addr + 40)
        record["marked_pc"] = a.mark_ncrisc_instruction
        for t in record["tiles"]:
          dev.dev.iface.write((t["x"], t["y"]), addr + 40, bytes(4))
      run.program = blackhole_build_grid_program(
        dev.dev, runtime.grid, instrument(c, addr, ordered=True).images, c.args_size
      )
      for previous_graph in graphs[:g]:
        previous_graph(**{name: variable(name, a.pos) for name in previous_graph.graph.vars}).wait(120)
      prefix = [bound_launch(prior, a.pos) for prior in graph.launches[:i]]
      graph_run = Graph(dev, [*prefix, (run, block, {})])
      before = monotonic_ns()
      graph_run().wait(120)
      # Host elapsed time at 2 GHz bounds every per-worker interval on this 1.35 GHz card.
      cycle_limit = 2 * (monotonic_ns() - before)
      if vocab and rep == 1:
        # The final launch reads logits and writes the token. Its input remains available.
        param = m["params"]["logits"]
        (encoded,) = struct.unpack_from("<I", block, 4 * param["slot"])
        address = dram((encoded & ~7) * 8 + (encoded & 7) * param["page"], param["page"])
        logits = bytearray(2 * vocab)
        dev.dev.allocator._copyout(logits, address)
        record["inputs"] = {"logits": logits.hex()}
      for t in record["tiles"]:
        xy = t["x"], t["y"]
        data = dev.dev.iface.read(xy, addr, 8 * len(fw.ROLES))
        spans = []
        reference = None
        for role in c.images:
          begin, end = struct.unpack_from("<II", data, 8 * fw.ROLES.index(role))
          reference = begin if reference is None else reference
          elapsed = ((end - begin) & 0xFFFFFFFF) - overhead[*xy, role]
          if not 0 < elapsed <= cycle_limit:
            raise ValueError(
              f"invalid {role} stamps at {xy}: begin={begin:#x}, end={end:#x}, elapsed={elapsed}, bound={cycle_limit}"
            )
          t["roles"][role].append(elapsed)
          start = ((begin - reference + (1 << 31)) & 0xFFFFFFFF) - (1 << 31)
          spans.append((start, start + elapsed))
        span = max(end for _, end in spans) - min(start for start, _ in spans)
        if not 0 < span <= cycle_limit:
          raise ValueError(f"invalid tile interval at {xy}: {span} cycles")
        t["cycles"].append(span)
        if a.mark_ncrisc_instruction is not None:
          (marker,) = struct.unpack("<I", dev.dev.iface.read(xy, addr + 40, 4))
          begin, end = struct.unpack_from("<II", data, 8 * fw.ROLES.index("ncrisc"))
          tail = (end - marker) & 0xFFFFFFFF
          t.setdefault("marker_to_return", []).append(tail if marker and tail <= ((end - begin) & 0xFFFFFFFF) else None)
      print(f"{a.model} graph {g} launch {i}, repetition {rep}/{a.repeats}", flush=True)
    except Exception as exc:
      exc.add_note(f"{a.model}, graph {g} launch {i}, repetition {rep}")
      raise
    finally:
      dev.close()
  return record


def capture(a):
  from role_cycles import Device

  targets = [a.launch]
  if not a.launch:
    # These graphs include stateful kernels. Time one target on a clean graph
    # prefix so an instrumented program cannot perturb a later target.
    dev = Device(a.device)
    try:
      targets, seen, images = [], set(), {}
      for g, graph in enumerate(model_graphs(a, dev)):
        for i, (runtime, _, _) in enumerate(graph.launches):
          if runtime not in images:
            images[runtime] = tuple(installed_kernel(runtime).images.items())
          key = images[runtime]
          if a.all_launches or key not in seen:
            targets.append([g, i])
            seen.add(key)
    finally:
      dev.close()
  # A failed late prefix keeps its completed siblings available for inspection.
  partial = a.path.with_name(a.path.name + ".partial")
  with gzip.open(partial, "xt") as out:
    for launch in targets:
      sub = copy(a)
      sub.launch = launch
      if launch:
        print(f"measuring graph {launch[0]} launch {launch[1]}", flush=True)
      print(json.dumps(capture_target(sub)), file=out, flush=True)
  partial.rename(a.path)


@lru_cache(None)
def median_confidence_rank(n):
  """Zero-based rank of the lower endpoint of an exact 95% sign-test interval."""
  tail = 0
  for rank in range(n // 2 + 1):
    tail += comb(n, rank)
    if 40 * tail > (1 << n):
      return rank - 1
  return -1


def replay(a):
  failed = False
  found = set()
  with ExitStack() as files:
    src = files.enter_context(gzip.open(a.path, "rt"))
    output = None
    if a.csv:
      output = csv.writer(files.enter_context(a.csv.open("x", newline="")))
      output.writerow(
        [
          "model",
          "record_index",
          "kernel",
          "graph",
          "launch",
          "x",
          "y",
          "role",
          "predicted_cycles",
          "hardware_median",
          "error_pct",
          "within_3pct",
          "hardware_min",
          "hardware_max",
          "hardware_repetitions",
          "simulation_trials",
        ]
      )
    for record_index, r in enumerate(map(json.loads, src)):
      if a.launch and a.launch != [r.get("graph_index"), r.get("launch_index")]:
        continue
      if a.kernel and r["name"] not in a.kernel:
        continue
      found.add(r["name"])
      if r["firmware"] != firmware_fingerprint():
        raise ValueError(f"{r['name']}: capture belongs to a different worker firmware")
      c = SimpleNamespace(images={k: bytes.fromhex(v) for k, v in r["images"].items()}, manifest=r["manifest"])
      c.args_size = max((4 * (v["slot"] + 1 + (v["kind"] != "dram")) for v in c.manifest["params"].values()), default=0)
      label = r["name"]
      if "launch_index" in r:
        label += f" [graph {r['graph_index']}, launch {r['launch_index']}]"
      inputs = {key: bytes.fromhex(value) for key, value in r.get("inputs", {}).items()}
      try:
        pred = estimate(
          c, arguments=bytes.fromhex(r["args"]), inputs=inputs, samples=a.samples, max_cycles=a.max_cycles
        )
      except ValueError as exc:
        print(f"{label}: simulation failed: {exc}", flush=True)
        failed = True
        continue
      errors = []
      by_role = defaultdict(list)
      disjoint = confident_misses = confident_intervals = 0
      for t, measured in zip(pred["tiles"], r["tiles"], strict=True):
        if (t["x"], t["y"]) != (measured["x"], measured["y"]) or t["cores"].keys() != measured["roles"].keys():
          raise ValueError("predicted and measured tile/role sets differ")
        for role, row, values in [
          ("tile", t, measured["cycles"]),
          *((k, v, measured["roles"][k]) for k, v in t["cores"].items()),
        ]:
          value = row.get("sampled_cycles", {}).get("median", row["cycles"])
          if not values or min(values) <= 0:
            raise ValueError(f"missing or invalid hardware interval for {role} at ({t['x']},{t['y']})")
          ordered = sorted(values)
          trim = len(ordered) // 10
          disjoint += 0.97 * ordered[-1 - trim] > 1.03 * ordered[trim]
          rank = median_confidence_rank(len(ordered))
          if rank >= 0:
            confident_intervals += 1
            confident_misses += value < 0.97 * ordered[rank] or value > 1.03 * ordered[-1 - rank]
          error = 100 * (value / median(values) - 1)
          by_role[role].append((error, t["x"], t["y"], value, median(values)))
          if output:
            output.writerow(
              [
                r["model"],
                record_index,
                r["name"],
                r.get("graph_index"),
                r.get("launch_index"),
                t["x"],
                t["y"],
                role,
                value,
                median(values),
                round(error, 4),
                abs(error) <= 3,
                ordered[0],
                ordered[-1],
                len(ordered),
                a.samples,
              ]
            )
          errors.append(abs(error))
      passed = sum(e <= 3 for e in errors)
      print(
        f"{label}: {passed}/{len(errors)} within 3%, median {median(errors):.2f}%, worst {max(errors):.2f}%",
        flush=True,
      )
      if a.by_role:
        print(
          f"  {disjoint}/{len(errors)} intervals have disjoint hardware ±3% bands after trimming 10% from each tail"
        )
        if confident_intervals:
          print(
            f"  {confident_misses}/{confident_intervals} predictions miss 3% throughout the individual 95% hardware-median confidence interval"
          )
        marker_pc = r.get("marked_pc", r.get("marked_store_pc"))
        if marker_pc is not None:
          tails = [
            median(observed)
            for t in r["tiles"]
            if (
              observed := [v for v in t.get("marker_to_return", t.get("marked_store_to_return", ())) if v is not None]
            )
          ]
          print(f"  NCRISC marker at {marker_pc:#x} observed on {len(tails)}/{len(r['tiles'])} tiles")
          if tails:
            print(
              f"  measured marker to return (per-tile medians, including stamp overhead): "
              f"min {min(tails):g}, median {median(tails):g}, max {max(tails):g} cycles"
            )
        for role, comparisons in by_role.items():
          err, x, y, predicted, measured = max(comparisons, key=lambda item: abs(item[0]))
          hits = sum(abs(v[0]) <= 3 for v in comparisons)
          print(
            f"  {role}: {hits}/{len(comparisons)}, worst ({x},{y}) {predicted:g} vs {measured:g} cycles ({err:+.2f}%)"
          )
      failed |= passed != len(errors)
  if not found or (a.kernel and set(a.kernel) - found):
    raise ValueError("capture does not contain every requested kernel")
  if failed:
    raise SystemExit(1)


if __name__ == "__main__":
  p = argparse.ArgumentParser(description=__doc__)
  sub = p.add_subparsers(required=True)
  hw = sub.add_parser("capture")
  hw.add_argument("path", type=Path)
  hw.add_argument("--model", default="1b", choices=["1b", "8b-bf16", "8b-bfp8", "qwen38", "nanbeige"])
  hw.add_argument("--rows", type=int, default=0, help="capture this prefill chunk instead of decode")
  hw.add_argument(
    "--all-launches", action="store_true", help="capture every layer and binding of repeated kernel images"
  )
  hw.add_argument(
    "--launch",
    nargs=2,
    type=int,
    metavar=("GRAPH", "INDEX"),
    help="execute the original graph prefix and time only the specified launch",
  )
  hw.add_argument(
    "--mark-ncrisc-instruction",
    type=lambda s: int(s, 0),
    metavar="PC",
    help="record the interval from the last visit to a selected NIU strobe or fence through NCRISC return",
  )
  hw.add_argument("--pos", type=int, default=0)
  hw.add_argument("--device", type=int, default=0)
  hw.add_argument("--repeats", type=int, default=21)
  hw.set_defaults(action=capture)
  sim = sub.add_parser("replay")
  sim.add_argument("path", type=Path)
  sim.add_argument("--kernel", nargs="+")
  sim.add_argument("--csv", type=Path, metavar="FILE", help="write every matched tile and RISC comparison to a new CSV")
  sim.add_argument("--launch", nargs=2, type=int, metavar=("GRAPH", "INDEX"), help="score a specific indexed launch")
  sim.add_argument("--by-role", action="store_true", help="show pass counts and worst coordinate for each role")
  sim.add_argument("--samples", type=int, default=1)
  sim.add_argument("--max-cycles", type=int, default=10000000)
  sim.set_defaults(action=replay)
  args = p.parse_args()
  if args.action == capture and (args.path.exists() or args.repeats < 1 or args.pos < 0 or args.rows < 0):
    p.error("capture requires a new output path, a nonnegative position and positive repetitions")
  if args.action == capture and args.mark_ncrisc_instruction is not None and not args.launch:
    p.error("--mark-ncrisc-instruction requires a specific --launch GRAPH INDEX")
  args.action(args)
