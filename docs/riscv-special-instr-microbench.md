# Blackhole RISC-V Special Instruction Microbench

This companion benchmark covers RISC-V instructions that need separate handling
from the pure arithmetic/control suite in `examples/riscv_core_bench.py`.

The harness lives in `examples/riscv_special_instr_bench.py`.

## Quick Read

Current result on logical core `1,2`:

| Probe | Approx adjusted cost |
|---|---:|
| `lbu`, `lhu`, `lw` from L1 scratch | `~2.6 cycles/op` |
| `sb`, `sh`, `sw` to L1 scratch | `~1.0 cycle/op` |
| all branch forms, taken and not taken | `~1.0 cycle/op` |
| `auipc` + `addi` + `jalr` sequence | `~1.0 cycle/op` per instruction |
| read-only `csrrs` / `csrrc` | `~4.0 cycles/op` |

All five RISCs were essentially identical for this special suite.

## What This Measures

- L1 load/store width variants: `lbu`, `lhu`, `lw`, `sb`, `sh`, `sw`
- all conditional branch opcodes in taken and not-taken form
- a PC-relative `auipc` + `addi` + `jalr` sequence
- read-only CSR probes using `csrrs rd, zero, 0x7c0` and
  `csrrc rd, zero, 0x7c0`

The `jalr` probe is not an isolated single-instruction measurement. It times the
three-instruction PC-relative sequence needed to safely give `jalr` a valid
target inside the timed loop.

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
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 examples/riscv_special_instr_bench.py --iters 10000
```

## Run 2026-06-06T20:40:41-04:00

- Core: logical `1,2`
- Iterations per test: `10000`
- Dispatch path: slow dispatch (`TT_USB=1`), one active role per launch

Debug L1 ranges:
- `riscv_core_bench_results` at `0x120000` (1120 bytes)
- `riscv_core_bench_scratch` at `0x124000` (64 bytes)

| role | test | cycles | cyc/iter | adj cyc/op | sink |
|---|---:|---:|---:|---:|---:|
| brisc | empty | 30027 | 3.003 |  | 0x12345679 |
| brisc | lbu_l1_1 | 56023 | 5.602 | 2.600 | 0x00000000 |
| brisc | lhu_l1_1 | 56022 | 5.602 | 2.599 | 0x00004000 |
| brisc | lw_l1_1 | 56023 | 5.602 | 2.600 | 0x00124000 |
| brisc | sb_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | sh_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | sw_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | beq_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| brisc | beq_not_taken1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| brisc | bne_taken1 | 40031 | 4.003 | 1.000 | 0x12345679 |
| brisc | bne_not_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| brisc | blt_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | blt_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | bge_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | bge_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | bltu_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | bltu_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | bgeu_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | bgeu_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | auipc_addi_jalr3 | 60028 | 6.003 | 1.000 | 0x12345679 |
| brisc | csrrs_read4 | 190025 | 19.003 | 4.000 | 0x00060008 |
| brisc | csrrc_read4 | 190025 | 19.003 | 4.000 | 0x00060008 |
| ncrisc | empty | 30024 | 3.002 |  | 0x12345679 |
| ncrisc | lbu_l1_1 | 56021 | 5.602 | 2.600 | 0x00000000 |
| ncrisc | lhu_l1_1 | 56022 | 5.602 | 2.600 | 0x00004000 |
| ncrisc | lw_l1_1 | 56022 | 5.602 | 2.600 | 0x00124000 |
| ncrisc | sb_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | sh_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | sw_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | beq_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| ncrisc | beq_not_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| ncrisc | bne_taken1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| ncrisc | bne_not_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| ncrisc | blt_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | blt_not_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| ncrisc | bge_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | bge_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | bltu_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | bltu_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | bgeu_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | bgeu_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | auipc_addi_jalr3 | 60028 | 6.003 | 1.000 | 0x12345679 |
| ncrisc | csrrs_read4 | 190025 | 19.003 | 4.000 | 0x00060008 |
| ncrisc | csrrc_read4 | 190025 | 19.003 | 4.000 | 0x00060008 |
| trisc0 | empty | 30024 | 3.002 |  | 0x12345679 |
| trisc0 | lbu_l1_1 | 56023 | 5.602 | 2.600 | 0x00000000 |
| trisc0 | lhu_l1_1 | 56022 | 5.602 | 2.600 | 0x00004000 |
| trisc0 | lw_l1_1 | 56024 | 5.602 | 2.600 | 0x00124000 |
| trisc0 | sb_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | sh_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | sw_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | beq_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| trisc0 | beq_not_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| trisc0 | bne_taken1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| trisc0 | bne_not_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| trisc0 | blt_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | blt_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | bge_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | bge_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | bltu_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | bltu_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | bgeu_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | bgeu_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | auipc_addi_jalr3 | 60028 | 6.003 | 1.000 | 0x12345679 |
| trisc0 | csrrs_read4 | 190025 | 19.003 | 4.000 | 0x00060008 |
| trisc0 | csrrc_read4 | 190025 | 19.003 | 4.000 | 0x00060008 |
| trisc1 | empty | 30023 | 3.002 |  | 0x12345679 |
| trisc1 | lbu_l1_1 | 56023 | 5.602 | 2.600 | 0x00000000 |
| trisc1 | lhu_l1_1 | 56023 | 5.602 | 2.600 | 0x00004000 |
| trisc1 | lw_l1_1 | 56023 | 5.602 | 2.600 | 0x00124000 |
| trisc1 | sb_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc1 | sh_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc1 | sw_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc1 | beq_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | beq_not_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | bne_taken1 | 40030 | 4.003 | 1.001 | 0x12345679 |
| trisc1 | bne_not_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | blt_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | blt_not_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | bge_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | bge_not_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | bltu_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | bltu_not_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | bgeu_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | bgeu_not_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | auipc_addi_jalr3 | 60029 | 6.003 | 1.000 | 0x12345679 |
| trisc1 | csrrs_read4 | 190025 | 19.003 | 4.000 | 0x00060008 |
| trisc1 | csrrc_read4 | 190025 | 19.003 | 4.000 | 0x00060008 |
| trisc2 | empty | 30023 | 3.002 |  | 0x12345679 |
| trisc2 | lbu_l1_1 | 56023 | 5.602 | 2.600 | 0x00000000 |
| trisc2 | lhu_l1_1 | 56022 | 5.602 | 2.600 | 0x00004000 |
| trisc2 | lw_l1_1 | 56023 | 5.602 | 2.600 | 0x00124000 |
| trisc2 | sb_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc2 | sh_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc2 | sw_l1_1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc2 | beq_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | beq_not_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | bne_taken1 | 40030 | 4.003 | 1.001 | 0x12345679 |
| trisc2 | bne_not_taken1 | 40028 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | blt_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | blt_not_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | bge_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | bge_not_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | bltu_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | bltu_not_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | bgeu_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | bgeu_not_taken1 | 40025 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | auipc_addi_jalr3 | 60029 | 6.003 | 1.000 | 0x12345679 |
| trisc2 | csrrs_read4 | 190025 | 19.003 | 4.000 | 0x00060008 |
| trisc2 | csrrc_read4 | 190025 | 19.003 | 4.000 | 0x00060008 |
