/* Per-EXEC entry stub for the exported llama1b kernels, compiled once per (program K, role ROLE) by llama1b.py.
 * EXEC launches one program on every core, but specialize() gives cores different kernel images, so all images are
 * installed resident and each core's entry table (written once by llama1b.py) says which one it runs.
 * The worker firmware has already reset Tensix state for this launch. */
#include "hw.h"

#define ENTRY_TABLE 0x8400

KERNEL kernel_main(void) { JUMP(read32(ENTRY_TABLE + 0x20 * K + 4 * ROLE)); }
