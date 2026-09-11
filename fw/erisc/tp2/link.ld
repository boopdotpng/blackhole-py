ENTRY(_start)
SECTIONS {
  . = 0x61000;
  .text : { *(.text.start) *(.text*) }
  .rodata : { *(.rodata*) }
  .data : { *(.data*) }
  .bss : { *(.bss*) *(COMMON) }
  ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "startup has no data/bss init")
  ASSERT(. < 0x62000, "E1 image exceeds reserved page")
}
