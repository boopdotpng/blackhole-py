/* Command issue cost (issue.py): how fast one RISC can send commands, and how long a command buffer stays busy.
 *
 * `count` commands of one kind, round-robin over `nbuf` command buffers (0..nbuf-1) of one NoC. Per command:
 * [wait until the buffer is ready] [store `nregs` address registers (2: target lo + coordinate, the per-page
 * minimum)] [fence] CMD_CTRL = 1 [fence] [poll the buffer until ready again, as the llama exports do, and log how long
 * that took]. aux = {t_first_send, t_last_send, t_all_done}; log = busy time per command when polling after send. */
#include "probe.h"

enum { P_FLAGS, P_COUNT, P_SIZE, P_TARGET, P_DRAM, P_OP, P_NBUF, P_NOC };
#define F_FENCE_BEFORE 1
#define F_FENCE_AFTER 2
#define F_POLL_AFTER 4
#define F_REGS 8  /* rewrite target lo + coordinate every command */
enum { OP_POSTED, OP_NP_WRITE, OP_READ };
enum { SITE_READY = 1, SITE_DONE };

KERNEL kernel_main(void) {
  u32 flags = PARAM(P_FLAGS), count = PARAM(P_COUNT), size = PARAM(P_SIZE), target = PARAM(P_TARGET);
  u32 dram = PARAM(P_DRAM), op = PARAM(P_OP), nbuf = PARAM(P_NBUF), noc = PARAM(P_NOC);
  u32 coords[8];
  for (u32 b = 0; b < 8; b++) coords[b] = dram ? dram_coord(b, 0) : target;
  u32 remote = dram ? 0x40000000 : PAYLOAD;
  u32 ctrl = CTRL_VC_STATIC | CTRL_STATIC_VC(1) | (op == OP_NP_WRITE ? CTRL_RESP_MARKED : 0);
  for (u32 b = 0; b < nbuf; b++) {
    u32 c = CMDBUF(noc, b);
    WAIT_CMD_READY(c, SITE_READY);
    if (op == OP_READ) cmd_read(c, noc, coords[0], remote, PAYLOAD + b * 0x10000, size, ctrl);
    else cmd_write(c, noc, PAYLOAD + b * 0x10000, coords[0], remote, size, ctrl);
    write32(c + C_PACKET_TAG, TAG_TID(1));
  }
  u32 lo_reg = op == OP_READ ? C_TARG_LO : C_RET_LO, coord_reg = op == OP_READ ? C_TARG_COORD : C_RET_COORD;
  u32 outst = NIU(noc) + 0x240 + 4, outg = NIU(noc) + 0x280 + 4;
  u32 t_first = 0, t_last = 0, b = 0, addr = remote;
  for (u32 i = 0; i < count; i++) {
    u32 c = CMDBUF(noc, b);
    WAIT_CMD_READY(c, SITE_READY);
    if (flags & F_REGS) { write32(c + lo_reg, addr); write32(c + coord_reg, coords[i & 7]); }
    if (flags & F_FENCE_BEFORE) fence();
    u32 t = now();
    write32(c + C_CMD_CTRL, 1);
    if (flags & F_FENCE_AFTER) fence();
    if (flags & F_POLL_AFTER) {
      WAIT_CMD_READY(c, SITE_READY);
      log_word(i, now() - t);
    }
    if (i == 0) t_first = t;
    t_last = t;
    if (dram && (i & 7) == 7) addr += size;
    if (++b == nbuf) b = 0;
  }
  if (op == OP_POSTED) WAIT_UNTIL(!read32(outg), SITE_DONE);
  else WAIT_UNTIL(!read32(outst), SITE_DONE);
  u32 t_done = now();
  write32(RES_AUX, t_first);
  write32(RES_AUX + 4, t_last);
  write32(RES_AUX + 8, t_done);
  write32(RES_COUNT, flags & F_POLL_AFTER ? count : 0);
  probe_done();
}
