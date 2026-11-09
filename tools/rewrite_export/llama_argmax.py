"""Rewrite argmax adapter, derived from blackhole-py/examples/llama3/kernels.py.

Uses persistent reducer mailboxes instead of a per-launch scratch clear. Imported
by the offline exporter in blackhole-py's namespace; no device is opened here.
Keep the scan/reduction algorithm in sync with the upstream generator.
"""
import dataclasses
from examples.llama3.kernels import (
  Buffer, Program, P100_WORKER_CORES, _token_counts, Const, DType, CB,
  physical_to_logical, noc_coord, R, CQConfig, _add_constant, TensixL1,
  rectangles, mcast_coords, load_bf16, scan_bf16, TT,
)

# Between resident per-core tables and code. Checked against the manifest at install.
MAILBOX_BASE, MAILBOX_END = 0x8800, 0x9000

def argmax(cfg, logits: Buffer, token_history: Buffer, host_output: int,
) -> Program:
  """SFPU-scan logits, reduce 32 candidates/core, and publish the winner.

  Every projection core scans its own compact logits shard (the LM head's
  output) on the SFPU, keeping 32 candidates. BRISC picks the best of
  them and sends (value, token) to core 0. Core 0 picks the global winner, then:
    - writes it to host memory (the token the host reads back),
    - appends it to token_history (the next embedding's input),
    - multicasts next-token runtime parameters for autonomous replay.
  Ties resolve to the lowest token ID.
  """
  # Projection cores are spread over the chip; argmax instead runs on the
  # first N workers in column-major order (a few multicast rectangles). Core i
  # still scans projection core i's logits shard.
  logits = dataclasses.replace(logits, cores=P100_WORKER_CORES[:len(logits.cores)])
  local_counts = _token_counts(cfg.vocab_size, len(logits.cores))
  local_starts, cursor = [], 0
  for count in local_counts:
    local_starts.append(cursor)
    cursor += count
  starts = Const("argmax_start", tuple(local_starts))
  counts = Const("argmax_count", local_counts)
  indices = Const("argmax_core", tuple(range(len(logits.cores))))
  write_pos = Const("write_pos", 1)
  write_token = Const("write_token", 1)
  host_address = Const("argmax_host_address", host_output)
  p = Program(
    logits.cores, logits, token_history, host_address,
    starts, counts, indices, write_pos, write_token, fp32_dst=True,
  )
  incoming = p.cb(DType.BF16, depth=logits.tiles_per_item)
  logits_l1 = incoming.addr
  candidates = p.cb(DType.F32, depth=1)
  # Keep the full-page NoC transfer cache-line aligned.
  history_l1 = p.l1(token_history.tile_size, alignment=64)
  local = p.l1(16, alignment=16)
  runtime_l1 = p.l1(32, alignment=16)
  # This mailbox survives intervening kernels, whose scratch allocations overlap.
  # The installer zeros it once; the reducer rearms each slot after consuming it.
  # EXEC completion prevents the next invocation from publishing before rearming.
  partials = MAILBOX_BASE
  assert partials + len(logits.cores) * 16 <= MAILBOX_END

  # BRISC: read this core's logits; overwrite padding beyond its valid
  # count with -inf so padding can never win.
  CB.reserve_back(p.brisc, incoming, logits.tiles_per_item)
  p.brisc.noc.read_tiles(logits, tuple(
    (tile, logits_l1 + tile * logits.tile_size)
    for tile in range(logits.tiles_per_item)
  ))
  with p.brisc.scope():
    count, start, core_index = p.brisc.reg(3)
    p.brisc.read(count, p.param_addr(counts))
    p.brisc.read(start, p.param_addr(starts))
    p.brisc.read(core_index, p.param_addr(indices))
    # Projection padding is unspecified (usually zero); exclude it even when
    # every valid logit is negative. Fill contiguous physical runs in L1.
    for valid in sorted(set(local_counts)):
      done = p.brisc._new_label("argmax_padding_done")
      with p.brisc.scope():
        size, address, value = p.brisc.reg(3)
        p.brisc.li(size, valid)
        p.brisc.bne(count, size, done)
        physical = sorted((i & ~1023) + (i & 512) + ((i & 16) << 4)
                          + ((i & 480) >> 1) + (i & 15)
                          for i in range(valid, logits.tiles_per_item * 1024))
        runs = []
        for index in physical:
          if runs and runs[-1][1] == index: runs[-1][1] += 1
          else: runs.append([index, index + 1])
        for first, end in runs:
          p.brisc.li(value, 0xff80ff80)
          if first & 1:
            p.brisc.write(logits_l1 + first * 2, value, bytes=2)
            first += 1
          p.brisc.li(address, logits_l1 + first * 2)
          for _ in p.brisc.range((end - first) // 2):
            p.brisc.sw(value, address)
            p.brisc.addi(address, address, 4)
          if end & 1: p.brisc.write(logits_l1 + (end - 1) * 2, value, bytes=2)
      p.brisc.label(done)
    p.brisc.fence()
    CB.push_back(p.brisc, incoming, logits.tiles_per_item)
    # BRISC: best of the SFPU's 32 candidates (key = order-preserving value bits).
    CB.wait_front(p.brisc, candidates)
    best_key, best_id, key, token, address, physical = p.brisc.reg(6)
    p.brisc.li(best_key, 0)
    p.brisc.li(best_id, 0x7fffffff)
    CB.get_read_ptr(p.brisc, candidates, address)
    for _ in p.brisc.range(32):
      p.brisc.lw(key, address)
      p.brisc.srli(key, key, 15)
      p.brisc.lw(physical, address, 4)
      physical_to_logical(p.brisc, physical, token, tilized=True)
      p.brisc.addi(address, address, 8)
      skip = p.brisc._new_label("argmax_skip")
      replace = p.brisc._new_label("argmax_replace")
      p.brisc.bgeu(token, count, skip)
      p.brisc.add(token, start, token)
      p.brisc.bltu(best_key, key, replace)
      p.brisc.bne(best_key, key, skip)
      p.brisc.bgeu(token, best_id, skip)
      p.brisc.label(replace)
      p.brisc.mv(best_key, key)
      p.brisc.mv(best_id, token)
      p.brisc.label(skip)
    CB.pop_front(p.brisc, candidates)

    p.brisc.write(local, best_key)
    p.brisc.write(local + 4, best_id)
    p.brisc.write(local + 8, 1)
    with p.brisc.scope():
      target, stride, base = p.brisc.reg(3, exclude=core_index)
      p.brisc.li(stride, 16)
      p.brisc.mul(target, core_index, stride)
      p.brisc.li(base, partials)
      p.brisc.add(target, target, base)
      p.brisc.noc.write(
        local, target, noc_coord(logits.cores[0]), 12, posted=False,
      )

    # Core 0 only: wait for every core's candidate and keep the best.
    reducer_done = p.brisc._new_label("argmax_reducer_done")
    p.brisc.bne(core_index, R.ZERO, reducer_done)
    p.brisc.li(best_key, 0)
    p.brisc.li(best_id, 0)
    for index in p.brisc.range(len(logits.cores)):
      with p.brisc.scope():
        address, stride, ready, candidate_key, candidate_id, base = (
          p.brisc.reg(6)
        )
        p.brisc.li(stride, 16)
        p.brisc.mul(address, index, stride)
        p.brisc.li(base, partials)
        p.brisc.add(address, address, base)
        wait = p.brisc._new_label("argmax_wait_partial")
        ready_label = p.brisc._new_label("argmax_partial_ready")
        p.brisc.label(wait)
        p.brisc.lw(ready, address, 8)
        p.brisc.bne(ready, R.ZERO, ready_label)
        p.brisc.fence()
        p.brisc.j(wait)
        p.brisc.label(ready_label)
        p.brisc.lw(candidate_key, address, 0)
        p.brisc.lw(candidate_id, address, 4)
        p.brisc.sw(R.ZERO, address, 8)
        skip = p.brisc._new_label("argmax_skip_partial")
        p.brisc.bgeu(best_key, candidate_key, skip)
        p.brisc.mv(best_key, candidate_key)
        p.brisc.mv(best_id, candidate_id)
        p.brisc.label(skip)
    # Scalar NoC writes require a 16-byte-aligned source address.
    p.brisc.write(local, best_id)
    with p.brisc.scope():
      target_address, position, offset = p.brisc.reg(3)
      p.brisc.read(target_address, p.param_addr(host_address))
      p.brisc.read(position, p.param_addr(write_pos))
      p.brisc.slli(offset, position, 4)
      p.brisc.add(target_address, target_address, offset)
      p.brisc.noc.write(
        local, target_address, CQConfig.PCIE_COORD, 16,
        target_middle_address=CQConfig.PCIE_MID, posted=False,
      )
    history_done = p.brisc._new_label("argmax_history_done")
    with p.brisc.scope():
      position, tile, within, enabled = p.brisc.reg(4)
      p.brisc.read(enabled, p.param_addr(write_token))
      p.brisc.beq(enabled, R.ZERO, history_done)
      p.brisc.read(position, p.param_addr(write_pos))
      p.brisc.srli(tile, position, 10)
      p.brisc.andi(within, position, 1023)
      p.brisc.noc.read_tile(token_history, tile, history_l1)
      p.brisc.slli(within, within, 2)
      _add_constant(p.brisc, within, history_l1)
      p.brisc.write(within, best_id)
      target_address, target_coordinate = p.brisc.noc._dram_tile(
        token_history, tile,
      )
      p.brisc.noc.write(
        history_l1, target_address, target_coordinate,
        token_history.tile_size, posted=False,
      )
    p.brisc.label(history_done)

    # Prepare the next token's compact runtime state on device. Host-driven
    # replay may overwrite it, while autonomous replay can consume it directly.
    with p.brisc.scope():
      position, value = p.brisc.reg(2)
      p.brisc.read(position, p.param_addr(write_pos))
      p.brisc.write(runtime_l1, position)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE, position)
      p.brisc.addi(value, position, 1)
      p.brisc.write(runtime_l1 + 4, value)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 4, value)
      p.brisc.write(runtime_l1 + 8, 1)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 8, 1)
      p.brisc.write(runtime_l1 + 12, position)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 12, position)
      p.brisc.srli(value, position, 5)
      p.brisc.addi(value, value, 1)
      p.brisc.write(runtime_l1 + 16, value)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 16, value)
      p.brisc.andi(value, position, 31)
      p.brisc.addi(value, value, 1)
      p.brisc.write(runtime_l1 + 20, value)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 20, value)
      for rect in rectangles(logits.cores):
        start, end = mcast_coords(rect)
        p.brisc.noc.multicast_write(
          runtime_l1, TensixL1.RUNTIME_PARAM_BASE, start, end, 24,
        )
    p.brisc.label(reducer_done)
  # TRISC0/1/2: SFPU scan of the logits -> 32 (value, index) candidates.
  CB.wait_front(p.trisc0, incoming, logits.tiles_per_item)
  load_bf16(p, logits_l1, logits.tiles_per_item)
  CB.pop_front(p.trisc0, incoming, logits.tiles_per_item)
  scan_bf16(p.trisc1, logits.tiles_per_item)
  p.trisc1.emit(TT.TTSFPSTORE(0, 4, 0, 0))
  p.trisc1.emit(TT.TTSFPSTORE(4, 4, 0, 2))
  p.sfpu.publish()
  p.pack.move(candidates, tile=0)
  return p
