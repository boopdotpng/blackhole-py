# NOC Atomic Operations

The NIU (Network Interface Unit) supports atomic read-modify-write operations against L1 memory of Tensix and Ethernet tiles. Atomic operations cannot target MMIO addresses, DRAM addresses, or PCIe endpoints. They can be unicast or multicast (broadcast to a rectangle of tiles, performed independently on each).

The existing niu.md documents the basic INCR_GET atomic used for software semaphore signaling. This document covers the remaining atomic operations: INCR_GET_PTR, CAS, SWAP, and ACC.


## Atomic Opcode Table

The atomic operation is encoded in `NOC_AT_LEN_BE[15:12]`:

| Code | Symbol | Description |
|------|--------|-------------|
| 0x0 | `AT_NOP` | No operation |
| 0x1 | `AT_INCR_GET` | Increment + return old value (documented in niu.md) |
| 0x2 | `AT_INCR_GET_PTR` | Increment with modular wrap |
| 0x3 | `AT_SWAP` | Masked 16-bit-granule swap |
| 0x4 | `AT_CAS` | Compare-and-swap |
| 0x5 | `AT_GET_TILE_MAP` | Tile map lookup |
| 0x6 | `AT_STORE_IND` | Indirect store |
| 0x7 | `AT_SWAP_4B` | Full 32-bit swap |
| 0x8 | Zaamo | RISC-V Zaamo atomic operations via NOC |
| 0x9 | `AT_ACC` | Parallel accumulate (FP32/FP16/BF16/INT) |

The constants are defined in `noc_parameters.h`:
```c
// From tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_parameters.h
#define NOC_AT_INS_NOP          0x0
#define NOC_AT_INS_INCR_GET     0x1
#define NOC_AT_INS_INCR_GET_PTR 0x2
#define NOC_AT_INS_SWAP         0x3
#define NOC_AT_INS_CAS          0x4
#define NOC_AT_INS_SWAP_4B      0x7
#define NOC_AT_INS_ACC          0x9
```


## NOC_AT_LEN_BE Field Layout

The `NOC_AT_LEN_BE` register encodes the atomic operation and its parameters. The exact field layout depends on the operation:

### For INCR_GET / INCR_GET_PTR:
```
[15:12] = INS     (opcode: 0x1 or 0x2)
[11:10] = IND_32_SRC
[9:6]   = INCR    (increment amount; 0 means 1)
[5:2]   = WRAP    (wrap boundary for INCR_GET_PTR; 0=no wrap)
[1:0]   = IND_32  (destination word offset within 16-byte aligned region)
```

### For CAS:
```
[15:12] = INS     (0x4)
[11:8]  = SetVal  (value to write if comparison succeeds)
[7:4]   = CmpVal  (value to compare against)
[3:2]   = Ofs     (word offset)
[1:0]   = IND_32
```

### For SWAP (mask variant):
```
[15:12] = INS     (0x3)
[11:4]  = Mask    (8 bits — selects which 16-bit granules to write)
[3:2]   = (unused)
[1:0]   = IND_32
```

### For ACC (parallel addition):
```
[15:12] = INS     (0x9)
[2:0]   = Fmt     (data format selector)
```


## INCR_GET_PTR — Atomic Increment with Wrap (opcode 0x2)

Increments a 32-bit value at the target L1 address, returning the old value. If the new value reaches or exceeds the wrap boundary, it resets to 0. This is the building block for circular buffer pointer management.

### Functional Model

```python
def atomic_incr_get_ptr(target_mem, targ_addr, at_len_be, noc_at_data):
    """
    at_len_be fields:
      INS       = (at_len_be >> 12) & 0xF  = 0x2
      INCR      = (at_len_be >> 6) & 0xF   (0 means increment by 1)
      WRAP      = (at_len_be >> 2) & 0xF   (0 means no wrap)
      IND_32    = at_len_be & 0x3
    """
    incr = (at_len_be >> 6) & 0xF
    if incr == 0:
        incr = 1
    wrap = (at_len_be >> 2) & 0xF

    # Read old value
    old_val = target_mem.read32(targ_addr)

    # Compute new value
    new_val = old_val + incr
    if wrap > 0 and new_val >= wrap:
        new_val = 0

    # Write new value
    target_mem.write32(targ_addr, new_val & 0xFFFFFFFF)

    # Return old value to NOC_RET_ADDR_LO (if NOC_CMD_RESP_MARKED)
    return old_val
```

### Tensix Coprocessor Analog: ATINCGETPTR (opcode 0x62)

ATINCGETPTR is a Scalar Unit instruction that implements FIFO push/pop atomics. It checks empty/full conditions before incrementing:
- `Ofs=0` (pop): increments read pointer if FIFO is not empty
- `Ofs=1` (push): increments write pointer if FIFO is not full

Retries in hardware if the FIFO condition is not met; takes at least 15 cycles per attempt.

### Difference from INCR_GET

| Feature | INCR_GET (0x1) | INCR_GET_PTR (0x2) |
|---------|----------------|---------------------|
| Wrap | No wrap | Wraps to 0 when `new_val >= wrap` |
| WRAP field | Ignored | Controls wrap boundary |
| Use case | Simple counters, semaphores | Circular buffer pointers |


## CAS — Compare-And-Swap (opcode 0x4)

Atomically reads the target word, compares it against a value, and if equal, replaces it with a new value. Returns the original value so software can determine whether the swap succeeded.

### Functional Model

```python
def atomic_cas(target_mem, targ_addr, at_len_be, noc_at_data):
    """
    at_len_be fields:
      INS     = (at_len_be >> 12) & 0xF  = 0x4
      SetVal  = (at_len_be >> 8) & 0xF   (value to write on match — 4-bit NOC CAS)
      CmpVal  = (at_len_be >> 4) & 0xF   (value to compare against — 4-bit NOC CAS)
      Ofs     = (at_len_be >> 2) & 0x3   (word offset)
    """
    # Wider CAS uses NOC_AT_DATA for compare/set values:
    compare = noc_at_data & 0xFFFF
    swap_val = (noc_at_data >> 16) & 0xFFFF

    # Read original value at target address
    result = target_mem.read32(targ_addr)

    # Compare against low 16 bits
    l1_addr = (targ_addr & ~0xF) + ((at_len_be >> 2) & 0x3) * 4
    original = target_mem.read32(l1_addr)

    if (original & 0xFFFF) == compare:
        target_mem.write32(l1_addr, (original & 0xFFFF0000) | swap_val)

    # Return original value at targ_addr (for success/failure detection)
    return result
```

The ISA documentation specifies the full functional model as:
```c
atomic {
    Result = *(uint32_t*)NOC_TARG_ADDR_LO;
    uint32_t* L1Address = (uint32_t*)((NOC_TARG_ADDR_LO & ~0xf) + (NOC_AT_LEN_BE.Ofs * 4));
    uint32_t OriginalValue = *L1Address;
    if (OriginalValue == NOC_AT_LEN_BE.CmpVal) {
        *L1Address = NOC_AT_LEN_BE.SetVal;
    }
}
```

### Tensix Coprocessor Analog: ATCAS (opcode 0x64)

ATCAS is a Scalar Unit instruction that spins on an L1 address until a 4-bit field equals `CmpVal`, then writes `SetVal`. Takes at least 15 cycles per attempt. Documented in the Wormhole ISA; may not exist on Blackhole.


## SWAP — Atomic Swap (opcodes 0x3 and 0x7)

Two variants: mask-based (0x3) and full 32-bit (0x7).

### Mask Variant (opcode 0x3)

Writes `NOC_AT_DATA` to selected 16-bit granules within a 16-byte aligned region of L1. An 8-bit mask selects which of the 8 possible 16-bit slots to overwrite. Returns the original 32-bit value at the target address.

```python
def atomic_swap_mask(target_mem, targ_addr, at_len_be, noc_at_data):
    """
    at_len_be fields:
      INS   = 0x3
      Mask  = (at_len_be >> 4) & 0xFF   (8 bits, one per 16-bit granule)
    """
    mask = (at_len_be >> 4) & 0xFF

    # Read original value
    result = target_mem.read32(targ_addr)

    # Write selected 16-bit granules
    l1_base = targ_addr & ~0xF
    to_write = [noc_at_data & 0xFFFF, (noc_at_data >> 16) & 0xFFFF]
    for i in range(8):
        if mask & (1 << i):
            addr = l1_base + i * 2
            target_mem.write16(addr, to_write[i & 1])

    return result
```

### Index Variant / SWAP_4B (opcode 0x7)

Writes the full 32 bits of `NOC_AT_DATA` to the word at `L1Address = (NOC_TARG_ADDR_LO & ~0xF) + (Ofs * 4)`. Returns the original 32-bit value at `NOC_TARG_ADDR_LO`.

```python
def atomic_swap_4b(target_mem, targ_addr, at_len_be, noc_at_data):
    result = target_mem.read32(targ_addr)
    ofs = (at_len_be >> 2) & 0x3
    l1_addr = (targ_addr & ~0xF) + ofs * 4
    target_mem.write32(l1_addr, noc_at_data & 0xFFFFFFFF)
    return result
```

### Tensix Coprocessor Analog: ATSWAP (opcode 0x63)

ATSWAP is a Scalar Unit instruction that writes up to 128 bits from GPRs to L1 using a mask (8 bits × 16-bit granules). Despite the name, it does **not** return the old value to a GPR. Takes ~3 cycles to occupy ThCon; sustained throughput ≤ 1 per 12 cycles.


## ACC — Parallel Accumulate (opcode 0x9)

The most complex atomic operation. Performs SIMD addition of `NOC_AT_DATA` (broadcast) onto 16 bytes of L1, with format-dependent interpretation. Always operates on a full 16-byte aligned region — no lane mask is available.

### Format Table

| Fmt | L1 interpretation | NOC_AT_DATA interpretation | Arithmetic |
|-----|-------------------|---------------------------|------------|
| 0 | 4× fp32 | 1× fp32, broadcast to 4 | Flush denormals |
| 1 | 8× fp16 | 2× fp16, broadcast to 8 | Flush denormals |
| 2 | 8× bf16 | 2× bf16, broadcast to 8 | Flush denormals |
| 4 | 4× u32 | 1× u32, broadcast to 4 | Wrapping two's complement |
| 7 | 16× u8 | 4× u8, broadcast to 16 | Saturating |

Formats 8–15 mirror 0–7 with minor behavioral differences (e.g., format 12 = INT32 wrapping, format 13 = INT32 wrapping, format 15 = INT8 wrapping instead of saturating).

### Functional Model

```python
import struct

def atomic_acc(target_mem, targ_addr, at_len_be, noc_at_data):
    fmt = at_len_be & 0x7
    l1_addr = targ_addr & ~0xF
    l1_bytes = target_mem.read_bytes(l1_addr, 16)
    at_bytes = struct.pack('<I', noc_at_data)

    if fmt == 0:       # FP32: 4 lanes
        for i in range(4):
            old = struct.unpack_from('<f', l1_bytes, i*4)[0]
            add = struct.unpack_from('<f', at_bytes, 0)[0]   # broadcast
            result = flush_denormal(old + add)
            struct.pack_into('<f', l1_bytes, i*4, result)

    elif fmt == 1:     # FP16: 8 lanes
        for i in range(8):
            old = fp16_to_float(struct.unpack_from('<H', l1_bytes, i*2)[0])
            add = fp16_to_float(struct.unpack_from('<H', at_bytes, (i & 1)*2)[0])  # 2-way broadcast
            result = float_to_fp16(flush_denormal(old + add))
            struct.pack_into('<H', l1_bytes, i*2, result)

    elif fmt == 2:     # BF16: 8 lanes
        for i in range(8):
            old = bf16_to_float(struct.unpack_from('<H', l1_bytes, i*2)[0])
            add = bf16_to_float(struct.unpack_from('<H', at_bytes, (i & 1)*2)[0])
            result = float_to_bf16(flush_denormal(old + add))
            struct.pack_into('<H', l1_bytes, i*2, result)

    elif fmt == 4:     # INT32: 4 lanes, wrapping
        for i in range(4):
            old = struct.unpack_from('<i', l1_bytes, i*4)[0]
            add = struct.unpack_from('<i', at_bytes, 0)[0]
            result = (old + add) & 0xFFFFFFFF
            struct.pack_into('<I', l1_bytes, i*4, result)

    elif fmt == 7:     # INT8: 16 lanes, saturating
        for i in range(16):
            old = l1_bytes[i]
            add = at_bytes[i & 3]  # 4-way broadcast
            result = min(255, max(0, old + add))  # unsigned saturating
            l1_bytes[i] = result

    target_mem.write_bytes(l1_addr, l1_bytes)

    # ACC does not return a meaningful value to NOC_RET_ADDR_LO
    return None  # UndefinedValue
```

### Usage

ACC is used for distributed accumulation in multi-core operations — each core atomically adds its partial result to a shared L1 buffer without needing locks:

```c
// From tt-metal firmware (noc.c)
NOC_AT_INS(NOC_AT_INS_ACC) | NOC_AT_ACC_FORMAT(data_format) | NOC_AT_ACC_SAT_DIS(disable_saturation)
```

### ACC Format Constants

```c
#define NOC_AT_ACC_FP32       0x0
#define NOC_AT_ACC_FP16_A     0x1
#define NOC_AT_ACC_FP16_B     0x2
#define NOC_AT_ACC_INT32      0x3
#define NOC_AT_ACC_INT32_COMPL 0x4
#define NOC_AT_ACC_INT32_UNS  0x5
#define NOC_AT_ACC_INT8       0x6
```


## Response Handling

All atomic operations (except ACC) return a result to `NOC_RET_ADDR_LO` if `NOC_CMD_RESP_MARKED` is set:

```c
// At the target tile, after the atomic completes:
*(uint32_t*)NOC_RET_ADDR_LO = Result;    // original value at target address
memory_barrier;
atomic {
    NIUCounters.NIU_MST_ATOMIC_RESP_RECEIVED += 1;
    NIUCounters.NIU_MST_REQS_OUTSTANDING_ID(NOC_PACKET_TRANSACTION_ID) -= 1;
}
```

Software polls `NIU_MST_ATOMIC_RESP_RECEIVED` or the outstanding-requests counter to determine when the response has arrived and the result is available.

For ACC, the response contains an undefined value — the operation is fire-and-forget from the initiator's perspective.


## Emulator Implementation Notes

1. **Atomicity**: In a single-threaded synchronous emulator, all operations are inherently atomic. No special locking is needed.
2. **Address alignment**: All atomic operations operate on 16-byte aligned addresses (`targ_addr & ~0xF`). The `Ofs` / `IND_32` fields select a word within that 16-byte region.
3. **Response counters**: The emulator must increment `NIU_MST_ATOMIC_RESP_RECEIVED` and decrement the per-transaction outstanding counter when the response is generated.
4. **Multicast**: Atomic operations can be multicast. Each target tile performs the operation independently. The response comes from the first tile in the multicast range.


## Source References

| Source | Path |
|--------|------|
| NOC Atomics ISA (BH) | `tt-isa-documentation/BlackholeA0/NoC/Atomics.md` |
| ATINCGET ISA (WH) | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ATINCGET.md` |
| ATINCGETPTR ISA (WH) | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ATINCGETPTR.md` |
| ATCAS ISA (WH) | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ATCAS.md` |
| ATSWAP ISA (WH) | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ATSWAP.md` |
| Python emulator (atomics) | `blackhole-py/emu/noc.py` |
| Python tests (atomics) | `blackhole-py/emu/tests/test_noc.py` |
| NOC parameter constants | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_parameters.h` |
| Firmware NOC API | `tt-metal/tt_metal/hw/firmware/src/tt-1xx/blackhole/noc.c` |
| NIU emulator spec | `emu-specs/niu.md` |
| Existing INCR_GET docs | `emu-specs/niu.md` §13 (Atomic Operations) |
