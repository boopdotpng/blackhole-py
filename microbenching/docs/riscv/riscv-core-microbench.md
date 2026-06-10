# Blackhole RISC-V Core Microbench

Goal: measure the execution behavior of the five small RISC-V cores on one
Blackhole Tensix tile before adding Tensix instruction FIFO or command queue
benchmarks.

The initial harness lives in `microbenching/riscv/riscv_core_bench.py`.

Special cases that need separate handling (`jalr`, CSR reads, load/store width
variants, and all branch opcodes) live in
`microbenching/riscv/riscv_special_instr_bench.py` and are reported in
`microbenching/docs/riscv/riscv-special-instr-microbench.md`.

Memory-specific probes live in `microbenching/riscv/riscv_memory_bench.py` and are reported
in `microbenching/docs/riscv/riscv-memory-microbench.md`.

## Quick Read

Current result: for pure RISC-V instruction streams, BRISC, NCRISC, and
TRISC0/1/2 behave almost identically on logical core `1,2`.

Baseline loop overhead is about `3` wall-clock cycles per iteration. After
subtracting that baseline:

| Probe | Approx adjusted cost |
|---|---:|
| base ALU/immediate/shift/compare/control ops | `~1.0 cycle/op` |
| `mul`, `mulhu` dependent chains | `~1.75 cycles/op` |
| independent `mul` issue | `~1.0 cycle/op` |
| `divu`, `remu` dependent chains | `~6.0 cycles/op` |
| `fence` | `~4.0 cycles/op` |
| dependent L1 load | `~5.0 cycles/op` |
| L1 stores | `~1.0 cycle/op` |

NCRISC measured slightly higher on dependent L1 load in the current run
(`5.165` adjusted cycles vs about `5.0` on the others). Treat that as a
single-run observation until repeated across cores and tiles.

## What This Measures

This is intentionally only a RISC-V execution benchmark. It does not measure
Tensix instruction FIFO behavior, Tensix backend latency, NoC throughput, or
command queue dispatch yet.

- Force slow dispatch with `TT_USB=1` so command queue behavior is not part of
  the first measurements.
- Run one active role per launch: `brisc`, `ncrisc`, `trisc0`, `trisc1`, or
  `trisc2`.
- Measure only inside the role kernel using `WALL_CLOCK_L/H` at
  `0xFFB121F0/0xFFB121F8`.
- Store raw start/end timestamps in an L1 debug range at `0x120000`;
  host-side analysis reads the range through a TLB window, computes deltas, and
  subtracts the empty-loop baseline.
- Treat an all-`0xff` L1 readback as device failure, not benchmark data.

## How To Run

From `blackhole-py`:

```sh
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 microbenching/riscv/riscv_core_bench.py --iters 10000
```

Useful options:

- `--roles brisc trisc1`: run only selected RISC roles.
- `--core X,Y`: choose the logical Tensix core.
- `--no-report`: print results without appending this file.

## L1 Result Layout

The benchmark writes records into L1 and the host reads them back through a TLB
window after the launch completes.

| Range | Address | Size | Purpose |
|---|---:|---:|---|
| `riscv_core_bench_results` | `0x120000` | `2272` bytes | header + timing records |
| `riscv_core_bench_scratch` | `0x124000` | `64` bytes | load/store probe scratch |

The result range starts with a fixed header, followed by one record per probe.
Each record includes the role id, test id, iteration count, ops per iteration,
raw start/end wall-clock values, and a sink word to keep generated code from
collapsing into dead work.

## Probes

The current pure instruction suite covers:

- empty counted loop baseline
- NOP, `lui`, `auipc`
- immediate ops: `addi`, `xori`, `ori`, `andi`, `sltiu`
- shifts and extensions: `slli`, `srli`, `srai`, `ctz`, `sext_b`, `sext_h`,
  `zext_h`
- register ALU/compare ops: `add`, `sub`, `xor`, `or`, `and`, `sll`, `srl`,
  `sra`, `slt`, `sltu`
- custom-ish integer helpers: `sh1add`, `sh2add`, `sh3add`, `min`, `minu`,
  `maxu`
- multiply/divide: `mul`, `mulhu`, `divu`, `remu`
- simple control flow: taken branch, not-taken branch, `jal`
- `fence`
- dependent L1 load
- repeated L1 stores

The last two probes are memory-side sanity checks and are not part of the pure
instruction layer. They stay in the table because they are useful comparators.
All numbers still include the counted-loop branch overhead until the
`adj cyc/op` column subtracts the empty-loop baseline.

## Reading The Table

- `cycles`: raw wall-clock delta for the whole timed loop.
- `cyc/iter`: raw cycles divided by iteration count.
- `adj cyc/op`: `(test_cycles - empty_loop_cycles) / total_payload_ops`.
- `sink`: final value of the sink register, useful as a cheap sanity check.

The raw columns include the two wall-clock reads around each timed loop. The
adjusted column subtracts the same role's `empty` probe, which has the same
wall-clock read pair and counted-loop branch/decrement shape. That cancellation
is why `adj cyc/op` is the column to use for instruction timing.

For dependency-chain probes such as `addi_dep8`, `mul_dep4`, and `divu_dep1`,
`adj cyc/op` is a rough latency/throughput signal for a dependent stream. For
independent or repeated-store probes, it is closer to issue cost.

## Run 2026-06-06T20:36:49-04:00

- Core: logical `1,2`
- Iterations per test: `10000`
- Dispatch path: slow dispatch (`TT_USB=1`), one active role per launch

Debug L1 ranges:
- `riscv_core_bench_results` at `0x120000` (2272 bytes)
- `riscv_core_bench_scratch` at `0x124000` (64 bytes)

| role | test | cycles | cyc/iter | adj cyc/op | sink |
|---|---:|---:|---:|---:|---:|
| brisc | empty | 30027 | 3.003 |  | 0x12345679 |
| brisc | nop8 | 110026 | 11.003 | 1.000 | 0x12345679 |
| brisc | lui8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| brisc | auipc8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| brisc | addi_dep8 | 110023 | 11.002 | 1.000 | 0x12358ef9 |
| brisc | xori_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| brisc | ori_dep8 | 110023 | 11.002 | 1.000 | 0x1234577b |
| brisc | andi_dep8 | 110023 | 11.002 | 1.000 | 0x00000679 |
| brisc | sltiu_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| brisc | slli_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| brisc | srli_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| brisc | srai_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| brisc | ctz_dep4 | 70023 | 7.002 | 1.000 | 0x00000000 |
| brisc | sext_b_dep8 | 110023 | 11.002 | 1.000 | 0x00000079 |
| brisc | sext_h_dep8 | 110023 | 11.002 | 1.000 | 0x00005679 |
| brisc | zext_h_dep8 | 110023 | 11.002 | 1.000 | 0x00005679 |
| brisc | add_dep8 | 110023 | 11.002 | 1.000 | 0x1237fff9 |
| brisc | sub_dep8 | 110023 | 11.002 | 1.000 | 0x1230acf9 |
| brisc | addi_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| brisc | xor_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| brisc | or_dep8 | 110023 | 11.002 | 1.000 | 0x1234567b |
| brisc | and_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| brisc | sll_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| brisc | srl_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| brisc | sra_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| brisc | slt_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| brisc | sltu_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| brisc | sh1add_dep8 | 110023 | 11.002 | 1.000 | 0xfffffffd |
| brisc | sh2add_dep8 | 110023 | 11.002 | 1.000 | 0xffffffff |
| brisc | sh3add_dep8 | 110023 | 11.002 | 1.000 | 0xdb6db6db |
| brisc | min_dep8 | 110023 | 11.002 | 1.000 | 0x00000003 |
| brisc | minu_dep8 | 110023 | 11.002 | 1.000 | 0x00000003 |
| brisc | maxu_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| brisc | add_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| brisc | xor_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| brisc | mul_dep4 | 100025 | 10.002 | 1.750 | 0x4150db79 |
| brisc | mulhu_dep4 | 100024 | 10.002 | 1.750 | 0x00000000 |
| brisc | mul_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| brisc | divu_dep1 | 90256 | 9.026 | 6.023 | 0x00000000 |
| brisc | remu_dep1 | 90052 | 9.005 | 6.003 | 0x00000001 |
| brisc | branch_taken1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| brisc | branch_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| brisc | jal1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| brisc | fence1 | 70024 | 7.002 | 4.000 | 0x12345679 |
| brisc | load_l1_dep1 | 80018 | 8.002 | 4.999 | 0x12345679 |
| brisc | store_l1_4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| ncrisc | empty | 30024 | 3.002 |  | 0x12345679 |
| ncrisc | nop8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| ncrisc | lui8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| ncrisc | auipc8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| ncrisc | addi_dep8 | 110023 | 11.002 | 1.000 | 0x12358ef9 |
| ncrisc | xori_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| ncrisc | ori_dep8 | 110023 | 11.002 | 1.000 | 0x1234577b |
| ncrisc | andi_dep8 | 110023 | 11.002 | 1.000 | 0x00000679 |
| ncrisc | sltiu_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| ncrisc | slli_dep8 | 110026 | 11.003 | 1.000 | 0x00000000 |
| ncrisc | srli_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| ncrisc | srai_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| ncrisc | ctz_dep4 | 70023 | 7.002 | 1.000 | 0x00000000 |
| ncrisc | sext_b_dep8 | 110023 | 11.002 | 1.000 | 0x00000079 |
| ncrisc | sext_h_dep8 | 110023 | 11.002 | 1.000 | 0x00005679 |
| ncrisc | zext_h_dep8 | 110023 | 11.002 | 1.000 | 0x00005679 |
| ncrisc | add_dep8 | 110023 | 11.002 | 1.000 | 0x1237fff9 |
| ncrisc | sub_dep8 | 110023 | 11.002 | 1.000 | 0x1230acf9 |
| ncrisc | addi_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| ncrisc | xor_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| ncrisc | or_dep8 | 110023 | 11.002 | 1.000 | 0x1234567b |
| ncrisc | and_dep8 | 110026 | 11.003 | 1.000 | 0x00000001 |
| ncrisc | sll_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| ncrisc | srl_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| ncrisc | sra_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| ncrisc | slt_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| ncrisc | sltu_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| ncrisc | sh1add_dep8 | 110023 | 11.002 | 1.000 | 0xfffffffd |
| ncrisc | sh2add_dep8 | 110023 | 11.002 | 1.000 | 0xffffffff |
| ncrisc | sh3add_dep8 | 110023 | 11.002 | 1.000 | 0xdb6db6db |
| ncrisc | min_dep8 | 110023 | 11.002 | 1.000 | 0x00000003 |
| ncrisc | minu_dep8 | 110023 | 11.002 | 1.000 | 0x00000003 |
| ncrisc | maxu_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| ncrisc | add_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| ncrisc | xor_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| ncrisc | mul_dep4 | 100024 | 10.002 | 1.750 | 0x4150db79 |
| ncrisc | mulhu_dep4 | 100024 | 10.002 | 1.750 | 0x00000000 |
| ncrisc | mul_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| ncrisc | divu_dep1 | 90256 | 9.026 | 6.023 | 0x00000000 |
| ncrisc | remu_dep1 | 90052 | 9.005 | 6.003 | 0x00000001 |
| ncrisc | branch_taken1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| ncrisc | branch_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| ncrisc | jal1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| ncrisc | fence1 | 70025 | 7.003 | 4.000 | 0x12345679 |
| ncrisc | load_l1_dep1 | 81679 | 8.168 | 5.165 | 0x12345679 |
| ncrisc | store_l1_4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc0 | empty | 30023 | 3.002 |  | 0x12345679 |
| trisc0 | nop8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc0 | lui8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc0 | auipc8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc0 | addi_dep8 | 110023 | 11.002 | 1.000 | 0x12358ef9 |
| trisc0 | xori_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc0 | ori_dep8 | 110023 | 11.002 | 1.000 | 0x1234577b |
| trisc0 | andi_dep8 | 110023 | 11.002 | 1.000 | 0x00000679 |
| trisc0 | sltiu_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc0 | slli_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc0 | srli_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc0 | srai_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc0 | ctz_dep4 | 70023 | 7.002 | 1.000 | 0x00000000 |
| trisc0 | sext_b_dep8 | 110023 | 11.002 | 1.000 | 0x00000079 |
| trisc0 | sext_h_dep8 | 110023 | 11.002 | 1.000 | 0x00005679 |
| trisc0 | zext_h_dep8 | 110023 | 11.002 | 1.000 | 0x00005679 |
| trisc0 | add_dep8 | 110023 | 11.002 | 1.000 | 0x1237fff9 |
| trisc0 | sub_dep8 | 110025 | 11.002 | 1.000 | 0x1230acf9 |
| trisc0 | addi_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc0 | xor_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc0 | or_dep8 | 110023 | 11.002 | 1.000 | 0x1234567b |
| trisc0 | and_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc0 | sll_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc0 | srl_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc0 | sra_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc0 | slt_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc0 | sltu_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc0 | sh1add_dep8 | 110023 | 11.002 | 1.000 | 0xfffffffd |
| trisc0 | sh2add_dep8 | 110023 | 11.002 | 1.000 | 0xffffffff |
| trisc0 | sh3add_dep8 | 110023 | 11.002 | 1.000 | 0xdb6db6db |
| trisc0 | min_dep8 | 110023 | 11.002 | 1.000 | 0x00000003 |
| trisc0 | minu_dep8 | 110023 | 11.002 | 1.000 | 0x00000003 |
| trisc0 | maxu_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc0 | add_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc0 | xor_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc0 | mul_dep4 | 100024 | 10.002 | 1.750 | 0x4150db79 |
| trisc0 | mulhu_dep4 | 100024 | 10.002 | 1.750 | 0x00000000 |
| trisc0 | mul_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc0 | divu_dep1 | 90256 | 9.026 | 6.023 | 0x00000000 |
| trisc0 | remu_dep1 | 90052 | 9.005 | 6.003 | 0x00000001 |
| trisc0 | branch_taken1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| trisc0 | branch_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc0 | jal1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| trisc0 | fence1 | 70024 | 7.002 | 4.000 | 0x12345679 |
| trisc0 | load_l1_dep1 | 80020 | 8.002 | 5.000 | 0x12345679 |
| trisc0 | store_l1_4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc1 | empty | 30023 | 3.002 |  | 0x12345679 |
| trisc1 | nop8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc1 | lui8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc1 | auipc8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc1 | addi_dep8 | 110023 | 11.002 | 1.000 | 0x12358ef9 |
| trisc1 | xori_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc1 | ori_dep8 | 110023 | 11.002 | 1.000 | 0x1234577b |
| trisc1 | andi_dep8 | 110023 | 11.002 | 1.000 | 0x00000679 |
| trisc1 | sltiu_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc1 | slli_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc1 | srli_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc1 | srai_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc1 | ctz_dep4 | 70023 | 7.002 | 1.000 | 0x00000000 |
| trisc1 | sext_b_dep8 | 110023 | 11.002 | 1.000 | 0x00000079 |
| trisc1 | sext_h_dep8 | 110023 | 11.002 | 1.000 | 0x00005679 |
| trisc1 | zext_h_dep8 | 110023 | 11.002 | 1.000 | 0x00005679 |
| trisc1 | add_dep8 | 110023 | 11.002 | 1.000 | 0x1237fff9 |
| trisc1 | sub_dep8 | 110023 | 11.002 | 1.000 | 0x1230acf9 |
| trisc1 | addi_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc1 | xor_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc1 | or_dep8 | 110023 | 11.002 | 1.000 | 0x1234567b |
| trisc1 | and_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc1 | sll_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc1 | srl_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc1 | sra_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc1 | slt_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc1 | sltu_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc1 | sh1add_dep8 | 110023 | 11.002 | 1.000 | 0xfffffffd |
| trisc1 | sh2add_dep8 | 110023 | 11.002 | 1.000 | 0xffffffff |
| trisc1 | sh3add_dep8 | 110023 | 11.002 | 1.000 | 0xdb6db6db |
| trisc1 | min_dep8 | 110023 | 11.002 | 1.000 | 0x00000003 |
| trisc1 | minu_dep8 | 110023 | 11.002 | 1.000 | 0x00000003 |
| trisc1 | maxu_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc1 | add_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc1 | xor_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc1 | mul_dep4 | 100024 | 10.002 | 1.750 | 0x4150db79 |
| trisc1 | mulhu_dep4 | 100025 | 10.002 | 1.750 | 0x00000000 |
| trisc1 | mul_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc1 | divu_dep1 | 90256 | 9.026 | 6.023 | 0x00000000 |
| trisc1 | remu_dep1 | 90052 | 9.005 | 6.003 | 0x00000001 |
| trisc1 | branch_taken1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | branch_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc1 | jal1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| trisc1 | fence1 | 70024 | 7.002 | 4.000 | 0x12345679 |
| trisc1 | load_l1_dep1 | 80018 | 8.002 | 5.000 | 0x12345679 |
| trisc1 | store_l1_4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc2 | empty | 30023 | 3.002 |  | 0x12345679 |
| trisc2 | nop8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc2 | lui8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc2 | auipc8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc2 | addi_dep8 | 110023 | 11.002 | 1.000 | 0x12358ef9 |
| trisc2 | xori_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc2 | ori_dep8 | 110023 | 11.002 | 1.000 | 0x1234577b |
| trisc2 | andi_dep8 | 110023 | 11.002 | 1.000 | 0x00000679 |
| trisc2 | sltiu_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc2 | slli_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc2 | srli_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc2 | srai_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc2 | ctz_dep4 | 70023 | 7.002 | 1.000 | 0x00000000 |
| trisc2 | sext_b_dep8 | 110023 | 11.002 | 1.000 | 0x00000079 |
| trisc2 | sext_h_dep8 | 110023 | 11.002 | 1.000 | 0x00005679 |
| trisc2 | zext_h_dep8 | 110023 | 11.002 | 1.000 | 0x00005679 |
| trisc2 | add_dep8 | 110023 | 11.002 | 1.000 | 0x1237fff9 |
| trisc2 | sub_dep8 | 110023 | 11.002 | 1.000 | 0x1230acf9 |
| trisc2 | addi_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc2 | xor_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc2 | or_dep8 | 110023 | 11.002 | 1.000 | 0x1234567b |
| trisc2 | and_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc2 | sll_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc2 | srl_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc2 | sra_dep8 | 110023 | 11.002 | 1.000 | 0x00000000 |
| trisc2 | slt_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc2 | sltu_dep8 | 110023 | 11.002 | 1.000 | 0x00000001 |
| trisc2 | sh1add_dep8 | 110023 | 11.002 | 1.000 | 0xfffffffd |
| trisc2 | sh2add_dep8 | 110023 | 11.002 | 1.000 | 0xffffffff |
| trisc2 | sh3add_dep8 | 110023 | 11.002 | 1.000 | 0xdb6db6db |
| trisc2 | min_dep8 | 110023 | 11.002 | 1.000 | 0x00000003 |
| trisc2 | minu_dep8 | 110023 | 11.002 | 1.000 | 0x00000003 |
| trisc2 | maxu_dep8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc2 | add_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc2 | xor_ind8 | 110023 | 11.002 | 1.000 | 0x12345679 |
| trisc2 | mul_dep4 | 100024 | 10.002 | 1.750 | 0x4150db79 |
| trisc2 | mulhu_dep4 | 100025 | 10.002 | 1.750 | 0x00000000 |
| trisc2 | mul_ind4 | 70023 | 7.002 | 1.000 | 0x12345679 |
| trisc2 | divu_dep1 | 90256 | 9.026 | 6.023 | 0x00000000 |
| trisc2 | remu_dep1 | 90052 | 9.005 | 6.003 | 0x00000001 |
| trisc2 | branch_taken1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | branch_not_taken1 | 40024 | 4.002 | 1.000 | 0x12345679 |
| trisc2 | jal1 | 40027 | 4.003 | 1.000 | 0x12345679 |
| trisc2 | fence1 | 70024 | 7.002 | 4.000 | 0x12345679 |
| trisc2 | load_l1_dep1 | 80018 | 8.002 | 5.000 | 0x12345679 |
| trisc2 | store_l1_4 | 70023 | 7.002 | 1.000 | 0x12345679 |
