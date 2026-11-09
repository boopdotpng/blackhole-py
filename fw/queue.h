#ifndef QUEUE_H
#define QUEUE_H
#include "noc.h"

typedef volatile struct {
  u32 op, op_arg;  /* op_arg reserved */
  u32 a_lo, a_hi, b_lo, b_hi, c, c_hi;
} packet;

u32 queue_fetch(u32 niu, u32 read, u32 local, u32 max);

void queue_init(u32 niu);
void queue_timestamp(u32 niu, u32 lo, u32 hi);
void queue_signal_op(u32 niu, packet *p);
void queue_flush(u32 niu, u32 acked);
void queue_idle(u32 niu);

#endif
