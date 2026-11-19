#!/usr/bin/env python3
"""Ground truth for the simulator: device-timed Llama 3 kernel launches, plus the exact kernel images that ran.

  python3 sims/probes/kernels.py --device 1 --model 1b --output sims/results/<date>-kernels-1b-card1.jsonl

Uses the normal TTRV runtime (dispatch firmware, CQ). Every EXEC carries a profile pair: the dispatcher's wall clock
when it starts the EXEC (before fetching/installing code) and when the last core's done-increment has arrived.
Times are dispatcher-tile AICLK cycles (1.35 GHz). Three kinds of record:

  step    the whole decode step (embedding, L x {qkv, attention, o, gate, down}, lm, argmax) queued as plain EXECs, each
          with its own stamps, at several positions. The dispatcher prefetches/installs the next EXEC while the current
          one runs, exactly as in the graph replay used by examples/llama3.py.
  graph   the same step through the graph's CALL (what llama3.py runs), stamped before and after: total cycles.
  single  one kernel (layer 0's launch), alone: EXEC + signal, waited each time (no install overlap).
  b2b     the same launch queued N times back to back (install of the next overlaps the current one).

Kernel images, manifests and launch argument blocks are written next to the output (<output stem>/), so a simulator
can run exactly the bytes that were timed. No result here depends on the kernel's numerical output.
"""
import argparse, hashlib, importlib.util, json, struct, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import ops_blackhole  # noqa: E402
from ops_blackhole import BlackholeComputeQueue  # noqa: E402
from ttrv import Device, Var  # noqa: E402
import fw  # noqa: E402

spec = importlib.util.spec_from_file_location("llama3_example", ROOT / "examples" / "llama3.py")
llama3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llama3)


INSTALLED = {}  # descriptor address -> the role images actually multicast (install may relink a kernel)
_build = ops_blackhole.blackhole_build_grid_program
def _record(dev, grid, roles, args_size=0):
  prg = _build(dev, grid, roles, args_size)
  INSTALLED[prg.addr] = dict(roles)
  return prg
ops_blackhole.blackhole_build_grid_program = _record


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--device", type=int, required=True)
  ap.add_argument("--model", default="1b", choices=["1b", "8b-bf16"])
  ap.add_argument("--output", required=True)
  ap.add_argument("--positions", default="0,127,1023,4095")
  ap.add_argument("--repeats", type=int, default=5)
  ap.add_argument("--b2b", type=int, default=16)
  a = ap.parse_args()
  out = Path(a.output)
  art = out.with_suffix("")
  art.mkdir(parents=True, exist_ok=True)
  out.unlink(missing_ok=True)
  def rec(**r):
    with out.open("a") as f: f.write(json.dumps(dict(r, model=a.model, card=a.device, time=time.time())) + "\n")

  t0 = time.monotonic()
  d = Device(a.device)
  model = llama3.Llama3(ROOT / "weights" / f"llama3-{a.model}", d)
  print(f"loaded {a.model} in {time.monotonic() - t0:.1f} s", flush=True)
  dev, cap = d.dev, model.step
  launches, graph = cap.launches, cap.graph
  layers = (len(launches) - 3) // 5
  names = ["embedding"] + [n for _ in range(layers) for n in ("qkv", "attention", "o", "gate", "down")] + ["lm", "argmax"]
  assert len(names) == len(launches)
  host_args = graph.base - dev.sysmem.noc_addr  # graph argument blocks in pinned host memory (written once)

  # artifacts: one entry per distinct kernel object
  kinfo = {}
  for i, (kernel, block, vars) in enumerate(launches):
    if id(kernel) in kinfo: continue
    c = kernel.compiled
    kdir = art / names[i]
    kdir.mkdir(exist_ok=True)
    shas = {}
    for role, image in INSTALLED[kernel.program.addr].items():
      (kdir / f"{role}.bin").write_bytes(image)
      shas[role] = hashlib.sha256(image).hexdigest()[:16]
    (kdir / "manifest.json").write_text(json.dumps(c.manifest, indent=1, default=str))
    (kdir / "args0.bin").write_bytes(block)
    (kdir / "listing.json").write_text(json.dumps(c.listing, indent=1, default=str))
    kinfo[id(kernel)] = dict(name=names[i], grid=c.manifest["grid"], image_bytes={r: len(x) for r, x in INSTALLED[kernel.program.addr].items()},
                             sha=shas)
  for k in kinfo.values(): rec(kind="kernel", **k)

  slots = dev.alloc_host(32 * max(len(launches), a.b2b) + 64, 64)
  mem = dev.sysmem.mem
  def stamps(n):
    return [(struct.unpack_from("<Q", mem, slots + 32 * i + 8)[0], struct.unpack_from("<Q", mem, slots + 32 * i + 24)[0])
            for i in range(n)]
  def clear(n): mem[slots:slots + 32 * n] = bytes(32 * n)
  def set_vars(pos):
    for name, value in (("pos", pos), ("write_token", 0)):
      for o in graph.vars.get(name, ()): struct.pack_into("<I", mem, host_args + o, value & 0xFFFFFFFF)
  def submit(q):
    q.signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
    dev.synchronize(30)

  positions = [int(p) for p in a.positions.split(",")]
  for pos in positions:
    set_vars(pos)
    for rep in range(a.repeats):
      clear(len(launches))
      q = BlackholeComputeQueue()
      for i, (kernel, _, _) in enumerate(launches):
        q.exec(kernel.program, graph.base + fw.PARAM_SIZE * i, profile=dev.sysmem.noc_addr + slots + 32 * i)
      submit(q)
      st = stamps(len(launches))
      rec(kind="step", pos=pos, rep=rep, names=names, start=[s - st[0][0] for s, _ in st], end=[e - st[0][0] for _, e in st],
          span=[e - s for s, e in st], total=st[-1][1] - st[0][0])
      # graph CALL path, stamped around it
      clear(2)
      q = BlackholeComputeQueue()
      q.timestamp(dev.sysmem.noc_addr + slots)
      q.call(graph.graph.addr, graph.graph.size, 1, graph.graph.stride)
      q.timestamp(dev.sysmem.noc_addr + slots + 16)
      submit(q)
      t_a, t_b = struct.unpack_from("<Q", mem, slots + 8)[0], struct.unpack_from("<Q", mem, slots + 24)[0]
      rec(kind="graph", pos=pos, rep=rep, total=t_b - t_a)
    print(f"pos {pos}: step total {rec_total(out, pos)}", flush=True)

  # single and back-to-back, layer 0's launch of each kernel, at the middle position
  pos = positions[len(positions) // 2]
  set_vars(pos)
  first = {}
  for i, n in enumerate(names): first.setdefault(n, i)
  for n, i in first.items():
    kernel = launches[i][0]
    args = graph.base + fw.PARAM_SIZE * i
    spans = []
    for rep in range(a.repeats + 1):
      clear(1)
      submit(BlackholeComputeQueue().exec(kernel.program, args, profile=dev.sysmem.noc_addr + slots))
      s, e = stamps(1)[0]
      spans.append(e - s)
    rec(kind="single", name=n, index=i, pos=pos, spans=spans, median=float(np.median(spans[1:])))
    clear(a.b2b)
    q = BlackholeComputeQueue()
    for j in range(a.b2b): q.exec(kernel.program, args, profile=dev.sysmem.noc_addr + slots + 32 * j)
    submit(q)
    st = stamps(a.b2b)
    ends = [e for _, e in st]
    rec(kind="b2b", name=n, index=i, pos=pos, starts=[s - st[0][0] for s, _ in st], ends=[e - st[0][0] for e in ends],
        period=float(np.median(np.diff(ends))))
    print(f"{n}: single {np.median(spans[1:]):.0f}  b2b period {np.median(np.diff(ends)):.0f}", flush=True)
  d.close()


def rec_total(out, pos):
  rows = [json.loads(l) for l in out.read_text().splitlines()]
  return [r["total"] for r in rows if r.get("kind") == "step" and r["pos"] == pos]


if __name__ == "__main__":
  main()
