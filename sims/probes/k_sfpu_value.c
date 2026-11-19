/* SFPU value checks through Dst (sfpu.py: hazards values, matrix values, loadmacro values). Three TRISCs, one GO:
 *   trisc0 (PART 0)  unpack INPUT (8192 F32 words) straight into FP32 Dst tile 0   (unpack.py emit_unpack_to_dst)
 *   trisc1 (PART 1)  take Dst (ZEROACC, MATH_DONE / UNPACK_TO_DEST handshake), run COMPUTE, publish to the packer
 *   trisc2 (PART 2)  pack Dst tile 0 rows to OUTPUT as F32                     (pack.py emit_pack_dst_to_cb)
 * Port of the old value_images()/run() (test_sfpu_hazards.py, test_sfpu_matrix.py, test_sfpu_loadmacro.py).
 * COMPUTE is the case's stream of T(...) word blocks and D drains (sfpu.py), the SFPSTOREs into Dst included.
 * Cross-thread waits are RISC polls of the Tensix semaphores, bounded (sfpu.h). INPUT/OUTPUT moved from the old
 * 0x50000/0x60000 (now trisc0/trisc1 RES/LOG) to 0x100000/0x110000. */
#include "sfpu.h"

#define INPUT  0x100000
#define OUTPUT 0x110000
#define WORDS  8192

enum { SITE_UNPACK_CFG = 1, SITE_MATH_DONE, SITE_UNPACK_TO_DEST, SITE_MATH_PACK };

KERNEL kernel_main(void) {
  if (PARAM(0)) {  /* [0] 1 = write [1] to the prefetch control (0: the old prefetch-off runs); every part does it */
    write32(CFG_RISC_PREFETCH_CTRL, PARAM(1));
    fence();
  }
  record_config();
#if PART == 0
  unpack_f32_to_dst(INPUT, WORDS * 4, SITE_UNPACK_CFG);  /* sites 1 (config sync) and 2 (MATH_DONE) */
#elif PART == 1
  math_take_dst(SITE_UNPACK_TO_DEST);
  COMPUTE
  publish_dst();
#elif PART == 2
  pack_dst_rows_f32(OUTPUT, WORDS / 16, SITE_MATH_PACK);
#else
#error "PART must be 0, 1 or 2"
#endif
  tensix_drain();
  probe_done();
}
