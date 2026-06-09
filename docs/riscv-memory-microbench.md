# Blackhole RISC-V Memory Microbench

This benchmark covers memory-side behavior for the five RISC-V cores on a
Blackhole Tensix tile. NoC command/register timing and Tensix instruction FIFO
or backend timing should live in a separate Tensix-specific benchmark.

The harness lives in `examples/riscv_memory_bench.py`.

## Quick Read

Current result on logical core `1,2`:

| Probe | Approx adjusted cost |
|---|---:|
| local RISC LDM load/store | `~1.0 cycle/op` |
| L1 fixed-address `lw` | `~2.6 cycles/op` |
| L1 independent `lw` stream | `~1.25-1.6 cycles/load` |
| L1 pointer chase | `~5.0 cycles/load` |
| L1 store | `~1.0 cycle/op` |
| L1 store followed by same-address load | `~6.5 cycles` per pair |
| local LDM store followed by same-address load | `~3.0 cycles` per pair on most roles |
| cross-core LDM window read | `~2.5 cycles/op` |

The L1 load-use probes are best read as total payload time, not as average
per-instruction throughput:

| Probe | Payload | Approx adjusted total |
|---|---|---:|
| `l1_load_use0_2` | `lw` then dependent `add` | `~9 cycles` |
| `l1_load_use1_3` | `lw`, 1 filler op, dependent `add` | `~9 cycles` |
| `l1_load_use2_4` | `lw`, 2 filler ops, dependent `add` | `~9 cycles` |
| `l1_load_use4_6` | `lw`, 4 filler ops, dependent `add` | `~9 cycles` |

That shape suggests the core can spend otherwise-stalled load-use time issuing
independent instructions, even though the long dependent path still costs about
the same total time.

## What This Measures

- L1 fixed-address load throughput
- L1 independent load streams
- L1 pointer chasing
- L1 load-use delay with 0/1/2/4 independent filler instructions
- L1 stores and store-to-load pairs
- local RISC LDM loads/stores through `0xffb00000`
- cross-core LDM window reads through `0xffb14000`, `0xffb16000`, and
  `0xffb18000`

## What This Does Not Measure

- NoC command issue or NoC data movement
- Tensix instruction FIFO push/drain behavior
- Tensix backend units
- DRAM read/write latency

## Wall-Clock Read Overhead

The raw `cycles` column includes the cost of the two wall-clock reads around
each timed loop. The `adj cyc/op` column subtracts the same role's `empty`
probe:

```text
adj = (test_cycles - empty_cycles) / (iterations * ops_per_iter)
```

That subtraction cancels the common wall-clock read overhead and the counted-loop
branch/decrement overhead for same-shaped loops. Raw `cycles` and `cyc/iter`
remain intentionally unadjusted.

## How To Run

From `blackhole-py`:

```sh
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 examples/riscv_memory_bench.py --iters 10000
```

## Run 2026-06-06T20:44:41-04:00

- Core: logical `1,2`
- Iterations per test: `10000`
- Dispatch path: slow dispatch (`TT_USB=1`), one active role per launch

Debug L1 ranges:
- `riscv_core_bench_results` at `0x120000` (1024 bytes)
- `riscv_core_bench_scratch` at `0x124000` (64 bytes)

| role | test | cycles | cyc/iter | adj cyc/op | sink |
|---|---:|---:|---:|---:|---:|
| brisc | empty | 30027 | 3.003 |  | 0x12345679 |
| brisc | l1_lw_fixed1 | 56023 | 5.602 | 2.600 | 0x00124000 |
| brisc | l1_lw_ind4 | 80022 | 8.002 | 1.250 | 0x12345679 |
| brisc | l1_lw_ind8 | 160018 | 16.002 | 1.625 | 0x12345679 |
| brisc | l1_lw_chase1 | 80017 | 8.002 | 4.999 | 0x12345679 |
| brisc | l1_load_use0_2 | 120025 | 12.002 | 4.500 | 0xdb185679 |
| brisc | l1_load_use1_3 | 120026 | 12.003 | 3.000 | 0xdb185679 |
| brisc | l1_load_use2_4 | 120027 | 12.003 | 2.250 | 0xdb185679 |
| brisc | l1_load_use4_6 | 120026 | 12.003 | 1.500 | 0xdb185679 |
| brisc | l1_sw_fixed1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | l1_sw_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| brisc | l1_sw_lw_pair2 | 95024 | 9.502 | 3.250 | 0x12345679 |
| brisc | ldm_lw_fixed1 | 40024 | 4.002 | 1.000 | 0xffb00080 |
| brisc | ldm_lw_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| brisc | ldm_lw_chase1 | 40023 | 4.002 | 1.000 | 0x12345679 |
| brisc | ldm_sw_fixed1 | 40023 | 4.002 | 1.000 | 0x12345679 |
| brisc | ldm_sw_lw_pair2 | 60024 | 6.002 | 1.500 | 0x12345679 |
| brisc | xldm_brisc_lw1 | 55022 | 5.502 | 2.499 | 0xffb00080 |
| brisc | xldm_ncrisc_lw1 | 55023 | 5.502 | 2.500 | 0x00ca00c7 |
| brisc | xldm_trisc0_lw1 | 55022 | 5.502 | 2.499 | 0x00000000 |
| ncrisc | empty | 30024 | 3.002 |  | 0x12345679 |
| ncrisc | l1_lw_fixed1 | 56022 | 5.602 | 2.600 | 0x00124000 |
| ncrisc | l1_lw_ind4 | 81692 | 8.169 | 1.292 | 0x12345679 |
| ncrisc | l1_lw_ind8 | 150792 | 15.079 | 1.510 | 0x12345679 |
| ncrisc | l1_lw_chase1 | 81682 | 8.168 | 5.166 | 0x12345679 |
| ncrisc | l1_load_use0_2 | 120029 | 12.003 | 4.500 | 0xdb185679 |
| ncrisc | l1_load_use1_3 | 122526 | 12.253 | 3.083 | 0xdb185679 |
| ncrisc | l1_load_use2_4 | 122525 | 12.252 | 2.313 | 0xdb185679 |
| ncrisc | l1_load_use4_6 | 122513 | 12.251 | 1.541 | 0xdb185679 |
| ncrisc | l1_sw_fixed1 | 40023 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | l1_sw_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| ncrisc | l1_sw_lw_pair2 | 95026 | 9.503 | 3.250 | 0x12345679 |
| ncrisc | ldm_lw_fixed1 | 40025 | 4.003 | 1.000 | 0xffb00080 |
| ncrisc | ldm_lw_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| ncrisc | ldm_lw_chase1 | 40023 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | ldm_sw_fixed1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | ldm_sw_lw_pair2 | 60024 | 6.002 | 1.500 | 0x12345679 |
| ncrisc | xldm_brisc_lw1 | 55022 | 5.502 | 2.500 | 0xffb00080 |
| ncrisc | xldm_ncrisc_lw1 | 55023 | 5.502 | 2.500 | 0xffb00080 |
| ncrisc | xldm_trisc0_lw1 | 55022 | 5.502 | 2.500 | 0x00000000 |
| trisc0 | empty | 30024 | 3.002 |  | 0x12345679 |
| trisc0 | l1_lw_fixed1 | 56023 | 5.602 | 2.600 | 0x00124000 |
| trisc0 | l1_lw_ind4 | 80024 | 8.002 | 1.250 | 0x12345679 |
| trisc0 | l1_lw_ind8 | 150792 | 15.079 | 1.510 | 0x12345679 |
| trisc0 | l1_lw_chase1 | 80018 | 8.002 | 4.999 | 0x12345679 |
| trisc0 | l1_load_use0_2 | 120031 | 12.003 | 4.500 | 0xdb185679 |
| trisc0 | l1_load_use1_3 | 120028 | 12.003 | 3.000 | 0xdb185679 |
| trisc0 | l1_load_use2_4 | 120028 | 12.003 | 2.250 | 0xdb185679 |
| trisc0 | l1_load_use4_6 | 120031 | 12.003 | 1.500 | 0xdb185679 |
| trisc0 | l1_sw_fixed1 | 40023 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | l1_sw_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc0 | l1_sw_lw_pair2 | 95026 | 9.503 | 3.250 | 0x12345679 |
| trisc0 | ldm_lw_fixed1 | 40025 | 4.003 | 1.000 | 0xffb00080 |
| trisc0 | ldm_lw_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc0 | ldm_lw_chase1 | 40023 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | ldm_sw_fixed1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc0 | ldm_sw_lw_pair2 | 60024 | 6.002 | 1.500 | 0x12345679 |
| trisc0 | xldm_brisc_lw1 | 55022 | 5.502 | 2.500 | 0xffb00080 |
| trisc0 | xldm_ncrisc_lw1 | 55023 | 5.502 | 2.500 | 0xffb00080 |
| trisc0 | xldm_trisc0_lw1 | 55022 | 5.502 | 2.500 | 0xffb00080 |
| trisc1 | empty | 30023 | 3.002 |  | 0x12345679 |
| trisc1 | l1_lw_fixed1 | 56023 | 5.602 | 2.600 | 0x00124000 |
| trisc1 | l1_lw_ind4 | 80022 | 8.002 | 1.250 | 0x12345679 |
| trisc1 | l1_lw_ind8 | 147025 | 14.703 | 1.463 | 0x12345679 |
| trisc1 | l1_lw_chase1 | 80017 | 8.002 | 4.999 | 0x12345679 |
| trisc1 | l1_load_use0_2 | 120027 | 12.003 | 4.500 | 0xdb185679 |
| trisc1 | l1_load_use1_3 | 120027 | 12.003 | 3.000 | 0xdb185679 |
| trisc1 | l1_load_use2_4 | 120026 | 12.003 | 2.250 | 0xdb185679 |
| trisc1 | l1_load_use4_6 | 120025 | 12.002 | 1.500 | 0xdb185679 |
| trisc1 | l1_sw_fixed1 | 40023 | 4.002 | 1.000 | 0x12345679 |
| trisc1 | l1_sw_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc1 | l1_sw_lw_pair2 | 95026 | 9.503 | 3.250 | 0x12345679 |
| trisc1 | ldm_lw_fixed1 | 40024 | 4.002 | 1.000 | 0xffb00080 |
| trisc1 | ldm_lw_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc1 | ldm_lw_chase1 | 40023 | 4.002 | 1.000 | 0x12345679 |
| trisc1 | ldm_sw_fixed1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc1 | ldm_sw_lw_pair2 | 60024 | 6.002 | 1.500 | 0x12345679 |
| trisc1 | xldm_brisc_lw1 | 55022 | 5.502 | 2.500 | 0xffb00080 |
| trisc1 | xldm_ncrisc_lw1 | 55023 | 5.502 | 2.500 | 0xffb00080 |
| trisc1 | xldm_trisc0_lw1 | 55022 | 5.502 | 2.500 | 0xffb00080 |
| trisc2 | empty | 30024 | 3.002 |  | 0x12345679 |
| trisc2 | l1_lw_fixed1 | 56021 | 5.602 | 2.600 | 0x00124000 |
| trisc2 | l1_lw_ind4 | 80025 | 8.002 | 1.250 | 0x12345679 |
| trisc2 | l1_lw_ind8 | 147025 | 14.703 | 1.463 | 0x12345679 |
| trisc2 | l1_lw_chase1 | 80017 | 8.002 | 4.999 | 0x12345679 |
| trisc2 | l1_load_use0_2 | 120026 | 12.003 | 4.500 | 0xdb185679 |
| trisc2 | l1_load_use1_3 | 120027 | 12.003 | 3.000 | 0xdb185679 |
| trisc2 | l1_load_use2_4 | 120026 | 12.003 | 2.250 | 0xdb185679 |
| trisc2 | l1_load_use4_6 | 120025 | 12.002 | 1.500 | 0xdb185679 |
| trisc2 | l1_sw_fixed1 | 40023 | 4.002 | 1.000 | 0x12345679 |
| trisc2 | l1_sw_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc2 | l1_sw_lw_pair2 | 95026 | 9.503 | 3.250 | 0x12345679 |
| trisc2 | ldm_lw_fixed1 | 40024 | 4.002 | 1.000 | 0xffb00080 |
| trisc2 | ldm_lw_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc2 | ldm_lw_chase1 | 40023 | 4.002 | 1.000 | 0x12345679 |
| trisc2 | ldm_sw_fixed1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc2 | ldm_sw_lw_pair2 | 70023 | 7.002 | 2.000 | 0x12345679 |
| trisc2 | xldm_brisc_lw1 | 55022 | 5.502 | 2.500 | 0xffb00080 |
| trisc2 | xldm_ncrisc_lw1 | 55023 | 5.502 | 2.500 | 0xffb00080 |
| trisc2 | xldm_trisc0_lw1 | 55022 | 5.502 | 2.500 | 0xffb00080 |
