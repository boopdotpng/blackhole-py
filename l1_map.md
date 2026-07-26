# Worker L1 map

Each Tensix core has 1.5 MiB of shared L1: `[0x000000, 0x180000)`.
Ranges below are half-open.

| Address range | Size | Contents |
|---|---:|---|
| `[0x000000, 0x000004)` | 4 B | Boot jump into BRISC firmware |
| `[0x000004, 0x0032E0)` | 12.71 KiB | Hardware/control reservation; fixed words include `0x60`, `0x68–0x6B`, and `0x370–0x373` |
| `[0x0032E0, 0x0034E0)` | 512 B | Zeroed during firmware boot |
| `[0x0034E0, 0x003FD0)` | 2.73 KiB | Packed BRISC/NCRISC/TRISC firmware |
| `[0x003FD0, 0x004000)` | 48 B | Current-launch parameters: 12 × `u32` |
| `[0x004000, 0x00A000)` | 24 KiB | BRISC kernel slot |
| `[0x00A000, 0x00C000)` | 8 KiB | NCRISC kernel slot |
| `[0x00C000, 0x00F000)` | 12 KiB | TRISC0 kernel slot |
| `[0x00F000, 0x011000)` | 8 KiB | TRISC1 kernel slot |
| `[0x011000, 0x012000)` | 4 KiB | TRISC2 kernel slot |
| `[0x012000, 0x042000)` | 192 KiB | Persistent program arena: resident kernels followed by parameter templates |
| `[0x042000, 0x17FFE0)` | 1,271.97 KiB | Per-program CBs, scratch, L1 constants, and staged data |
| `[0x17FFE0, 0x180000)` | 32 B | Compact-trace runtime parameters: 8 × `u32` |

There are no gaps after the firmware-zeroed region. The constants live in
[fw/consts.py](/home/boop/tenstorrent/blackhole-py/fw/consts.py).

## Firmware and kernel sizing

Firmware roles are packed at 4-byte boundaries; L1 destinations do not require
64-byte alignment. Current firmware occupies 2,280 of the reserved 2,800 bytes.

Fixed kernel slots are sized per role instead of sharing the old 39.75 KiB
limit. The largest surviving Llama/RNG images are:

| Role | Largest image | Slot |
|---|---:|---:|
| BRISC | 20,532 B | 24 KiB |
| NCRISC | 5,832 B | 8 KiB |
| TRISC0 | 10,040 B | 12 KiB |
| TRISC1 | 5,484 B | 8 KiB |
| TRISC2 | 2,904 B | 4 KiB |

Ordinary launches write an image at the start of each role slot. Resident
launches instead patch each slot's first instruction to jump into the
persistent program arena.

## Persistent program arena

`cache_kernels()` packs unique per-core kernel images upward from `0x12000`,
retaining 64-byte image alignment. The current Llama trace uses at most 155,872
bytes on one core.

Parameter templates follow the highest kernel end, aligned to 32 bytes. A
template is an immutable launch recipe containing up to twelve parameter
values, their runtime-parameter IDs, and five jumps to resident role images.
BRISC selects a template from the low 24 bits of the GO word, materializes the
48-byte current-launch table at `0x3FD0`, patches the kernel entry jumps, and
then releases the worker RISCs.

Templates are 96 bytes and identical per-core payload sets are deduplicated.
The 228-launch Llama trace has 153 unique templates, consuming 14,688 bytes.
Kernels and templates together currently end at `0x3BA40`, leaving 25.44 KiB
free in the persistent arena.

## Per-program arena

`p.l1()`, explicit and internal CBs, and `p.l1_constant()` all share one
16-byte-aligned bump allocator over `[0x42000, 0x17FFE0)`. Constants differ
only in that static launch commands initialize their bytes. The current peak is
52 KiB in fused attention.

The DRAM transfer kernel also uses the beginning of this arena as standalone
staging scratch, for at most one 16 KiB tile.

## Prefetch and dispatch cores

Cores `(14,2)` and `(14,3)` are excluded from the worker set and repurpose L1:

- Prefetch: state near `0x1000`, descriptor queue at `[0x1100,0x1500)`, trace
  state near `0x1500`, and record staging at `[0x20000,0x30000)`.
- Dispatch: state near `0x1000`, dispatch ring at `[0x20000,0x160000)`, then
  timestamp, GO, and completion state near `0x160000`.

The `0xFFB…` ranges in `Firmware.LOCAL_MEMORY` are private RISC local RAM and
are not part of shared L1.
