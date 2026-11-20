# Offline simulation elapsed time on card 0 captures

One CPython process simulates one image and its entire grid. This run used CPython 3.14, one phase trial per image and up to nine concurrent replay processes on a 12-CPU host. Other validation processes also used the host. Elapsed times include interpreter startup, loading and scoring the capture. They are reconstructed from job dispatch order and the completion timestamps. Fast jobs are sensitive to host load. Capture and checkpoint loading time are excluded. Record numbers index the corresponding compressed capture from zero.

## Llama 1B decode

| Record | Kernel | Elapsed wall time |
|---:|---|---:|
| 0 | embedding | 0.11 s |
| 1 | qkv | 31.0 s |
| 2 | attention | 1.05 s |
| 3 | o | 19.7 s |
| 4 | gate | 2 min 19 s |
| 5 | down | 1 min 20 s |
| 6 | lm | over 15 min 42 s, running |
| 7 | argmax | 1.52 s |

## Llama 8B BF16 decode

| Record | Kernel | Elapsed wall time |
|---:|---|---:|
| 0 | embedding | 0.11 s |
| 1 | qkv | 2 min 09 s |
| 2 | attention | 1.68 s |
| 3 | o | 1 min 17 s |
| 4 | gate | 6 min 50 s |
| 5 | down | 3 min 53 s |
| 6 | lm | over 15 min 42 s, running |
| 7 | argmax | 1.51 s |

## Llama 8B BFP8 decode

| Record | Kernel | Elapsed wall time |
|---:|---|---:|
| 0 | embedding | 0.10 s |
| 1 | vector | 0.29 s |
| 2 | projection | 34.9 s |
| 3 | attention | 1.77 s |
| 4 | projection | 25.9 s |
| 5 | vector | 0.24 s |
| 6 | projection | 2 min 51 s |
| 7 | vector | 0.71 s |
| 8 | projection | 1 min 27 s |
| 9 | projection | 12 min 45 s |
| 10 | argmax | 1.50 s |

## Nanbeige decode

| Record | Kernel | Elapsed wall time |
|---:|---|---:|
| 0 | embedding | 0.10 s |
| 1 | vector | 0.51 s |
| 2 | projection | 1 min 31 s |
| 3 | attention | 1.93 s |
| 4 | projection | 1 min 26 s |
| 5 | vector | 0.17 s |
| 6 | projection | 4 min 39 s |
| 7 | vector | 1.09 s |
| 8 | projection | 2 min 36 s |
| 9 | projection | over 15 min 42 s, running |
| 10 | argmax | 1.57 s |

## Qwen decode

| Record | Kernel | Elapsed wall time |
|---:|---|---:|
| 0 | embedding | 0.10 s |
| 1 | vector | 0.39 s |
| 2 | projection | 2 min 03 s |
| 3 | projection | 0.57 s |
| 4 | gdn_conv | 1.13 s |
| 5 | gdn_state | 13.5 s |
| 6 | gdn_out | 0.34 s |
| 7 | projection | 48.2 s |
| 8 | vector | 0.14 s |
| 9 | projection | 2 min 52 s |
| 10 | vector | 0.89 s |
| 11 | projection | 2 min 12 s |
| 12 | projection | 1 min 49 s |
| 13 | attention | 3.48 s |
| 14 | projection | over 15 min 42 s, running |
| 15 | argmax | 2.08 s |

## Llama 1B four-row prefill

| Record | Kernel | Elapsed wall time |
|---:|---|---:|
| 0 | embedding | 0.10 s |
| 1 | vector | 0.22 s |
| 2 | pack | 0.19 s |
| 3 | projection | 13.0 s |
| 4 | attention | 2.40 s |
| 5 | projection | 6.55 s |
| 6 | vector | 0.16 s |
| 7 | projection | 1 min 07 s |
| 8 | vector | 0.65 s |
| 9 | pack | 0.51 s |
| 10 | projection | 26.6 s |
