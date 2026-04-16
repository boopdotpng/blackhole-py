"""TRISC0 firmware — unpack thread (Tensix thread 0).

Boot sequence:
  1. configure_csr, do_crt1 (zero 0x420 BSS)
  2. Zero Tensix regfile (64 GPRs)
  3. Reset cfg_state_id, seed PRNG, wait ~600 cycles
  4. Read logical coordinates
  5. Signal DONE (trisc0_run = 0)

Dispatch loop:
  - Wait for trisc0_run == GO  (also handles INIT_SYNC_REGISTERS)
  - Parse launch_msg, call TRISC0 kernel
  - tensix_sync (write/read PCBUF_COPROC_DONE)
  - Signal DONE
"""
from extra.emu.rvir import Kernel
from extra.emu.rvlib import *
from extra.emu import memory as _M

def build():
    k = Kernel(base=_M.TRISC0_FW_BASE)

    # ── _start ──────────────────────────────────────────────────────
    emit_start(k, TRISC_SP)

    # ── main (never returns) ────────────────────────────────────────
    with k.func("main", saves=[s0, s1, s2, s3, s4]):

        # ── configure_csr ───────────────────────────────────────────
        emit_configure_csr(k)

        # ── do_crt1: zero 0x420 BSS (no init data) ─────────────────
        emit_do_crt1(k, TRISC0_SCRATCH, 0, 0x420)

        # ── zero Tensix regfile (64 × 32-bit GPRs at 0xFFE00000) ──
        zero_regfile(k)

        # ── reset cfg_state_id = 0 (write to LDM) ──────────────────
        # cfg_state_id lives in BSS; already zeroed by do_crt1

        # ── seed PRNG and wait ~600 cycles ──────────────────────────
        seed_prng(k)

        # ── read core_info.logical_x/y ─────────────────────────────
        read_core_info(k, s0, s1)

        # ── signal DONE ─────────────────────────────────────────────
        signal_done(k, TRISC0_RUN)

        # ================================================================
        # Main dispatch loop (infinite)
        # ================================================================
        with k.while_true():

            # ── wait for trisc0_run == GO ───────────────────────────
            # TRISC0 also handles INIT_SYNC_REGISTERS (value 3):
            #   zero tiles_received & tiles_acked for streams 8..39,
            #   then signal DONE and keep waiting.
            with k.while_true() as Lw:
                k.lbu(t0, zero, TRISC0_RUN)
                k.li(t1, RUN_SYNC_MSG_GO)
                k.beq(t0, t1, Lw.brk)
                # Check for INIT_SYNC_REGISTERS
                k.li(t1, RUN_SYNC_MSG_INIT_SYNC_REGISTERS)
                k.bne(t0, t1, ".no_sync_init")
                # ── init_sync_registers ─────────────────────────────
                init_sync_registers(k)
                signal_done(k, TRISC0_RUN)
                k.label(".no_sync_init")
                k.emit(FENCE())

            # ── read launch message ─────────────────────────────────
            read_launch_msg(k, s2, s3, s4)

            # ── call TRISC0 kernel ──────────────────────────────────
            call_kernel(k, s3, s4, LM_TEXT_TRISC0)

            # ── tensix_sync: write 0 to PCBUF_COPROC_DONE, read back ──
            tensix_sync(k, tmp0=s2, tmp1=t0)

            # ── signal done ─────────────────────────────────────────
            signal_done(k, TRISC0_RUN)

    # ── pack ────────────────────────────────────────────────────────
    return pack_firmware(k, _M.TRISC0_FW_BASE, bss_size=0x420)
