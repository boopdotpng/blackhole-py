# Instruction Push Mechanism

How RISC-V cores push 32-bit opcodes into the Tensix coprocessor's instruction FIFOs. See `tensix-coprocessor-pipeline.md` for the full pipeline these instructions flow through.

## Two Delivery Mechanisms, Same Result

Both put the same 32-bit instruction word into the same per-thread FIFO. The coprocessor cannot tell the difference.

### 1. MMIO Store (`TT_*` macros)

A plain `sw` to `INSTRN_BUF_BASE` (`0xFFE40000`):

```c
instrn_buffer[0] = TT_OP_SETC16(reg, val);   // sw to 0xFFE40000
```

- Goes through the RISC-V load/store unit like any other store
- Value can be computed at runtime
- No fusion (one instruction per store)
- Available on BRISC and all TRISCs

### 2. `.ttinsn` Inline Instruction (`TTI_*` macros)

The Tensix opcode is encoded directly into the RISC-V binary:

```c
__asm__ __volatile__(".ttinsn %0" : : "i"(TT_OP_SETC16(reg, val)));
```

- Encoding: the 32-bit Tensix opcode is **rotated left by 2 bits** and placed in the RISC-V instruction stream. Since valid Tensix opcodes are `< 0xC0000000`, the low 2 bits of the encoded word are never `0b11`, which is how standard RISC-V marks 32-bit instructions. The hardware detects this (low bits != `0b11`), rotates right by 2, and pushes the result to the FIFO.
- Decoded at the I-cache, bypasses the load/store unit
- Up to 4 consecutive `.ttinsn` can be fused into one cycle (TRISCs only, not BRISC)
- Value must be a compile-time constant
- This is what objdump shows as `ttsetc16`, `ttseminit`, etc.

### Summary

| | `.ttinsn` (`TTI_*`) | `sw` to instrn_buf (`TT_*`) |
|---|---|---|
| Path | I-cache decode -> FIFO | Load/store unit -> FIFO |
| Fusion | Up to 4/cycle (TRISCs only) | No |
| Operand | Compile-time constant | Runtime value |
| Stalls on full FIFO | Yes | Yes |

## Address Routing

| Address | From BRISC | From TRISC0 | From TRISC1 | From TRISC2 |
|---------|-----------|-------------|-------------|-------------|
| `0xFFE40000` | Push to T0 | Push to T0 | Push to T1 | Push to T2 |
| `0xFFE50000` | Push to T1 | hangs | hangs | hangs |
| `0xFFE60000` | Push to T2 | hangs | hangs | hangs |

Each TRISC writes only to `0xFFE40000` — the hardware routes it to that TRISC's own thread. Only BRISC can use the other two addresses to target specific threads. NCRISC cannot push instructions at all.

## FIFO Behavior

- Capacity: 32 entries per thread (effective limit ~28 before backpressure, 32 reachable via fusion burst)
- **Non-blocking** until full, then the RISC-V core **hardware-stalls** transparently. No polling needed, no software-visible status to check.
- An instruction is considered "pushed" once it enters the FIFO, not when the coprocessor finishes executing it.
- To wait for execution to complete, use `tensix_sync()` (read from `pc_buf_base[1]`, see `pcbufs.md`).

## Emulator Implementation

1. Detect `.ttinsn` in the RISC-V instruction stream: any 32-bit word with low 2 bits != `0b11` (and it's not a 16-bit compressed instruction, which these cores don't support anyway).
2. Rotate right by 2 to recover the Tensix opcode.
3. Push to the thread's instruction FIFO — identical to handling a store to `0xFFE40000`.
4. For stores to `0xFFE40000`/`0xFFE50000`/`0xFFE60000`: route based on the source core (see address routing table above).
5. If the FIFO is full, stall the RISC-V core until space is available.

Both paths feed the same pipeline: Instruction FIFO -> MOP Expander -> Replay Expander -> Wait Gate -> Backend dispatch.
