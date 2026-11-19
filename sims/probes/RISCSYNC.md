# RISC <-> RISC handshakes and RISC L1 access under traffic (riscsync.py)

Run on card 1, tile (1,2), 2026-11-18. Data: `sims/results/2026-11-18-riscsync-card1.jsonl` (39 cases, no failures).

```
python3 sims/probes/run.py --device 1 --output sims/results/<date>-riscsync-card1.jsonl riscsync
```

## Handshakes (`hs-<mode>-<initiator>-<responder>`, k_handshake.c)

Ping-pong between two RISCs of one tile. The initiator bumps word A, the responder waits for it and bumps word B, and
the initiator waits for B. After 16 warm-up round trips there are 7 samples of 64 round trips each. `median` is half
a round trip: from a store on one RISC until the other RISC has seen it and is past its poll loop. That is what a
kernel pays to hand work from one RISC to another.

| mechanism | how | one way (cycles) |
|---|---|---|
| L1 word | `sw` + `fence`; the other side polls with a fence per retry (the L0 data cache is not coherent) | **29.2-29.6** |
| overlay stream register (ttrv's CB pushed/popped counters, stream 38/39 reg 8) | MMIO store; poll an MMIO load | **27.5-27.6** |
| Tensix semaphore through PC_BUF (TRISCs only) | store 0 = post; poll value != 0, then store 1 = get and wait for 0 | **23.6-24.6** |

- **The roles don't matter:** BRISC, NCRISC and each TRISC pair give the same number (within 0.5 cycle).
- These are poll-to-poll times. Each side's own costs (fence 4+, MMIO load 7, ~9 per L1 load) are inside them.

## L1 access under L1 traffic (`l1lat-<kind>-<role>-<companions>`, k_l1chase.c)

The measured role is NCRISC or TRISC1. It runs either a dependent load chase over 16 lines 4 KiB apart (every load
misses the L0 data cache) or a 1024-instruction straight-line loop (past the I-cache knee). It does this while
companions keep the L1 busy:
- `noc`: BRISC NoC0 posted writes of 8 KiB from this L1 to itself, ~63 B/c (so ~126 B/c of L1 reads + writes).
- `noc2`: the same plus NCRISC on NoC1.
- `unpack`: the TRISC0 unpacker streaming a bf16 face, ~4.1 cycles per 512 B UNPACR, ~125 B/c.

Both companion logs show they ran for the whole measurement window.

| measured | none | noc | noc2 | unpack | noc + unpack |
|---|---|---|---|---|---|
| load chase, NCRISC (cycles/load) | 8.02 | 8.06 | – | 8.17 | 8.18 |
| load chase, TRISC1 | 8.00 | 8.05 | 8.12 | 8.00 | 8.09 |
| fetch, NCRISC (cycles/instruction) | 1.007 | 1.008 | – | 1.007 | 1.006 |
| fetch, TRISC1 | 1.008 | 1.007 | 1.008 | 1.007 | 1.008 |

**Result:** NoC and unpacker traffic slow a RISC's L1 loads by at most 2% (+0.18 cycles per load) and do not slow
its instruction fetch at all. A simulator can treat RISC L1 access as uncontended. The opposite direction does matter:
NoC traffic into the same L1 slows the unpacker by up to 2x (`UNPACK.md` contention group) and the packer by up to
~20% (`PACK.md` contend group).
