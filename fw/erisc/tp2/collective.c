/* Persistent TP=2 L1 exchange. All 16-KiB payloads stay in Ethernet L1.
 * One outstanding vector; exact per-worker generation flags and peer credits.
 * Each <=4096-byte hardware packet is acknowledged before its source can be
 * reused. E0 and the firmware-configured queue/classifier remain untouched.
 */
#include <stdint.h>
#define REG(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define MAIL 0x60000u
#define TX 0xffb91000u
#define RX 0xffb95000u
#define PEER_READY (MAIL+0x20)
#define SEND_MARKER (MAIL+0x40)
#define LOCAL_READY (MAIL+0x60)
#define PEER_CREDIT (MAIL+0x80)
#define PRODUCED (MAIL+0x200)
#define CONSUMED (MAIL+0x400)
#define STATS (MAIL+0x600)
#define CLOCK 0xffb121f0u
static inline void fence(void) { __asm__ volatile("fence iorw, iorw" ::: "memory"); }
static void fail(unsigned code) {
    REG(MAIL+12)=code;
    for (;;) {}
}
static void wait_value(uint32_t addr, uint32_t expected, uint32_t mask) {
    unsigned budget=1000000000;
    while ((REG(addr)&mask)!=expected) if (!--budget) fail(1);
    fence();
}
static void send(uint32_t src, uint32_t dst, uint32_t size, uint32_t *ack) {
    (void)REG(TX+4);
    wait_value(TX+8,0,1u<<16);
    REG(TX+0x14)=src; REG(TX+0x18)=size; REG(TX+0x1c)=dst;
    fence(); REG(TX+4)=2; (void)REG(TX+4);
    wait_value(TX+8,0,1u<<16);
    *ack=(*ack+1)&255;
    wait_value(RX+0x44,*ack,255);
}
void main(void) {
    const uint32_t producers=REG(MAIL+24);
    if (!producers || producers>117 || REG(TX+12)<4114) fail(2);
    uint32_t ack=REG(RX+0x44)&255;
    REG(MAIL+16)=0xe1000001;
    for (uint32_t seq=1; seq; ++seq) {
        uint32_t start=REG(CLOCK);
        /* Waiting for a new token is an idle state, not a link timeout. */
        for (uint32_t i=0;i<producers;++i) while (REG(PRODUCED+4*i)!=seq) {}
        fence();
        uint32_t produced=REG(CLOCK);
        if ((seq-1)%64==0) for (unsigned i=0;i<4;++i) REG(STATS+4*i)=0;
        for (uint32_t off=0;off<16384;off+=4096) send(0x50000+off,0x54000+off,4096,&ack);
        REG(SEND_MARKER)=seq; fence();
        send(SEND_MARKER,PEER_READY,16,&ack);
        wait_value(PEER_READY,seq,0xffffffff);
        wait_value(RX+0x50,0,0xffffffff);
        REG(LOCAL_READY)=seq; fence();
        uint32_t exchanged=REG(CLOCK);
        for (uint32_t i=0;i<32;++i) wait_value(CONSUMED+4*i,seq,0xffffffff);
        send(SEND_MARKER,PEER_CREDIT,16,&ack);
        wait_value(PEER_CREDIT,seq,0xffffffff);
        wait_value(RX+0x50,0,0xffffffff);
        uint32_t finished=REG(CLOCK);
        /* Last-token cycle totals. Producer time includes host gaps; the other
         * two intervals attribute exchange and consumer/credit waiting. */
        REG(STATS)+=produced-start;
        REG(STATS+4)+=exchanged-produced;
        REG(STATS+8)+=finished-exchanged;
        REG(STATS+12)=seq;
        REG(MAIL+8)=seq;
    }
    fail(3);
}
