# Registers: What to Emulate

Analysis of which CSRs and tile control/debug registers the emulator actually
needs, based on what firmware accesses in practice.

## Must Emulate (firmware breaks without these)

### CSR: cfg0 (0x7C0)

Every firmware binary (BRISC, NCRISC, all TRISCs) writes this at startup via
`csrrs`/`csrrc`. Always write-only in current firmware (rd=zero), so read-back
value doesn't matter today, but store it correctly anyway.

Firmware sequence (`configure_csr()`):
```
csrrs zero, 0x7c0, 2       # set bit 1 (DisBp)
csrrs zero, 0x7c0, 1<<18   # set bit 18 (DisTrisCache)
csrrc zero, 0x7c0, 2       # clear bit 1
csrrs zero, 0x7c0, 8       # set bit 3 (DisLowCash)
```

Bit fields:

| Bit | Name | Default | Effect |
|-----|------|---------|--------|
| 0 | DisLdBufByp | 0 | Load waits for store queue empty |
| 1 | DisBp | 0 | Disable branch predictor (no effect in emulator) |
| 3 | DisLowCash | 0 | Disable L0 data cache |
| 18 | DisTriscCache | 0 | Disable .ttinsn fusion (no effect in emulator) |
| 24 | DisLowCachePeriodicFlush | 0 | Disable random L0 flush |
| 30 | EnBFloat | 0 | BF16 mode for Zfh instructions |
| 31 | EnBFloatRTNE | 0 | BF16 rounding mode (0=RTZ, 1=RTNE) |

For the emulator, only bits 30-31 have observable effects (they change FPU
behavior). The rest control caches and branch prediction that don't exist in
the emulator.

### SOFT_RESET_0 (0xFFB121B0)

Core launch sequencer. This must actually control which cores execute.

Boot sequence:
1. Host writes `0x47800` (all cores in reset)
2. Host writes `0x47000` (release BRISC only)
3. BRISC firmware writes `0x00000` (release all cores)

Bit assignments:

| Bit | Target |
|-----|--------|
| 0,1,7 | Unpackers |
| 2-5 | Packers 0-3 |
| 6 | Mover |
| 8 | TDMA-RISC |
| 9 | Scalar Unit + THCON |
| 10 | FPU + SFPU + SrcA |
| 11 | RISCV B (BRISC) |
| 12 | RISCV T0 (TRISC0) |
| 13 | RISCV T1 (TRISC1) |
| 14 | RISCV T2 (TRISC2) |
| 15-17 | SrcA/SrcB ownership, Packer-Dst |
| 18 | RISCV NC (NCRISC) |
| 19-22 | SrcA data columns |
| 23 | Auto TTSync |

Key values:
- `SOFT_RESET_ALL = 0x47800` — all 5 RISC-V cores held in reset
- `SOFT_RESET_BRISC_ONLY_RUN = 0x47000` — TRISCs + NCRISC in reset, BRISC released
- `SOFT_RESET_NONE = 0x00000` — all cores running

For the emulator, bits 11-14 and 18 (the five RISC-V cores) are the ones that
matter. Bits 0-10 and 15-23 control coprocessor blocks and can be tracked but
don't need to gate execution.

### RESET_PC Registers

Written by host during firmware upload to set each core's boot address.

| Address | Register | Who writes |
|---------|----------|------------|
| 0xFFB12228 | TRISC0_RESET_PC | Host |
| 0xFFB1222C | TRISC1_RESET_PC | Host |
| 0xFFB12230 | TRISC2_RESET_PC | Host |
| 0xFFB12234 | TRISC_RESET_PC_OVERRIDE | BRISC (writes 0b111) |
| 0xFFB12238 | NCRISC_RESET_PC | Host |
| 0xFFB1223C | NCRISC_RESET_PC_OVERRIDE | BRISC (writes 0x1) |

The OVERRIDE registers are 1-bit (NCRISC) or 3-bit (TRISCs) enables. When set,
the core uses the programmed RESET_PC instead of the default reset vector.

Implementation: when a core is released from reset (SOFT_RESET_0 bit cleared)
and its override bit is set, start execution at the corresponding RESET_PC value.

### WALL_CLOCK (0xFFB121F0 / 0xFFB121F8)

TRISC firmware spins in `riscv_wait(600)` reading these at startup. If they
return 0, TRISCs hang forever. Must be monotonically increasing.

| Address | Register | Behavior |
|---------|----------|----------|
| 0xFFB121F0 | WALL_CLOCK_0 | Low 32 bits of 64-bit counter. Reading this latches WALL_CLOCK_1_AT. |
| 0xFFB121F4 | WALL_CLOCK_1 | High 32 bits (live, may change between reads) |
| 0xFFB121F8 | WALL_CLOCK_1_AT | High 32 bits latched at time of WALL_CLOCK_0 read |

There is also an alias at `0xFFB11024` (WALL_CLOCK_L in the TDMA region) which
BRISC writes with value 63 during `device_setup`. The write likely initializes
or configures the clock.

Implementation: track a global cycle counter. On read of WALL_CLOCK_0, return
low 32 bits and snapshot high 32 bits into WALL_CLOCK_1_AT. WALL_CLOCK_1
returns live high bits. The counter should increment with instruction execution
(doesn't need to be cycle-accurate, just monotonically increasing).

## Write-Sink No-ops (firmware writes, never reads)

These registers are written during BRISC `device_setup()` but control clock
gating which is meaningless in an emulator. Accept writes, discard them.

| Address | Register | Value written |
|---------|----------|---------------|
| 0xFFB12240 | DEST_CG_CTRL | 0 |
| 0xFFB12244 | CG_CTRL_EN | 0 |
| 0xFFB11024 | RISCV_TDMA_REG_CLK_GATE_EN | 0x3F |

## Return-Zero Stubs (specified, not used by current firmware)

These are defined in the spec or in `ckernel.h` but no firmware binary in the
current disassemblies reads them. Implement as simple registers that return 0
(or a sensible default). User kernels or LLK code may eventually use them.

### Standard RISC-V counters

| CSR | Address | Notes |
|-----|---------|-------|
| mcycle | 0xB00 | Cycle counter low. Could return wall clock for correctness. |
| mcycleh | 0xB80 | Cycle counter high. |
| minstret | 0xB02 | Instructions retired low. Could track actual count. |
| minstreth | 0xB82 | Instructions retired high. |

Worth implementing properly since user kernels might use them for profiling.
Returning the wall clock counter for mcycle and an instruction counter for
minstret would be faithful.

### Tensix custom CSRs

| CSR | Address | Notes |
|-----|---------|-------|
| tt_cfg_qstatus | 0xBC0 | Queue status. 0 = queues empty (safe for emulation). |
| tt_cfg_bstatus | 0xBC1 | Backend busy. 0 = not busy (safe for emulation). |
| tt_cfg_sstatus0-7 | 0xBC2-0xBC9 | Stream status (T0/T1/T2) or scratch (B/NC). |
| intp_restore_pc | 0xBCA | Interrupt return PC. Only matters with interrupt emulation. |

For `tt_cfg_qstatus` and `tt_cfg_bstatus`, returning 0 means "not busy" which
is correct for an emulator that executes coprocessor ops synchronously.

The `tt_cfg_sstatus` registers are scratch space for BRISC/NCRISC. For TRISCs
they reflect stream state which would need real stream emulation to be useful.

## Defer Entirely (profiler/debug only)

Not needed for functional emulation. Implement only if adding profiling or
debug tool support.

| Address | Register | Used by |
|---------|----------|---------|
| 0xFFB120B4 | FPU_STICKY_BITS | LLK math layer (not startup firmware) |
| 0xFFB12054 | DBG_BUS_CTRL | Host `read_risc_pc()` debug function |
| 0xFFB1205C | DBG_BUS_RD_DATA | Host `read_risc_pc()` debug function |
| 0xFFB12000-0x124 | PERF_CNT_* | Profiler builds only |
| 0xFFB12218 | PERF_CNT_MUX_CTRL | Profiler builds only |
| 0xFFB12070 | CG_CTRL_HYST0 | Power management (dead code in rvir path) |
| 0xFFB12074 | CG_CTRL_HYST1 | Power management (dead code in rvir path) |
| 0xFFB1207C | CG_CTRL_HYST2 | Power management (dead code in rvir path) |
| 0xFFB121D0 | ECC_CTRL | Not accessed by firmware |
| 0xFFB121D4 | ECC_STATUS | Not accessed by firmware |
| 0xFFB121E0 | WATCHDOG_TIMER | Not accessed by firmware |

## Summary

| Priority | Count | Registers |
|----------|-------|-----------|
| Must work | 8 | cfg0, SOFT_RESET_0, 4x RESET_PC, 2x RESET_PC_OVERRIDE, WALL_CLOCK_0/1_AT |
| Write sinks | 3 | DEST_CG_CTRL, CG_CTRL_EN, CLK_GATE_EN |
| Return-zero stubs | 10 | mcycle/h, minstret/h, qstatus, bstatus, sstatus0-7, intp_restore_pc |
| Defer | ~12 | Perf counters, debug bus, FPU sticky, ECC, watchdog, etc. |
