# registers

**Source:** [`registers.md`](../specs/registers.md)

## CSR cfg0 (0x7C0)

### `REG.CFG0.EXISTS`
§Must Emulate / CSR: cfg0 (0x7C0)

> Every firmware binary (BRISC, NCRISC, all TRISCs) writes cfg0 (CSR 0x7C0) at startup via csrrs/csrrc. Store it correctly.

### `REG.CFG0.BIT_DISBP`
§CSR cfg0 / Bit 1 DisBp

> Bit 1 (DisBp) disables branch predictor; has no effect in the emulator.

### `REG.CFG0.BIT_ENBB_FLOAT`
§CSR cfg0 / Bit 30 EnBFloat

> Bits 30 (EnBFloat) and 31 (EnBFloatRTNE) change FPU behavior for BF16 mode; these are the only bits with observable effects in the emulator.

### `REG.SOFT_RESET.GATES_CORES`
_§SOFT_RESET_0 (0xFFB121B0)_

> SOFT_RESET_0 controls which RISC-V cores execute. Bit 11 = BRISC, bits 12-14 = TRISC0/1/2, bit 18 = NCRISC. When a bit is set the corresponding core is held in reset.

### `REG.SOFT_RESET.ALL_VALUE`
_§SOFT_RESET_0 / Key values_

> SOFT_RESET_ALL = 0x47800 — all 5 RISC-V cores held in reset.

### `REG.SOFT_RESET.BRISC_ONLY_VALUE`
_§SOFT_RESET_0 / Key values_

> SOFT_RESET_BRISC_ONLY_RUN = 0x47000 — TRISCs + NCRISC in reset, BRISC released.

### `REG.RESET_PC.TRISC_REGISTERS`
_§RESET_PC Registers_

> TRISC0_RESET_PC (0xFFB12228), TRISC1_RESET_PC (0xFFB1222C), TRISC2_RESET_PC (0xFFB12230) set each TRISC's boot address.

### `REG.RESET_PC.NCRISC_REGISTER`
_§RESET_PC Registers_

> NCRISC_RESET_PC (0xFFB12238) sets NCRISC's boot address.

### `REG.WALL_CLOCK.MONOTONIC`
_§WALL_CLOCK (0xFFB121F0 / 0xFFB121F8)_

> WALL_CLOCK must be monotonically increasing. TRISC firmware spins in riscv_wait(600) reading it at startup; returning 0 causes TRISCs to hang forever.

### `REG.WALL_CLOCK.LATCH_HI`
_§WALL_CLOCK / 0xFFB121F0 WALL_CLOCK_0_

> Reading WALL_CLOCK_0 (0xFFB121F0) latches the high 32 bits into WALL_CLOCK_1_AT (0xFFB121F8) for atomic 64-bit reads.

### `REG.WRITE_SINK.DEST_CG_CTRL`
_§Write-Sink No-ops / DEST_CG_CTRL_

> DEST_CG_CTRL (0xFFB12240), CG_CTRL_EN (0xFFB12244), and RISCV_TDMA_REG_CLK_GATE_EN (0xFFB11024) are written during device_setup() but control clock gating; the emulator should accept writes and discard them.

### `REG.CSR.MCYCLE`
§Standard RISC-V counters / mcycle 0xB00

> mcycle (0xB00) and mcycleh (0xB80) are the RISC-V cycle counters. At minimum they must be readable without trapping; returning the wall clock value is acceptable.

### `REG.CSR.MINSTRET`
§Return-Zero Stubs / Standard RISC-V counters

> minstret (0xB02) and minstreth (0xB82) count retired instructions. At minimum they must be readable without trapping.

### `REG.CSR.TT_CFG_QSTATUS`
_§Tensix custom CSRs / tt_cfg_qstatus (0xBC0)_

> tt_cfg_qstatus (0xBC0) and tt_cfg_bstatus (0xBC1) return 0 (not busy) in the emulator since coprocessor ops execute synchronously.
