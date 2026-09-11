# 1B projection and RISC-V investigation

Measured September 7, 2026, exclusively on **card 0**, eight DRAM banks and
117 projection workers. Same Llama 3.2 1B BF16 weights, HiFi2 arithmetic,
16 attention workers and 83 launches/token as [round two](decode-fusion-round2.md).
No 8B experiments were run.

## Result

| Fixed-length generation, three prompts | Round two | This round |
|---|---:|---:|
| 64 tokens/prompt, contexts 42–108 | 152.34 tok/s | **153.37 tok/s** |
| 512 tokens/prompt, contexts 42–556 | 148.24 tok/s | **149.22 tok/s** |

This is a modest improvement of about 0.7%, not a breakthrough toward 200 tok/s.
Timings include the complete decode call and token readback, excluding startup,
prompt ingestion and diagnostic logit reads. Comparisons use recorded card-0
round-two results, not a simultaneous baseline. Small timing differences should
not be interpreted as precise causal effects.

All **1,728 token IDs and 120 sampled complete BF16 logit buffers** match the
saved round-two results exactly. CPU tests exercise all nine supported
storage/attention-worker combinations for lowering and L1 residency, and execute
the emitted NoC command setup instructions to check the ordered MMIO writes and
input-register preservation on both NoCs.

Raw results: [64-token generation](benchmarks/llama3_round3_final_64.json),
[512-token generation](benchmarks/llama3_round3_final_512.json),
[exact comparisons](benchmarks/llama3_round3_validation.json), and
[fixed-context attribution](benchmarks/llama3_round3_final_profile.json).

## Retained instruction improvements

1. Hoist the paired unpack MOP and invariant ADC configuration out of the
   projection row loop. Address updates and synchronization still happen per tile.
2. Use the existing tile-offset calculation for scalar output placement,
   eliminating repeated shifts and masks.
3. Build NoC commands with one NIU base address and immediate-offset stores;
   use `x0` for zero words. A representative 2 KiB read command drops from
   **47 to 20 RISC-V instructions**, with the same twelve ordered register
   writes. This count excludes submission and credit/completion polling;
   it is not a 57% reduction in the full reader or full kernel.

[Instruction counts](benchmarks/llama3_round3_noc_codegen.json) and the CPU
code-generation test make the third change independently reviewable.
These improvements leave arithmetic and weight format unchanged.

The sequential context-64 ablations were:

| Cumulative change | Device decode, µs |
|---|---:|
| Starting round-two runtime | 6532.68 |
| Unpack invariants | 6529.87 |
| Scalar offset simplification | 6518.25 |
| NoC command construction | 6487.65 |

These are separate runs, not confidence intervals. The largest measurable
improvement came from NoC command construction; unpack hoisting alone barely
changed time.

## Where the projection pipelines spend time

A synthetic probe keeps the normal output shapes, core assignment, unpack,
math and output machinery, but substitutes zero weights already resident in L1
for the DRAM reader. It measures pure projections without fused norms or
residual/SwiGLU epilogues. These are diagnostic timings, not inference speed.

| Pure projection | Normal weights, µs | Resident zero weights, µs | Normal useful weight GB/s |
|---|---:|---:|---:|
| O | 27.20 | 16.41 | 308.4 |
| QKV | 39.08 | 20.07 | 321.9 |
| Gate/up | 143.49 | 60.05 | 467.7 |
| Down | 76.81 | 36.19 | 436.8 |
| LM head | 1049.08 | 395.97 | 500.8 |

Removing weight reads substantially reduces every projection's time. This
implicates the reader/DRAM path, but does not isolate physical DRAM service from
NoC issue overhead, contention, synchronization, or overlap with computation.
In particular, the resident timings must not be added to weight-transfer time:
the pipelines overlap. All projections already use 117 workers, including the
small matrices; increasing attention workers from 16 to 32 in round two did not
improve throughput.

The final reproducible probes are in
[all five projections](benchmarks/llama3_round3_final_pipelines.json).
The earlier probe data is in
[O](benchmarks/llama3_round3_pipeline_limits.json) and
[other projections](benchmarks/llama3_round3_pipeline_limits_remaining.json).
The O file also contains a one-off copy-math experiment. It did not speed up O,
but that synthetic variant timed out on QKV and was removed from the diagnostic
tool; it is not reliable evidence for other shapes.

## Fused kernel bandwidth and time headroom

At context 64, divide useful projection weight bytes by the entire fused
kernel time. These figures include norms/epilogues and launch work; they are
not measured DRAM bus utilization. The final column subtracts an ideal
512 GB/s weight transfer from the measured stage time across all layers.
It includes non-weight work and is not all recoverable bandwidth loss.

| Stage | µs/launch | Useful GB/s | Percent of 512 GB/s | Above weight-only floor, µs/token |
|---|---:|---:|---:|---:|
| O | 32.17 | 260.7 | 50.9% | 252.6 |
| QKV | 40.88 | 307.8 | 60.1% | 260.8 |
| Gate | 151.08 | 444.2 | 86.8% | 320.2 |
| Down | 81.67 | 410.9 | 80.2% | 258.1 |
| LM | 1055.36 | 497.8 | 97.2% | 29.3 |

**O has the lowest useful bandwidth; gate/up has the largest aggregate gap.**

## Experiments rejected

- Persisting fixed NIU command fields across weight reads, with explicit row
  transaction draining and only three variable command fields per packet,
  matched all 192 short-test tokens and sampled logits. It did **not** improve
  performance (6494 µs device decode versus 6488 µs before it), so it was reverted.
  Its result argues against repeated fixed-field stores being the main remaining
  limitation. See `llama3_round3_reader_{64,profile}.json` in `benchmarks/`.
- General assembler address-generation rewrites, including a GP-relative
  experiment, caused hardware timeouts. They were reverted; no causal hardware
  explanation was established. The generic assembler is unchanged by this round.
- The synthetic copy-math probe was removed after its QKV timeout. Only the
  normal and resident-weight modes are offered by the diagnostic tool.

## Can BF16 1B reach 200 tok/s?

Using the supplied theoretical **512 GB/s** peak and **2,471,493,632 useful
projection-weight bytes/token**, the optimistic weight-only time is
**4.827 ms**, or **207.16 tok/s**. Padding and activation/KV traffic make the
actual memory requirement higher.

At 200 tok/s, all other work has only **0.173 ms/token** beyond that weight-only
ideal. Context-64 attention alone currently takes about **0.471 ms/token**
across 16 layers, before embedding, argmax, fused epilogues, and host overhead.
Even idealizing every projection to its weight-transfer floor while retaining
current separately scheduled attention/embedding/argmax gives only roughly
**187 tok/s**. This is a conditional model, not a device-wide impossibility
proof: it assumes current scheduling and no overlap of that remaining work.

Thus 200 tok/s is not a credible expectation from easy RISC-V cleanup alone.
It requires near-peak weight delivery **and** substantial removal or overlap of
non-weight work. The smaller O/QKV kernels have the worst useful bandwidth,
while the gate/up and down kernels offer more aggregate time savings across
16 layers. LM already approaches peak useful bandwidth and offers little
weight-transfer headroom.

A next architecture experiment should target bank-aware multirow weight
streaming/packing and useful work per transfer, with measurements of outstanding
requests and bank balance. More projection cores alone will not fix a workload
already spread across all available workers. Reduced weight precision could
change the bandwidth budget substantially, but is outside this exact-BF16 round.

## Reproduce

```sh
PYTHONPATH=. python3 examples/benchmark_llama3.py --device 0 --steps 64 --output short.json
PYTHONPATH=. python3 examples/benchmark_llama3.py --device 0 --steps 512 --output long.json
PYTHONPATH=. python3 examples/profile_llama3.py --device 0 --contexts 32 64 128 512 --output profile.json
PYTHONPATH=. python3 examples/diagnose_llama3_projections.py --device 0 --output pipelines.json
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

[Source hashes](benchmarks/llama3_round3_sources.json) identify the changed
inference/unpack/NoC modules. The
[reverse patch](benchmarks/llama3_round3_to_round2.patch) restores those three
modules to their round-two snapshots; apply it only in a separate copy of the
repository. Shared compiler changes also affect an inference-only reference
loaded with `--reference`, which is why correctness comparisons here use saved
round-two token IDs and logit hashes.
