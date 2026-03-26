# Blackhole P100A RISC-V Debug Infrastructure

Interactive debugger for stepping through kernels on Tensix RISC-V cores, inspecting registers, memory, and compute state.

## Quick Start

```bash
# run any example with DEBUG=1 to drop into the debugger at kernel entry
PYTHONPATH=. DEBUG=1 uv run examples/matmul_peak.py

# or attach manually in Python
from debug.repl import DebugSession
sess = DebugSession(fd=device.fd, cores=worker_cores)
sess.add_elf("trisc1", trisc1_elf_bytes)
sess.repl()
```

## Architecture

```
debug/
  regs.py    - register addresses, bit fields, Tensix instruction encodings
  core.py    - single-tile: DR protocol, halt/step/continue, GPR, breakpoints
  inspect.py - single-tile: Dest, SrcA, SrcB, LRegs, L1, CFG reads
  source.py  - addr2line/objdump/c++filt wrappers for PC -> source mapping
  multi.py   - multi-core: scan 118 cores, snapshot, bulk halt/resume/breakpoints
  repl.py    - interactive cmd.Cmd REPL tying everything together
```

All communication goes through `hw.TLBWindow` (ioctl + mmap to `/dev/tenstorrent/0`). No additional dependencies.

## Hardware Debug Capabilities

### Per-Core Debug Interface (BRISC, TRISC0, TRISC1, TRISC2 only)

Each core has 14 debug registers (DR0-DR17) accessed via 4 MMIO registers at `0xFFB12080-0xFFB1208C`. The host writes to `RISC_DBG_CNTL_0/1` and reads from `RISC_DBG_STATUS_0/1`.

| Capability | Mechanism |
|---|---|
| Halt / resume / single-step | DR(1) command bits 0/2/1 |
| Read/write GPRs x0-x31 | DR(2)=reg index, DR(1) bit 3/4, result in DR(4) |
| Read/write PC | GPR pseudo-index 32 (or debug bus for non-intrusive read) |
| Read/write memory (as core) | DR(2)=addr, DR(1) bit 5/6, result in DR(4) |
| 8 hardware breakpoints | DR(10-17)=address, DR(5)=modes (4 bits each) |
| 8 memory watchpoints | Same as breakpoints, mode 9/10/11 for read/write/both |

### NCRISC Limitations

NCRISC has **no debug hardware**. The `Which_RISCV` field in `RISC_DBG_CNTL_0` is 2 bits (values 0-3 = B/T0/T1/T2). There is no encoding for NCRISC. Available: PC via debug bus (non-intrusive, approximate), soft reset, L1 inspection.

### Blackhole-Specific Quirks

| Quirk | Details |
|---|---|
| Double-step bug | `step()` must be issued twice (hardware bug) |
| PC via debug bus | Blackhole reads PC from daisy chain, not DR protocol |
| Direct dest access | Dest register file mapped at `0xFFBD8000` (32KB, Blackhole only) |
| TRISC2 memory bug | Private memory at `addr % 16 > 4` broken (tt-exalens issue #528) |

## REPL Command Reference

### Execution Control

| Command | Description |
|---|---|
| `halt` | Halt all 4 debuggable RISCs on the current tile |
| `step` / `s` | Single-step current RISC (others stay halted) |
| `cont` / `c` | Resume all RISCs on current tile |
| `status` / `st` | Show halt/running state of all 5 RISCs |

### Register / PC Inspection

| Command | Description |
|---|---|
| `regs [risc]` | All 32 GPRs + PC (core must be halted) |
| `pc` | All 5 PCs with source location (non-intrusive) |

### Source / Disassembly

| Command | Description |
|---|---|
| `where` / `w` | Source + disassembly at current PC |
| `list` | Source context (10 lines around PC) |
| `disasm` | Disassembly context (10 instructions around PC) |

Requires ELFs compiled with `-g`. Source mapping uses `riscv-tt-elf-addr2line` and `riscv-tt-elf-objdump` from `tt-metal-deps/sfpi-toolchain/bin/`.

### Memory

| Command | Description |
|---|---|
| `l1 <addr> [count]` | Hex dump L1 memory (no halt required) |
| `read <addr>` | Read word from core's address space (halted, sees private mem + CFG) |

### Tensix Compute State

| Command | Description |
|---|---|
| `dest [tile]` | Dest register tile 0-7 as FP32 grid (direct read at `0xFFBD8000`) |
| `srca [rows]` | SrcA register (via MOVDBGA2D injection, requires math halted, slow) |
| `srcb [bank] [rows]` | SrcB register, bank 0 or 1 (direct debug array read) |
| `lregs` | All SFPU LRegs: 0-7 + 11-14 + 16 (via SFPSTORE injection) |
| `lreg <n>` | Single LReg, all 32 lanes |
| `cfg <idx>` | Read Tensix CFG register by index |
| `fpu` | FPU sticky bits (NaN/Inf/denorm flags) |
| `clock` | 64-bit tile wall clock (cycle counter) |

### Breakpoints

| Command | Description |
|---|---|
| `break <addr> [idx]` | Set PC breakpoint on current RISC (up to 8, idx 0-7) |
| `watch <addr> [r\|w\|rw] [idx]` | Memory watchpoint |
| `clearbreak [idx\|all]` | Clear breakpoint(s) on current RISC |

### Multi-Core (118 cores)

| Command | Description |
|---|---|
| `scan [risc]` | Read all PCs via debug bus (~1ms, non-intrusive) |
| `snapshot` | Halt ALL cores, read all status + PCs |
| `haltall` | Halt all debuggable RISCs on all cores |
| `resumeall` | Resume all cores |
| `breakall <addr> [idx]` | Set breakpoint on every core for current RISC |
| `clearall` | Clear all breakpoints on all cores |
| `waitbreak [timeout]` | Poll until any core hits breakpoint, switch focus there |

### Navigation

| Command | Description |
|---|---|
| `core <x>,<y>` | Switch focus to a tile (list cores with no args) |
| `risc <name>` | Switch RISC: brisc / trisc0 / trisc1 / trisc2 / ncrisc |

## Register File Details

### SrcA / SrcB (64 rows x 16 cols x 19 bits, 2 banks each)

Double-buffered: one bank is owned by unpackers (writing new tile data), one by the matrix unit (reading for computation). Data formats: TF32 (19-bit), BF16, FP16, Int8, Int16.

- **SrcB**: directly readable via debug array (`array_id=1`, `bank_id=0|1`)
- **SrcA**: requires instruction injection. `MOVDBGA2D` copies one row to dest, then dest is read via debug array. Slow (~20ms for all 64 rows).

### Dest (1024 rows x 16 cols x 16 bits, or 512 x 16 x 32 bits in FP32)

On Blackhole, directly memory-mapped at `0xFFBD8000` (32KB). Can be read without instruction injection. Supports FP32, FP16, BF16, Int32, Int16, Int8 via `RISC_DEST_ACCESS_CTRL` CFG register.

### LRegs (SFPU SIMD registers, 17 regs x 32 lanes x 32 bits)

| LReg | Type | Access |
|---|---|---|
| 0-7 | Mutable | SFPSTORE injection to dest, read dest |
| 8 | Constant 0.8373 | Known value |
| 9 | Constant 0.0 | Known value |
| 10 | Constant 1.0 | Known value |
| 11-14 | Programmable constants | SFPSTORE injection |
| 15 | lane_id * 2 | Known pattern |
| 16 | SFPLOADMACRO target | SFPSTORE injection |

## Key Register Addresses

All offsets from `DEBUG_REGS_BASE = 0xFFB12000`:

| Register | Address | Purpose |
|---|---|---|
| `RISC_DBG_CNTL_0` | `0xFFB12080` | DR read/write trigger |
| `RISC_DBG_CNTL_1` | `0xFFB12084` | DR write data |
| `RISC_DBG_STATUS_0` | `0xFFB12088` | Read-valid flag (bit 30) |
| `RISC_DBG_STATUS_1` | `0xFFB1208C` | Read result |
| `DBG_BUS_CTRL` | `0xFFB12054` | Debug bus control (for PC reads) |
| `DBG_BUS_RD_DATA` | `0xFFB1205C` | Debug bus read data |
| `DBG_ARRAY_RD_EN` | `0xFFB12060` | Enable register file reads |
| `DBG_ARRAY_RD_CMD` | `0xFFB12064` | Register file read command |
| `DBG_ARRAY_RD_DATA` | `0xFFB1206C` | Register file read data |
| `INSTRN_BUF_CTRL0` | `0xFFB120A0` | Tensix instruction injection control |
| `INSTRN_BUF_CTRL1` | `0xFFB120A4` | Tensix instruction injection data |
| `INSTRN_BUF_STATUS` | `0xFFB120A8` | Instruction injection status |
| `SOFT_RESET_0` | `0xFFB121B0` | Per-RISC soft reset |
| `WALL_CLOCK_L` | `0xFFB121F0` | Cycle counter low |
| `WALL_CLOCK_H` | `0xFFB121F8` | Cycle counter high (snapshot) |
| `DEST_BASE` | `0xFFBD8000` | Direct dest access (32KB) |
| `TENSIX_CREG_READ` | `0xFFB12058` | CFG register read trigger |
| `TENSIX_CREG_RDDATA` | `0xFFB12078` | CFG register read result |
| `FPU_STICKY_BITS` | `0xFFB120B4` | NaN/Inf/denorm flags |

### CNTL_0 Bit Layout

```
[31]    pulse       0->1 triggers access
[19:17] risc_sel    0=BRISC, 1=TRISC0, 2=TRISC1, 3=TRISC2 (2 bits, no NCRISC)
[16]    is_write    1=write DR, 0=read DR
[10:0]  dr_addr     debug register address (0-17)
```

### DR Command Bits (DR(1))

```
bit 0:  HALT             bit 5:  READ_MEMORY
bit 1:  STEP             bit 6:  WRITE_MEMORY
bit 2:  CONTINUE         bit 7:  FLUSH_REGISTERS
bit 3:  READ_REGISTER    bit 8:  FLUSH (write PC)
bit 4:  WRITE_REGISTER   bit 31: DEBUG_MODE (must be ORed)
```

### Debug Bus PC Signals (daisy_sel=7, rd_sel=1)

| RISC | sig_sel | mask |
|---|---|---|
| brisc | 11 | `0x3FFFFFFF` |
| trisc0 | 13 | `0x3FFFFFFF` |
| trisc1 | 15 | `0x3FFFFFFF` |
| trisc2 | 17 | `0x3FFFFFFF` |
| ncrisc | 25 | `0x3FFFFFFF` |

### Soft Reset Bits (`0xFFB121B0`)

| Bit | Core |
|---|---|
| 11 | BRISC |
| 12 | TRISC0 |
| 13 | TRISC1 |
| 14 | TRISC2 |
| 18 | NCRISC |

All 5 in reset: `0x47800`.

### Instruction Encodings (for injection)

```
SFPLOAD(lreg, fmt, addr_mode, dest_addr)  = (0x70 << 24) | (lreg << 20) | (fmt << 16) | (addr_mode << 13) | dest_addr
SFPSTORE(lreg, fmt, addr_mode, dest_addr) = (0x72 << 24) | (lreg << 20) | (fmt << 16) | (addr_mode << 13) | dest_addr
STALLWAIT(stall_res, wait_res)            = (0xA2 << 24) | (stall_res << 15) | wait_res
SETRWC(clr, cr, d, b, a, mask)           = (0x37 << 24) | (clr << 22) | (cr << 18) | (d << 14) | (b << 10) | (a << 6) | mask
MOVDBGA2D(dest_lo, src, am, im, dst)     = (0x09 << 24) | (dest_lo << 23) | (src << 17) | (am << 14) | (im << 12) | dst
```

SFPSTORE fmt: 0=default, 1=FP16A, 2=FP16B, 3=FP32, 4=Int32, 5=Int8.

### Private Data Memory NOC Addresses

Each RISC sees `0xFFB00000` as its own local RAM. The host reads via these NOC addresses:

| RISC | NOC Address | Size |
|---|---|---|
| BRISC | `0xFFB14000` | 8 KB |
| NCRISC | `0xFFB16000` | 8 KB |
| TRISC0 | `0xFFB18000` | 4 KB |
| TRISC1 | `0xFFB1A000` | 4 KB |
| TRISC2 | `0xFFB1C000` | 4 KB |

### Default Reset PCs

| RISC | PC |
|---|---|
| BRISC | `0x00000` |
| TRISC0 | `0x06000` |
| TRISC1 | `0x0A000` |
| TRISC2 | `0x0E000` |
| NCRISC | `0x12000` |

## Multi-Core Debugging Strategy

118 worker cores run concurrently with inter-core NOC coordination. Practical approach:

1. **Pick one core** to focus on. All workers run the same kernel code (different input data).
2. **Set breakpoint at kernel entry** on that core (or all cores with `breakall`).
3. **Dispatch normally.** Firmware runs, calls kernel, hits breakpoint, halts.
4. **Other cores naturally quiesce** at semaphore waits. NOC writes to the halted core's L1 still land (NIU handles them independently of RISC execution).
5. **Step through** the one core. Inspect dest, SrcA/SrcB, LRegs after each compute op.
6. **Resume all** when done. Pipeline picks up where it left off.

Use `scan` for a fast non-intrusive overview of all 118 cores. Use `snapshot` to freeze everything and inspect the full system state.

## Source Files Reference

| File | What |
|---|---|
| `tt-metal/.../blackhole/tensix.h` | All `RISCV_DEBUG_REG_*` defines |
| `tt-exalens/.../baby_risc_debug.py` | DR protocol implementation |
| `tt-exalens/.../blackhole/baby_risc_debug.py` | Blackhole quirks (double-step, PC via debug bus) |
| `tt-exalens/.../debug_tensix.py` | Instruction injection, regfile reads |
| `tt-llk/.../ckernel_debug.h` | `dbg_array_id`, `dbg_bus_cntl_t`, `dbg_array_rd_cmd_t` |
| `tt-llk/.../ckernel_ops.h` | `TT_OP_SFPLOAD`, `TT_OP_SFPSTORE`, `TT_OP_MOVDBGA2D` |
| `tt-isa-documentation/WormholeB0/.../DebugInterface.md` | Full debug register protocol spec |
| `tt-isa-documentation/BlackholeA0/.../README.md` | Blackhole memory map, dest access, PC snapshots |
