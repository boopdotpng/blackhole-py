// Kernel call trampoline (adapted from blackhole-py-archive/fw/call.S).
// Compiled kernels use gp = LOCAL_MEM + 2048 (0xFFB00800) as spill base (offsets >= 0),
// tp = SECOND + 2048, and t0 = PC_BUF + 2048 (TRISC0). The return vector lives below
// spill slot 0 at -16(gp) = 0xFFB007F0 (return PC) and -12(gp) = 0xFFB007F4 (saved sp).
.text
.global run_kernel
// void run_kernel(u32 pc, u32 tp_val, u32 t0_val)
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
  li gp, 0xffb00800
  mv tp, a1
  la t1, .Lreturned
  sw t1, -16(gp)
  sw sp, -12(gp)
  mv ra, t1
  mv t0, a2
  jr a0
.Lreturned:
  li gp, 0xffb00800
  lw sp, -12(gp)
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
