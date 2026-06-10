# microbenching

Hardware microbenchmarks, analytical/timing models, and their result reports for
the blackhole-py framework. Kept out of `examples/` so that `examples/` stays
focused on real kernels (matmul, add1, DRISC POCs, `examples/llama/`).

## Running

Every script is directly runnable from any cwd — no `PYTHONPATH` needed:

```bash
python3 microbenching/riscv/riscv_core_bench.py --iters 10000
```

Each script bootstraps `_bench_path.py`, which adds the repo root, `examples/`,
and all category dirs to `sys.path` (the benches cross-import each other and the
kernel examples).

On the shared device, run through the `tt-device-queue` MCP, not directly.
Add `TT_USB=1` and a `BLACKHOLE_RUN_TIMEOUT_S` like existing queue jobs.

## Layout

Scripts in category dirs; each has its writeup under the matching `docs/<cat>/`.

### riscv/ — RISC-V core behavior
| script | doc | status |
|---|---|---|
| `riscv_core_bench.py` | `docs/riscv/riscv-core-microbench.md` | done |
| `riscv_memory_bench.py` | `docs/riscv/riscv-memory-microbench.md` | done |
| `riscv_special_instr_bench.py` | `docs/riscv/riscv-special-instr-microbench.md` | done |
| `riscv_contention_bench.py` | `docs/riscv/riscv-contention-microbench.md` | done |
| `riscv_wall_clock_skew.py` | `docs/riscv/wall-clock-skew.md` | done |

### noc/ — NoC and DRAM-over-NoC
| script | doc | status |
|---|---|---|
| `riscv_noc_bench.py` | `docs/noc/noc-microbench.md` | done |
| `riscv_noc_aggregate.py` | `docs/noc/noc-aggregate.md` | done |
| `riscv_noc_dual_dm_aggregate.py` | `docs/noc/noc-dual-dm-aggregate.md` | done (supersedes the deleted `riscv_noc_dual_aggregate.py`, quarantined for wedging the PCIe bus; see `docs/noc/noc-dual-aggregate.md`) |
| `riscv_noc_hop_sweep.py` | `docs/noc/noc-hop-sweep.md` | done |
| `riscv_noc_stream_sweep.py` | `docs/noc/noc-stream-sweep.md` | done |
| `riscv_noc_write_observe.py` | `docs/noc/noc-write-observe.md` | done |
| `riscv_noc_arbitration_bench.py` | `docs/noc/noc-arbitration.md`, plan `docs/noc/noc-arbitration-bench-plan.md` | blocked: full matrix gated on a clean K=2 smoke (0 bad counters/sentinels) |
| `riscv_noc_contention_probe.py` | `docs/noc/noc-contention.md` | in progress |
| `riscv_noc_topology_probe.py` | `docs/noc/noc-topology.md`, smoke `docs/noc/noc-legacy-smoke.md` | in progress |
| `noc_topology.py` | helper (offline path/link model; `python3 noc_topology.py` self-tests) | done |
| `microbench_noc_mcast_mixed.py` | `docs/noc/noc-mcast-mixed-microbench.md` | done |
| `riscv_dram_noc_bench.py` | `docs/noc/dram-noc-bench.md`, plan `docs/noc/dram-noc-bench-plan.md` | done |

### tensix/ — Tensix compute pipeline
| script | doc | status |
|---|---|---|
| `tensix_instr_bench.py` | `docs/tensix/tensix-instr-microbench.md` | done |
| `microbench_math_backend.py` | `docs/tensix/math-backend-microbench.md` | done |
| `microbench_math_mvmul.py` | `docs/tensix/math-mvmul.md` | scaffold |
| `microbench_unpack_backend.py` | `docs/tensix/unpack-backend-microbench.md` | done |
| `microbench_pack_backend.py` | `docs/tensix/pack-backend-microbench.md` | done; `--validate` quarantined |
| `microbench_sem_cb.py` | `docs/tensix/sem-cb-microbench.md` | done |
| `microbench_drisc_overlap_output.py` | `docs/tensix/drisc-overlap-output-microbench.md` | done |
| `microbench_xmov.py` | `docs/tensix/xmov-microbench.md` | DMA-reg ops done; **TTMOVA2D/D2A/D2B + debug moves QUARANTINED** (crash risk) |
| `microbench_sfpu.py` | `docs/tensix/sfpu-microbench.md` | **QUARANTINED** — validation/readback path; re-enable checklist in doc |
| `microbench_sfpu_transcendental.py` | (results pending) | needs device |
| `microbench_dest_readback.py` | `docs/tensix/dest-readback.md` | build-only proven; hardware run quarantined |
| plan | `docs/tensix/tensix-backend-bench-plan.md` | — |

### matmul/ — matmul ceiling models
| script | doc |
|---|---|
| `matmul_shape_sweep.py`, `matmul_solver.py`, `matmul_static_model.py` | `docs/matmul/matmul-bf16-ceiling.md` |

### models/ — cross-bench timing model & summary
| script | doc |
|---|---|
| `program_timing_model.py`, `microbench_summary.py` | `docs/models/program-timing-microbench-summary.md` |

## Quarantine / safety

Known device-wedging paths (each doc has details + a re-enable checklist):
dual-NoC same-core sweeps (the deleted `riscv_noc_dual_aggregate.py`; see
`docs/noc/noc-dual-aggregate.md`), XMOV mover instructions,
SFPU validation/readback, dest/src debug-array readback. A wedge takes the card
off the PCIe bus and needs a **cold power cycle** (warm reboot does not recover
it — bridge link retraining fails at boot).

## Shims

- `_bench_path.py` — sys.path bootstrap, see Running.
- `_examples_path.py` — legacy shim (adds `examples/`); superseded by
  `_bench_path.py`, kept for back-compat.
