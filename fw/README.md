# Blackhole HCQ firmware

`queue.py` and `dma.py` implement the command processor and the DMA service for tinygrad HCQ2. The service cores are prefetch `(14, 2)`, dispatch `(14, 3)`, and DMA `(14, 4)` (BRISC/NoC0 and NCRISC/NoC1). `abi.py` defines the packet and service-memory ABI.

Build with Python from the repository root:

```sh
python -m fw.build build/bh_hcq_v2.bin
```

The binary contains an 8-byte `BHCQ0002` ABI identifier, nine little-endian u32 image lengths, and the five resident worker images followed by prefetch, dispatch, DMA BRISC, and DMA NCRISC. The loader validates all image boundaries. Build output is independent of the card and pinned-memory address. `build.unpack` accepts a binary for `Device.boot(images=...)`.

Before GO, the host writes these values on each service core:

| L1 address | Value |
| --- | --- |
| `0x1080` | pinned sysmem NoC middle address |
| `0x1084` | enabled DRAM bank count |
| `0x10a0` | eight NoC0 DRAM endpoint coordinates, u32 each |
| `0x10c0` | eight NoC1 DRAM endpoint coordinates, u32 each |

The original `llama3/` snapshot remains unchanged and supplies the assembler, NoC emitters, and resident workers. `build.py` runs it in an isolated interpreter and loads the new service sources. TRISC fusion/cache policy and instruction-prefetch settings are preserved; worker entry selection is extended as described below. `llama3-manifest.json` describes the original snapshot, not this new binary.

## Command stream

Records are 64-byte aligned and use the existing 16-byte `<BxHIII` header: opcode, target count, record size, address, data size. An individual record is at most 64 KiB. The 4 MiB host issue ring has monotonic 64-bit read/put counters. The host publishes bytes before its UC MMIO doorbell store.

| Opcode | Operation |
| --- | --- |
| 0 | PAD |
| 1 / 2 | unicast / multicast L1 writes |
| 3 | RUN worker images and wait for all selected workers |
| 4 | existing DRAM-resident record indirection |
| 5 | write an ordered 64-bit completion value to sysmem |
| 6 | indirect command buffer: sysmem address in header, byte length at +16 |
| 7 | existing page/bank-prefix DMA descriptor |
| 8 | WAIT sysmem u64: address in header, value at +16, equality flag at +24 (otherwise unsigned >=) |
| 9 | write an ordered 64-bit clock timestamp to the exact sysmem address in the header |
| 10 | byte DMA: source u64 at +16, destination u64 at +24, byte count u32 at +32 |

SIGNAL writes exactly eight bytes so HCQ2's adjacent host timeline value is not overwritten. The Python `Signal` convenience wrapper emits TIMESTAMP at signal+8 followed by SIGNAL, preserving its existing completion/timing API.

Indirect streams reside in the same pinned sysmem aperture as the issue ring. They cannot nest. Retain their storage until completion, and do not patch a stream while a previous invocation still uses it. tinygrad HCQ2 provides that fence and storage lifetime.

One ordered dispatch FIFO fronts compute and DMA. Copies are queued asynchronously to both DMA RISCs; ordinary dispatch commands and WAIT drain earlier copies. SIGNAL and TIMESTAMP join the same DMA descriptor stream and complete after both engines. Separate logical compute/copy queues are deliberately not advertised to HCQ2.

## DMA addresses

- Bit 63 set: logical DRAM byte address, striped in 2048-byte pages across enabled banks. Bank = page % banks; bank address = (page // banks)*2048 + byte offset.
- PCIe address: the tt-kmd PIN_PAGES NoC address plus an offset within the pinned allocation.
- L1: `((x | y<<6) << 32) | l1_address`, using virtual NoC coordinates.

Full-stripe, aligned host/DRAM copies use the existing dual-engine gather/scatter implementation: 64 KiB per-bank staging, multiple PCIe requests in flight, and contiguous DRAM batches. Other copies split at logical page boundaries and alternate chunks across the engines. Mismatched low-six-bit endpoint offsets are realigned in L1; this path prioritizes byte-view correctness over peak bandwidth. Copies must not overlap. Each descriptor supports less than 4 GiB; larger transfers must be split.

## Validation

```sh
python -m pytest tests/test_hcq_firmware.py tests/timing/test_firmware_cache.py --bh-hardware --bh-device 0 -q
```

Hardware checks cover topology-independent builds, indirect execution, 64-bit equality waits, timestamps, unaligned copies above the 4 GiB logical address boundary, and resident worker cache/fusion settings. tinygrad's `test/device/test_tt.py` additionally covers allocation reclamation, byte views, L1 and DRAM copies, parameterized worker dispatch, TinyJit with new input/output addresses, and issue-ring wraparound.

Worker firmware loads its entry PC from the launch-owned five-word table at `TensixL1.WORKER_ENTRY_BASE`. Boot initializes direct-launch slots; `Program` restores those entries, while `GridProgram` supplies common resident entry addresses without trampolines. Grid launches write logical `(ri, ci)` to the aligned `GRID_RANK_BASE` and broadcast common parameters. Rebuild older firmware blobs for this ABI.
