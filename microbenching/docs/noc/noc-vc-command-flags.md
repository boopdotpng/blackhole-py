# NoC VC Command Flags

## What the bits are

`CMD_VC_STATIC` and `CMD_VC_LINKED` are fields in the value written to the NoC
command buffer `NOC_CTRL` register. They are not separate MMIO registers.

The Blackhole bit definitions match this repo's `ttk.noc.NOC` constants:

- `NOC_CMD_VC_LINKED = 1 << 6`
- `NOC_CMD_VC_STATIC = 1 << 7`
- `NOC_CMD_STATIC_VC(vc) = vc << 13`

Local definitions:

- `ttk/noc.py`
- `fw/cq.py`

tt-metal definitions:

- `~/tenstorrent/tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_parameters.h`

## What `CMD_VC_STATIC` does

`CMD_VC_STATIC` asks the NoC to use the VC encoded by `NOC_CMD_STATIC_VC(vc)`
instead of dynamic VC allocation. In tt-metal, Blackhole's fast NoC paths
normally set this bit for reads, writes, inline writes, multicast writes, and
atomics.

Useful tt-metal references:

- `noc/noc.h`: the public firmware API describes `static_vc_alloc` as "use
  static VC allocation" and `static_vc` as the selected static request VC.
- `noc_nonblocking_api.h`: the fast write path constructs
  `NOC_CMD_CPY | NOC_CMD_WR | NOC_CMD_VC_STATIC | NOC_CMD_STATIC_VC(vc)`.
- `tt_metal/hw/firmware/src/tt-1xx/blackhole/noc.c`: the lower-level firmware
  wrappers expose `static_vc_alloc` and conditionally OR in
  `NOC_CMD_VC_STATIC`.

Bench:

```bash
python3 microbenching/noc/riscv_noc_vc_static_speed.py \
  --nocs 0,1 --modes dynamic,static --vcs 0,1,2,3,4,5 \
  --sizes 64,1024,16384 --packets 16,128,1024 --repeat 3
```

This bench writes repeated unicast packets from one L1 to another, comparing
`dynamic` control words with `static` control words:

- `dynamic`: clears `CMD_VC_STATIC`
- `static`: sets `CMD_VC_STATIC | NOC_CMD_STATIC_VC(vc)`

The table reports sender-side payload bytes/cycle and receiver-observed
bytes/cycle. The final 4-byte marker is used only to stop the receiver and is
not counted as payload.

Smoke validation:

- `11ed34d0`: `--nocs 0 --modes dynamic,static --vcs 1 --sizes 64 --packets 4 --repeat 1 --no-report`

## What `CMD_ARB_PRIORITY` does

`CMD_ARB_PRIORITY(p)` encodes a VC-allocation arbitration priority in bits
`[30:27]` of the command word. tt-metal's public NoC API documents
`vc_arb_priority` as an "arbitration priority for VC allocation"; priority `0`
disables priority and uses round-robin.

In the lower-level Blackhole firmware wrapper, the priority field is ORed into
unicast copy/accumulate commands. The multicast branch does not include this
field, and the API description ties it to VC allocation, so the most useful
tests are dynamic-VC unicast traffic and contended multi-stream cases.

Bench:

```bash
python3 microbenching/noc/riscv_noc_vc_static_speed.py \
  --nocs 0,1 --modes dynamic,static --vcs 1 \
  --priorities 0,1,15 --sizes 64,1024,16384 --packets 128 --repeat 3
```

Expect single-stream results to mainly validate command legality. A fairness or
throughput effect should show up under contention, where multiple initiators
share a directed route or target endpoint.

Smoke validation:

- `6a2931b7`: `--nocs 0 --modes dynamic --vcs 1 --priorities 0,1,15 --sizes 64 --packets 4 --repeat 1 --no-report`

Focused contention bench:

```bash
python3 microbenching/noc/riscv_noc_arb_priority_order.py \
  --noc 0 --count 4 --priorities 15,1,15,1 \
  --trids 0,1,2,3 --packets 128 --bytes 1024
```

This bench chooses four unicast streams crossing the same directed row cut. It
sets a distinct transaction ID per stream, waits for each sender's transaction
ID outstanding counter to return to zero, and records receiver marker timestamps
to show arrival order.

Observed jobs:

- `6448b01a`: dynamic VC, priorities `0,1,8,15`. Streams with priority `8/15`
  finished far ahead of priority `0/1`, but the all-0 baseline showed stream
  position also matters on this cut.
- `4d6ec69f`: dynamic VC, reversed priorities `15,8,1,0`. Priority `8/15`
  followed the priority assignment, while priority `0` also stayed fast because
  `0` is the special round-robin mode, not "lowest priority".
- `0965d13e`: all priorities `0`, establishes the row-position baseline.
- `a938010f`: all priorities `1`, similar row-position baseline when priorities
  are equal.
- `5447b6b1`: priorities `15,1,15,1`. Both priority-15 streams arrived at about
  `7.1k` cycles, while both priority-1 streams arrived at about `9.4k-9.9k`
  cycles. This is the clearest evidence that nonzero higher priority can win
  arbitration under same-cut contention.
- `e392d9f1`: same `15,1,15,1` pattern with all streams pinned to static VC 1.
  Priority-15 streams arrived at about `6.9k` cycles while priority-1 streams
  arrived at about `10.0k-10.1k` cycles, so the priority field still affects
  this traffic even when `CMD_VC_STATIC` is set.
- `fe884fa8` / `cb6caff3`: five streams, all pinned to static VC 1, priorities
  `1,2,4,8,15` and reversed. Priorities `8/15` arrived at about `6.9k`
  cycles, priority `4` arrived at about `6.9k-7.2k`, and priorities `1/2`
  arrived at about `13.3k-13.4k` cycles. The split followed the priority values
  across reversal, indicating priority buckets/thresholds rather than only row
  position.

## What `CMD_VC_LINKED` does

`CMD_VC_LINKED` links a sequence of NoC commands. The tt-metal firmware API
documents linked calls to the same destination as manifesting on the NoC as a
single multi-command packet, guaranteeing in-order completion for that
destination. It also warns that linked ordering is not available across
different destinations or across unicast/multicast VC classes.

Useful tt-metal references:

- `noc/noc.h`: documents the ordering semantics of the `linked` argument.
- `noc_nonblocking_api.h`: fast write, multicast, and atomic paths OR
  `NOC_CMD_VC_LINKED` when their `linked` argument is set.
- `kernel_profiler.hpp`: profiler quick-push avoids issuing while any command
  buffer has `NOC_CMD_VC_LINKED` set, because long linked multicast runs can
  hold the command buffer in linked state.
- `models/demos/deepseek_v3_b1/unified_kernels/mcast.hpp`: the linked
  multicast sender contains a Blackhole-specific note that only multicast
  transactions are safe to send on the same NoC while linked.

Bench:

```bash
python3 microbenching/noc/riscv_noc_mcast_vc_linked.py \
  --nocs 0,1 --majors x,y --sizes 64,1024,16384 \
  --depths 1,2,4,8 --iters 32
```

Depth `1` is the unlinked baseline. Depths greater than `1` issue a linked
multicast chain where all but the final command have `CMD_VC_LINKED` set. The
bench records both source issue-to-sent time and receiver-observed time, which
is the useful distinction because `VC_LINKED` affects source/trunk bandwidth,
not only ordering.

Existing calibrated result: `microbenching/docs/noc/noc-mcast-scheduler-calibration.md`
shows 16 KiB, fanout-8 multicast source bandwidth improving by about `1.5x` to
`1.6x` at linked depth 4 versus depth 1.

Smoke validation:

- `23deba7d`: `--nocs 0 --majors x --sizes 64 --depths 1,2 --iters 2`

## Run 2026-06-30T02:23:33-04:00 NoC arbitration priority victim/interferer

- NoC: `0`; row: `4`; cut: `6,4->7,4`
- Victim: `1,4->14,4`
- Interferers: `4,4->7,4 5,4->10,4 6,4->11,4`
- Static VC: `1`; dynamic VC: `False`; posted: `False`
- Packets/stream: `128`; bytes/packet: `16384`; victim priorities: `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15`; background priorities: `1,8,15`
- This bench isolates one victim stream and same-cut background streams. The intended clean setting is static VC enabled so the flows share a known VC.
- `0` remains supported by the CLI, but tt-metal documents it as round-robin/no-priority rather than a numeric priority below `1`.

| victim priority | background priority | sender slowdown | receiver slowdown | sender delta cyc | receiver delta cyc |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 3.942 | 3.943 | 100034.0 | 100019.0 |
| 1 | 8 | 3.969 | 3.970 | 100951.0 | 100936.0 |
| 1 | 15 | 3.969 | 3.970 | 100952.0 | 100940.0 |
| 2 | 1 | 1.000 | 1.000 | -17.0 | -14.0 |
| 2 | 8 | 3.966 | 3.969 | 100897.0 | 100896.0 |
| 2 | 15 | 3.966 | 3.968 | 100881.0 | 100881.0 |
| 3 | 1 | 0.999 | 0.999 | -20.0 | -18.0 |
| 3 | 8 | 3.967 | 3.969 | 100903.0 | 100901.0 |
| 3 | 15 | 3.968 | 3.970 | 100935.0 | 100936.0 |
| 4 | 1 | 0.995 | 0.994 | -186.0 | -187.0 |
| 4 | 8 | 3.967 | 3.969 | 100909.0 | 100907.0 |
| 4 | 15 | 3.969 | 3.971 | 100982.0 | 100980.0 |
| 5 | 1 | 0.999 | 0.999 | -22.0 | -28.0 |
| 5 | 8 | 3.969 | 3.971 | 100978.0 | 100977.0 |
| 5 | 15 | 3.967 | 3.969 | 100904.0 | 100902.0 |
| 6 | 1 | 1.000 | 1.000 | -12.0 | -15.0 |
| 6 | 8 | 3.962 | 3.965 | 100748.0 | 100750.0 |
| 6 | 15 | 3.968 | 3.970 | 100937.0 | 100934.0 |
| 7 | 1 | 0.995 | 0.995 | -171.0 | -172.0 |
| 7 | 8 | 3.968 | 3.971 | 100943.0 | 100949.0 |
| 7 | 15 | 3.966 | 3.969 | 100880.0 | 100886.0 |
| 8 | 1 | 1.000 | 1.000 | -1.0 | 1.0 |
| 8 | 8 | 3.951 | 3.954 | 100360.0 | 100364.0 |
| 8 | 15 | 3.968 | 3.971 | 100911.0 | 100913.0 |
| 9 | 1 | 1.000 | 1.000 | -8.0 | -8.0 |
| 9 | 8 | 1.000 | 1.000 | -14.0 | -15.0 |
| 9 | 15 | 3.989 | 3.992 | 101163.0 | 101168.0 |
| 10 | 1 | 1.000 | 1.000 | -4.0 | -7.0 |
| 10 | 8 | 1.000 | 1.000 | -6.0 | -4.0 |
| 10 | 15 | 3.964 | 3.967 | 100802.0 | 100802.0 |
| 11 | 1 | 0.999 | 0.999 | -18.0 | -19.0 |
| 11 | 8 | 1.000 | 0.999 | -17.0 | -21.0 |
| 11 | 15 | 3.967 | 3.969 | 100909.0 | 100909.0 |
| 12 | 1 | 1.005 | 1.005 | 165.0 | 164.0 |
| 12 | 8 | 1.005 | 1.005 | 157.0 | 160.0 |
| 12 | 15 | 3.989 | 3.991 | 101119.0 | 101122.0 |
| 13 | 1 | 1.000 | 1.000 | -9.0 | -12.0 |
| 13 | 8 | 1.000 | 1.000 | -17.0 | -16.0 |
| 13 | 15 | 3.969 | 3.971 | 100995.0 | 100996.0 |
| 14 | 1 | 1.000 | 1.000 | -16.0 | -14.0 |
| 14 | 8 | 1.000 | 1.000 | -10.0 | -11.0 |
| 14 | 15 | 3.963 | 3.966 | 100773.0 | 100775.0 |
| 15 | 1 | 1.005 | 1.005 | 160.0 | 156.0 |
| 15 | 8 | 1.004 | 1.004 | 150.0 | 149.0 |
| 15 | 15 | 3.970 | 3.972 | 100497.0 | 100487.0 |

| mode | victim priority | background priority | repeats | victim sender cyc | victim receiver cyc | victim B/cyc | done delta | seen delta | start skew | ready avg | ready max | ack delta | marker |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 1 |  | 1 | 34004.0 | 33988.0 | 61.674 | 34004.0 | 33988.0 | 0.0 | 228.87 | 239 | 129.0 | 0xa6b00000 |
| contended | 1 | 1 | 1 | 134038.0 | 134007.0 | 15.646 | 134038.0 | 134007.0 | 604.0 | 1002.33 | 2087 | 129.0 | 0xa6b00000 |
| contended | 1 | 8 | 1 | 134955.0 | 134924.0 | 15.540 | 134955.0 | 134924.0 | 528.0 | 1013.55 | 101175 | 129.0 | 0xa6b00000 |
| contended | 1 | 15 | 1 | 134956.0 | 134928.0 | 15.540 | 134956.0 | 134928.0 | 546.0 | 1013.49 | 101167 | 129.0 | 0xa6b00000 |
| baseline | 2 |  | 1 | 34018.0 | 33986.0 | 61.648 | 34018.0 | 33986.0 | 0.0 | 228.87 | 239 | 129.0 | 0xa6b00000 |
| contended | 2 | 1 | 1 | 34001.0 | 33972.0 | 61.679 | 34001.0 | 33972.0 | 549.0 | 228.74 | 239 | 129.0 | 0xa6b00000 |
| contended | 2 | 8 | 1 | 134915.0 | 134882.0 | 15.544 | 134915.0 | 134882.0 | 536.0 | 1013.18 | 101143 | 129.0 | 0xa6b00000 |
| contended | 2 | 15 | 1 | 134899.0 | 134867.0 | 15.546 | 134899.0 | 134867.0 | 526.0 | 1013.12 | 101119 | 129.0 | 0xa6b00000 |
| baseline | 3 |  | 1 | 34012.0 | 33980.0 | 61.659 | 34012.0 | 33980.0 | 0.0 | 228.93 | 239 | 129.0 | 0xa6b00000 |
| contended | 3 | 1 | 1 | 33992.0 | 33962.0 | 61.695 | 33992.0 | 33962.0 | 544.0 | 228.74 | 239 | 129.0 | 0xa6b00000 |
| contended | 3 | 8 | 1 | 134915.0 | 134881.0 | 15.544 | 134915.0 | 134881.0 | 530.0 | 1013.18 | 101143 | 129.0 | 0xa6b00000 |
| contended | 3 | 15 | 1 | 134947.0 | 134916.0 | 15.541 | 134947.0 | 134916.0 | 531.0 | 1013.49 | 101167 | 129.0 | 0xa6b00000 |
| baseline | 4 |  | 1 | 34015.0 | 33986.0 | 61.654 | 34015.0 | 33986.0 | 0.0 | 228.93 | 239 | 129.0 | 0xa6b00000 |
| contended | 4 | 1 | 1 | 33829.0 | 33799.0 | 61.993 | 33829.0 | 33799.0 | 528.0 | 227.69 | 239 | 129.0 | 0xa6b00000 |
| contended | 4 | 8 | 1 | 134924.0 | 134893.0 | 15.543 | 134924.0 | 134893.0 | 539.0 | 1013.30 | 101143 | 129.0 | 0xa6b00000 |
| contended | 4 | 15 | 1 | 134997.0 | 134966.0 | 15.535 | 134997.0 | 134966.0 | 541.0 | 1013.80 | 101215 | 129.0 | 0xa6b00000 |
| baseline | 5 |  | 1 | 34011.0 | 33983.0 | 61.661 | 34011.0 | 33983.0 | 0.0 | 228.87 | 239 | 129.0 | 0xa6b00000 |
| contended | 5 | 1 | 1 | 33989.0 | 33955.0 | 61.701 | 33989.0 | 33955.0 | 534.0 | 228.62 | 239 | 129.0 | 0xa6b00000 |
| contended | 5 | 8 | 1 | 134989.0 | 134960.0 | 15.536 | 134989.0 | 134960.0 | 555.0 | 1013.80 | 101207 | 129.0 | 0xa6b00000 |
| contended | 5 | 15 | 1 | 134915.0 | 134885.0 | 15.544 | 134915.0 | 134885.0 | 546.0 | 1013.24 | 101143 | 129.0 | 0xa6b00000 |
| baseline | 6 |  | 1 | 34011.0 | 33984.0 | 61.661 | 34011.0 | 33984.0 | 0.0 | 228.87 | 239 | 129.0 | 0xa6b00000 |
| contended | 6 | 1 | 1 | 33999.0 | 33969.0 | 61.683 | 33999.0 | 33969.0 | 534.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 6 | 8 | 1 | 134759.0 | 134734.0 | 15.562 | 134759.0 | 134734.0 | 544.0 | 1012.06 | 101159 | 129.0 | 0xa6b00000 |
| contended | 6 | 15 | 1 | 134948.0 | 134918.0 | 15.540 | 134948.0 | 134918.0 | 546.0 | 1013.43 | 101159 | 129.0 | 0xa6b00000 |
| baseline | 7 |  | 1 | 34012.0 | 33978.0 | 61.659 | 34012.0 | 33978.0 | 0.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 7 | 1 | 1 | 33841.0 | 33806.0 | 61.971 | 33841.0 | 33806.0 | 527.0 | 227.69 | 239 | 129.0 | 0xa6b00000 |
| contended | 7 | 8 | 1 | 134955.0 | 134927.0 | 15.540 | 134955.0 | 134927.0 | 539.0 | 1013.55 | 101183 | 129.0 | 0xa6b00000 |
| contended | 7 | 15 | 1 | 134892.0 | 134864.0 | 15.547 | 134892.0 | 134864.0 | 536.0 | 1013.05 | 101111 | 129.0 | 0xa6b00000 |
| baseline | 8 |  | 1 | 34004.0 | 33970.0 | 61.674 | 34004.0 | 33970.0 | 0.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 8 | 1 | 1 | 34003.0 | 33971.0 | 61.675 | 34003.0 | 33971.0 | 526.0 | 228.74 | 239 | 129.0 | 0xa6b00000 |
| contended | 8 | 8 | 1 | 134364.0 | 134334.0 | 15.608 | 134364.0 | 134334.0 | 547.0 | 1004.43 | 2079 | 129.0 | 0xa6b00000 |
| contended | 8 | 15 | 1 | 134915.0 | 134883.0 | 15.544 | 134915.0 | 134883.0 | 549.0 | 1013.18 | 101135 | 129.0 | 0xa6b00000 |
| baseline | 9 |  | 1 | 33848.0 | 33814.0 | 61.958 | 33848.0 | 33814.0 | 0.0 | 227.69 | 239 | 129.0 | 0xa6b00000 |
| contended | 9 | 1 | 1 | 33840.0 | 33806.0 | 61.973 | 33840.0 | 33806.0 | 544.0 | 227.69 | 239 | 129.0 | 0xa6b00000 |
| contended | 9 | 8 | 1 | 33834.0 | 33799.0 | 61.984 | 33834.0 | 33799.0 | 533.0 | 227.63 | 239 | 129.0 | 0xa6b00000 |
| contended | 9 | 15 | 1 | 135011.0 | 134982.0 | 15.533 | 135011.0 | 134982.0 | 535.0 | 1013.92 | 101223 | 129.0 | 0xa6b00000 |
| baseline | 10 |  | 1 | 34004.0 | 33973.0 | 61.674 | 34004.0 | 33973.0 | 0.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 10 | 1 | 1 | 34000.0 | 33966.0 | 61.681 | 34000.0 | 33966.0 | 551.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 10 | 8 | 1 | 33998.0 | 33969.0 | 61.685 | 33998.0 | 33969.0 | 540.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 10 | 15 | 1 | 134806.0 | 134775.0 | 15.557 | 134806.0 | 134775.0 | 541.0 | 1012.43 | 101191 | 129.0 | 0xa6b00000 |
| baseline | 11 |  | 1 | 34010.0 | 33985.0 | 61.663 | 34010.0 | 33985.0 | 0.0 | 228.87 | 239 | 129.0 | 0xa6b00000 |
| contended | 11 | 1 | 1 | 33992.0 | 33966.0 | 61.695 | 33992.0 | 33966.0 | 537.0 | 228.68 | 239 | 129.0 | 0xa6b00000 |
| contended | 11 | 8 | 1 | 33993.0 | 33964.0 | 61.694 | 33993.0 | 33964.0 | 539.0 | 228.87 | 239 | 129.0 | 0xa6b00000 |
| contended | 11 | 15 | 1 | 134919.0 | 134894.0 | 15.544 | 134919.0 | 134894.0 | 555.0 | 1013.24 | 101151 | 129.0 | 0xa6b00000 |
| baseline | 12 |  | 1 | 33836.0 | 33806.0 | 61.980 | 33836.0 | 33806.0 | 0.0 | 227.75 | 239 | 129.0 | 0xa6b00000 |
| contended | 12 | 1 | 1 | 34001.0 | 33970.0 | 61.679 | 34001.0 | 33970.0 | 530.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 12 | 8 | 1 | 33993.0 | 33966.0 | 61.694 | 33993.0 | 33966.0 | 545.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 12 | 15 | 1 | 134955.0 | 134928.0 | 15.540 | 134955.0 | 134928.0 | 535.0 | 1013.55 | 101175 | 129.0 | 0xa6b00000 |
| baseline | 13 |  | 1 | 34017.0 | 33989.0 | 61.650 | 34017.0 | 33989.0 | 0.0 | 228.87 | 239 | 129.0 | 0xa6b00000 |
| contended | 13 | 1 | 1 | 34008.0 | 33977.0 | 61.666 | 34008.0 | 33977.0 | 525.0 | 228.87 | 239 | 129.0 | 0xa6b00000 |
| contended | 13 | 8 | 1 | 34000.0 | 33973.0 | 61.681 | 34000.0 | 33973.0 | 548.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 13 | 15 | 1 | 135012.0 | 134985.0 | 15.533 | 135012.0 | 134985.0 | 565.0 | 1013.98 | 101231 | 129.0 | 0xa6b00000 |
| baseline | 14 |  | 1 | 34010.0 | 33981.0 | 61.663 | 34010.0 | 33981.0 | 0.0 | 228.93 | 239 | 129.0 | 0xa6b00000 |
| contended | 14 | 1 | 1 | 33994.0 | 33967.0 | 61.692 | 33994.0 | 33967.0 | 535.0 | 228.74 | 239 | 129.0 | 0xa6b00000 |
| contended | 14 | 8 | 1 | 34000.0 | 33970.0 | 61.681 | 34000.0 | 33970.0 | 532.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 14 | 15 | 1 | 134783.0 | 134756.0 | 15.559 | 134783.0 | 134756.0 | 549.0 | 1012.25 | 101175 | 129.0 | 0xa6b00000 |
| baseline | 15 |  | 1 | 33840.0 | 33814.0 | 61.973 | 33840.0 | 33814.0 | 0.0 | 227.69 | 239 | 129.0 | 0xa6b00000 |
| contended | 15 | 1 | 1 | 34000.0 | 33970.0 | 61.681 | 34000.0 | 33970.0 | 562.0 | 228.87 | 239 | 129.0 | 0xa6b00000 |
| contended | 15 | 8 | 1 | 33990.0 | 33963.0 | 61.699 | 33990.0 | 33963.0 | 552.0 | 228.81 | 239 | 129.0 | 0xa6b00000 |
| contended | 15 | 15 | 1 | 134337.0 | 134301.0 | 15.611 | 134337.0 | 134301.0 | 544.0 | 1004.19 | 2079 | 129.0 | 0xa6b00000 |

Interpretation:

- This is a stricter test than the earlier finish-order probe: one long victim
  route (`1,4->14,4`) and three background streams all cross the same directed
  row cut (`6,4->7,4`) while pinned to static VC 1.
- With background priority `1`, victim priority `1` slows down by about `3.94x`,
  while victim priorities `2..15` stay at baseline. With background priority
  `8`, victim priorities `1..8` slow down by about `3.95x-3.97x`, while
  priorities `9..15` stay at baseline. With background priority `15`, every
  victim priority `1..15` slows down by about `3.96x-3.99x`.
- So, in this setup, nonzero priority behaves like a strict ordering threshold
  more than a smooth weighted-share number: strictly greater than the contenders
  wins the arbitration strongly; equal or lower shares/loses at the bottleneck.

## Run 2026-06-30T20:34:13-04:00 NoC VC static speed

- Command: `microbenching/noc/riscv_noc_vc_static_speed.py --nocs 0,1 --modes dynamic,static --vcs 0,1,2,3,4,5 --priorities 0 --sizes 64,1024,16384 --packets 128 --repeat 3`
- `dynamic` clears `CMD_VC_STATIC`; `static` sets `CMD_VC_STATIC | NOC_CMD_STATIC_VC(vc)`.
- `priority` is encoded as `priority << 27`; tt-metal documents `0` as round-robin/no priority.
- The measured payload excludes the final 4-byte marker used to stop the receiver.

| mode | posted | noc | vc | priority | source | target | bytes | packets | sender B/cyc | receiver B/cyc | sender cyc | receiver cyc | counter delta | receiver polls |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---|---|---|---:|
| dynamic | 0 | 0 | 0 | 0 | `1,2` | `2,2` | 64 | 128 | 2.370 (min 2.369, max 2.372) | 2.486 (min 2.485, max 2.488) | 3456.667 (min 3454.000, max 3458.000) | 3295.000 (min 3293.000, max 3296.000) | 129.000 (min 129.000, max 129.000) | 309 |
| dynamic | 0 | 0 | 0 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.908 (min 37.904, max 37.915) | 39.767 (min 39.755, max 39.779) | 3457.667 (min 3457.000, max 3458.000) | 3296.000 (min 3295.000, max 3297.000) | 129.000 (min 129.000, max 129.000) | 310 |
| dynamic | 0 | 0 | 0 | 0 | `1,2` | `2,2` | 16384 | 128 | 60.789 (min 60.736, max 60.835) | 61.252 (min 61.200, max 61.302) | 34499.000 (min 34473.000, max 34529.000) | 34238.000 (min 34210.000, max 34267.000) | 129.000 (min 129.000, max 129.000) | 3088 |
| dynamic | 0 | 0 | 1 | 0 | `1,2` | `2,2` | 64 | 128 | 2.364 (min 2.360, max 2.366) | 2.480 (min 2.476, max 2.482) | 3465.000 (min 3462.000, max 3471.000) | 3303.667 (min 3300.000, max 3308.000) | 129.000 (min 129.000, max 129.000) | 311 |
| dynamic | 0 | 0 | 1 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.857 (min 37.849, max 37.860) | 39.687 (min 39.683, max 39.695) | 3462.333 (min 3462.000, max 3463.000) | 3302.667 (min 3302.000, max 3303.000) | 129.000 (min 129.000, max 129.000) | 312 |
| dynamic | 0 | 0 | 1 | 0 | `1,2` | `2,2` | 16384 | 128 | 60.608 (min 60.364, max 60.829) | 61.081 (min 60.836, max 61.299) | 34602.333 (min 34476.000, max 34742.000) | 34334.333 (min 34212.000, max 34472.000) | 129.000 (min 129.000, max 129.000) | 3082 |
| dynamic | 0 | 0 | 2 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.365, max 2.366) | 2.480 (min 2.479, max 2.482) | 3462.667 (min 3462.000, max 3464.000) | 3302.667 (min 3300.000, max 3305.000) | 129.000 (min 129.000, max 129.000) | 310 |
| dynamic | 0 | 0 | 2 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 39.715 (min 39.707, max 39.719) | 3462.000 (min 3462.000, max 3462.000) | 3300.333 (min 3300.000, max 3301.000) | 129.000 (min 129.000, max 129.000) | 312 |
| dynamic | 0 | 0 | 2 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.537 (min 61.317, max 61.757) | 62.015 (min 61.790, max 62.239) | 34079.667 (min 33958.000, max 34202.000) | 33817.333 (min 33695.000, max 33940.000) | 129.000 (min 129.000, max 129.000) | 3054 |
| dynamic | 0 | 0 | 3 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.481 (min 2.479, max 2.482) | 3462.000 (min 3462.000, max 3462.000) | 3301.333 (min 3300.000, max 3304.000) | 129.000 (min 129.000, max 129.000) | 311 |
| dynamic | 0 | 0 | 3 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 39.691 (min 39.671, max 39.719) | 3462.000 (min 3462.000, max 3462.000) | 3302.333 (min 3300.000, max 3304.000) | 129.000 (min 129.000, max 129.000) | 312 |
| dynamic | 0 | 0 | 3 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.266 (min 60.638, max 61.596) | 61.745 (min 61.117, max 62.075) | 34232.000 (min 34047.000, max 34585.000) | 33966.667 (min 33784.000, max 34314.000) | 129.000 (min 129.000, max 129.000) | 3077 |
| dynamic | 0 | 0 | 4 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.482 (min 2.482, max 2.482) | 3462.333 (min 3462.000, max 3463.000) | 3300.667 (min 3300.000, max 3301.000) | 129.000 (min 129.000, max 129.000) | 311 |
| dynamic | 0 | 0 | 4 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.857 (min 37.849, max 37.860) | 39.687 (min 39.671, max 39.707) | 3462.333 (min 3462.000, max 3463.000) | 3302.667 (min 3301.000, max 3304.000) | 129.000 (min 129.000, max 129.000) | 311 |
| dynamic | 0 | 0 | 4 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.220 (min 60.801, max 61.794) | 61.690 (min 61.263, max 62.265) | 34257.333 (min 33938.000, max 34492.000) | 33996.667 (min 33681.000, max 34232.000) | 129.000 (min 129.000, max 129.000) | 3084 |
| dynamic | 0 | 0 | 5 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.482 (min 2.482, max 2.482) | 3462.333 (min 3462.000, max 3463.000) | 3301.000 (min 3301.000, max 3301.000) | 129.000 (min 129.000, max 129.000) | 310 |
| dynamic | 0 | 0 | 5 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.857 (min 37.849, max 37.860) | 39.715 (min 39.707, max 39.719) | 3462.333 (min 3462.000, max 3463.000) | 3300.333 (min 3300.000, max 3301.000) | 129.000 (min 129.000, max 129.000) | 311 |
| dynamic | 0 | 0 | 5 | 0 | `1,2` | `2,2` | 16384 | 128 | 60.736 (min 60.548, max 60.914) | 61.209 (min 61.033, max 61.383) | 34529.333 (min 34428.000, max 34636.000) | 34262.333 (min 34165.000, max 34361.000) | 129.000 (min 129.000, max 129.000) | 3079 |
| static | 0 | 0 | 0 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.367) | 2.482 (min 2.482, max 2.483) | 3462.000 (min 3461.000, max 3463.000) | 3300.000 (min 3299.000, max 3301.000) | 129.000 (min 129.000, max 129.000) | 310 |
| static | 0 | 0 | 0 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.846 (min 37.838, max 37.860) | 39.679 (min 39.671, max 39.683) | 3463.333 (min 3462.000, max 3464.000) | 3303.333 (min 3303.000, max 3304.000) | 129.000 (min 129.000, max 129.000) | 312 |
| static | 0 | 0 | 0 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.683 (min 61.654, max 61.726) | 61.968 (min 61.947, max 62.009) | 33998.667 (min 33975.000, max 34015.000) | 33842.333 (min 33820.000, max 33854.000) | 129.000 (min 129.000, max 129.000) | 3072 |
| static | 0 | 0 | 1 | 0 | `1,2` | `2,2` | 64 | 128 | 2.364 (min 2.361, max 2.366) | 2.481 (min 2.477, max 2.482) | 3464.667 (min 3462.000, max 3470.000) | 3302.333 (min 3300.000, max 3307.000) | 129.000 (min 129.000, max 129.000) | 310 |
| static | 0 | 0 | 1 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 39.699 (min 39.683, max 39.719) | 3462.000 (min 3462.000, max 3462.000) | 3301.667 (min 3300.000, max 3303.000) | 129.000 (min 129.000, max 129.000) | 311 |
| static | 0 | 0 | 1 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.702 (min 61.672, max 61.732) | 61.985 (min 61.949, max 62.020) | 33988.333 (min 33972.000, max 34005.000) | 33833.000 (min 33814.000, max 33853.000) | 129.000 (min 129.000, max 129.000) | 3073 |
| static | 0 | 0 | 2 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.481 (min 2.480, max 2.482) | 3462.333 (min 3462.000, max 3463.000) | 3301.333 (min 3300.000, max 3303.000) | 129.000 (min 129.000, max 129.000) | 311 |
| static | 0 | 0 | 2 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 39.687 (min 39.671, max 39.707) | 3462.000 (min 3462.000, max 3462.000) | 3302.667 (min 3301.000, max 3304.000) | 129.000 (min 129.000, max 129.000) | 312 |
| static | 0 | 0 | 2 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.679 (min 61.659, max 61.717) | 61.966 (min 61.943, max 62.007) | 34001.333 (min 33980.000, max 34012.000) | 33843.333 (min 33821.000, max 33856.000) | 129.000 (min 129.000, max 129.000) | 3073 |
| static | 0 | 0 | 3 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.481 (min 2.480, max 2.482) | 3462.667 (min 3462.000, max 3463.000) | 3302.000 (min 3300.000, max 3303.000) | 129.000 (min 129.000, max 129.000) | 311 |
| static | 0 | 0 | 3 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 39.715 (min 39.707, max 39.719) | 3462.000 (min 3462.000, max 3462.000) | 3300.333 (min 3300.000, max 3301.000) | 129.000 (min 129.000, max 129.000) | 310 |
| static | 0 | 0 | 3 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.683 (min 61.657, max 61.717) | 61.963 (min 61.945, max 61.991) | 33999.000 (min 33980.000, max 34013.000) | 33845.000 (min 33830.000, max 33855.000) | 129.000 (min 129.000, max 129.000) | 3073 |
| static | 0 | 0 | 4 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.365, max 2.366) | 2.482 (min 2.482, max 2.482) | 3462.667 (min 3462.000, max 3464.000) | 3300.333 (min 3300.000, max 3301.000) | 129.000 (min 129.000, max 129.000) | 312 |
| static | 0 | 0 | 4 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 39.703 (min 39.683, max 39.719) | 3462.000 (min 3462.000, max 3462.000) | 3301.333 (min 3300.000, max 3303.000) | 129.000 (min 129.000, max 129.000) | 312 |
| static | 0 | 0 | 4 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.697 (min 61.657, max 61.717) | 61.986 (min 61.952, max 62.009) | 33991.000 (min 33980.000, max 34013.000) | 33832.667 (min 33820.000, max 33851.000) | 129.000 (min 129.000, max 129.000) | 3071 |
| static | 0 | 0 | 5 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.482 (min 2.480, max 2.482) | 3462.333 (min 3462.000, max 3463.000) | 3301.000 (min 3300.000, max 3303.000) | 129.000 (min 129.000, max 129.000) | 311 |
| static | 0 | 0 | 5 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 39.715 (min 39.707, max 39.719) | 3462.000 (min 3462.000, max 3462.000) | 3300.333 (min 3300.000, max 3301.000) | 129.000 (min 129.000, max 129.000) | 311 |
| static | 0 | 0 | 5 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.698 (min 61.659, max 61.717) | 61.980 (min 61.936, max 62.002) | 33990.667 (min 33980.000, max 34012.000) | 33836.000 (min 33824.000, max 33860.000) | 129.000 (min 129.000, max 129.000) | 3072 |
| dynamic | 0 | 1 | 0 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.384 (min 2.382, max 2.386) | 3462.000 (min 3462.000, max 3462.000) | 3436.000 (min 3434.000, max 3439.000) | 129.000 (min 129.000, max 129.000) | 324 |
| dynamic | 0 | 1 | 0 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.857 (min 37.838, max 37.871) | 38.161 (min 38.147, max 38.169) | 3462.333 (min 3461.000, max 3464.000) | 3434.667 (min 3434.000, max 3436.000) | 129.000 (min 129.000, max 129.000) | 321 |
| dynamic | 0 | 1 | 0 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.342 (min 61.088, max 61.482) | 61.576 (min 61.309, max 61.710) | 34188.000 (min 34110.000, max 34330.000) | 34058.333 (min 33984.000, max 34206.000) | 129.000 (min 129.000, max 129.000) | 3094 |
| dynamic | 0 | 1 | 1 | 0 | `1,2` | `2,2` | 64 | 128 | 2.364 (min 2.361, max 2.366) | 2.383 (min 2.380, max 2.385) | 3464.667 (min 3462.000, max 3470.000) | 3437.667 (min 3435.000, max 3442.000) | 129.000 (min 129.000, max 129.000) | 323 |
| dynamic | 0 | 1 | 1 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 38.150 (min 38.136, max 38.158) | 3462.000 (min 3462.000, max 3462.000) | 3435.667 (min 3435.000, max 3437.000) | 129.000 (min 129.000, max 129.000) | 324 |
| dynamic | 0 | 1 | 1 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.245 (min 60.557, max 61.632) | 61.481 (min 60.792, max 61.865) | 34244.000 (min 34027.000, max 34631.000) | 34113.000 (min 33899.000, max 34497.000) | 129.000 (min 129.000, max 129.000) | 3089 |
| dynamic | 0 | 1 | 2 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.365, max 2.366) | 2.384 (min 2.383, max 2.385) | 3462.667 (min 3462.000, max 3464.000) | 3435.667 (min 3435.000, max 3437.000) | 129.000 (min 129.000, max 129.000) | 324 |
| dynamic | 0 | 1 | 2 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 38.139 (min 38.102, max 38.158) | 3462.000 (min 3462.000, max 3462.000) | 3436.667 (min 3435.000, max 3440.000) | 129.000 (min 129.000, max 129.000) | 323 |
| dynamic | 0 | 1 | 2 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.566 (min 61.435, max 61.646) | 61.803 (min 61.681, max 61.876) | 34063.667 (min 34019.000, max 34136.000) | 33932.667 (min 33893.000, max 34000.000) | 129.000 (min 129.000, max 129.000) | 3063 |
| dynamic | 0 | 1 | 3 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.385 (min 2.385, max 2.385) | 3462.667 (min 3462.000, max 3463.000) | 3435.000 (min 3435.000, max 3435.000) | 129.000 (min 129.000, max 129.000) | 322 |
| dynamic | 0 | 1 | 3 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 38.143 (min 38.124, max 38.158) | 3462.000 (min 3462.000, max 3462.000) | 3436.333 (min 3435.000, max 3438.000) | 129.000 (min 129.000, max 129.000) | 322 |
| dynamic | 0 | 1 | 3 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.277 (min 60.611, max 61.623) | 61.506 (min 60.843, max 61.852) | 34226.333 (min 34032.000, max 34600.000) | 34098.667 (min 33906.000, max 34468.000) | 129.000 (min 129.000, max 129.000) | 3098 |
| dynamic | 0 | 1 | 4 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.383 (min 2.381, max 2.385) | 3462.667 (min 3462.000, max 3463.000) | 3437.333 (min 3435.000, max 3441.000) | 129.000 (min 129.000, max 129.000) | 322 |
| dynamic | 0 | 1 | 4 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 38.158 (min 38.158, max 38.158) | 3462.000 (min 3462.000, max 3462.000) | 3435.000 (min 3435.000, max 3435.000) | 129.000 (min 129.000, max 129.000) | 323 |
| dynamic | 0 | 1 | 4 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.449 (min 61.317, max 61.603) | 61.684 (min 61.538, max 61.841) | 34128.667 (min 34043.000, max 34202.000) | 33998.333 (min 33912.000, max 34079.000) | 129.000 (min 129.000, max 129.000) | 3069 |
| dynamic | 0 | 1 | 5 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.384 (min 2.382, max 2.385) | 3462.333 (min 3462.000, max 3463.000) | 3436.333 (min 3435.000, max 3439.000) | 129.000 (min 129.000, max 129.000) | 323 |
| dynamic | 0 | 1 | 5 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 38.158 (min 38.158, max 38.158) | 3462.000 (min 3462.000, max 3462.000) | 3435.000 (min 3435.000, max 3435.000) | 129.000 (min 129.000, max 129.000) | 323 |
| dynamic | 0 | 1 | 5 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.605 (min 61.561, max 61.661) | 61.836 (min 61.795, max 61.894) | 34042.000 (min 34011.000, max 34066.000) | 33914.667 (min 33883.000, max 33937.000) | 129.000 (min 129.000, max 129.000) | 3066 |
| static | 0 | 1 | 0 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.367) | 2.384 (min 2.383, max 2.386) | 3461.667 (min 3461.000, max 3462.000) | 3436.000 (min 3434.000, max 3437.000) | 129.000 (min 129.000, max 129.000) | 323 |
| static | 0 | 1 | 0 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.857 (min 37.838, max 37.871) | 38.158 (min 38.147, max 38.169) | 3462.333 (min 3461.000, max 3464.000) | 3435.000 (min 3434.000, max 3436.000) | 129.000 (min 129.000, max 129.000) | 322 |
| static | 0 | 1 | 0 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.733 (min 61.728, max 61.743) | 61.767 (min 61.765, max 61.770) | 33971.333 (min 33966.000, max 33974.000) | 33952.667 (min 33951.000, max 33954.000) | 129.000 (min 129.000, max 129.000) | 3074 |
| static | 0 | 1 | 1 | 0 | `1,2` | `2,2` | 64 | 128 | 2.364 (min 2.361, max 2.366) | 2.382 (min 2.380, max 2.385) | 3465.333 (min 3462.000, max 3470.000) | 3439.333 (min 3435.000, max 3442.000) | 129.000 (min 129.000, max 129.000) | 324 |
| static | 0 | 1 | 1 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 38.143 (min 38.124, max 38.158) | 3462.000 (min 3462.000, max 3462.000) | 3436.333 (min 3435.000, max 3438.000) | 129.000 (min 129.000, max 129.000) | 323 |
| static | 0 | 1 | 1 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.722 (min 61.717, max 61.732) | 61.765 (min 61.755, max 61.777) | 33977.333 (min 33972.000, max 33980.000) | 33953.667 (min 33947.000, max 33959.000) | 129.000 (min 129.000, max 129.000) | 3074 |
| static | 0 | 1 | 2 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.382 (min 2.381, max 2.383) | 3462.333 (min 3462.000, max 3463.000) | 3439.333 (min 3438.000, max 3441.000) | 129.000 (min 129.000, max 129.000) | 324 |
| static | 0 | 1 | 2 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 38.143 (min 38.124, max 38.158) | 3462.000 (min 3462.000, max 3462.000) | 3436.333 (min 3435.000, max 3438.000) | 129.000 (min 129.000, max 129.000) | 323 |
| static | 0 | 1 | 2 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.848 (min 61.714, max 62.112) | 61.886 (min 61.750, max 62.153) | 33908.667 (min 33764.000, max 33982.000) | 33887.667 (min 33742.000, max 33962.000) | 129.000 (min 129.000, max 129.000) | 3076 |
| static | 0 | 1 | 3 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.383 (min 2.381, max 2.385) | 3463.000 (min 3463.000, max 3463.000) | 3437.000 (min 3435.000, max 3441.000) | 129.000 (min 129.000, max 129.000) | 323 |
| static | 0 | 1 | 3 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 38.147 (min 38.124, max 38.158) | 3462.000 (min 3462.000, max 3462.000) | 3436.000 (min 3435.000, max 3438.000) | 129.000 (min 129.000, max 129.000) | 323 |
| static | 0 | 1 | 3 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.726 (min 61.717, max 61.732) | 61.761 (min 61.759, max 61.763) | 33975.000 (min 33972.000, max 33980.000) | 33956.000 (min 33955.000, max 33957.000) | 129.000 (min 129.000, max 129.000) | 3075 |
| static | 0 | 1 | 4 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.384 (min 2.383, max 2.385) | 3462.333 (min 3462.000, max 3463.000) | 3436.667 (min 3435.000, max 3438.000) | 129.000 (min 129.000, max 129.000) | 323 |
| static | 0 | 1 | 4 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 38.147 (min 38.124, max 38.158) | 3462.000 (min 3462.000, max 3462.000) | 3436.000 (min 3435.000, max 3438.000) | 129.000 (min 129.000, max 129.000) | 323 |
| static | 0 | 1 | 4 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.862 (min 61.715, max 62.127) | 61.902 (min 61.759, max 62.164) | 33901.000 (min 33756.000, max 33981.000) | 33879.000 (min 33736.000, max 33957.000) | 129.000 (min 129.000, max 129.000) | 3075 |
| static | 0 | 1 | 5 | 0 | `1,2` | `2,2` | 64 | 128 | 2.366 (min 2.366, max 2.366) | 2.384 (min 2.384, max 2.385) | 3463.000 (min 3463.000, max 3463.000) | 3435.667 (min 3435.000, max 3436.000) | 129.000 (min 129.000, max 129.000) | 323 |
| static | 0 | 1 | 5 | 0 | `1,2` | `2,2` | 1024 | 128 | 37.860 (min 37.860, max 37.860) | 38.147 (min 38.147, max 38.147) | 3462.000 (min 3462.000, max 3462.000) | 3436.000 (min 3436.000, max 3436.000) | 129.000 (min 129.000, max 129.000) | 322 |
| static | 0 | 1 | 5 | 0 | `1,2` | `2,2` | 16384 | 128 | 61.858 (min 61.730, max 62.112) | 61.896 (min 61.766, max 62.147) | 33903.000 (min 33764.000, max 33973.000) | 33882.333 (min 33745.000, max 33953.000) | 129.000 (min 129.000, max 129.000) | 3073 |
