# Llama 3 8B speculative decoding on Blackhole card 0

The implementation uses the existing full-BF16 target weights, a two-token
weight-sharing verifier, and a CPU prompt/history lookup proposer. It requires
no additional checkpoint. Ordinary greedy decoding remains available.

## Card 0 measurements — September 7, 2026

Full BF16 Llama 3 8B Instruct, 88 projection workers, 32 attention workers.
Each row generates 128 tokens with EOS ignored, using the same loaded target
for the baseline and speculative run. All 640 generated token IDs match.

| Workload | Baseline tok/s | Speculative tok/s | Decode speedup | Accepted/proposed | Prefill speedup |
|---|---:|---:|---:|---:|---:|
| Sky explanation | 29.26 | 29.20 | 0.998x | 0/1 | 1.63x |
| Python Fibonacci | 29.23 | 30.07 | 1.028x | 5/7 | 1.65x |
| Robot story | 29.24 | 29.19 | 0.998x | 0/1 | 1.64x |
| Repeated phrase | 29.20 | 46.59 | 1.596x | 60/61 | 1.70x |
| Counting | 29.13 | 29.12 | 0.999x | 0/0 | 1.69x |

These are single paired measurements per workload; small differences around
1.00x are not evidence of a meaningful throughput change. Repeated text gains
about 60%, while ordinary prose stays close to baseline. Prompt prefill gains
about 63–70% on these prompts. No generalized generation speedup is claimed.

The initial more aggressive `--min-ngram 1` experiment reached **47.49 tok/s
(1.63x)** on the repeated phrase and **36.87 tok/s (1.27x)** on counting. It
slowed the sky explanation and robot story by about 3.6% and 2.6%, respectively.
That experiment used ordinary one-token prefill; its generation timings include
all draft/rejection costs but exclude prefill, just like the final comparison.

Raw results: [final default and correctness checks](validation/card0-speculative.json),
[initial aggressive lookup](validation/card0-speculative-ngram1.json).
The final verifier matched all 514 teacher-forced tokens, all 22 sampled full
BF16 logit buffers, and all 14 forced-rejection recovery checks. Twelve CPU tests
pass. Source hashes for the measured runtime files are included in the JSON.

## Operation

For committed history ending at position `p`, lookup proposes one token `d`.
The verifier consumes `[history[p], d]` at positions `p` and `p+1`. Each
projection weight row is read from DRAM once and reused for both dot products.
The arithmetic and BF16 rounding follow the ordinary decoder. Attention runs
in position order within each layer, using each position's own causal mask.

If the first target prediction equals `d`, commit `d` and the second target
prediction (the bonus token). Otherwise commit only the first target prediction.
The speculative KV entry is then logically invalid: the next decode/verifier
writes the corrected token at that position before using it. The verifier does
not append its predictions into the device token history. EOS and the requested
generation limit are enforced on committed tokens, including the bonus.

The default proposer requires a matching suffix of three or four tokens and
uses the most recent matching continuation. `--min-ngram 1` also tries shorter
matches. The initial single-token-match experiment helped repetition and
counting, but wasted verification on general prose; the more conservative
minimum is therefore the default. This is greedy decoding only, not stochastic
speculative sampling.

Prompt ingestion uses the same two-token path with known prompt tokens. It
leaves the final prompt token for the first generation call. This reduces prompt
processing time independently of draft acceptance during generation.

[Prompt lookup decoding](https://github.com/apoorvumang/prompt-lookup-decoding)
describes the proposer technique. The target verifier here is implemented in
this repository's Python-generated Blackhole kernels.

## Implementation

- `examples/llama3_speculative.py`: shared-weight projection, causal verifier,
  prompt prefill, lookup, greedy acceptance, CLI and comparison mode.
- `ttk/unpack.py`: optional retained-CB tile access so both tokens consume a
  weight row before it is released. Retained rows divide the ring depth and
  never wrap inside the group.
- `examples/llama3.py`: separates program creation from trace capture so the
  ordinary decoder and verifier can share one resident kernel installation.
- `fw/consts.py`: expands the resident kernel/template arena to `0xC2000`;
  scratch allocation and kernel relocation are checked by CPU lowering tests.

Ordinary decode uses 163 launches per token. The two-token verifier currently
uses 679 launches per pair, with separate normalization and epilogue launches.
The additional launches are a remaining optimization opportunity. This is still
a GEMV-derived kernel: the verifier saves DRAM reads while retaining the
original per-token dot-product arithmetic, rather than using a new GEMM path.

## Reproduce

Run commands from this directory, using card 0 exclusively:

```sh
PYTHONPATH=. .venv/bin/python examples/llama3_speculative.py \
  --device 0 --steps 128 --prompt 'Explain why the sky is blue.'

PYTHONPATH=. .venv/bin/python examples/llama3_speculative.py \
  --device 0 --steps 128 --benchmark --min-ngram 1 \
  --prompt 'Continue this sequence to 100, preserving the format: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,' \
  --output validation/counting-comparison.json

PYTHONPATH=. .venv/bin/python scripts/validate_speculative.py --device 0
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests
```

`--benchmark` runs fixed-length ordinary and speculative generation on the same
loaded target and raises on token differences. Without this flag the CLI stops
at EOS. Timed generation includes drafting, verifier calls, history uploads,
token readback, and rejection handling. Weight loading, prompt ingestion, and
diagnostic logit reads are excluded. Prefill time is reported separately.

## Validation scope

Hardware checks compare 514 teacher-forced predictions against the ordinary
Blackhole decoder and full BF16 logit bytes at 22 positions through 513.
Fourteen forced rejections test cache overwrite around the 32-, 64-, 128-, 256-,
and 512-token boundaries. Five prompts compare 128 generated tokens each.
CPU tests cover acceptance, rejection, bonus tokens, EOS, generation limits,
prefill boundaries, retained-kernel residency, and the inherited decoder checks.

This establishes equivalence to the existing Blackhole target in the tested
cases. It does not claim bit-exact Transformers equivalence; the inherited
runtime's CPU numerical comparison limits are described in `PERFORMANCE.md`.
The full 8192-token cache is allocated; maximum-context hardware validation has
not been performed. Speedups depend on draft acceptance, so these results should
not be treated as a general 8B throughput multiplier.
