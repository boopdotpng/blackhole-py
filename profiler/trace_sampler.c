/*
 * trace_sampler.c — C hot loop for TRACE=1 debug bus sampling.
 *
 * Build:
 *   gcc -O3 -march=native -shared -fPIC -o trace_sampler.so trace_sampler.c
 */

#include <stdint.h>
#include <time.h>
#include <x86intrin.h>

/* ── MMIO ──────────────────────────────────────────────────────────── */

static inline void mmio_write32(volatile uint8_t *base, uint32_t off, uint32_t val) {
    *(volatile uint32_t *)(base + off) = val;
    _mm_sfence();  /* flush WC buffer so the write lands before any subsequent read */
}

static inline uint32_t mmio_read32(volatile uint8_t *base, uint32_t off) {
    _mm_lfence();  /* ensure prior writes are visible before reading */
    return *(volatile uint32_t *)(base + off);
}

/* ── timing ────────────────────────────────────────────────────────── */

static inline uint64_t rdtsc_fenced(void) {
    _mm_lfence();
    return __rdtsc();
}

static inline uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/* TSC calibration — done once at .so load time via constructor */
static uint64_t g_tsc_base;
static uint64_t g_ns_base;
static double   g_tsc_to_ns;

__attribute__((constructor))
static void calibrate_tsc(void) {
    uint64_t t0_ns = now_ns();
    uint64_t t0_tsc = rdtsc_fenced();
    /* Spin-calibrate for ~1ms (no syscall, just busy-wait) */
    while (now_ns() - t0_ns < 1000000ULL)
        ;
    uint64_t t1_ns = now_ns();
    uint64_t t1_tsc = rdtsc_fenced();
    g_tsc_base = t0_tsc;
    g_ns_base = t0_ns;
    g_tsc_to_ns = (double)(t1_ns - t0_ns) / (double)(t1_tsc - t0_tsc);
}

static inline uint64_t tsc_to_ns(uint64_t tsc) {
    return g_ns_base + (uint64_t)((double)(tsc - g_tsc_base) * g_tsc_to_ns);
}

/* ── completion queue ──────────────────────────────────────────────── */

struct cq_state {
    volatile uint8_t *sysmem;
    uint32_t noc_local;
    uint32_t cq_wr_off;
    uint32_t cursor_16b;
    uint32_t cursor_toggle;
    uint32_t page_16b;
    uint32_t end_16b;
    uint32_t base_16b;
};

static inline uint32_t cq_peek_wr_raw(const struct cq_state *cq) {
    return *(volatile uint32_t *)(cq->sysmem + cq->cq_wr_off);
}

static inline uint32_t cq_peek_event(const struct cq_state *cq, uint32_t cursor_16b) {
    uint32_t off = (cursor_16b << 4) - cq->noc_local;
    return *(volatile uint32_t *)(cq->sysmem + off + 16);
}

static inline void cq_advance(struct cq_state *cq) {
    cq->cursor_16b += cq->page_16b;
    if (cq->cursor_16b >= cq->end_16b) {
        cq->cursor_16b = cq->base_16b;
        cq->cursor_toggle ^= 1;
    }
}

/* ── result structs ────────────────────────────────────────────────── */

struct boundary {
    uint32_t event_id;
    uint32_t sample_count;
    uint64_t timestamp_ns;
};

struct sampler_result {
    uint32_t sample_count;
    int      truncated;
    uint64_t mmio_write_ns;
    uint64_t mmio_read_ns;
    uint32_t mmio_write_count;
    uint32_t mmio_read_count;
    uint64_t capture_start_ns;
    uint64_t capture_end_ns;
    uint32_t boundary_count;
};

/* ── kept for backwards compat (the "with timing" variant) ─────────── */

void trace_sampler_run(
    volatile uint8_t *tlb_base,
    uint32_t ctrl_off,
    uint32_t data_off,
    const uint32_t *config_words,
    uint32_t words_per_sample,
    uint32_t max_samples,
    uint64_t *timestamps_ns,
    uint32_t *raw_words,
    const uint32_t *event_ids,
    uint32_t num_events,
    struct boundary *boundaries,
    struct cq_state *cq,
    volatile int *stop_flag,
    struct sampler_result *result)
{
    uint32_t sample = 0;
    uint64_t write_ns = 0, read_ns = 0;
    uint32_t boundary_count = 0;
    int truncated = 0;
    uint64_t seen_mask = 0;

    result->capture_start_ns = now_ns();

    for (;;) {
        if (sample < max_samples) {
            timestamps_ns[sample] = now_ns();
            uint32_t base = sample * words_per_sample;
            for (uint32_t w = 0; w < words_per_sample; w++) {
                uint64_t t0 = now_ns();
                mmio_write32(tlb_base, ctrl_off, config_words[w]);
                uint64_t t1 = now_ns();
                raw_words[base + w] = mmio_read32(tlb_base, data_off);
                uint64_t t2 = now_ns();
                write_ns += t1 - t0;
                read_ns  += t2 - t1;
            }
            sample++;
        } else if (!truncated) {
            truncated = 1;
        }

        if (cq->sysmem) {
            uint32_t wr_raw = cq_peek_wr_raw(cq);
            uint32_t wr_16b = wr_raw & 0x7FFFFFFFU;
            uint32_t wr_toggle = wr_raw >> 31;
            while (cq->cursor_16b != wr_16b || cq->cursor_toggle != wr_toggle) {
                uint32_t eid = cq_peek_event(cq, cq->cursor_16b);
                for (uint32_t i = 0; i < num_events && i < 64; i++) {
                    if (event_ids[i] == eid && !(seen_mask & (1ULL << i))) {
                        seen_mask |= (1ULL << i);
                        boundaries[boundary_count].event_id = eid;
                        boundaries[boundary_count].sample_count = sample;
                        boundaries[boundary_count].timestamp_ns = now_ns();
                        boundary_count++;
                        break;
                    }
                }
                cq_advance(cq);
            }
        }

        if (boundary_count >= num_events) break;
        if (*stop_flag) break;
        if (truncated) { struct timespec z = {0,0}; nanosleep(&z, NULL); }
    }

    result->capture_end_ns = now_ns();
    result->sample_count = sample;
    result->truncated = truncated;
    result->mmio_write_ns = write_ns;
    result->mmio_read_ns = read_ns;
    result->mmio_write_count = sample * words_per_sample;
    result->mmio_read_count = sample * words_per_sample;
    result->boundary_count = boundary_count;
}

/*
 * trace_sampler_run_fast — maximum throughput variant.
 *
 * Optimizations vs the basic loop:
 *   1. rdtsc instead of clock_gettime — ~3ns vs ~20ns per timestamp
 *   2. CQ polling only every N samples (batched) — avoid cache-miss on CQ page
 *   3. Specialized unrolled paths for signal (1 word) vs group (4 word)
 *   4. Running pointer instead of multiply for raw_words index
 *   5. stop_flag check batched with CQ poll
 *   6. Timestamps stored as raw TSC ticks, converted to ns in bulk at the end
 */
void trace_sampler_run_fast(
    volatile uint8_t *tlb_base,
    uint32_t ctrl_off,
    uint32_t data_off,
    const uint32_t *config_words,
    uint32_t words_per_sample,
    uint32_t max_samples,
    uint64_t *timestamps_ns,  /* actually stores TSC ticks during sampling, converted at end */
    uint32_t *raw_words,
    const uint32_t *event_ids,
    uint32_t num_events,
    struct boundary *boundaries,
    struct cq_state *cq,
    volatile int *stop_flag,
    struct sampler_result *result)
{
    uint32_t sample = 0;
    uint32_t boundary_count = 0;
    int truncated = 0;
    uint64_t seen_mask = 0;

    result->capture_start_ns = now_ns();

    /* Poll interval: check CQ + stop every this many samples.
     * Too low = wasted branch every sample. Too high = delayed boundary detection.
     * 32 samples at ~3µs each ≈ 100µs between polls — plenty responsive. */
    const uint32_t POLL_INTERVAL = 4;

    /* Cache volatile pointers in registers */
    volatile uint32_t *ctrl_ptr = (volatile uint32_t *)(tlb_base + ctrl_off);
    volatile uint32_t *data_ptr = (volatile uint32_t *)(tlb_base + data_off);

    uint32_t *rw = raw_words;  /* running pointer */

    if (words_per_sample == 1) {
        /* ── SIGNAL MODE: fully unrolled, no inner loop ─────────── */
        uint32_t cfg0 = config_words[0];

        while (sample < max_samples) {
            /* Tight batch of POLL_INTERVAL samples with zero branching */
            uint32_t batch_end = sample + POLL_INTERVAL;
            if (batch_end > max_samples) batch_end = max_samples;

            while (sample < batch_end) {
                timestamps_ns[sample] = rdtsc_fenced();
                *ctrl_ptr = cfg0;
                *rw++ = *data_ptr;
                sample++;
            }

            /* Batched CQ poll + stop check */
            if (cq->sysmem) {
                uint32_t wr_raw = cq_peek_wr_raw(cq);
                uint32_t wr_16b = wr_raw & 0x7FFFFFFFU;
                uint32_t wr_toggle = wr_raw >> 31;
                while (cq->cursor_16b != wr_16b || cq->cursor_toggle != wr_toggle) {
                    uint32_t eid = cq_peek_event(cq, cq->cursor_16b);
                    for (uint32_t i = 0; i < num_events && i < 64; i++) {
                        if (event_ids[i] == eid && !(seen_mask & (1ULL << i))) {
                            seen_mask |= (1ULL << i);
                            boundaries[boundary_count].event_id = eid;
                            boundaries[boundary_count].sample_count = sample;
                            boundaries[boundary_count].timestamp_ns = rdtsc_fenced();
                            boundary_count++;
                            break;
                        }
                    }
                    cq_advance(cq);
                }
            }
            if (boundary_count >= num_events) goto done;
            if (*stop_flag) goto done;
        }
        truncated = 1;
    } else if (words_per_sample == 4) {
        /* ── GROUP MODE: unrolled 4-word inner ──────────────────── */
        uint32_t cfg0 = config_words[0];
        uint32_t cfg1 = config_words[1];
        uint32_t cfg2 = config_words[2];
        uint32_t cfg3 = config_words[3];

        while (sample < max_samples) {
            uint32_t batch_end = sample + POLL_INTERVAL;
            if (batch_end > max_samples) batch_end = max_samples;

            while (sample < batch_end) {
                timestamps_ns[sample] = rdtsc_fenced();
                *ctrl_ptr = cfg0;  rw[0] = *data_ptr;
                *ctrl_ptr = cfg1;  rw[1] = *data_ptr;
                *ctrl_ptr = cfg2;  rw[2] = *data_ptr;
                *ctrl_ptr = cfg3;  rw[3] = *data_ptr;
                rw += 4;
                sample++;
            }

            if (cq->sysmem) {
                uint32_t wr_raw = cq_peek_wr_raw(cq);
                uint32_t wr_16b = wr_raw & 0x7FFFFFFFU;
                uint32_t wr_toggle = wr_raw >> 31;
                while (cq->cursor_16b != wr_16b || cq->cursor_toggle != wr_toggle) {
                    uint32_t eid = cq_peek_event(cq, cq->cursor_16b);
                    for (uint32_t i = 0; i < num_events && i < 64; i++) {
                        if (event_ids[i] == eid && !(seen_mask & (1ULL << i))) {
                            seen_mask |= (1ULL << i);
                            boundaries[boundary_count].event_id = eid;
                            boundaries[boundary_count].sample_count = sample;
                            boundaries[boundary_count].timestamp_ns = rdtsc_fenced();
                            boundary_count++;
                            break;
                        }
                    }
                    cq_advance(cq);
                }
            }
            if (boundary_count >= num_events) goto done;
            if (*stop_flag) goto done;
        }
        truncated = 1;
    } else {
        /* ── GENERIC: any words_per_sample ──────────────────────── */
        while (sample < max_samples) {
            uint32_t batch_end = sample + POLL_INTERVAL;
            if (batch_end > max_samples) batch_end = max_samples;

            while (sample < batch_end) {
                timestamps_ns[sample] = rdtsc_fenced();
                for (uint32_t w = 0; w < words_per_sample; w++) {
                    *ctrl_ptr = config_words[w];
                    *rw++ = *data_ptr;
                }
                sample++;
            }

            if (cq->sysmem) {
                uint32_t wr_raw = cq_peek_wr_raw(cq);
                uint32_t wr_16b = wr_raw & 0x7FFFFFFFU;
                uint32_t wr_toggle = wr_raw >> 31;
                while (cq->cursor_16b != wr_16b || cq->cursor_toggle != wr_toggle) {
                    uint32_t eid = cq_peek_event(cq, cq->cursor_16b);
                    for (uint32_t i = 0; i < num_events && i < 64; i++) {
                        if (event_ids[i] == eid && !(seen_mask & (1ULL << i))) {
                            seen_mask |= (1ULL << i);
                            boundaries[boundary_count].event_id = eid;
                            boundaries[boundary_count].sample_count = sample;
                            boundaries[boundary_count].timestamp_ns = rdtsc_fenced();
                            boundary_count++;
                            break;
                        }
                    }
                    cq_advance(cq);
                }
            }
            if (boundary_count >= num_events) goto done;
            if (*stop_flag) goto done;
        }
        truncated = 1;
    }

    /* If we exhausted max_samples, spin-wait for completions */
    while (boundary_count < num_events && !(*stop_flag)) {
        if (cq->sysmem) {
            uint32_t wr_raw = cq_peek_wr_raw(cq);
            uint32_t wr_16b = wr_raw & 0x7FFFFFFFU;
            uint32_t wr_toggle = wr_raw >> 31;
            while (cq->cursor_16b != wr_16b || cq->cursor_toggle != wr_toggle) {
                uint32_t eid = cq_peek_event(cq, cq->cursor_16b);
                for (uint32_t i = 0; i < num_events && i < 64; i++) {
                    if (event_ids[i] == eid && !(seen_mask & (1ULL << i))) {
                        seen_mask |= (1ULL << i);
                        boundaries[boundary_count].event_id = eid;
                        boundaries[boundary_count].sample_count = sample;
                        boundaries[boundary_count].timestamp_ns = rdtsc_fenced();
                        boundary_count++;
                        break;
                    }
                }
                cq_advance(cq);
            }
        }
        struct timespec z = {0, 0};
        nanosleep(&z, NULL);
    }

done:
    ;
    result->capture_end_ns = now_ns();
    result->sample_count = sample;
    result->truncated = truncated;
    result->mmio_write_ns = 0;
    result->mmio_read_ns = 0;
    result->mmio_write_count = 0;
    result->mmio_read_count = 0;
    result->boundary_count = boundary_count;

    /* Convert TSC ticks -> ns for all timestamps and boundaries */
    for (uint32_t i = 0; i < sample; i++) {
        timestamps_ns[i] = tsc_to_ns(timestamps_ns[i]);
    }
    for (uint32_t i = 0; i < boundary_count; i++) {
        boundaries[i].timestamp_ns = tsc_to_ns(boundaries[i].timestamp_ns);
    }
}
