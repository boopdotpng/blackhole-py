"""Attribute resident decode time to kernels and measure empty-launch overhead.

Each kernel is measured in traces containing 8 and 24 copies. The difference
removes fixed trace/host overhead. Results include per-launch firmware work;
they are isolated-kernel estimates, not timestamps inside a full decode trace.
The sum is reported alongside a separately measured full decode.
"""

import argparse
import json
from pathlib import Path
import statistics

from examples.llama3_1b import Llama3Decode, ROPE_CACHE_TOKENS
from ttko.program import Const, Program


class ProfileRuntime(Llama3Decode):
  def _queue(self, name, replacements=(), constants=None):
    self.launch_counts[name] = self.launch_counts.get(name, 0) + 1
    return super()._queue(name, replacements, constants)

  def _build_programs(self):
    self.launch_counts = {}
    cache = self.device.cache_kernels

    def install(programs):
      self.noops = {
        n: Program(self.device.dram.cores[:n], Const("noop", 0), images={})
        for n in (1, 8, 32, 40, 117)
      }
      return cache((*programs, *self.noops.values()))

    self.device.cache_kernels = install
    try:
      super()._build_programs()
    finally:
      self.device.cache_kernels = cache


def profile(args):
  runtime = ProfileRuntime(args.safetensor, args.device, attention_cores=args.attention_cores)
  try:
    runtime.load_tokens([128000, 9906])
    traces = {}
    programs = {
      **runtime.programs,
      **{f"noop{n}": program for n, program in runtime.noops.items()},
    }
    for name, program in programs.items():
      names = tuple(n for n in (
        "token_pos", "start_pos", "kv_blocks", "valid_columns",
        "write_pos", "write_token", "noop",
      ) if n == "token_pos" or n in program.params)
      traces[name] = []
      for repeats in (8, 24):
        # Provides one common dynamic parameter even for static kernels.
        runtime.device.queue(runtime.programs["embedding"])
        for _ in range(repeats): runtime.device.queue(program)
        traces[name].append(runtime.device.capture_trace(names))

    results, filled = [], 0
    for context in args.contexts:
      while filled < context:
        runtime.decode(filled, logits=False)
        filled += 1
      full = [runtime.decode(context - 1)[1] for _ in range(9)]
      result = {
        "context": context,
        "device": args.device,
        "attention_cores": args.attention_cores,
        "launch_counts": runtime.launch_counts,
        "full_decode_us": statistics.median(full),
        "kernels": {},
      }
      values = dict(
        token_pos=context - 1, start_pos=context - 1,
        kv_blocks=(context + 31) // 32, valid_columns=(context - 1) % 32 + 1,
        write_pos=context, write_token=0, noop=0,
      )
      for name, pair in traces.items():
        runtime.decode(context - 1, logits=False)
        medians = []
        for trace in pair:
          samples = []
          for repeat in range(9):
            trace.replay({n: values[n] for n in trace.params})
            if repeat >= 2: samples.append(trace.last_profile["device_us"])
          medians.append(statistics.median(samples))
        elapsed = (medians[1] - medians[0]) / 16
        result["kernels"][name] = {
          "us": elapsed, "per_token_us": elapsed * runtime.launch_counts.get(name, 0),
        }
      result["sum_kernel_us"] = sum(
        kernel["per_token_us"] for kernel in result["kernels"].values()
      )
      print(json.dumps(result), flush=True)
      results.append(result)
    return results
  finally:
    runtime.close()


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--safetensor", default="weights/llama3-1b/model.safetensors")
  parser.add_argument("--device", type=int, default=0)
  parser.add_argument("--attention-cores", type=int, choices=(8, 16, 32), default=16)
  parser.add_argument("--contexts", type=int, nargs="+", default=[32, 64, 128, 512])
  parser.add_argument("--output", type=Path)
  args = parser.parse_args()
  if any(not 1 <= n < ROPE_CACHE_TOKENS for n in args.contexts):
    parser.error("contexts must fit in the KV cache")
  args.contexts = sorted(set(args.contexts))
  results = profile(args)
  if args.output:
    args.output.write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
  main()
