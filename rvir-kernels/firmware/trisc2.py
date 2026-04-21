"""TRISC2 firmware — pack thread (Tensix thread 2).

Same structure as TRISC0 but:
  - trisc2_run byte is at SUBORDINATE_SYNC + 3  (0x6B)
  - Kernel text from LM_TEXT_TRISC2 (offset 52)
  - No INIT_SYNC_REGISTERS handling (TRISC0-only)
"""
from extra.emu.rvir import Kernel
from extra.emu.rvlib import *
from extra.emu import memory as _M

def build():
  k = Kernel(base=_M.TRISC2_FW_BASE)

  # ── _start ──────────────────────────────────────────────────────
  emit_start(k, TRISC_SP)

  # ── main (never returns) ────────────────────────────────────────
  with k.func("main", saves=[s0, s1, s2, s3, s4]):

    # ── configure_csr ───────────────────────────────────────────
    emit_configure_csr(k)

    # ── do_crt1: zero 0x420 BSS ────────────────────────────────
    emit_do_crt1(k, TRISC2_SCRATCH, 0, 0x420)

    # ── zero Tensix regfile ─────────────────────────────────────
    zero_regfile(k)

    # ── seed PRNG, wait ~600 cycles ─────────────────────────────
    seed_prng(k)

    # ── read core_info ──────────────────────────────────────────
    read_core_info(k, s0, s1)

    # ── signal DONE ─────────────────────────────────────────────
    signal_done(k, TRISC2_RUN)

    # ================================================================
    # Main dispatch loop (infinite)
    # ================================================================
    with k.while_true():

      # ── wait for trisc2_run == GO ───────────────────────────
      wait_for_go(k, TRISC2_RUN)

      # ── read launch message ─────────────────────────────────
      read_launch_msg(k, s2, s3, s4)

      # ── call TRISC2 kernel ──────────────────────────────────
      call_kernel(k, s3, s4, LM_TEXT_TRISC2)

      # ── tensix_sync ─────────────────────────────────────────
      tensix_sync(k, tmp0=s2, tmp1=t0)

      # ── signal done ─────────────────────────────────────────
      signal_done(k, TRISC2_RUN)

  # ── pack ────────────────────────────────────────────────────────
  return pack_firmware(k, _M.TRISC2_FW_BASE, bss_size=0x420)
