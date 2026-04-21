# Tensix Coprocessor Pipeline

## Overview

The Tensix coprocessor is a multi-threaded instruction-driven accelerator embedded in each Tensix tile. It has **3 independent threads** (T0, T1, T2), each with its own frontend pipeline, feeding into **9 shared backend execution units** that run concurrently.

The 5 RISC-V cores on a Tensix tile map to these roles:

| Index | Core   | Role                  | Tensix Push Access         |
|-------|--------|-----------------------|----------------------------|
| 0     | BRISC  | Data Movement 0       | All 3 thread FIFOs         |
| 1     | NCRISC | Data Movement 1       | None                       |
| 2     | TRISC0 | Unpack kernels (T0)   | Own thread FIFO (T0) only  |
| 3     | TRISC1 | Math/Compute kernels (T1) | Own thread FIFO (T1) only |
| 4     | TRISC2 | Pack kernels (T2)     | Own thread FIFO (T2) only  |

## Frontend Pipeline (per-thread)

Each thread has its own independent frontend pipeline:

```
RISC-V store to INSTRN_BUF
         |
         v
  Instruction FIFO (32 slots)
         |
         v
  MOP Expander (expands MOP to up to 32639 instructions)
         |
         v
  Replay Expander (32-slot replay buffer)
         |
         v
  Wait Gate (STALLWAIT/SEMWAIT re-evaluate each cycle)
         |
         v
  Backend Dispatch (by opcode)
```

The three frontend pipelines are fully independent. Instructions are dispatched in-order per thread, but across threads the backend can reorder as each unit processes at its own rate.

## Backend Execution Units (shared)

The backend has 9 concurrent execution units. Dispatch is purely opcode-driven:

| Unit                | Instructions                                      |
|---------------------|---------------------------------------------------|
| Sync Unit           | STALLWAIT, SEMWAIT, SEMINIT, SEMPOST, SEMGET      |
| Unpacker 0 (SrcA/Dst) | UNPACR variants                                |
| Unpacker 1 (SrcB)  | UNPACR variants                                   |
| Matrix Unit (FPU)   | MVMUL, ELWADD, ELWSUB, ELWMUL, MATMUL (1 IPC)   |
| Packers 0-3         | PACR variants (4 packer units)                    |
| Vector Unit (SFPU)  | SFPLOAD, SFPSTORE, SFPADD, SFPMAD, etc. (32x32b) |
| Scalar Unit (ThCon) | SETDMAREG, ADDDMAREG, LOAD_IND, STORE_IND, CAS   |
| Configuration Unit  | SETC16, WRCFG, RMWCIB, CFGSHIFTMASK              |
| Mover               | Bulk L1 data transfers                            |

The Matrix Unit (FPU) accepts at most 1 instruction per cycle regardless of source thread. Unpackers and packers are similarly contended across threads.

The design intent is triple-buffered execution: T0 unpacks the next tile, T1 computes on the current tile, T2 packs the previous tile's results — all running concurrently. Cross-thread synchronization uses hardware semaphores (MATH_PACK, UNPACK_TO_DEST, MATH_DONE) via STALLWAIT.

## Instruction Encoding

All Tensix instructions are 32-bit words:

```
bits[31:24] = opcode (8 bits)
bits[23:0]  = parameters (24 bits)
```

Constructed via:
```c
#define TT_OP(opcode, params) ((opcode << 24) + params)
```

## Instruction Issue Mechanisms

There are two ways to push instructions into a thread's FIFO. Both deliver the identical 32-bit instruction word.

### 1. MMIO Store (runtime-variable operands)

Write the 32-bit instruction word to the thread's INSTRN_BUF address:

```c
// volatile pointer to INSTRN_BUF_BASE (0xFFE40000)
volatile uint32_t* instrn_buffer = (volatile uint32_t*)INSTRN_BUF_BASE;
instrn_buffer[0] = TT_OP_MVMUL(src_a, src_b, ...);
```

Used via `TT_XXX()` macros (e.g. `TT_MVMUL(...)`) and the `ex_push_insn()` helper in firmware.

### 2. Inline `.ttinsn` Custom RISC-V Instruction (compile-time constants)

A custom RISC-V ISA extension that encodes the Tensix instruction directly in the RISC-V instruction stream:

```c
#define INSTRUCTION_WORD(x) __asm__ __volatile__(".ttinsn %0" : : "i"((x)))
```

The 32-bit Tensix opcode is rotated left by 2 bits and stored in the encoding space normally reserved for the RISC-V "C" extension (which these cores do not implement). The hardware rotates right by 2 to recover the original instruction word and pushes it to the thread's FIFO.

Used via `TTI_XXX()` macros (e.g. `TTI_MVMUL(...)`). Requires compile-time constant operands.

On Blackhole, up to 4 adjacent `.ttinsn` instructions can be fused and pushed in a single cycle (though the FIFO still dequeues at most 1 per cycle per thread).

### FIFO Backpressure

The instruction FIFO holds 32 entries per thread. When full, the RISC-V core automatically stalls on the next store/`.ttinsn` until a slot frees up. A slot is freed when the instruction is consumed by the MOP Expander, not when it reaches the backend.

## INSTRN_BUF Address Map

| Address        | Symbol            | Purpose                                  |
|----------------|-------------------|------------------------------------------|
| `0xFFE40000`   | INSTRN_BUF_BASE   | T0 instruction FIFO                      |
| `0xFFE50000`   | INSTRN1_BUF_BASE  | T1 instruction FIFO                      |
| `0xFFE60000`   | INSTRN2_BUF_BASE  | T2 instruction FIFO                      |

Stride between threads: `0x10000` (64 KB).

### Routing by Source Core

The address `0xFFE40000` is context-sensitive — hardware routes the write based on which RISC-V core performs the store:

| Store Address  | From BRISC    | From TRISC0   | From TRISC1   | From TRISC2   |
|----------------|---------------|---------------|---------------|---------------|
| `0xFFE40000`   | Push to T0    | Push to T0    | Push to T1    | Push to T2    |
| `0xFFE50000`   | Push to T1    | (hangs)       | (hangs)       | (hangs)       |
| `0xFFE60000`   | Push to T2    | (hangs)       | (hangs)       | (hangs)       |

Each TRISC can only push to its own thread via `0xFFE40000`. The hardware remaps the address per-core. Writing to `0xFFE50000` or `0xFFE60000` from a TRISC will hang the core.

BRISC can target any thread by writing to the corresponding address directly.

## BRISC Coprocessor Access

BRISC can push Tensix instructions to all three thread FIFOs. However:

- BRISC's pushes enter **after** the MOP Expander (bypassing MOP expansion). This means BRISC cannot issue MOP instructions — only fully-expanded individual instructions.
- There is a mux at each thread's frontend that merges BRISC and TRISC_i inputs. If both push on the same cycle, the **TRISC_i instruction is silently discarded**. BRISC must only push to a thread when that thread's TRISC is not actively issuing.

In practice, BRISC issues instructions only during **initialization** (before TRISCs start their kernels):

```c
// From brisc.cc — device_setup()
instrn_buf[0] = core.instrn_buf_base(0);  // 0xFFE40000
instrn_buf[1] = core.instrn_buf_base(1);  // 0xFFE50000
instrn_buf[2] = core.instrn_buf_base(2);  // 0xFFE60000

core.ex_zeroacc(instrn_buf[0]);                     // Clear dest registers
core.ex_encc(instrn_buf[0]);                         // Enable CC stack
core.ex_load_const(instrn_buf[0]);                   // Load SFPU constants
core.initialize_tensix_semaphores(instrn_buf[0]);    // Init hardware semaphores
```

NCRISC has **no** tensix instruction push capability.

## Hardware Semaphores

The Tensix coprocessor has 8 hardware semaphores accessed via the PC Buffer address space (`PC_BUF_BASE + semaphore_offset`). Key semaphores used for inter-thread synchronization:

| Semaphore       | Index | Purpose                                |
|-----------------|-------|----------------------------------------|
| MATH_PACK       | 1     | TRISC1 (math) <-> TRISC2 (pack) sync on Dst register |
| UNPACK_TO_DEST  | 2     | TRISC0 (unpack) <-> TRISC1 (math) sync on unpack-to-dest |
| MATH_DONE       | 7     | Wait for TRISC1 math completion        |

Semaphore operations (SEMINIT, SEMPOST, SEMGET) are Tensix instructions issued through the instruction FIFO. STALLWAIT with semaphore wait conditions allows a thread to stall in the Wait Gate until a semaphore reaches a threshold.

BRISC initializes all semaphores at boot via `SEMINIT` through T0's FIFO.

## Other Key Address Regions

| Address        | Symbol              | Purpose                                |
|----------------|---------------------|----------------------------------------|
| `0xFFE00000`   | REGFILE_BASE        | ThCon GPR file (192 regs, 64 per thread) |
| `0xFFE80000`   | PC_BUF_BASE         | T0 PC buffer / sync registers          |
| `0xFFE90000`   | PC1_BUF_BASE        | T1 PC buffer                           |
| `0xFFEA0000`   | PC2_BUF_BASE        | T2 PC buffer                           |
| `0xFFB80000`   | TENSIX_MOP_CFG_BASE | MOP Expander config (write-only, 9 words) |
| `0xFFB11000`   | RISCV_TDMA_REGS     | TDMA mover command registers           |
| `0xFFEC0000`   | TENSIX_MAILBOX0     | Hardware mailbox (BRISC)               |
| `0xFFEC1000`   | TENSIX_MAILBOX1     | Hardware mailbox (TRISC0)              |
| `0xFFEC2000`   | TENSIX_MAILBOX2     | Hardware mailbox (TRISC1)              |
| `0xFFEC3000`   | TENSIX_MAILBOX3     | Hardware mailbox (TRISC2)              |
| `0xFFEF0000`   | TENSIX_CFG_BASE     | Backend config registers (unpack/pack/FPU config) |

## BRISC <-> TRISC Orchestration

BRISC controls TRISC lifecycle via two mechanisms:

### Software Mailboxes (L1)

BRISC writes go/done signals to `subordinate_sync` in L1:

```c
subordinate_sync->trisc0 = RUN_SYNC_MSG_GO;   // 0x80 = start kernel
subordinate_sync->trisc1 = RUN_SYNC_MSG_GO;
subordinate_sync->trisc2 = RUN_SYNC_MSG_GO;
// TRISCs write back RUN_SYNC_MSG_DONE (0x00) when finished
```

### PC Buffer

BRISC writes kernel launch tokens to `pc_buf[thread]` to trigger TRISC execution. TRISCs call `tensix_sync()` (a blocking store to `pc_buf_base[1]`) after each kernel to drain the coprocessor pipeline before signaling done.

## Key Opcodes

| Opcode | Instruction | Execution Unit    |
|--------|-------------|-------------------|
| `0x01` | MOP         | Frontend (MOP Expander) |
| `0x02` | REPLAY      | Frontend (Replay Expander) |
| `0x08`-`0x0f` | STALLWAIT, SEMWAIT, SEMINIT | Sync Unit |
| `0x28` | ELWADD      | Matrix Unit (FPU) |
| `0x29` | ELWSUB      | Matrix Unit (FPU) |
| `0x2a` | ELWMUL      | Matrix Unit (FPU) |
| `0x41` | PACR        | Pack Unit         |
| `0x42` | UNPACR      | Unpack Unit       |
| `0x58` | MATMUL      | Matrix Unit (FPU) |
| `0x80`-`0x8f` | SFP* | Vector Unit (SFPU) |
| `0xa0`-`0xaf` | WRCFG, RMWCIB | Config Unit |
| `0xb0`-`0xbf` | THCON_LD_IND, THCON_ST_IND | Scalar Unit (ThCon) |
| `0xb2` | SETC16      | Config Unit       |

## Source References

- ISA spec (coprocessor overview): `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/README.md`
- Push mechanism: `tt-isa-documentation/WormholeB0/TensixTile/BabyRISCV/PushTensixInstruction.md`
- Blackhole push (`.ttinsn` fusion): `tt-isa-documentation/BlackholeA0/TensixTile/BabyRISCV/PushTensixInstruction.md`
- MOP Expander: `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOPExpander.md`
- Instruction encoding (all opcodes): `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h`
- ISA YAML (opcode -> execution unit mapping): `tt-llk/tt_llk_blackhole/instructions/assembly.yaml`
- BRISC firmware: `tt-metal/tt_metal/hw/firmware/src/tt-1xx/brisc.cc`
- Instruction push helpers: `tt-metal/tt_metal/hw/inc/internal/tensix_functions.h`
- Address map: `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix.h`
- Stall/wait parameters: `tt-llk/tt_llk_blackhole/common/inc/ckernel_instr_params.h`
