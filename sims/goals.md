# sims/: goals

## The goal

Writing kernels and doing performance analysis for Blackhole should not need the hardware.

The card is deterministic enough to count cycles for everything: simulate the RISC-V cores, the Tensix
instructions and the NoC transactions, and know how many cycles a kernel will take. With a simulator
that close to the card, an LLM can sit in a loop writing and optimizing kernels without waiting on, or
breaking, a real card. Target error for a good simulation against hardware: **under 3% in cycle count**.

The hardware quirks (places where NOPs are required, or a hazard gives a strange result) count as behaviour
to model, not noise. In every test so far, the "undefined" behaviour has been the same every time, so it
can be measured and written down like everything else.

## Scope

- **Abstraction level:** ttrv is the highest level we target. It sits just above the RISC-V that runs on
  the device: it handles register allocation and lifetimes, which are hard for a person or a model to get
  right by hand (a clobbered register breaks a program silently). It still exposes everything the device
  can do and leaves every choice about how a kernel runs to the author. It is not a compiler: no SSA, no
  optimization passes. Going higher hides how the device works.
- **What gets measured:** every instruction that can run on the device is timed, benchmarked and
  categorized into one full timing table for the chip. Every finding is backed by hardware runs, and the
  experiment that produced it is kept with it.
- **What the simulator must cover:** exactly what the Llama 3 kernels (`kernels/llama3-*`) and the
  firmware that runs them use, modelled accurately enough to reach the error target. Features no kernel
  uses are out of scope until a kernel needs them.
- **Longer term:** a tinygrad backend for Blackhole that runs at reasonable speed (about a 6-month
  horizon). That is the hardest part.

## How the probes run

`sims/probes/`: plain C with inline asm (clang, rv32im, no SFPI), launched directly on blackhole-py's
resident firmware by `tile.py`, driven by `run.py`.

- Every wait inside a kernel is bounded, so a stuck wait returns to firmware rather than hanging.
- The card is never reset automatically. A run stops at the first host-side failure, so a person
  looks at the card and resets it by hand if needed.
- Results go to `sims/results/*.jsonl`, one line per case. A rerun resumes from that file.

Status of every measurement category, and what is still open: `STATUS.md`. Ground truth for the simulator: `KERNELS.md`.
