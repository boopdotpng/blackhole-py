# Interconnect — cycle timing

NoC, DRAM, L1 / stream registers / circular buffers / PCBufs / mailboxes, and clock
domains. Everything off-tile plus the shared L1 bank fabric.

---

## 1. NoC

### Peak per-hop bandwidth and latency (BH)

Source: `BlackholeA0/NoC/README.md:62-66`:

| Hop | Throughput | Latency |
|---|---|---|
| NIU → directly connected router | 1 flit (512 b) / cycle | ~5 cycles |
| Router → neighbouring router | 1 flit / cycle / axis | **9 cycles** |
| Router → directly connected NIU | 1 flit / cycle | ~5 cycles |

Upgrade from WH (`README.md:44`):
> "higher clock speed (1 GHz → 1.35 GHz), doubling of bandwidth per clock cycle (256
> bits per flit → 512 bits per flit), and widening of addresses (36 bits → 64 bits)"

Flit = 512 b = 64 B. Max burst: `NOC_MAX_BURST_WORDS 256` × 64 B = **16 KiB**
(`noc_parameters.h:289-290`).

Per-link peak: 512 b/cycle × 1.35 GHz ≈ **86.4 GB/s** each direction per NoC.

### Congestion-free RTT formula (crude)

Header crosses H hops; data follows at 1 flit/cycle; response crosses H hops back:
`RTT ≈ 2·(5 + 9·hops) + ceil(N/64)` AICLK cycles.

The empirical data below supersedes this.

### Empirical BH measurements (gold mine)

**`tt-metal/tt_metal/impl/experimental/noc_estimator/latencies/noc_latencies.yaml`** has
**390 BH-specific entries** (tagged `arch: 3`) across payloads
{64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536} bytes.

Selected cuts:

**Unicast write (ONE_TO_ONE, L1→L1, different axis):**
`[373, 393, 372, 379, 388, 414, 439, 510, 636, 916, 1457]` cycles

**Unicast write (same axis):**
`[226, 240, 244, 228, 246, 253, 286, 355, 503, 754, 1300]` — ~40% lower at 64 B.

**Unicast read (ONE_FROM_ONE, different axis):**
`[358, 359, 360, 369, 375, 403, 432, 510, 629, 892, 1441]`

**Unicast read (same axis):**
`[208, 210, 208, 236, 224, 251, 271, 344, 484, 741, 1281]`

**Batched writes (64 tx/barrier, different axis):**
`[2558, 2559, 2566, 2566, 2585, 2594, 4705, 8894, 17391, 34410, 68313]`
→ 2558/64 ≈ **40 cycles/tx** average at 64 B, pipelined.

**DRAM interleaved reads (1 tx/barrier):**
`[481, 481, 500, 506, 540, 538, 578, 665, 841, 841, 841]`
→ **Plateau at 841 cycles for ≥ 16 KiB** — DRAM BW ceiling.

**DRAM reads (64 tx/barrier):**
`[1874, 1874, 1890, 1890, 2032, 3602, 6693, 12705, 22905, -, -]`

**Multicast (same-axis, 1 tx/barrier, 64 B):**
- 4 subs: 626 cyc
- 9 subs: 627 cyc
- 64 subs: 761 cyc
- 110 subs (with loopback): 779 cyc

Multicast overhead over unicast at 64 B same-axis: ~+400–540 cyc path reservation,
amortized per destination. Multicast with loopback (MULTICAST_LINKED) cuts ~37% at
small sizes.

**→ Import this YAML as a lookup table in the emulator's NoC model.**

### Transaction IDs / outstanding limits

`noc_parameters.h:15-16`:
- `NOC_MAX_TRANSACTION_ID 0xF` — 16 IDs (0–15)
- `NOC_MAX_TRANSACTION_ID_COUNT 255` — 8-bit counter (both ++ and -- so wraps if
  software over-commits)

`BlackholeA0/NoC/Counters.md:22-24`:
> "`NIU_MST_REQS_OUTSTANDING_ID(i)` For 0 ≤ i ≤ 15 — 8 bits each"

`noc_parameters.h:65-66`: `// 16 VC, 64 bit registers, 2 ports`. `NOC_VCS = 16`,
`NOC_BCAST_VC_START = 4`.

### Virtual channels

`BlackholeA0/NoC/README.md:48-54`:
> "The four-bit [VC] number consists of one dateline bit, two class bits, and one
> buddy bit. ... 0b00/0b01: Unicast request packets / 0b10: Broadcast request packets
> / 0b11: Response packets (always unicast)."

Head-of-line blocking (`RoutingPaths.md:59`):
> "When congestion occurs, if the two packets have the same virtual circuit number,
> then one packet will wait for the other. Otherwise, the two packets will be
> interleaved onto the link."

Cut-through routing confirmed (`RoutingPaths.md:63`):
> "NoC routers always operate in cut-through mode: a router can start forwarding (the
> flits of) a packet _before_ it has finished receiving the entire packet."

### Posted vs. non-posted writes

Atomic / non-posted: 1 request flit → execution → 1 response flit back (only if
`NOC_CMD_RESP_MARKED=1`). Posted write: no ACK packet.

### Needs microbenching (NoC)

1. **Per-distance RTT breakdown** — YAML tags `same_axis` bool, not (dx, dy). Measure
   (1,0), (2,0), (4,0), (0,1), (0,2), (1,1), (2,2), (4,4) at 64 B to calibrate
   hop-count model.
2. **Atomic RTT** (ATINCGET, ATCAS, ATSWAP) at various hops — **no atomic entries in
   the YAML at all**. Poll `NIU_MST_ATOMIC_RESP_RECEIVED` for completion timestamp.
3. **Read: first-flit vs. last-flit back** (matters for cut-through consumers).
4. **Write RTT (non-posted, issue → ACK) by payload size** — YAML conflates DMA-read
   + transit + write + ACK. Need separated measurement.
5. **Diagonal multicast (non-same-axis rectangle).** YAML only has same-axis mcast.
6. **VC / credit return latency.** 9-cycle router-router hop is known; credit-return
   delay and HOL-blocking depth under sustained injection are not.
7. **NIU outstanding depth → throughput cliff.** Sweep `num_tx_per_barrier` 1–256 at
   512 B.
8. **Cross-chip (Ethernet-routed) NoC RTT.** No numbers anywhere in the repo.
9. **L1 port arbitration: NoC slave vs. packer/unpacker contention.** Measure NoC
   read BW while local packers are busy.

---

## 2. DRAM (GDDR6)

### Topology

Source: `tt-metal/tt_metal/third_party/umd/.../blackhole_implementation.hpp:83-85`:
> "Blackhole P100A has 7 active DRAM banks (1 of 8 physical banks harvested). Each
> bank is fronted by 3 DRAM tiles — three independent NoC ingress points (ports) that
> all map to the same DDR controller."

```c
NUM_DRAM_BANKS = 8;                // physical; 7 active on P100A
NUM_NOC_PORTS_PER_DRAM_BANK = 3;
```

### Peak bandwidth (spec)

`tt-metal/ttnn/core/operation.cpp:33`:
> "BH DRAM bandwidth: 512 GB/s (32GB GDDR6 @ 16 GT/sec)"

`tt-metal/tests/.../test_dram_read.cpp:283`:
`BH_DRAM_BANDWIDTH_GB_PER_SEC = 512;`

Per bank: 512 / 8 = **64 GB/s** (at 16 Gbps × 4 B bus).

### GDDR6 speed / memclk

`tt-zephyr-platforms/lib/tenstorrent/bh_arc/gddr.h:13-15`:
```c
#define MIN_GDDR_SPEED             12000   // Mbps
#define MAX_GDDR_SPEED             20000   // Mbps
#define GDDR_SPEED_TO_MEMCLK_RATIO 16
```

GDDR6 is DDR, so `memclk = speed_Mbps / 16`. Typical P100 / p150 trains at 14 Gbps →
`memclk = 875 MHz`. At 16 Gbps → 1000 MHz. Fallback when config blob corrupt: 12 Gbps →
750 MHz.

P150/galaxy note (release notes `18.7.md:17`): "Reduce Blackhole Galaxy GDDR speed
from 16G to 14G" — so the real-world running value varies.

### GDDRMEMCLK is independent of AICLK

`tt-zephyr-platforms/.../pll.c:217`: `GDDRMEMCLK` fed by **PLL3** (VCO 3000 MHz ÷ 4 =
750 MHz init); AICLK is on PLL0. **No fixed ratio** between them is documented.

### Bank arbitration and no caching

`BlackholeA0/NoC/README.md:15`:
> "as in Tensix tiles, 'L1' is a misnomer here; this a plain RAM rather than any kind
> of cache"

There is no hardware caching between L1 and DRAM. Every DRAM access is an explicit DMA
via `noc_async_read` / `noc_async_write`. The 4-line L0 RISC-V cache (64 B total) is
local to the baby RV core; it does not see DRAM.

### NoC → DRAM alignment

`BlackholeBringUpProgrammingGuide.md:60-61`:
> "Blackhole ... DRAM: Read: 64B, Write: 16B"

For multi-packet transfers >16 KiB, both src and dst must be 64-byte aligned.

### Saturating the banks

`tt-metal/tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md`:
> "To saturate all the DRAM banks, there needs to be one DRAM reader per bank, and
> each reader can only access its assigned bank, otherwise serving multiple readers
> per bank would cause serious NoC congestion. ... we can achieve 92% of the
> theoretical bandwidth."

(The 92% is WH. No BH-specific saturation number is in the repo.)

### Informal latency estimate

`boop-docs/matmul/fast-matmul-eli5.md:61-62`:
> "read A tile <- wait for DRAM (~100 cycles)" — AICLK, informal estimate, not
> datasheet.

### Needs microbenching (DRAM)

1. **DRAM read RTT in AICLK cycles vs. payload size and bank state.** Use a Tensix
   tile adjacent to the DRAM tile (zero intermediate router hops) to isolate DRAM
   controller latency from NoC transit. Sweep 64 B – 16 KiB, same-bank sequential vs.
   bank-switch vs. random.
2. **Write RTT (non-posted, issue → ACK).** ACK source is NoC NIU vs. DRAM
   controller — which?
3. **Refresh impact.** No tREFI/tRFC in open code. Saturate one bank for 100 ms and
   record bandwidth histogram; look for periodic ~30–50 ns gaps.
4. **Per-bank BW vs. concurrency.** Vary 1–7 Tensix tiles targeting bank 0; measure
   per-bank throughput and fairness.
5. **Runtime DRAM data rate confirmation** (read telemetry tag `TAG_GDDR_SPEED`).
6. **NIU → DRAM one-way latency** (excl. NoC hop) — zero-hop read, measure
   `WALL_CLOCK_L` delta.
7. **Arbitration between Tensix tiles for same bank / head-of-line blocking.**

---

## 3. L1 / SRAM

### Size

`BlackholeA0/TensixTile/README.md:4`: "L1 scratchpad RAM (1536 KiB)" at
`0x0000_0000 – 0x0017_FFFF`.

### Structure (WH — BH's `L1.md` is a dead link)

`WormholeB0/TensixTile/L1.md:3-5`:
> "L1 is organised as 16 banks of 91.5 KiB, with each bank capable of one 128-bit read
> or one 128-bit write per cycle. Access to these banks is arbitrated through 16
> access ports; any port can access any bank, but a bank conflict will occur if
> multiple ports try to access the same bank on the same cycle - all but one of the
> ports will be forced to wait."

BH README only says "more L1 bandwidth" — bank count / width not re-specified.

### Narrow-write penalty (5-cycle RMW)

Confirmed on BH in `BlackholeA0/TensixTile/BabyRISCV/README.md:85`:
> "...if [the store queue can coalesce] 128-bit blocks, throughput is one store every
> cycle, otherwise one coalesced store every five cycles."

Mechanism from WH `L1.md:10`:
> "Narrow writes of less than 128 bits ... implemented as an atomic read-modify-write
> operation, which blocks both the port and the underlying bank for five cycles."

Atomics use the same 5-cycle RMW path (`L1.md:11-13`).

### Port arbitration

`WormholeB0/L1.md:16-17`:
> "Each mux can be modelled as performing round-robin allocation in the case of
> conflicts. Where an access port has multiple levels of muxing, there is independent
> conflict resolution and round-robin allocation at each mux."

### Per-client BW (WH reference — the authoritative doc)

From `WormholeB0/TensixTile/L1.md`:

| Client | Bandwidth |
|---|---|
| RISCV narrow stores | 32-bit write / 5 cycles (6.4 b/cyc) |
| RISCV sustained loads | 4×32 b reads / 7 cycles (~18.3 b/cyc) |
| RISCV dependent loads | 32-bit load / 8 cycles (4 b/cyc) |
| Mover (measured) | 8×128 b r + 8×128 b w / 11 cycles (~93.1 b/cyc each way) |
| Single unpacker | 4×128 b reads / cycle |
| Both unpackers | 5×128 b reads / cycle |
| Each packer (write) | 128 b / cycle |
| Packer atomic accumulate | 128 b / 5 cycles |
| Packer non-atomic accumulate | 128 b / 2 cycles |
| ThCon narrow writes | 32 b / 5 cycles |
| ThCon wide writes | 128 b / 3 cycles |
| Each NoC NIU | 256 b r + 256 b w / cycle |

### L1 access port queue

`BlackholeA0/TensixTile/BabyRISCV/MemoryOrdering.md:36`:
> "L1, which can handle 32 simultaneous requests per cycle: one per bank per cycle.
> Thankfully, each L1 access port ensures that no reordering happens as requests pass
> through that port: the request at the front of the queue will cause head-of-line
> blocking if the bank it wants to access is busy, even if a request behind it in that
> same port's queue wants to access an idle bank."

(32 simultaneous requests — note BH-specific; WH was 16 banks. Whether BH has 32
banks or 32 ports into 16 banks is not clarified.)

### Access latency from RV core (BH)

See [`control-plane.md`](control-plane.md) § "Load latency tiers" — 2 / ≥3 / ≥4 /
≥7 / ≥8 / ≥12 cycles by address range and cache state.

---

## 4. Stream registers, CBs, PCBufs, mailboxes

### Stream registers

Read latency from RV core (NoC overlay range, `0xFFB40000`): **≥ 7 cycles**
(`BabyRISCV/README.md:79`).

Wait-Gate polls a stream reg every cycle (`SyncUnit.md:3-15`).

### Circular buffers (CBs)

CBs are **not dedicated hardware** — they are implemented via stream-register
read/write. 
- `cb_push_back(cb, n)` → atomic add `n` to `tiles_received` (reg 10)
- `cb_wait_front(cb, n)` → poll `tiles_received` until `received - acked >= n`
- `cb_pop_front(cb, n)` → atomic add `n` to `tiles_acked` (reg 8)
- `cb_reserve_back(cb, n)` → poll `tiles_acked` until `acked + n - received <= num_pages`

Cost = stream-register write (≥7 cyc from RV via NoC overlay) + whatever polling
overhead the RV loop has.

### PCBufs

`BabyRISCV/PCBufs.md:3`:
> "Each FIFO queue can hold up to **16 32-bit values**; attempting to push more values
> than this will cause the writes to sit in shared buffers within the RISCV B memory
> subsystem. If those shared buffers become full, RISCV B will be stalled until space
> becomes available."

PCBuf read latency: **≥ 3 cycles** (from load-latency tier); blocks until non-empty.
Full/empty propagation happens "within the memory subsystem" — **no cycle count
given**.

### Mailboxes

`BabyRISCV/Mailboxes.md:7`:
> "Each mailbox can hold up to **four 32-bit values**. Furthermore, considering all
> four mailboxes that any given RISCV can write to, those four mailboxes in aggregate
> can only hold four 32-bit values."

Mailbox read: ≥ 3 cycles; blocks until non-empty. Mailbox write: stalls issuing core
when "shared buffers" fill (size undocumented).

### AutoTTSync / ManualTTSync

`BabyRISCV/AutoTTSync.md` — no cycle numbers. RISC-V store is stalled until the
Tensix instruction has "passed through the Wait Gate."

### Needs microbenching (L1 / streams / CBs)

1. **BH L1 bank count and width.** WH = 16 × 128 b; BH says only "more BW." Stride
   test to infer bank count.
2. **BH L1 port assignments** (NoC vs. packer/unpacker/ThCon/RV). No diagram in BH
   docs.
3. **CB `tiles_received`/`tiles_acked` write latency** from RV perspective.
4. **CB wait poll interval** (how often RV polls before unblocking).
5. **PCBuf push→pop round-trip** (between RISC-V B and TRISC).
6. **Mailbox write-to-read propagation latency between cores.**
7. **AutoTTSync stall overhead** when a long-latency Tensix op is pending.
8. **STREAMWAIT update-visibility latency** from a remote NoC atomic write to the
   Wait Gate seeing it.

---

## 5. Clock domains

### Frequency table

| Domain | Frequency | Source |
|---|---|---|
| **AICLK** (Tensix, NoC, baby RV, most of Ethernet tile) | 1,350 MHz busy / 800 MHz idle / 200 MHz min / 1,400 MHz FW ceiling | `tt-umd/.../blackhole_implementation.hpp:262-263`, `bh_arc/aiclk_ppm.c:30-33`, `spirom_data_tables/P100A/fw_table.txt:5-6` |
| AXICLK (PCIe ↔ AI NIU bridge) | 960 MHz | `pll.c:192` ("to saturate PCIE DMA BW") |
| ARCCLK (management µC) | 800 MHz | `pll.c:191` |
| APBCLK | 100 MHz | `pll.c:195` |
| MACCLK (Eth MAC/PCS) | 850 MHz | `pll.c:205` |
| GDDRMEMCLK | 750 MHz init → ~875 MHz trained at 14 Gbps | `pll.c:217`, `gddr.h` |
| GDDR6 data rate | 12–20 Gbps (14–16 typical) | `gddr.h:13-15` |
| L2CPUCLK (SiFive x280 × 4 PLLs) | 800 MHz init, raised post-reset | `pll.c:229-232`, `L2CPUTile/README.md:33` |
| REFCLK (PLL reference, ARC wall timer) | 50 MHz → 20 ns/tick | `bh_arc/timer.h:11-13` |
| DMC refclk (external µC) | 64 MHz | `bh_arc.h:43` |
| PCIe wire rate | PCIe 5.0 x16 → 500 Gb/s | `PCIExpressTile/README.md:31`, `index.rst:46` |
| **DebugTimestamper / WALL_CLOCK** | **1 tick per AICLK cycle** | `TensixTile/DebugTimestamper.md:4` |

### Topology

`PCIExpressTile/README.md:62-66`:
> "The PCI Express Controller straddles the boundary between the PCI Express clock
> domain and the AXI clock domain. The NoC NIUs straddle the boundary between the AXI
> clock domain and the AI clock domain. Once in the AI clock domain, there is a
> **single clock domain** containing every NoC router and every Tensix tile and the
> majority of every Ethernet tile."

→ Inside the AI domain, no cross-clock synchronization. All NoC, Tensix, SFPU, FPU,
unpacker, packer, baby RV, Sync unit, Config unit timing is in AICLK cycles.

### Cross-domain latencies

**Not documented.** The NIUs "straddle the boundary" but synchronizer depths are not
published for PCIe↔AXI or AXI↔AI or AI↔L2CPU.

### Needs microbenching (clocks)

1. **`mcycle` CSR clock identity.** Almost certainly AICLK, but not stated. Cross-check
   `mcycle` delta vs. `WALL_CLOCK_L` delta over a fixed loop.
2. **AXICLK actual runtime value** (FW initialization vs. what `GetAXICLK()` reports).
3. **AXI ↔ AI crossing latency** (synchronizer depth) — L2CPU NoC write → BRISC sees
   data.
4. **PCIe ↔ AXI crossing latency** — host MMIO write → device BRISC reads it.
5. **GDDR6 actual trained data rate** — read `TAG_GDDR_SPEED` telemetry.
6. **L2CPUCLK runtime frequency** — `GetL2CPUCLK()` via telemetry.
7. **Ethernet SerDes per-lane rate** (~25.78 Gbps for 400 GbE, implied not stated).
