# emu

Cycle-structured Blackhole emulator.

## Design

The simulator advances in fixed phases:

1. `COMPLETE`: events whose scheduled cycle has arrived run.
2. `COMMIT`: completed operations publish externally visible state.
3. `ISSUE`: cores and Tensix threads issue new work into available units.
4. `LATCH`: objects may transfer next-cycle state into current state.

Instructions should not directly mutate all architectural state when decoded.
They should become operations issued into units. Units reserve resources in the
scoreboard, schedule completions, and commit results in the commit phase.

This prevents ordering bugs where Python loop order lets one component observe
same-cycle writes that hardware would not expose until a later cycle.

## Notes

- Decode metadata is wrapped in instruction objects.
- Existing functional Tensix units are used behind timed unit interfaces.
- Memory and NoC calls flow through transaction models that can gain measured
  latency data over time.
