/* Two-tile timing (ping.py): a sender updates a word in the receiver's L1, the receiver polls it.
 *
 * sender:   `count` times, every `period` cycles: fire one update to peer:FLAG, log t_fire. The update is either an
 *           inline 4-byte write of t_fire itself, or an atomic increment (posted, or non-posted with the old value
 *           returned to local FLAG2; then it also waits for the atomic response and logs t_resp).
 * receiver: poll FLAG until it changes, log (value, t_seen), `count` times.
 * With one tile's clock offset known (inline writes both ways, ping.py), t_seen - t_fire is the one-way time.
 * Control words as in the llama kernels: VC static 1, non-posted atomic 0x2091. */
#include "probe.h"

enum { P_ROLE, P_NOC, P_PEER, P_COUNT, P_PERIOD, P_OP, P_BUF };
enum { ROLE_SEND, ROLE_RECV };
enum { OP_INLINE, OP_ATOMIC_POSTED, OP_ATOMIC_NP };
enum { SITE_READY = 1, SITE_FLAG, SITE_RESP };

KERNEL kernel_main(void) {
  u32 count = PARAM(P_COUNT);
  if (PARAM(P_ROLE) == ROLE_RECV) {
    u32 last = read32(FLAG), v;
    for (u32 i = 0; i < count; i++) {
      WAIT_L1((v = read32(FLAG)) != last, SITE_FLAG);
      u32 t = now();
      log_word(2 * i, v);
      log_word(2 * i + 1, t);
      last = v;
    }
    write32(RES_COUNT, 2 * count);
    probe_done();
  }
  u32 noc = PARAM(P_NOC), c = CMDBUF(noc, PARAM(P_BUF)), peer = PARAM(P_PEER), op = PARAM(P_OP), period = PARAM(P_PERIOD);
  u32 resp = NIU_STATUS(noc, CNT_ATOMIC_RESP);
  WAIT_CMD_READY(c, SITE_READY);
  if (op == OP_INLINE) {
    cmd_inline(c, peer, FLAG, CTRL_VC_STATIC | CTRL_STATIC_VC(1));
  } else {
    write32(c + C_TARG_LO, FLAG); write32(c + C_TARG_MID, 0); write32(c + C_TARG_COORD, peer);
    write32(c + C_RET_LO, FLAG2); write32(c + C_RET_MID, 0); write32(c + C_RET_COORD, my_coord(noc));
    cmd_common(c, 0, AT_INCREMENT, CTRL_ATOMIC | CTRL_VC_STATIC | CTRL_STATIC_VC(1) | (op == OP_ATOMIC_NP ? CTRL_RESP_MARKED : 0));
    write32(c + C_AT_DATA, 1);
  }
  u32 next = now() + 2000;
  for (u32 i = 0; i < count; i++) {
    while ((int)(now() - next) < 0) {}
    WAIT_CMD_READY(c, SITE_READY);
    u32 base = read32(resp);
    fence();
    u32 t = now();
    if (op == OP_INLINE) write32(c + C_AT_DATA, t);
    write32(c + C_CMD_CTRL, 1);
    fence();
    u32 t1 = 0;
    if (op == OP_ATOMIC_NP) { WAIT_UNTIL(read32(resp) != base, SITE_RESP); t1 = now(); }
    log_word(2 * i, t);
    log_word(2 * i + 1, t1);
    next += period;
  }
  WAIT_CMD_READY(c, SITE_READY);
  write32(RES_COUNT, 2 * count);
  probe_done();
}
