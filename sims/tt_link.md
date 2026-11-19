# TT-link between two p150a cards: measured 2026-11-19

Raw data: `sims/results/2026-11-19-tt-link.jsonl`. Probe: `sims/probes/tt_link.py` (ERISC1 runs `eth/e1_link.c`).
Setup: two p150a joined by QSFP-DD on Ethernet channels 11 and 13, straight across (card 0 ch n to card 1 ch n), both
links trained at 400G. The vendor base firmware runs on ERISC0. ERISC1 issues data transfers on TX queue 2, which the
base firmware leaves in TT-link mode and never uses. No queue, MAC or PCS register is written.

## Clock
- ERISC1's wall clock (0xFFB121F0) runs at the AI clock. Over a 23 ms run it counted 1344 MHz against the host
  clock; the 0.4% below 1350 MHz is host issue and polling. Cycle counts below are E1 cycles at 1.35 GHz.

## Bandwidth (ERISC1 L1 -> peer Ethernet L1, `START_DATA` transfers)
- **One link, one direction: 49.15 GB/s, 36.6 B/cycle**, for every transfer size from 4 KiB to 128 KiB. That is 98.3%
  of 400 Gb/s; TT-link's ~4 KiB frames (`ETH_TXQ_MAX_PKT_SIZE_BYTES` = 0x1012) carry little overhead.
- Below 4 KiB the issuing RISC limits: a 1 KiB transfer costs **62 cycles** per command (program four TXQ registers,
  poll `STATUS.cmd_ongoing` with the BH-55 dummy read), so 1 KiB transfers reach only 22 GB/s. A 4 KiB transfer takes
  112 cycles on the wire, longer than its issue cost.
- **Directions and links are independent.** Duplex on one link: 49.15 GB/s each way. One direction on both links:
  49.15 GB/s each. All four (both links, both ways): 196.6 GB/s total, 49.15 per stream.
- Every point checked the last transfer's bytes on the receiver.

| Case | Transfer | GB/s per stream | Total GB/s |
| --- | ---: | ---: | ---: |
| one way, ch 11 | 1 KiB | 22.0 | 22.0 |
| one way, ch 11 | 4 KiB .. 128 KiB | 49.1 .. 49.2 | 49.2 |
| duplex, ch 11 | 16 / 64 KiB | 49.1 | 98.3 |
| one way, ch 11 + ch 13 | 16 / 64 KiB | 49.1 | 98.3 |
| duplex, ch 11 + ch 13 | 16 / 64 KiB | 49.1 | 196.6 |

## Latency
- **Round trip: 856 cycles (0.64 µs)** for a 16-byte packet card 1 -> card 0 -> card 1. ERISC1 on each side polls its
  own L1 for the packet and answers at once. That includes two transfer issues, two wire crossings and both polls,
  so one way is about 430 cycles (0.32 µs).

## What this means for tensor-parallel all-reduce
- Decode (one token, 8 to 14 KiB per all-reduce) is latency-bound: about 0.2 to 0.3 µs on the wire against the
  measured 10 to 15 µs per all-reduce launch. The cost is the launch and the worker handshakes, not TT-link.
- Prefill moves rows x dim BF16 per all-reduce: 2.6 MB for a 320-row Llama 3 8B chunk. That is 53 µs per direction
  on one link, or 27 µs split over both. 64 all-reduces per chunk: 3.4 ms on one link against ~80 ms of matmuls per
  card, so one link is enough if staging keeps up.
- Payloads that large do not fit in the Ethernet tile (~448 KiB of L1 below the base firmware). A streaming all-reduce
  must reuse a ring of staging slots, and the sender may only refill a slot after the receiver acknowledges it:
  credits. With a 0.64 µs round trip and 49 GB/s, about 31 KB is in flight per round trip, so a ring of 4 to 8
  slots of 16 KiB keeps the link full.
- Not measured yet: how fast workers can fill the sender's Ethernet L1 and drain the receiver's over the NoC. The NIU
  injects ~61 B/cycle per NoC (`noc_findings.md`), above TT-link's 36.6 B/cycle, so the tile should keep up if
  writes use both NoCs or several workers.
