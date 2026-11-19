# Packer probes (pack.py)

**Status, 2026-11-18: run on hardware.** All 165 cases ran on card 1 (`results/2026-11-18-fw3-pack-card1.jsonl`).
147 pass `verify`; the 18 handoff cases have nothing to verify. The hypotheses further down are the pre-run
expectations. The measured values:

| quantity | measured (card 1) |
|---|---|
| tile, f32→bf16 or f32→f32, MOP, back to back | **34** per tile; 16 inline PACRs 67.6 |
| tile, f16→e4m3 | 18 per tile (MOP); inline 78 |
| per-tile L1 address by WRCFG (its STALLWAIT serialises tiles) | 96.6 per tile; by ADC 34.3 (f32) / 20.7 (e4m3) |
| llama per-tile sequence built up | +PRE 102.6, +POST (STALLWAIT + drain per tile) 160-162, +CB MMIO 176-178, full llama tile **179-181** (f32), 164 (e4m3); ttrv `move` 172, with post 198-200; re-writing the MOP template every tile 284-302 |
| last PACR → data visible to a RISC load or a NoC read | 104-121, about the packer-idle time |
| math SEMPOST → pack done | SEMWAIT (as llama) **82**, RISC poll of the semaphore 127 |
| pipeline, math delay d per tile then post, MATH_PACK max 1 | period = max(192, d + ~145): d 0 → 192, 200 → 344, 1600 → 1748. Max 2: 192 until d ≈ 100, then d + ~42 |
| contention | own-NIU NoC writes near the output +1.4 to +7 per tile; remote writes +1.3; unpacker reading L1 +0; unpacker + NoC writes +6.7; llama tile with NoC writes 184 (+3) |

```
python3 sims/probes/pack.py                       # self-test, no hardware
python3 sims/probes/run.py --device 1 --output sims/results/<date>-pack-card1.jsonl pack --list
python3 sims/probes/run.py --device 1 --output sims/results/<date>-pack-card1.jsonl pack -k fmt-     # start here
python3 sims/probes/run.py --device 1 --output sims/results/<date>-pack-card1.jsonl pack             # everything
```
Run order: `fmt-` first. If any `fmt-` case has `verify` FAIL, stop and fix the configuration before running the rest.
Then `shape- tiny- l1acc- overhead- vis-`, then `handoff-`, then `contend-`. Cases are listed in that order, with the
unpack-contention cases last.

## Files

| file | role | what it does |
|---|---|---|
| `pack.h` | all | Tensix encodings (`TT_*`), packer cfg word numbers, the llama MOP template, `pack_wait`, `sem_value`, the L1 layout |
| `k_pack.c` | TRISC2 | packer config (as the exported llama kernels write it), timed pack loops, visibility, handoff |
| `k_pack_math.c` | TRISC1 | fills Dst from the SFPU with a known pattern; the math side of the handoff (SEMPOST) |
| `k_pack_noc.c` | BRISC | NoC traffic stream (local or remote tile), or the visibility reader (NoC reads of the output) |
| `k_pack_unp.c` | TRISC0 | unpacker 0 stream reading L1 (contention) |
| `pack.py` | host | cases, launch, numpy reference, analysis |

Tiles: pack tile (1,2); the remote traffic source is (2,2).

## What the llama kernels do (the scope)

From `kernels/llama3-*/*/trisc2.S` (exported) and `docs/examples/llama3_*.ttrv`:

- (in, out) pairs: fp32 Dst, `in=fp32` to bf16 (most packs) and to fp32 (argmax, attention state).
  `in=fp16` to e4m3 from a 32-bit Dst (Round_10b_mant, Pac_LF8_4b_exp) in every fp8-model pack (qkv/gate/o/down
  outputs). 16-bit Dst `in=bf16` to bf16 (1b/8b-bf16 down, o). bfp8 and bfp4 output were added to the scope by the
  user. No other formats are covered.
- Pack shape: whole 32x32 tiles, `ReadIntfSel=0` (4 rows per PACR). Exported kernels use a MOP of 4 faces x 4 PACRs
  (face end AddrMode 2: Z+=1; tile end AddrMode 1 + Last). The ttrv ports use 16 inline PACRs (AddrMode 0, the last
  AddrMode 1 + Last). argmax packs 64 datums (`n=64`, one PACR).
- Per tile: `SEMWAIT(TDMA, MATH_PACK, ON_ZERO)`, CB space poll (stream reg), `SETADC W=dst tile`, `SETDMAREG` x2 +
  `STALLWAIT(CFG, THCON|PACK0)` + `WRCFG 69` + `SETDMAREG` + `DMANOP` (L1 address), `SETADCXX`, `SETADCZW`, the
  cfg[180] write, `STALLWAIT(CFG, PACK0)`, MOP, `STALLWAIT(SYNC, PACK0)`, PC_BUF drain, CB push, `ZEROACC`, `SEMGET`.
- Not used by any llama kernel: L1 accumulation (`Pack_L1_Acc` is never set), untilize / strided Dst reads
  (`DstAccessMode`), single-datum gather (`ReadIntfSel=1`), compression, contexts 1-3. Only `l1acc-` is probed among
  these, because the task asked for it.
- Edge masks: qkv/gate/lm/o have a second pack config with `PCK_EDGE` select 2, SEC1 mask 1, row-set map 1. It is timed
  (`overhead-*-edge-llama`) but not checked.

## Dst pattern and verification

TRISC1 writes each 4-row x 8-column SFPSTORE block as `base(tile, row group, parity) + lane term` (`k_pack_math.c`).
Every value is exact in its output format, so the reference needs no rounding model:
- pattern 1 (fp32, bf16, bfp8): exponent 64 + (16t + g) % 128, sign = column parity, mantissa = lane << 17.
  bf16 keeps it exactly. bfp8: every value in a row has the same exponent and 5 mantissa bits.
- pattern 2 (bfp4): same exponent, mantissa = (lane & 3) << 21 (2 bits). The nibble order is not documented, so both
  orders are accepted and `verify_notes.variant` records which one matched.
- pattern 3 (e4m3): unbiased exponent -6..7, 3 mantissa bits. No saturation.
- l1acc: L1 starts at zero and every pack adds into it. fp32 is exact; bf16 is simulated step by step with RNE, as in
  `Accumulation.md`.
- The sentinel 0xFFFFFFFF used for visibility cannot occur in any of these outputs (checked by the self-test).

Fill instructions that have not been tested on hardware: `SFPSHFT` mod1 5 (shift `LReg[15]`, lane x 2), and
`SFPIADD` mod1 4. If they are wrong, every case fails verify. Nothing hangs.

## Record fields

- mode 0 (fmt, shape, tiny, l1acc, overhead, contend): `samples[count] = [(issue, total), ...]` (8 samples, the first
  is a warmup). `issue` = RISC cycles to push the units, `total` = until `STALLWAIT(packer)` + drain return.
  `per_unit` (= `median`) = slope of median totals between the smallest and largest count. `fixed` is the intercept
  (drain + timer cost). `steps` = slopes between consecutive counts. A drop in the steps means the first unit overlaps
  the start-up.
- vis: per sample `(t0 before issue, t1 issued, t2 packer idle + drained, t3 RISC sees the last 16 B)`.
  `seen = t3 - t0`, `idle = t2 - t0`. `noc[i].first_new_fire` = fire time (relative to t0) of the first BRISC NoC read
  that returned packed data. `last_old_fire` = the read before it, which saw the old value.
- handoff: `latency[i] = done_i - post_i` (TRISC1's now() just before SEMPOST, TRISC2's now() after the pack drained).
  `period` = differences between consecutive dones (pipeline).
- contention: `brisc_covers` / `trisc0_covers` = the companion stream ran for the whole timed window (same tile clock).
  Remote traffic runs for 2M cycles, which is far longer than the window, but it is not checked.

## Case groups

| group | n | what | hw.py entry it fills |
|---|---|---|---|
| `fmt-<fmt>-{mop,inline,mop-adv}` | 18 | tile throughput per (in, out) pair, back to back, no per-tile config. `adv`: each tile to its own L1 address through the ch1 W ADC | `PACK.tile_cycles[fmt]` |
| `shape-<fmt>-r{4,16,64}-k{1,2,4}` | 48 | rows per unit x rows per PACR (`ReadIntfSel` 1/3/15) | `PACK.tile_cycles` as a function of PACRs and rows; per-PACR cost vs rows |
| `tiny-<fmt>-x{1,16}-{lasteach,lastonce}` | 12 | one-row PACRs of 1 or 16 datums: the admission / issue rate and the cost of `Last` (tile end, output flush) | `PACK.admission` (DOC 1/cycle), new `pacr_issue`, `tile_end` |
| `l1acc-<fmt>-{mop,inline,mop-selfwr-near}` | 6 | `Pack_L1_Acc` + `Disable_pack_zero_flags`; compare with `fmt-` | new `PACK.l1acc` |
| `overhead-<fmt>-<step>` | 36 | the llama per-tile sequence built up one piece at a time: bare MOP, +SETADC W, +L1 address (WRCFG with its STALLWAIT, or ADC), +PRE (ADC resets, cfg180, STALLWAIT CFG), +POST (STALLWAIT + drain per tile), +CB MMIO, full llama tile (+ZEROACC, +self-posted sem), ttrv `pack.move`, full reconfigure per tile | `SCALAR.WRCFG` / `STALLWAIT` effective costs in context, new `PACK.per_tile_overhead` |
| `vis-<fmt>-r{64,4}-{poll,drainfirst,noc}` | 12 | last-PACR issue to data readable in L1 by the RISC, and by an outgoing NoC read. Compares with the packer-idle drain | new `PACK.visibility_risc`, `visibility_noc` |
| `handoff-lat-{semwait,sempoll,selfsem}` | 3 | math SEMPOST to pack done (Tensix SEMWAIT, as llama, vs RISC poll of the semaphore). selfsem = the same tile with no wait (baseline) | `SCALAR.sem_op`, new `PACK.handoff` |
| `handoff-pipe-max{1,2}-d{0..1600}[-poll]` | 14 | steady rate of math (delay d, then post) feeding the llama per-tile pack. MATH_PACK max 1 (as llama) or 2 (double-buffered) | pipeline model: period = max(math, pack + handoff) or their sum |
| `contend-<fmt>-<companion>` | 16 | tile throughput while the L1 is busy: own-NIU NoC writes/reads (4 KiB) to the same 96 KiB range as the output (`near`) or far away, incoming writes from (2,2), the unpacker reading L1, both | `UNPACK`/`PACK`/`NOC_COST` contention, `RISCV` TODO "L1 bank contention" |

## Hypotheses and expected values

| quantity | expected | source |
|---|---|---|
| tile, f32->bf16, MOP or 16 inline PACRs | ~18 cyc | `docs/ttrv_pack_unpack.md` §12 cycles ("pack 1024: bf16 18, fp32 35"; mop = replay = inline) |
| tile, f32->f32 | ~35 cyc (4 KiB in 35 cyc = ~117 B/cyc, about 7 x 16 B L1 writes per cycle) | same |
| tile with per-tile re-arm | +14 (hand MOP) to +41 (ttk) | same |
| tile incl. setup + STALLWAIT + drain | 116 (bf16) / 180 (fp32); 4 passes 428 / 684 => ~104 / ~168 per drained tile | `boop-docs/measurements/sfpu-argmax-l1acc-loadmacro.md` |
| l1acc vs overwrite | equal (measured equal at 16, 256, 1024 datums), although `L1.md` says a non-atomic accumulate is 2 cycles per 16 B (an f32 tile would take >= 512 cyc). The repeated-tile slope settles it | same, and `WormholeB0/TensixTile/L1.md` |
| PACR admission | <= 1 per cycle; the issuing thread blocks until the packer accepts | `Packers/README.md` (WH, BH defers) |
| per-PACR cost | grows with rows (16 datums per enabled read interface); one row per PACR should be ~4x slower per datum than four if the cost is per PACR | `PACR.md` (BH) |
| e4m3 | conversion in 128-byte input groups (fp16 -> fp8); expect ~ the bf16 rate or slower | `PACR.md` late-conversion note |
| bfp8/bfp4 | exponent section + shared-exponent pass; slower than bf16? unknown | none |
| 16-bit Dst bf16 | half the Dst read bytes of f32->bf16; expect <= f32->bf16 | none |
| WRCFG L1 address per tile | its `STALLWAIT(CFG, THCON|PACK0)` waits for the previous tile, so the tiles serialize: `addr-wrcfg` per tile ~ the drained latency rather than the throughput | `kernels/*/trisc2.S`, `Packers/README.md` |
| visibility | RISC read sees the data at about the packer-idle time (STALLWAIT C3); a NoC read a little later. Unknown | none; this is the open question |
| contention | NoC writes into the same L1 range slow the pack if banks are 96 KiB ranges (`near` slower than `far`); with fine interleaving, near and far are equal | `L1.md` (WH: 16 banks of 91.5 KiB, bank conflicts stall all but one port) |
| handoff | SEMPOST -> SEMWAIT release a few cycles, plus pack latency; RISC poll adds an MMIO round trip (~10-20) | `SCALAR.sem_op` DOC 1 |

## Risky cases (could wedge the Tensix or the NoC and need `smi.py -r`)

- `handoff-*` with `semwait` (and the `pipe` cases): TRISC2 pushes a Tensix `SEMWAIT` and then blocks in an unbounded
  PC_BUF drain. TRISC1 always posts (its waits are bounded and a timeout still posts), so the wait always ends unless
  TRISC1 dies. If it does, you get a HostTimeout with a stuck Tensix. Medium risk.
- `contend-*-unpack-*`: the unpacker config is a copy of the deleted, hardware-tested `configure_unpacker`
  (BF16 -> SrcA), without its UNPACK_SYNC commit. Per `ttrv_pack_unpack.md` §8, a wrong unpack config can hang the
  card. Highest risk; these cases run last.
- `l1acc-*`: uses the bits from the tested `test_l1_accumulation.py` (70.2, 71.19). Low risk.
- Every PACR sequence ends with `Last`. `PACR.md` says a STALLWAIT on the packer never finishes after a 3-4 interface
  fp32 PACR without Last, and that `Flush` wedges the packer. Neither is used.
- `vis-*-noc` and self traffic: NoC reads and writes to the tile's own coordinate. Low risk. Remote traffic is
  time-bounded (2M cycles).
- `overhead-*-recfg-tile` rewrites the MOP template every tile (after `mop_drain`). Low risk.

## Not covered

untilize / `DstAccessMode`, scatter / row gather / `pack.gather` single datums (no llama kernel emits a ReadIntfSel != 0
PACR), contexts 1-3, ReLU, stochastic rounding, compression, edge-mask values (only timed), `PACR_SETREG`.
Multiple packers: Blackhole has one packer with four Dst read interfaces (`PACR.md`), so "x4 / concurrent packers"
means the `ReadIntfSel` sweep in `shape-`. The RISC is out of the way in the bare cases (`fast_units`: ~6 RISC
instructions per tile), but for one-row PACRs `tiny-` can be limited by the RISC store rate (~1 per cycle). Compare
`per_unit_issue` with `per_unit`.
