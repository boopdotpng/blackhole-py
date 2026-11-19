#pragma once
typedef unsigned short bf16;
typedef union {
  float f;
  u32 u;
} FloatBits;
static inline float load(bf16 x) { return (FloatBits){.u = (u32)x << 16}.f; }
static inline bf16 store(float x) {
  u32 u = (FloatBits){.f = x}.u;
  return (u + 0x7fff + ((u >> 16) & 1)) >> 16;
}
static inline float rsqrt(float x) {
  float y = (FloatBits){.u = 0x5f3759df - ((FloatBits){.f = x}.u >> 1)}.f;
  for (int i = 0; i < 3; ++i)
    y *= 1.5f - 0.5f * x * y * y;
  return y;
}
static inline float exponential(float x) {
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
static inline float reciprocal(float x) {
  float y = (FloatBits){.u = 0x7ef311c3 - (FloatBits){.f = x}.u}.f;
  for (int i = 0; i < 3; ++i)
    y *= 2.f - x * y;
  return y;
}
static inline float sigmoid(float x) { return reciprocal(1.f + exponential(-x)); }
