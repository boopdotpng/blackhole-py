# Blackhole Tensix measured timing

Card 0, physical core index 0, T0/T1/T2; 2026-09-17. See [method and limitations](README.md).
These are completed-loop median slopes, not isolated result latencies.
Two slopes use successive 1,024 / 2,048 / 4,096-operation points.
`empty` counts empty body slots; `swap_nop`/`shuffle_nop` include a padding SFPNOP in each body operation.

Each cell gives the range of the two slopes, in cycles per body operation.

| Probe | T0 | T1 | T2 |
|---|---:|---:|---:|
| empty | 0.125–0.125 | 0.125–0.125 | 0.125–0.125 |
| nop | 1.000–1.000 | 1.000–1.000 | 0.999–1.000 |
| loadi | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| mov_dep | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| iadd_dep | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| add_dep | 2.000–2.000 | 2.000–2.000 | 2.000–2.000 |
| add_ind4 | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| mul_dep | 2.000–2.001 | 1.999–2.000 | 2.000–2.000 |
| mul_ind4 | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| mad_dep | 1.999–2.000 | 2.000–2.000 | 2.000–2.000 |
| mad_ind4 | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| arecip_dep | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| mul24_dep | 2.000–2.000 | 2.000–2.000 | 1.999–2.000 |
| cast_dep | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| transp | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| swap | 2.000–2.000 | 1.999–2.000 | 2.000–2.000 |
| swap_nop | 2.000–2.000 | 1.998–2.000 | 2.000–2.000 |
| shuffle | 2.000–2.000 | 1.999–2.000 | 2.000–2.000 |
| shuffle_nop | 2.000–2.000 | 2.000–2.000 | 2.000–2.000 |
| shft2_bit | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| setcc | 1.000–1.000 | 1.000–1.000 | 1.000–1.000 |
| encc | 1.000–1.000 | 1.000–1.000 | 1.000–1.001 |
| dma_nop | 1.000–1.000 | 1.000–1.000 | 0.999–1.000 |
| ADDDMAREG_immediate | 3.000–3.000 | 3.000–3.000 | 2.999–3.000 |
| ADDDMAREG_same_bank | 3.000–3.000 | 3.000–3.001 | 3.000–3.000 |
| ADDDMAREG_cross_bank | 4.000–4.000 | 4.000–4.000 | 4.000–4.000 |
| SUBDMAREG_immediate | 3.000–3.000 | 3.000–3.000 | 3.000–3.000 |
| SUBDMAREG_same_bank | 3.000–3.000 | 3.000–3.001 | 3.000–3.000 |
| SUBDMAREG_cross_bank | 4.000–4.000 | 4.000–4.000 | 4.000–4.000 |
| MULDMAREG_immediate | 3.000–3.000 | 3.000–3.000 | 3.000–3.000 |
| MULDMAREG_same_bank | 3.000–3.000 | 3.000–3.000 | 3.000–3.000 |
| MULDMAREG_cross_bank | 4.000–4.000 | 4.000–4.000 | 4.000–4.000 |
| BITWOPDMAREG_immediate | 3.000–3.000 | 3.000–3.000 | 3.000–3.000 |
| BITWOPDMAREG_same_bank | 2.999–3.000 | 3.000–3.001 | 3.000–3.000 |
| BITWOPDMAREG_cross_bank | 4.000–4.000 | 3.999–4.000 | 4.000–4.000 |
| SHIFTDMAREG_immediate | 3.000–3.000 | 3.000–3.000 | 3.000–3.000 |
| SHIFTDMAREG_same_bank | 3.000–3.000 | 2.999–3.000 | 3.000–3.001 |
| SHIFTDMAREG_cross_bank | 4.000–4.001 | 4.000–4.000 | 4.000–4.000 |
| CMPDMAREG_immediate | 3.000–3.000 | 3.000–3.000 | 2.999–3.000 |
| CMPDMAREG_same_bank | 3.000–3.000 | 3.000–3.000 | 3.000–3.000 |
| CMPDMAREG_cross_bank | 4.000–4.000 | 4.000–4.001 | 4.000–4.000 |
| NOP_default | 0.996–1.000 | 1.000–1.000 | 0.998–1.000 |
| DMANOP_default | 0.999–1.000 | 0.999–1.000 | 1.000–1.000 |
| SETDMAREG_default | 0.999–1.000 | 1.000–1.000 | 1.000–1.001 |

Raw samples and image/source SHA-256 hashes are in [tensix_measured.jsonl](tensix_measured.jsonl).
Only `swap_nop`/`shuffle_nop` contain padding instructions; `dma_nop` is one DMANOP per body operation.
