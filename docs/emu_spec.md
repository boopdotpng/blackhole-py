# Blackhole Emulator Specification

## 1. Overview

A cycle-approximate Python emulator for the Tenstorrent Blackhole A0 ASIC. The emulator
executes real firmware and kernel binaries (ELF or raw instruction streams from dsl.py)
against a faithful model of the Tensix tile, NoC, DRAM, and host interface. The goal is
correctness, not performance — we need bit-accurate results for every instruction, and
faithful modeling of synchronization, so that programs that work on the emulator also work
on hardware (and vice versa, modulo known HW bugs we choose to model).

### Non-goals (for now)
- Cycle-exact timing (cycle-approximate is fine; relative ordering must be correct)
- Full PCIe/iATU emulation (host writes go directly into the model)
- Ethernet/ERISC tiles (add later)
- L2CPU tiles (add later)
- ARC firmware (stub out reset/init)

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EmulatedDevice                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐       ┌──────────────────┐ │
│  │ TensixTile│  │ TensixTile│ ...  │  DramBank × 8    │ │
│  │  (1,2)    │  │  (1,3)    │      │  (sparse storage)│ │
│  │           │  │           │      └──────────────────┘ │
│  │ ┌───────┐ │  │           │                           │
│  │ │5×RISCV│ │  │           │      ┌──────────────────┐ │
│  │ │Tensix │ │  │           │      │  NocRouter       │ │
│  │ │L1 1536K│ │  │           │      │  (2 networks)    │ │
│  │ │NOC NIU │ │  │           │      └──────────────────┘ │
│  │ └───────┘ │  │           │                           │
│  └──────────┘  └──────────┘       ┌──────────────────┐ │
│                                    │  HostInterface    │ │
│                                    │  (sysmem model)   │ │
│                                    └──────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Top-level classes

| Class | Responsibility |
|---|---|
| `EmulatedDevice` | Owns grid of tiles, DRAM banks, NoC fabric, host interface. Drives the main execution loop. |
| `TensixTile` | One compute tile: 5 RISCV cores, 1 Tensix coprocessor, 1536 KiB L1, 2 NOC NIUs. |
| `RiscVCore` | RV32IM + Zicsr + Zaamo + Zba + Zbb + `.ttinsn`. Fetches/decodes/executes. Has local data RAM (4 or 8 KiB). |
| `TensixCoprocessor` | 3-threaded backend: FPU, SFPU, Unpackers, Packers, Sync, Config, Scalar, Mover. |
| `NocFabric` | Models both NoC0 and NoC1. Routes reads, writes, broadcasts, atomics between tiles. |
| `DramBank` | Sparse storage for one 4 GiB bank. Tracks written regions. |
| `HostInterface` | Models sysmem (hugepages). Host can read/write any tile via TLB-like addressing. |

---

## 3. RISC-V Emulator

### 3.1 ISA support

Implement every instruction present in `dsl.py` plus those found in disassemblies:

**RV32I base:**
ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND,
ADDI, SLTI, SLTIU, XORI, ORI, ANDI, SLLI, SRLI, SRAI,
LB, LBU, LH, LHU, LW, SB, SH, SW,
BEQ, BNE, BLT, BGE, BLTU, BGEU,
LUI, AUIPC, JAL, JALR, FENCE

**M extension:**
MUL, MULH, MULHSU, MULHU, DIV, DIVU, REM, REMU

**Zicsr:**
CSRRW, CSRRS, CSRRC (and immediate variants CSRRWI, CSRRSI, CSRRCI)

**Zaamo (atomics against local L1 only):**
AMOADD.W, AMOXOR.W, AMOOR.W, AMOAND.W, AMOMIN.W, AMOMAX.W, AMOMINU.W, AMOMAXU.W, AMOSWAP.W

**Zba:**
SH1ADD, SH2ADD, SH3ADD

**Zbb:**
MIN, MINU, MAX, MAXU, CTZ, CLZ, CPOP, SEXT.B, SEXT.H, ZEXT.H, REV8, ORC.B, ANDN, ORN, XNOR, ROL, ROR, RORI

**Custom `.ttinsn` encoding:**
When the RISCV executes a `.ttinsn IMM32` instruction, rotate IMM32 right by 2 bits and
push the resulting 32-bit Tensix word into the coprocessor instruction FIFO for the
appropriate thread. Only RISCV T0/T1/T2 can push to their own thread; RISCV B can push
to any thread (T0 at `0xFFE40000`, T1 at `0xFFE50000`, T2 at `0xFFE60000`).

### 3.2 Registers

- 32 × 32-bit integer registers (x0 hardwired to 0)
- PC (32-bit)
- CSRs (see section 7)

### 3.3 Core instances

| Core | Name | Index | Local RAM | NOC access | Can push Tensix |
|---|---|---|---|---|---|
| RISCV B | BRISC | 0 | 8 KiB | NOC1 | Any thread (T0/T1/T2) |
| RISCV NC | NCRISC | 1 | 8 KiB | NOC0 | No |
| RISCV T0 | TRISC0 | 2 | 4 KiB | No | T0 only |
| RISCV T1 | TRISC1 | 3 | 4 KiB | No | T1 only |
| RISCV T2 | TRISC2 | 4 | 4 KiB | No | T2 only |

### 3.4 Local data RAM

Each core has private data RAM at fast-path address `0xFFB00000`:
- BRISC/NCRISC: 8 KiB (`0xFFB00000–0xFFB01FFF`)
- TRISC0/1/2: 4 KiB (`0xFFB00000–0xFFB00FFF`)

Slow-path (NOC-visible) addresses for external access:
| Core | Address | Size |
|---|---|---|
| BRISC | `0xFFB14000` | 8 KiB |
| NCRISC | `0xFFB16000` | 8 KiB |
| TRISC0 | `0xFFB18000` | 4 KiB |
| TRISC1 | `0xFFB1A000` | 4 KiB |
| TRISC2 | `0xFFB1C000` | 4 KiB |

Initialized to zero on reset (real HW takes up to 2048 cycles; emulator can zero
immediately).

### 3.5 L0 data cache

Model as a 4-line, 16-byte-per-line direct-mapped cache with non-coherent behavior:
- Stores to L1 flush the containing line
- Any `fence` or atomic flushes the entire cache
- Optionally model the ~0.8% random flush per access (configurable, default off for
  determinism)

### 3.6 Memory map (per-core view)

Loads and stores from any RISCV core go through a unified address decoder:

```
0x00000000–0x0017FFFF  → L1 scratchpad (1536 KiB, shared by all 5 cores)
0xFFB00000–0xFFB01FFF  → own local data RAM (fast path, 2-cycle equivalent)
0xFFB11000–0xFFB11FFF  → TDMA-RISC registers (see §11)
0xFFB12000–0xFFB12FFF  → tile control/debug/status registers (see §8)
0xFFB13000–0xFFB1314B  → PIC registers (see §12)
0xFFB14000–0xFFB1DFFF  → per-core local data RAM (slow path, any core can access)
0xFFB20000–0xFFB2FFFF  → NOC0 NIU registers
0xFFB30000–0xFFB3FFFF  → NOC1 NIU registers
0xFFB40000–0xFFB7FFFF  → NOC overlay / stream registers (64 streams × 0x1000)
0xFFB80000–0xFFB80023  → MOP config registers (per-thread, write-only)
0xFFBD8000–0xFFBDFFFF  → Dst register file direct access (T0/T1/T2 only, 32 KiB)
0xFFE00000–0xFFE00FFF  → Tensix GPRs (scalar unit DMA registers)
0xFFE40000             → Push Tensix T0 instruction
0xFFE50000             → Push Tensix T1 instruction (BRISC only)
0xFFE60000             → Push Tensix T2 instruction (BRISC only)
0xFFE80000–0xFFE8001F  → PCBuf B→T0 + manual TTSync
0xFFE80020–0xFFE8FFFF  → Tensix semaphores (RISCV-side view)
0xFFE90000             → PCBuf B→T1
0xFFEA0000             → PCBuf B→T2
0xFFEC0000–0xFFEC3FFF  → Mailboxes (4 × 4 KiB)
0xFFEF0000–0xFFEFFFFF  → Tensix backend config registers (Config/ThreadConfig)
```

### 3.7 Execution model

Each RISCV core is modeled as a coroutine or generator that yields after each instruction.
The main loop round-robins across all active cores (across all tiles) and the Tensix
backend. This gives us deterministic interleaving without threads.

```python
class RiscVCore:
    def __init__(self, tile, core_id, ram_size):
        self.x = [0] * 32          # integer register file
        self.pc = 0
        self.csr = {}              # CSR map
        self.local_ram = bytearray(ram_size)
        self.tile = tile           # back-pointer for memory access
        self.halted = False
        self.in_reset = True

    def step(self):
        """Execute one instruction. Returns number of cycles consumed."""
        insn = self.fetch()
        return self.execute(insn)
```

---

## 4. L1 Scratchpad

### 4.1 Storage

```python
class L1Memory:
    def __init__(self):
        self.data = bytearray(0x180000)  # 1536 KiB, zero-initialized
```

### 4.2 Layout (firmware reserves)

```
0x000000  FIRMWARE_BASE / boot vector
0x000004  NOC_ATOMIC_RET_VAL_ADDR
0x00000C  L1_BARRIER
0x000010  ARC_FW_SCRATCH (16 bytes)
0x000020  NOC_INLINE_BASE (64 bytes, workaround for inline write bug)
0x000060  MAILBOX_BASE
0x003270  MAILBOX_END
0x003280  ZEROS_BASE (1024 bytes)
0x003480  LLK_DEBUG_BASE (1024 bytes)
0x003840  BRISC_FIRMWARE_BASE
0x003E40  NCRISC_FIRMWARE_BASE
0x004440  TRISC0_FIRMWARE_BASE
0x004A40  TRISC1_FIRMWARE_BASE
0x005440  TRISC2_FIRMWARE_BASE
0x0086B0  KERNEL_CONFIG_BASE (CB configs, kernel RTAs, XIP code)
0x037000  DATA_BUFFER_SPACE_BASE (CB backing storage starts here)
0x180000  END (top of L1)
```

### 4.3 Atomics

Zaamo instructions (amoadd.w, etc.) operate atomically on L1 addresses. The emulator
serializes all L1 access so atomicity is trivially correct. NOC atomics (see §9.4) also
target L1.

### 4.4 Concurrency

All 5 RISCV cores share the L1. In the emulator's round-robin model, no true data races
exist, but we must still honor `fence` semantics and ensure that store visibility follows
the memory ordering configured in CSR `cfg0`.

---

## 5. Tensix Coprocessor

### 5.1 Architecture overview

The Tensix coprocessor is a 3-threaded (T0/T1/T2) in-order processor with specialized
execution units. Instructions arrive via per-thread instruction FIFOs, pass through MOP
expansion and replay, and execute on the backend.

```
RISCV T0 ──► [Input FIFO 32×32b] ──► [MOP Expander] ──► [Replay Buffer 32×32b]
                                           │                      │
RISCV T1 ──► [Input FIFO 32×32b] ──► [MOP Expander] ──► [Replay Buffer 32×32b]
                                           │                      │
RISCV T2 ──► [Input FIFO 32×32b] ──► [MOP Expander] ──► [Replay Buffer 32×32b]
                                           │                      │
                                     [Wait Gate] ◄── Sync Unit
                                           │
                            ┌──────────────┼──────────────┐
                            ▼              ▼              ▼
                    ┌─────────────┐ ┌───────────┐ ┌────────────┐
                    │ Unpackers   │ │ FPU/SFPU  │ │ Packers    │
                    │ (T0 ctrl)   │ │ (T1 ctrl) │ │ (T2 ctrl)  │
                    └─────────────┘ └───────────┘ └────────────┘
```

### 5.2 Instruction format

All Tensix instructions are 32-bit words: `[opcode:8][params:24]`.

The `.ttinsn IMM32` RISCV instruction encodes a Tensix word as:
`encoded = ((IMM32 << 2) | (IMM32 >> 30)) & 0xFFFFFFFF`

The emulator reverses this on push:
`tensix_word = ((encoded >> 2) | (encoded << 30)) & 0xFFFFFFFF`

### 5.3 Instruction FIFO

Each thread has a 29–32 entry input FIFO. When a RISCV core writes to `0xFFE4xxxx` /
`0xFFE5xxxx` / `0xFFE6xxxx`, the 32-bit value is enqueued. If the FIFO is full, the
RISCV write stalls (the RISCV core blocks until space is available).

```python
class TensixThread:
    def __init__(self, thread_id):
        self.input_fifo = deque(maxlen=32)
        self.mop_cfg = [0] * 9           # MOP config regs
        self.replay_buf = [0] * 32       # replay buffer
```

### 5.4 MOP expander

The `MOP` instruction expands into a configurable sequence of Tensix instructions using
the 9×32-bit MOP config registers at `0xFFB80000 + thread_id * 0x24`.

MOP config layout (per thread, 9 registers):
```
[0] outer_loop_len — number of outer iterations
[1] inner_loop_len — number of inner iterations
[2] outer_loop[0]  — first instruction of outer template
[3] outer_loop[1]  — second instruction
...
```

The MOP instruction `MOP(mop_type, loop_count, zmask)` expands based on the configured
template. `mop_type=0`: execute template once per iteration. `loop_count`: up to 127
iterations of the inner loop.

### 5.5 Replay buffer

32-slot circular buffer per thread. `REPLAY(start_idx, len, execute_while_loading, load_mode)`
replays previously recorded instructions without RISCV involvement.

### 5.6 Backend execution units

Each unit processes instructions from specific threads:

| Unit | Controlled by | Key operations |
|---|---|---|
| Sync | Any thread | STALLWAIT, SEMWAIT, SEMINIT, SEMPOST, SEMGET, ATGETM, ATRELM |
| Unpack (×2) | T0 | UNPACR (L1→SrcA/SrcB), UNPACR_NOP |
| FPU (Matrix) | T1 | MVMUL, ELWADD, ELWMUL, ELWSUB, ZEROACC, ZEROSRC, MOVx2x, etc. |
| SFPU (Vector) | T1 | SFPLOAD/STORE, SFPMAD, SFPMUL, SFPADD, SFPIADD, etc. |
| Scalar (ThCon) | T1 | SETDMAREG, ADDDMAREG, MULDMAREG, DMANOP |
| Pack (×4) | T2 | PACR (Dst→L1) |
| Config | Any thread | WRCFG, RDCFG, SETC16, RMWCIB0-3 |
| Mover (XMOV) | Any thread | Bulk L1 data movement |

---

## 6. Tensix Register Files

### 6.1 SrcA and SrcB

```python
class SrcRegFile:
    def __init__(self):
        # 2 banks × 64 rows × 16 columns × 19 bits
        # Store as 32-bit for convenience; only low 19 bits are meaningful
        self.banks = [[[0]*16 for _ in range(64)] for _ in range(2)]
        self.active_bank = 0        # bank currently owned by FPU
        self.dvalid = [False, False] # data-valid flag per bank
```

Storage format is **shuffled**: `{sign(1), mantissa(10), exponent(8)}` for TF32.
The emulator must convert to/from this format when data enters/leaves SrcA/SrcB.

Supported input formats (set by Config registers):
- TF32: 1+10+8 = 19 bits
- BF16: 1+7+8 = 16 bits (padded to 19)
- FP16: 1+10+5 = 16 bits (padded to 19)
- INT8: 1+8+0 = 9 bits (sign-magnitude)

### 6.2 Dst (Destination register file)

```python
class DstRegFile:
    def __init__(self):
        self.bits = [[0]*16 for _ in range(1024)]  # 1024 rows × 16 × 16-bit
        self.row_valid = [False] * 1024

    # Two logical views:
    # Dst16b: 1024 rows × 16 cols × 16 bits → 16 tiles (8 per half)
    # Dst32b: 512 rows × 16 cols × 32 bits → 8 tiles (4 per half)
    # In 32b mode, logical row R maps to physical rows Adj32(R) and Adj32(R)+8
```

Double-buffered: rows 0–511 = half 0, rows 512–1023 = half 1. MATH writes one half
while PACK reads the other, coordinated by the `MATH_PACK` semaphore.

RISCV T0/T1/T2 can directly access Dst at `0xFFBD8000` (32 KiB window). The format is
controlled by `RISC_DEST_ACCESS_CTRL_SEC[i].fmt`:
- 0=float32, 1=int32, 2=fp16, 3=bf16, 4=int16, 5=int8

### 6.3 LReg (SFPU local registers)

```python
class LRegFile:
    def __init__(self):
        # 17 registers × 32 lanes × 32 bits
        self.data = [[0]*32 for _ in range(17)]
        self._init_constants()

    def _init_constants(self):
        import struct
        def f2u(f): return struct.unpack('<I', struct.pack('<f', f))[0]
        # Read-only constants
        self.data[8]  = [f2u(0.8373)] * 32
        self.data[9]  = [0] * 32               # 0.0
        self.data[10] = [f2u(1.0)] * 32
        self.data[15] = [i * 2 for i in range(32)]  # lane_id * 2
        # LReg[11] initialized to -1.0 by firmware via SFPLOADI + SFPCONFIG
        self.data[11] = [f2u(-1.0)] * 32
```

- LReg[0–7]: general-purpose, read/write
- LReg[8–10]: read-only hardware constants
- LReg[11–14]: programmable via SFPCONFIG (write LReg[0] lane 0 → target)
- LReg[15]: read-only lane IDs (lane i = i*2)
- LReg[16]: SFPLOADMACRO scratch

### 6.4 DMA registers (Scalar Unit)

```python
class ScalarUnit:
    def __init__(self):
        # 64 × 16-bit DMA registers per thread, 3 threads
        self.dma_regs = [[0]*64 for _ in range(3)]
```

Accessed via:
- `SETDMAREG(reg_idx, value)`: load immediate
- `ADDDMAREG(dst, src_a, src_b)`: integer add
- `MULDMAREG(dst, src_a, src_b)`: integer multiply

Also visible at `0xFFE00000` (Tensix GPR base).

---

## 7. CSR Registers

### 7.1 Standard CSRs

| CSR | Address | Notes |
|---|---|---|
| `mcycle` | 0xB00 | Cycle counter low (read-only) |
| `mcycleh` | 0xB80 | Cycle counter high (read-only) |
| `minstret` | 0xB02 | Instructions retired low |
| `minstreth` | 0xB82 | Instructions retired high |

### 7.2 Custom CSRs

| CSR | Address | Description |
|---|---|---|
| `cfg0` | 0x7C0 | Core configuration (see below) |
| `tt_cfg_qstatus` | 0xBC0 | Tensix frontend queue status / SFPU CC status |
| `tt_cfg_bstatus` | 0xBC1 | Tensix backend busy status |
| `tt_cfg_sstatus0–7` | 0xBC2–0xBC9 | Stream status (T0/T1/T2) or scratch (B/NC) |
| `intp_restore_pc` | 0xBCA | Interrupt return PC |

### 7.3 `cfg0` bit fields

| Bit | Name | Default | Effect |
|---|---|---|---|
| 0 | DisLdBufByp | 0 | Load waits for store queue empty |
| 1 | DisBp | 0 | Disable branch predictor (no effect in emulator) |
| 3 | DisLowCash | 0 | Disable L0 data cache |
| 18 | DisTriscCache | 0 | Disable `.ttinsn` fusion (no effect in emulator) |
| 24 | DisLowCachePeriodicFlush | 0 | Disable random L0 flush |
| 30 | EnBFloat | 0 | BF16 mode for Zfh instructions |
| 31 | EnBFloatRTNE | 0 | BF16 rounding mode (0=RTZ, 1=RTNE) |

---

## 8. Tile Control / Debug Registers

Located at `0xFFB12000–0xFFB12FFF`:

| Address | Register | Emulator behavior |
|---|---|---|
| `0xFFB121B0` | SOFT_RESET_0 | Controls which cores are in/out of reset (see §14) |
| `0xFFB121F0` | WALL_CLOCK_0 | Low 32 bits of 64-bit cycle counter |
| `0xFFB121F4` | WALL_CLOCK_1 | High 32 bits (live) |
| `0xFFB121F8` | WALL_CLOCK_1_AT | Latched high bits (snapshot on read of WALL_CLOCK_0) |
| `0xFFB12228` | TRISC0_RESET_PC | Reset PC for T0 |
| `0xFFB1222C` | TRISC1_RESET_PC | Reset PC for T1 |
| `0xFFB12230` | TRISC2_RESET_PC | Reset PC for T2 |
| `0xFFB12234` | TRISC_RESET_PC_OVERRIDE | 3-bit mask: enable custom reset PC per TRISC |
| `0xFFB12238` | NCRISC_RESET_PC | Reset PC for NCRISC |
| `0xFFB1223C` | NCRISC_RESET_PC_OVERRIDE | 1-bit enable |
| `0xFFB12240` | DEST_CG_CTRL | Dst clock gating (model as no-op) |
| `0xFFB12244` | CG_CTRL_EN | Clock gating enable (model as no-op) |
| `0xFFB120B4` | FPU_STICKY_BITS | NaN/Inf/denorm sticky flags |

### Soft reset register (`0xFFB121B0`)

| Bit | Target |
|---|---|
| 0,1,7 | Unpackers |
| 2–5 | Packers 0–3 |
| 6 | Mover |
| 8 | TDMA-RISC |
| 9 | Scalar Unit + THCON |
| 10 | FPU + SFPU + SrcA |
| 11 | RISCV B |
| 12 | RISCV T0 |
| 13 | RISCV T1 |
| 14 | RISCV T2 |
| 15–17 | SrcA/SrcB ownership, Packer-Dst |
| 18 | RISCV NC |
| 19–22 | SrcA data columns |
| 23 | Auto TTSync |

Firmware boots with all bits set (`0x47800` = B/T0/T1/T2/NC in reset). BRISC is released
first, then it releases the others.

---

## 9. NOC Emulation

### 9.1 Fabric model

```python
class NocFabric:
    def __init__(self, device):
        self.device = device
        # pending_transactions: list of in-flight NOC ops
        self.pending = []

    def submit_write(self, src_tile, noc_id, targ_xy, targ_addr, data, flags):
        """Unicast or multicast write."""
        ...

    def submit_read(self, src_tile, noc_id, targ_xy, targ_addr, ret_addr, length):
        """Read request: data returned to ret_addr in src_tile's L1."""
        ...

    def submit_atomic(self, src_tile, noc_id, targ_xy, targ_addr, op, operand):
        """Atomic operation on target tile's L1."""
        ...

    def tick(self):
        """Process pending transactions. Move data between tiles."""
        ...
```

Two independent networks (NOC0 and NOC1). Each tile has 4 command buffer slots per NIU.

### 9.2 NIU register model

Per-NOC registers at `0xFFB20000` (NOC0) / `0xFFB30000` (NOC1):

| Offset | Register | Model |
|---|---|---|
| `+0x00` | NOC_TARG_ADDR_LO | Written by RISCV, consumed on CMD_CTRL |
| `+0x04` | NOC_TARG_ADDR_MID | Target address high bits |
| `+0x08` | NOC_TARG_ADDR_HI | Target X/Y: bits [5:0]=X, [11:6]=Y |
| `+0x0C` | NOC_RET_ADDR_LO | Return/source address low |
| `+0x10` | NOC_RET_ADDR_MID | Return address high |
| `+0x14` | NOC_RET_ADDR_HI | Return X/Y |
| `+0x18` | NOC_PACKET_TAG | Transaction ID |
| `+0x1C` | NOC_CTRL | Command type and flags (see §9.3) |
| `+0x20` | NOC_AT_LEN_BE | Length / byte-enable / atomic opcode |
| `+0x28` | NOC_AT_DATA | Inline data / atomic operand |
| `+0x2C` | NOC_BRCST_EXCLUDE | Broadcast exclusion mask |
| `+0x40` | NOC_CMD_CTRL | Write 1 to trigger; cleared when command accepted |
| `+0x44` | NOC_NODE_ID | This tile's X/Y (read-only, set at init) |

Command buffer stride: `0x800` (4 initiators per NIU at offsets 0, 0x800, 0x1000, 0x1800).

### 9.3 NOC_CTRL flags

```python
NOC_CMD_CPY            = 0 << 0   # copy (vs atomic)
NOC_CMD_AT             = 1 << 0   # atomic
NOC_CMD_RD             = 0 << 1   # read
NOC_CMD_WR             = 1 << 1   # write
NOC_CMD_WR_BE          = 1 << 2   # byte-enable write
NOC_CMD_WR_INLINE      = 1 << 3   # inline data (BH: broken for L1, ok for MMIO)
NOC_CMD_RESP_MARKED    = 1 << 4   # request ack/response
NOC_CMD_BRCST_PACKET   = 1 << 5   # multicast
NOC_CMD_VC_LINKED      = 1 << 6   # linked VC (multi-packet transaction)
NOC_CMD_VC_STATIC      = 1 << 7   # software-controlled VC
NOC_CMD_BRCST_XY       = 1 << 16  # broadcast direction (0=X-major, 1=Y-major)
NOC_CMD_BRCST_SRC_INCLUDE = 1 << 17  # include source in broadcast
```

### 9.4 Address encoding

```python
def noc_unicast_addr(x, y, local_addr):
    """Encode 40-bit NOC address for unicast."""
    return (y << 36) | (x << 32) | (local_addr & 0xFFFFFFFF)

def noc_multicast_addr(x_start, y_start, x_end, y_end, local_addr):
    """Encode multicast rectangle."""
    return (y_start << 36) | (x_start << 32) | (y_end << 24) | (x_end << 18) | local_addr
```

### 9.5 NOC completion tracking

NIU counters at `NIU_BASE + 0x200`:
- `NIU_MST_REQS_OUTSTANDING_ID(i)`: incremented on submit, decremented on response
- `NIU_MST_WR_ACK_RECEIVED`: total write acks received
- `NIU_MST_RD_RESP_RECEIVED`: total read responses received

Firmware polls these to implement `noc_async_write_barrier()` and
`noc_async_read_barrier()`.

### 9.6 NOC configuration registers

| Offset | Register | Key bits |
|---|---|---|
| `+0x100` | NIU_CFG_0 | bit 14: coordinate translation enable |
| `+0x104` | ROUTER_CFG_0 | reserved |
| `+0x108` | ROUTER_CFG_1 | broadcast column opt-out mask |
| `+0x110` | ROUTER_CFG_3 | broadcast row opt-out mask |
| `+0x118..0x144` | translate tables | X/Y coordinate translation (5-bit entries, packed) |
| `+0x148` | NOC_ID_LOGICAL | this tile's logical X/Y |

### 9.7 NOC atomics

Supported against L1 of Tensix tiles only:
- Atomic increment (with width mask)
- Compare-and-swap
- Swap (unconditional write, returns old)
- AMOADD, AMOXOR, AMOOR, AMOAND, AMOMIN, AMOMAX, AMOMINU, AMOMAXU
- Parallel accumulation: fp32×4, fp16×8, bf16×8, u32×4, u8×16 (128-bit)

### 9.8 Known hardware bugs to model

- **Inline write to L1 is broken** on Blackhole A0. `NOC_CMD_WR_INLINE` must only target
  MMIO addresses, not L1. Firmware works around this by writing data to
  `MEM_L1_INLINE_BASE` (0x20) and issuing a normal write. The emulator should reject or
  warn on inline writes to L1 addresses.

---

## 10. DRAM Model

### 10.1 Architecture

8 banks × 4 GiB = 32 GiB total. Each bank is fronted by 3 DRAM tiles on the NoC (all 3
expose the same data).

NOC coordinates of DRAM tiles:
- West banks 0–3: X=0, various Y
- East banks 4–7: X=9, various Y

### 10.2 Sparse storage

Do NOT allocate 32 GiB. Use a sparse dict-of-pages model:

```python
class DramBank:
    PAGE_SIZE = 4096  # 4 KiB pages

    def __init__(self, bank_id):
        self.bank_id = bank_id
        self.pages = {}  # page_number → bytearray(PAGE_SIZE)

    def read(self, offset, length):
        result = bytearray(length)
        for i in range(length):
            addr = offset + i
            page = addr // self.PAGE_SIZE
            off = addr % self.PAGE_SIZE
            if page in self.pages:
                result[i] = self.pages[page][off]
            # else: 0 (uninitialized)
        return result

    def write(self, offset, data):
        for i, byte in enumerate(data):
            addr = offset + i
            page = addr // self.PAGE_SIZE
            off = addr % self.PAGE_SIZE
            if page not in self.pages:
                self.pages[page] = bytearray(self.PAGE_SIZE)
            self.pages[page][off] = byte
```

### 10.3 Interleaved addressing

For interleaved DRAM buffers: tile N goes to bank `N % num_banks` at offset
`(N // num_banks) * tile_size + base_offset`.

### 10.4 DRAM tile NOC handling

When a NOC read/write targets a DRAM tile (identified by X/Y coordinate), the fabric
routes to the appropriate `DramBank`. The local address within the DRAM tile maps to the
GDDR offset.

---

## 11. Tensix Instruction Emulation

### 11.1 Complete instruction table

Every instruction from `dsl.py` with opcode and key semantics:

#### Flow control
| Opcode | Mnemonic | Semantics |
|---|---|---|
| 0x01 | MOP | Expand macro-operation from MOP_CFG |
| 0x02 | NOP | No operation |
| 0x04 | REPLAY | Replay `len` instructions starting at `start_idx` in replay buffer |

#### Sync unit
| Opcode | Mnemonic | Semantics |
|---|---|---|
| 0xA0 | ATGETM | Acquire mutex (spin if held) |
| 0xA1 | ATRELM | Release mutex |
| 0xA2 | STALLWAIT | Stall units in `block_mask` until all `condition_mask` bits clear |
| 0xA3 | SEMINIT | Initialize semaphore: `sem[sel] = {max, init_value}` |
| 0xA4 | SEMPOST | `sem[sel].value++` (saturate at max) |
| 0xA5 | SEMGET | `sem[sel].value--` (saturate at 0) |
| 0xA6 | SEMWAIT | Stall units in `block_mask` until semaphore condition met |

#### Configuration unit
| Opcode | Mnemonic | Semantics |
|---|---|---|
| 0xB0 | WRCFG | Write GPR value to Config register (32 or 128 bit) |
| 0xB1 | RDCFG | Read Config register to GPR |
| 0xB2 | SETC16 | Write 16-bit immediate to ThreadConfig register |
| 0xB3–0xB6 | RMWCIB0–3 | Read-modify-write byte in Config (mask + data) |

#### FPU (matrix unit)
| Opcode | Mnemonic | Semantics | Latency |
|---|---|---|---|
| 0x10 | ZEROACC | Clear Dst row_valid flags | 1 |
| 0x11 | ZEROSRC | Zero or -inf fill SrcA/SrcB | 1 |
| 0x13 | MOVB2D | SrcB → Dst | 4 |
| 0x16 | TRNSPSRCB | Transpose SrcB rows 16–31 | 1 |
| 0x26 | MVMUL | `Dst += SrcB @ SrcA` (8×16 matmul) | 5 |
| 0x28 | ELWADD | `Dst [+=] SrcA + SrcB` | 5 |
| 0x33 | GMPOOL | Global max pool | 5 |
| 0x36 | CLEARDVALID | Clear data-valid flags | 1 |
| 0x0A | MOVD2B | Dst → SrcB | 3 |
| 0x37 | SETRWC | Set read/write counters | 1 |
| 0x38 | INCRWC | Increment read/write counters | 1 |

Dead on Blackhole (implement as NOP): 0x22 CONV3S1, 0x23 CONV3S2, 0x24 MFCONV3S1,
0x25 APOOL3S1, 0x32 APOOL3S2, 0x31 MPOOL3S1, 0x2A MPOOL3S2.

#### Unpack
| Opcode | Mnemonic | Semantics |
|---|---|---|
| 0x42 | UNPACR | Unpack L1 data → SrcA (sel=0) or SrcB (sel=1) |
| 0x43 | UNPACR_NOP | NOP with side effects: clear stream counters, set dvalid |

#### Pack
| Opcode | Mnemonic | Semantics |
|---|---|---|
| 0x41 | PACR | Pack Dst data → L1 (16 rows per call) |

PACR fields: `AddrMode(1)`, `ZeroWrite(1)`, `CfgContext(3)`, `AddrCntContext(2)`,
`OvrdThreadId(2)`, `Concat(1)`, `Flush(1)`, `Last(1)`, `PackSel(1)`, `AddrSel(1)`.

#### SFPU (vector unit)

Data movement:
| Opcode | Mnemonic | Semantics |
|---|---|---|
| 0x70 | SFPLOAD | Load 32 elements from Dst → LReg |
| 0x71 | SFPLOADI | Load BF16/FP16/int immediate → LReg |
| 0x72 | SFPSTORE | Store LReg → Dst |
| 0x93 | SFPLOADMACRO | Pipelined load + 4 ops |

Arithmetic (MAD sub-unit, 2-cycle latency):
| Opcode | Mnemonic | Operation |
|---|---|---|
| 0x84 | SFPMAD | VD = ±VA * ±VB ± VC (FMA) |
| 0x85 | SFPADD | VD = ±VB ± VC |
| 0x86 | SFPMUL | VD = VA * ±VB |
| 0x74 | SFPMULI | VD *= BF16ToFP32(imm16) |
| 0x75 | SFPADDI | VD += BF16ToFP32(imm16) |
| 0x95 | SFPLUTFP32 | 3-piece FP32 LUT |

Simple sub-unit (1-cycle latency):
| Opcode | Mnemonic | Operation |
|---|---|---|
| 0x76 | SFPDIVP2 | Multiply/divide by power of 2 |
| 0x77 | SFPEXEXP | Extract FP32 exponent |
| 0x78 | SFPEXMAN | Extract FP32 mantissa |
| 0x79 | SFPIADD | Integer add (VC ± VD or VC ± imm11) |
| 0x7A | SFPSHFT | Bit shift |
| 0x7B | SFPSETCC | Set per-lane condition flags |
| 0x7C | SFPMOV | Move/negate/PRNG |
| 0x7D | SFPABS | Absolute value |
| 0x7E | SFPAND | Bitwise AND |
| 0x80 | SFPNOT | Bitwise NOT |
| 0x82 | SFPSETEXP | Set FP32 exponent |
| 0x89 | SFPSETSGN | Set/clear/copy sign |
| 0x8A | SFPENCC | Enable/disable conditional execution |
| 0x8B | SFPCOMPC | Complement condition flags ("else") |
| 0x87 | SFPPUSHC | Push condition flags |
| 0x88 | SFPPOPC | Pop condition flags |
| 0x8F | SFPNOP | SFPU no-op |
| 0x90 | SFPCAST | Type cast (SignMag32 ↔ FP32/INT32) |
| 0x91 | SFPCONFIG | Write LReg[0] lane 0 → constant register |
| 0x92 | SFPSWAP | Min/max swap (2 cycles) |
| 0x94 | SFPSHFT2 | Two-source shift |
| 0x99 | SFPARECIP | Approximate 1/x (7-bit, Blackhole-new) |
| 0x8E | SFPSTOCHRND | Stochastic rounding: FP32→BF16/FP16/INT8/etc. |

SFPU conditional execution:
- Each lane has a `UseLaneFlagsForLaneEnable` flag
- SFPENCC enables/disables per-lane predication
- SFPSETCC sets flags based on comparisons
- SFPPUSHC/SFPPOPC: 4-deep condition flag stack (enables SIMT if/else/endif)
- SFPCOMPC: flips flags ("else" branch)

#### Scalar unit (ThCon/DMA)
| Opcode | Mnemonic | Semantics |
|---|---|---|
| 0x45 | SETDMAREG | Load 16-bit immediate → DMA register |
| 0x58 | ADDDMAREG | DMA[dst] = DMA[src_a] + DMA[src_b] |
| 0x5A | MULDMAREG | DMA[dst] = DMA[src_a] * DMA[src_b] |
| 0x60 | DMANOP | DMA no-op |

#### ADC (address counter) unit
| Opcode | Mnemonic | Semantics |
|---|---|---|
| 0x51 | SETADCXY | Set X/Y address counter values |
| 0x54 | SETADCZW | Set Z/W address counter values |
| 0x55 | INCADCZW | Increment Z/W counters |
| 0x5E | SETADCXX | Set X start/end for address generation |

#### Read/write counters
| Opcode | Mnemonic | Semantics |
|---|---|---|
| 0x37 | SETRWC | Set RWC values for SrcA/SrcB/Dst/CR |
| 0x38 | INCRWC | Increment RWC values |

---

## 12. Semaphore & Synchronization Model

### 12.1 Tensix hardware semaphores

```python
class TensixSemaphore:
    def __init__(self):
        self.value = 0  # 4-bit (0–15)
        self.max = 0    # 4-bit

    def post(self):
        if self.value < self.max:
            self.value += 1

    def get(self):
        if self.value > 0:
            self.value -= 1

    def check_wait(self, cond):
        # cond=0: value == 0
        # cond=1: value >= max
        if cond == 0:
            return self.value == 0
        elif cond == 1:
            return self.value >= self.max
```

8 semaphores per tile, shared across all 3 Tensix threads.

RISCV access via MMIO at `0xFFE80020 + sem_idx * 4`:
- Read → returns current value
- Write even value → SEMPOST
- Write odd value → SEMGET

### 12.2 STALLWAIT

```python
def stallwait(self, block_mask, condition_mask):
    """
    Stall execution units in block_mask until ALL condition_mask bits are 0.

    block_mask bits (B0-B8):
      B0=Misc/Scalar/Pack/Unpack, B1=Sync, B2=Pack, B3=Unpack,
      B4=Mover, B5=Scalar, B6=FPU, B7=Config, B8=SFPU

    condition_mask bits (C0-C12):
      C0=Scalar outstanding, C1=Unpack0 busy, C2=Unpack1 busy,
      C3=Pack busy, C4=FPU busy, C5/C6=SrcA/B not owned by Unpack,
      C7/C8=SrcA/B not owned by FPU, C9=Mover busy, C10=RISCV pending,
      C11=SFPU busy, C12=Config busy
    """
    while self._check_conditions(condition_mask):
        yield  # stall for one cycle
```

### 12.3 SEMWAIT

```python
def semwait(self, block_mask, sem_mask, condition):
    """
    Stall units in block_mask until semaphore condition met.
    sem_mask: bitmask of which semaphores to check
    condition: 0=any selected sem has value==0, 1=any selected sem has value>=max
    """
    while self._check_sem_condition(sem_mask, condition):
        yield
```

### 12.4 Mutexes

4 hardware mutexes (indices 0, 2, 3, 4):
- `ATGETM(idx)`: spin until mutex is free, then acquire
- `ATRELM(idx)`: release

### 12.5 Firmware semaphore protocol

Three well-known semaphores initialized at boot:
- Sem 0 (`MATH_PACK`): max=1 (or 2 for SyncHalf), init=0
- Sem 1 (`UNPACK_TO_DEST`): max=1, init=0
- Sem 2 (`MATH_DONE`): max=1, init=0

**Dst double-buffer protocol:**
```
MATH (T1):                        PACK (T2):
  tile_regs_acquire()               tile_regs_wait()
    → SEMWAIT(value < max)            → SEMWAIT(value > 0)
  ... compute into Dst half ...     ... pack from Dst half ...
  tile_regs_commit()                tile_regs_release()
    → STALLWAIT(FPU+SFPU drain)       → ZEROACC(half)
    → SEMPOST(MATH_PACK)              → SEMGET(MATH_PACK)
    → flip Dst half                   → flip Dst half
```

### 12.6 Software semaphores (NOC-based)

Used for inter-core synchronization (e.g., matmul multicast):
- Semaphore is a 32-bit word in L1 at a known address
- `noc_semaphore_wait(ptr, val)`: spin until `*ptr == val`
- `noc_semaphore_set(ptr, val)`: `*ptr = val`
- `noc_semaphore_inc(noc_addr, incr)`: NOC atomic increment to remote tile's L1

### 12.7 BRISC ↔ TRISC sync protocol

Uses `RUN_SYNC_MSG` in mailbox area:
```
RUN_SYNC_MSG_INIT             — all cores idle
RUN_SYNC_MSG_GO               — BRISC signals "start kernel"
RUN_SYNC_MSG_DONE             — each core signals "kernel done"
RUN_SYNC_MSG_INIT_SYNC_REGS  — T0 signals "CB semaphores zeroed"
```

---

## 13. Circular Buffer Emulation

### 13.1 CB structure

```python
class CircularBuffer:
    def __init__(self, cb_id, base_addr, size, num_pages, page_size):
        self.cb_id = cb_id
        self.base_addr = base_addr   # L1 byte address of backing storage
        self.size = size             # total bytes (page_size * num_pages)
        self.num_pages = num_pages   # depth (number of tiles)
        self.page_size = page_size   # bytes per tile

        # Producer/consumer pointers (in stream registers)
        self.tiles_received = 0      # producer has written this many tiles
        self.tiles_acked = 0         # consumer has consumed this many tiles
```

### 13.2 CB ↔ Stream mapping

CB indices map to hardware streams:
```
CB 0–7   (inputs)        → streams 8–15    (unpack reads)
CB 8–15  (params)        → streams 16–23   (unpack reads)
CB 16–23 (outputs)       → streams 24–31   (pack writes)
CB 24–31 (intermediates) → streams 32–39   (both)
```

Stream ID = 8 + CB index.

### 13.3 CB config in L1

Each CB is described by 4 × u32 = 16 bytes in L1 at
`KERNEL_CONFIG_BASE + local_cb_offset + cb_id * 16`:

```c
struct CBConfig {
    uint32_t fifo_addr;       // L1 base address
    uint32_t fifo_size;       // total size in bytes
    uint32_t fifo_num_pages;  // number of pages (tiles)
    uint32_t fifo_page_size;  // page size in bytes
};
```

### 13.4 CB synchronization via stream registers

The `tiles_received` and `tiles_acked` counters live in NOC overlay stream registers:
- `tiles_received`: `STREAM_REG(stream, STREAM_REMOTE_DEST_BUF_SIZE_REG_INDEX)`
- `tiles_acked`: `STREAM_REG(stream, STREAM_REMOTE_DEST_BUF_START_REG_INDEX)`

Stream register base: `0xFFB40000 + stream_id * 0x1000`.

### 13.5 CB API semantics

**Producer (e.g., unpacker writing input tiles):**
```python
def cb_reserve_back(cb, num_tiles):
    """Block until num_tiles free slots available."""
    while (cb.tiles_received - cb.tiles_acked) + num_tiles > cb.num_pages:
        yield  # stall

def cb_push_back(cb, num_tiles):
    """Signal that num_tiles have been written."""
    cb.tiles_received += num_tiles
```

**Consumer (e.g., math reading input tiles):**
```python
def cb_wait_front(cb, num_tiles):
    """Block until num_tiles are available to read."""
    while (cb.tiles_received - cb.tiles_acked) < num_tiles:
        yield  # stall

def cb_pop_front(cb, num_tiles):
    """Signal that num_tiles have been consumed."""
    cb.tiles_acked += num_tiles
```

### 13.6 Data layout in L1

CB data starts at `DATA_BUFFER_SPACE_BASE = 0x037000`. Tiles are stored contiguously
within each CB's allocation. The write pointer wraps: `write_addr = base + (tiles_received
% num_pages) * page_size`.

### 13.7 Tile format

Tiles are 32×32 elements, arranged as 4 faces of 16×16 in face-major order:
`(face_r, face_c, row, col)` where face_r/face_c ∈ {0,1}.

Tile sizes by data type:
| Dtype | BPE | Tile bytes |
|---|---|---|
| Float32 / Int32 / UInt32 | 4 | 4096 |
| Float16 / Float16_b / UInt16 | 2 | 2048 |
| Int8 / UInt8 | 1 | 1024 |

---

## 14. Unpack Pipeline Model

### 14.1 UNPACR instruction

`UNPACR(block_sel, ...)`:
- `block_sel=0`: unpack to SrcA (Unpacker 0)
- `block_sel=1`: unpack to SrcB (Unpacker 1)

Reads tile data from L1 (at address determined by CB config + ADC counters), converts
format, and loads into the appropriate SrcA/SrcB bank.

### 14.2 Format conversion

On-the-fly conversion during unpack:
- BFP8 → BF16 (expand shared exponent)
- FP32 → TF32 (truncate mantissa to 10 bits)
- FP16 → internal 19-bit format
- BF16 → internal 19-bit format
- Controlled by `ALU_FORMAT_SPEC_REG0_SrcA` / `SrcB` config fields

### 14.3 Special modes

- **XY transpose** (`haloize_mode=1`, Unpacker 0 only): swap low 4 row bits with column index
- **Tilize** (`tileize_mode=1`): gather row-major L1 data into tiled SrcA
- **Unpack-to-Dst** (`UnpackToDst=1`): write directly to Dst instead of SrcA

### 14.4 Ownership protocol

SrcA/SrcB banks are double-buffered. Ownership alternates between Unpackers and FPU:
- `SETDVALID`: Unpacker signals "bank ready for FPU"
- `CLEARDVALID`: FPU signals "bank consumed, Unpacker can refill"

---

## 15. Pack Pipeline Model

### 15.1 PACR instruction

Reads 16 rows from Dst and writes to L1. Multiple PACR calls pack a full tile
(4 faces × 16 rows = 4 PACR calls per 32×32 tile).

### 15.2 Pipeline stages

```
Dst → Edge Mask → Format Conv → ReLU → Exp Threshold → Late Conv → L1
```

- **Edge masking**: 16-bit column mask, replace masked with 0 or -inf
- **ReLU**: 4 modes (none, zero, min-threshold, max-threshold) — free in HW
- **Format conversion**: e.g., FP32 Dst → BF16 L1, with optional shared exponent (BFP)
- **L1 accumulation** (`PACKER_L1_ACC`): `L1[addr] += packed_value` instead of overwrite

### 15.3 Known bugs

**Packer L1 accumulation + IEEE Float16**: produces NaN (0x7fff/0xffff) when combining
FPU matmul + L1 acc + IEEE FP16 + multiple sub-blocks. BF16 and FP32 work correctly.
The emulator should model this bug (configurable flag to enable/disable).

---

## 16. FPU Computation Model

### 16.1 MVMUL (matrix-vector multiply)

```python
def mvmul(self, fidelity_phase=0):
    """Dst += SrcB @ SrcA for one 8×16 face."""
    # SrcA: 8 rows (selected by RWC_A) × 16 cols
    # SrcB: 16 rows × 16 cols
    # Result: 8 rows × 16 cols accumulated into Dst

    for dst_row in range(8):
        for dst_col in range(16):
            acc = self.read_dst(dst_row_addr + dst_row, dst_col)
            for k in range(16):
                a = self.decode_src(self.srca[row_a + dst_row][k], fidelity_phase, 'a')
                b = self.decode_src(self.srcb[k][dst_col], fidelity_phase, 'b')
                acc += a * b
            self.write_dst(dst_row_addr + dst_row, dst_col, acc)
```

### 16.2 Fidelity phases

The FPU multiplier is bandwidth-limited: 5 bits of SrcA mantissa × 7 bits of SrcB
mantissa per phase:

| Phase | SrcA bits | SrcB bits |
|---|---|---|
| 0 (LoFi) | [9:5] | [9:3] |
| 1 (HiFi2) | [4:0] | [9:3] |
| 2 (HiFi3) | [9:5] | [2:0]+pad |
| 3 (HiFi4) | [4:0] | [2:0]+pad |

**LLK convention**: in0 ("A" matrix) → SrcB (7-bit path), in1 ("B" matrix) → SrcA
(5-bit path). This is swapped from the mathematical convention.

For exact BF16: HiFi2 is sufficient (7+7 ≤ 14 mantissa bits).
For exact FP16/TF32: HiFi4 required.

### 16.3 Accumulation modes

- **Dst16b**: accumulate in BF16/FP16 (16 tiles capacity)
- **Dst32b**: accumulate in FP32 (8 tiles capacity, ~26% throughput reduction)
- Controlled by `ALU_ACC_CTRL_Fp32_enabled` config bit

### 16.4 ELWADD, ELWMUL, ELWSUB

Element-wise operations on aligned SrcA/SrcB rows → Dst. Same face structure as MVMUL.

---

## 17. SFPU Computation Model

### 17.1 SFPLOAD / SFPSTORE addressing

```python
def sfp_effective_addr(base_imm, dst_offset):
    """Compute which Dst rows/cols are accessed."""
    addr = base_imm + dst_offset
    for lane in range(32):
        row = (addr & ~3) + (lane // 8)   # 4 consecutive Dst rows
        col = (lane & 7) * 2 + (addr & 2) # 8 even or 8 odd columns
        yield lane, row, col
```

One SFPLOAD accesses half the columns of 4 Dst rows → 32 elements into one LReg.
Full 32×32 tile (64 Dst rows) needs 16 SFPLOAD/SFPSTORE pairs for even columns, or 32
for all columns.

### 17.2 Conditional execution

```python
class SFPUCondState:
    def __init__(self):
        self.enabled = False
        self.lane_flags = [True] * 32   # per-lane enable
        self.flag_stack = []            # up to 4 deep

    def setcc(self, lreg, comparison):
        """Set flags based on comparison of LReg values."""
        for lane in range(32):
            self.lane_flags[lane] = compare(lreg[lane], comparison)

    def pushc(self):
        self.flag_stack.append(self.lane_flags[:])

    def popc(self):
        self.lane_flags = self.flag_stack.pop()

    def compc(self):
        """Complement: flip all flags (else branch)."""
        self.lane_flags = [not f for f in self.lane_flags]
```

When conditional execution is enabled (`SFPENCC`), only lanes with `flag=True` execute
the instruction; other lanes retain their previous value.

### 17.3 PRNG

32-bit LFSR per lane, used by `SFPMOV` (mode=PRNG) and `SFPSTOCHRND` for stochastic
rounding. Seed initialized by hardware; emulator should use a deterministic seed.

---

## 18. Tensix Backend Configuration

### 18.1 Config registers

```python
class TensixConfig:
    def __init__(self):
        # Two ping-pong banks of config state
        self.config = [bytearray(CFG_STATE_SIZE * 4) for _ in range(2)]
        # Plus dual-write bank (writes go to both)
        self.config_dual = bytearray(CFG_STATE_SIZE * 4)
        # Per-thread config (3 threads)
        self.thread_config = [[0] * THD_STATE_SIZE for _ in range(3)]
        # Active bank per thread
        self.cfg_state_id = [0, 0, 0]
```

RISCV access at `0xFFEF0000`:
- Writes to Config are auto-synchronized with Tensix pipeline (Auto TTSync)
- ThreadConfig only writable via `SETC16` Tensix instruction

### 18.2 Key config fields

| Field | Purpose |
|---|---|
| `ALU_ACC_CTRL_Fp32_enabled` | FP32 vs FP16 accumulation in Dst |
| `ALU_FORMAT_SPEC_REG0_SrcA/SrcB` | Input data format |
| `DEST_REGW_BASE_Base` | Base row offset in Dst |
| `DEST_ACCESS_CFG_remap_addrs` | Dst address remapping mode |
| `CFG_STATE_ID_StateID` | Active Config bank (ThreadConfig) |
| `FIDELITY_BASE_Phase` | Starting fidelity phase (ThreadConfig) |
| `RISC_DEST_ACCESS_CTRL_SEC[i].fmt` | Dst RISCV access format |

---

## 19. NOC Overlay / Stream Registers

64 streams per tile, base `0xFFB40000`, stride `0x1000` per stream.

Used primarily for:
1. CB tile counters (`tiles_received`, `tiles_acked`)
2. Dispatch message delivery (stream 48)
3. DMA coprocessor commands (firmware-managed)

The emulator needs to model the stream registers that CB synchronization reads/writes,
and stream 48 for dispatch signaling. Full stream overlay DMA is a stretch goal.

---

## 20. Host Interface

### 20.1 Sysmem model

```python
class HostInterface:
    def __init__(self, sysmem_size=96 * 1024 * 1024):
        self.sysmem = bytearray(sysmem_size)  # host hugepage memory

    def write_to_device(self, tile_xy, local_addr, data):
        """Host writes to a tile's L1 or MMIO (via TLB)."""
        ...

    def read_from_device(self, tile_xy, local_addr, length):
        """Host reads from a tile (slow, MMIO path)."""
        ...
```

### 20.2 Device-to-host writes

When a tile writes to `4ULL << 58` + offset, the data lands in sysmem at the specified
offset. The emulator routes these to `HostInterface.sysmem`.

### 20.3 Firmware/kernel upload

The host writes firmware and kernel binaries into each tile's L1 at the appropriate base
addresses (see §4.2), then deasserts soft reset bits to start execution.

---

## 21. Device Grid

### 21.1 Tile coordinates

P100 (120 Tensix cores):
- X: {1,2,3,4,5,6,7,10,11,12,13,14} (12 columns)
- Y: {2,3,4,5,6,7,8,9,10,11} (10 rows)
- Dispatch: (14,2) prefetch, (14,3) dispatch
- Available workers: 110 cores (excluding dispatch)

P150 (140 Tensix cores):
- X: {1,2,3,4,5,6,7,10,11,12,13,14,15,16} (14 columns)
- Y: {2,3,4,5,6,7,8,9,10,11} (10 rows)
- Dispatch: (16,2) prefetch, (16,3) dispatch

### 21.2 DRAM tile coordinates

```python
DRAM_BANK_XY = {
    0: (0, [0, 1, 11]),   # bank 0, west, 3 ports
    1: (0, [2, 10, 3]),
    2: (0, [9, 4, 8]),
    3: (0, [5, 7, 6]),
    4: (9, [0, 1, 11]),   # bank 4, east
    5: (9, [2, 10, 3]),
    6: (9, [9, 4, 8]),
    7: (9, [5, 7, 6]),
}
```

### 21.3 Coordinate translation

The emulator should support translated coordinates (used by NOC1). Translation tables
are programmed in NIU_CFG registers at `0xFFB20118–0x144`. When bit 14 of NIU_CFG_0 is
set, X/Y coordinates in NOC commands are translated through these tables before routing.

---

## 22. Execution Model

### 22.1 Main loop

```python
class EmulatedDevice:
    def step(self):
        """Advance one global tick."""
        # 1. Step all RISCV cores (round-robin across tiles)
        for tile in self.tiles.values():
            for core in tile.cores:
                if not core.in_reset and not core.halted:
                    core.step()

        # 2. Step all Tensix coprocessors
        for tile in self.tiles.values():
            tile.tensix.step()

        # 3. Step NOC fabric (deliver pending transactions)
        self.noc.tick()

        self.cycle += 1

    def run_until_done(self, max_cycles=10_000_000):
        """Run until all cores halt or timeout."""
        while self.cycle < max_cycles:
            self.step()
            if self.all_done():
                break
```

### 22.2 "Done" detection

A kernel is done when BRISC writes `RUN_MSG_DONE` to the dispatch stream (stream 48).
The host polls for this completion signal.

### 22.3 Multi-core execution

All tiles execute concurrently in the round-robin. NOC transactions have a configurable
latency (default: 1 tick for same-tile, proportional to Manhattan distance for
cross-tile). This is cycle-approximate, not cycle-exact.

---

## 23. Data Types

### 23.1 Format conversion utilities

```python
import struct

def fp32_to_bf16(f):
    """Truncate FP32 to BF16 (top 16 bits)."""
    bits = struct.unpack('<I', struct.pack('<f', f))[0]
    return (bits >> 16) & 0xFFFF

def bf16_to_fp32(bf16):
    """Expand BF16 to FP32."""
    bits = bf16 << 16
    return struct.unpack('<f', struct.pack('<I', bits))[0]

def fp32_to_fp16(f):
    """Convert FP32 to IEEE FP16 (non-conformant: no inf/NaN)."""
    ...

def fp32_to_tf32(f):
    """Truncate FP32 to TF32 (19-bit: 1+8+10)."""
    bits = struct.unpack('<I', struct.pack('<f', f))[0]
    return bits & 0xFFFFE000  # zero low 13 mantissa bits

def shuffled_to_ieee(val_19bit):
    """Convert {sign, mantissa, exponent} to IEEE {sign, exponent, mantissa}."""
    sign = (val_19bit >> 18) & 1
    mantissa = (val_19bit >> 8) & 0x3FF
    exponent = val_19bit & 0xFF
    return (sign << 31) | (exponent << 23) | (mantissa << 13)

def ieee_to_shuffled(ieee_bits):
    """Convert IEEE FP32 to 19-bit shuffled {sign, mantissa, exponent}."""
    sign = (ieee_bits >> 31) & 1
    exponent = (ieee_bits >> 23) & 0xFF
    mantissa = (ieee_bits >> 13) & 0x3FF
    return (sign << 18) | (mantissa << 8) | exponent
```

### 23.2 Sign-magnitude integers

Tensix uses sign-magnitude (not two's complement) for integers in Dst and SFPU:
```python
def int_to_signmag(val, bits=32):
    if val < 0:
        return (1 << (bits-1)) | (-val & ((1 << (bits-1)) - 1))
    return val

def signmag_to_int(val, bits=32):
    sign = (val >> (bits-1)) & 1
    mag = val & ((1 << (bits-1)) - 1)
    return -mag if sign else mag
```

---

## 24. PIC (Programmable Interrupt Controller)

Base: `0xFFB13000`. 32 software IRQs + 4 hardware IRQs.

```python
class PIC:
    def __init__(self):
        self.sw_int = [0] * 32          # atomic single-slot queues
        self.hw_int = [0] * 4
        self.brisc_sw_int_en = 0        # enable mask
        self.brisc_hw_int_en = 0
        self.ncrisc_sw_int_en = 0
        self.ncrisc_hw_int_en = 0
        self.sw_int_pc = [0] * 32       # handler PCs
        self.hw_int_pc = [0] * 4
```

Model as needed; initially stub out (no interrupt delivery in V1).

---

## 25. Implementation Plan

### Phase 1: Core infrastructure
1. `RiscVCore` — full RV32IM + Zicsr + Zaamo + Zba + Zbb decoder and executor
2. `L1Memory` — 1536 KiB scratchpad with atomic support
3. `TensixTile` — glue: 5 cores + L1 + memory map decoder
4. `EmulatedDevice` — grid of tiles + main loop
5. Memory map routing (loads/stores to correct backing store)

### Phase 2: Tensix coprocessor
6. Instruction FIFO + MOP expander + replay buffer
7. Sync unit (STALLWAIT, SEMWAIT, semaphores, mutexes)
8. SrcA/SrcB/Dst register files with format conversion
9. FPU: MVMUL, ELWADD, ELWMUL, ZEROACC, ZEROSRC, MOVx2x
10. SFPU: all instructions from §11, conditional execution, LReg file
11. Config unit (WRCFG, RDCFG, SETC16, RMWCIB)
12. Scalar unit (SETDMAREG, ADDDMAREG, MULDMAREG)

### Phase 3: Memory subsystem
13. NOC fabric (reads, writes, broadcasts, atomics, completion counters)
14. NOC NIU register model
15. DRAM banks (sparse storage)
16. Circular buffer state + stream register model
17. Unpack pipeline (L1 → SrcA/SrcB with format conversion)
18. Pack pipeline (Dst → L1 with format conversion, ReLU, accumulation)

### Phase 4: Integration
19. Host interface (firmware upload, kernel dispatch, completion detection)
20. Firmware boot sequence support (CSR init, soft reset, BRISC→TRISC handoff)
21. End-to-end test: run `add1.py` kernel through emulator
22. End-to-end test: run `matmul_peak.py` multi-core matmul

### Phase 5: Correctness & completeness
23. Hardware bug modeling (FP16 L1 acc, inline write to L1)
24. Fidelity phase modeling for MVMUL
25. Stochastic rounding (SFPSTOCHRND)
26. ADC (address counter) unit
27. XMOV (mover) unit
28. Coordinate translation tables

---

## 26. Testing Strategy

### Unit tests
- RISCV: test each instruction against known-good values
- Tensix: test each opcode in isolation (SFPMAD, MVMUL, etc.)
- Format conversion: round-trip tests for all data types
- Semaphore: test SEMINIT/SEMPOST/SEMGET/SEMWAIT sequences

### Integration tests
- Run real firmware boot sequence; verify BRISC reaches main loop
- Run add1.py kernel; compare output against hardware/expected values
- Run matmul_peak.py; verify multi-core NOC communication + result correctness

### Comparison tests
- Run same kernel on emulator and real hardware; diff outputs
- Use `dsl.py` to generate instruction sequences, run on both, compare register state

---

## 27. File Structure

```
blackhole-py-emu/
  emulator/
    __init__.py
    device.py           # EmulatedDevice, main loop
    tile.py             # TensixTile
    riscv.py            # RiscVCore (decoder + executor)
    riscv_decode.py     # Instruction decoding tables
    tensix.py           # TensixCoprocessor (frontend + backend dispatch)
    tensix_sync.py      # Sync unit (STALLWAIT, semaphores, mutexes)
    tensix_fpu.py       # FPU (MVMUL, ELWADD, etc.)
    tensix_sfpu.py      # SFPU (all vector instructions)
    tensix_scalar.py    # Scalar unit (DMA regs)
    tensix_config.py    # Config/ThreadConfig management
    tensix_unpack.py    # Unpacker pipeline
    tensix_pack.py      # Packer pipeline
    regfiles.py         # SrcA, SrcB, Dst, LReg register files
    l1.py               # L1Memory
    noc.py              # NocFabric + NIU register model
    dram.py             # DramBank (sparse)
    host.py             # HostInterface
    cb.py               # CircularBuffer state
    formats.py          # Data type conversion utilities
    constants.py        # All address constants, register offsets
    pic.py              # PIC (stub)
  tests/
    test_riscv.py
    test_tensix.py
    test_sfpu.py
    test_fpu.py
    test_noc.py
    test_cb.py
    test_formats.py
    test_integration.py
```
