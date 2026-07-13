# refactor notes for blackhole-py-rewrite

## goals
lower line count (sz.py)
decrease complexity
make ttk/ do more stuff in a better abstracted way to avoid kernels failing to launch

## cq.py
the host-side Fence is gone, but Op.FENCE and the dispatch handler remain for firmware/internal compatibility. decide whether those should also be removed.

## device.py
the firmware upload still waits for every core to signal boot completion. removing the wait may race CQ firmware upload and startup, so this needs hardware validation if we want to trim it further.

the host still installs the NCRISC/TRISC reset PCs and overrides. BRISC does not currently do this, and its resident image exactly fills its 1536-byte region. moving these writes into BRISC requires shrinking it or changing the resident firmware layout.

_dram_program can be inserted into the queue normally instead of special handling. every time a program gets added to the queue, we could determine which buffers need uploading, add those commands before the program, and reserve output space. DRAM read kernels are only needed when reading a buffer. Buffer.read/write could add operations to the device queue, but this needs decisions about buffer ownership and staging lifetime.

## firmware builders
the build_dispatch and dram builder patterns should still be reconsidered together.

the outer fw.scope() around NoC batches cannot currently be removed: entering write_ack_batch/read_batch allocates registers and requires an active assembly scope. changing this requires the batch context to own its scope without invalidating registers used by the body.
