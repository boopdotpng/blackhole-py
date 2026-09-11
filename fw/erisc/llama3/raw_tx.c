#include "bhp.h"
#if !defined(__riscv)
#error "raw_tx.c is ERISC device code; do not execute on the host"
#endif
static void fence_io(void) { __asm__ volatile("fence iorw, iorw" ::: "memory"); }
int bhp_raw_send(unsigned q, unsigned header, uint32_t src, uint32_t size,
                 unsigned budget, void (*service)(void)) {
    if(q>2 || header>9 || (src&15u) || size<32 || size>32+BHP_MAX_PAYLOAD ||
       src>=0x70000 || size>0x70000-src || !service) return -1;
    volatile uint32_t *r=(volatile uint32_t *)(uintptr_t)(0xffb90000u+q*0x1000u);
    /* Reading CMD orders the preceding command write before STATUS. */
    (void)r[1];
    while(r[2] & (1u<<16)) { if(!budget--) return -2; service(); }
    /* Raw mode must have been provisioned by our board adapter, not here. */
    if((r[0]&1u) || r[0x0c/4]<size) return -1; /* forbid implicit fragmentation */
    r[0x80/4]=(r[0x80/4]&~15u)|header;
    r[0x14/4]=src;
    r[0x18/4]=size;
    fence_io();
    r[1]=1; /* raw TX, NOT TT-link L1 remote write */
    (void)r[1];
    while(r[2] & (1u<<16)) { if(!budget--) return -2; service(); }
    fence_io();
    return 0;
}
