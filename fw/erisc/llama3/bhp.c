#include "bhp.h"
static uint32_t get32(const uint8_t *p) {
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static uint16_t get16(const uint8_t *p) { return p[0] | (uint16_t)p[1]<<8; }
static void put32(uint8_t *p, uint32_t v) { for(unsigned i=0;i<4;i++) p[i]=(uint8_t)(v>>(i*8)); }
static void put16(uint8_t *p, uint16_t v) { p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8); }
static uint32_t crc_bytes(uint32_t crc, const uint8_t *p, size_t n) {
    while(n--) {
        crc ^= *p++;
        for(unsigned i=0;i<8;i++) crc=(crc>>1) ^ (0xedb88320u & (0u-(crc&1u)));
    }
    return crc;
}
static uint32_t crc_packet(const uint8_t *wire, size_t n) {
    return ~crc_bytes(crc_bytes(~0u, wire, 28), wire+32, n-32);
}
static int valid(const struct bhp_packet *p) {
    return p->epoch && p->sequence && p->hops && p->kind>=1 && p->kind<=3 &&
        p->length<=BHP_MAX_PAYLOAD && (p->kind!=2 || p->length==0);
}
int bhp_decode(const uint8_t *w, size_t n, struct bhp_packet *p) {
    if(!w || !p || n<32 || w[0]!='B' || w[1]!='H' || w[2]!='P' || w[3]!='1' ||
       w[4]!=1 || get16(w+6) || w[23]) return -1;
    struct bhp_packet v = {0};
    v.kind=w[5]; v.epoch=get32(w+8); v.sequence=get32(w+12);
    v.source=get16(w+16); v.destination=get16(w+18); v.slot=get16(w+20);
    v.hops=w[22]; v.length=get32(w+24); v.payload=w+32;
    if(!valid(&v) || n != 32u+v.length || crc_packet(w,n)!=get32(w+28)) return -1;
    *p=v;
    return 0;
}
int bhp_encode(uint8_t *w, size_t n, const struct bhp_packet *p) {
    if(!w || !p || !valid(p) || n<32u+p->length || (p->length && !p->payload)) return -1;
    w[0]='B';w[1]='H';w[2]='P';w[3]='1';w[4]=1;w[5]=p->kind;
    put16(w+6,0);put32(w+8,p->epoch);put32(w+12,p->sequence);
    put16(w+16,p->source);put16(w+18,p->destination);put16(w+20,p->slot);
    w[22]=p->hops;w[23]=0;put32(w+24,p->length);
    for(uint32_t i=0;i<p->length;i++) w[32+i]=p->payload[i];
    put32(w+28,crc_packet(w,32u+p->length));
    return (int)(32u+p->length);
}
