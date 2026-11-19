/* TRISC0 side of the pack probes (pack.py): an unpacker 0 stream reading L1 while TRISC2 packs, for L1 contention.
 *
 * Configuration is blackhole-py's configure_unpacker(UNPACKER0, addr, BF16, SRCA) from the deleted
 * tests/movement/unpacker/unpack.py (hardware-tested), without its UNPACK_SYNC commit (no base is rewritten while
 * unpacks are in flight). Then UNPACR of one 256-datum BF16 face from `src`, AddrMode 0 (same face every time), no
 * SetDatValid, so SrcA bank 0 stays with the unpacker and the stream never waits for math. Runs until PK_STOP or `max`
 * UNPACRs. aux[0] start, aux[1] end, aux[2] UNPACRs pushed. */
#include "pack.h"

enum { P_SRC, P_MAX };
enum { SITE_DONE = 1 };

KERNEL kernel_main(void) {
  u32 src = PARAM(P_SRC), max = PARAM(P_MAX);
  static const unsigned short W[][2] = {{44, 0}, {45, 0}, {48, 0}, {49, 0}, {50, 0x100}, {53, 0}, {57, 512},
                                        {66, 0}, {67, 0}, {73, 3}, {74, 0}, {75, 0}, {92, 0}, {93, 0}};
  for (u32 i = 0; i < sizeof W / sizeof W[0]; i++) cfg_write(W[i][0], W[i][1]);
  cfg_write(64, 5 | 0x10);            /* descriptor: BF16, uncompressed, XDim 0 (A reads Tile_x_dim) */
  cfg_write(65, 1 | 4 << 16);         /* YDim 1, ZDim 4 */
  cfg_write(72, 0x20 | 5);            /* out BF16, ovrd format */
  cfg_write(56, 2 | 32 << 16);        /* Src side strides: X 2 B, Y 32 B */
  cfg_write(84, 64 | 64 << 16);       /* Dest_cntx: SrcA row 0 */
  cfg_write(86, 256 | 256 << 16);     /* Tile_x_dim: one face */
  cfg_write(76, (src >> 4) - 1);
  cfg_write(77, (src >> 4) - 1);
  cfg_commit(77);
  TTINSN(SETC16(41, 0));
  TTINSN(SETC16(5, 4));
  TTINSN(TT_SETADCXX(1, 255, 0));
  TTINSN(TT_SETADCZW(3, 0, 0, 0, 0, 0xF));
  TTINSN(TT_STALLWAIT(STALL_UNPACK, WAIT_TRISC_CFG));
  tensix_drain();

  u32 t0 = now(), n = 0;
  write32(PK_UNPACK_UP, t0 | 1);
  while (n < max && (fence(), !read32(PK_STOP))) {  /* fence: L0 data cache, re-read L1 */
    for (u32 i = 0; i < 8; i++) TTINSN(TT_UNPACR(0, 0, 1, 0, 1));
    n += 8;
  }
  u32 t1 = now();
  TTINSN(TT_STALLWAIT(STALL_SYNC, WAIT_UNPACK0));
  tensix_drain();
  write32(RES_AUX, t0); write32(RES_AUX + 4, t1); write32(RES_AUX + 8, n);
  probe_done();
}
