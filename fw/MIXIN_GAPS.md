# Firmware Mixin Gaps

This is the helper surface used by the handwritten firmware sources that does not
yet have complete `mixins` coverage. Local helper routines are included because
they should become readable builder-level calls too.

## Common Startup / Flow

- `configure_csr`
- `do_crt1`
- `risc_init`
- `invalidate_l1_cache`
- `wait_for_go_message`
- `wait_for_brisc_notification`
- `signal_ncrisc_completion`
- `tensix_sync`
- `riscv_wait`
- `reset_cfg_state_id`
- `internal_::get_hw_thread_idx`

## BRISC Orchestration

- `device_setup`
- `set_deassert_addresses`
- `deassert_all_reset`
- `deassert_ncrisc_trisc`
- `run_triscs`
- `start_ncrisc_kernel_run_early`
- `start_ncrisc_kernel_run`
- `wait_ncrisc_trisc`
- `trigger_sync_register_init`
- `barrier_remote_cb_interface_setup`
- `calculate_dispatch_addr`
- `notify_dispatch_core_done`
- `firmware_config_init`

## NOC

- `noc_init`
- `noc_local_state_init`
- `dynamic_noc_init`
- `dynamic_noc_local_state_init`
- `noc_set_active_instance`
- `noc_get_cfg_reg`
- `noc_set_cfg_reg`
- `NOC_READ_REG`
- `NOC_WRITE_REG`
- `ncrisc_noc_nonposted_atomics_flushed`
- `ncrisc_dynamic_noc_nonposted_atomics_flushed`
- `noc_bank_table_init`
- `noc_worker_logical_to_virtual_map_init`

## Circular Buffers

- `setup_local_cb_read_write_interfaces`
- `experimental::setup_remote_cb_interfaces`
- `get_cb_tiles_received_ptr`
- `get_cb_tiles_acked_ptr`
- `init_sync_registers`

## Tensix Setup

- `c_tensix_core::instrn_buf_base`
- `c_tensix_core::pc_buf_base`
- `c_tensix_core::cfg_regs_base`
- `c_tensix_core::write_stream_register`
- `c_tensix_core::ex_zeroacc`
- `c_tensix_core::ex_encc`
- `c_tensix_core::ex_load_const`
- `c_tensix_core::ex_rmw_cfg`
- `c_tensix_core::initialize_tensix_semaphores`
- `get_cfg_pointer`
- `pack_field`

## Memory Utilities

- `WRITE_REG`
- `wzeromem`
- `round_up_to_mult_of_4`
