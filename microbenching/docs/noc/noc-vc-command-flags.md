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
