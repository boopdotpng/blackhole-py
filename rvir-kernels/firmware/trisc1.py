"""TRISC1 firmware — math thread (Tensix thread 1).

Same boot sequence as TRISC0/2 but:
  - Smaller BSS (0x1C bytes vs 0x420)
  - No CB interface setup (math core doesn't touch CBs directly)
  - No INIT_SYNC_REGISTERS handling (TRISC0-only)
"""
from extra.emu.rvir import Kernel
from extra.emu.rvlib import *
from extra.emu import memory as _M

def build():
  k = Kernel(base=_M.TRISC1_FW_BASE)

  # ── _start ──────────────────────────────────────────────────────
  emit_start(k, TRISC_SP)

  # ── main (never returns) ────────────────────────────────────────
  with k.func("main", saves=[s0, s1, s2, s3]):

    # ── configure_csr ───────────────────────────────────────────
    emit_configure_csr(k)

    # ── do_crt1: zero 0x1C BSS (no init data) ──────────────────
    emit_do_crt1(k, TRISC1_SCRATCH, 0, 0x1C)

    # ── zero Tensix regfile ─────────────────────────────────────
    zero_regfile(k)

    # ── seed PRNG, wait ~600 cycles ─────────────────────────────
    seed_prng(k)

    # ── read core_info ──────────────────────────────────────────
    read_core_info(k, s0, s1)

    # ── signal DONE ─────────────────────────────────────────────
    signal_done(k, TRISC1_RUN)

    # ================================================================
    # Main dispatch loop (infinite)
    # ================================================================
    with k.while_true():

      # ── wait for trisc1_run == GO ───────────────────────────
      wait_for_go(k, TRISC1_RUN)

      # ── read launch message ─────────────────────────────────
      read_launch_msg(k, s2, s3, s2)

      # ── call TRISC1 kernel ──────────────────────────────────
      call_kernel(k, s3, s2, LM_TEXT_TRISC1)

      # ── tensix_sync ─────────────────────────────────────────
      tensix_sync(k, tmp0=s3, tmp1=t0)

      # ── signal done ─────────────────────────────────────────
      signal_done(k, TRISC1_RUN)

  # ── pack ────────────────────────────────────────────────────────
  return pack_firmware(k, _M.TRISC1_FW_BASE, bss_size=0x1C)
