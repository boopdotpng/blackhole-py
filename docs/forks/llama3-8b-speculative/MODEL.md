# Model and source provenance

- Intended model: [Meta Llama 3 8B Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct), original Llama 3 (not 3.1 or 3.2).
- Download: [Unsloth full BF16 distribution](https://huggingface.co/unsloth/llama-3-8b-Instruct/tree/f3710969eb766fb49d4d1ed3aeabcb03390772bd).
- Exact revision: `f3710969eb766fb49d4d1ed3aeabcb03390772bd`.
- Date downloaded: 2026-09-07.
- 291 BF16 tensors, 8,030,261,248 parameters, 16,060,522,496 tensor bytes.
- Four shard SHA-256 digests are recorded in `validation/preflight.json`.
- Original source: local `blackhole-py-llama3`, HEAD `cce3e77f3a245dadfaa4a29ae3a0dda499b53708`, plus the working-tree changes present at copy time. The new repository's first commit preserves that copied tree.

Meta's gated download returned `GatedRepoError` with the environment's existing
credentials. No account permissions were changed. The downloaded distribution's
config and tensor shapes match Llama 3 8B, and its CPU reference produces coherent
output. Byte-for-byte equivalence to Meta's gated artifacts was not independently
verified. The included license is in `weights/LICENSE`.

Meta Llama 3 is licensed under the Meta Llama 3 Community License, Copyright © Meta Platforms, Inc. All Rights Reserved.
