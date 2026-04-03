# Compiler Process, -D Defines, and Writing Raw RISC-V Firmware

How `compiler.py` builds firmware and kernels, every compile-time define and what it touches, and how to bypass the compiler entirely to upload raw RISC-V blobs.

## Compilation phases

### Phase A: Firmware (once at `Compiler.__init__`)

Compiles 5 ELFs from `firmware/{brisc,ncrisc,trisc}.cc`. These are resident dispatch loops that run forever on each RISC-V core, polling for kernel launches.

```
firmware/brisc.cc  → brisc   (-mcpu=tt-bh,        -Os)
firmware/ncrisc.cc → ncrisc  (-mcpu=tt-bh,        -Os)
firmware/trisc.cc  → trisc0  (-mcpu=tt-bh-tensix,  -O3)
firmware/trisc.cc  → trisc1  (-mcpu=tt-bh-tensix,  -O3)
firmware/trisc.cc  → trisc2  (-mcpu=tt-bh-tensix,  -O3)
```

Each links against a linker script from `tt-metal-deps/toolchain/blackhole/firmware_{target}.ld` and `tmu-crt0.o`. Firmware is multicast to all worker cores via WC TLB. BRISC is released from reset, then releases the others.

### Phase B: User kernels (per-program)

1. Generates in-memory ckernel headers (`_ckernel_headers`) for Trisc pipeline config
2. Writes them + user kernel source to a temp dir as `kernel_includes.hpp`
3. Compiles `tt-metal-deps/firmware-src/{brisck,ncrisck,trisck}.cc` (stubs that `#include <kernel_includes.hpp>`)
4. Links with weakened firmware ELF (`--just-symbols`) to resolve firmware BSS symbols
5. `pack_xip_elf` strips the ELF to a flat binary blob — **no ELF headers reach the chip**
6. Blob placed in L1 at `KERNEL_CONFIG_BASE + kernel_text_offset`

For Trisc, three stubs are generated (e.g. `chlkc_unpack.cpp` with `#define TRISC_UNPACK`), giving each sub-processor its own view of the kernel.

## All -D defines

### Dynamic (board-dependent, from `_device_defines()`)

These are computed from actual hardware topology at runtime.

| Define | P100A | P150 | What it controls |
|--------|-------|------|------------------|
| `NUM_DRAM_BANKS` | 7 | 8 | Array sizes for `dram_bank_to_noc_xy[NUM_NOCS][N]`, `bank_to_dram_offset[N]`. Controls division method in `get_bank_offset_index()` in `dataflow_api_addrgen.h`. |
| `NUM_L1_BANKS` | ~110 | 120 or 140 | Array sizes for `l1_bank_to_noc_xy[NUM_NOCS][N]`, `bank_to_l1_offset[N]`. Same division logic. |
| `IS_NOT_POW2_NUM_DRAM_BANKS=1` | **set** (7) | **not set** (8) | Forces software division (`udivsi3_const_divisor<N>`) instead of bit-shift for DRAM bank index. |
| `LOG_BASE_2_OF_NUM_DRAM_BANKS=3` | **not set** | **set** | Enables `id >> 3` fast path for DRAM bank index. |
| `IS_NOT_POW2_NUM_L1_BANKS=1` | **always set** | **always set** | 110, 120, 140 are all non-pow2. Always software division for L1 banks. |
| `PREFETCH_NOC_X` | 14 | 16 | CQ kernel peer location. Only consumed by CQ (prefetch/dispatch) kernels, not worker kernels. |
| `PREFETCH_NOC_Y` | 2 | 2 | Same. |
| `DISPATCH_NOC_X` | 14 | 16 | Same. |
| `DISPATCH_NOC_Y` | 3 | 3 | Same. |

**Note on bank tables:** The actual bank-to-NOC-XY mapping is entirely runtime. It's computed in Python by `build_bank_noc_table()` in `hw.py`, DMA'd to `MEM_BANK_TO_NOC_SCRATCH` in each core's L1, then copied into BSS arrays by `noc_bank_table_init()` at firmware startup. The defines only size the arrays and pick the division method.

**Note on P150 core counts:** BH silicon has 14 cols x 10 rows = 140 physical Tensix cores. Since Jan 2026, all P150s ship with `tensix_col_disable_count: 2` in the zephyr firmware's `fw_table.txt`, soft-harvesting 2 columns → 120 cores. Pre-2026 P150s can still have 140. The `tt-update-tensix-disable-count` tool can re-enable all 14 columns.

### Static (always the same, both boards)

| Define | Value | What it controls |
|--------|-------|------------------|
| `ARCH_BLACKHOLE` | defined | ~dozens of `#ifdef` branches. Key effects: `invalidate_l1_cache()` emits `asm("fence")`; `configure_gathering()` disables Tensix instruction gathering (bit 18, workaround for tt-metal#16439); `configure_l1_data_cache()` calls `set_l1_data_cache<false>()`; BH-specific compute paths in matmul, tilize, pack_untilize. |
| `TENSIX_FIRMWARE` | defined | Gates firmware-only code paths vs kernel code paths. |
| `LOCAL_MEM_EN` | 0 | Register file storage location in ckernel. Always 0 for BH bare-metal. |
| `PCIE_NOC_X` | 19 | PCIe endpoint NOC coordinate — hardcoded for BH silicon. Used in `dataflow_api_addrgen.h` for host DMA and in `kernel_profiler.hpp`. |
| `PCIE_NOC_Y` | 24 | Same. |
| `DISPATCH_MESSAGE_ADDR` | `0xFFB70438` | Stream register address for kernel-done notification. BRISC uses this with `notify_dispatch_core_done()` to signal dispatch core. |
| `FW_BUILD` | defined (fw only) | Gates firmware-specific paths in `dev_msgs.h`. |
| `KERNEL_BUILD` | defined (kernels only) | Gates kernel-specific paths. |

### Per-processor (static, one set per target)

| Target | Defines |
|--------|---------|
| BRISC | `-DCOMPILE_FOR_BRISC -DPROCESSOR_INDEX=0 -DNOC_INDEX=1 -DNOC_MODE=0` |
| NCRISC | `-DCOMPILE_FOR_NCRISC -DPROCESSOR_INDEX=1 -DNOC_INDEX=0 -DNOC_MODE=0` |
| TRISC0 | `-DCOMPILE_FOR_TRISC=0 -DPROCESSOR_INDEX=2 -DUCK_CHLKC_UNPACK -DNAMESPACE=chlkc_unpack` |
| TRISC1 | `-DCOMPILE_FOR_TRISC=1 -DPROCESSOR_INDEX=3 -DUCK_CHLKC_MATH -DNAMESPACE=chlkc_math` |
| TRISC2 | `-DCOMPILE_FOR_TRISC=2 -DPROCESSOR_INDEX=4 -DUCK_CHLKC_PACK -DNAMESPACE=chlkc_pack` |

What each controls:

- `COMPILE_FOR_{BRISC,NCRISC,TRISC=N}` — primary processor selector. Used throughout `risc_common.h`, `firmware_common.h`, `trisc.cc`, kernel entry stubs. Gates huge amounts of code.
- `PROCESSOR_INDEX` — indexes into `LaunchMsg.rta_offset[]` and `kernel_text_offset[]` arrays. BRISC=0, NCRISC=1, TRISC0=2, TRISC1=3, TRISC2=4.
- `NOC_INDEX` — default NOC channel (BRISC=1, NCRISC=0). BRISC's is overridden at runtime from `launch_msg.kernel_config.brisc_noc_id`.
- `NOC_MODE=0` — `DM_DEDICATED_NOC`, each RISC owns its NOC. Used in kernel entry stubs for `noc_local_state_init()`.
- `UCK_CHLKC_{UNPACK,MATH,PACK}` — gates ckernel stage inclusion in `chlkc_list.h`. Each `#ifdef` block includes the relevant generated headers and the user's kernel function (`unpack_main`, `math_main`, `pack_main`).
- `NAMESPACE` — C++ namespace wrapping each stage's kernel function. `chlkc_list.h`'s `run_kernel()` calls `chlkc_math::math_main()` etc.

### Conditional (profiling, off by default)

Set when `PROFILE=1` env var is present. `compiler.py` line 9: `PROFILER = os.environ.get("PROFILE") == "1"`.

| Define | Value | Scope | Notes |
|--------|-------|-------|-------|
| `PROFILE_KERNEL` | 1 | All 5 firmware targets + user BRISC/NCRISC/TRISC kernels | Activates entire profiler infrastructure |
| `PROFILER_FULL_HOST_BUFFER_SIZE_PER_RISC` | 65536 (64 KB) | Same as above | From `TensixL1.PROFILER_HOST_BUFFER_BYTES_PER_RISC` in `hw.py` |
| `PROFILE_PERF_COUNTERS` | `0x3f` | **Firmware TRISC1 only** (not user kernels, not CQ kernels) | Hardware performance counter capture around kernel execution |

CQ kernels (`compile_cq_kernels`) always pass `profiler=False` — they never get profiling defines.

#### What `PROFILE_KERNEL=1` enables

Activates `kernel_profiler.hpp`. Without it, all profiler macros (`DeviceZoneScopedN`, `DeviceProfilerInit`, etc.) are empty no-ops.

With it active, each firmware file declares profiler state in L1:

```cpp
// brisc.cc, ncrisc.cc, trisc.cc:
namespace kernel_profiler {
    uint32_t wIndex;        // write cursor into L1 profiler buffer
    uint32_t stackSize;     // tracks nested zone depth
    uint32_t sums[SUM_COUNT];
    uint32_t sumIDs[SUM_COUNT];
    // brisc.cc also has: uint32_t traceCount
}
```

**Key macros when active:**

| Macro | What it does |
|-------|-------------|
| `DeviceProfilerInit()` | Clears L1 profiler buffer header, resets cursors |
| `DeviceZoneScopedMainN("BRISC-FW")` | RAII scope writing guaranteed start/end timestamps at fixed buffer slots. Destructor calls `finish_profiler()` which NOC-DMAs the L1 buffer to host sysmem. |
| `DeviceZoneScopedN("name")` | RAII scope writing timestamped start/end pairs into optional zone area (dropped if buffer full) |
| `DeviceZoneSetCounter(id)` | Records host-assigned program ID |
| `DeviceValidateProfiler(enables)` | Marks zone valid/invalid |

**Timestamp format:** Each timestamp reads `RISCV_DEBUG_REG_WALL_CLOCK_L` (44-bit wall clock), packed as two uint32s: `0x80000000 | (timer_id << 12) | clock_hi12` and `clock_lo32`.

**`finish_profiler()` flush path:** On `DeviceZoneScopedMainN` destructor, NOC-writes the entire L1 profiler buffer to the per-RISC slot in host sysmem at:
```
flat_offset = core_flat_id * 5 * 65536 + risc_id * 65536 + (host_written_words * 4)
```
Then increments `RUN_COUNTER` and sets `PROFILER_DONE=1` in the control buffer.

#### What `PROFILE_PERF_COUNTERS=0x3f` enables

Hardware performance counter capture, **only in firmware trisc1** (the MATH processor). The code lives in `trisc.cc` lines 87-169.

**Bit flags:**

| Bit | Mask | Group | Control register | Counters |
|-----|------|-------|-----------------|----------|
| 0 | `0x01` | FPU | `RISCV_DEBUG_REG_PERF_CNT_FPU0` | 3 |
| 1 | `0x02` | PACK | `RISCV_DEBUG_REG_PERF_CNT_TDMA_PACK0` | 3 |
| 2 | `0x04` | UNPACK | `RISCV_DEBUG_REG_PERF_CNT_TDMA_UNPACK0` | 11 |
| 3 | `0x08` | L1_0 | `RISCV_DEBUG_REG_PERF_CNT_L1_0` | 8 |
| 4 | `0x10` | L1_1 | Same as L1_0, MUX bit 4 = 1 | 8 |
| 5 | `0x20` | INSTRN | `RISCV_DEBUG_REG_PERF_CNT_INSTRN_THREAD0` | 61 |

Total: **94 counters** when all bits set (`0x3f`).

L1_0 and L1_1 share the same hardware register block. `RISCV_DEBUG_REG_PERF_CNT_MUX_CTRL` bit 4 selects which channel: 0 = NOC ring 0 / L1 arbitration, 1 = NOC ring 1 / TDMA.

**How it works in the firmware main loop** (`trisc.cc`):

```cpp
// Before kernel call:
perf_counter_start();       // zeros control regs, writes PERF_CNT_CONTINUOUS_MODE, starts all enabled groups

auto stack_free = reinterpret_cast<uint32_t (*)()>(kernel_lma)();  // run user kernel

// After kernel returns:
perf_counter_emit(perf_counter_stop_and_capture());
// stop_and_capture: reads all 94 counter values into perf_counter_samples[]
// Each sample packed as: counter_value | (ref_cnt << 32) | (counter_type << 56)
// emit: writes each sample as TS_DATA packet with profiler ID 9090 into L1 profiler buffer
```

#### Profiler control buffer in L1

32 x uint32 at `TensixL1.PROFILER_CONTROL = 0x0009C0` (128 bytes). Host reads this after execution to determine how much data each RISC wrote.

| Index | Name | Purpose |
|-------|------|---------|
| 0-4 | `HOST_BUFFER_END_INDEX_{BR,NC,T0,T1,T2}` | Words already written to host sysmem per RISC |
| 5-9 | `DEVICE_BUFFER_END_INDEX_{BR,NC,T0,T1,T2}` | Words written to L1 buffer this run |
| 10-11 | `FW_RESET_H`, `FW_RESET_L` | Firmware reset timestamp |
| 12 | `DRAM_PROFILER_ADDRESS_DEFAULT` | Sysmem NOC local offset (written by host before each run) |
| 13 | `RUN_COUNTER` | Incremented by `finish_profiler()` each run |
| 14-15 | `NOC_X`, `NOC_Y` | Core NOC coordinates (written by host) |
| 16 | `FLAT_ID` | Core flat index (written by host) |
| 18 | `DROPPED_ZONES` | Bitmask of which RISC buffers had drops |
| 19 | `PROFILER_DONE` | Set to 1 by `finish_profiler()` |

Host programs indices 12, 14, 15, 16 per-core via `CQWritePacked` before each program. Zeroes indices 0-4 and 19 at start.

#### Host sysmem profiler layout

```
_HOST_PROFILER_BASE (after issue + completion rings):
  per core (320 KB):
    BRISC  : 64 KB (16384 uint32s)
    NCRISC : 64 KB
    TRISC0 : 64 KB
    TRISC1 : 64 KB
    TRISC2 : 64 KB
```

#### Full profiler data flow

1. `PROFILE=1` → compiler adds defines to all firmware + kernel builds
2. Before each program: host CQ writes profiler control block to each core's L1 at `0x9C0`
3. Firmware runs:
   - All RISCs: `DeviceZoneScopedMainN` captures guaranteed FW start/end timestamps
   - TRISC1: `perf_counter_start()` → user kernel → `perf_counter_stop_and_capture()` → `perf_counter_emit()` writes 94 counter values as `TS_DATA` packets (ID 9090) into L1 buffer
   - User kernels: `DeviceZoneScopedN` writes optional zone timestamps
   - `finish_profiler()`: NOC-DMAs L1 buffer to per-RISC slot in host sysmem
4. After completion: Python reads `ctrl_regs` from L1 `0x9C0`, reads sysmem profiler data, `profiler.py` parses into structured zones and perf counter records

### Per-program generated headers (Trisc compute kernels only)

Synthesized by `_ckernel_headers()` from the `Program` object. Written to temp dir before Trisc compilation.

| Header | Key contents | Source |
|--------|-------------|--------|
| `chlkc_unpack_data_format.h` | `unpack_src_format[32]`, `unpack_dst_format[32]` | CB dtype values (default `Float16_b=5`) |
| `chlkc_pack_data_format.h` | `pack_src_format[32]`, `pack_dst_format[32]` | Same |
| `chlkc_unpack_tile_dims.h` | `unpack_tile_face_r_dim[32]=16`, `unpack_tile_r_dim[32]=32`, `unpack_tile_c_dim[32]=32`, etc. | Fixed 32x32 full tiles |
| `chlkc_pack_tile_dims.h` | Same with `pack_` prefix | Same |
| `chlkc_dst_accum_mode.h` | `constexpr bool DST_ACCUM_MODE` | `program.dst_accum_mode` |
| `chlkc_dst_sync_mode.h` | `#define DST_SYNC_MODE DstSync::SyncFull` or `SyncHalf` | `program.dst_full_sync` |
| `chlkc_math_fidelity.h` | `constexpr int32_t MATH_FIDELITY` | `program.math_fidelity` (LoFi=0, HiFi2=2) |
| `chlkc_math_approx_mode.h` | `constexpr bool APPROX` | `program.approx` |
| `defines_generated.h` | Empty | Placeholder |

## What `pack_xip_elf` does

Converts an ELF into a flat binary:

1. Optionally rewrites `LUI` instructions to `AUIPC`-relative for position independence (`_xipify_riscv32_elf`)
2. Extracts all `PT_LOAD` segments within L1 range (`0 <= paddr < 0x180000`)
3. Assembles them into a single contiguous blob, zero-filling gaps
4. Returns `(blob_bytes, text_segment_length)`

The result is raw machine code. No ELF headers, no metadata. This is what gets written to L1.

## BSS

**BSS** = "Block Started by Symbol". The section for uninitialized global/static variables. In a binary, it takes zero space — just a recorded address range that must be zeroed before the program runs.

```c
int counter;           // BSS — no space in binary, zeroed at startup
int table[1024];       // BSS — same
int magic = 0xDEAD;    // .data — 4 bytes stored in binary
```

### How BSS is zeroed today

**Firmware BSS:** Host pads each ELF segment with `\0` bytes up to `memsz` before DMA to L1 (`device.py:165-166`). BSS arrives pre-zeroed.

**Kernel BSS:** Firmware calls `do_crt1()` before jumping into kernel code:
```cpp
inline void do_crt1(uint32_t tt_l1_ptr* data_image) {
    extern uint32_t __ldm_bss_start[], __ldm_bss_end[];
    wzerorange(__ldm_bss_start, __ldm_bss_end);           // zero BSS in local SRAM
    extern uint32_t __ldm_data_start[], __ldm_data_end[];
    l1_to_local_mem_copy(__ldm_data_start, data_image, ...); // copy .data from L1 to local SRAM
}
```

**Firmware's own local-SRAM BSS:** BRISC calls `do_crt1(MEM_BRISC_INIT_LOCAL_L1_BASE_SCRATCH)` at boot. Same for NCRISC.

## Writing raw RISC-V firmware (no compiler, no ELF)

### Can you skip ELF entirely?

**Yes.** The ELF format is only used at compile/link time on the host. By the time code runs on a Tensix core, it's always a flat binary called via function pointer or reset vector. `pack_xip_elf` already strips everything.

### Boot sequence (what the host does)

1. Write a `JAL` instruction at **L1 address 0x0** — BRISC's reset vector, jumps to wherever you put BRISC code
2. Write BRISC blob at target address (e.g. `0x3840`)
3. Write NCRISC/TRISC blobs at their addresses
4. Program subordinate reset PC MMIO registers:
   - `0xFFB12238` → NCRISC start address
   - `0xFFB12228` → TRISC0 start address
   - `0xFFB1222C` → TRISC1 start address
   - `0xFFB12230` → TRISC2 start address
5. Assert all cores into reset (`SOFT_RESET_ALL = 0x47800` at `0xFFB121B0`)
6. Release BRISC only (`0x47000` at `0xFFB121B0`)
7. BRISC runs, releases subordinates when ready

### What your raw blob needs

**If you have no global variables** (no BSS, no `.data`): just set up `sp` and `gp`.

```
Local SRAM: 0xFFB00000
  BRISC/NCRISC: 8 KB  → sp = 0xFFB02000
  TRISC0/1/2:   4 KB  → sp = 0xFFB01000
  gp convention:         gp = 0xFFB007F0
```

**If you have globals:** zero your BSS range and/or copy `.data` initializers from L1 into local SRAM. Or just don't use globals.

**If you're using NOC:** call `noc_local_state_init(noc_index)` or configure NOC registers manually.

### Minimum viable blob

```asm
# BRISC firmware — executes from wherever you place it in L1
_start:
    li sp, 0xFFB02000       # stack top (8 KB local SRAM)
    li gp, 0xFFB007F0       # global pointer

    # your code here — NOC reads/writes, DRAM access, whatever

    j _start                 # loop forever
```

Assemble and extract flat binary:
```bash
riscv-tt-elf-as -o fw.o fw.s
riscv-tt-elf-ld -Ttext=0x3840 -nostdlib -o fw.elf fw.o
riscv-tt-elf-objcopy -O binary fw.elf fw.bin
# fw.bin is your raw blob — upload to L1 at 0x3840
```

Or compile C with no runtime:
```bash
riscv-tt-elf-g++ -mcpu=tt-bh -nostartfiles -nostdlib -Wl,-Ttext=0x3840 -O2 -o fw.elf fw.c
riscv-tt-elf-objcopy -O binary fw.elf fw.bin
```

### Dispatch protocol (optional)

Today's firmware polls `mailboxes->go_messages` at `L1[0x370]`. If you're replacing the entire firmware, you define your own protocol:

- Host writes a "go" word to a known L1 address
- Core polls for it, does work, writes "done"
- Host polls for "done"

Or skip the protocol entirely — firmware does its thing on boot.

### What defines you can hardcode if targeting P100A + P150 only

| What | P100A | P150 | Can hardcode? |
|------|-------|------|---------------|
| `ARCH_BLACKHOLE` | yes | yes | **Yes** — always defined |
| `PCIE_NOC_X/Y` | 19, 24 | 19, 24 | **Yes** — same on all BH |
| `DISPATCH_MESSAGE_ADDR` | `0xFFB70438` | `0xFFB70438` | **Yes** |
| `LOCAL_MEM_EN` | 0 | 0 | **Yes** |
| `NUM_DRAM_BANKS` | 7 | 8 | **No** — must detect or branch |
| `NUM_L1_BANKS` | ~110 | 120 or 140 | **No** — depends on harvesting |
| DRAM pow2 logic | software div | bit-shift | **No** — or just always use software div |
| `PREFETCH/DISPATCH_NOC_X` | 14 | 16 | **No** — but only matters for CQ kernels |

If you don't use the interleaved bank abstraction (`InterleavedAddrGenFast`) and address DRAM/cores directly by NOC coordinates, you can skip `NUM_DRAM_BANKS`, `NUM_L1_BANKS`, and all the pow2 defines entirely.

## Toolchain reference

```
Compiler:   tt-metal-deps/sfpi-toolchain/bin/riscv-tt-elf-g++
Assembler:  tt-metal-deps/sfpi-toolchain/bin/riscv-tt-elf-as
Linker:     tt-metal-deps/sfpi-toolchain/bin/riscv-tt-elf-ld
Objcopy:    tt-metal-deps/sfpi-toolchain/bin/riscv-tt-elf-objcopy

Common CFLAGS:  -std=c++17 -flto=auto -ffast-math -fno-exceptions -fno-use-cxa-atexit
Common LFLAGS:  -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles

BRISC/NCRISC CPU:  -mcpu=tt-bh -fno-tree-loop-distribute-patterns -mno-tt-tensix-optimize-replay
TRISC CPU:         -mcpu=tt-bh-tensix -mno-tt-tensix-optimize-replay
```
