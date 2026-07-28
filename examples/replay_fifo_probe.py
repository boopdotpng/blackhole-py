"""Probe the number of Replay commands one Blackhole MOP may safely emit."""

import argparse
import time

from device import Device
from isa import Tensix as TT
from program import DType, Program
from ttk.sfpu import LaneConfig, SfpuFormat
from ttk.sync import (
  Sem, SemWait, Stall, Wait, sem_wait, stall,
)


def build(output, replay_commands):
  p = Program(output.cores, output)
  output_cb = p.cb(DType.BF16, depth=1)
  sfpu = p.sfpu

  builder = sfpu.program()
  value = builder.load_float(1.0)
  builder.store(value, format=SfpuFormat.BF16)
  program = builder.finish()
  start, body = sfpu._prepare(program)
  if start is None:
    raise RuntimeError("probe SFPU body did not fit in Replay storage")

  sem_wait(
    sfpu.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
    Stall.SYNC | Stall.MATH | Stall.SFPU,
  )
  sfpu._configure_dst(0, LaneConfig())
  stall(sfpu.k, Stall.SFPU, Wait.MATH)
  for word in program.setup_words: sfpu._issue(word)
  sfpu._configure_replay_mop(
    start, len(body), iterations=replay_commands,
  )

  # Exactly one incoming MOP; only its number of emitted Replay commands
  # varies between probe cases.
  sfpu._mop.run()
  sfpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)
  sfpu.publish()

  p.pack.move(output_cb, tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, output, 0)
  return p, len(body)


def run(replay_commands, timeout):
  device = Device()
  try:
    device.init_device()
    core = (device.dram.cores[0],)
    output = device.dram.buffer(
      "replay_probe_output", DType.BF16, (32, 32),
      cores=core,
    )
    program, replay_length = build(output, replay_commands)
    started = time.perf_counter()
    device.run(program, timeout=timeout)
    elapsed = time.perf_counter() - started
    print(
      f"PASS replay_commands={replay_commands} "
      f"replay_length={replay_length} wall_s={elapsed:.6f}",
    )
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("replay_commands", type=int)
  parser.add_argument("--timeout", type=float, default=3.0)
  args = parser.parse_args()
  if not 1 <= args.replay_commands <= 1023:
    parser.error("replay_commands must be in range 1..1023")
  run(args.replay_commands, args.timeout)
