# TTK design

TTK is the explicit hardware layer between raw instruction encoding and a
five-role worker program:

```text
isa.py       raw RISC-V and Tensix encodings
asm.py       one private instruction stream: registers, labels, loops, fixups
ttk/         CB, NoC, Tensix, unpack, math, SFPU, and pack operations
program.py   public five-stream Program, resources, lowering, CQ commands
cq.py        upload and launch transport
```

## Program construction

`Program` is the only public authoring object. It owns five independent
instruction streams and exposes them as `brisc`, `ncrisc`, `trisc0`, `trisc1`,
and `trisc2`. Each stream still has independent registers, labels, local RAM,
and a firmware return path, but there is no public role-builder or bundle
layer.

```python
p = Program(cores, buffers=(src, dst))

input_cb = p.cb(src.dtype, pages=2, name="input")
output_cb = p.cb(dst.dtype, pages=2, name="output")

input_reader = p.brisc.init_cb(input_cb)
input_unpack = p.trisc0.init_cb(input_cb)
output_pack = p.trisc2.init_cb(output_cb)
output_writer = p.ncrisc.init_cb(output_cb)

p.unpack.init(input_unpack)
p.math.initialize()
p.pack.init(output_pack)

# Emit the five concurrent streams through p.brisc, p.trisc0, ...
```

CB declarations allocate non-overlapping storage from the worker L1 data
region. `init_cb()` remains explicit for each participating role because each
RISC owns a separate local CB cursor and counter shadow.

Buffers passed to `Program` occupy fixed parameter words. A role loads a
buffer's current DRAM address with `p.brisc.param(src)`. `Program.bind(src,
replacement)` creates a CQ write for rebinding without rebuilding text.
`buffer.from_numpy(array)` converts any NumPy input dtype through FP32 into the
buffer's BF16 or F32 host representation, including zero padding;
`buffer.to_numpy(data)` performs the inverse logical-shape conversion. Device
transfer remains explicit.

Calling `Program.lower()`, inspecting `Program.kernels`, or submitting the
program finalizes all five streams. The same role images are uploaded to every
target core. Per-core runtime arguments are still needed before kernels can
assign different tile ranges while sharing text.

## Firmware construction

Firmware and transport helper images use `Asm` directly because they are one
instruction stream rather than a five-role user program. `Asm.firmware(role)`
omits the generated user-kernel return path. This is an internal assembler
facility, not a second kernel-authoring API.

## Synchronization

Synchronization stays with the hardware subsystem whose fact is being waited
on:

- CB owns reserve, publication, availability, and release counters.
- NoC owns command readiness and each distinct completion counter.
- Tensix owns drains, resource stalls, configuration handshakes, and hardware
  semaphores.
- Firmware owns reset, GO, DONE, and launch completion.
- Ordinary L1 signal/wait operations are added only for a demonstrated
  same-worker RISC dependency.

There is no generic barrier object or synchronization lowering pass. Python
emission order between role streams never creates a runtime edge.

The add1 program needs no software L1 rendezvous. Firmware resets
Tensix, hardware semaphores, CB hardware counters, NoC command buffers, and
TRISC register files before launch. Unpack, math, and pack then perform their
operation-specific setup before issuing their own ordered work.

Add1 emits one runtime tile loop per role with ordinary Python authoring syntax:

```python
for tile in p.brisc.range(src.pages):
  input_cb.reserve_back()
  with noc.read_batch() as reads:
    reads.issue_dram(src, tile, input_cb)
  input_cb.push_back()
```

Device buffers are striped by logical tile across seven DRAM banks. Add1 is
hardware-validated for 1, 2, 7, 8, 17, 33, and 1,000 tiles on one core. The
1,000-tile run repeatedly crosses both the seven-bank stripe and 16-page CB
ring while keeping role image sizes constant.

## Current next steps

1. Add Tensix-ordered CB publication and release forms to remove current full
   engine drains.
2. Add per-core tile start/count arguments while retaining shared role images.
3. Validate one disjoint tile range per program core, then multiple tiles per
   core and uneven tails.

See `examples/add1.py` for the executable API and `sync.md` for the complete
synchronization inventory.
