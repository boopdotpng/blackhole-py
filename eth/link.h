/* Ethernet-tile L1 layout shared by the E1 forwarder and the worker all-reduce kernel. Both cards use the same
   channel and the same layout; TT-link data from the peer lands directly in RECV/FLAG.
   Each all-reduce has a tag (replay * NSLOT + slot, never 0 in a session); buffers alternate by tag parity. */
#ifndef LINK_H
#define LINK_H

#define LINK_BOX    0x30000              /* E1 status: [0] magic [1] heartbeat [4] last tag sent [5] last malformed tag */
#define LINK_READY  0x30400              /* worker w writes {tag, bytes, workers} at LINK_READY + 16 w (64 max) */
#define LINK_FLAGSRC 0x30800             /* E1's outgoing flag packets, 16 B per parity */
#define LINK_STAGE(p) (0x40000 + (p) * 0x8000)   /* outgoing partials, written by local workers */
#define LINK_RECV(p)  (0x50000 + (p) * 0x8000)   /* the peer's partials, written by the peer E1 */
#define LINK_FLAG(p)  (0x60000 + (p) * 16)       /* the peer's tag once RECV(p) is complete */
#define LINK_MAX_BYTES 0x8000
#define LINK_MAGIC 0xE1F0A4D1

#endif
