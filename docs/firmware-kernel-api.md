# Firmware & Kernel API Reference

All functions used by the base firmware (`TT_USB=1` slow-dispatch path) and
the `add1.py` compute kernel, organized by subsystem.  Each entry includes a
short description, the source header, and approximate line number so you can
find the actual instruction sequence to port.

Paths are relative to `tt-metal-deps/include/`.

---

## 1  Boot / CRT

### `configure_csr()`
Writes CSR `0x7C0` to disable Tensix instruction gathering, optionally enable
the 4-line L1 data cache, and set memory ordering.  Three sub-calls:
`configure_gathering()`, `configure_l1_data_cache()`,
`disable_relaxed_memory_ordering()` -- each a single `csrs`/`csrc` on CSR
`0x7C0`.

**Source:** `tt_metal/hw/inc/internal/firmware_common.h:260`

### `do_crt1(scratch_base)`
Standard C runtime init.  Zeroes `.bss` via `wzerorange(__ldm_bss_start,
__ldm_bss_end)`, then copies `.data` from L1 into LDM if the link-time
addresses differ (`l1_to_local_mem_copy`).

**Source:** `tt_metal/hw/inc/internal/firmware_common.h:62`

### `wzerorange(start, end)` / `wzeromem(addr, len)`
`wzerorange` is an extern-C assembly routine that zeroes `[start, end)` word
by word (unrolled 3-word loop visible in disasm).  `wzeromem` is a thin inline
wrapper.

**Source:** `tt_metal/hw/inc/internal/tensix_functions.h:738`

### `l1_to_local_mem_copy(dst, src, nwords)`
Copies `nwords` 32-bit words from an L1 pointer to an LDM pointer (unrolled
3-word loop).

**Source:** visible in disasm as `_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l`

---

## 2  NOC Initialization

### `noc_bank_table_init(l1_scratch_addr)`
Copies four lookup tables from L1 into LDM: `dram_bank_to_noc_xy[2][N]`,
`l1_bank_to_noc_xy[2][N]`, `bank_to_dram_offset[N]`,
`bank_to_l1_offset[N]`.  These are used by `InterleavedAddrGenFast` for
bank-interleaved tile addressing.

**Source:** `tt_metal/hw/inc/internal/firmware_common.h:89`

### `noc_worker_logical_to_virtual_map_init(l1_scratch_addr)`
Copies `worker_logical_col_to_virtual_col[]` and
`worker_logical_row_to_virtual_row[]` from L1 into LDM.

**Source:** `tt_metal/hw/inc/internal/firmware_common.h:112`

### `risc_init()`
Reads each NOC's `NOC_NODE_ID` register at `NOCx_REGS + 0x148`, extracts x
(bits 5:0) and y (bits 11:6), stores into `my_x[noc]`, `my_y[noc]`.  Only
runs on BRISC/NCRISC (dataflow cores).

**Source:** `tt_metal/hw/inc/internal/tt-1xx/risc_common.h:194`

### `noc_init(atomic_ret_addr)`
For each NOC: reads `NOC_NODE_ID`, then programs 4 command buffer slots
(write, write-reg, atomic, read) with the local node's XY and default control
fields.  Each cmd buf is a set of 7 contiguous 32-bit MMIO registers starting
at `NOCx_REGS + cmd_buf_offset`.

**Source:** `tt_metal/hw/inc/internal/tt-1xx/blackhole/noc_nonblocking_api.h:431`

### `noc_local_state_init(noc_index)`
Snapshots 5 hardware status counters into software variables:
`noc_reads_num_issued`, `noc_nonposted_writes_num_issued`,
`noc_nonposted_writes_acked`, `noc_nonposted_atomics_acked`,
`noc_posted_writes_num_issued`.  These baselines let barrier functions detect
when new operations complete.

**Source:** `tt_metal/hw/inc/internal/tt-1xx/blackhole/noc_nonblocking_api.h:512`

### `noc_set_active_instance(n)` / `noc_get_cfg_reg(id)` / `noc_set_cfg_reg(id, val)`
Select which NOC (0 or 1) is active; read/write NOC config registers by ID.
Implemented in the noc.o object linked with BRISC.

**Source:** `tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc.h:446,515,520`

---

## 3  Register / MMIO Access Primitives

### `WRITE_REG(addr, val)`
`*(volatile tt_reg_ptr uint32_t*)addr = val`.  Writes to the Tensix MMIO
register space (`0xFFB1xxxx`).

**Source:** `tt_metal/hw/inc/internal/tt-1xx/risc_common.h:45`

### `NOC_READ_REG(addr)` / `NOC_WRITE_REG(addr, val)`
`*(volatile uint32_t*)addr` reads/writes.  For NOC overlay/stream registers
(`0xFFB2xxxx`, `0xFFB3xxxx`, etc.).

**Source:** `tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_overlay_parameters.h:80`

### `invalidate_l1_cache()`
On Blackhole: emits a single RISC-V `fence` instruction.  Invalidates the
small 4-line write-through data cache so subsequent loads fetch from L1 SRAM.

**Source:** `tt_metal/hw/inc/internal/tt-1xx/risc_common.h:153`

---

## 4  Tensix Hardware Setup (BRISC only)

These run once during `device_setup()` in BRISC firmware.  They push encoded
32-bit command words to `0xFFE40000` (the Tensix instruction queue FIFO).

### `core.ex_zeroacc(instrn_buf)`
Pushes a `ZEROACC` command (clear accumulator/dest register, all faces).

**Source:** `tt_metal/hw/inc/internal/tt-1xx/blackhole/c_tensix_core.h:255` ->
`tt_metal/hw/inc/internal/tensix_functions.h:145`

### `core.ex_encc(instrn_buf)`
Pushes `SFPENCC` (enable condition codes in SFPU) + a NOP.

**Source:** `c_tensix_core.h:259` -> `tensix_functions.h:151`

### `core.ex_load_const(instrn_buf)`
Loads -1.0f into SFPU LREG11: pushes `SFPLOADI` (loads 0xBF80 into LREG0)
then `SFPCONFIG` (copies LREG0 -> LREG11).

**Source:** `c_tensix_core.h:261`

### `core.ex_rmw_cfg(instrn_buf, RMW_field, value)`
Read-modify-write on a Tensix CFG register.  Reads `cfg_regs[addr]`, masks
out the bitfield, ORs in the new value, writes back.  Used for ECC scrubber
config.

**Source:** `c_tensix_core.h:101` -> `tensix_functions.h:124`

### `core.initialize_tensix_semaphores(instrn_buf)`
Pushes `SEMINIT` commands for three hardware semaphores: `MATH_PACK` (max=1),
`UNPACK_TO_DEST` (max=1), `MATH_DONE` (max=1).  These synchronize the
TRISC0/1/2 pipeline during kernel execution.

**Source:** `c_tensix_core.h:415`

---

## 5  Reset / Subordinate Coordination

### `deassert_all_reset()`
`WRITE_REG(RISCV_DEBUG_REG_SOFT_RESET_0, 0)` -- releases all 5 RISC-V cores
from reset.

**Source:** `tt_metal/hw/inc/internal/tt-1xx/risc_common.h:127`

### `set_deassert_addresses()`
Writes to `RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE` and
`RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE` to tell the hardware to use the
host-programmed reset PCs (not compiled-in defaults).

**Source:** `firmware/brisc.cc:135`

### Subordinate sync protocol
BRISC, NCRISC, TRISC0/1/2 synchronize via a `subordinate_sync` struct in the
mailbox (5 bytes at `MEM_MAILBOX_BASE + offset`).  Values:
- `RUN_SYNC_MSG_INIT` (initial)
- `RUN_SYNC_MSG_GO` (run kernel)
- `RUN_SYNC_MSG_DONE` (kernel finished)
- `RUN_SYNC_MSG_INIT_SYNC_REGISTERS` (TRISC0: zero CB semaphores)

All polling loops use `invalidate_l1_cache()` (`fence`) before re-reading.

---

## 6  Launch Message / Kernel Config

### `firmware_config_init(mailboxes, core_type, proc_index)`
Reads `launch_msg[rd_ptr].kernel_config` to extract:
- `kernel_config_base` -- L1 base address for CB config / kernel text
- `rta_offset[proc]` / `crta_offset[proc]` -- runtime argument pointers
- `sem_offset[core_type]` -- semaphore base
Returns `kernel_config_base`.

**Source:** `tt_metal/hw/inc/internal/firmware_common.h:127`

### `setup_local_cb_read_write_interfaces<read, write, pack>(cb_l1_base, start, mask)`
Iterates the bitmask of active circular buffers.  For each set bit, reads the
4-word CB descriptor from `cb_l1_base` (base addr, size, num pages, page size)
and populates the `cb_interface[]` array in LDM with FIFO pointers, limits,
and initial read/write positions.  Has a hand-written assembly fast path.

**Source:** `tt_metal/hw/inc/internal/circular_buffer_init.h:17`

### `experimental::setup_remote_cb_interfaces<is_brisc>(cb_l1_base, end_idx, ...)`
Reads remote CB config from L1, determines sender vs receiver role, populates
`RemoteSenderCBInterface` / `RemoteReceiverCBInterface` structs with NOC XY of
the peer core, FIFO addresses, page counters.

**Source:** `tt_metal/hw/inc/internal/circular_buffer_init.h:169`

---

## 7  Kernel Entry / Exit

### Kernel jump
All cores use `jalr` to the kernel text address:
```c
auto stack_free = reinterpret_cast<uint32_t (*)()>(kernel_lma)();
```
The kernel is expected to return the free stack watermark (or 0).

### `record_stack_usage(stack_free)`
When watcher is enabled, records stack high-water mark.  When disabled (our
builds), this is an empty inline stub.

**Source:** `tt_metal/hw/inc/internal/debug/stack_usage.h:55`

### `tensix_sync()` (TRISC only)
Forces all pending Tensix instruction-buffer operations to drain by doing a
volatile write then read to `pc_buf_base[1]`.  The read blocks until the
Tensix thread is idle.

**Source:** `tt_metal/third_party/tt_llk/tt_llk_blackhole/common/inc/ckernel.h:90`

### `reset_cfg_state_id()` (TRISC only)
Sets `cfg_state_id = 0`.  Selects which of the two ping-pong Tensix CFG
register banks is active.

**Source:** `ckernel.h:244`

### `get_cfg_pointer()` (TRISC only)
Returns `volatile uint* cfg` pointing to the active CFG bank base
(`0xFFEF0000` or `0xFFEF0000 + CFG_STATE_SIZE*16`).

**Source:** `ckernel.h:216`

### `riscv_wait(cycles)` (TRISC only)
Busy-loops reading the 64-bit wall clock at `0xFFB121F0` / `0xFFB121F8`
until `cycles` ticks have elapsed.

**Source:** `tt_metal/hw/inc/internal/tt-1xx/risc_common.h:207`

---

## 8  Dispatch Signaling (BRISC only)

### `calculate_dispatch_addr(go_msg)`
Extracts dispatch core X/Y and message offset from the go-message, returns a
64-bit NOC address pointing to the dispatch core's stream register space.

**Source:** `tt_metal/hw/inc/internal/firmware_common.h:165`

### `notify_dispatch_core_done(dispatch_addr, noc_index)`
Sends a fast posted NOC inline write of
`1 << REMOTE_DEST_BUF_WORDS_FREE_INC` to the dispatch core's stream
register, signaling kernel completion.

**Source:** `tt_metal/hw/inc/internal/firmware_common.h:175`

---

## 9  Dataflow Kernel API (reader/writer kernels)

These are used in the `K_READER` and `K_WRITER` inline kernels of `add1.py`.

### `get_arg_val<T>(index)`
Returns runtime argument `index` from the RTA region.  Just reads
`rta_l1_base[index]`.

**Source:** `tt_metal/hw/inc/api/dataflow/dataflow_api.h` (top-level)

### `get_tile_size(cb_id)`
Returns the tile size in bytes for CB `cb_id`.  Compile-time lookup from the
`unpack_tile_size[]` array (generated from the CB dtype).

**Source:** `tt_metal/hw/inc/api/dataflow/dataflow_api.h:249`

### `InterleavedAddrGenFast<is_dram>`
Struct with `bank_base_address`, `page_size`, `data_format`.  Method
`get_noc_addr(tile_id, offset, noc)` computes which DRAM/L1 bank owns
`tile_id`, looks up the bank's NOC XY from `dram_bank_to_noc_xy[]`, adds the
bank offset from `bank_to_dram_offset[]`, and returns a 40-bit NOC address.
The bank index is `tile_id % num_banks` (uses multiply-high for
constant-time modulo).

**Source:** `tt_metal/hw/inc/internal/dataflow/dataflow_api_addrgen.h:332`

### `cb_reserve_back(cb_id, num_pages)`
**Producer wait.**  Spins until the CB has `num_pages` free slots by comparing
`tiles_received - tiles_acked` against `fifo_num_pages`.  Calls
`invalidate_l1_cache()` in the spin loop.

**Source:** `tt_metal/hw/inc/api/dataflow/dataflow_api.h:375`

### `cb_push_back(cb_id, num_pages)`
**Producer commit.**  Increments the `pages_received` counter at the
stream-register pointer, advances `fifo_wr_ptr`, wraps at `fifo_limit`.

**Source:** `dataflow_api.h:186`

### `cb_wait_front(cb_id, num_pages)`
**Consumer wait.**  Spins until `pages_received - tiles_acked >= num_pages`.
Reads from the stream-register pointer (not LDM), so no cache invalidate
needed.

**Source:** `dataflow_api.h:454`

### `cb_pop_front(cb_id, num_pages)`
**Consumer commit.**  Increments `pages_acked` at the stream-register pointer,
advances `fifo_rd_ptr`, wraps at `fifo_limit`.

**Source:** `dataflow_api.h:228`

### `get_write_ptr(cb_id)` / `get_read_ptr(cb_id)`
Return the current FIFO write/read byte address from `cb_interface[]`.

**Source:** `dataflow_api.h:292,313`

### `noc_async_read_tile(tile_id, addrgen, dst_l1_addr)`
Computes the NOC address for `tile_id` via `addrgen.get_noc_addr()`, then
issues an async NOC read of `page_size` bytes into `dst_l1_addr`.  Under the
hood: programs the NOC read command buffer registers (target addr, local addr,
length, control) and triggers by writing 1 to the doorbell register.

**Source:** `dataflow_api.h:1113`  (InterleavedAddrGenFast overload)

### `noc_async_write_tile(tile_id, addrgen, src_l1_addr)`
Same as read but in reverse: programs NOC write command buffer and triggers.

**Source:** `dataflow_api.h:1276`

### `noc_async_read_barrier()`
Spins until `NOC_STATUS_READ_REQS_OUTSTANDING == 0` (reads issued == reads
completed), then calls `invalidate_l1_cache()`.

**Source:** `dataflow_api.h:1575`

### `noc_async_write_barrier()`
Spins until `nonposted_writes_acked == nonposted_writes_issued`, then calls
`invalidate_l1_cache()`.

**Source:** `dataflow_api.h:1605`

---

## 10  Compute Kernel API (trisc0/1/2)

These are used in the `K_COMPUTE` kernel of `add1.py`.  Each function is
dispatched to the correct TRISC by `#ifdef` guards -- the same source is
compiled three times with `COMPILE_FOR_TRISC=0/1/2`.

### `unary_op_init_common(in_cb, out_cb)`
One-time init for unary elementwise ops.  On TRISC0 (unpack): configures
unpacker HW for A->DST.  On TRISC1 (math): inits A->D datacopy and pack sync.
On TRISC2 (pack): configures packer HW.

**Source:** `tt_metal/include/compute_kernel_api/eltwise_unary/eltwise_unary.h:17`

### `copy_tile_init(in_cb)`
Re-inits unpacker+math for A->DST copy without full format reconfig.

**Source:** `tt_metal/include/compute_kernel_api/tile_move_copy.h:40`

### `binop_with_scalar_tile_init()`
Inits the SFPU for binary-op-with-scalar (add/mul/sub with a constant).
MATH thread only.

**Source:** `tt_metal/include/compute_kernel_api/eltwise_unary/binop_with_scalar.h:89`

### `tile_regs_acquire()`
MATH waits for PACK to release DST registers (hardware semaphore wait).

**Source:** `tt_metal/include/compute_kernel_api/reg_api.h:42`

### `cb_wait_front(in_cb, n)` (compute-side)
TRISC0 (unpack) waits for `n` tiles to be available in the input CB.  Same
semantic as the dataflow version but implemented via Tensix semaphore polling
(`ttsemwait`).

**Source:** `tt_metal/include/compute_kernel_api/cb_api.h`

### `copy_tile(in_cb, in_tile_idx, dst_tile_idx)`
TRISC0 unpacks tile from CB into SrcA; TRISC1 does a datacopy from SrcA to
DST[dst_tile_idx].  The two operations are synchronized by hardware
semaphores.

**Source:** `tt_metal/include/compute_kernel_api/tile_move_copy.h:82`

### `cb_pop_front(in_cb, n)` (compute-side)
TRISC0 signals that `n` tiles have been consumed from the input CB.

**Source:** `tt_metal/include/compute_kernel_api/cb_api.h`

### `add_unary_tile(dst_idx, scalar_param)`
TRISC1 (MATH): adds fp32-encoded `scalar_param` (e.g. `0x3f800000` = 1.0f) to
every element of DST[dst_idx] using the SFPU.  The scalar is split into two
16-bit halves and pushed as two config commands to `0xFFE40000`, then an
SFPU replay loop runs `sfpload -> sfpadd -> sfpnop -> sfpstore -> ttincrwc`
across all tile faces.

**Source:** `tt_metal/include/compute_kernel_api/eltwise_unary/binop_with_scalar.h:28`
**Disasm:** `compute_trisc1_math.S`, function `_ZN7ckernel4sfpu27calculate_binop_with_scalarILb0ELi0ELi8EEEvm` at `0x65D4`

### `tile_regs_commit()`
MATH signals it has finished writing DST (releases semaphore to PACK).

**Source:** `reg_api.h:75`

### `tile_regs_wait()`
PACK waits for MATH to commit DST (acquires semaphore).

**Source:** `reg_api.h:49`

### `cb_reserve_back(out_cb, n)` (compute-side)
TRISC2 (pack) waits for `n` free slots in the output CB.

**Source:** `tt_metal/include/compute_kernel_api/cb_api.h`

### `pack_tile(dst_idx, out_cb)`
TRISC2 (PACK): packs DST[dst_idx] into the output CB's reserved FIFO slot.
Configures pack source address, destination L1 address, triggers the packer
hardware, then waits for completion.

**Source:** `tt_metal/include/compute_kernel_api/pack.h:61`

### `cb_push_back(out_cb, n)` (compute-side)
TRISC2 signals that `n` tiles have been written to the output CB.

**Source:** `tt_metal/include/compute_kernel_api/cb_api.h`

### `tile_regs_release()`
PACK releases DST back to MATH (releases semaphore).

**Source:** `reg_api.h:80`

---

## 11  Profiler Macros (when `PROFILE=1`)

All defined in `tools/profiler/kernel_profiler.hpp`.  When profiling is
disabled, every macro expands to nothing.

### `DeviceProfilerInit()`
Resets the profiler write index, stack size, and trace count.  On BRISC,
initializes the profiler buffer if in trace mode.

**Source:** `kernel_profiler.hpp:739`

### `DeviceZoneScopedMainN(name)`
Constructs a RAII `profileScopeGuaranteed<hash>` that records a timestamp
pair (enter/exit) into the profiler ring buffer.  The `Guaranteed` variant
always records even if the profiler is paused.  Used for the top-level
firmware loop body (`"BRISC-FW"`, `"NCRISC-FW"`, `"TRISC-FW"`).

**Source:** `kernel_profiler.hpp:713`

### `DeviceZoneScopedN(name)`
Constructs a RAII `profileScope<hash>` that records a timestamp pair if the
profiler is active.  Used inside kernels (`"UNPACK"`, `"SFPU_ADD"`, `"PACK"`
in add1.py).

Each `profileScope` constructor and destructor:
1. Reads the 64-bit wall clock (`RISCV_DEBUG_REG_WALL_CLOCK_L/H`)
2. Packs a 64-bit record: `(hash << 48) | timestamp` (or similar encoding)
3. Writes it to the next slot in the profiler ring buffer in L1
4. Increments the write index

**Source:** `kernel_profiler.hpp:668`

### `DeviceValidateProfiler(enables)`
Calls `set_profiler_zone_valid(enables)`.  Marks whether the current zone's
data should be considered valid.

**Source:** `kernel_profiler.hpp:711`

### `DeviceZoneSetCounter(host_assigned_id)`
Stores a host-provided counter (typically the program index) alongside the
profiler data so the host can correlate profiler output with specific kernel
launches.

**Source:** `kernel_profiler.hpp:733`

### `DeviceIncrementTraceCount()` / `DeviceTraceOnlyProfilerInit()`
For trace replay mode: increments the trace event counter / initializes
minimal trace-only profiler state.

**Source:** `kernel_profiler.hpp:751,753`

### Profiler data path
When `PROFILE=1`, each RISC writes timestamped records into a per-RISC
section of an L1 profiler buffer.  After the kernel completes, the host reads
this buffer via the CQ sysmem DMA path and correlates timestamps with zone
hashes to build the flame chart.

---

## 12  Perf Counters (when `PROFILE=1` on TRISC1 only)

Defined inline in `firmware/trisc.cc` (guarded by
`PROFILE_PERF_COUNTERS && COMPILE_FOR_TRISC == 1`).

### `perf_counter_start()`
For each enabled counter group (FPU, PACK, UNPACK, L1_0, L1_1, INSTRN):
sets the L1 mux if needed, zeros the control register, sets continuous mode,
writes start/clear values.

### `perf_counter_stop_and_capture()`
Writes stop values to each counter, then reads the 64-bit counter output
registers for each descriptor in each group, packing them into
`perf_counter_samples[]`.

### `perf_counter_emit(sample_count)`
Writes each captured sample into the profiler ring buffer via
`kernel_profiler::timeStampedData<PERF_COUNTER_PROFILER_ID>()`.
