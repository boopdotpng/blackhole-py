# Legacy TTK

The model kernels use `ttko` while the new `ttk/model.py` develops independently.
Its assembler uses scoped physical registers; the raw assembler uses virtual
registers. Both share the instruction encoders in `ttko/isa.py`. Firmware still comes from the central
`firmware/__init__.py`; this package does not build replacement worker or CQ firmware.

Sources: FP8 TTK, the 1B NoC operand-lifetime fix, and the 8B prefill retained-row
unpacker.

`matmul_peak` also uses the shared ISA plus this package's loop templates, NoC and circular
buffer operations, and blocked math/unpack/pack helpers. Those helpers take
explicit scratch registers for schedules that keep values in fixed registers.
The example retains its tiling, multicast schedule, and mailbox initialization.
