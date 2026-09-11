## Synchronization families

1. **NoC transaction completion and backpressure**

   Blackhole-py tracks transactions by TID using two counters:

   - `writes_outgoing == 0`: the NoC is finished reading the local source buffer.
   - `requests_outstanding == 0`: read data or a non-posted write/atomic acknowledgment has returned.
   - NIU `SEND_REQUEST == 0`: command registers may be reused.
   - The `< 129` issue-safety check prevents TID-counter ambiguity/overflow.

   This is completion, not data “verification”—there is no checksum or readback comparison. Posted writes only guarantee source release; non-posted writes also guarantee remote acknowledgment. See [noc.py](/home/boop/tenstorrent/blackhole-py/ttk/noc.py:57) and [noc.py](/home/boop/tenstorrent/blackhole-py/ttk/noc.py:227).

2. **Circular-buffer producer/consumer credits**

   This is one four-operation protocol backed by 16-bit `tiles_received` and `tiles_acked` counters:

   - `reserve_back`: waits for free capacity.
   - `push_back`: publishes produced pages.
   - `wait_front`: waits for available pages.
   - `pop_front`: releases consumed pages.

   Read/write pointers are local state; the received/acked counters are the actual synchronization. Page and tile counters are not additional sync mechanisms. There are 32 CB channels. See [cb.py](/home/boop/tenstorrent/blackhole-py/ttk/cb.py:70).

3. **Tensix pipeline scoreboard — `TTSTALLWAIT`**

   There are nine selectable resources to stall:

   `TDMA, SYNC, PACK, UNPACK, XMOV, THCON, MATH, CFG, SFPU`.

   They can wait on thirteen conditions:

   `THCON, UNPACK0, UNPACK1, PACK0, MATH, SRCA_CLR, SRCB_CLR, SRCA_VLD, SRCB_VLD, XMOV, TRISC_CFG, SFPU, CFGEXU`.

   Important corrections:

   - Unpack/pack/math/SFPU completion is primarily these scoreboard conditions, not a TT semaphore.
   - `TRISC_CFG` means pending RISC-issued configuration must reach the engine.
   - There is no `DST_VALID` or `DST_READY` condition.
   - `XMOV` and `CFGEXU` are exposed by the architecture wrapper but currently unused in blackhole-py.

   The complete bit definitions are in [sync.py](/home/boop/tenstorrent/blackhole-py/ttk/sync.py:7) and the official Blackhole definitions in [ckernel_instr_params.h](/home/boop/tenstorrent/tt-llk/tt_llk_blackhole/common/inc/ckernel_instr_params.h:237).

4. **SrcA/SrcB bank rendezvous**

   This is a specialized scoreboard handshake:

   - Unpack waits for `SRCA_CLR`/`SRCB_CLR` before overwriting a source bank.
   - Unpack makes the bank valid.
   - Math waits for `SRCA_VLD`/`SRCB_VLD`.
   - Math instructions clear validity through their instruction/address-modifier release bits.

   So your “SrcA/SrcB clear/valid” entry is correct and distinct from CB synchronization.

5. **Dst ownership: math/SFPU ↔ pack**

   This uses semaphore 1, `MATH_PACK`:

   ```text
   math/SFPU: wait-on-max → write Dst → drain math/SFPU → POST
   pack:      wait-on-zero → read/pack Dst → drain PACK0 → ZEROACC → GET
   ```

   This is what blackhole-py uses instead of separate Dst-valid/Dst-ready signals. `ZEROACC` clears/invalidates Dst before returning it to math. See [fpu.py](/home/boop/tenstorrent/blackhole-py/ttk/fpu.py:106) and [pack.py](/home/boop/tenstorrent/blackhole-py/ttk/pack.py:105).

   Official LLK additionally supports `SyncHalf`: semaphore max 2 plus alternating Dst sections. Blackhole-py initializes max 1 and implements full-Dst ownership only. Therefore “destination ownership switching” is a mode layered over `MATH_PACK`, not an independent primitive.

6. **Unpack configuration-context ownership**

   Semaphore 5, `UNPACK_SYNC`, tracks live unpack contexts:

   - Writing zero to `0xFFE80034` posts/acquires a configuration context.
   - `TRISC_CFG` ensures configuration writes arrive before the unpack MOP starts.
   - `UNPACK0`/`UNPACK1` waits for engine completion.
   - `TTSEMGET(UNPACK_SYNC)` releases the context.

   This is separate from source validity and unpack-engine completion. See [unpack.py](/home/boop/tenstorrent/blackhole-py/ttk/unpack.py:97).

7. **PC-buffer and MOP synchronization**

   Two explicit drains were missing from your list:

   - `sync()` / `tensix_sync()`: blocking PC-buffer synchronization.
   - `mop_sync()`: waits before rewriting MOP configuration.

   Every `Mop.configure()` performs `mop_sync()` before touching the template registers. See [sync.py](/home/boop/tenstorrent/blackhole-py/ttk/sync.py:53) and [mop.py](/home/boop/tenstorrent/blackhole-py/ttk/mop.py:95).

8. **Instruction-level latency hazards**

   Your SFPU dependency entry is real, but it is static instruction scheduling rather than inter-thread synchronization:

   - The SFPU builder tracks per-LReg `ready_at` cycles.
   - It inserts `SFPNOP` for read-after-write latency.
   - Arithmetic generally has two-cycle result latency.
   - `SFPSWAP` requires a forced following NOP on Blackhole.

   Similar fixed-cycle requirements exist around some configuration writes. See [sfpu.py](/home/boop/tenstorrent/blackhole-py/ttk/sfpu.py:179).

9. **RISC memory ordering and software flags**

   RISC-V `fence` orders RISC memory accesses and polling loops. It does not replace a NoC completion wait or Tensix pipeline wait.

   Kernels can build additional synchronization using L1 ready flags, NoC writes, and NoC atomic increments. The distributed argmax example does this. There is no general cross-core barrier object in blackhole-py.

10. **Firmware launch/completion barrier**

    Outside the datapath, BRISC coordinates NCRISC and the three TRISCs through `GO_SIGNAL` and `SUBORDINATE_SYNC`. BRISC waits for every subordinate to report `DONE`, then increments the dispatch completion counter. See [core.py](/home/boop/tenstorrent/blackhole-py/fw/core.py:123).

## The eight TT semaphores

Yes, exactly eight are architecturally assigned:

| Index | Name | Intended protocol | Current blackhole-py |
|---:|---|---|---|
| 0 | `FPU_SFPU` | FPU ↔ SFPU coordination | Used for BRISC→SFPU seed handoff |
| 1 | `MATH_PACK` | Dst ownership between math/SFPU and pack | Actively used |
| 2 | `UNPACK_TO_DEST` | Unpack ↔ math direct-to-Dst ownership | Partial implementation |
| 3 | `UNPACK_OPERAND_SYNC` | Unpack operand/mailbox release to math and pack | Defined, unused |
| 4 | `PACK_DONE` | Pack iteration instrumentation/delay or custom pack→unpack protocol | Defined, unused |
| 5 | `UNPACK_SYNC` | TRISC ↔ unpack configuration contexts | Actively used |
| 6 | `UNPACK_MATH_DONE` | Unpack-or-math iteration instrumentation | Defined, unused |
| 7 | `MATH_DONE` | Math-ready handshake for direct-to-Dst | Waiter exists; producer absent |

The authoritative mapping is [ckernel_structs.h](/home/boop/tenstorrent/tt-llk/tt_llk_blackhole/common/inc/ckernel_structs.h:13). `SEMPOST` atomically increments and `SEMGET` decrements; `SEMWAIT` can stall while the value is zero or while it equals its configured maximum.

## Direct-to-Dst caveat

Your “unpack-to-destination requires stalls” entry is correct, but it is a compound protocol:

- Math-ready semaphore 7.
- Direct-Dst ownership semaphore 2.
- `TRISC_CFG | PACK0` before issue.
- `THCON | UNPACK0` after issue.
- Unpack-context semaphore 5.
- PC-buffer synchronization.

More importantly, current blackhole-py has no `MATH_DONE` producer and no math-side consumer of `UNPACK_TO_DEST`, and there are no current callers of `UnpackTarget.DST`. As written, that path is dormant/incomplete and would block if invoked. The official LLK contains the missing math-side handshake.

Finally, Blackhole also has hardware mutex acquire/release (`ATGETM`/`ATRELM`), notably mutex 0 for shared configuration RMW and mutex 4 for SFPU ownership. The ISA encodes them, but blackhole-py’s TTK layer does not currently use them.

I made no filesystem changes.