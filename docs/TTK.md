# TTK design

TTK is the stateful hardware layer between the assembler and a five-kernel
program:

```text
isa.py       raw instruction encodings
asm.py       registers, labels, loops, fixups, and kernel lowering
ttk/         stateful Blackhole engines
program.py   kernel bundles, CB configuration, and lowered program artifacts
cq.py        upload and run transport
```

## Engine modules

Map each hardware engine directly:

```text
ttk/noc.py
ttk/unpack.py
ttk/fpu.py
ttk/sfpu.py
ttk/pack.py
ttk/cb.py
ttk/tensix.py
```

An assembled kernel receives the engines appropriate to its role. BRISC and
NCRISC use NoC, TRISC0 uses unpack, TRISC1 uses FPU/SFPU, and TRISC2 uses
pack. Raw ISA methods remain available for unusual sequences.

## Kernel construction

Kernel functions receive a `KernelBuilder` for one `(x, y)` core.
`KernelBundle` assembles each function separately for every core and freezes
the results into an immutable `Program`:

```py
src = Param("src", src_buffer)

def brisc(k):
  src_addr = k.param(src)
  noc = k.noc(0)
  noc.initialize(NoC.static_coord(*k.core))
  # Emit the reader kernel.

def trisc1(k):
  # Emit the math kernel.
  pass

bundle = KernelBundle(cores, params=(src,), brisc=brisc, trisc1=trisc1)
program = bundle.lower()
```

Inside a kernel function, `k.core` is a `Core = Tuple[int, int]` containing its
compile-time `(x, y)` coordinate. Ordinary Python control flow can therefore
specialize the emitted kernel for that core. Scalar geometry, core indices,
strides, and fixed buffer addresses are therefore compile-time immediates.
Only replaceable DRAM buffers are declared as `Param` objects. Each parameter
owns a fixed word beginning at `0x4100`; `k.param()` loads the buffer address
stored in that word. `program.bind(param, buffer)` creates the CQ write that
updates it while enforcing the captured dtype, shape, and layout. The builder
saves the firmware return address in role-local RAM before the kernel body and
restores it in the default epilogue. Kernel-specific initialization and
synchronization remain explicit in each function.

Images entered directly by hardware use `KernelBuilder.standalone(role)`. A
standalone builder has no compile-time core, return-address save, local return
slot, or generated epilogue. Firmware placement and capacity belong solely to
the L1 map, not the assembler.

Local allocations begin after firmware-local state and fixed TTK tables.
The return address is allocated first; user allocations therefore start four
bytes later. The upper bound excludes the linker-reserved stack:

| Role | Return address | First user allocation | Allocation limit |
|---|---:|---:|---:|
| BRISC | `0xFFB0_0878` | `0xFFB0_087C` | `0xFFB0_1F00` |
| NCRISC | `0xFFB0_0864` | `0xFFB0_0868` | `0xFFB0_1F00` |
| TRISC0 | `0xFFB0_0820` | `0xFFB0_0824` | `0xFFB0_0F40` |
| TRISC1 | `0xFFB0_0140` | `0xFFB0_0144` | `0xFFB0_0F40` |
| TRISC2 | `0xFFB0_08C0` | `0xFFB0_08C4` | `0xFFB0_0F00` |

See `examples/add1.py` for a complete construction and lowering example.

## Exact configuration state

Use TTSIM to establish the reset value of every engine configuration register.
Each kernel starts from that verified snapshot. Every configuration mutation
must go through its engine object, which:

1. Creates the requested new typed state.
2. Compares it with the current state.
3. Emits the minimum hardware instructions needed for the change.
4. Updates both the human-readable state and exact raw-register shadows.

For example:

```py
k.fpu.configure(
  fidelity=HiFi2,
  broadcast=Broadcast.ROW,
  accumulate=False,
)
```

The state remains inspectable:

```py
FPUState(
  fidelity=HiFi2,
  broadcast=Broadcast.ROW,
  accumulate=False,
  srca_format=BF16,
  srcb_format=BF16,
  dst_format=BF16,
)
```

Do not expose every packed configuration register as a public Python object.
Typed engine state is the public model; exact 32-bit register words are an
internal shadow used to produce correct diffs.

State belongs to a fresh per-core, per-role kernel builder. `KernelBundle`
assembles all five roles for every core; lowering freezes them into a `Program`.
A program may omit unused roles; launch materializes each missing role as an
empty return kernel so an older worker image cannot run accidentally. State
from one builder must never leak into another.

Runtime-dependent configuration writes must merge to a symbolic or unknown
state unless every path produces the same value. Ordinary data, engine progress,
and address counters may also be symbolic even when configuration is exact.

## Architectural operands

SrcA, SrcB, Dst, and SFPU local registers can be lightweight Python objects.
They represent architectural storage, not host values.

FPU expressions map naturally to instructions with implied operands:

```py
k.fpu.dst[0] = k.fpu.srcA * k.fpu.srcB.row_broadcast()
```

The assignment can lower to the required format and address-modifier changes,
`TTELWMUL`, and an appropriate MOP. Unsupported operand combinations fail while
constructing the kernel.

SFPU is even more naturally value-like because its local registers are explicit
and allocatable:

```py
x = k.sfpu.load(Dst.bf16(offset))
y = k.sfpu.load(Dst.bf16(offset + 2))
x = x * x + y * y
k.sfpu.store(Dst.f32(acc_offset), x)
```

The compute expression layer can be added after the stateful engines work. It
must stay small and only express operations that map clearly to hardware.

## Keep synchronization explicit

Expressions must not hide movement, occupancy, or cross-engine ordering:

```py
unpack = Unpack(k)
unpack.wait(A)
unpack.tile(A, fpu.srcA)

fpu.wait_inputs()
fpu.dst[0] = fpu.srcA * fpu.srcB

pack = Pack(k)
pack.wait_dst()
pack.tile(fpu.dst[0], OUT)
```

CB reserve/wait/push/pop, engine stalls, semaphores, and phase barriers remain
explicit operations.

## NoC

BRISC and NCRISC may explicitly select either NIU with `k.noc(0)` or
`k.noc(1)`. TRISC builders reject NoC access. Both NIUs use the same
implementation and have separate MMIO register banks. Lowering chooses
the endpoint and its address before emitting data movement:

```py
noc = k.noc(index)
noc.read(src, dram_coord, dst, size)
noc.write(src, dst, dram_coord, size)
```

The hardware command-buffer selection is private: `read()`, `write()`, and
`atomic_inc()` select the appropriate slot and control word. Ordinary issues
emit a complete required register image, making them safe across runtime
branches. Explicit read/write stream contexts program invariant state once for
hot loops. `read_batch()`, `write_batch()`, and `atomic_batch()` hide completion
counter snapshots and emit modulo-safe waits. A stream's nested `batch()` does
the same without repeating its invariant command setup.

`noc.logical_coord(reg)` reads the NIU's runtime logical coordinate rather
than pretending it is compile-time state. One-time NoC hardware setup belongs
to BRISC firmware, not the per-kernel NoC object.

## Concurrent ownership

The five RISC-V kernels run concurrently, so compile-time state tracking needs
clear ownership:

```text
TRISC0 owns unpack configuration.
TRISC1 owns FPU and SFPU configuration.
TRISC2 owns pack configuration.
BRISC and NCRISC own their respective NoC state.
```

Changes to shared/global Tensix configuration require an explicit phase barrier.
If two roles can concurrently write the same register, there is no single final
state and the API must reject it or model the synchronization that orders it.

## RMSNorm example

RMSNorm demonstrates both useful expression styles:

- Its reduction is SFPU work: load Dst chunks into L0-L7, square them, reduce
  lanes, accumulate row sums, scale, add epsilon, and apply reciprocal square
  root. SFPU register expressions can make this readable.
- Its final gamma stage unpacks normalized activations into SrcA, row-broadcasts
  gamma through SrcB, runs HiFi2 `ELWMUL`, and produces Dst. This maps directly
  to an FPU expression.

It also demonstrates why synchronization stays explicit: unpack writes Dst,
SFPU transforms it, pack consumes it, and configuration changes are separated
by waits and phase barriers.

## Porting order

1. Record the TTSIM reset snapshot and define typed state dataclasses.
2. Implement the raw configuration shadow and diff emitter.
3. Port NoC, CB, unpack, FPU, SFPU, and pack helpers onto that state model.
4. Port BRISC, NCRISC, and TRISC firmware using the new TTK.
5. Port simple kernels and verify final engine states against TTSIM.
6. Add the optional compute-expression layer after the direct engine APIs are
   correct.
