# llama3 firmware

`llama3/` contains unchanged firmware sources and their original build
requirements from `~/tenstorrent/blackhole-py-llama3`, commit
`cce3e77f3a245dadfaa4a29ae3a0dda499b53708`. The copied files matched that
repository's working tree on 2026-09-06. No sibling checkout is required at
runtime.

`build.py` runs this assembler in an isolated Python subprocess to avoid
replacing the main repository's current assembler, ISA objects, or TTK model.
`consts.py` is an exact copy of the reference memory/launch ABI. Device boot
uses the reference's resident firmware on all 120 tiles, then starts the CQ
services through GO. The C firmware has been removed.

`llama3-manifest.json` records source hashes and all nine image hashes for P100
and P150 using PCIe middle address `0x10000000`. Those images were compared
byte-for-byte with images built directly in the reference checkout.

Keep the snapshot unchanged. Update it from the working reference as a unit,
including its build dependencies, ABI constants, and reference hashes.

The current build wrapper deliberately overrides the snapshot's TRISC CSR
policy: it clears `cfg0.DisTriscCache` (bit 18) to enable `.ttinsn` fusion,
while leaving `DisIcPrefetch` (bit 2) clear. After every backend reset it also
sets Blackhole's `RISC_PREFETCH_CTRL` (config word 208) to `0x11f`: prefetch
enabled for all five RISC cores, with eight requests allowed in flight.
The manifest above describes the original reference images, not the patched
BRISC/TRISC images. The snapshot files remain unchanged.
`tests/timing/test_firmware_cache.py` checks live CSR and backend settings on
the selected test core and all compute workers. The builder checks resident
image sizes against the fixed ABI slots.
