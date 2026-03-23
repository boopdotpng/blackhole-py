// SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
//
// SPDX-License-Identifier: Apache-2.0

#include "ckernel.h"
#include "internal/firmware_common.h"
#include "risc_common.h"
#include <tensix.h>
#include "hostdev/dev_msgs.h"

#include "tools/profiler/kernel_profiler.hpp"
#include "tools/profiler/perf_counters.hpp"

#include "internal/debug/fw_debug.h"
#include "api/debug/waypoint.h"
#include "api/debug/dprint.h"
#include "internal/debug/stack_usage.h"
#if !defined(UCK_CHLKC_MATH)
#include "internal/circular_buffer_interface.h"
#include "internal/circular_buffer_init.h"
#endif
#include "tt-metalium/circular_buffer_constants.h"

#if defined(PROFILE_KERNEL)
namespace kernel_profiler {
uint32_t wIndex __attribute__((used));
uint32_t stackSize __attribute__((used));
uint32_t sums[SUM_COUNT] __attribute__((used));
uint32_t sumIDs[SUM_COUNT] __attribute__((used));
}  // namespace kernel_profiler
#endif

uint32_t tt_l1_ptr* rta_l1_base __attribute__((used));
uint32_t tt_l1_ptr* crta_l1_base __attribute__((used));

uint8_t my_logical_x_ __attribute__((used));
uint8_t my_logical_y_ __attribute__((used));
uint8_t my_relative_x_ __attribute__((used));
uint8_t my_relative_y_ __attribute__((used));

namespace ckernel {

enum class ttRiscCores : std::uint32_t { Unpack = 0, Math = 1, Pack = 2, Brisc = 3, Nrisc = 4 };

#if defined(__PTR_CONST)
#define PTR_CONST const
#else
#define PTR_CONST
#endif
volatile tt_reg_ptr uint* PTR_CONST reg_base = reinterpret_cast<volatile uint*>(0xFFB10000);
volatile tt_reg_ptr uint* PTR_CONST pc_buf_base = reinterpret_cast<volatile uint*>(PC_BUF_BASE);
volatile tt_reg_ptr uint* PTR_CONST regfile = reinterpret_cast<volatile uint*>(REGFILE_BASE);
#undef PTR_CONST
#if defined(__INSTRN_BUFFER_TOS)
volatile tt_reg_ptr uint32_t* const instrn_buffer = reinterpret_cast<volatile uint32_t*>(INSTRN_BUF_BASE);
#endif
uint32_t cfg_state_id __attribute__((used)) = 0;
uint32_t dest_offset_id __attribute__((used)) = 0;

uint32_t op_info_offset __attribute__((used)) = 0;

const uint8_t thread_id = COMPILE_FOR_TRISC;

volatile tt_l1_ptr uint8_t* const trisc_run =
    &((tt_l1_ptr mailboxes_t*)(MEM_MAILBOX_BASE))->subordinate_sync.map[COMPILE_FOR_TRISC + 1];
tt_l1_ptr mailboxes_t* const mailboxes = (tt_l1_ptr mailboxes_t*)(MEM_MAILBOX_BASE);
}  // namespace ckernel

#if !defined(UCK_CHLKC_MATH)
uint32_t tt_l1_ptr* cb_l1_base __attribute__((used));
CBInterface cb_interface[NUM_CIRCULAR_BUFFERS] __attribute__((used));
#endif

#if defined(UCK_CHLKC_UNPACK)
constexpr bool cb_init_read = true;
#else
constexpr bool cb_init_read = false;
#endif
#if defined(UCK_CHLKC_PACK)
constexpr bool cb_init_write = true;
#else
constexpr bool cb_init_write = false;
#endif

using namespace ckernel;

#if defined(PROFILE_PERF_COUNTERS) && COMPILE_FOR_TRISC == 1
namespace {

uint64_t perf_counter_samples[PERF_COUNTER_MAX_RECORDS] = {};

inline void perf_counter_set_l1_mux(PerfCounterGroup group) {
    volatile tt_reg_ptr uint32_t* mux_reg =
        reinterpret_cast<volatile tt_reg_ptr uint32_t*>(RISCV_DEBUG_REG_PERF_CNT_MUX_CTRL);
    constexpr uint32_t L1_MUX_SEL_BIT = (1u << 4);
    uint32_t mux_val = *mux_reg;
    if (group == L1_0) {
        mux_val &= ~L1_MUX_SEL_BIT;
    } else {
        mux_val |= L1_MUX_SEL_BIT;
    }
    *mux_reg = mux_val;
}

inline void perf_counter_start() {
    for (PerfCounterGroup group : PERF_COUNTER_GROUPS) {
        if ((PROFILE_PERF_COUNTERS & perf_counter_group_flag(group)) == 0) {
            continue;
        }
        if (group == L1_0 || group == L1_1) {
            perf_counter_set_l1_mux(group);
        }
        volatile tt_reg_ptr uint32_t* cntl =
            reinterpret_cast<volatile tt_reg_ptr uint32_t*>(perf_counter_cntl_reg(group));
        cntl[0] = 0;
        cntl[1] = PERF_CNT_CONTINUOUS_MODE;
        cntl[2] = PERF_CNT_START_VALUE;
        cntl[2] = 0;
    }
}

inline uint32_t perf_counter_stop_and_capture() {
    for (PerfCounterGroup group : PERF_COUNTER_GROUPS) {
        if ((PROFILE_PERF_COUNTERS & perf_counter_group_flag(group)) == 0) {
            continue;
        }
        volatile tt_reg_ptr uint32_t* cntl =
            reinterpret_cast<volatile tt_reg_ptr uint32_t*>(perf_counter_cntl_reg(group));
        cntl[2] = PERF_CNT_STOP_VALUE;
        cntl[2] = 0;
    }

    uint32_t sample_count = 0;
    for (PerfCounterGroup group : PERF_COUNTER_GROUPS) {
        if ((PROFILE_PERF_COUNTERS & perf_counter_group_flag(group)) == 0) {
            continue;
        }
        if (group == L1_0 || group == L1_1) {
            perf_counter_set_l1_mux(group);
        }
        volatile tt_reg_ptr uint32_t* cntl =
            reinterpret_cast<volatile tt_reg_ptr uint32_t*>(perf_counter_cntl_reg(group));
        volatile tt_reg_ptr uint32_t* out =
            reinterpret_cast<volatile tt_reg_ptr uint32_t*>(perf_counter_out_reg(group));
        const PerfCounterDesc* descs = perf_counter_descs(group);
        const size_t desc_count = perf_counter_desc_count(group);
        for (size_t i = 0; i < desc_count; ++i) {
            const uint32_t mode = (static_cast<uint32_t>(descs[i].bank_sel) << PERF_CNT_BANK_SELECT_SHIFT) |
                                  PERF_CNT_CONTINUOUS_MODE;
            cntl[1] = mode;
            while (cntl[1] != mode) {
            }
            for (int wait_count = 0; wait_count < 100; ++wait_count) {
                asm("nop");
            }
            perf_counter_samples[sample_count++] = PerfCounter(out[1], out[0], descs[i].type).raw_data;
        }
    }
    return sample_count;
}

inline void perf_counter_emit(uint32_t sample_count) {
    for (uint32_t i = 0; i < sample_count; ++i) {
        kernel_profiler::timeStampedData<PERF_COUNTER_PROFILER_ID>(perf_counter_samples[i]);
    }
}

}  // namespace
#endif

void init_sync_registers() {
    for (uint32_t operand = 0; operand < NUM_CIRCULAR_BUFFERS; operand++) {
        get_cb_tiles_received_ptr(operand)[0] = 0;
        get_cb_tiles_acked_ptr(operand)[0] = 0;
    }
}

int main(int argc, char* argv[]) {
    configure_csr();
    WAYPOINT("I");

    do_crt1((uint32_t tt_l1_ptr*)PREPROCESSOR_EXPAND(MEM_TRISC, COMPILE_FOR_TRISC, _INIT_LOCAL_L1_BASE_SCRATCH));

#pragma GCC unroll 0
    for (int i = 0; i < 64; i++) {
        regfile[i] = 0;
    }

    reset_cfg_state_id();

    {
        volatile uint tt_reg_ptr* cfg = get_cfg_pointer();
        cfg[PRNG_SEED_Seed_Val_ADDR32] = 0;
        riscv_wait(600);
    }
    my_logical_x_ = mailboxes->core_info.absolute_logical_x;
    my_logical_y_ = mailboxes->core_info.absolute_logical_y;
    *trisc_run = RUN_SYNC_MSG_DONE;

    DeviceProfilerInit();
    while (1) {
        WAYPOINT("W");
        while (*trisc_run != RUN_SYNC_MSG_GO) {
            if constexpr (COMPILE_FOR_TRISC == 0) {
                if (*trisc_run == RUN_SYNC_MSG_INIT_SYNC_REGISTERS) {
                    init_sync_registers();
                    *trisc_run = RUN_SYNC_MSG_DONE;
                }
            }
            invalidate_l1_cache();
        }
        DeviceZoneScopedMainN("TRISC-FW");

        uint32_t launch_msg_rd_ptr = mailboxes->launch_msg_rd_ptr;
        launch_msg_t* launch_msg = &(mailboxes->launch[launch_msg_rd_ptr]);

        uint32_t kernel_config_base = launch_msg->kernel_config.kernel_config_base[ProgrammableCoreType::TENSIX];

#if !defined(UCK_CHLKC_MATH)
        uint32_t tt_l1_ptr* cb_l1_base =
            (uint32_t tt_l1_ptr*)(kernel_config_base + launch_msg->kernel_config.local_cb_offset);
        uint32_t local_cb_mask = launch_msg->kernel_config.local_cb_mask;
        setup_local_cb_read_write_interfaces<cb_init_read, cb_init_write, cb_init_write>(cb_l1_base, 0, local_cb_mask);

        cb_l1_base = (uint32_t tt_l1_ptr*)(kernel_config_base + launch_msg->kernel_config.remote_cb_offset);
        uint32_t end_cb_index = launch_msg->kernel_config.min_remote_cb_start_index;

        experimental::setup_remote_cb_interfaces<false>(cb_l1_base, end_cb_index, 0, 0, 0, 0);
#endif

        rta_l1_base = (uint32_t tt_l1_ptr*)(kernel_config_base +
                                            launch_msg->kernel_config.rta_offset[PROCESSOR_INDEX].rta_offset);
        crta_l1_base = (uint32_t tt_l1_ptr*)(kernel_config_base +
                                             launch_msg->kernel_config.rta_offset[PROCESSOR_INDEX].crta_offset);
        my_relative_x_ = my_logical_x_ - launch_msg->kernel_config.sub_device_origin_x;
        my_relative_y_ = my_logical_y_ - launch_msg->kernel_config.sub_device_origin_y;

        WAYPOINT("R");
        int index =
            static_cast<std::underlying_type<TensixProcessorTypes>::type>(TensixProcessorTypes::MATH0) + thread_id;
        uint32_t kernel_lma = (kernel_config_base + launch_msg->kernel_config.kernel_text_offset[index]);
#if defined(PROFILE_PERF_COUNTERS) && COMPILE_FOR_TRISC == 1
        perf_counter_start();
#endif
        auto stack_free = reinterpret_cast<uint32_t (*)()>(kernel_lma)();
#if defined(PROFILE_PERF_COUNTERS) && COMPILE_FOR_TRISC == 1
        perf_counter_emit(perf_counter_stop_and_capture());
#endif
        record_stack_usage(stack_free);
        WAYPOINT("D");

        tensix_sync();
        *trisc_run = RUN_SYNC_MSG_DONE;
    }
}
