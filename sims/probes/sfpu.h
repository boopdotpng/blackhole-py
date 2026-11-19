/* Shared pieces of the SFPU and I-cache probes (sfpu.py, icache.py; k_sfpu_*.c, k_icache.c). TRISC roles unless noted.
 *
 * These are ports of the old Python harness (blackhole-py 718843a^: asm.py, tests/profiler.py,
 * tests/operation_pocs/sfpu_math/emit.py, tests/movement/{unpacker/unpack.py,packer/pack.py}). Every Tensix word
 * below is the word the old harness emitted; sfpu.py SFPU.md lists where the delivery differs.
 *
 * Case-specific instruction streams come from sfpu.py as defines, already rotated for .ttinsn:
 *   BODY      comma-separated words, the timed loop body (one asm block: nothing can be scheduled inside it)
 *   SETUP/TAIL/COMPUTE  a sequence of T(w, ...) (one asm block of words) and D (drain, as emit.drain)
 *
 * Waits: every RISC-side poll is WAIT_UNTIL (bounded). The old Tensix SEMWAITs on another thread's semaphore are
 * replaced by RISC polls of the semaphore (sem_wait_nonzero); the Tensix STALLWAITs left are on this thread's own
 * units or on state another thread is known to have produced already (each is commented). The PC_BUF_SYNC loads
 * (tensix_drain) return once this thread's queued work finishes, and none of it waits on anything unbounded. */
#ifndef SFPU_H
#define SFPU_H
#include "probe.h"

#define STR_(...) #__VA_ARGS__
#define XSTR(...) STR_(__VA_ARGS__)
/* One block of pre-rotated Tensix words, exactly what asm.py emitted for consecutive TensixWords. */
#define T(...) __asm__ volatile(".word " #__VA_ARGS__ ::: "memory");
#define D sfpu_drain();

/* The timed region's RISC instructions, as tests/profiler.py and emit.drain emitted them (same count and order):
 *   PROF_REC(slot):  li t5, WALL_CLOCK_L ; lw t6, 0(t5) ; li t5, slot ; sw t6, 0(t5)   (the old record(); the lw
 *                    is the time stamp, so start = lw + 3 instructions, stop = 2 instructions + lw)
 *   PROF_DRAIN(w):   .ttinsn STALLWAIT w ; li t5, PC_BUF_SYNC ; sw zero ; lw ; and zero, zero (the old pc_sync)
 * Slots sit at LOG + 0xFC0 / 0xFC4 so that, like the old PROFILE_L1_BASE, each li is lui + addi. */
#define PROF0 (LOG + 0xFC0)
#define PROF1 (LOG + 0xFC4)
#define PROF_REC(slot) "li t5, 0xFFB121F0\nlw t6, 0(t5)\nli t5, " XSTR(slot) "\nsw t6, 0(t5)\n"
#define PROF_DRAIN(rotated_stall) ".word " XSTR(rotated_stall) "\nli t5, 0xFFE80004\nsw zero, 0(t5)\nlw t6, 0(t5)\nand zero, zero, t6\n"
#define ROT_STALL_SYNC_SFPU      0x88042002  /* STALLWAIT(SYNC, SFPU) a2010800, rotated */
#define ROT_STALL_SYNC_MATH_SFPU 0x88042042  /* STALLWAIT(SYNC, MATH | SFPU) a2010810, rotated */

#define PC_BUF_MOP_SYNC     0xFFE80008u
#define SEM(i)              (0xFFE80020u + 4u * (i))  /* RISC view of Tensix semaphore i: load = value */
#define UNPACK_CONFIG_SYNC  0xFFE80034u
#define MOP_CFG(i)          (0xFFB80000u + 4u * (i))
#define CFG(byte_offset)    (TENSIX_CFG + (byte_offset))

/* Semaphores (unpack.py Sem) */
#define SEM_MATH_PACK       1
#define SEM_UNPACK_TO_DEST  2
#define SEM_UNPACK_SYNC     5
#define SEM_MATH_DONE       7

/* emit.drain: STALLWAIT(SYNC, SFPU) then a PC_BUF_SYNC round trip. */
#define W_STALL_SYNC_SFPU   0xA2010800u
#define W_STALL_SYNC_MATH_SFPU 0xA2010810u
#define W_MOP               0x01800000u  /* MOP(1, 0, 0) */
#define W_NOP               0x02000000u

INLINE void sfpu_drain(void) {
  TTINSN(W_STALL_SYNC_SFPU);
  tensix_drain();
}

INLINE void mop_sync(void) {  /* unpack.py mop_sync: PC_BUF_MOP_SYNC round trip */
  write32(PC_BUF_MOP_SYNC, 0);
  u32 v = read32(PC_BUF_MOP_SYNC);
  __asm__ volatile("and zero, zero, %0" :: "r"(v));
}

/* unpack.py configure_mop: drain the expander, then the nine template words. */
INLINE void configure_mop(u32 outer, u32 inner, u32 start, u32 end0, u32 end1, u32 loop, u32 alt, u32 last,
                          u32 outer_last) {
  mop_sync();
  write32(MOP_CFG(0), outer); write32(MOP_CFG(1), inner); write32(MOP_CFG(2), start);
  write32(MOP_CFG(3), end0); write32(MOP_CFG(4), end1); write32(MOP_CFG(5), loop);
  write32(MOP_CFG(6), alt); write32(MOP_CFG(7), last); write32(MOP_CFG(8), outer_last);
}

/* Replaces Tensix SEMWAIT(ON_ZERO): the RISC polls until another thread has posted, bounded. */
#define sem_wait_nonzero(i, site) WAIT_UNTIL(read32(SEM(i)) != 0, site)

/* cfg0 (CSR 0x7c0) and the instruction prefetch control, recorded in every result. */
INLINE u32 read_cfg0(void) {
  u32 v;
  __asm__ volatile("csrr %0, 0x7c0" : "=r"(v));
  return v;
}

/* RES_AUX words common to every SFPU/I-cache kernel */
enum { AUX_CFG0_ENTRY, AUX_CFG0_TIMED, AUX_PREFETCH, AUX_DEST_CG, AUX_TDMA_CG };

INLINE void record_config(void) {  /* cfg0 now as both "at entry" and "while timing" (a kernel that changes it rewrites the latter) */
  write32(RES_AUX + 4 * AUX_CFG0_ENTRY, read_cfg0());
  write32(RES_AUX + 4 * AUX_CFG0_TIMED, read_cfg0());
#ifndef NO_TENSIX_CFG  /* NCRISC cannot reach the Tensix config space: only cfg0 there */
  write32(RES_AUX + 4 * AUX_PREFETCH, read32(CFG_RISC_PREFETCH_CTRL));
  write32(RES_AUX + 4 * AUX_DEST_CG, read32(DEST_CG_CTRL));
  write32(RES_AUX + 4 * AUX_TDMA_CG, read32(TDMA_CLK_GATE_EN));
#endif
}

/* ---- trisc0: F32 L1 stream -> FP32 Dst tile 0 (unpack.py emit_unpack_to_dst with a constant byte count) ----
 * Byte count must be a multiple of 1024 (whole 256-element faces): the old runs used 8192 words, no tail. */
INLINE void unpack_f32_to_dst(u32 address, u32 bytes, u32 site) {
  /* configure_unpacker(UNPACKER0, address, F32, DST) */
  WAIT_UNTIL(!(read32(UNPACK_CONFIG_SYNC) & 0xFE), site);
  TTINSN(0xB2000000);                      /* SETC16(0, 0) */
  write32(CFG(0x100), 0x10); write32(CFG(0x104), 0x40001); write32(CFG(0x108), 0); write32(CFG(0x10C), 0);
  write32(CFG(0x120), 0x20); write32(CFG(0x124), 0x33); write32(CFG(0x128), 0); write32(CFG(0x12C), 0);
  TTINSN(0xB5400047);                      /* RMWCIB2 cfg 71: mask 0x40 data 0 */
  write32(CFG(0xB0), 0); write32(CFG(0xB4), 0); write32(CFG(0xE0), 0x400004); write32(CFG(0xE4), 0x400);
  write32(CFG(0xC0), 0); write32(CFG(0xC4), 0); write32(CFG(0xC8), 0x100); write32(CFG(0xD4), 0);
  write32(CFG(0x150), 0x400040); write32(CFG(0x158), 0x1000100); write32(CFG(0x170), 0); write32(CFG(0x174), 0);
  write32(CFG(0x130), (address >> 4) - 1); write32(CFG(0x134), (address >> 4) - 1);
  TTINSN(0xB2290000);                      /* SETC16(UNPACK_MISC_CONFIG 41, 0) */
  TTINSN(0xB2050000);                      /* SETC16(SRCA_SET 5, 0): direct to Dst */
  (void)read32(CFG(0x130));               /* commit: read back the base, then release the config */
  write32(UNPACK_CONFIG_SYNC, 0);
  TTINSN(0xB3070001);                      /* configure_stochastic_rounding: RMWCIB0 cfg 1 mask 7 data 0 */
  TTINSN(0x04000021);                      /* REPLAY(0, 2, 0, load) */
  TTINSN(0x42088081);                      /*   UNPACR(0, to Dst, last) */
  TTINSN(0xA2040002);                      /*   STALLWAIT(UNPACK, UNPACK0) */
  TTINSN(0x5460000F);                      /* SETADCZW(3, 0...) */
  /* old: SEMWAIT(UNPACK, MATH_DONE, ON_ZERO). Math posts it after its ZEROACC. */
  sem_wait_nonzero(SEM_MATH_DONE, site + 1);
  TTINSN(0xA5000200);                      /* SEMGET(MATH_DONE) */
  /* old: SEMWAIT(UNPACK, UNPACK_TO_DEST, ON_MAX). Kept as a Tensix wait: the semaphore is 0 at entry (reset_tensix
   * SEMINITs it) and only this thread posts it, below, so the condition already holds. */
  TTINSN(0xA6040012);
  TTINSN(0xA2040408);                      /* STALLWAIT(UNPACK, TRISC_CFG | PACK0) */
  TTINSN(0x5E23FC00);                      /* SETADCXX(1, 255, 0) */
  configure_mop(bytes >> 10, 1, 0x04000020 /* REPLAY(0, 2) */, W_NOP, W_NOP, W_NOP, W_NOP, W_NOP, W_NOP);
  TTINSN(W_MOP);
  TTINSN(0xA2040003);                      /* STALLWAIT(UNPACK, THCON | UNPACK0) */
  TTINSN(0xA5000080);                      /* SEMGET(UNPACK_SYNC) */
  tensix_drain();
  TTINSN(0xB2050004);                      /* SETC16(SRCA_SET, 4) */
  TTINSN(0xA4000010);                      /* SEMPOST(UNPACK_TO_DEST) */
}

/* ---- trisc1: the math side of the direct-to-Dst handshake, then FP32 Dst for the SFPU (the old value_images) ---- */
INLINE void math_take_dst(u32 site) {
  TTINSN(0x101C4000);                      /* ZEROACC(3, 1, 0, 1, 0) */
  TTINSN(0xA2010010);                      /* STALLWAIT(SYNC, MATH) */
  TTINSN(0xA4000200);                      /* SEMPOST(MATH_DONE) */
  sem_wait_nonzero(SEM_UNPACK_TO_DEST, site);  /* old: SEMWAIT(SYNC, UNPACK_TO_DEST, ON_ZERO) */
  TTINSN(0xA5000010);                      /* SEMGET(UNPACK_TO_DEST) */
  TTINSN(0xB2000000); TTINSN(0xB2010000);  /* configure_fp32_dst(0): SETC16(0, 0), SETC16(1, 0) */
  TTINSN(0xA2400810);                      /*   STALLWAIT(CFG, MATH | SFPU) */
  TTINSN(0xB6202001);                      /*   RMWCIB3 cfg 1: mask 0x20 data 0x20 (FP32 Dst) */
  TTINSN(0xB20C0000); TTINSN(0xB21C0000); TTINSN(0xB22F0000);  /* SETC16 12, 28, 47 = 0 */
  TTINSN(0x3700000F);                      /* SETRWC(0, 0, 0, 0, 0, 0xF) */
}

INLINE void publish_dst(void) {            /* unpack.py publish_dst */
  TTINSN(W_STALL_SYNC_MATH_SFPU);
  TTINSN(0xA4000008);                      /* SEMPOST(MATH_PACK) */
}

/* ---- trisc2: pack.py configure_packer(F32) ---- */
INLINE void configure_packer_f32(void) {
  TTINSN(0xB5800047);                      /* RMWCIB2 cfg 71: mask 0x80 data 0 */
  TTINSN(0xB2000000);                      /* SETC16(0, 0) */
  TTINSN(0xB61E0001);                      /* RMWCIB3 cfg 1: source format F32 */
  TTINSN(0xB3070001);                      /* RMWCIB0 cfg 1: no stochastic rounding */
  TTINSN(0xB3FC0002); TTINSN(0xB4FF0002); TTINSN(0xB53F0002);  /* ReLU off */
  write32(CFG(0x110), 0x40000); write32(CFG(0x118), 1); write32(CFG(0x48), 1); write32(CFG(0x30), 0x400000);
  write32(CFG(0x34), 0x10000400); write32(CFG(0x70), 0x1000); write32(CFG(0x60), 0xFFFF); write32(CFG(0x64), 0);
  write32(CFG(0x50), 0); write32(CFG(0x54), 0);
  write32(REGFILE + 16 * 4, 0x100); write32(REGFILE + 52 * 4, 0x40000);
  TTINSN(0xB2250104); TTINSN(0xB2262820); TTINSN(0xB2271120);  /* ADDR_MOD_PACK 37-39 */
  TTINSN(0x5180000B); TTINSN(0x5480000F);  /* SETADCXY / SETADCZW (packer) */
  configure_mop(4, 4, W_NOP, W_NOP, W_NOP, 0x41000000, W_NOP, 0x41008001, 0x41010000);
  tensix_drain();
}

INLINE void pack_row_addressing(void) {    /* pack.py _configure_row_addressing */
  TTINSN(0xB2250001); TTINSN(0xB2260020); TTINSN(0xB2270000);
  write32(CFG(0x70), 0x100);
}

INLINE void set_dma_reg16(u32 half, u32 value) {  /* unpack.py _set_dma_reg16: SETDMAREG built at run time, sw push */
  tensix_push(0x45000000 | half | ((value << 8) & 0xFFFF00));
}

/* unpack.py _set_pack_destination(tile 0, output) */
INLINE void set_pack_destination(u32 output) {
  TTINSN(0x508C0000);                      /* SETADC(4, 0, 3, 0) */
  u32 address = (output >> 4) - 1, high = address >> 16;
  set_dma_reg16(24, address);
  set_dma_reg16(25, 0x8000 | high);
  TTINSN(0xA2400009);                      /* STALLWAIT(CFG, THCON | PACK0) */
  TTINSN(0xB00C0045);                      /* WRCFG(12, 0, L1_DESTINATION) */
  set_dma_reg16(25, high);
  TTINSN(0x60000000);                      /* DMANOP */
}

/* pack.py emit_pack_dst_to_cb(tile 0, output, rows * 16 elements, F32), no tail. */
INLINE void pack_dst_rows_f32(u32 output, u32 rows, u32 site) {
  sem_wait_nonzero(SEM_MATH_PACK, site);   /* old: SEMWAIT(TDMA, MATH_PACK, ON_ZERO) */
  configure_packer_f32();
  pack_row_addressing();
  set_pack_destination(output);
  TTINSN(0x50840000); TTINSN(0x50880000); TTINSN(0x508C0000);  /* _set_dst_position(0, 0) */
  write32(CFG(0x2D0), 0);                  /* DESTINATION_OFFSET */
  TTINSN(0x5E803C00);                      /* SETADCXX(4, 15, 0) */
  configure_mop(1, rows, W_NOP, W_NOP, W_NOP, 0x41000100, W_NOP, 0x41008101, W_NOP);
  TTINSN(0xA2400008);                      /* STALLWAIT(CFG, PACK0) */
  TTINSN(W_MOP);
  TTINSN(0xA2010008);                      /* STALLWAIT(SYNC, PACK0) */
  tensix_drain();
  TTINSN(0xA5000008);                      /* SEMGET(MATH_PACK) */
}

#endif
