/* BHP1 raw Ethernet transport. Original implementation, hardware-spec based.
 * No tt-metal dependency. A payload codec, not a bootable firmware image. */
#ifndef BHP_H
#define BHP_H
#include <stddef.h>
#include <stdint.h>
#define BHP_HEADER 32u
#define BHP_MAX_PAYLOAD 8192u
struct bhp_packet {
    uint32_t epoch, sequence, length;
    uint16_t source, destination, slot;
    uint8_t kind, hops;
    const uint8_t *payload;
};
int bhp_decode(const uint8_t *wire, size_t size, struct bhp_packet *out);
int bhp_encode(uint8_t *wire, size_t capacity, const struct bhp_packet *p);
/* queue/header entry must be exclusively owned and configured for raw mode.
 * src points to BHP_HEADER+payload bytes in local L1. Return 0 once RAW data
 * has been read by TX, -1 invalid args, -2 timeout (do NOT recycle source).
 * poll_budget is iteration count, not a time unit. service must preserve link
 * management and invalidate L1 as required by the independently built runtime. */
int bhp_raw_send(unsigned queue, unsigned header_entry, uint32_t src,
                 uint32_t size, unsigned poll_budget, void (*service)(void));
#endif
