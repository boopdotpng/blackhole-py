"""Compile-time evaluation on the tree (spec §3). In: parsed tree and -D overrides. Out: a flat tree containing only
scalar statements, runtime control flow (if/while/for/loop), calls and device-op nodes.

- const and -D (never grid), grid.size, repeat indices: compile-time integers. Fold with Python ints and check they fit their type.
- if with a constant condition: keep the taken branch.
- repeat: one copy per index; repeat 0 emits nothing.
- macro!(args): substitute argument trees for parameters; names assigned inside the body get a fresh suffix per
  expansion and iteration. Everything else (globals, SFPU registers, operand words) passes through. Bound the size.
- loop/for/while stay runtime even with constant bounds. mop/replay bodies are hardware templates, not expanded here
  beyond source macros and constants inside them."""
