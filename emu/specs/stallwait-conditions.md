# STALLWAIT and SEMWAIT — Wait Gate Conditions

## Overview

`STALLWAIT` (opcode `0xA2`) and `SEMWAIT` (opcode `0xA6`) are the primary synchronization instructions in the Tensix coprocessor. Both install a "latched wait instruction" into the **Wait Gate** of the issuing thread's frontend pipeline. The Wait Gate re-evaluates the condition every cycle and holds back the selected categories of downstream instructions until all selected conditions are simultaneously satisfied.

Both instructions are dispatched to the **Sync Unit** (1-cycle throughput, shared with SEMINIT/SEMPOST/SEMGET), and the latched condition takes effect immediately — the instruction immediately following STALLWAIT/SEMWAIT is subject to the block mask for at least one cycle, even if the condition is already met.

---

## Instruction Encodings

```
STALLWAIT: opcode=0xA2, word = (0xA2 << 24) | (stall_res << 15) | (wait_res << 0)
SEMWAIT:   opcode=0xA6, word = (0xA6 << 24) | (stall_res << 15) | (sem_sel << 2) | (wait_sem_cond << 0)
```

Field widths: `stall_res` is 9 bits [23:15]; `wait_res` is 13 bits [12:0] for STALLWAIT; `sem_sel` is 8 bits [9:2] and `wait_sem_cond` is 2 bits [1:0] for SEMWAIT.

```c
// ckernel_ops.h macros
#define TT_OP_STALLWAIT(stall_res, wait_res) \
    TT_OP(0xa2, (((stall_res) << 15) + ((wait_res) << 0)))

#define TT_OP_SEMWAIT(stall_res, sem_sel, wait_sem_cond) \
    TT_OP(0xa6, (((stall_res) << 15) + ((sem_sel) << 2) + ((wait_sem_cond) << 0)))
```

---

## `stall_res` — Block Mask (9 bits)

The block mask selects which categories of instructions are held back at the Wait Gate until the wait condition is satisfied. Named B0 (LSB) through B8 (MSB).

| Bit | `p_stall` constant | Value  | Instructions blocked |
|----:|--------------------|-------:|----------------------|
| B0  | `STALL_TDMA`       | `0x01` | Misc Unit (ADDRCRXY, ADDRCRZW, INCADCXY, INCADCZW, RSTDMA, SETADC, SETADCXX, SETADCXY, SETADCZW, SETDVALID), Mover (XMOV), Scalar Unit (ThCon) (ATCAS, ATINCGET, ATINCGETPTR, ATSWAP, DMANOP, LOADIND, LOADREG, REG2FLOP, SETDMAREG, STOREIND, STOREREG, arithmetic DMA ops), and Packer (PACR, PACR_SETREG) |
| B1  | `STALL_SYNC`       | `0x02` | Sync Unit (ATGETM, ATRELM, SEMGET, SEMINIT, SEMPOST, SEMWAIT, STALLWAIT, STREAMWAIT) |
| B2  | `STALL_PACK`       | `0x04` | Packer (PACR, PACR_SETREG) |
| B3  | `STALL_UNPACK`     | `0x08` | Unpacker (UNPACR, UNPACR_NOP) |
| B4  | `STALL_XMOV`       | `0x10` | Mover (XMOV) |
| B5  | `STALL_THCON`      | `0x20` | Scalar Unit / ThCon (ADDDMAREG, ATCAS, ATINCGET, ATINCGETPTR, ATSWAP, BITWOPDMAREG, CMPDMAREG, DMANOP, FLUSHDMA, LOADIND, LOADREG, MULDMAREG, REG2FLOP, SETDMAREG, SHIFTDMAREG, STOREIND, STOREREG, SUBDMAREG) |
| B6  | `STALL_MATH`       | `0x40` | Matrix Unit / FPU (APOOL3S1, APOOL3S2, CLEARDVALID, CLREXPHIST, CONV3S1, CONV3S2, DOTPV, ELWADD, ELWMUL, ELWSUB, GAPOOL, GATESRCRST, GMPOOL, INCRWC, MFCONV3S1, MOVA2D, MOVB2A, MOVB2D, MOVD2A, MOVD2B, MOVDBGA2D, MPOOL3S1, MPOOL3S2, MVMUL, SETRWC, SHIFTXA, SHIFTXB, TRNSPSRCB, ZEROACC, ZEROSRC) |
| B7  | `STALL_CFG`        | `0x80` | Configuration Unit (CFGSHIFTMASK, RDCFG, RMWCIB, SETC16, WRCFG, STREAMWRCFG) |
| B8  | `STALL_SFPU`       | `0x100`| Vector Unit / SFPU (all SFP* instructions) |

**Special cases:**
- `NOP` is blocked only if **all** block bits B0–B8 are set.
- `MOP`, `MOP_CFG`, `REPLAY`, `RESOURCEDECL` are never blocked (handled before the Wait Gate).
- `SEMWAIT`, `STALLWAIT`, and `STREAMWAIT` themselves are always blocked by any block bit (B0–B8 all apply).

**Combined constants in `p_stall`:**
```cpp
STALL_THREAD = 0x1ff   // all bits B0–B8: block everything
```

**Default when `stall_res == 0`:** Hardware treats it as `1 << 6` = `STALL_MATH` (B6 only).

---

## `wait_res` — Condition Mask for STALLWAIT (13 bits)

The condition mask selects which "keep waiting" conditions must all clear before the STALLWAIT is released. Named C0 (LSB) through C12 (MSB). The STALLWAIT remains latched as long as **any** selected condition is true.

| Bit  | `p_stall` constant  | Value   | Keep waiting while... |
|-----:|---------------------|--------:|----------------------|
| C0   | `THCON`             | `0x001` | Scalar Unit (ThCon) has memory requests outstanding for the current thread |
| C1   | `UNPACK0`           | `0x002` | Current thread has an instruction in any stage of Unpacker 0's pipeline |
| C2   | `UNPACK1`           | `0x004` | Current thread has an instruction in any stage of Unpacker 1's pipeline |
| C3   | `PACK0`             | `0x008` | Current thread has an instruction in any stage of the Packer pipeline |
| C4   | `MATH`              | `0x010` | Current thread has an instruction in any stage of the Matrix Unit (FPU) pipeline |
| C5   | `SRCA_CLR`          | `0x020` | `SrcA[Unpackers[0].SrcBank].AllowedClient != SrcClient::Unpackers` |
| C6   | `SRCB_CLR`          | `0x040` | `SrcB[Unpackers[1].SrcBank].AllowedClient != SrcClient::Unpackers` |
| C7   | `SRCA_VLD`          | `0x080` | `SrcA[MatrixUnit.SrcABank].AllowedClient != SrcClient::MatrixUnit` |
| C8   | `SRCB_VLD`          | `0x100` | `SrcB[MatrixUnit.SrcBBank].AllowedClient != SrcClient::MatrixUnit` |
| C9   | `XMOV`              | `0x200` | The Mover has any outstanding memory requests (from any thread or TDMA-RISC) |
| C10  | `TRISC_CFG`         | `0x400` | The associated RISC-V T core has an emitted-but-unprocessed memory request to Tensix GPRs, Tensix config, or TDMA-RISC |
| C11  | `SFPU1` / `WAIT_SFPU` | `0x800` | Current thread has an instruction in any stage of the Vector Unit (SFPU) pipeline |
| C12  | `CFGEXU`            | `0x1000`| **Any** thread has an instruction in any stage of the Configuration Unit pipeline |

> Note: C4 (MATH) and C11 (SFPU1) may wait longer than strictly necessary when the respective unit is being shared by multiple threads simultaneously, since the hardware cannot distinguish per-thread occupancy in those units.

**Combined constants:**
```cpp
UNPACK = UNPACK0 | UNPACK1   // 0x006  — both unpackers
PACK   = PACK0               // 0x008  — alias
ALL_THREAD_RES = THCON | UNPACK0 | UNPACK1 | PACK0 | MATH | XMOV  // 0x21f
```

**Default when `wait_res == 0`:** Hardware uses `0x0F` (C0|C1|C2|C3: ThCon + both unpackers + packer).

**Usage notes from ISA documentation:**
- C0 (THCON): Use after `LOADIND`/`LOADREG`/`ATINCGET` to ensure the GPR contains the result.
- C1, C2 (UNPACK0/1): Block mask should include B3 or B0 to prevent new unpacker instructions from flowing in.
- C3 (PACK): Block mask should include B2 or B0.
- C4 (MATH): Block mask should include B6.
- C5, C6 (SRCA_CLR/SRCB_CLR): Rarely needed directly; UNPACR automatically waits for this.
- C7, C8 (SRCA_VLD/SRCB_VLD): Rarely needed directly; Matrix Unit instructions automatically wait. Needed for MOVD2A/MOVD2B because those instructions do NOT automatically wait.
- C9 (XMOV): Block mask should include B4 or B0.
- C10 (TRISC_CFG): Guards against a RISC-V store to config not yet visible to the coprocessor. Auto TTSync normally handles this.
- C11 (SFPU1): Block mask should include B8.
- C12 (CFGEXU): Block mask should include B7. **Cross-thread:** any thread's config instructions count.

---

## SEMWAIT — Condition Fields

SEMWAIT uses the same `stall_res` block mask as STALLWAIT. Its wait condition is defined by two additional fields:

### `sem_sel` — Semaphore Mask (8 bits, field [9:2])

A bitmask selecting which hardware semaphores to observe. The hardware semaphores are indexed 0–7. The `sem_sel` field uses `t6_sem(index) = (1 << index)` to select semaphores:

| Semaphore index | `t6_sem()` value | `p_stall` constant | Logical name |
|----------------:|----------------:|---------------------|--------------|
| 0 | `0x001` | `SEMAPHORE_0` | `FPU_SFPU` — FPU↔SFPU sync |
| 1 | `0x002` | `SEMAPHORE_1` | `MATH_PACK` — math↔pack sync on Dest |
| 2 | `0x004` | `SEMAPHORE_2` | `UNPACK_TO_DEST` — unpack↔math sync |
| 3 | `0x008` | `SEMAPHORE_3` | `UNPACK_OPERAND_SYNC` — unpack↔pack/math operand sync |
| 4 | `0x010` | `SEMAPHORE_4` | `PACK_DONE` — pack iteration |
| 5 | `0x020` | `SEMAPHORE_5` | `UNPACK_SYNC` — TRISC↔unpack sync on HW kernel |
| 6 | `0x040` | `SEMAPHORE_6` | `UNPACK_MATH_DONE` — unpack or math iteration done |
| 7 | `0x080` | `SEMAPHORE_7` | `MATH_DONE` — math done when unpacking to dest |

The `sem_sel` field occupies the 8-bit span [9:2] of the instruction, so `sem_sel = (1 << sem_index)` directly selects one semaphore. Multiple bits may be set to wait on any of several semaphores simultaneously.

`SEMAPHORE_BIAS = SEMAPHORE_4 = 0x10` appears in `p_stall` as a legacy offset name.

### `wait_sem_cond` — Semaphore Condition (2 bits, field [1:0])

| Bit | `p_stall` constant | Value | Keep waiting while... |
|----:|--------------------|------:|----------------------|
| C0  | `STALL_ON_ZERO`    | `0x1` | Any selected semaphore has `Value == 0` |
| C1  | `STALL_ON_MAX`     | `0x2` | Any selected semaphore has `Value >= Max` |

Both bits may be set. A `wait_sem_cond == 0` is undefined behavior.

The SEMWAIT is released when the selected condition(s) are cleared on all selected semaphores simultaneously. The canonical patterns are:

- `STALL_ON_ZERO` (C0=1, C1=0): Wait until `Value > 0` — i.e., "wait until something has been posted to this semaphore."
- `STALL_ON_MAX` (C0=0, C1=1): Wait until `Value < Max` — i.e., "wait until there is room to post again."

### SEMWAIT vs STALLWAIT

| Feature | STALLWAIT | SEMWAIT |
|---------|-----------|---------|
| Opcode | `0xA2` | `0xA6` |
| Block mask (`stall_res`) | Same | Same |
| Wait condition | 13-bit `ConditionMask` against hardware status signals | 2-bit comparison against 1-of-8 semaphore values |
| `ConditionMask == 0` behavior | Hardware substitutes `0x0F` | Undefined behavior |
| Cleared by | Hardware units becoming idle, ownership changing | SEMPOST or SEMGET from any thread, or RISC-V write to PCBuf semaphore window |
| Typical use | Wait for pipeline stages to drain | Cross-thread handshake (math→pack, unpack→math) |

---

## The Wait Gate

Each of the three Tensix threads has its own Wait Gate stage in the frontend pipeline:

```
Replay Expander
      |
      v
  Wait Gate  <-- STALLWAIT/SEMWAIT latch installed here
      |           re-evaluated every cycle
      v
Backend Dispatch
```

When a STALLWAIT or SEMWAIT reaches the Wait Gate (via the Sync Unit), it installs a latched wait instruction. From that point on, **every cycle**, the Wait Gate tests the condition:
- If any selected condition still signals "keep waiting": hold the next instruction.
- If all selected conditions simultaneously clear: release the latch and allow instructions to flow.

There is a **one-cycle lag** between the condition clearing and the block mask lifting. The instruction immediately following STALLWAIT will always be held for at least one cycle.

Once the block mask is installed, instructions pass through the Wait Gate in order. When the first instruction matching the block mask arrives, **no further instructions of any kind** can pass until the condition clears — not just the blocked category.

### Python pseudocode for Wait Gate evaluation

```python
@dataclass
class LatchedWait:
    opcode: str          # "STALLWAIT" or "SEMWAIT" or None
    block_mask: int      # 9-bit
    cond_mask: int       # 13-bit (STALLWAIT) or 0 (SEMWAIT)
    sem_mask: int        # 8-bit (SEMWAIT) or 0 (STALLWAIT)
    sem_cond: int        # 2-bit (SEMWAIT)

def wait_gate_stall_condition(latch: LatchedWait, hw: HardwareState, thread: int) -> bool:
    """Return True if the Wait Gate should hold the next instruction."""
    if latch.opcode is None:
        return False

    if latch.opcode == "STALLWAIT":
        cond = latch.cond_mask
        keep_waiting = False
        if (cond >> 0) & 1:  keep_waiting |= hw.thcon_requests_outstanding[thread]
        if (cond >> 1) & 1:  keep_waiting |= hw.unpacker0_pipeline_nonempty[thread]
        if (cond >> 2) & 1:  keep_waiting |= hw.unpacker1_pipeline_nonempty[thread]
        if (cond >> 3) & 1:  keep_waiting |= hw.packer_pipeline_nonempty[thread]
        if (cond >> 4) & 1:  keep_waiting |= hw.fpu_pipeline_nonempty[thread]
        if (cond >> 5) & 1:  keep_waiting |= (hw.srca_unpack_bank_owner != "unpackers")
        if (cond >> 6) & 1:  keep_waiting |= (hw.srcb_unpack_bank_owner != "unpackers")
        if (cond >> 7) & 1:  keep_waiting |= (hw.srca_fpu_bank_owner != "matrix_unit")
        if (cond >> 8) & 1:  keep_waiting |= (hw.srcb_fpu_bank_owner != "matrix_unit")
        if (cond >> 9) & 1:  keep_waiting |= hw.mover_requests_outstanding
        if (cond >> 10) & 1: keep_waiting |= hw.trisc_config_request_pending[thread]
        if (cond >> 11) & 1: keep_waiting |= hw.sfpu_pipeline_nonempty[thread]
        if (cond >> 12) & 1: keep_waiting |= hw.cfgu_pipeline_nonempty_any_thread
        return keep_waiting

    if latch.opcode == "SEMWAIT":
        keep_waiting = False
        for i in range(8):
            if not (latch.sem_mask >> i) & 1:
                continue
            sem = hw.semaphores[i]
            if (latch.sem_cond >> 0) & 1:  keep_waiting |= (sem.value == 0)
            if (latch.sem_cond >> 1) & 1:  keep_waiting |= (sem.value >= sem.max)
        return keep_waiting

    return False

def can_instruction_pass(instr, latch: LatchedWait) -> bool:
    """Return True if the instruction is blocked by the current latch."""
    if latch.opcode is None:
        return True
    block = latch.block_mask
    # Instruction's block bits are OR-d; blocked if any matching bit is set
    return (instr.block_bits & block) == 0

# Each cycle:
def wait_gate_cycle(thread):
    latch = thread.latched_wait
    if latch.opcode is not None:
        if not wait_gate_stall_condition(latch, hw, thread.id):
            latch.opcode = None   # condition met, release latch
    # Pass instruction through only if condition is cleared AND instr not blocked
    if thread.next_instr is not None:
        if latch.opcode is None or not can_instruction_pass(thread.next_instr, latch):
            thread.dispatch(thread.next_instr)
```

### Per-thread independence

Each of the three Tensix threads has its own independent Wait Gate. A STALLWAIT issued by T0 (unpack thread) blocks only T0's future instructions; T1 (math) and T2 (pack) continue unaffected. This is the mechanism that enables the three threads to run concurrently at different pipeline stages.

---

## Common STALLWAIT Patterns

### Pattern 1: Before WRCFG — wait for ThCon or Packer

Used throughout the LLK to ensure a GPR value written by SETDMAREG/ADDDMAREG is visible before WRCFG commits it to configuration registers.

```cpp
// Block CFG unit until ThCon (SETDMAREG/ADDDMAREG) completes
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::THCON);
TTI_WRCFG(p_gpr_pack::TMP0, p_cfg::WRCFG_32b, SOME_CFG_ADDR);
```

Decoded: `ttstallwait 128, 1` — block=`STALL_CFG`(B7), wait=`THCON`(C0).

The WRCFG is a Configuration Unit instruction (blocked by B7). The wait condition C0 says "keep waiting while ThCon has memory requests outstanding for this thread." The sequence is: SETDMAREG writes a GPR via ThCon → STALLWAIT waits for ThCon to finish → WRCFG reads the GPR.

When packer is also running and the config register belongs to it:
```cpp
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::THCON | p_stall::PACK0);
```
Decoded: `ttstallwait 128, 9` — additionally waits for packer pipeline to drain (C3).

### Pattern 2: Before MOVD2A/MOVD2B — wait for SrcA/SrcB valid

MOVD2A and MOVD2B move data from Dest to SrcA/SrcB register files. They are Matrix Unit instructions but do **not** automatically wait for the SrcA/SrcB bank ownership to transfer to the Matrix Unit (unlike most FPU read operations). The LLK must wait explicitly.

```cpp
// Before MOVD2A: wait until SrcA bank is owned by Matrix Unit
TTI_STALLWAIT(p_stall::STALL_MATH, p_stall::SRCA_VLD);
TTI_MOVD2A(0, p_mova2d::MATH_HALO_ROWS + 0, addrmod, p_movd2a::MOV_4_ROWS, 0);
```

Decoded: `ttstallwait 64, 128` — block=`STALL_MATH`(B6), wait=`SRCA_VLD`(C7).

```cpp
// Before MOVD2B: wait until SrcB bank is owned by Matrix Unit
TTI_STALLWAIT(p_stall::STALL_MATH, p_stall::SRCB_VLD);
TTI_MOVD2B(0, p_movd2b::SRC_ZERO_OFFSET + 0, addrmod, p_movd2b::MOV_4_ROWS, 0);
```

For transpose operations needing both SrcA and SrcB:
```cpp
TTI_STALLWAIT(p_stall::STALL_MATH, p_stall::WAIT_SFPU | p_stall::SRCA_VLD | p_stall::SRCB_VLD);
```

### Pattern 3: UNPACK_TO_DEST semaphore — unpack→math handshake

Used when unpacking directly into the Dest register (bypass mode). Unpack thread posts to semaphore 2 (`UNPACK_TO_DEST`) when a tile is ready; math thread waits before starting computation.

```cpp
// In T0 (unpack thread): after unpacking tile to dest
t6_semaphore_post<p_stall::UNPACK0>(semaphore::UNPACK_TO_DEST);
//   expands to:
//   TTI_STALLWAIT(p_stall::STALL_SYNC, p_stall::UNPACK0)  [optional wait]
//   TTI_SEMPOST(semaphore::t6_sem(semaphore::UNPACK_TO_DEST))  // sem_sel=0x4

// In T1 (math thread): before consuming the dest data
t6_semaphore_wait_on_zero<p_stall::STALL_SYNC>(semaphore::UNPACK_TO_DEST);
//   expands to:
//   TTI_SEMWAIT(p_stall::STALL_SYNC, t6_sem(UNPACK_TO_DEST), p_stall::STALL_ON_ZERO)
//   = TTI_SEMWAIT(0x2, 0x4, 0x1)
t6_semaphore_get<p_stall::MATH | p_stall::WAIT_SFPU>(semaphore::UNPACK_TO_DEST);
//   expands to:
//   TTI_STALLWAIT(p_stall::STALL_SYNC, p_stall::MATH | p_stall::WAIT_SFPU)
//   TTI_SEMGET(t6_sem(UNPACK_TO_DEST))
```

### Pattern 4: MATH_PACK semaphore — math→pack handshake

The most common cross-thread synchronization. Semaphore 1 (`MATH_PACK`) tracks how many tiles math has written into Dest and pack has not yet consumed. Initialized with `Max = number of dest half-buffers`.

```cpp
// T1 (math): before writing results to dest
// STALL_MATH|STALL_SFPU: block math and SFPU until semaphore has room
TTI_SEMWAIT(p_stall::STALL_MATH | p_stall::STALL_SFPU,
            semaphore::t6_sem(semaphore::MATH_PACK),
            p_stall::STALL_ON_MAX);
// = ttsemwait 322, 2, 2
//   stall_res=0x142 (B1|B6|B8), sem_sel=0x2 (sem[1]), cond=C1

// T1: after math is done, signal packer
t6_semaphore_post<p_stall::MATH | p_stall::WAIT_SFPU>(semaphore::MATH_PACK);
//   TTI_STALLWAIT(STALL_SYNC, MATH|WAIT_SFPU)  — wait for FPU+SFPU idle
//   TTI_SEMPOST(t6_sem(MATH_PACK))             — increment sem[1]

// T2 (pack): wait until math has something to pack
TTI_SEMWAIT(p_stall::STALL_TDMA,
            semaphore::t6_sem(semaphore::MATH_PACK),
            p_stall::STALL_ON_ZERO);
// = ttsemwait 1, 2, 1
//   stall_res=0x1 (B0), sem_sel=0x2 (sem[1]), cond=C0

// T2: after pack is done, release dest slot to math
t6_semaphore_get<WaitRes>(semaphore::MATH_PACK);
//   TTI_STALLWAIT(STALL_SYNC, WaitRes) [if WaitRes != NONE]
//   TTI_SEMGET(t6_sem(MATH_PACK))
```

### Pattern 5: Wait for packer before reconfiguring

When reconfiguring packer-owned configuration registers, the current packer operation must complete first:

```cpp
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::PACK);
TTI_WRCFG(p_gpr_pack::TMP0, p_cfg::WRCFG_32b, PCK_EDGE_OFFSET_SEC0_mask_ADDR32);
```

Or waiting for both packer and ThCon:
```cpp
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::PACK | p_stall::THCON);
```

### Pattern 6: Wait for SFPU before math (dest bank flip)

Before flipping the dest buffer (via SETC16 to configuration), wait for both FPU and SFPU to drain:

```cpp
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::MATH | p_stall::SFPU1);
TT_SETC16(DEST_TARGET_REG_CFG_MATH_Offset_ADDR32, base_addr);
```

Decoded: `ttstallwait 128, 0x810` — block=`STALL_CFG`(B7), wait=`MATH`(C4)|`SFPU1`(C11).

### Pattern 7: Block unpacker until RISC-V config writes complete

When TRISC0 programs configuration registers from RISC-V code (not through the coprocessor), the unpacker must not start until those writes have propagated:

```cpp
TTI_STALLWAIT(p_stall::STALL_UNPACK, p_stall::TRISC_CFG);
```

Decoded: `ttstallwait 8, 1024` — block=`STALL_UNPACK`(B3), wait=`TRISC_CFG`(C10).

### Pattern 8: Wait for SFPU then post to SEMPOST (math thread)

After SFPU operations but before posting a semaphore (so the semaphore signals true completion):

```cpp
// In T1, end of compute: wait for FPU+SFPU, then post MATH_PACK
// ttstallwait 2, 2064
TTI_STALLWAIT(p_stall::STALL_SYNC, p_stall::MATH | p_stall::WAIT_SFPU);
TTI_SEMPOST(semaphore::t6_sem(semaphore::MATH_PACK));

// Then wait for FPU+SFPU before changing CFG (dest flip)
// ttstallwait 128, 2064
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::MATH | p_stall::WAIT_SFPU);
TT_SETC16(...);
```

---

## Annotated Disassembly Examples

### T0 (unpack): matmul_trisc0.S

```asm
; Before WRCFG — wait for ThCon (SETDMAREG) to complete
6130:  ttstallwait  128, 1          ; STALL_CFG | wait THCON(C0)
6130:  ttwrcfg      12, 0, 124      ; write unpack config reg

; Before UNPACR — wait for TRISC_CFG (RISC-V config write) to complete
62ac:  ttstallwait  8, 1024         ; STALL_UNPACK | wait TRISC_CFG(C10)
62b0:  ttunpacr     ...             ; start unpacking

; Wait for unpack pipelines to drain before ThCon operation
6344:  ttstallwait  32, 6           ; STALL_THCON | wait UNPACK0(C1)|UNPACK1(C2)
```

### T1 (math): matmul_trisc1.S

```asm
; Before dest section flip — wait for FPU to drain
64e4:  ttstallwait  128, 16         ; STALL_CFG | wait MATH(C4=FPU)

; Math/SFPU done, block sync unit, wait for FPU+SFPU
6794:  ttstallwait  2, 2064         ; STALL_SYNC | wait MATH(C4)|SFPU1(C11)
6798:  ttsempost    2               ; post to MATH_PACK (sem[1]) — signal packer

; Block CFG until FPU+SFPU drain (dest flip)
67a4:  ttstallwait  128, 2064       ; STALL_CFG | wait MATH(C4)|SFPU1(C11)

; Wait for MATH_PACK semaphore room (math blocked until packer consumes)
654c:  ttsemwait    322, 2, 2       ; stall=B1|B6|B8, sem[1]=MATH_PACK, cond=STALL_ON_MAX
```

### T2 (pack): matmul_trisc2.S

```asm
; Block CFG, wait for ThCon (SETDMAREG completing)
6f80:  ttstallwait  128, 1          ; STALL_CFG | wait THCON(C0)
6f84:  ttwrcfg      28, 0, 12       ; write packer config

; Block TDMA+THCON, wait for PACK pipeline to drain
70e8:  ttstallwait  33, 8           ; STALL_TDMA|STALL_THCON | wait PACK0(C3)

; Block CFG, wait for ThCon + PACK (reconfiguring while packing)
7258:  ttstallwait  128, 9          ; STALL_CFG | wait THCON(C0)|PACK0(C3)

; Wait for MATH_PACK semaphore: stall TDMA until math posts something
71fc:  ttsemwait    1, 2, 1         ; stall=B0(TDMA), sem[1]=MATH_PACK, cond=STALL_ON_ZERO

; Block MATH, wait for PACK to finish (before math reads freed dest)
7294:  ttstallwait  64, 8           ; STALL_MATH | wait PACK0(C3)

; Block THCON, wait for PACK (ThCon config after pack done)
72fc:  ttstallwait  32, 8           ; STALL_THCON | wait PACK0(C3)
```

---

## Emulator Implementation Notes

1. **Latched wait per thread**: Each thread state holds one `LatchedWait` struct (opcode, block_mask, cond_mask, sem_mask, sem_cond). It is overwritten each time a new STALLWAIT or SEMWAIT executes.

2. **Re-evaluation**: Every cycle the Wait Gate evaluates the latched condition against current hardware state. The hardware state inputs needed:
   - Per-thread pipeline occupancy signals: ThCon outstanding, Unpacker 0 in-flight, Unpacker 1 in-flight, Packer in-flight, FPU in-flight, SFPU in-flight.
   - SrcA/SrcB bank ownership state (four possible owners: `None`, `Unpackers`, `MatrixUnit`, or other).
   - Global Mover outstanding count.
   - Per-thread RISC-V config-write-pending flag (C10, rarely needed).
   - Configuration Unit pipeline occupancy across all threads (for C12).
   - 8-element semaphore array `{value: u4, max: u4}`.

3. **Block mask application**: When the condition is not cleared, any instruction whose `block_bits & block_mask != 0` is stalled at the Wait Gate. The Wait Gate holds a single instruction slot; everything behind it in the pipeline is implicitly stalled.

4. **One-cycle release lag**: Implement by letting the release take effect at the start of the next cycle. The instruction that caused the release (the first one past the Wait Gate when the condition clears) sees the block mask still active for one cycle.

5. **Default substitution**: If `stall_res == 0`, treat as `0x40` (B6=STALL_MATH). If `wait_res == 0` in STALLWAIT, treat as `0x0F`.

6. **SEMWAIT `sem_sel` encoding**: The field occupies bits [9:2] of the instruction word. After decoding: `sem_sel_actual = (word >> 2) & 0xFF`. A bit at position `i` selects semaphore `i`. The LLK uses `t6_sem(index) = (1 << index)`.

---

## Source References

- `~/tenstorrent/tt-llk/tt_llk_blackhole/common/inc/ckernel_instr_params.h` — `struct p_stall` (all `STALL_*` and wait condition constants)
- `~/tenstorrent/tt-llk/tt_llk_blackhole/common/inc/ckernel_structs.h` — `struct semaphore` (named semaphore indices, `t6_sem()`)
- `~/tenstorrent/tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h` — `TT_OP_STALLWAIT`, `TT_OP_SEMWAIT` encoding macros
- `~/tenstorrent/tt-llk/tt_llk_blackhole/common/inc/ckernel.h` — `t6_semaphore_post/get/wait_on_max/wait_on_zero` helpers
- `~/tenstorrent/tt-llk/tt_llk_blackhole/common/inc/cmath_common.h` — `wait_math_semaphores()`, `set_math_semaphores()`, `dest_section_flip()`, MOVD2A/MOVD2B stall patterns
- `~/tenstorrent/tt-llk/tt_llk_blackhole/llk_lib/llk_pack_common.h` — `_llk_packer_wait_for_math_done_()`, pack stall patterns
- `~/tenstorrent/tt-llk/tt_llk_blackhole/common/inc/cpack_common.h` — packer configuration STALLWAIT sequences
- `~/tenstorrent/tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_tilize.h` — unpack STALLWAIT patterns including TRISC_CFG
- `~/tenstorrent/tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/STALLWAIT.md` — authoritative block mask table, condition mask semantics
- `~/tenstorrent/tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SEMWAIT.md` — SEMWAIT functional model, condition mask
- `~/tenstorrent/tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SyncUnit.md` — semaphore data structure, RISCV access
- `~/tenstorrent/blackhole-py/dsl.py` — field definitions: `TT_STALLWAIT`, `TT_SEMWAIT`
- `~/tenstorrent/blackhole-py/disasms/matmul_peak/matmul_trisc{0,1,2}.S` — real-world examples decoded above
