# Blackhole Debug TODO

## Current State

### Working Now

- [x] `DEBUG=1` debugger entry on queued programs
- [x] Debug all queued programs by default in slow-dispatch mode
- [x] HTTP debug API server with structured JSON responses
- [x] Event stream / polling endpoints for automation and future UI
- [x] Basic REPL frontend backed by the same session API
- [x] RISC halt / continue / step / next / location / GPR / memory reads
- [x] Kernel-pause flow (`run_to_kernel_pause`, `release_kernel_pause`)
- [x] `SrcA` read during `DEBUG_PAUSE()` loop
- [x] `Dest` read during `DEBUG_PAUSE()` loop
- [x] Structured Tensix state dump API (`read_tensix_state`) for `alu` / `pack` / `unpack` / `gpr` / `rwc` / `adc` / `all`
- [x] Multi-program / multi-iteration debug flow in `TT_USB=1`
- [x] Cleanup that clears pause flags, breakpoints, and resumes halted RISCs
- [x] Debug-friendly `matmul_peak` input patterns (`random`, `ones`, `ramp`)

### Known Limitations

- [ ] Fast-dispatch debug is not supported; `DEBUG=1` currently requires `TT_USB=1`
- [ ] Initial status can report stale `kernel_paused=true` if L1 pause flag was already set
- [ ] `SrcA` path only exposes the currently visible / last-two-faces window
- [ ] `SrcA` read is intrusive; it injects instructions and temporarily clobbers `Dest`
- [ ] `SrcB` parity is not done yet (helpers exist, but no surfaced session/API flow yet)
- [ ] Cleanup from some DR-halted entry states can still time out while waiting for program completion
- [ ] `read_tensix_state` `gpr` currently means Tensix thread-private registers, not halted baby-RISC ABI GPRs (`read_gprs` is the RISC view)
- [ ] No standalone debug-bus signal/group list/read API yet beyond the grouped `rwc` / `adc` dumps
- [ ] No callstack / backtrace API yet

## Parity Targets

### 1. Tensix State Dumps (`tensix` parity)

- [x] Dump ALU config registers
- [x] Dump packer config / counters / strides / edge offsets
- [x] Dump unpacker config / tile descriptor registers
- [x] Dump Tensix GP registers by thread
- [x] Dump RWC state
- [x] Dump ADC state
- [x] Return all of the above in structured JSON for the future UI

### 2. Arbitrary Tensix Register Access (`reg` parity)

- [ ] Read arbitrary named Tensix cfg/dbg registers
- [ ] Search register names by wildcard / substring
- [ ] Optional write support for bring-up use
- [ ] Expose this over both REPL and HTTP API

### 3. Debug Bus Access (`dbus` parity)

- [ ] List predefined debug bus signals
- [ ] List predefined debug bus groups
- [ ] Read named signals directly
- [ ] Sample groups into L1 / over time where supported
- [ ] Expose signal values in structured JSON

### 4. RISC Introspection (`bt`, richer `gpr` parity)

- [ ] Add `bt` / backtrace support from halted PC + ELF symbols
- [ ] Improve GPR output with source location / function / current frame context
- [ ] Optional multi-RISC dump (brisc / trisc0 / trisc1 / trisc2 together)
- [ ] Show breakpoint / watchpoint state in a structured way

## Lower Priority / Later

- [ ] `SrcB` support with clear semantics and restore story
- [ ] LReg inspection if practical
- [ ] NOC register / status view
- [ ] Fast-dispatch-aware debug flow
- [ ] UI-specific metadata / schemas for panels and tables

## Recommended Next Steps

1. Implement arbitrary `reg` read/search
2. Implement standalone `dbus` list/read/group endpoints
3. Implement `bt` and richer `gpr` / clearer RISC-vs-Tensix naming
4. Harden cleanup / resume behavior from halted entry states
5. Revisit `SrcB` only after the above inspection surface is solid
