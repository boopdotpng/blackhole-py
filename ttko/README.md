# Legacy TTK

The model kernels use `ttko` while the new `ttk/model.py` develops independently.
Its assembler and ISA are namespaced here because their register and instruction
interfaces differ from the raw assembler. Firmware still comes from the central
`fw/build.py`; this package does not build replacement worker or CQ firmware.

Sources: FP8 TTK, the 1B NoC operand-lifetime fix, the 8B prefill retained-row
unpacker, and the TP2 assembler CSR policy.
