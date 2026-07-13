# Device-side tilize and untilize on Blackhole

## Conclusion

Blackhole can tilize row-major input while unpacking and untilize a tile while
packing. `tt-metal` exposes these paths as `tilize_init`/`tilize_block` and
`pack_untilize_dest_init`/`pack_untilize_dest`.

These are not single flags on a circular buffer. A CB has an address, page
size, format, and face geometry; the operation consuming or producing it
decides whether its bytes are row-major or tiled. Both conversions require a
coordinated engine mode, MOP, address-counter setup, and (for pack-untilize on
Blackhole) math-thread DEST remapping.

For the current one-tile BF16 `add1`, the required geometry is especially
simple:

| Property | Value |
|---|---:|
| Matrix | `32 x 32` |
| Bytes | `2048` |
| Faces | `4 x (16 x 16)` |
| Input column-tile count, `ct_dim` | `1` |
| Pack block width, `block_ct_dim` | `1` |
| Complete output width, `full_ct_dim` | `1` |
| Pack block height | `1` |

The practical answer is therefore **yes**, but `Unpack.init(..., tilize=True)`
and `Pack.init(..., untilize=True)` must each select a complete configuration;
merely setting one register bit on the existing tile path is insufficient.

This investigation uses `tt-metal` commit
[`da4b5148e26bc7cf1aa40b05b38751b20fe7f743`](https://github.com/tenstorrent/tt-metal/tree/da4b5148e26bc7cf1aa40b05b38751b20fe7f743).
Local source links below assume `tt-metal` and `blackhole-py-rewrite` remain
sibling directories.

## What “tilize on unpack” means

The input CB contains ordinary row-major rows. For a BF16 `32 x 32` matrix its
2048 bytes are:

```text
row 0:  32 BF16 values
row 1:  32 BF16 values
...
row 31: 32 BF16 values
```

The unpacker reads that row-major block and presents a normal four-face tile to
SrcA/Dest. There is no second, tiled input CB in the `add1` design: tilization
happens in the unpack-to-SrcA transfer.

The high-level `tt-metal` initialization proves that this is a coordinated
three-thread mode. It selects unpack-tilize on TRISC0 and a matching
`PackMode::Tilize` A-to-Dest copy on TRISC1; its TRISC2 setup is needed by the
standalone tilize operator because that operator writes a separate tiled CB.
See [`tilize_init`](../../tt-metal/tt_metal/hw/inc/api/compute/tilize.h) and its
calls to `llk_unpack_tilize_init` and
`llk_math_eltwise_unary_datacopy_init<..., PackMode::Tilize>`.

`add1` only needs the first two parts. Its existing computation already leaves
the result in Dest for the output packer, so it does not need the standalone
tilize operator's intermediate output CB or ordinary tile pack.

### Required unpack configuration for BF16 `add1`

The authoritative implementation is
[`_llk_unpack_tilize_init_`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_tilize.h).
The important settings for `ct_dim=1`, `face_r_dim=16`, `num_faces=4`, and a
non-narrow BF16 tile are:

| Setting | BF16 one-tile value | Reason |
|---|---:|---|
| `Haloize_mode` | `0` | Do not transpose X/Y. |
| `Throttle_mode` | `2` | Same throttle selected by the LLK. |
| `Tileize_mode` | `1` | Enables row-major addressing in the unpacker. |
| `Shift_amount` context 0 | `4` | `32 BF16 * 2 bytes / 16 bytes`. |
| unpack A X end | `1023` | `16 rows/face * 4 faces * 16 columns - 1`. |
| tile X dimension | `1024` | Flatten all four faces for the Blackhole workaround. |
| tile Z dimension | `1` | X covers the complete tile. |

With the current register definitions, unpack config word 0 becomes
`0x0004_0225`: BF16 format `5`, throttle `2`, `Tileize_mode` bit `0x200`, and
shift amount `4`. The field layout is defined in
[`unpack_config_t`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/common/inc/cunpack_common.h),
and the hardware mask confirms that `Tileize_mode` is bit 9 in
[`cfg_defines.h`](../../tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h).

The non-8-bit Blackhole path also changes the descriptors used by the current
`Unpack.init` implementation:

```text
THCON_SEC0_REG5_Tile_x_dim_cntx01 = 0x0400_0400
THCON_SEC0_REG0_TileDescriptor    = existing low fields | 0x0400_0000
THCON_SEC0_REG0_TileDescriptor_1  = existing low fields | 0x0001_0000
```

The exact low fields should continue to come from the format/tile descriptor
builder rather than being copied as constants.

### Required unpack MOP and math copy

The ordinary unpack MOP in `ttk/unpack.py` walks four faces independently. The
BF16 tilize MOP does not. Blackhole's workaround configures an outer count of
one and an inner count of one, starts with an SrcA `UNPACR` covering the
flattened tile, and uses the SrcB dvalid/zero-source NOP as its body. Port
[`_llk_unpack_tilize_mop_config_`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_tilize.h)
rather than adding `Tileize_mode` to `UNPACK_SRC_A_MOP`.

The execution sequence in
[`_llk_unpack_tilize_`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_tilize.h)
is otherwise close to `Unpack.to_src_a`: clear Z/W, wait for an unpack context,
program the row-major base address, post `UNPACK_SYNC`, stall on TRISC config,
run the MOP, wait for completion, and switch context.

The math copy must also use tilize mode. For BF16 this changes the datacopy MOP
from four outer iterations by two eight-row moves to one outer iteration by
eight eight-row moves. That behavior is selected by `PackMode::Tilize` in
[`_llk_math_eltwise_unary_datacopy_init_`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_math_eltwise_unary_datacopy.h).
After that copy, the existing SFPU add-immediate program can operate on the
normal tile in Dest.

## What “untilize on pack” means

The packer consumes the normal four-face tile in Dest and writes 32 contiguous
row-major rows to the output CB. For one BF16 tile, each output row is 64 bytes
and the whole CB page is still 2048 bytes.

The relevant public API is
[`pack_untilize_dest_init<1, 1>` and `pack_untilize_dest<1, 1>`](../../tt-metal/tt_metal/hw/inc/api/compute/pack_untilize.h).
This is the correct variant for `add1` because the math/SFPU kernel has already
placed the value in Dest. `pack_untilize_init`/`pack_untilize_block` is instead
for reading a tiled input CB back through unpack and math before untilizing it.

### Required Blackhole DEST flags

Pack-untilize does have two literal Blackhole flags, but they are only one part
of the mode:

```text
DEST_ACCESS_CFG.swizzle_32b = 1   # bit 0
DEST_ACCESS_CFG.remap_addrs = 1   # bit 1
```

Together they are `DEST_ACCESS_CFG |= 0x3`. `tt-metal` sets both on the math
thread in
[`_llk_math_reconfig_remap_`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_math_common.h),
and `pack_untilize_dest_init` explicitly invokes that helper on Blackhole.
The synchronization in that helper matters: it waits for in-flight Dest access
and prior packs before changing the mapping.

In `blackhole-py-rewrite`, TRISC1 and TRISC2 are emitted as separate Python
kernel functions. Consequently, this configuration should be owned by the
math-side API (for example `Math.initialize(dest_remap=True)`) and completed
before the existing three-party initialization barrier. It should not be
silently written by `Pack.init` on TRISC2; that would violate the ownership
model documented in `TTK.md` and omit the math-side synchronization contract.

### Required pack configuration and MOP

The authoritative implementation is
[`llk_pack_untilize.h`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_pack_untilize.h).
For BF16 and a one-tile-wide row it configures:

| Setting | BF16 one-tile value |
|---|---:|
| `block_ct_dim` | `1` |
| `full_ct_dim` | `1` |
| MOP outer count | `16` face rows |
| MOP inner count | `1` tile |
| PACR access | `DST_ACCESS_STRIDED_MODE` |
| PACR interfaces | two active interfaces |
| pack X end | `15` |
| pack Z stride | `1024` bytes (`2 * 16 * 16 * 2`) |
| L1 row stride | `64` bytes (`1 * 2 * 16 * 2`) |
| scratch row stride | `4` in 16-byte address units |

The pack MOP is structurally different from `MopCfg.pack_tile()`:

1. `ADDR_MOD_0` keeps the Dest Y row fixed; `ADDR_MOD_1` advances it once on
   the row-closing PACR.
2. Each inner iteration increments Dest W and then issues a strided PACR.
3. A start op restores W from its CR shadow for every output row.
4. An end op replays `CFGSHIFTMASK + NOP` to add the 64-byte row stride to the
   L1 destination address.
5. The last inner/outer PACR uses `ADDR_MOD_1` and sets `Last=1`.

The execute path programs the output address, establishes W as `15` so the
first tile increment wraps to tile 0, and runs the 16-row MOP twice: once for
the top face pair and once for the bottom face pair. Between those runs it
increments Z and resets Y. See
[`_llk_pack_untilize_`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_pack_untilize.h).

`ttk/tensix.py` already has MOP and replay-buffer state, so the missing pieces
are primarily the untilize MOP constructor, the row-stride replay instruction,
the two ADDR_MOD encodings, the scratch configuration register, and the
untilize-specific execute sequence. This should be implemented as a distinct
mode such as `Pack.init(output_cb, untilize=True, block_ct_dim=1,
full_ct_dim=1)`, not by conditionally changing `PACK_MOP` in place.

## Applying this to `add1`

The target data path is:

```text
host row-major bytes
  -> DRAM
  -> input CB (row-major bytes)
  -> unpack tilize
  -> SrcA / math copy / Dest (tile)
  -> SFPU add 1 (tile)
  -> pack untilize
  -> output CB (row-major bytes)
  -> DRAM
  -> host row-major bytes
```

The minimal code-level changes are:

1. Add an unpack-tilize mode to `ttk/unpack.py`, including the descriptor,
   unpack config, MOP, and execution changes above.
2. Add the matching tilize A-to-Dest MOP to `ttk/math.py` and use it for the
   initial `copy_src_a_to_dst()` in `add1`.
3. Add an explicit DEST-remap option to the math initialization and enable it
   before the initialization barrier.
4. Add pack-untilize initialization/execution to `ttk/pack.py` for
   `block_ct_dim=full_ct_dim=1`.
5. Change `examples/add1.py` to write `source` directly and compare
   `device.read(dst)` directly with `expected`.
6. Make the external `src` and `dst` buffers logically row-major and make the
   reader/writer gather/scatter their row pages as described below.
7. Remove the only import of `ttk.tile`; once the hardware test passes,
   delete `ttk/tile.py`.

The last step is safe at the source level: currently only `examples/add1.py`
imports `ttk.tile`.

## Host row-major data is possible—and should be the target

The host does **not** need to tilize. The intended contract can be:

```text
Device.write(row-major bytes)
    -> device DRAM containing row-major tensor data
    -> row-major input CB
    -> unpacker tilizes
    -> tiled compute
    -> packer untilizes
    -> row-major output CB
    -> device DRAM containing row-major tensor data
    -> Device.read() returns row-major bytes
```

The earlier caveat was only about the current `add1` reader/writer, not a
hardware limitation. To see the distinction, separate these four concepts:

| Concept | Meaning for `add1` |
|---|---|
| Host byte layout | Always row-major; the host never permutes faces. |
| Device tensor layout | Row-major for external `src` and `dst`. |
| Physical DRAM paging | How those row-major bytes are divided and striped across DRAM banks. |
| Compute/CB interpretation | Input/output CBs are row-major; SrcA/Dest are tiled. |

`blackhole-py-rewrite` currently collapses the middle two concepts into
`Buffer.layout`. In `program.py`:

- `layout="tile"` means one 2048-byte physical page for this tensor.
- `layout="row_major"` means 32 physical pages of 64 bytes, one per row.

`Device.write()` already accepts the original row-major byte string in the
second case. Its transfer firmware writes row 0 to DRAM bank 0, row 1 to bank
1, and so on, wrapping across seven banks. Nothing is tilized on the host.

The mismatch is later in `examples/add1.py`: its BRISC reader issues one
contiguous 2048-byte read from one DRAM bank, and its NCRISC writer issues one
contiguous 2048-byte write to one bank. That is correct for one 2048-byte
physical page, but not for 32 row pages distributed across banks. Merely
changing the buffers to `layout="row_major"` without changing those kernels
would therefore read and write the wrong addresses.

### Recommended split for this rewrite

Use row-major external buffers and row-sized physical pages, matching the
existing `Buffer` and generic DRAM-transfer behavior:

1. Allocate `src` and `dst` with `layout="row_major"`.
2. Change `lower_add1` to require row-major external buffers instead of tile
   buffers.
3. In BRISC, gather 32 rows of 64 bytes from their seven interleaved DRAM-bank
   locations into consecutive locations in the 2048-byte input CB.
4. Run unpack-tilize from that now-contiguous row-major CB.
5. Run pack-untilize into the 2048-byte row-major output CB.
6. In NCRISC, scatter its 32 consecutive 64-byte rows back to the corresponding
   interleaved DRAM-bank locations.
7. `Device.read(dst)` then gathers those row pages into one ordinary row-major
   host byte string, as it already does for row-major buffers.

For logical row `r`, the DRAM location follows the same mapping as
`fw/dram.py`:

```text
bank          = r % 7
address       = buffer.addr + (r // 7) * 64
CB row offset = r * 64
```

The bank endpoint coordinate must be selected from
`endpoint_coords(...)[bank]`. The 32 reads/writes can be issued through the
existing NoC batch APIs so completion is waited once per batch rather than once
per row.

This is the cleanest target because `Buffer.layout="row_major"` is truthful,
host transfer remains row-major, and the only conversions occur at the
unpacker/packer boundary.

### Alternative physical layout

It is also possible to store a logically row-major matrix as one contiguous
2048-byte device page. That would preserve the current single NoC read/write,
but it requires splitting logical layout from physical paging in `Buffer`, for
example:

```text
layout = "row_major"
physical_page_size = 2048
```

This is a valid optimization, not a requirement for device tilization. The
row-page gather/scatter design above fits the current model without adding
another buffer-layout axis.

CB metadata should likewise record layout independently of byte volume.
Row-major and tiled `32 x 32` BF16 CB pages are both 2048 bytes, so page size
alone cannot say how an engine must interpret them. A useful future shape is
`CBConfig(dtype, pages, page_size, layout, ...)`, with the unpack/pack APIs
checking that tilize consumes row-major and untilize produces row-major.

## Validation checklist

The change is complete only when all of these hold on Blackhole hardware:

- `device.write(src, source)` is used with no host permutation.
- `device.read(dst) == expected` is checked with no host permutation.
- The asymmetric test pattern in `input_and_reference()` still passes. A
  constant or face-symmetric input would not detect a layout error.
- No source file imports `ttk.tile` and `ttk/tile.py` is deleted.
- Input/output CB byte counts remain 2048 and their flags are published only
  after the complete transfer/pack.
- Initialization keeps explicit TRISC0/TRISC1/TRISC2 ownership and reaches the
  barrier only after unpack-tilize, math tilize-copy/DEST-remap, and
  pack-untilize state are installed.
- A follow-up ordinary tile pack/unpack test either restores the special state
  or builds a fresh kernel with the default mode. The `tt-metal` APIs provide
  `tilize_uninit` and `pack_untilize_uninit` because these modes mutate state
  beyond one operation.

## Primary `tt-metal` references

- Public unpack-tilize orchestration:
  [`api/compute/tilize.h`](../../tt-metal/tt_metal/hw/inc/api/compute/tilize.h)
- Blackhole unpack-tilize registers, MOP, execute, and restore:
  [`llk_unpack_tilize.h`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_tilize.h)
- Matching Blackhole math datacopy mode:
  [`llk_math_eltwise_unary_datacopy.h`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_math_eltwise_unary_datacopy.h)
- Public pack-untilize orchestration:
  [`api/compute/pack_untilize.h`](../../tt-metal/tt_metal/hw/inc/api/compute/pack_untilize.h)
- Blackhole pack-untilize registers, MOP, replay, and execute:
  [`llk_pack_untilize.h`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_pack_untilize.h)
- Blackhole DEST remap flags and synchronization:
  [`llk_math_common.h`](../../tt-metal/tt_metal/tt-llk/tt_llk_blackhole/llk_lib/llk_math_common.h)
- Small reference kernels showing CB wait/reserve and init/block/uninit lifecycle:
  [`tilize.cpp`](../../tt-metal/tests/tt_metal/tt_metal/test_kernels/compute/tilize.cpp) and
  [`pack_untilize.cpp`](../../tt-metal/tests/tt_metal/tt_metal/test_kernels/compute/pack_untilize.cpp)
