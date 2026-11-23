// TTRV owns all integer registers and the low 2 KiB of private RAM.
// Restore the C ABI after a kernel returns via the private return vector.
.text
.global run_kernel
run_kernel:
  addi sp, sp, -64
  sw ra, 0(sp)
  sw gp, 4(sp)
  sw tp, 8(sp)
  sw s0, 12(sp)
  sw s1, 16(sp)
  sw s2, 20(sp)
  sw s3, 24(sp)
  sw s4, 28(sp)
  sw s5, 32(sp)
  sw s6, 36(sp)
  sw s7, 40(sp)
  sw s8, 44(sp)
  sw s9, 48(sp)
  sw s10, 52(sp)
  sw s11, 56(sp)
  li t0, 0xffb00800
  la t1, .Lreturned
  sw t1, 0(t0)
  sw sp, 4(t0)
  jr a0
.Lreturned:
  lw sp, 4(gp)
  lw ra, 0(sp)
  lw gp, 4(sp)
  lw tp, 8(sp)
  lw s0, 12(sp)
  lw s1, 16(sp)
  lw s2, 20(sp)
  lw s3, 24(sp)
  lw s4, 28(sp)
  lw s5, 32(sp)
  lw s6, 36(sp)
  lw s7, 40(sp)
  lw s8, 44(sp)
  lw s9, 48(sp)
  lw s10, 52(sp)
  lw s11, 56(sp)
  addi sp, sp, 64
  ret
