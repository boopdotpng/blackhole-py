# execution-model

**Source:** [`execution-model.md`](../specs/execution-model.md) · **Emulator:** `blackhole-py/emu/core.py`

## Core types

### `EXEC.CORES.FIVE_PER_TILE`
§3 Core Scheduling

> All 5 RISC-V cores per tile (BRISC, NCRISC, TRISC0/1/2) are stepped in order within each tile.

### `EXEC.CORES.IN_RESET_SKIP`
§3 Core Scheduling ¶skip conditions

> A core is skipped if in_reset == True (held by SOFT_RESET_0 register).

### `EXEC.CORES.HALTED_SKIP`
§3 Core Scheduling ¶skip conditions

> A core is skipped if halted == True (core has halted).

### `EXEC.STEP.ONE_INSN`
§2 Main Loop

> Each RISC-V core executes exactly one instruction per step() call.

### `EXEC.STEP.PC_ADVANCE`
§2 Main Loop

> After a non-branch instruction, PC advances to PC+4.

### `EXEC.STEP.BRANCH_TAKEN`
§2 Main Loop implied by fetch/execute

> A taken branch sets PC to pc + imm (signed).

### `EXEC.STEP.RETURNS_FALSE_ON_STUCK`
§2 Main Loop implied

> step() returns False when PC does not advance (infinite loop at same address), and True when PC advances.

### `EXEC.REGFILE.X0_IMMUTABLE`
§2 Main Loop implied by RV32I spec

> Register x0 (zero) is hardwired to 0; writes to it are silently discarded.

### `EXEC.REGFILE.THIRTY_TWO_REGS`
§2 Main Loop (RV32I)

> The integer register file has exactly 32 registers (x0..x31), each 32 bits wide.

### `EXEC.NOC.IMMEDIATE_COMPLETION`
§6 NOC Transaction Timing ¶functional-first

> For a functional-first emulator, all NOC transactions complete immediately when NOC_CMD_CTRL is written. Status counters are incremented in the same tick.

### `EXEC.RUN.STOPS_ON_STUCK`
§2 implied by Core.run

> run(n) executes up to n instructions; it stops early if step() returns False (PC did not advance).
