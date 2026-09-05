# Raw Blackhole tests

These tests are small, explicit proofs for the operations in
[`docs/components.md`](../docs/components.md). They use `Asm` directly and do
not import `ttk`. Create only the worker streams a test needs:

```python
from asm import Asm

brisc = Asm("brisc")
```

`bh.launch` fills missing roles with one-instruction placeholders that jump
back to resident firmware. For example, a NoC test can launch only BRISC:

```python
bh.launch({"brisc": brisc.lower()})
```

Use a mapping with any subset of `brisc`, `ncrisc`, `trisc0`, `trisc1`, and
`trisc2`. A literal RISC-V `ret` is not valid here because firmware jumps into
worker kernels without setting a return address.

## Running tests

```sh
# Unit tests only
PYTHONPATH=. pytest -q

# Hardware component tests on card 0
PYTHONPATH=. pytest -q tests/movement tests/compute \
  --bh-hardware --bh-device=0
```

Hardware tests run sequentially and boot the card once. Do not use xdist. Put
movement tests under `tests/movement/` and compute tests under `tests/compute/`.
The many-core DRAM curve can be run on its own with:

```sh
PYTHONPATH=. pytest -q -s \
  tests/movement/test_noc.py::test_many_core_interleaved_dram_copy_scaling \
  --bh-hardware --bh-device=0
```

## The `bh` fixture

```python
def test_an_operation(bh):
  brisc = Asm("brisc")

  source = bh.dram_buffer(64, initial=source_bytes)
  result = bh.dram_buffer(64)

  # Emit the BRISC instructions here. Parameters are raw u32 words at
  # TensixL1.PARAM_BASE. Other worker roles are filled automatically.
  bh.launch({"brisc": brisc.lower()}, params=(
    source.address, source.coordinate,
    result.address, result.coordinate,
  ))

  assert bh.read(result) == expected_bytes
```

Useful calls:

- `bh.dram_buffer(size, initial=..., bank=0)` allocates one DRAM buffer.
- `bh.interleaved_dram_buffer(size, page_size=..., banks=8, bank_start=0)`
  stripes logical pages over a contiguous physical bank range.
- `bh.launch(images, params=(), l1=None)` runs all five streams on one tile.
- `bh.launch_many(images, cores=..., params={core: words})` runs identical
  images with per-core parameter tables.
- `bh.read_l1(core, address, size)` reads a small post-kernel result record.
- `params` contains up to 12 raw u32 words.
- `l1={address: bytes}` initializes selected worker L1 ranges before launch.
- `bh.read(buffer)` and `bh.write(buffer, data)` access DRAM.

Tests choose their own parameter slots and L1 layout. General test data starts
at `TensixL1.DATA_BUFFER_SPACE_BASE`.

## Cycle profiler

Create a profiler for the RISC being measured. Call the same method twice with
the same label: first to start, then to stop.

```python
from tests.profiler import Profiler

ncrisc = Asm("ncrisc")
profile = Profiler(ncrisc)

profile.record("kernel")
profile.record("NoC read")
# Issue the read and wait for its completion.
profile.record("NoC read")
profile.record("kernel")

bh.launch({"ncrisc": ncrisc.lower()}, profiler=profile)

assert profile.last["NoC read"] > 0
```

The launch prints:

```text
cycle profile:
  [1] kernel: 123 cycles
  [2] NoC read: 45 cycles
```

There are at most three labels. Each marker stores `WALL_CLOCK_L` directly to
a reserved, 16-byte-aligned 32-byte block at the end of usable L1. After the
user kernel finishes, a tiny BRISC kernel copies the used 8, 16, or 24 bytes to
DRAM and the host subtracts each timestamp pair. The export is not timed.

One interval must be shorter than the low counter's 2^32-cycle wrap (about
3.18 seconds at 1.35 GHz). A NoC stop marker measures completion only if its
wait is before the marker. For very small operations, measure an empty section
too if you want to subtract marker overhead.

Use `profile.accumulate(label)` in place of `record(label)` when a loop has
several disjoint intervals that should be reported as one sum. Each start/stop
pair is added on device; CB waits and address work between pairs are excluded.
