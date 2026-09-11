# Consolidation record

All eight included working trees were inventoried by file content, including
uncommitted and untracked sources. Git ancestry was not used to decide which
implementation was current. Qwen was explicitly excluded.

Before editing, source files were backed up to
`../blackhole-merge-backup-20260911-115916/sources.tar.gz`; the accompanying
manifest records SHA-256 hashes. This backup excludes downloaded weights,
virtual environments, caches, and Git directories. The original source forks
remain available. Their weight paths now link into central `weights/`.

The first five commits save the pre-existing central work by area. Subsequent
commits introduce the legacy compiler, ABI, model adapters, checkpoint support,
individual runner families, distributed implementations, and supporting tools.

## Resolution choices

- `ttk/model.py` and `ttk/sketches/rmsnorm_embedding.py` are byte-identical to the
  original central working tree. Its original Llama example is preserved as
  `examples/llama3_reference.py` and remains an unhooked reference.
- `ttko/` combines FP8 formats, 8B prefill's retained-row unpacking, the 1B NoC
  register-lifetime fix, and the protected kernel CSR policy. Speculation uses
  the same retained-row interface. The old assembler/ISA stay namespaced.
- Central raw PCIe, device boot, and CQ transport remain authoritative. The
  model adapter adds the existing trace/cache capabilities and TP2 asynchronous
  replay. Worker boot comes only from central `fw/build.py`.
- With explicit approval, the ABI expands to 24 parameter words at `0x3280`,
  160-byte templates, and a resident arena ending at `0x90000`. Cache, fusion,
  and instruction-prefetch settings remain protected. All four CQ service
  image hashes match the old reference on both supported board configurations.
- No host face tilization/untilization was copied into the active runtime.
  `ttko/layout.py` provides device conversion for legacy layout boundaries.
  Row-major checkpoint uploads bypass it. Layout reference math in tests is
  only an oracle, not an inference path.
- The three primary model modules retain their variant-specific kernel tuning.
  The TP2 runtime loads a private instance of the FP8 kernel module so its
  reduced head counts cannot alter single-card model globals.
- The two distributed implementations coexist under `distributed/llama3/` and
  `distributed/tp2/`; their Ethernet code is separated accordingly.
- 8B BF16 prefill is opt-in. Its construction hooks also support the speculative
  verifier without changing the default decode path.
- The experimental local FP8 checkpoint and conversion tool were retired at
  the user's request. Only the published calibrated FP8 checkpoint is retained.
  Historical notes can still mention old conversion experiments.
- Old scripts that experiment with firmware cache policy are superseded by
  central's live firmware-setting tests. The hardcoded card-reset script is
  superseded by the existing device-queue reset command.

`imports.json` records initial source-to-destination copies and source hashes;
`source-inventory.json` accounts for every inventoried source path, including
shared replacements and historical material. `weights.json` records the moves;
the experimental FP8 destination listed there was subsequently deleted as
requested. Duplicate BF16 directories were retained under `weights/archive/`
rather than deleting existing checkpoints.

Fresh validation lives in `validation/current/`. Files under `docs/forks/` are
historical evidence; their paths and performance numbers are not claims about
the consolidated checkout. Large historical binary outputs and redundant
source captures remain in the source backup, not in the active code tree.
