"""BRISC firmware — master core.

Boot sequence:
  1. configure_csr, do_crt1 (BSS zero + LDM data copy)
  2. Read logical coordinates from core_info
  3. device_setup: tensix init, NOC clock-gate, reset-PC overrides, zero L1,
     instruction-cache invalidate, semaphore init
  4. Release subordinates (write SOFT_RESET_0 = 0)
  5. Wait for all subordinates to signal DONE
  6. Write go_msg = RUN_MSG_DONE

Dispatch loop:
  - Wait for go_msg == RUN_MSG_GO
  - Parse launch_msg, IC-invalidate, signal TRISCs & NCRISC
  - Call BRISC kernel
  - Wait subordinates done, write go_msg = DONE
"""
from extra.emu.rvir import Kernel
from extra.emu.rvlib import *
from extra.emu import memory as _M

def build():
  k = Kernel(base=_M.BRISC_FW_BASE)

  # ── _start ──────────────────────────────────────────────────────
  emit_start(k, BRISC_SP)

  # ── main (never returns) ────────────────────────────────────────
  with k.func("main", saves=[s0, s1, s2, s3, s4, s5]):

    # ── configure_csr ───────────────────────────────────────────
    emit_configure_csr(k)

    # ── do_crt1(BRISC_SCRATCH, 4 data, 0x874 BSS) ──────────────
    emit_do_crt1(k, BRISC_SCRATCH, 4, 0x874)

    # ── launch_msg_rd_ptr = 0 ──────────────────────────────────
    k.emit(SW(zero, zero, LAUNCH_MSG_RD_PTR))

    # ── read core_info.logical_x/y ─────────────────────────────
    read_core_info(k, s0, s1)              # s0 = logical_x, s1 = logical_y

    # ── risc_init: read NOC IDs (extract x/y coordinates) ──────
    read_noc_ids(k, t1, t2)               # t1 = (y0<<6)|x0, t2 = (y1<<6)|x1

    # ── device_setup ────────────────────────────────────────────
    disable_dest_clock_gating(k)
    enable_tdma_clock_gating(k)

    # NOC0/NOC1: read-modify-write NIU_CFG_0 and ROUTER_CFG_0 (set bit 0)
    noc_cfg_enable(k, NOC0_CFG0, base_reg=s2, tmp=t0)
    noc_cfg_enable(k, NOC1_CFG0, base_reg=s2, tmp=t0)

    # set_deassert_addresses: enable reset-PC overrides
    set_reset_pc_overrides(k)

    # wzeromem(ZEROS_BASE, 512)
    memzero(k, ZEROS_BASE, 512)

    # Invalidate all instruction caches
    invalidate_icache(k)

    # Tensix init: ZEROACC + SFPENCC + SEMINIT
    tensix_init(k, buf_reg=s2, tmp=t0)

    # ── ncrisc_halt.resume_addr = 0 ────────────────────────────
    k.emit(SW(zero, zero, MAILBOX_BASE))

    # ── deassert_ncrisc_trisc ───────────────────────────────────
    # subordinate_sync.all = RUN_SYNC_MSG_ALL_INIT (0x40404040)
    k.li(t0, RUN_SYNC_MSG_ALL_INIT)
    k.emit(SW(zero, t0, SUBORDINATE_SYNC))

    # Write SOFT_RESET_0 = 0 → releases NCRISC + TRISCs from reset
    release_subordinates(k)

    # ── wait_ncrisc_trisc: poll until all subordinates signal DONE ──
    wait_subordinates_done(k)

    # ── go_msg.signal = RUN_MSG_DONE ────────────────────────────
    k.emit(SB(zero, zero, GO_SIGNAL))

    # ── noc_init (NOC registers already pre-populated by emulator) ──
    # Read NOC0 node-ID for firmware state (minimal)
    read_noc_ids(k, t1, t2)

    # ── trigger_sync_register_init ──────────────────────────────
    k.li(t0, RUN_SYNC_MSG_INIT_SYNC_REGISTERS)
    k.emit(SB(zero, t0, TRISC0_RUN))

    # ================================================================
    # Main dispatch loop (infinite)
    # ================================================================
    with k.while_true():

      # ── wait for go_msg.signal == RUN_MSG_GO ────────────────
      poll_byte_eq(k, GO_SIGNAL, RUN_MSG_GO)

      # ── read launch message ─────────────────────────────────
      # s2=rd_ptr, s3=&launch_msg, s4=kernel_config_base
      read_launch_msg(k, s2, s3, s4)
      k.lw(s5, s3, LM_ENABLES)               # s5 = enables

      # ── invalidate instruction caches ───────────────────────
      invalidate_icache(k)

      # ── run_triscs: if MATH0 enabled, signal GO to all TRISCs ──
      k.li(t0, EN_TRISC0)
      k.emit(AND(t1, s5, t0))
      with k.if_('nez', t1):
        # Wait until trisc0 has finished its previous iteration
        poll_byte_eq(k, TRISC0_RUN, RUN_MSG_DONE)
        # Signal all three TRISCs
        k.li(t0, RUN_SYNC_MSG_GO)
        k.emit(SB(zero, t0, TRISC0_RUN))
        k.emit(SB(zero, t0, TRISC1_RUN))
        k.emit(SB(zero, t0, TRISC2_RUN))

      # ── start_ncrisc: if DM1 enabled, signal GO ────────────
      k.li(t0, EN_NCRISC)
      k.emit(AND(t1, s5, t0))
      with k.if_('nez', t1):
        signal_go(k, NCRISC_RUN)

      # ── call BRISC kernel if DM0 enabled ────────────────────
      k.li(t0, EN_BRISC)
      k.emit(AND(t1, s5, t0))
      with k.if_('nez', t1):
        call_kernel(k, s3, s4, LM_TEXT_BRISC)

      # ── wait for all subordinates done ──────────────────────
      wait_subordinates_done(k)

      # ── trigger_sync_register_init ──────────────────────────
      k.li(t0, RUN_SYNC_MSG_INIT_SYNC_REGISTERS)
      k.emit(SB(zero, t0, TRISC0_RUN))

      # ── go_msg.signal = RUN_MSG_DONE ────────────────────────
      k.emit(SB(zero, zero, GO_SIGNAL))

  # ── pack ────────────────────────────────────────────────────────
  ldm_data = struct.pack('<I', SUBORDINATE_SYNC)   # 0x68
  return pack_firmware(k, _M.BRISC_FW_BASE, ldm_data, bss_size=0x874)
