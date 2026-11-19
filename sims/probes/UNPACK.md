# Unpacker probes (`unpack.py`)

Timing and correctness probes for the Tensix unpackers: `UNPACR` on unpacker A (SrcA) and B (SrcB), the address
counters, the config writes and `UNPACK_SYNC` credit that the llama kernels emit per block, and the dvalid hand-off
to the math thread. **None of this has run on hardware yet**: every number below is a hypothesis with its source.

Files: `unpack.py` (cases, data/reference models, `run`), `unpack.h` (encodings, config helpers, ttrv lowering),
`k_unpack.c` (TRISC0), `k_unpack_math.c` (TRISC1), `k_unpack_pack.c` (TRISC2), `k_unpack_noc.c` (BRISC/NCRISC or a
second tile).

```
python3 sims/probes/unpack.py --check     # host only: encodings vs ttrv.isa, all 12 images compile, data models
python3 sims/probes/run.py --device 1 --output /dev/null unpack --list
# suggested order: correctness first, risky groups last
python3 sims/probes/run.py --device 1 --output sims/results/<date>-unpack-card1.jsonl unpack -k verify-
python3 sims/probes/run.py --device 1 --output sims/results/<date>-unpack-card1.jsonl unpack -k issue-
python3 sims/probes/run.py --device 1 --output sims/results/<date>-unpack-card1.jsonl unpack -k size-
python3 sims/probes/run.py --device 1 --output sims/results/<date>-unpack-card1.jsonl unpack   # the rest (resumes)
```
A `verify-` failure is raised as a hard failure on purpose (RuntimeError): fix the configuration before trusting
any timing for that format.

## Scope (what llama uses)

From `docs/examples/llama3_*.ttrv` (the ttrv ports) and the exported `kernels/llama3-*/*/trisc0.S`; formats cut to
the user's list (2026-11-18): **bf16, fp8 e4m3, bfp8, bfp4** in L1, plus **fp32 -> SrcA** (`fmt=fp32-srca`,
attention state merge, `llama3_attention.ttrv:472`) and **bf16 with transpose** (`attention.ttrv:449`).

| pattern (`pat`) | llama use | per block |
|---|---|---|
| `pair_face` | qkv / o / gate / lm dot products: `unpack.move a, n=256, dvalid` + `unpack.move b, n=256, dvalid`, 4 faces per tile | 1 face A + 1 face B, one dvalid each |
| `a_face` | lm / qkv residual: 4 x `unpack.move a, n=256, dvalid` | 1 face A |
| `a_tile` | argmax / gate / o / attention merge: `unpack.move a, n=1024, dvalid` (BFP: 4 UNPACR, AddrMode 0x11) | whole tile into one A bank |
| `ba_tile` | attention QK^T (A transposed) and PV: `move b` then `move a`, n=1024 | one B + one A bank |
| `b_tile` | bfp / bf16 into B (bfp per user scope; no current llama kernel) | whole tile into one B bank |

Every move is the ttrv lowering of `ttrv/movement.py` (credit poll on semaphore 5, RMWCIB writes of ZDim/XDim (+ A's
Dest_cntx/Tile_x_dim), base `sw` + `lw` readback, credit post, `SETADCXX`, `SETADCZW`,
`STALLWAIT(UNPACK, TRISC_CFG|SRC*_CLR)`, the UNPACR(s), `STALLWAIT(SYNC, UNPACK*)`, `SEMGET(5)`). The RMWCIB
words are precomputed (ttrv emits them as immediates); the RISC-side difference is a few extra loads per move.

Not covered (out of the format scope or unused by llama): fp16, int8, e5m2, bfp2, fp32/int32 to Dst (unpack to Dst:
no ttrv kernel uses `to_dst`), tilize (`Tileize_mode`), upsampling, compressed input, context counters / per-context
formats (llama uses ctx 0 only; the context-reset hazard of `boop-docs/kernel-dev/unpack-context-reset-repro.md` is
not exercised beyond timing one `UNPACR_NOP` mode-2 wake-up), the second config state.

## Method

- Every launch starts from the firmware's reset Tensix state (`reset_tensix`, `reset_thread`) and does all its own
  configuration; setup ends with a drain so no config write is in flight when timing starts.
- TRISC0 sample = `t0 = now()`, issue `c` ops, `tensix_drain()`, `t1 = now()`. Counts `COUNTS = (8, 24, 56)` ops
  (`TILE_COUNTS = (2, 6, 14)` tiles for `move`), 8 samples each (first = warmup). Raw samples are recorded;
  `slope = (median(c=56) - median(c=8)) / 48` cycles per op, plus pairwise slopes and the intercept.
- Raw-mode L1 walks forward (UNPACR AddrMode = ch0 Z += 1, descriptor XDim = n) so every op reads new L1; BFP raw
  streams are one block of `ops` faces (ZDim = ops) so the exponent section is where the unpacker looks.
- Without SetDatValid the same Src bank is overwritten (no math needed). With it, T1 consumes exactly the number of
  banks T0 fills.
- Verification (`verify-*`): the move lowering, then T1 copies Src -> Dst (MOVA2D 8 rows / MOVB2D 4 rows,
  blackhole-py-old's proven `emit_copy_src_to_dst`), T2 packs Dst tile 0 (proven `configure_packer` +
  `emit_pack_dst`), the host compares every datum with the ISA conversion model (`make_data`: bf16 identity, fp32
  truncation to bf16, e4m3 -> fp16 -> fp32 via a 16-bit Dst, BFP8ToBF16 for bfp8/bfp4, per-face transpose).
- Encodings: `unpack.py --check` compiles `unpack.h` for the host and compares each macro with `ttrv.isa`; the
  llama words `0x420080c1` (UNPACR A, AddrMode 1, dvalid) and `0x43800101` (UNPACR_NOP B dvalid) are asserted.

## Case groups (239 cases)

| group | n | what | fills (`sims/hw.py`) |
|---|---:|---|---|
| `issue` | 10 | 16-datum UNPACR / UNPACR_NOP(mode 2), A / B / A+B, via one MOP vs pushed one by one | `UNPACK.addr_calc`, new `UNPACK.issue` |
| `size` | 40 | one unpacker, MOP, n = 16..1024 datums per UNPACR, bf16/fp8 on A and B, bfp8/bfp4 n = 128/256, fp32-srca on A; bf16 transpose; one no-L1-walk control | `UNPACK.rate_bytes_per_cycle`, `UNPACK.tile_cycles` |
| `dual` | 7 | A and B interleaved (the llama pair), same sizes; compare with `size` | new `UNPACK.dual` (interference) |
| `place` | 26 | pair, B's source = A's + 0..64 KiB (16 B steps first) | new `UNPACK.l1_bank_conflict` |
| `align` | 20 | single A, source base +0..512 B from a 64 KiB boundary | same |
| `extra` | 25 | pushed `[op] + UNPACR` for each op llama emits between unpacks: SETADCZW, SETADCXX+ZW, 4 x RMWCIB, STALLWAIT(TRISC_CFG\|CLR), STALLWAIT(SYNC,UNPACK0) after, RISC base sw+lw, full UNPACK_SYNC credit round trip, WRCFG, SETC16 41, UNPACR_NOP wake-up | `SCALAR.WRCFG/RMWCIB/SETC16` (unpack thread), new `UNPACK.credit_roundtrip` |
| `move` | 12 | the ttrv `unpack.move` lowering per tile, every llama pattern and format, no dvalid | new `UNPACK.move_overhead` |
| `pipe` | 22 | the same with SetDatValid and T1 consuming as fast as possible: bare release, MOVA2D copy (llama copies), ELWMUL x2 (llama dots), MVMUL x16/x4 (attention); also raw MOP pairs | new `UNPACK.pipeline` |
| `handoff` | 11 | `lat`: UNPACR issue -> T1's STALLWAIT(SRC*_VLD) passes (n = 16/256/1024, A/B). `full`: both A banks full, third UNPACR waits; time from T1's release to completion, delay 200/1000/5000 | new `UNPACK.dvalid_latency`, `UNPACK.bank_full_resume` |
| `contention` | 30 | 4 workloads (raw A bf16 1024, raw pair bf16 256, raw A fp8 1024, move pair_face bf16) x {none, BRISC self-loop NoC writes 8 KiB, + NCRISC on NoC1, writes from (2,2) into this L1, reads of this L1 by (2,2), packer loop on T2, packer + self-loop}; self-loop size 512/2048 | new `UNPACK.contention_noc`, `UNPACK.contention_pack` (the piece the model lacks) |
| `throttle` | 18 | override bit (word 70 bit 3) with x1/x2/x4 per unpacker, and the 3 x 3 A/B table | `UNPACK.rate_bytes_per_cycle` x1/x2/x4 |
| `verify` | 18 | correctness per format: bf16/fp8 A/B face/tile, bfp8/bfp4 A/B tile, fp32-srca A face/tile, bf16 transpose, bf16 tile at x1/x2/x4 override | (gate for all of the above) |

Contention launches: T0 waits for the generator's `FL_START` (bounded) before timing, raises `FL_DONE` at the end and
records `generator_stopped_early` / `packer_stopped_early` (nonzero = the traffic ended before the measurement did, so
that record under-states contention). Remote generators run a fixed 20000 x 8 KiB commands.

## Hypotheses and expected values

| quantity | expected | source |
|---|---|---|
| UNPACR issue (thread blocked) | 2 cycles address generation, uncompressed | `UNPACR_Regular.md` Performance; hw.py `UNPACK.addr_calc` |
| MOP-issued back-to-back 16-datum UNPACR | ~2 cycles/op (addr-gen bound; MOP expander emits 1/cycle) | same + `MOPExpander.md` |
| pushed one by one | RISC push ~1 sw/cycle, so the same ~2 unless the FIFO path adds a cycle | hw.py RISCV store = 1 |
| L1 read rate, default throttle | BH without the override: 16/32-bit inputs at "x4 2x" = 128 B burst, 8-bit at x8 = 128 B; L1-side limit 4 x 128-bit ports = 64 B/cycle per unpacker | `UNPACR_Regular.md` (BurstRows logic, BH note), WH `L1.md` "Unpackers" |
| bf16 1024 datums (2 KiB) | 16..32 cycles + ~2 + pipeline fill; i.e. 64-128 B/cycle | above |
| fp8 1024 (1 KiB) | 8..16 cycles | above |
| fp32 -> bf16 1024 (4 KiB) | 32..64 cycles (L1 bytes, not Src bytes, count) | above |
| bfp8 face (16 B exp + 256 B) | ~3-5 cycles + an exponent read on a shared port | `L1.md`: "+ another 128-bit read for BFP exponents" |
| one unpacker with override x1/x2/x4 | 16/32/64 B/cycle | ISA table; hw.py `rate_bytes_per_cycle` |
| both unpackers | jointly 5 x 128-bit reads/cycle (ports 2-4 shared): A+B bf16 tiles ~80 B/cycle combined; override table: x4/x4 -> both x2 | `L1.md`, `UNPACR_Regular.md` interference table |
| B at A + small offset | conflicts when both hit the same 16 B bank in a cycle; the sweep should show a period (bank count x 16 B) | `L1.md` (16 banks x 128 bit on WH; BH bank map undocumented) |
| move overhead per block | RISC credit poll + 8 RMWCIB + base sw/lw + 6 Tensix words + `STALLWAIT(SYNC)` + `SEMGET` serialises each block: expect tens of cycles per move, dominating face-sized moves | movement.py; "Config-context flip 9.5, PC-unpack poll 4.2" (boop-docs/timing README) |
| pipe, llama pair_face + ELWMUL | per tile = max(unpack+move, math); historical matmul row ~37.5/row, CB stream 560/tile include other costs | boop-docs/timing/README.md "Measured unpack path" |
| dvalid -> math sees bank | a few cycles after the last Src write (no documented number) | — |
| full banks -> resume | release (SETRWC clear) -> the waiting unpack restarts within a few cycles; stall = delay + that | `SrcASrcB.md` ownership model |
| NoC self-loop / remote writes | NoC writes are 2 x 128-bit ports with no access-port contention, only bank conflicts: small slowdown unless banks collide; packer writes share ports | `L1.md` port assignments |
| WRCFG / RMWCIB / SETC16 | 1 cycle issue (WRCFG latency 2) | hw.py `SCALAR` (DOC) |

## Risky cases (could wedge the Tensix, the NoC, or need `smi.py -r`)

- **Cross-thread cases** (`pipe`, `handoff`, `verify`): T0's UNPACR with SetDatValid blocks until T1 releases; T1's
  STALLWAIT/MOVA2D/ELWMUL block until T0 delivers. Counts are matched and every flag wait in T1/T0 is soft (the release
  is issued anyway), but if one TRISC kernel fails to start or dies before issuing its share, the other Tensix thread
  stays blocked, its RISC hangs in the firmware's drain, and run.py stops with a HostTimeout (reset by hand).
- **`throttle-*` and `verify-bf16-a_tile-x*`**: set `ovrd_default_throttle_mode` (word 70 bit 3). Known: x8 with the
  override hangs FP32->16-bit, bfp4 and drops rows (ttrv_pack_unpack.md §4/§8); x1/x2/x4 with the override have not
  been run on BH. Only bf16 and fp8 are used here, never bfp4/fp32. Run last.
- **bfp4**: a run crossing a 256-datum exponent group mid 16-byte word "breaks later unpacks until a card reset"
  (ttrv_pack_unpack.md §12). Here every bfp UNPACR is a whole face or the first/second half of one starting on a
  16 B word, which the ISA model allows, but n = 128 with Z stepping (`size-bfp4-*-n128`) starts every other run at
  datum 128 of a group: allowed (ends inside the group) yet the closest to the hazard.
- `verify-bfp*`: the observation path (MOVA2D of a BFP-format SrcA into FP32 Dst) is unproven; a mismatch there may
  be the copy, not the unpacker. ttrv's ALU_FORMAT_SPEC write (SrcA format = bfp8) is kept on purpose.
- `contention-*-wr_in8k/rd_out8k`: a second tile (2,2) runs BRISC NoC traffic aimed at this tile's L1
  [0x170000, 0x180000); posted writes / reads only, bounded command count.
- `contention-*pack*`: T2 runs the packer continuously on garbage Dst; same packer configuration as `verify`.
- Writing cfg word 70 from T2 (pack DATA_FORMAT) clears the unpack throttle bit unless the case passes it through
  (`w70`); this is done for throttle cases.

## Results fields

Timing groups: `counts`, `samples` (raw cycles per sample incl. warmup), `medians`, `slope` (= `median` printed by
run.py, cycles per op: UNPACR, A+B pair, or tile for `move`/`pipe-move-*`), `slopes`, `intercept`,
`generator_stopped_early`, `packer_stopped_early`, and the generators' own logs (`noc_log` = t0, t1, commands,
t_done; `pack_log` = t0, t1, tiles; `math_log` = T1 t0, t_end).
`handoff-lat`: `unpack_done` (UNPACR issue -> T0 drain), `math_seen` (UNPACR issue -> T1 drain returns; includes T1's
drain overhead, compare `unpack_done`). `handoff-full`: `stall` (third UNPACR issue -> done), `after_release`
(T1's release push -> T0 done). `verify`: `ok`, `mismatches`, `first_bad` [index, got, expected].
