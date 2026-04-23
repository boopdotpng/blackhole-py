# noc-atomics

**Source:** [`noc-atomics.md`](../specs/noc-atomics.md)

## Opcode table

### `NOC-AT.OPCODE.NOP`
§Atomic Opcode Table / 0x0

> Code 0x0 AT_NOP: No operation.

### `NOC-AT.OPCODE.INCR_GET`
§Atomic Opcode Table / 0x1

> Code 0x1 AT_INCR_GET: Increment + return old value (no wrap).

### `NOC-AT.OPCODE.INCR_GET_PTR`
§Atomic Opcode Table / 0x2

> Code 0x2 AT_INCR_GET_PTR: Increment with modular wrap.

### `NOC-AT.OPCODE.SWAP_MASK`
§Atomic Opcode Table / 0x3

> Code 0x3 AT_SWAP: Masked 16-bit-granule swap.

### `NOC-AT.OPCODE.CAS`
§Atomic Opcode Table / 0x4

> Code 0x4 AT_CAS: Compare-and-swap.

### `NOC-AT.OPCODE.GET_TILE_MAP`
§Atomic Opcode Table / 0x5

> Code 0x5 AT_GET_TILE_MAP: Tile map lookup.

### `NOC-AT.OPCODE.STORE_IND`
§Atomic Opcode Table / 0x6

> Code 0x6 AT_STORE_IND: Indirect store.

### `NOC-AT.OPCODE.SWAP_4B`
§Atomic Opcode Table / 0x7

> Code 0x7 AT_SWAP_4B: Full 32-bit swap.

### `NOC-AT.OPCODE.ACC`
§Atomic Opcode Table / 0x9

> Code 0x9 AT_ACC: Parallel accumulate (FP32/FP16/BF16/INT).

### `NOC-AT.TARGET.L1_ONLY`
§Intro ¶1

> Atomic operations cannot target MMIO addresses, DRAM addresses, or PCIe endpoints.

## INCR_GET_PTR fields

Provenance: firmware-inferred (not in BlackholeA0/NoC/Atomics.md).

### `NOC-AT.INCR_GET_PTR.INCR_FIELD`
_firmware: noc_parameters.h macros_

> NOC_AT_LEN_BE[9:6] = INCR (increment amount; 0 means 1).

### `NOC-AT.INCR_GET_PTR.WRAP_FIELD`
_firmware: noc_parameters.h macros_

> NOC_AT_LEN_BE[5:2] = WRAP (wrap boundary; 0=no wrap).

### `NOC-AT.INCR_GET_PTR.OLD_VAL_RETURNED`
_§INCR_GET_PTR Functional Model_

> Returns the old (pre-increment) value to NOC_RET_ADDR_LO.

### `NOC-AT.INCR_GET_PTR.WRAP_SEMANTIC`
_§INCR_GET_PTR Functional Model_

> new_val = old + incr; if wrap > 0 and new_val >= wrap then new_val = 0; target_mem.write32(targ_addr, new_val).

### `NOC-AT.INCR_GET.INCR_FROM_AT_DATA`
_BlackholeA0/NoC/Atomics.md §INCR_GET_

> The increment added to the target word is NOC_AT_DATA. NOC_AT_LEN_BE[9:6] is IntWidth (mask-width), not INCR.

### `NOC-AT.INCR_GET.NO_WRAP`
_§Difference table INCR_GET vs INCR_GET_PTR_

> INCR_GET has no wrap; WRAP field is ignored.

### `NOC-AT.CAS.COMPARE_FROM_AT_DATA`
§CAS Functional Model

> compare = noc_at_data & 0xFFFF; swap_val = (noc_at_data >> 16) & 0xFFFF.

### `NOC-AT.CAS.SUCCESS_PATH`
§CAS Functional Model

> If (original & 0xFFFF) == compare, write (original & 0xFFFF0000) | swap_val back to L1.

### `NOC-AT.CAS.FAILURE_PATH`
§CAS Functional Model

> If compare mismatches, L1 is unchanged.

### `NOC-AT.CAS.RETURN_ORIGINAL`
§CAS Functional Model

> Return original target value (for success/failure detection by software).

## SWAP

### `NOC-AT.SWAP.MASK_SELECTS_GRANULES`
§SWAP Mask Variant

> Writes NOC_AT_DATA to selected 16-bit granules within a 16-byte aligned region. Mask bit i selects granule at l1_base + i*2.

### `NOC-AT.SWAP.DATA_BROADCAST_PATTERN`
§SWAP Mask Variant code

> to_write[0] = at_data & 0xFFFF (written to even-index granules), to_write[1] = (at_data >> 16) & 0xFFFF (written to odd-index granules).

### `NOC-AT.SWAP.RETURN_ORIGINAL_32B`
§SWAP Mask Variant

> Returns the original 32-bit value at targ_addr.

### `NOC-AT.SWAP_4B.WRITE_32B`
_§SWAP Index Variant / SWAP_4B_

> Writes 32 bits of NOC_AT_DATA to L1Address = (targ_addr & ~0xF) + Ofs*4.

### `NOC-AT.SWAP_4B.RETURN_ORIGINAL`
_§SWAP Index Variant / SWAP_4B_

> Returns original 32-bit value at targ_addr.

## STORE_IND

### `NOC-AT.STORE_IND.INDIRECT_WRITE`
§Atomic Opcode Table / 0x6

> Reads pointer at targ_addr; writes NOC_AT_DATA to that pointer's target.

### `NOC-AT.ACC.FMT0.FP32_LANES`
§ACC Format Table / Fmt=0

> Fmt=0: L1 is 4× fp32; NOC_AT_DATA is 1× fp32 broadcast to 4.

### `NOC-AT.ACC.FMT0.FLUSH_DENORMAL`
§ACC Format Table / Fmt=0

> Fmt=0: denormals flushed to zero.

### `NOC-AT.ACC.FMT1.FP16_LANES`
§ACC Format Table / Fmt=1

> Fmt=1: L1 is 8× fp16; NOC_AT_DATA is 2× fp16 broadcast to 8 (2-way).

### `NOC-AT.ACC.FMT2.BF16_LANES`
§ACC Format Table / Fmt=2

> Fmt=2: L1 is 8× bf16; NOC_AT_DATA is 2× bf16 broadcast to 8 (2-way).

### `NOC-AT.ACC.FMT4.INT32_LANES`
§ACC Format Table / Fmt=4

> Fmt=4: L1 is 4× u32 (wrapping two's complement); NOC_AT_DATA broadcast to 4.

### `NOC-AT.ACC.FMT7.INT8_SAT`
§ACC Format Table / Fmt=7

> Fmt=7: L1 is 16× u8 (saturating); NOC_AT_DATA is 4× u8 broadcast to 16.

### `NOC-AT.ACC.ALIGNMENT`
§Emulator Implementation Notes #2

> All atomic operations operate on 16-byte aligned addresses (targ_addr & ~0xF).

### `NOC-AT.ACC.SAT_DIS_FLAG`
_§ACC Usage (NOC_AT_ACC_SAT_DIS)_

> NOC_AT_ACC_SAT_DIS bit disables saturation.

### `NOC-AT.ACC.RESPONSE_UNDEFINED`
§Response Handling ¶final

> For ACC, the response contains an undefined value — fire-and-forget.

## Response handling

### `NOC-AT.RESP.WRITES_TO_RET_ADDR`
§Response Handling ¶1

> All atomic operations (except ACC) return the original value to NOC_RET_ADDR_LO if NOC_CMD_RESP_MARKED is set.

### `NOC-AT.RESP.COUNTER_INCREMENT`
§Response Handling code block

> NIU_MST_ATOMIC_RESP_RECEIVED += 1 on response arrival.

### `NOC-AT.RESP.POSTED_NO_WRITE`
§Response Handling ¶1

> If NOC_CMD_RESP_MARKED is clear, no response is generated and NIU_RET_ADDR_LO is not written.

## Multicast

### `NOC-AT.MCAST.PER_TILE`
§Emulator Implementation Notes #4

> Atomic operations can be multicast; each target tile performs independently.

## Atomicity invariant

### `NOC-AT.ATOMICITY`
§Emulator Implementation Notes #1

> In a single-threaded synchronous emulator, all operations are inherently atomic. No special locking is needed.
