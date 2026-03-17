# debug/ - Blackhole P100A interactive RISC-V debugger
#
# Standalone debug infrastructure for blackhole-py. No runtime deps beyond
# hw.TLBWindow (the same ioctl/mmap transport the main driver uses).
#
# Modules:
#   regs    - hardware register addresses, bit fields, instruction encodings
#   core    - low-level debug register protocol (halt/step/GPR/breakpoints)
#   inspect - higher-level reads (Dest tiles, LRegs, L1 dump, CFG, debug bus)
#   source  - addr2line / objdump integration for PC -> source mapping
#   repl    - interactive command-line debugger
