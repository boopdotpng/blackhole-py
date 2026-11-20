"""Compare isolated per-RISC AICLK intervals to offline estimates, using unprofiled launches."""

import argparse
import hashlib
import json
import struct
import sys
from dataclasses import replace
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import fw
from ttrv import build, hw, isa, compile_program
from ops_blackhole import blackhole_build_grid_program
from ttrv.cycles import estimate, firmware_fingerprint
from ttrv.runtime import Device, Kernel


def stamp(addr, ordered=False):
  # Registers 1 and 2 are dead on entry and after the last kernel instruction.
  if ordered:
    # Some TRISC entry stamps contained instruction words after a grid change. A fenced second read gave valid start stamps.
    return struct.pack(
      "<8I",
      isa.rv("fence"),
      isa.rv("lui", 2, imm=0xFFB12),
      isa.rv("lw", 1, 2, imm=0x1F0),
      isa.rv("fence"),
      isa.rv("lw", 1, 2, imm=0x1F0),
      isa.rv("lui", 2, imm=(addr + 2048) >> 12),
      isa.rv("sw", rs1=2, rs2=1, imm=((addr + 2048) % 4096) - 2048),
      isa.rv("fence"),
    )
  return struct.pack(
    "<4I",
    isa.rv("lui", 1, imm=0xFFB12),
    isa.rv("lw", 1, 1, imm=0x1F0),
    isa.rv("lui", 2, imm=(addr + 2048) >> 12),
    isa.rv("sw", rs1=2, rs2=1, imm=((addr + 2048) % 4096) - 2048),
  )


def mark_ncrisc_instruction(compiled, pc, address):
  """Timestamp the last visit to one NIU strobe or fence. Preserve the original GPRs and branch targets."""
  img = compiled.images["ncrisc"]
  if pc < 0 or pc % 4 or pc + 4 >= len(img) or not img.endswith(fw.ret("ncrisc")):
    raise ValueError("invalid NCRISC marker offset")
  (word,) = struct.unpack_from("<I", img, pc)
  decoded = isa.rv_decode(word)
  if not decoded or not (decoded[0] == "fence" or (decoded[0] == "sw" and decoded[1]["imm"] == hw.Cmd.CMD_CTRL)):
    raise ValueError("marked instruction must be a fence or a word store with a CMD_CTRL displacement")
  used = {v["cb"] for v in compiled.manifest["storage"].values() if "cb" in v}
  unused = set(range(32)) - used
  if not unused:
    raise ValueError("no unused private CB cursor to preserve timestamp registers")
  offset = 16 * max(unused) - 2048  # x3 is the TTRV private-memory base + 2048
  save = [isa.rv("sw", rs1=hw.LOCAL_BASE_REG, rs2=r, imm=offset + 4 * r) for r in (1, 2)]
  restore = [isa.rv("lw", r, hw.LOCAL_BASE_REG, imm=offset + 4 * r) for r in (1, 2)]
  # The old firmware return jumps over an out-of-line copy of the store. All
  # other original offsets stay valid, including branches to the old return.
  trampoline = len(img)
  stub = struct.pack("<2I", *save) + stamp(address, ordered=True) + struct.pack("<3I", *restore, word)
  stub += struct.pack("<I", isa.rv("jal", imm=pc + 4 - (trampoline + len(stub))))
  patched = bytearray(img)
  struct.pack_into("<I", patched, pc, isa.rv("jal", imm=trampoline - pc))
  struct.pack_into("<I", patched, trampoline - 4, isa.rv("jal", imm=len(stub) + 4))
  return replace(compiled, images=compiled.images | {"ncrisc": bytes(patched) + stub + fw.ret("ncrisc")})


def instrument(compiled, record_address=fw.PROFILE_RECORD, ordered=False):
  images = {}
  for role, img in compiled.images.items():
    addr = record_address + 8 * fw.ROLES.index(role)
    if not img.endswith(fw.ret(role)):
      raise ValueError(f"{role}: missing final return")
    images[role] = stamp(addr, ordered) + img[:-4] + stamp(addr + 4, ordered) + fw.ret(role)
    if len(images[role]) > fw.CODE_SIZE[role]:
      raise ValueError(f"{role}: stamped image exceeds slot")
  return replace(compiled, images=images)


def measure(run, compiled, bindings, repeats, ordered=False):
  device = run.device
  if device._profiler:
    raise ValueError("role stamps use the unprofiled launch's unused profile record; unset PROFILE")
  # install() has already allocated and initialized any keep storage. Install exactly
  # these image bytes into a descriptor without relocating them a second time.
  run.program = blackhole_build_grid_program(
    device.dev, run.grid, instrument(compiled, ordered=ordered).images, compiled.args_size
  )
  rows = []
  previous = None
  for _ in range(repeats + 1):
    if isinstance(bindings, bytes):
      device._launch(run.program, bindings)
    else:
      run(**bindings)
    device.synchronize()
    sample, offsets = {}, {}
    for core in device.dev.workers[: run.grid]:
      data = device.dev.iface.read(core, fw.PROFILE_RECORD, 8 * len(fw.ROLES))
      for role in compiled.images:
        begin, end = struct.unpack_from("<II", data, 8 * fw.ROLES.index(role))
        sample[(*core, role)] = (end - begin) & 0xFFFFFFFF
        offsets[(*core, role)] = begin
    reference = offsets[1, 2, next(iter(compiled.images))]
    if reference == previous:
      raise RuntimeError("stale role timestamps")
    previous = reference
    offsets = {k: ((v - reference + (1 << 31)) & 0xFFFFFFFF) - (1 << 31) for k, v in offsets.items()}
    rows.append((sample, offsets))
  keys = rows[0][0].keys()
  return (
    {k: [sample[k] for sample, _ in rows[1:]] for k in keys},
    {k: [offs[k] for _, offs in rows[1:]] for k in keys},
  )


def case(device, name, source, bindings, repeats, trials=1, startup=None, counters=False):
  compiled = build(source) if isinstance(source, str) else source
  ceiling = device.dev.ttrv_keep_base
  run = Kernel(device, compiled, "role_cycles")
  if compiled.manifest != run.program.manifest:
    compiled = compile_program(compiled.program, ceiling)
    if compiled.manifest != run.program.manifest:
      raise ValueError("stamp image layout differs from installed kernel")
  normal_program = run.program
  blank = replace(compiled, images={r: fw.ret(r) for r in compiled.images})
  overhead, _ = measure(run, blank, bindings, repeats)
  samples, skew = measure(run, compiled, bindings, repeats)
  perf = {}
  if counters:
    run.program = normal_program
    with device.profile() as prof:
      run(**bindings)
    for xy, record in zip(device.dev.workers, prof.launches[0].cores):
      perf[xy] = {field: int(record[field]) for field in fw.PROFILE_FIELDS if field in record.dtype.names}
  args = {k: getattr(v, "addr", v) for k, v in bindings.items()}
  prediction = estimate(compiled, bindings=args, samples=trials, startup=startup)
  rows = []
  flat = (dict(x=t["x"], y=t["y"], role=r, **row) for t in prediction["tiles"] for r, row in t["cores"].items())
  for row in flat:
    key = row["x"], row["y"], row["role"]
    measured = median(samples[key]) - median(overhead[key]) + 1
    rows.append(
      dict(
        **row,
        entry_clock_offset=median(skew[key]),
        raw=samples[key],
        blank=overhead[key],
        measured=measured,
        error_pct=round(100 * (row.get("sampled_cycles", {}).get("median", row["cycles"]) / measured - 1), 3),
      )
    )
  tiles = []
  for t in prediction["tiles"]:
    xy = t["x"], t["y"]
    keys = [(*xy, role) for role in compiled.images]
    # Differences on one tile cancel the offset of its local wall clock, including on wrap.
    spans = [
      max(skew[k][i] + samples[k][i] - median(overhead[k]) + 1 for k in keys) - min(skew[k][i] for k in keys)
      for i in range(repeats)
    ]
    measured = median(spans)
    tiles.append(
      dict(
        x=t["x"],
        y=t["y"],
        **({"hardware_counters": perf[xy]} if xy in perf else {}),
        cycles=t.get("sampled_cycles", {}).get("median", t["cycles"]),
        measured=measured,
        raw=spans,
        error_pct=round(100 * (t.get("sampled_cycles", {}).get("median", t["cycles"]) / measured - 1), 3),
      )
    )
  return dict(
    name=name,
    trials=trials,
    tiles=tiles,
    grid=compiled.manifest["grid"],
    bindings=args,
    images={r: hashlib.sha256(img).hexdigest() for r, img in compiled.images.items()},
    cores=rows,
  )


def main():
  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument(
    "--counters", action="store_true", help="also collect hardware unit counters in a separate uninstrumented launch"
  )
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--samples", type=int, default=1, help="simulated phase trials for estimating the median")
  ap.add_argument("--startup", help="startup calibration file or simultaneous, as in ttrv build --cycles")
  ap.add_argument("--repeats", type=int, default=7)
  ap.add_argument("--startup-only", type=Path, help="write a firmware-specific role entry calibration and exit")
  ap.add_argument("--grid", type=int, default=4)
  ap.add_argument(
    "--traffic-sweep",
    action="store_true",
    help="also isolate each NIU and reverse the mapping from worker ID to DRAM page",
  )
  ap.add_argument(
    "--check", action="store_true", help="exit nonzero if any worker or RISC median misses the ±3% target"
  )
  ap.add_argument(
    "--embedding-sweep",
    action="store_true",
    help="isolate history reads, common and striped row reads, and output writes",
  )
  ap.add_argument("--argmax", action="store_true", help="also measure the 88-worker Llama 1B argmax")
  ap.add_argument(
    "--full-projection", action="store_true", help="run the 1B O projection at DIM=2048 and INPUT_TILES=2"
  )
  ap.add_argument("--output", type=Path, help="write full per-worker samples as JSONL")
  a = ap.parse_args()
  outside = 0

  def report(r):
    nonlocal outside
    r["card"] = a.device
    r["firmware_sha256"] = firmware_fingerprint()
    outside += sum(abs(row["error_pct"]) > 3 for kind in ("tiles", "cores") for row in r[kind])
    if a.output:
      with a.output.open("a") as out:
        print(json.dumps(r), file=out)
    tiles = [x["error_pct"] for x in r["tiles"]]
    print(f"{r['name']}: {len(tiles)} tile intervals, {min(tiles):+.2f}% .. {max(tiles):+.2f}%")
    errors = [x["error_pct"] for x in r["cores"]]
    print(f"{r['name']}: {len(errors)} worker/RISC intervals, {min(errors):+.2f}% .. {max(errors):+.2f}%", flush=True)

  if not 1 <= a.grid <= 138 or min(a.samples, a.repeats) < 1:
    ap.error("invalid grid or repeats")
  dev = Device(a.device)
  try:
    grid = f"grid {a.grid}\n"
    loop = "s = core.id\nfor i in 0..256 { s = s + i }\n"
    source = grid + "\n".join(f"fn {r}() {{\n{loop}}}" for r in fw.ROLES)
    if a.startup_only:
      compiled = build(source)
      run = Kernel(dev, compiled, "entry_offsets")
      _, offsets = measure(run, compiled, {}, a.repeats)
      workers = dev.dev.workers[: a.grid]
      role_offsets = {
        r: round(median(t - b for xy in workers for t, b in zip(offsets[(*xy, r)], offsets[(*xy, "brisc")])))
        for r in fw.ROLES
      }
      calibration = dict(
        card=a.device, grid=a.grid, repeats=a.repeats, firmware_sha256=firmware_fingerprint(), role_offsets=role_offsets
      )
      # Preserve the joint distribution: tiles can be in the same WAIT_SLOW polling phase.
      launches = [
        [offsets[(*xy, "ncrisc")][i] - offsets[(*xy, "brisc")][i] for xy in workers] for i in range(a.repeats)
      ]
      launches.sort(key=median)
      count = min(33, len(launches))
      calibration["ncrisc_phases"] = [launches[(2 * j + 1) * len(launches) // (2 * count)] for j in range(count)]
      a.startup_only.write_text(json.dumps(calibration, indent=2) + "\n")
      return
    report(case(dev, "scalar", source, {}, a.repeats, a.samples, a.startup, a.counters))
    source = (
      grid
      + """param input: bf16[]
param output: bf16[]
l1 a: bf16[1024]
l1 b: bf16[1024]
fn brisc() {
  for i in 0..8 { noc.read a, input[core.id * 1024], n=1024, wait }
}
fn ncrisc() {
  for i in 0..8 { noc.write output[core.id * 1024], b, n=1024, wait }
}
"""
    )
    bindings = {k: dev.zeros(a.grid * 1024, "bf16") for k in ("input", "output")}
    report(case(dev, "dram", source, bindings, a.repeats, a.samples, a.startup, a.counters))
    if a.traffic_sweep:
      for which in ("read", "write", "mixed"):
        cut = source
        if which == "read":
          cut = source.split("fn ncrisc")[0]
        if which == "write":
          cut = source.split("fn brisc")[0] + "fn ncrisc" + source.split("fn ncrisc")[1]
        for reverse in (False, True):
          if which == "mixed" and not reverse:
            continue
          src = cut.replace("core.id * 1024", "(grid.size - 1 - core.id) * 1024") if reverse else cut
          report(
            case(
              dev,
              f"{which}-{'reverse' if reverse else 'forward'}",
              src,
              bindings,
              a.repeats,
              a.samples,
              a.startup,
              a.counters,
            )
          )
    examples = Path(__file__).resolve().parents[2] / "examples" / "llama3"
    embedding_src = (examples / "embedding.ttrv").read_text()
    embedding = build(embedding_src, {"ROW_LANES": a.grid}, str(examples / "embedding.ttrv"))
    args = dict(
      history=dev.zeros(max(16, a.grid + 15), "u32"),
      weights=dev.zeros(2048, "bf16"),
      output=dev.zeros(2048 * a.grid, "bf16"),
      token_pos=0,
    )
    report(case(dev, "embedding", embedding, args, a.repeats, a.samples, a.startup, a.counters))
    if a.embedding_sweep:
      # Keep all buffer addresses fixed while changing the participating operations.
      args = dict(
        history=dev.zeros(max(16, a.grid + 15), "u32"),
        weights=dev.zeros(2048 * a.grid, "bf16"),
        output=dev.zeros(2048 * a.grid, "bf16"),
        token_pos=0,
      )
      history = embedding_src[: embedding_src.index("    token =")] + "}\n"
      gather = embedding_src[: embedding_src.index("    noc.write")] + "}\n"
      for name, variant in (
        ("history", history),
        ("history-gather-common", gather),
        ("history-gather-striped", gather.replace("token * DIM", "(token + core.id) * DIM")),
        ("full-common", embedding_src),
      ):
        kernel = build(variant, {"ROW_LANES": a.grid})
        report(case(dev, name, kernel, args, a.repeats, a.samples, a.startup, a.counters))
    rows = 2048 if a.full_projection else a.grid * 8
    tiles = 2 if a.full_projection else 1
    if (rows + a.grid - 1) // a.grid + 31 > 1024:
      raise ValueError("projection output slice exceeds its CB page")
    proj = build(
      (examples / "o.ttrv").read_text(),
      {"WORKERS": a.grid, "DIM": rows, "INPUT_TILES": tiles},
      str(examples / "o.ttrv"),
    )
    args = {
      k: dev.zeros(n, "bf16")
      for k, n in dict(context=1024 * tiles, matrix=rows * 1024 * tiles, output=rows + 32, residual=rows + 32).items()
    }
    report(case(dev, "o", proj, args, a.repeats, a.samples, a.startup, a.counters))
    if a.argmax:
      argmax = build((examples / "argmax.ttrv").read_text(), file=str(examples / "argmax.ttrv"))
      args = dict(
        logits=dev.zeros(128256, "bf16"),
        history=dev.zeros(8192, "u32"),
        tokens=dev.zeros(8, "u32", host=True),
        start_pos=0,
        write_token=0,
      )
      report(case(dev, "argmax", argmax, args, a.repeats, a.samples, a.startup, a.counters))
  finally:
    dev.close()
  if a.check and outside:
    raise SystemExit(f"{outside} intervals outside ±3%")


if __name__ == "__main__":
  main()
