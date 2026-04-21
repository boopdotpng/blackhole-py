"""NCRISC firmware — data movement subordinate core (DM1).

Boot sequence:
  1. configure_csr, do_crt1
  2. Read logical coordinates, risc_init
  3. Signal DONE to BRISC (write 0 to ncrisc_run)

Dispatch loop:
  - Wait for ncrisc_run == RUN_SYNC_MSG_GO
  - Parse launch_msg, compute kernel_lma
  - Call NCRISC kernel
  - Signal DONE
"""
import struct
from extra.emu.rvir import Kernel
from extra.emu.rvlib import *
from extra.emu import memory as _M

def build():
  k = Kernel(base=_M.NCRISC_FW_BASE)

  # ── _start ──────────────────────────────────────────────────────
  emit_start(k, NCRISC_SP)

  # ── main (never returns) ────────────────────────────────────────
  with k.func("main", saves=[s0, s1, s2, s3, s4]):

    # ── configure_csr ───────────────────────────────────────────
    emit_configure_csr(k)

    # ── do_crt1(NCRISC_SCRATCH, 4 data, 0x864 BSS) ─────────────
    emit_do_crt1(k, NCRISC_SCRATCH, 4, 0x864)

    # ── noc_bank_table_init / noc_worker_logical_to_virtual ─────
    # (NOC registers already pre-populated by emulator)

    # ── risc_init: read NOC IDs ─────────────────────────────────
    read_noc_ids(k, t1, t2)

    # ── read core_info.logical_x/y ─────────────────────────────
    read_core_info(k, s0, s1)      # s0 = logical_x, s1 = logical_y

    # ── signal_ncrisc_completion: ncrisc_run = DONE ─────────────
    signal_done(k, NCRISC_RUN)

    # ================================================================
    # Main dispatch loop (infinite)
    # ================================================================
    with k.while_true():

      # ── wait for ncrisc_run == GO or LOAD ───────────────────
      with k.while_true() as Lw:
        k.lbu(t0, zero, NCRISC_RUN)
        k.li(t1, RUN_SYNC_MSG_GO)
        k.beq(t0, t1, Lw.brk)
        k.li(t1, RUN_SYNC_MSG_LOAD)
        k.beq(t0, t1, Lw.brk)
        k.emit(FENCE())

      # ── read launch message ─────────────────────────────────
      read_launch_msg(k, s2, s3, s4)

      # ── wait for GO (may have entered on LOAD) ──────────────
      wait_for_go(k, NCRISC_RUN)

      # ── call NCRISC kernel ──────────────────────────────────
      call_kernel(k, s3, s4, LM_TEXT_NCRISC)

      # ── signal done ─────────────────────────────────────────
      signal_done(k, NCRISC_RUN)

  # ── pack ────────────────────────────────────────────────────────
  ldm_data = struct.pack('<I', SUBORDINATE_SYNC)   # 0x68 (ncrisc_run ptr)
  return pack_firmware(k, _M.NCRISC_FW_BASE, ldm_data, bss_size=0x864)
