import argparse, math, struct, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Cond
from cq import McastWrite, UnicastWrite
from program import Buffer, DType, Dram, Program, rectangles
from ttk.reduce import scalar_reduce_tile


ARGS_BASE = 0x4300
ARG_TILE_START = 0
ARG_TILE_COUNT = 4
ARG_CORE_INDEX = 8
ARG_CORE_COUNT = 12
ARG_ROOT_COORD = 16
ARG_IS_ROOT = 20
ARG_GROUP_LOCAL_INDEX = 24
ARG_GROUP_SIZE = 28
ARG_GROUP_ROOT_COORD = 32
ARG_IS_GROUP_ROOT = 36
ARG_GROUP_PAGES = 40
ARG_GROUP_INDEX = 44
ARG_GROUP_COUNT = 48
ARG_WORKSPACE_ADDR = 52
ARG_WORKSPACE_COORD = 56
ARG_REGION_ROOT_COORD = 60
ARG_IS_REGION_ROOT = 64
ARG_REGION_GROUP_INDEX = 68
ARG_REGION_GROUP_COUNT = 72
ARG_REGION_INDEX = 76
ARG_REGION_COUNT = 80
ARG_REGION_TARGETS = 84
PARTIAL_BYTES = 16
GATHER_FAN_IN = 8
# Four gather pages are reliable, but a completely full 32-scalar gather
# wraps the current scalar-pack layout. Keep one slot empty.
GROUP_SIZE = 31
P100_WORKERS = tuple(
  (x, y) for x in (*range(1, 8), *range(10, 15)) for y in range(2, 12)
  if (x, y) not in ((14, 2), (14, 3))
)


def cross_core_mean(src: Buffer, dst: Buffer, workspace: Buffer, cores, *, root=None) -> Program:
  """Reduce BF16 tiles across a P100 using FP32 Tensix accumulators.

  Local sums, subgroup sums, regional sums, and the final normalized sum all
  use FP32 destination mode. Packed hierarchy edges and the output are BF16.
  """
  cores = tuple(cores)
  if src.dtype is not DType.BF16 or dst.dtype is not DType.BF16:
    raise ValueError("cross_core_mean requires BF16 buffers")
  if workspace.dtype is not DType.BF16:
    raise ValueError("cross_core_mean workspace must be BF16")
  if workspace.dram_coords is None:
    raise ValueError("cross_core_mean workspace must be in device DRAM")
  if dst.pages != 1: raise ValueError("cross_core_mean output must be one tile")
  if len(cores) < 3: raise ValueError("cross_core_mean requires at least three cores")
  if len(cores) > 128: raise ValueError("gather tile supports at most 128 cores")
  root = cores[0] if root is None else root
  if root not in cores: raise ValueError("root must be one of the worker cores")

  grouped_cores = tuple(core for core in cores if core != root)
  # P100 worker columns form two connected regions (x=1..7 and x=10..14).
  # Keep first-stage traffic inside a region instead of routing a reduction
  # group across the non-worker x=8..9 gap.
  regions = tuple(filter(None, (
    tuple(core for core in grouped_cores if core[0] <= 7),
    tuple(core for core in grouped_cores if core[0] >= 10),
  )))
  region_roots = tuple(region[0] for region in regions)
  groups = []
  group_regions = []
  for region_index, region in enumerate(regions):
    members = region[1:]
    group_count = (len(members) + GROUP_SIZE - 1) // GROUP_SIZE
    base, extra = divmod(len(members), group_count)
    start = 0
    for index in range(group_count):
      size = base + int(index < extra)
      groups.append(members[start:start + size]); group_regions.append(region_index); start += size
  groups = tuple(groups)
  # Reducer cores have dedicated roles. Keeping input work off them bounds
  # every FP32 destination section to the reliable four-page reduction path.
  group_roots = tuple(group[-1] for group in groups)
  if len(groups) > GATHER_FAN_IN:
    raise ValueError("cross_core_mean supports at most eight reduction groups")
  if workspace.pages < len(regions):
    raise ValueError("cross_core_mean workspace needs one tile per worker region")
  input_cores = tuple(
    core for core in cores
    if core != root and core not in region_roots and core not in group_roots
  )
  if src.pages < len(input_cores):
    raise ValueError("cross_core_mean requires at least one tile per input core")
  if src.pages > 2 * len(input_cores):
    raise ValueError("cross_core_mean supports at most two input tiles per data core")

  p = Program(cores, buffers=(src, dst, workspace))
  depth = min(4, (src.pages + len(input_cores) - 1) // len(input_cores))
  input_cb = p.cb(src.dtype, depth, name="input")
  scaler_cb = p.cb(src.dtype, 1, name="scaler")
  partial_cb = p.cb(dst.dtype, 1, name="partial")
  max_gather_pages = (max(map(len, groups)) + GATHER_FAN_IN - 1) // GATHER_FAN_IN
  gather_cb = p.cb(dst.dtype, max_gather_pages + 1, name="gather")
  ready_addr = gather_cb.addr + max_gather_pages * gather_cb.page_size
  region_gather_cb = p.cb(dst.dtype, 2, name="region_gather")
  region_ready_addr = region_gather_cb.addr + region_gather_cb.page_size
  final_gather_cb = p.cb(dst.dtype, 1, name="final_gather")

  input_reader = p.brisc.init_cb(input_cb)
  input_unpack = p.trisc0.init_cb(input_cb)
  scaler_unpack = p.trisc0.init_cb(scaler_cb)
  partial_pack = p.trisc2.init_cb(partial_cb)
  partial_reader = p.ncrisc.init_cb(partial_cb)
  gather_writer = p.ncrisc.init_cb(gather_cb)
  gather_unpack = p.trisc0.init_cb(gather_cb)
  region_gather_writer = p.ncrisc.init_cb(region_gather_cb)
  region_gather_unpack = p.trisc0.init_cb(region_gather_cb)
  final_gather_writer = p.ncrisc.init_cb(final_gather_cb)
  final_gather_unpack = p.trisc0.init_cb(final_gather_cb)

  p.unpack.init_scalar_reduce(input_unpack, scaler_unpack)
  p.math.initialize_scalar_reduce(fp32_dest=True)
  p.pack.init_scalar_reduce(partial_pack, fp32_dest=True)

  with p.brisc.scope():
    start, count = p.brisc.reg(2)
    p.brisc.load(start, ARGS_BASE + ARG_TILE_START)
    p.brisc.load(count, ARGS_BASE + ARG_TILE_COUNT)
    noc = p.brisc.noc(0).initialize_from_firmware()
    for tile in p.brisc.range(count):
      input_reader.reserve_back()
      with p.brisc.scope():
        page = p.brisc.reg(); p.brisc.add(page, start, tile)
        with noc.read_batch() as reads: reads.issue_dram(src, page, input_reader)
      input_reader.push_back()

  with p.trisc0.scope():
    count, is_root, is_group_root, is_region_root, group_pages = p.trisc0.reg(5)
    p.trisc0.load(count, ARGS_BASE + ARG_TILE_COUNT)
    p.trisc0.load(is_root, ARGS_BASE + ARG_IS_ROOT)
    p.trisc0.load(is_group_root, ARGS_BASE + ARG_IS_GROUP_ROOT)
    p.trisc0.load(is_region_root, ARGS_BASE + ARG_IS_REGION_ROOT)
    p.trisc0.load(group_pages, ARGS_BASE + ARG_GROUP_PAGES)
    for _ in p.trisc0.range(count):
      input_unpack.wait_front()
      p.unpack.wait_config_idle().configure_scalar_reduce(input_unpack, scaler_unpack).commit_config()
      p.unpack.scalar_reduce().wait()
      input_unpack.pop_front()
    with p.trisc0.if_(Cond(is_group_root, "!=", 0)):
      for _ in p.trisc0.range(group_pages):
        gather_unpack.wait_front()
        p.unpack.wait_config_idle().configure_scalar_reduce(gather_unpack, scaler_unpack).commit_config()
        p.unpack.scalar_reduce().wait()
        gather_unpack.pop_front()
    with p.trisc0.if_(Cond(is_region_root, "!=", 0)):
      region_gather_unpack.wait_front()
      p.unpack.wait_config_idle().configure_scalar_reduce(region_gather_unpack, scaler_unpack).commit_config()
      p.unpack.scalar_reduce().wait()
      region_gather_unpack.pop_front()
    with p.trisc0.if_(Cond(is_root, "!=", 0)):
      final_gather_unpack.wait_front()
      p.unpack.wait_config_idle().configure_scalar_reduce(final_gather_unpack, scaler_unpack).commit_config()
      p.unpack.scalar_reduce().wait()
      final_gather_unpack.pop_front()

  with p.trisc1.scope():
    count, is_root, is_group_root, is_region_root, group_pages = p.trisc1.reg(5)
    p.trisc1.load(count, ARGS_BASE + ARG_TILE_COUNT)
    p.trisc1.load(is_root, ARGS_BASE + ARG_IS_ROOT)
    p.trisc1.load(is_group_root, ARGS_BASE + ARG_IS_GROUP_ROOT)
    p.trisc1.load(is_region_root, ARGS_BASE + ARG_IS_REGION_ROOT)
    p.trisc1.load(group_pages, ARGS_BASE + ARG_GROUP_PAGES)
    p.math.acquire_dst().clear_dst()
    for _ in p.trisc1.range(count): p.math.scalar_reduce()
    p.math.publish_dst()
    with p.trisc1.if_(Cond(is_group_root, "!=", 0)):
      p.math.acquire_dst().clear_dst()
      for _ in p.trisc1.range(group_pages): p.math.scalar_reduce()
      p.math.publish_dst()
    with p.trisc1.if_(Cond(is_region_root, "!=", 0)):
      p.math.acquire_dst().clear_dst().scalar_reduce().publish_dst()
    with p.trisc1.if_(Cond(is_root, "!=", 0)):
      p.math.acquire_dst().clear_dst().scalar_reduce().publish_dst()

  with p.trisc2.scope():
    is_root, is_group_root, is_region_root = p.trisc2.reg(3)
    p.trisc2.load(is_root, ARGS_BASE + ARG_IS_ROOT)
    p.trisc2.load(is_group_root, ARGS_BASE + ARG_IS_GROUP_ROOT)
    p.trisc2.load(is_region_root, ARGS_BASE + ARG_IS_REGION_ROOT)
    p.pack.acquire_dst(); partial_pack.reserve_back(); p.pack.to_cb()
    partial_pack.push_back(); p.pack.release_dst()
    with p.trisc2.if_(Cond(is_group_root, "!=", 0)):
      p.pack.acquire_dst(); partial_pack.reserve_back(); p.pack.to_cb()
      partial_pack.push_back(); p.pack.release_dst()
    with p.trisc2.if_(Cond(is_region_root, "!=", 0)):
      p.pack.acquire_dst(); partial_pack.reserve_back(); p.pack.to_cb()
      partial_pack.push_back(); p.pack.release_dst()
    with p.trisc2.if_(Cond(is_root, "!=", 0)):
      p.pack.acquire_dst(); partial_pack.reserve_back(); p.pack.to_cb()
      partial_pack.push_back(); p.pack.release_dst()

  with p.ncrisc.scope():
    local_index, group_size, group_root_coord, is_group_root = p.ncrisc.reg(4)
    is_root, group_index, group_count, group_pages = p.ncrisc.reg(4)
    p.ncrisc.load(local_index, ARGS_BASE + ARG_GROUP_LOCAL_INDEX)
    p.ncrisc.load(group_size, ARGS_BASE + ARG_GROUP_SIZE)
    p.ncrisc.load(group_root_coord, ARGS_BASE + ARG_GROUP_ROOT_COORD)
    p.ncrisc.load(is_group_root, ARGS_BASE + ARG_IS_GROUP_ROOT)
    p.ncrisc.load(is_root, ARGS_BASE + ARG_IS_ROOT)
    p.ncrisc.load(group_index, ARGS_BASE + ARG_GROUP_INDEX)
    p.ncrisc.load(group_count, ARGS_BASE + ARG_IS_REGION_ROOT)
    p.ncrisc.load(group_pages, ARGS_BASE + ARG_GROUP_PAGES)
    noc = p.ncrisc.noc(0).initialize_from_firmware()
    pull_noc = noc
    partial_reader.wait_front()
    with p.ncrisc.scope():
      source, target, base, ready, offset, chunk = p.ncrisc.reg(6)
      partial_reader.read_ptr(source)
      p.ncrisc.lw(ready, source); p.ncrisc.slli(ready, ready, 16); p.ncrisc.srli(ready, ready, 16)
      p.ncrisc.sw(ready, source); p.ncrisc.li(ready, 0)
      for byte_offset in (4, 8, 12): p.ncrisc.sw(ready, source, byte_offset)
      p.ncrisc.fence()
      with p.ncrisc.if_(Cond(is_root, "==", 0)):
        with p.ncrisc.if_(Cond(group_count, "==", 0)):
          p.ncrisc.andi(offset, local_index, GATHER_FAN_IN - 1); p.ncrisc.slli(offset, offset, 4)
          p.ncrisc.srli(chunk, local_index, 3); p.ncrisc.slli(chunk, chunk, 11); p.ncrisc.add(offset, offset, chunk)
          p.ncrisc.li(base, gather_cb.addr); p.ncrisc.add(target, offset, base)
          with noc.write_batch(count=1) as writes: writes.issue(source, target, group_root_coord, PARTIAL_BYTES)
          p.ncrisc.slli(offset, local_index, 4); p.ncrisc.li(base, ready_addr); p.ncrisc.add(target, offset, base)
          p.ncrisc.li(ready, 1); p.ncrisc.sw(ready, source, 4); p.ncrisc.fence()
          with noc.write_ack_batch(count=1) as writes: writes.issue(source, target, group_root_coord, PARTIAL_BYTES)
    partial_reader.pop_front()
    with p.ncrisc.if_(Cond(is_group_root, "!=", 0)):
      with p.ncrisc.scope():
        slot, ready = p.ncrisc.reg(2); p.ncrisc.li(slot, ready_addr + 4)
        for _ in p.ncrisc.range(group_size):
          with p.ncrisc.loop():
            p.ncrisc.lw(ready, slot)
            p.ncrisc.break_(Cond(ready, "!=", 0))
          p.ncrisc.addi(slot, slot, 16)
      for _ in p.ncrisc.range(group_pages): gather_writer.push_back()
      partial_reader.wait_front()
      with p.ncrisc.scope():
        source, ready, target = p.ncrisc.reg(3); partial_reader.read_ptr(source)
        p.ncrisc.lw(ready, source); p.ncrisc.slli(ready, ready, 16); p.ncrisc.srli(ready, ready, 16)
        p.ncrisc.sw(ready, source); p.ncrisc.li(ready, 0)
        for byte_offset in (4, 8, 12): p.ncrisc.sw(ready, source, byte_offset)
        p.ncrisc.load(group_index, ARGS_BASE + ARG_REGION_GROUP_INDEX); p.ncrisc.slli(group_index, group_index, 4)
        p.ncrisc.load(group_root_coord, ARGS_BASE + ARG_REGION_ROOT_COORD)
        p.ncrisc.li(target, region_gather_cb.addr); p.ncrisc.add(target, target, group_index)
        with noc.write_batch(count=1) as writes:
          writes.issue(source, target, group_root_coord, PARTIAL_BYTES)
        p.ncrisc.li(ready, 1); p.ncrisc.sw(ready, source, 4); p.ncrisc.fence()
        p.ncrisc.li(target, region_ready_addr); p.ncrisc.add(target, target, group_index)
        with noc.write_ack_batch(count=1) as writes:
          writes.issue(source, target, group_root_coord, PARTIAL_BYTES)
      partial_reader.pop_front()
    p.ncrisc.load(local_index, ARGS_BASE + ARG_IS_REGION_ROOT)
    with p.ncrisc.if_(Cond(local_index, "!=", 0)):
      p.ncrisc.load(group_size, ARGS_BASE + ARG_REGION_GROUP_COUNT)
      with p.ncrisc.scope():
        slot, ready = p.ncrisc.reg(2); p.ncrisc.li(slot, region_ready_addr + 4)
        for _ in p.ncrisc.range(group_size):
          with p.ncrisc.loop():
            p.ncrisc.lw(ready, slot)
            p.ncrisc.break_(Cond(ready, "!=", 0))
          p.ncrisc.addi(slot, slot, PARTIAL_BYTES)
      region_gather_writer.push_back()
      partial_reader.wait_front()
      with p.ncrisc.scope():
        source, ready, target = p.ncrisc.reg(3); partial_reader.read_ptr(source)
        p.ncrisc.lw(ready, source); p.ncrisc.slli(ready, ready, 16); p.ncrisc.srli(ready, ready, 16)
        p.ncrisc.sw(ready, source); p.ncrisc.li(ready, 0)
        for byte_offset in (4, 8, 12): p.ncrisc.sw(ready, source, byte_offset)
        p.ncrisc.li(ready, 1); p.ncrisc.sw(ready, source, 4); p.ncrisc.fence()
        p.ncrisc.load(target, ARGS_BASE + ARG_WORKSPACE_ADDR)
        p.ncrisc.load(group_index, ARGS_BASE + ARG_WORKSPACE_COORD)
        with noc.write_ack_batch(count=1) as writes:
          writes.issue(source, target, group_index, PARTIAL_BYTES)
      partial_reader.pop_front()
    p.ncrisc.load(group_count, ARGS_BASE + ARG_REGION_COUNT)
    with p.ncrisc.if_(Cond(is_root, "!=", 0)):
      with p.ncrisc.scope():
        target, ready = p.ncrisc.reg(2)
        p.ncrisc.li(target, final_gather_cb.addr)
        p.ncrisc.li(group_index, ARGS_BASE + ARG_REGION_TARGETS)
        for _ in p.ncrisc.range(group_count):
          with p.ncrisc.loop():
            p.ncrisc.lw(local_index, group_index); p.ncrisc.lw(group_size, group_index, 4)
            with pull_noc.read_batch(count=1) as reads:
              reads.issue(local_index, group_size, target, PARTIAL_BYTES)
            p.ncrisc.lw(ready, target, 4)
            p.ncrisc.break_(Cond(ready, "!=", 0))
          p.ncrisc.li(ready, 0); p.ncrisc.sw(ready, target, 4)
          p.ncrisc.addi(group_index, group_index, 8); p.ncrisc.addi(target, target, PARTIAL_BYTES)
      final_gather_writer.push_back()
      partial_reader.wait_front()
      with noc.write_ack_batch(count=1) as writes: writes.issue_dram(dst, 0, partial_reader)
      partial_reader.pop_front()

  tiles_per_core, extra = divmod(src.pages, len(input_cores))
  input_assignment = {}
  for index, core in enumerate(input_cores):
    input_assignment[core] = (
      index * tiles_per_core + min(index, extra),
      tiles_per_core + int(index < extra),
    )
  group_assignment = {}
  region_assignment = {}
  region_group_counts = tuple(group_regions.count(index) for index in range(len(regions)))
  next_group_in_region = [0] * len(regions)
  for group_index, group in enumerate(groups):
    group_pages = (len(group) + GATHER_FAN_IN - 1) // GATHER_FAN_IN
    region_index = group_regions[group_index]
    region_group_index = next_group_in_region[region_index]
    next_group_in_region[region_index] += 1
    for local_index, core in enumerate(group):
      group_assignment[core] = (local_index, len(group), group_roots[group_index], group_pages, group_index)
      region_assignment[core] = (
        region_roots[region_index], 0, region_group_index,
        region_group_counts[region_index], region_index,
      )
  for region_index, region_root in enumerate(region_roots):
    group_assignment[region_root] = (0, 0, group_roots[0], 0, 0)
    region_assignment[region_root] = (
      region_root, 1, 0, region_group_counts[region_index], region_index,
    )
  group_assignment[root] = (0, 0, group_roots[0], 0, 0)
  region_assignment[root] = (region_roots[0], 0, 0, 0, 0)
  args = []
  region_targets = []
  for region_index, region in enumerate(regions):
    bank = 0
    region_targets.append((
      workspace.addr + region_index * PARTIAL_BYTES,
      workspace.dram_coords[0][bank],
      workspace.dram_coords[1][bank],
    ))
  region_targets = tuple(region_targets)
  target_table = tuple(value for address, _, pull_coord in region_targets for value in (address, pull_coord))
  target_table += (0,) * (4 - len(target_table))
  for index, core in enumerate(cores):
    start, count = input_assignment.get(core, (0, 0))
    local_index, group_size, group_root, group_pages, group_index = group_assignment[core]
    region_root, is_region_root, region_group_index, region_group_count, region_index = region_assignment[core]
    workspace_addr, workspace_coord, _ = region_targets[region_index]
    args.append(struct.pack(
      "<25I", start, count, index, len(cores), root[0] | root[1] << 6, int(core == root),
      local_index, group_size, group_root[0] | group_root[1] << 6, int(core == group_root),
      group_pages, group_index, len(regions), workspace_addr, workspace_coord,
      region_root[0] | region_root[1] << 6, is_region_root, region_group_index,
      region_group_count, region_index, len(regions), *target_table,
    ))
  # scalar_reduce multiplies by its scaler twice. The global root is a
  # dedicated final reducer, so its fixed SrcB scaler can normalize without
  # runtime unpack reconfiguration.
  mean_scale = 1 / math.sqrt(src.pages * 1024)
  zero_gathers = tuple(
    UnicastWrite(
      group_roots, gather_cb.addr + page * gather_cb.page_size,
      (bytes(GATHER_FAN_IN * PARTIAL_BYTES),) * len(group_roots),
    )
    for page in range(max_gather_pages)
  )
  zero_workspace = tuple(
    UnicastWrite(
      ((workspace.dram_coords[0][0] & 0x3F, workspace.dram_coords[0][0] >> 6),),
      workspace.addr, (bytes(PARTIAL_BYTES * len(regions)),),
    )
    for _ in (0,)
  )
  p.launch = (
    *zero_workspace,
    UnicastWrite(cores, ARGS_BASE, tuple(args)),
    McastWrite(rectangles(cores), scaler_cb.addr, scalar_reduce_tile(1, src.dtype)),
    UnicastWrite((root,), scaler_cb.addr, (scalar_reduce_tile(mean_scale, src.dtype),)),
    *zero_gathers,
    UnicastWrite(
      group_roots, ready_addr,
      (bytes(max(map(len, groups)) * PARTIAL_BYTES),) * len(group_roots),
    ),
    UnicastWrite(region_roots, region_gather_cb.addr, (bytes(2 * region_gather_cb.page_size),) * len(region_roots)),
    UnicastWrite((root,), final_gather_cb.addr, (bytes(final_gather_cb.page_size),)),
  )
  return p


def run_hardware(tiles=118, repeats=10, core_offset=0):
  import numpy as np
  from device import Device

  device = Device()
  try:
    device.init_device()
    shape = (32, 32 * tiles)
    src = device.dram.buffer("src", DType.BF16, shape, shape)
    dst = device.dram.buffer("dst", DType.BF16, (1, 1), (32, 32))
    workspace = device.dram.buffer("workspace", DType.BF16, (32, 64), (32, 64))
    core_count = min(tiles, len(device.pcie.cores) - core_offset)
    cores = tuple(device.pcie.cores[core_offset:core_offset + core_count])
    program = cross_core_mean(src, dst, workspace, cores)
    values = (np.arange(1024 * tiles, dtype=np.float32) % 31).reshape(shape) / 16
    source = src.from_numpy(values)
    device.write(src, source)
    timings = device.run(program)
    actual = float(dst.to_numpy(device.read(dst))[0, 0])
    expected = float(src.to_numpy(source).mean())
    tolerance = max(2e-3, abs(expected) * 2e-2)
    if abs(actual - expected) > tolerance:
      raise AssertionError(f"mean mismatch: actual={actual}, expected={expected}, tolerance={tolerance}")
    samples = [timings[-1].us]
    for _ in range(repeats - 1): samples.append(device.run(program)[0].us)
    print(f"PASS mean: tiles={tiles} cores={len(cores)} actual={actual:.7g} expected={expected:.7g}")
    print(f"latency_us min={min(samples):.3f} median={float(np.median(samples)):.3f} samples={samples}")
  finally: device.close()


def show(program: Program):
  print(f"cores: {len(program.cores)}")
  print(f"CBs:   {program.cbs}")
  print(f"params: {[(buffer.name, hex(program.param_addr(buffer)), hex(buffer.addr)) for buffer in program.params.values()]}")
  for role, image in program.kernels[program.cores[0]].items():
    print(f"{role:7s}: {len(image):4d} bytes")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--run", action="store_true")
  parser.add_argument("--tiles", type=int, default=118)
  parser.add_argument("--repeats", type=int, default=10)
  parser.add_argument("--core-offset", type=int, default=0)
  args = parser.parse_args()
  if args.tiles <= 0: parser.error("--tiles must be positive")
  if args.repeats <= 0: parser.error("--repeats must be positive")
  if args.core_offset < 0: parser.error("--core-offset must be nonnegative")
  if args.run: return run_hardware(args.tiles, args.repeats, args.core_offset)
  cores = P100_WORKERS[args.core_offset:args.core_offset + min(args.tiles, len(P100_WORKERS) - args.core_offset)]
  dram = Dram(harvested_dram_bank=3)
  shape = (32, 32 * args.tiles)
  src = dram.buffer("src", DType.BF16, shape, shape)
  dst = dram.buffer("dst", DType.BF16, (1, 1), (32, 32))
  workspace = dram.buffer("workspace", DType.BF16, (32, 64), (32, 64))
  show(cross_core_mean(src, dst, workspace, cores))


if __name__ == "__main__": main()
