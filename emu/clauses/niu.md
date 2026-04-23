# niu

**Source:** [`niu.md`](../specs/niu.md)

## Address space

### `NIU.ADDR.NOC0_BASE`
§1 Address Space / NoC0

> NoC0 NIU is memory-mapped at 0xFFB20000, size 0x10000.

### `NIU.ADDR.NOC1_BASE`
§1 Address Space / NoC1

> NoC1 NIU is memory-mapped at 0xFFB30000, size 0x10000.

### `NIU.CMDBUF.STRIDE`
§2 Command Buffer Registers

> 4 command buffers at offsets 0x000, 0x800, 0x1000, 0x1800 (stride 0x800 = 2048 bytes).

### `NIU.CMDBUF.FIRE`
§8 Transaction Execution

> Writing 0x1 to NOC_CMD_CTRL (+0x40) fires the command; CMD_CTRL reads 0x0 when ready.

### `NIU.CMDBUF.AVAIL`
_§7 Misc Control / CMD_BUF_AVAIL_

> CMD_BUF_AVAIL (offset 0x64) returns all-available (0x1F1F1F1F) in emulator.

### `NIU.CFG.NOC_ID_LOGICAL`
_§5 Configuration Registers / NOC_ID_LOGICAL_

> NOC_ID_LOGICAL at offset 0x148 from NIU base holds (y<<6)|x for the tile's logical coordinates. Must be pre-populated before firmware boots.

### `NIU.CFG.NODE_ID`
_§2 Command Buffer Registers / NOC_NODE_ID_

> NOC_NODE_ID at +0x44 reads (y<<6)|x — the tile's physical coordinate.

### `NIU.XY.UNICAST_ENCODING`
§4 XY Coordinate Encoding / Unicast

> Unicast: bits [5:0]=x, bits [11:6]=y in NOC_TARG_ADDR_HI / NOC_RET_ADDR_HI.

### `NIU.XY.MCAST_ENCODING`
§4 XY Coordinate Encoding / Multicast

> Multicast (BRCST_PACKET=1): [5:0]=end_x, [11:6]=end_y, [17:12]=start_x, [23:18]=start_y.

### `NIU.TX.READ`
§8 Transaction Execution / Read

> AT=0,WR=0: copy from remote TARG address to local RET address.

### `NIU.TX.WRITE`
§8 Transaction Execution / Write

> AT=0,WR=1,WR_INLINE=0: copy length bytes from local TARG to remote RET address.

### `NIU.TX.INLINE_WRITE`
§8 Transaction Execution / Inline Write

> AT=0,WR=1,WR_INLINE=1: write 4 bytes of NOC_AT_DATA to TARG address.

### `NIU.COUNTER.WR_ACK`
_§6 Status Counters / NIU_MST_WR_ACK_RECEIVED_

> NIU_MST_WR_ACK_RECEIVED increments after non-posted (RESP_MARKED=1) write completes.

### `NIU.COUNTER.POSTED_WR`
_§6 Status Counters / NIU_MST_POSTED_WR_REQ_SENT_

> NIU_MST_POSTED_WR_REQ_SENT increments after posted (RESP_MARKED=0) write completes.

### `NIU.COUNTER.NONPOSTED_WR`
_§6 Status Counters / NIU_MST_NONPOSTED_WR_REQ_SENT_

> NIU_MST_NONPOSTED_WR_REQ_SENT increments after non-posted write completes.

### `NIU.COUNTER.RD_RESP`
_§6 Status Counters / NIU_MST_RD_RESP_RECEIVED_

> NIU_MST_RD_RESP_RECEIVED increments after DMA read response is received.

### `NIU.COUNTER.RD_REQ`
_§6 Status Counters / NIU_MST_RD_REQ_SENT_

> NIU_MST_RD_REQ_SENT increments after read request is sent.

### `NIU.MCAST.RECT_DELIVERY`
§14 Multicast Delivery Model / Delivery algorithm

> Multicast (BRCST_PACKET=1) delivers to all tiles (x,y) with start_x<=x<=end_x and start_y<=y<=end_y. Tiles not registered in the NOC routing table are ignored.

### `NIU.MCAST.SRC_INCLUDE`
_§14 Multicast / BRCST_SRC_INCLUDE_

> BRCST_SRC_INCLUDE=0 (default): sender's (x,y) is excluded even if inside the rect. BRCST_SRC_INCLUDE=1: sender also receives the write.

### `NIU.MCAST.WR_ACK_PER_DEST`
§14 Multicast / Counter accounting

> For non-posted multicast: NIU_MST_WR_ACK_RECEIVED increments by 1 per destination tile that ACKs; NIU_MST_NONPOSTED_WR_REQ_SENT increments by 1 (one command).

### `NIU.MCAST.BRCST_XY_ROUTING_AXIS`
_§14 Multicast / NOC_CMD_BRCST_XY_

> BRCST_XY (bit 16 of NOC_CTRL) selects the major routing axis (X-first vs Y-first) for the multicast packet. It affects routing topology and congestion only — it does not change which tiles receive the write.
