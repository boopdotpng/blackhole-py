OUTPUT_ARCH(riscv)
/* Megakernel pieces (fw/boot.c, C kernel bodies): code only, padded to 16 bytes; _end is where the next piece goes. */
SECTIONS
{
  . = BASE;
  .text : {
    KEEP(*(.entry))
    *(.text .text.*)
    *(.rodata .rodata.* .srodata .srodata.*)
    . = ALIGN(16);
  }
  _end = .;
  .data : {
    *(.data .data.* .sdata .sdata.* .bss .bss.* .sbss .sbss.* COMMON)
  }
  ASSERT(SIZEOF(.data) == 0, "megakernel pieces are relocated by plain concatenation: no data allowed")
  ASSERT(_end <= BASE + SIZE, "image exceeds its slot")
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) *(.riscv.attributes) }
}
