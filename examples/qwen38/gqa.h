#pragma once
#define KEY_BLOCK 8
typedef struct {
  bf16 q[256], gate[256], k[256], v[256], qnorm[256], knorm[256], angles[64], out[256];
  float accum[256];
#if PROMPT && !CACHE_ONLY
  _Alignas(64) bf16 keys[KEY_BLOCK][256], values[KEY_BLOCK][256];
  float query[256], total;
#endif
} Scratch;
