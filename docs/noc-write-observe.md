# Blackhole NoC Write Observe

Goal: compare source-side NoC write acknowledgement timing against target-core
visibility of a final sentinel word.

The harness lives in `examples/riscv_noc_write_observe.py`. The sender writes a
payload to peer L1 in 16 KiB chunks. The receiver polls the final word of the
target buffer and records `WALL_CLOCK_L/H` when it observes the expected
sentinel. The sender records start and `noc_write_barrier()` timestamps.

## Runs

Source `1,2`, target `2,2`, 16 KiB on NoC0:

- sender ack/barrier delta from start: `503` cycles
- receiver observed sentinel delta from start: `363` cycles
- observed minus ack: `-140` cycles
- write ack counter delta: `1`

Source `1,2`, target `2,2`, 1 MiB on NoC0:

- sender ack/barrier delta from start: `17133` cycles
- receiver observed sentinel delta from start: `16980` cycles
- observed minus ack: `-153` cycles
- write ack counter delta: `64`

Source `1,2`, target `2,2`, 1 MiB on NoC1:

- sender ack/barrier delta from start: `17130` cycles
- receiver observed sentinel delta from start: `17129` cycles
- observed minus ack: `-1` cycle
- write ack counter delta: `64`

In these runs, target L1 visibility was not later than the source-side write
ack barrier. The source barrier looks conservative for NoC0 by roughly 150
cycles and essentially aligned for NoC1 on this adjacent pair.
