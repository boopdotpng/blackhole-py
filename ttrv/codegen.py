"""The per-RISC tree walk. In: flat tree, layout map, one entry function. Out: a list of items (instruction word,
label, branch to label, call placeholder), each tagged with its source location.

- Registers: x1-x31, no calling convention. Base registers (hw.py table per RISC) are loaded in the entry prologue
  and never allocated; constant addresses within +-2 KiB of one become offset(base). A variable holds a register from
  first assignment to block end; temporaries until statement end. Exhaustion is an error naming who holds what.
- Expressions return (reg, type): pointer scaling by T.size, load/store width, signed vs unsigned div/shift/compare.
- Control flow: labels and branches; emit.py resolves and relaxes them.
- Calls: compile functions callers-first. Record the registers busy at each call site; the callee takes its params,
  locals, temporaries and link register from the complement. Argument/result moves and the jal are placeholders
  until the callee is compiled.
- Device ops: dispatch to ops.py.
- Config writes need no value tracking. Config (one per core, shared by the TRISCs): every field write is masked,
  RMWCIBn per touched byte (words 0-255), so a write never depends on or clobbers another field. Probed: two
  TRISCs hammering the same byte never lost a write. WRCFG only for words one RISC owns entirely (runtime addresses).
  ThreadConfig is per thread: each op writes whole SETC16 words. When another engine sees a new value is the
  author's protocol (CBs, semaphores), never inferred."""
