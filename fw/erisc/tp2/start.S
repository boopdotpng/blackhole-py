.section .text.start,"ax",@progbits
.global _start
_start:
    li sp, 0xffb02000
    call main
1:  j 1b
