The shared L1 on each Tensix core is 1.5 MiB: `[0x000000, 0x180000)`. The map below uses half-open ranges, so the last valid byte is `end - 1`.

### Normal worker-core L1 map

| Address range | Size | Contents |
|---|---:|---|
| `[0x000000, 0x000004)` | 4 B | Boot instruction jumping into BRISC firmware |
| `[0x000004, 0x0032E0)` | — | Mostly unmanaged; fixed control words live at `0x60`, `0x68–0x6B`, and `0x370–0x373` |
| `[0x0032E0, 0x0034E0)` | 512 B | Explicitly zeroed during firmware boot |
| `[0x0034E0, 0x003840)` | 864 B | Unused gap |
| `[0x003840, 0x003EF0)` | 1,712 B | BRISC firmware partition |
| `[0x003EF0, 0x003FC8)` | 216 B | NCRISC firmware partition |
| `[0x003FC8, 0x004090)` | 200 B | TRISC0 firmware partition |
| `[0x004090, 0x004158)` | 200 B | TRISC1 firmware partition |
| `[0x004158, 0x004220)` | 200 B | TRISC2 firmware partition |
| `[0x004220, 0x004240)` | 32 B | Unused gap |
| `[0x004240, 0x005100)` | 3.69 KiB | Per-launch program parameter table, up to 944 32-bit slots |
| `[0x005100, 0x00F000)` | 39.75 KiB | Current BRISC kernel slot |
| `[0x00F000, 0x018F00)` | 39.75 KiB | Current NCRISC kernel slot |
| `[0x018F00, 0x022E00)` | 39.75 KiB | Current TRISC0 kernel slot |
| `[0x022E00, 0x02CD00)` | 39.75 KiB | Current TRISC1 kernel slot |
| `[0x02CD00, 0x036C00)` | 39.75 KiB | Current TRISC2 kernel slot |
| `[0x036C00, 0x037000)` | 1 KiB | Unused/alignment gap |
| `[0x037000, 0x050000)` | 100 KiB | Default per-program data arena |
| `[0x050000, 0x0F0000)` | 640 KiB | Per-core resident kernel cache |
| `[0x0F0000, 0x15FF00)` | 447.75 KiB | Optional high per-program data arena |
| `[0x15FF00, 0x15FF40)` | 64 B | Compact-trace runtime parameters, 16 × `u32` |
| `[0x15FF40, 0x160000)` | 192 B | Reserved gap |
| `[0x160000, 0x170000)` | 64 KiB | Resident parameter templates: 512 × 128-byte entries |
| `[0x170000, 0x180000)` | 64 KiB | Currently unused |

The authoritative constants are in [fw/consts.py](/home/boop/tenstorrent/blackhole-py/fw/consts.py:8).

### What uses the data arenas

All of these share the same bump allocator in allocation order:

- `p.l1(...)`: caller-managed temporary/persistent L1 scratch.
- `p.cb(...)` and internal CBs: circular-buffer tile storage.
- `p.l1_constant(...)`: immutable constants; these are uploaded before execution.
- The DRAM transfer kernel separately uses `0x37000` as fixed staging scratch, up to one 16 KiB tile.

Programs allocate from `[0x37000, 0x50000)`. The upper data arena remains
unused. See [program.py](/home/boop/tenstorrent/blackhole-py/program.py),
[ttk/cb.py](/home/boop/tenstorrent/blackhole-py/ttk/cb.py), and
[fw/dram.py](/home/boop/tenstorrent/blackhole-py/fw/dram.py).

These are reservations, not initialized memory: `p.l1()` and CB allocation do not clear or upload anything. Kernel/NoC operations populate them later, so unused bytes may contain stale data.

### Kernel and parameter behavior

Ordinary launches write each kernel image at the beginning of its fixed 39.75 KiB role slot. They do not clear the unused remainder of the slot. Runtime parameters similarly write only the used prefix beginning at `0x4240`. See [program.py](/home/boop/tenstorrent/blackhole-py/program.py:346).

`cache_kernels()` packs unique role images upward from `0x50000`, 64-byte aligned, independently per core. Parameter templates then patch the fixed kernel-slot entry instructions to jump into those resident images. See [device.py](/home/boop/tenstorrent/blackhole-py/device.py:334).

Each 128-byte template contains:

| Template offset | Contents |
|---|---|
| `+0x00` | Parameter count |
| `+0x04…+0x33` | Up to twelve 32-bit parameter values |
| `+0x34…+0x3F` | Twelve runtime-parameter IDs |
| `+0x40…+0x53` | Five resident-kernel jump instructions |
| `+0x54…+0x7F` | Zero padding |

One implementation hazard: `cache_kernels()` currently resets its per-core cache pointer to `0x50000` on every call. Calling it again with different programs can overwrite previously resident images even though the old `_resident_programs` entries remain. It should currently be treated as a single installation batch.

### Prefetch and dispatch cores are different

Cores `(14,2)` and `(14,3)` are excluded from the worker set and repurpose L1:

- Prefetch core: state near `0x1000`, 256-entry descriptor queue at `[0x1100,0x1500)`, trace state near `0x1500`, and a 64 KiB record staging buffer at `[0x20000,0x30000)`.
- Dispatch core: state near `0x1000`, a 1.25 MiB dispatch ring at `[0x20000,0x160000)`, then timestamp/GO/completion scratch in approximately `[0x160000,0x160074)`.

Those definitions are in [cq.py](/home/boop/tenstorrent/blackhole-py/cq.py:13). The `0xFFB…` local-RISC allocator ranges in `Firmware.LOCAL_MEMORY` are private RISC local RAM, not part of this shared 1.5 MiB L1 map.
