/* One BRISC per value head (GDN) or query head (GQA). State and caches are in DRAM.
 * Matrix projections run separately on Tensix. Scratch and parameter slots are assigned by TTRV. */
#include "noc.h"
#include "worker.h"

typedef unsigned short bf16;
typedef union {
  float f;
  u32 u;
} FloatBits;
static float load(bf16 x) { return (FloatBits){.u = (u32)x << 16}.f; }
static bf16 store(float x) {
  u32 u = (FloatBits){.f = x}.u;
  return (u + 0x7fff + ((u >> 16) & 1)) >> 16;
}
static float rsqrt(float x) {
  float y = (FloatBits){.u = 0x5f3759df - ((FloatBits){.f = x}.u >> 1)}.f;
  for (int i = 0; i < 3; ++i)
    y *= 1.5f - 0.5f * x * y * y;
  return y;
}
static float exponential(float x) {
  if (x < -80.f)
    return 0;
  if (x > 80.f)
    x = 80.f;
  int n = (int)(x * 1.44269504f + (x < 0 ? -0.5f : 0.5f));
  float r = x - n * 0.69314718f;
  float p = 1 + r * (1 + r * (0.5f + r * (1.f / 6 + r * (1.f / 24 + r * (1.f / 120)))));
  return p * (FloatBits){.u = (u32)(127 + n) << 23}.f;
}
// Blackhole implements FP32 multiply and add in hardware. Division needs a reciprocal refinement.
static float reciprocal(float x) {
  float y = (FloatBits){.u = 0x7ef311c3 - (FloatBits){.f = x}.u}.f;
  for (int i = 0; i < 3; ++i)
    y *= 2.f - x * y;
  return y;
}
static float sigmoid(float x) { return reciprocal(1.f + exponential(-x)); }
#ifdef GDN
static float softplus(float x) {
  // log(1+t) = 2 atanh(t/(2+t)), 0 <= t <= 1.
  float t = exponential(x < 0 ? x : -x), y = t * reciprocal(2 + t), s = y * y;
  return (x > 0 ? x : 0) + 2 * y * (1 + s * (1.f / 3 + s * (1.f / 5 + s * (1.f / 7 + s * (1.f / 9)))));
}
#endif
static void transfer(int write, int slot, int shift, u32 offset, void *local, u32 bytes) {
  u32 base = read32(L1_PARAM_BASE + 4 * slot);
  // TTRV encodes per-bank byte address + starting bank in one parameter word.
  u32 low = ((base & ~7u) << 3) + ((base & 7) << shift);
  u32 high = (1u << 31) | ((u32)shift << 24) | (base >> 29);
  noc_move(0, write, low, high, offset, bytes, (u32)local, 1);
  noc_wait(0, 1, 1);
}
#define GET(slot, offset, arr) transfer(0, slot, 11, 2 * (offset), arr, sizeof(arr))
#define PUT(slot, offset, arr) transfer(1, slot, 11, 2 * (offset), arr, sizeof(arr))

// Write the dense head as the two 16-column faces expected by projection.ttrv.
static void emit(int slot, int first, bf16 *x, int count) {
#if PROMPT
  transfer(1, slot, 11, 2 * first, x, 2 * count);
#else
  for (int i = 0; i < count; i += 32) {
    int k = (first + i) / 32, off = (k / 16) * 512 + (k % 16) * 16;
    transfer(1, slot, 11, 2 * off, x + i, 32);
    transfer(1, slot, 11, 2 * (off + 256), x + i + 16, 32);
  }
#endif
}

#ifdef GDN
#include "state.h"
static void head(Scratch *s, int h, u32 pos, u32 row, u32 rows) {
  int channel[3] = {(h / 3) * 128, 2048 + (h / 3) * 128, 4096 + h * 128};
  for (int p = 0; p < 3; p++) {
    GET(0, row * 10240 + channel[p], s->raw[p]);
    if (!row)
      GET(3, 4 * channel[p], s->taps[p]);
  }
  GET(1, row * 6144 + h * 128, s->z);
  GET(2, row * 1024, s->ab);
  if (!row)
    GET(4, 0, s->params); // exp(A_log), dt_bias
  if (!row)
    GET(5, 0, s->weights);
  if (!row && pos)
    GET(6, h * 3 * 3 * 128, s->history);
  float sums[2] = {0, 0};
  for (int p = 0; p < 3; p++)
    for (int j = 0; j < 128; j++) {
      float x = load(s->raw[p][j]) * load(s->taps[p][j][3]);
      for (int t = 0; t < 3; t++) {
        if (pos)
          x += load(s->history[t][p][j]) * load(s->taps[p][j][t]);
        s->history[t][p][j] = t == 2 ? s->raw[p][j] : pos ? s->history[t + 1][p][j] : 0;
      }
      x = load(store(x * sigmoid(x)));
      s->act[p][j] = x;
      if (p < 2)
        sums[p] += x * x;
    }
  if (row + 1 == rows)
    PUT(6, h * 3 * 3 * 128, s->history);
  float scaleq = rsqrt(sums[0] + 1e-6f) * 0.08838834765f, scalek = rsqrt(sums[1] + 1e-6f);
  float decay = exponential(-load(s->params[h]) * softplus(load(s->ab[h]) + load(s->params[48 + h])));
  float beta = sigmoid(load(s->ab[64 + h]));
  if (!row && pos)
    transfer(0, 7, 12, h * sizeof(s->state), s->state, sizeof(s->state));
  for (int k = 0; k < 128; k++) {
    s->act[0][k] *= scaleq;
    s->act[1][k] *= scalek;
  }
  s->decay = decay;
  s->beta = beta;
  fence();
  write32(PCBUF(2), pos != 0);
  (void)read32(MAILBOX_FROM(2));
  fence();
  if (row + 1 == rows)
    transfer(1, 7, 12, h * sizeof(s->state), s->state, sizeof(s->state));
  float sum = 0;
  for (int i = 0; i < 128; i++) {
    float x = load(store(s->context[i]));
    s->context[i] = x;
    sum += x * x;
  }
  float inv = rsqrt(sum / 128 + 1e-6f);
  for (int i = 0; i < 128; i++) {
    float z = load(s->z[i]);
    s->out[i] = store(s->context[i] * inv * load(s->weights[i]) * z * sigmoid(z));
  }
  emit(8, row * 6144 + h * 128, s->out, 128);
}
#else
typedef struct {
  bf16 q[256], gate[256], k[256], v[256], qnorm[256], knorm[256], angles[64], out[256];
  float accum[256];
} Scratch;
static void norm_rope(bf16 *x, const bf16 *gamma, const bf16 *angles) {
  float sum = 0;
  for (int i = 0; i < 256; i++) {
    float v = load(x[i]);
    sum += v * v;
  }
  float inv = rsqrt(sum / 256 + 1e-6f);
  for (int i = 0; i < 256; i++)
    x[i] = store(load(x[i]) * inv * (1 + load(gamma[i])));
  for (int i = 0; i < 32; i++) {
    float a = load(x[i]), b = load(x[i + 32]), c = load(angles[i]), s = load(angles[i + 32]);
    x[i] = store(a * c - b * s);
    x[i + 32] = store(b * c + a * s);
  }
}
static void head(Scratch *s, int h, u32 pos, u32 row, u32 rows) {
  (void)rows;
  const int kv = h / 6;
  GET(5, pos * 64, s->angles);
#if CACHE_ONLY || !PROMPT
  GET(1, row * 1024 + kv * 256, s->k);
  GET(2, row * 1024 + kv * 256, s->v);
  GET(4, 0, s->knorm);
  norm_rope(s->k, s->knorm, s->angles);
  if (h % 6 == 0) {
    PUT(6, (pos * 4 + kv) * 256, s->k);
    PUT(7, (pos * 4 + kv) * 256, s->v);
  }
#else
  GET(6, (pos * 4 + kv) * 256, s->k);
  GET(7, (pos * 4 + kv) * 256, s->v);
#endif
#if CACHE_ONLY
  return;
#endif
  GET(0, row * 12288 + h * 512, s->q);
  GET(0, row * 12288 + h * 512 + 256, s->gate);
  GET(3, 0, s->qnorm);
  norm_rope(s->q, s->qnorm, s->angles);
  // The current row is already local. Other workers only read earlier cache rows.
  float maxscore = 0, total = 0;
  for (int i = 0; i < 256; i++)
    s->accum[i] = 0;
  for (u32 t = 0; t <= pos; t++) {
    if (t) {
      GET(6, ((t - 1) * 4 + kv) * 256, s->k);
      GET(7, ((t - 1) * 4 + kv) * 256, s->v);
    }
    float score = 0;
    for (int i = 0; i < 256; i++)
      score += load(s->q[i]) * load(s->k[i]);
    score *= 0.0625f;
    float next = t && maxscore > score ? maxscore : score;
    float prev = t ? exponential(maxscore - next) : 0, w = exponential(score - next);
    for (int i = 0; i < 256; i++)
      s->accum[i] = s->accum[i] * prev + w * load(s->v[i]);
    total = total * prev + w;
    maxscore = next;
  }
  float inv = reciprocal(total);
  for (int i = 0; i < 256; i++)
    s->out[i] = store(s->accum[i] * inv * sigmoid(load(s->gate[i])));
  emit(8, row * 6144 + h * 256, s->out, 256);
}
#endif

_Static_assert(sizeof(Scratch) <= SCRATCH_BYTES, "worker scratch too small");
KERNEL kernel_main(void) {
  noc_init(0);
  u32 worker = read32(WORKER_ID), pos = read32(L1_PARAM_BASE + 4 * POS_SLOT);
#if PROMPT
  u32 rows = read32(L1_PARAM_BASE + 4 * ROWS_SLOT);
#else
  u32 rows = 1;
#endif
#if CACHE_ONLY
  u32 h = (worker % 4) * 6, first = worker / 4, lanes = GRID / 4;
#elif PROMPT && !defined(GDN)
  u32 h = worker % 24, first = worker / 24, lanes = GRID / 24;
#else
  u32 h = worker, first = 0, lanes = 1;
#endif
  for (u32 r = first; r < rows; r += lanes)
    head((Scratch *)SCRATCH_ADDR, h, pos + r, r, rows);
  JUMP(FW_BRISC + 4);
}
