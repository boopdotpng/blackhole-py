typedef unsigned short bf16;
typedef struct {
  float state[8][128][16], act[3][128], context[128], decay, beta;
  _Alignas(64) bf16 raw[3][128], taps[3][128][4], history[3][3][128];
  bf16 z[128], weights[128], ab[128], params[96], out[128];
} Scratch;
