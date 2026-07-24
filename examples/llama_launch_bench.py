"""Launch-cost profile for the llama3 bs=1 decode forward pass.

Three measurements:
  1. isolated device kernel time per stage (dispatcher GO->done timestamp)
  2. dispatch pipeline floor (empty launches, nothing to hide overhead behind)
  3. in-situ ablation: rebuild the token trace with one stage class removed,
     which gives the true marginal cost of those launches inside the pipeline
"""
import time, statistics, sys
sys.path.insert(0, ".")

from examples.llama3 import Llama3Decode, LLAMA_LAYERS, LLAMA_CORES
from program import Program
from pcie import P100_WORKER_CORES

STAGES = (
  "rms", "q", "k", "k", "rope", "cache", "attention", "q", "residual",
  "rms", "gate", "gate", "swiglu", "dense", "down", "residual",
)
ORDER = ("embedding", *dict.fromkeys(STAGES), "lm", "argmax")
POSITION = 64
PARAMS = {
  "token_pos": POSITION, "write_pos": POSITION + 1, "write_token": 0,
  "start_pos": POSITION, "kv_blocks": POSITION // 32 + 1,
  "valid_columns": POSITION % 32 + 1,
}
# Bytes of weight streamed from DRAM by each stage launch.
WEIGHT_BYTES = {
  "q": 2048 * 2048 * 2, "k": 512 * 2048 * 2, "gate": 8192 * 2048 * 2,
  "down": 2048 * 8192 * 2, "lm": 128256 * 2048 * 2,
}
CORES = {
  "embedding": 1, "rms": 1, "q": 118, "k": 118, "rope": 40, "cache": 8,
  "attention": 8, "residual": 32, "gate": 118, "swiglu": 118,
  "dense": 118, "down": 118, "lm": 118, "argmax": 118,
}


def replay_min(trace, params, repeats=15):
  samples = []
  for _ in range(repeats):
    started = time.perf_counter_ns()
    trace.replay(params, timeout=60.0)
    samples.append((time.perf_counter_ns() - started) / 1e3)
  return min(samples)


def build_trace(runtime, skip=()):
  """Re-queue a whole token, omitting every launch in ``skip``.

  Each ablation trace is used once and discarded, so the resident
  parameter-template arena is rewound instead of leaking 260 slots per build.
  """
  from fw.consts import TensixL1
  device = runtime.device
  device._param_template_next = TensixL1.PARAM_TEMPLATE_BASE
  skip = set(skip)

  def queue(name, replacements=(), constants=None):
    if name in skip: return
    params = {source: target for source, target in replacements}
    if constants: params.update(constants)
    device.queue(runtime.programs[name], params=params)

  queue("embedding")
  template = runtime.layers[0]
  tw = template["weights"]
  for index in range(LLAMA_LAYERS):
    layer = runtime.layers[index]
    w = layer["weights"]
    queue("rms", ((runtime.x_a, runtime.x_a),
                  (tw["input_norm"], w["input_norm"])))
    queue("q", ((tw["q"], w["q"]),))
    queue("k", ((tw["k"], w["k"]),))
    queue("k", ((tw["k"], w["v"]), (runtime.k_compact, runtime.v_compact)))
    queue("rope", constants={"start_pos": 0})
    queue("cache", ((template["key_cache"], layer["key_cache"]),
                    (template["value_cache"], layer["value_cache"])),
          {"start_pos": 0})
    queue("attention", ((template["key_cache"], layer["key_cache"]),
                        (template["value_cache"], layer["value_cache"])),
          {"kv_blocks": 1, "valid_columns": 1})
    queue("q", ((runtime.q_projection_input, runtime.context_projection_input),
                (tw["q"], w["o"])))
    queue("residual")
    queue("rms", ((runtime.x_a, runtime.x_b),
                  (tw["post_norm"], w["post_norm"])))
    queue("gate", ((tw["gate"], w["gate"]),))
    queue("gate", ((tw["gate"], w["up"]), (runtime.gate, runtime.up)))
    queue("swiglu")
    queue("dense")
    queue("down", ((tw["down"], w["down"]),))
    queue("residual", ((runtime.x_a, runtime.x_b), (runtime.x_b, runtime.x_a)))
  queue("rms", ((tw["input_norm"], runtime.final_norm),))
  queue("lm")
  queue("argmax")
  count = len(device.program_queue)
  # A runtime name must still be claimed by some queued program.
  names = ["token_pos", "write_pos", "write_token", "start_pos",
           "kv_blocks", "valid_columns"]
  if "attention" in skip:
    names.remove("kv_blocks"); names.remove("valid_columns")
  if {"rope", "cache", "attention"} <= skip: names.remove("start_pos")
  if {"lm", "argmax"} <= skip:
    names.remove("write_pos"); names.remove("write_token")
  return device.capture_trace(tuple(names)), count


def main():
  runtime = Llama3Decode()
  device = runtime.device
  report = []

  def out(line=""):
    print(line)
    report.append(line)

  try:
    full = replay_min(runtime.decode_trace, PARAMS)
    launches = 1 + LLAMA_LAYERS * len(STAGES) + 3
    out("=" * 74)
    out("llama3.2-1B bs=1 decode launch profile (p100a, position 64)")
    out("=" * 74)
    out(f"token latency      : {full:.1f} us  ({1e6 / full:.1f} tok/s)")
    out(f"launches per token : {launches}")
    out()

    # ---- 1. isolated per-stage kernel time ---------------------------------
    # Measured before any extra program is cached: installing new resident
    # kernels mid-session perturbs the traced launches measured below.
    per_token = {s: STAGES.count(s) * LLAMA_LAYERS for s in dict.fromkeys(STAGES)}
    per_token["rms"] += 1
    per_token.update(embedding=1, lm=1, argmax=1)

    device_us = {}
    for stage in ORDER:
      program = runtime.programs[stage]
      best = None
      for _ in range(12):
        stamp, = device.run(program, timeout=60.0)
        best = stamp.us if best is None else min(best, stamp.us)
      device_us[stage] = best

    # ---- 2. in-situ ablation ----------------------------------------------
    out("-- in-situ ablation (marginal cost inside the pipeline) " + "-" * 18)
    out(f"{'removed':<22} {'launches':>8} {'us':>9} {'saved':>9} {'us/launch':>10}")
    out(f"{'(baseline)':<22} {launches:8d} {full:9.1f} {'-':>9} {'-':>10}")
    groups = (
      ("rms", ("rms",)),
      ("rope", ("rope",)),
      ("cache", ("cache",)),
      ("residual", ("residual",)),
      ("swiglu", ("swiglu",)),
      ("dense", ("dense",)),
      ("swiglu+dense", ("swiglu", "dense")),
      ("all small stages", ("rms", "cache", "residual", "swiglu", "dense")),
      ("k/v projections", ("k",)),
      ("attention", ("attention",)),
      ("lm+argmax", ("lm", "argmax")),
    )
    ablations = {}
    for label, skip in groups:
      trace, count = build_trace(runtime, skip)
      params = {k: v for k, v in PARAMS.items() if k in trace.params}
      lo = replay_min(trace, params, repeats=12)
      removed = launches - count
      saved = full - lo
      ablations[label] = (removed, lo, saved)
      out(f"{label:<22} {count:8d} {lo:9.1f} {saved:9.1f} "
          f"{saved / removed if removed else 0:10.2f}")
    out()

    # ---- 3. dispatch floor (last: caching a new program perturbs state) ---
    empty = Program(P100_WORKER_CORES[:LLAMA_CORES], images={})
    device.cache_kernels((empty,))
    stamps = []
    for _ in range(12):
      stamp, = device.run(empty, timeout=60.0)
      stamps.append(stamp.us)
    out("-- dispatch pipeline floor " + "-" * 47)
    out(f"empty 118-core launch, device GO->done : {min(stamps):.2f} us")
    floor = None
    for count in (1, 130, 260, 520):
      for _ in range(count): device.queue(empty)
      trace = device.capture_trace()
      lo = replay_min(trace, None, repeats=25)
      floor = lo / count
      out(f"empty x{count:<4} trace {lo:9.1f} us   per-launch {lo / count:6.2f} us")
    out(f"=> steady-state dispatch rate ~{floor:.1f} us/launch; a launch whose")
    out("   kernel is shorter than that is dispatch-bound, not compute-bound.")
    out()

    out("-- isolated device kernel time " + "-" * 43)
    out(f"{'stage':<10} {'cores':>5} {'us':>8} {'GB/s':>7} {'n':>4} {'us/token':>9} {'bound':>7}")
    for stage in ORDER:
      best = device_us[stage]
      bw = WEIGHT_BYTES.get(stage)
      rate = f"{bw / best / 1e3:7.0f}" if bw else "      -"
      kind = "disp" if best < floor else "mem" if bw else "lat"
      out(f"{stage:<10} {CORES[stage]:5d} {best:8.2f} {rate} {per_token[stage]:4d} "
          f"{best * per_token[stage]:9.1f} {kind:>7}")
    out(f"sum of isolated kernel time: {sum(device_us[s] * per_token[s] for s in ORDER):.0f} us")
    out()

    # ---- 4. projection cost model -----------------------------------------
    out("-- projection cost model " + "-" * 48)
    slope = (device_us["q"] - device_us["k"]) / (2048 - 512)
    fixed = device_us["k"] - 512 * slope
    out(f"decode_projection(rows) ~ {fixed:.2f} us + {slope * 1e3:.2f} ns/row")
    for stage, rows in (("q", 2048), ("k", 512), ("gate", 8192), ("lm", 128256)):
      out(f"  predict {stage:<5} {fixed + rows * slope:8.2f} us   "
          f"actual {device_us[stage]:8.2f} us")
    projections = 7 * LLAMA_LAYERS + 1
    out(f"projection launches/token: {projections}  "
        f"fixed overhead: {projections * fixed:.0f} us "
        f"({projections * fixed / full * 100:.1f}% of token)")
    out(f"  fuse q+k+v -> 1 launch : saves ~{2 * fixed * LLAMA_LAYERS:.0f} us")
    out(f"  fuse gate+up -> 1      : saves ~{fixed * LLAMA_LAYERS:.0f} us")
    out()

    # ---- 5. DRAM bandwidth -------------------------------------------------
    layer_bytes = 2 * (2048 * 2048 * 2) + 2 * (512 * 2048 * 2) + 3 * (8192 * 2048 * 2)
    token_bytes = LLAMA_LAYERS * layer_bytes + WEIGHT_BYTES["lm"]
    out("-- DRAM roofline " + "-" * 56)
    out(f"weight bytes per token : {token_bytes / 1e6:.0f} MB")
    out(f"achieved bandwidth     : {token_bytes / full / 1e3:.0f} GB/s")
    out(f"ideal token at 400 GB/s: {token_bytes / 400e3:.0f} us "
        f"({1e6 / (token_bytes / 400e3):.0f} tok/s)")
  finally:
    runtime.close()
    with open("llama3_launch_profile.txt", "w") as handle:
      handle.write("\n".join(report) + "\n")
    print("\nwrote llama3_launch_profile.txt")


main()
