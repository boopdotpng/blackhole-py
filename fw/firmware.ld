OUTPUT_ARCH(riscv)
ENTRY(_start)

SECTIONS
{
  . = TT_IMAGE_BASE;
  __image_start = .;

  .entry : ALIGN(4) {
    KEEP(*(.entry))
    KEEP(*(.entry.*))
  }
  ASSERT(ADDR(.entry) == TT_IMAGE_BASE,
         "firmware entry is not at the image base")
  ASSERT(SIZEOF(.entry) <= TT_TEXT_OFFSET,
         "firmware entry exceeds its reserved space")

  . = TT_IMAGE_BASE + TT_TEXT_OFFSET;
  .text : ALIGN(4) {
    *(.text)
    *(.text.*)
  }
  ASSERT(ADDR(.text) + SIZEOF(.text) <=
         TT_IMAGE_BASE + TT_TEXT_CAPACITY,
         "firmware program exceeds its code region")

  __data_start = .;

  .rodata : ALIGN(8) {
    *(.rodata)
    *(.rodata.*)
    *(.srodata)
    *(.srodata.*)
  }

  .data : ALIGN(8) {
    *(.data)
    *(.data.*)
    *(.sdata)
    *(.sdata.*)
  }

  .bss (NOLOAD) : ALIGN(8) {
    __bss_start = .;
    *(.bss)
    *(.bss.*)
    *(.sbss)
    *(.sbss.*)
    *(COMMON)
    __bss_end = .;
  }

  __image_end = .;
  ASSERT(__image_end - __data_start <= TT_DATA_CAPACITY,
         "firmware data exceeds its allowance")
  ASSERT(__image_end <= TT_IMAGE_BASE + TT_IMAGE_CAPACITY,
         "firmware image exceeds its slot")

  .riscv.attributes 0 : { *(.riscv.attributes) }

  /DISCARD/ : {
    *(.comment)
    *(.note*)
    *(.eh_frame*)
  }
}
