# Unified program authoring

The unified builder design is implemented as one public `Program` object.
`RoleBuilder`, `KernelBuilder`, `KernelBundle`, explicit `Param` wrappers, and
the generic `Barrier` experiment have been removed.

## Boundary

A physical Tensix worker still runs five independent RISC-V instruction
streams. They cannot share assembler state: each role requires its own register
allocator, labels, local RAM, prologue, and return path. Those streams are now
private `Asm` instances owned by `Program` rather than separate public builder
objects.

```python
def add1(src, dst, *, core=(1, 2)):
  p = Program((core,), buffers=(src, dst))
  input_cb = p.cb(src.dtype, 1, name="input")
  output_cb = p.cb(dst.dtype, 1, name="output")

  input_reader = p.brisc.init_cb(input_cb)
  input_unpack = p.trisc0.init_cb(input_cb)
  output_pack = p.trisc2.init_cb(output_cb)
  output_writer = p.ncrisc.init_cb(output_cb)

  # Explicit engine initialization and role operations follow.
  return p
```

`Device.run(program)` finalizes the streams, uploads the five images and
parameter table, and submits the CQ run command. No nested build callback or
separate lowering bundle is required.

## Resource policy

- Buffer arguments are passed directly to `Program`; roles use `param(buffer)`.
- CB indices and L1 addresses are assigned when `Program.cb()` is called.
- Every role explicitly initializes its local view with `role.init_cb(cb)`.
- Tile byte size comes from the buffer or CB dtype.
- User kernels do not choose fixed CB or software-sync addresses.
- The same images are shared by all target cores.

## Synchronization policy

The author writes waits and publications explicitly through CB, NoC, Tensix,
or raw RISC operations. There is no `Program.sync`, `Barrier`, `ttk/sync.py`,
or inferred lowering.

The former add1 three-TRISC initialization rendezvous was removed and passed
hardware validation. It ran once per launch, not once per tile, and did not
serialize concurrent configuration writes. Firmware's real per-launch reset
remains intact.

If a future kernel demonstrates a same-worker RISC dependency not represented
by CB or Tensix hardware, use explicit named L1 signal and wait operations for
that specific edge. Do not introduce a universal synchronization facade.

## Add1 completion path

The next complete milestone is a shared-text, all-core, multi-tile add1:

```text
BRISC  : DRAM page -> input CB publication
TRISC0 : input CB wait -> unpack -> Tensix-ordered CB release
TRISC1 : math/SFPU -> MATH_PACK post
TRISC2 : MATH_PACK wait -> pack -> output CB publication
NCRISC : output CB wait -> acknowledged DRAM write -> CB release
```

Single-core multi-tile add1 is complete: runtime role loops, moving CB pointers,
seven-bank DRAM addressing, balanced `MATH_PACK` flow control, and CB ring wrap
are hardware-validated through 1,000 tiles. Remaining implementation order:

1. Port deferred CB publication/release ordering to replace full drains.
2. Add per-core tile start/count arguments while retaining shared images.
3. Test one and multiple tiles per core, including an uneven all-core workload.

Tinygrad integration remains later. The standalone Python kernel stack should
first prove these hardware protocols without adding another IR or lowering
layer.
