OUTPUT_ARCH(riscv)
_start = BASE;
SECTIONS
{
  . = BASE;
  .text : {
    KEEP(*(.entry))
    *(.text .text.*)
  }
  .data : ALIGN(8) {
    *(.rodata .rodata.* .srodata .srodata.*)
    *(.data .data.* .sdata .sdata.*)
    *(.bss .bss.* .sbss .sbss.* COMMON)
  }
  ASSERT(. <= BASE + SIZE, "image exceeds its slot")
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) *(.riscv.attributes) }
}
