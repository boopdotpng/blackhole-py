# Legacy TTK

The model kernels use `ttko` while the new `ttk/model.py` develops independently.
The shared root `asm.py` supports both scoped physical registers and virtual
register allocation through one instruction/lowering path. `device.py` owns
hardware access and exposes `Device` for raw launches and `TensorDevice` for
queued tensor programs. `program.py` owns raw `Program` and `TensorProgram`
builders; `cq.py` owns the command queue and its optional trace arena.
There are no private assembler/device/program/CQ copies in this package.
Firmware comes from the central `firmware/__init__.py`.


Sources: FP8 TTK, the 1B NoC operand-lifetime fix, and the 8B prefill retained-row
unpacker.

`matmul_peak` also uses the shared ISA plus this package's loop templates, NoC and circular
buffer operations, and blocked math/unpack/pack helpers. Those helpers take
explicit scratch registers for schedules that keep values in fixed registers.
The example retains its tiling, multicast schedule, and mailbox initialization.
