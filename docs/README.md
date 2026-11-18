# Documentation

- [ttrv language specification](ttrv_spec.md): the canonical consolidated v1 design.
- [Llama3 kernels in TTRV](examples/): every decode kernel, one source per kernel for 1B, 8B and 8B FP8.
  Embedding and O/down compile and run; the others are written against the spec ahead of the compiler.
- [Gaps found by the ports](ttrv_gaps.md): open language questions, with the kernel lines that raised them.
- [Port review and compiler assessment](ttrv_port_review.md): validation, costs and remaining gaps.
- [Pack/unpack measurements](ttrv_pack_unpack.md): hardware evidence and unresolved modes.
- [Native config fields](ttrv_cfg.md): generated encoding reference, not the public API.
- [Llama kernels](kernels.md): existing implementation and performance notes.
