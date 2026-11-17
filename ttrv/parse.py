"""Lex and parse source into a tree. Knows the syntax (spec §2), not the instruction set.

Out: file-level declarations (const, param, l1, cb, sem, macro, fn, mop, replay, sfpmacro) and statement trees.
Every node carries its source location; expansion appends invocation sites to it. Errors are raised here as one
exception type with a location, a stable id and a message.

- Statements end at newline or `;`; a trailing comma continues. `//` and `/* */` comments.
- Expressions: precedence climbing, C precedence (spec §5), plus `a..b` ranges, `p[i]`, `f(x)`, dotted reads
  (`core.x`, `bf16.tile`). Integer literals with `_`; floats and `inf` only where an operand takes them.
- A device op is one generic node: (name, results, args, opts). `x = cb.reserve q` vs `x = core.x`: the namespace
  list (noc cb tensix sem unpack pack math sfp mop replay sfpmacro) decides. Operand words like `a`, `l0`, `risc`,
  `dst` stay identifiers; `a|b` stays an or-expression; ops.py gives them meaning.
- Options: `name=e`, `name+=e`, `name-=e`, bare flags. Template bodies: `label: op` lines.
- `if` keeps both branches; `repeat`, `macro!()` and constant folding are expand.py's."""
