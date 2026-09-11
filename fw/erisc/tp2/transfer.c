/* E1 bring-up service. Uses the hardware's trained TT-link queue 1.
 * No tt-metal runtime or firmware headers. Host grants one outstanding slot.
 * accepted != delivered: host verifies peer bytes AND hardware acknowledgement
 * before reusing TX storage. Fixed local/remote slots prevent arbitrary writes.
 */
#include <stdint.h>
#define REG(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define MAIL 0x60000u
#define TX 0xffb91000u
static inline void fence(void) { __asm__ volatile("fence iorw, iorw" ::: "memory"); }
static int wait_command(void) {
    unsigned budget = 10000000;
    (void)REG(TX+4);
    while (REG(TX+8) & (1u<<16)) if (!--budget) return -1;
    return 0;
}
void main(void) {
    uint32_t seen = 0;
    REG(MAIL+16) = 0xe1000001;
    for (;;) {
        uint32_t sequence = REG(MAIL);
        if (sequence == seen) continue;
        fence();
        uint32_t size = REG(MAIL+4);
        if (!sequence || !size || size > 16384 || (size & 15) || wait_command()) {
            REG(MAIL+12) = 1;
            for (;;) {}
        }
        REG(TX+0x14) = 0x50000;
        REG(TX+0x18) = size;
        REG(TX+0x1c) = 0x54000;
        fence();
        REG(TX+4) = 2;
        if (wait_command()) {
            REG(MAIL+12) = 2;
            for (;;) {}
        }
        seen = sequence;
        fence();
        REG(MAIL+8) = sequence;
    }
}
