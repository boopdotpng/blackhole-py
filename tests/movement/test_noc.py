from dataclasses import dataclass
from statistics import median
from struct import Struct

import pytest

from asm import Asm
from fw.consts import TensixL1, TensixMMIO
from tests.movement.noc import (
  InterleavedConfig, emit_cb_discard, emit_cb_generate,
  emit_interleaved_dram_to_l1, emit_interleaving_benchmark,
  emit_l1_to_interleaved_dram,
)
from tests.profiler import Profiler


PAGE_BYTES = 2048
TILE_COUNT = 8192
CB_DEPTH = 64
BENCHMARK_DEPTHS = (1, 2, 4, 8, 16, 32, 64, 96, 128)
TENSOR_BYTES = TILE_COUNT * PAGE_BYTES
CB_ADDRESS = TensixL1.DATA_BUFFER_SPACE_BASE

# The many-core benchmark uses the largest hardware packet. It first tunes the
# ring depth and issue batch; each worker then receives an independent 1 MiB
# shard, still striped over all eight banks.
SCALING_PAGE_BYTES = 16 * 1024
SCALING_BYTES_PER_CORE = 1 * 1024 * 1024
STRONG_SCALING_BYTES = 128 * 1024 * 1024
SCALING_CB_CONFIGS = (
  (2, 1), (4, 2), (8, 4), (16, 4), (16, 8),
  (32, 8), (32, 16), (64, 16), (64, 32),
)
SCALING_COUNTS = (1, 2, 4, 8, 16, 32, 48, 64, 72, 76, 80, 84, 88, 96, 104, 112)
TIMING_L1_ADDRESS = TensixL1.DATA_BUFFER_SPACE_END - 64
TIMING_RECORD = Struct("<8I")
CLOCK_HI_TO_LO = (
  TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L -
  TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H
)
CLOCK_GHZ = 1.35

# P150 physical DRAM columns in the firmware's translated NoC coordinates.
# Keeping source and destination in different groups is the fastest measured
# full-card copy layout. Dependent stages may ping-pong; independent ones need
# not switch their placement.
LEFT_DRAM_BANKS = (0, 1, 2, 3)       # translated NoC x=17
MIDDLE_DRAM_BANKS = (4, 5, 6, 7)     # translated NoC x=18


def _data(size):
  pattern = bytes((index * 131 + index // 17 + 29) & 0xFF for index in range(4096))
  return (pattern * ((size + len(pattern) - 1) // len(pattern)))[:size]


def _config(bh, noc=0, depth=CB_DEPTH, *, page_bytes=PAGE_BYTES,
            command_slot=0, batch_pages=None):
  return InterleavedConfig(
    bh.dram_coordinates(noc, banks=8), CB_ADDRESS, depth, page_bytes, noc,
    command_slot=command_slot, batch_pages=batch_pages,
  )


def _record_clock(kernel, address):
  """Store one coherent 64-bit worker wall-clock sample in shared L1."""
  low, high, high_again, clock, output = kernel.reg(5)
  retry = kernel._new_label("movement_clock_retry")
  kernel.li(clock, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  kernel.label(retry)
  kernel.lw(high, clock)
  kernel.lw(low, clock, CLOCK_HI_TO_LO)
  kernel.lw(high_again, clock)
  kernel.bne(high, high_again, retry)
  kernel.li(output, address)
  kernel.sw(low, output)
  kernel.sw(high, output, 4)
  kernel.fence()


@dataclass(frozen=True)
class _CoreTiming:
  brisc_start: int
  brisc_end: int
  ncrisc_start: int
  ncrisc_end: int

  @classmethod
  def read(cls, bh, core):
    words = TIMING_RECORD.unpack(
      bh.read_l1(core, TIMING_L1_ADDRESS, TIMING_RECORD.size),
    )
    values = tuple(words[index] | words[index + 1] << 32
                   for index in range(0, len(words), 2))
    return cls(*values)

  @property
  def completion_cycles(self):
    return self.ncrisc_end - min(self.brisc_start, self.ncrisc_start)


def _scaling_row(count, timings, cores=None, *, bytes_per_core=SCALING_BYTES_PER_CORE):
  cores = tuple(range(count)) if cores is None else tuple(cores)
  if len(cores) != len(timings):
    raise ValueError("timing/core count mismatch")
  start = min(min(item.brisc_start, item.ncrisc_start) for item in timings)
  read_end = max(item.brisc_end for item in timings)
  end = max(item.ncrisc_end for item in timings)
  read_cycles = read_end - min(item.brisc_start for item in timings)
  write_cycles = end - min(item.ncrisc_start for item in timings)
  copy_cycles = end - start
  total_bytes = count * bytes_per_core
  completions = [item.completion_cycles for item in timings]
  per_core = tuple(zip(cores, completions))
  slowest_core, slowest_cycles = max(per_core, key=lambda item: item[1])
  return {
    "cores": count,
    "bytes_per_core": bytes_per_core,
    "total_bytes": total_bytes,
    "read_gb_s": total_bytes * CLOCK_GHZ / read_cycles,
    "write_gb_s": total_bytes * CLOCK_GHZ / write_cycles,
    "copy_gb_s": total_bytes * CLOCK_GHZ / copy_cycles,
    "dram_gb_s": 2 * total_bytes * CLOCK_GHZ / copy_cycles,
    "cycles": copy_cycles,
    "median_cycles": median(completions),
    "max_cycles": slowest_cycles,
    "slowest_core": slowest_core,
    "per_core": per_core,
  }


def _print_scaling_curve(rows, title):
  peak = max(row["dram_gb_s"] for row in rows)
  peak_row = max(rows, key=lambda row: row["dram_gb_s"])
  collapse, running_peak = None, rows[0]
  for row in rows[1:]:
    if row["dram_gb_s"] > running_peak["dram_gb_s"]:
      running_peak = row
    elif row["dram_gb_s"] < running_peak["dram_gb_s"] * 0.90:
      collapse = row
      break
  print(
    f"\n{title}\n"
    "cores | MiB/core | read GB/s | write GB/s | copy GB/s | DRAM R+W GB/s | "
    "tail/median | slowest | curve"
  )
  for row in rows:
    bar = "#" * max(1, round(36 * row["dram_gb_s"] / peak))
    tail = row["max_cycles"] / row["median_cycles"]
    print(
      f'{row["cores"]:5d} | {row["bytes_per_core"] / (1 << 20):8.3f} | '
      f'{row["read_gb_s"]:9.1f} | '
      f'{row["write_gb_s"]:10.1f} | '
      f'{row["copy_gb_s"]:9.1f} | {row["dram_gb_s"]:13.1f} | '
      f'{tail:11.3f} | {str(row["slowest_core"]):>8s} | {bar}'
    )
  if collapse is None:
    print(f"no >=10% post-peak collapse through {rows[-1]['cores']} cores")
  else:
    print(
      f">=10% post-peak collapse begins at {collapse['cores']} cores "
      f"(peak {peak:.1f} GB/s at {peak_row['cores']} cores)"
    )
  slowest = sorted(rows[-1]["per_core"], key=lambda item: item[1], reverse=True)
  print("slowest final-launch cores: " + ", ".join(
    f"{core}={cycles} cyc" for core, cycles in slowest[:8]
  ))


def _movement_images(read_coordinates, write_coordinates, depth, batch_pages,
                     *, read_vc=1, write_vc=1, read_priority=0,
                     write_priority=0):
  read_config = InterleavedConfig(
    tuple(read_coordinates), CB_ADDRESS, depth, SCALING_PAGE_BYTES, 0,
    command_slot=1, batch_pages=batch_pages, static_vc=read_vc,
    priority=read_priority,
  )
  write_config = InterleavedConfig(
    tuple(write_coordinates), CB_ADDRESS, depth, SCALING_PAGE_BYTES, 1,
    command_slot=2, batch_pages=batch_pages, static_vc=write_vc,
    priority=write_priority,
  )
  if CB_ADDRESS + read_config.l1_bytes > TIMING_L1_ADDRESS:
    raise ValueError("scaling CB overlaps its L1 timing record")

  brisc = Asm("brisc")
  _record_clock(brisc, TIMING_L1_ADDRESS)
  emit_interleaved_dram_to_l1(brisc, read_config, 0, 1)
  _record_clock(brisc, TIMING_L1_ADDRESS + 8)

  ncrisc = Asm("ncrisc")
  _record_clock(ncrisc, TIMING_L1_ADDRESS + 16)
  emit_l1_to_interleaved_dram(ncrisc, write_config, 2, 1)
  _record_clock(ncrisc, TIMING_L1_ADDRESS + 24)
  return {"brisc": brisc.lower(), "ncrisc": ncrisc.lower()}


def _scaling_images(bh, depth, batch_pages):
  return _movement_images(
    bh.dram_coordinates(0, banks=8), bh.dram_coordinates(1, banks=8),
    depth, batch_pages,
  )


def _one_way_images(coordinates, depth, batch_pages, *, read, noc=None,
                    posted_write=False):
  if noc is None:
    noc = 0 if read else 1
  config = InterleavedConfig(
    tuple(coordinates), CB_ADDRESS, depth, SCALING_PAGE_BYTES,
    noc, command_slot=1 if read else 2,
    batch_pages=batch_pages, posted_write=posted_write,
  )
  brisc, ncrisc = Asm("brisc"), Asm("ncrisc")
  _record_clock(brisc, TIMING_L1_ADDRESS)
  if read:
    emit_interleaved_dram_to_l1(brisc, config, 0, 1)
  else:
    emit_cb_generate(brisc, config, 1)
  _record_clock(brisc, TIMING_L1_ADDRESS + 8)
  _record_clock(ncrisc, TIMING_L1_ADDRESS + 16)
  if read:
    emit_cb_discard(ncrisc, config, 1)
  else:
    emit_l1_to_interleaved_dram(ncrisc, config, 2, 1)
  _record_clock(ncrisc, TIMING_L1_ADDRESS + 24)
  return {"brisc": brisc.lower(), "ncrisc": ncrisc.lower()}


def _independent_traffic_images(read_coordinates, write_coordinates,
                                depth=8, batch_pages=4, *, standalone=False):
  """Emit independent read and write streams with separate CBs/counts."""
  read_config = InterleavedConfig(
    tuple(read_coordinates), CB_ADDRESS, depth, SCALING_PAGE_BYTES, 0,
    sync_slot=0, command_slot=1, batch_pages=batch_pages,
    standalone=standalone,
  )
  write_config = InterleavedConfig(
    tuple(write_coordinates), CB_ADDRESS + read_config.l1_bytes,
    depth, SCALING_PAGE_BYTES, 1, sync_slot=1, command_slot=2,
    batch_pages=batch_pages, standalone=standalone,
  )
  if write_config.l1_address + write_config.l1_bytes > TIMING_L1_ADDRESS:
    raise ValueError("independent traffic CBs overlap the timing record")

  brisc = Asm("brisc")
  _record_clock(brisc, TIMING_L1_ADDRESS)
  emit_interleaved_dram_to_l1(brisc, read_config, 0, 1)
  _record_clock(brisc, TIMING_L1_ADDRESS + 8)

  ncrisc = Asm("ncrisc")
  _record_clock(ncrisc, TIMING_L1_ADDRESS + 16)
  emit_l1_to_interleaved_dram(ncrisc, write_config, 2, 3)
  _record_clock(ncrisc, TIMING_L1_ADDRESS + 24)

  images = {"brisc": brisc.lower(), "ncrisc": ncrisc.lower()}
  if not standalone:
    trisc0 = Asm("trisc0")
    emit_cb_discard(trisc0, read_config, 1)
    trisc1 = Asm("trisc1")
    emit_cb_generate(trisc1, write_config, 3)
    images.update(trisc0=trisc0.lower(), trisc1=trisc1.lower())
  return images


def _traffic_ratio_row(count, timings, cores, read_bytes_per_core,
                       write_bytes_per_core):
  """Measure unequal concurrent streams over their common completion window."""
  start = min(min(item.brisc_start, item.ncrisc_start) for item in timings)
  end = max(max(item.brisc_end, item.ncrisc_end) for item in timings)
  cycles = end - start
  read_bytes = count * read_bytes_per_core
  write_bytes = count * write_bytes_per_core
  read_cycles = max(item.brisc_end for item in timings) - min(
    item.brisc_start for item in timings
  )
  write_cycles = max(item.ncrisc_end for item in timings) - min(
    item.ncrisc_start for item in timings
  )
  completions = [
    max(item.brisc_end, item.ncrisc_end) -
    min(item.brisc_start, item.ncrisc_start)
    for item in timings
  ]
  per_core = tuple(zip(cores, completions))
  slowest_core, slowest_cycles = max(per_core, key=lambda item: item[1])
  return {
    "read_gb_s": read_bytes * CLOCK_GHZ / cycles,
    "write_gb_s": write_bytes * CLOCK_GHZ / cycles,
    "dram_gb_s": (read_bytes + write_bytes) * CLOCK_GHZ / cycles,
    "read_active_gb_s": read_bytes * CLOCK_GHZ / read_cycles,
    "write_active_gb_s": write_bytes * CLOCK_GHZ / write_cycles,
    "cycles": cycles,
    "median_cycles": median(completions),
    "max_cycles": slowest_cycles,
    "slowest_core": slowest_core,
  }


def _round_up_bank_round(byte_count, bank_count):
  round_bytes = bank_count * SCALING_PAGE_BYTES
  return (byte_count + round_bytes - 1) // round_bytes * round_bytes


def _bank_partition(read_bank_count, *, middle_first):
  """Return disjoint physical banks, placing the read-heavy side first."""
  order = (
    MIDDLE_DRAM_BANKS + LEFT_DRAM_BANKS if middle_first else
    LEFT_DRAM_BANKS + MIDDLE_DRAM_BANKS
  )
  return order[:read_bank_count], order[read_bank_count:]


def _balanced_bank_assignment(cores, endpoints, *, localized):
  """Assign nearly equal workers per bank, optionally minimizing route hops."""
  cores = tuple(cores)
  capacities = [len(cores) // 8 + (bank < len(cores) % 8) for bank in range(8)]
  if not localized:
    return tuple(index % 8 for index in range(len(cores)))

  # Translated Blackhole coordinates span a 19x24 torus. A NoC0 DRAM-read
  # response and a NoC1 DRAM write both take the wrapping direction represented
  # by source-worker minus DRAM endpoint here. Prioritize workers whose second
  # choice is much worse, then greedily respect equal bank capacities.
  def cost(core, bank):
    return sum(
      (core[0] - endpoint[0]) % 19 + (core[1] - endpoint[1]) % 24
      for endpoint in endpoints[bank]
    )

  costs = [[cost(core, bank) for bank in range(8)] for core in cores]
  order = sorted(
    range(len(cores)),
    key=lambda index: sorted(costs[index])[1] - min(costs[index]),
    reverse=True,
  )
  assignment = [None] * len(cores)
  for index in order:
    bank = min(
      (bank for bank in range(8) if capacities[bank]),
      key=lambda candidate: costs[index][candidate],
    )
    assignment[index] = bank
    capacities[bank] -= 1
  return tuple(assignment)


def _explicit_dram_port_coordinates(endpoint_pairs, noc, port):
  """Select one of the three mirrored ports for every supplied DRAM bank."""
  if port not in (0, 1, 2):
    raise ValueError("DRAM port must be zero, one, or two")
  coordinates = []
  for pair in endpoint_pairs:
    x = pair[noc][0]
    first_y = 12 + ((min(pair[0][1], pair[1][1]) - 12) // 3) * 3
    coordinates.append(x | (first_y + port) << 6)
  return tuple(coordinates)


def _rotate_bank_coordinates(coordinates, bank_delta):
  """Map logical bank i to physical bank (i + bank_delta) modulo eight."""
  coordinates = tuple(coordinates)
  if len(coordinates) != 8:
    raise ValueError("bank rotation requires exactly eight coordinates")
  if type(bank_delta) is not int or not 0 <= bank_delta < 8:
    raise ValueError("bank rotation must be in [0, 7]")
  return coordinates[bank_delta:] + coordinates[:bank_delta]


def _run_bank_sharded_case(bh, cores, assignments, buffers, images):
  bank_slots = [0] * 8
  params, mapped_images = {}, {}
  for core, bank in zip(cores, assignments):
    slot = bank_slots[bank]
    bank_slots[bank] += 1
    source, result = buffers[bank]
    params[core] = (
      source.address + slot * SCALING_BYTES_PER_CORE,
      SCALING_BYTES_PER_CORE,
      result.address + slot * SCALING_BYTES_PER_CORE,
    )
    mapped_images[core] = images[bank]
  bh.launch_many_mapped(mapped_images, params=params)
  timings = [_CoreTiming.read(bh, core) for core in cores]
  return _scaling_row(len(cores), timings, cores), tuple(bank_slots)


def test_direct_noc_emitters_reject_misaligned_l1():
  with pytest.raises(ValueError, match="16-byte-aligned"):
    InterleavedConfig(tuple(range(8)), CB_ADDRESS + 1,
                      CB_DEPTH)


def test_direct_noc_emitters_reject_empty_pages():
  with pytest.raises(ValueError, match="page size must be positive"):
    InterleavedConfig(tuple(range(8)), CB_ADDRESS, page_bytes=0)


def test_direct_noc_emitters_assemble_without_ttk():
  config = InterleavedConfig(tuple(18 | y << 6 for y in range(8)),
                             CB_ADDRESS, CB_DEPTH, PAGE_BYTES)
  read = Asm("brisc")
  emit_interleaved_dram_to_l1(read, config)
  write = Asm("brisc")
  emit_l1_to_interleaved_dram(write, config)
  profiled_write = Asm("ncrisc")
  profile = Profiler(profiled_write)
  profile.record("kernel")
  emit_l1_to_interleaved_dram(profiled_write, config)
  profile.record("kernel")

  assert read.lower()
  assert write.lower()
  assert profiled_write.lower()


def test_batch_depth_is_bounded_by_cb_capacity():
  coordinates = tuple(18 | y << 6 for y in range(8))
  with pytest.raises(ValueError, match="issue batch"):
    InterleavedConfig(
      coordinates, CB_ADDRESS, depth=4, page_bytes=PAGE_BYTES,
      batch_pages=5,
    )


@pytest.mark.parametrize("depth", (1, 2, 3, 8, 64, 129))
def test_cb_depth_is_static_configuration(depth):
  config = InterleavedConfig(
    tuple(18 | y << 6 for y in range(8)), CB_ADDRESS, depth, PAGE_BYTES,
  )
  read, write = Asm("brisc"), Asm("ncrisc")
  emit_interleaved_dram_to_l1(read, config)
  emit_l1_to_interleaved_dram(write, config)

  assert config.l1_bytes == depth * PAGE_BYTES
  assert config.issue_depth == min(depth, 128)
  assert read.lower() and write.lower()


@pytest.mark.parametrize("depth", BENCHMARK_DEPTHS)
def test_interleaved_dram_bandwidth_through_cb(bh, depth):
  """Sweep CB depth while streaming 16 MiB through all eight DRAM banks."""
  source_bytes = _data(TENSOR_BYTES)
  source = bh.interleaved_dram_buffer(
    TENSOR_BYTES, page_size=PAGE_BYTES, banks=8, initial=source_bytes,
  )
  result = bh.interleaved_dram_buffer(
    TENSOR_BYTES, page_size=PAGE_BYTES, banks=8,
  )

  brisc = Asm("brisc")
  emit_interleaved_dram_to_l1(brisc, _config(bh, noc=0, depth=depth), 0, 1)

  ncrisc = Asm("ncrisc")
  profile = Profiler(ncrisc)
  profile.record("kernel")
  profile.record("interleaving")
  emit_interleaving_benchmark(
    ncrisc, _config(bh, noc=1, depth=depth), 2, 1,
  )
  profile.record("interleaving")
  profile.record("NoC write")
  emit_l1_to_interleaved_dram(
    ncrisc, _config(bh, noc=1, depth=depth), 2, 1,
  )
  profile.record("NoC write")
  profile.record("kernel")

  bh.launch(
    {"brisc": brisc.lower(), "ncrisc": ncrisc.lower()},
    params=(source.address, TENSOR_BYTES, result.address),
    profiler=profile,
  )

  assert bh.read(result) == source_bytes
  assert profile.last["NoC write"] > 0
  assert profile.last["interleaving"] > 0
  nominal_gib_s = TENSOR_BYTES * 1_350_000_000 / profile.last["NoC write"] / (1 << 30)
  cycles_per_tile = profile.last["interleaving"] / TILE_COUNT
  print(
    f"depth {depth:3d} ({depth * PAGE_BYTES >> 10:3d} KiB L1): "
    f"{nominal_gib_s:.2f} GiB/s at 1.35 GHz; "
    f"interleaving: {cycles_per_tile:.2f} cycles/tile"
  )


def test_asymmetric_interleaved_bank_split_bandwidth(bh):
  """Cross traffic ratios with disjoint 4:4 through 7:1 bank splits."""
  cores = tuple(bh.device.cores)
  core_count = len(cores)
  endpoint_pairs = bh.device.pcie.dram_endpoints[:8]
  unit_bytes = 2 << 20
  traffic_ratios = ((1, 1), (2, 1), (3, 1), (4, 1), (7, 1))
  read_bank_counts = (4, 5, 6, 7)

  # Round each direction independently to complete bank rounds. This gives
  # every worker an aligned per-bank stride while perturbing the requested
  # ratio by less than one bank round.
  cases = []
  for read_weight, write_weight in traffic_ratios:
    for read_bank_count in read_bank_counts:
      write_bank_count = 8 - read_bank_count
      read_bytes = _round_up_bank_round(
        unit_bytes * read_weight, read_bank_count,
      )
      write_bytes = _round_up_bank_round(
        unit_bytes * write_weight, write_bank_count,
      )
      cases.append({
        "weights": (read_weight, write_weight),
        "read_banks": read_bank_count,
        "write_banks": write_bank_count,
        "read_bytes": read_bytes,
        "write_bytes": write_bytes,
        "read_stride": read_bytes // read_bank_count,
        "write_stride": write_bytes // write_bank_count,
      })

  # Raw buffers reserve a common address interval in all eight banks. The
  # kernels select disjoint subsets themselves, which also permits wrapped
  # physical sets such as banks 4,5,6,7,0 without pretending they are a
  # contiguous host-visible interleaved tensor.
  read_span = max(case["read_stride"] * core_count for case in cases)
  write_span = max(case["write_stride"] * core_count for case in cases)
  source = bh.device.alloc_interleaved_dram(
    read_span * 8, page_size=SCALING_PAGE_BYTES, banks=8,
  )
  destination = bh.device.alloc_interleaved_dram(
    write_span * 8, page_size=SCALING_PAGE_BYTES, banks=8,
  )

  measurements = []
  for case in cases:
    for middle_first in (True, False):
      read_banks, write_banks = _bank_partition(
        case["read_banks"], middle_first=middle_first,
      )
      variants = [
        _independent_traffic_images(
          _explicit_dram_port_coordinates(
            tuple(endpoint_pairs[bank] for bank in read_banks), 0, port,
          ),
          _explicit_dram_port_coordinates(
            tuple(endpoint_pairs[bank] for bank in write_banks), 1, port,
          ),
        )
        for port in range(3)
      ]
      images = {
        core: variants[index % 3] for index, core in enumerate(cores)
      }
      params = {
        core: (
          source.address + index * case["read_stride"],
          case["read_bytes"],
          destination.address + index * case["write_stride"],
          case["write_bytes"],
        )
        for index, core in enumerate(cores)
      }
      repeats = []
      for _ in range(3):
        bh.launch_many_mapped(images, params=params)
        timings = [_CoreTiming.read(bh, core) for core in cores]
        repeats.append(_traffic_ratio_row(
          core_count, timings, cores,
          case["read_bytes"], case["write_bytes"],
        ))

      rate_keys = (
        "read_gb_s", "write_gb_s", "dram_gb_s",
        "read_active_gb_s", "write_active_gb_s",
      )
      measured = {key: median(row[key] for row in repeats)
                  for key in rate_keys}
      measured["tail"] = median(
        row["max_cycles"] / row["median_cycles"] for row in repeats
      )
      # A disjoint-bank model assigns 64 GB/s to every bank and says the
      # slower directional share determines joint completion.
      read_share = case["read_bytes"] / case["read_banks"]
      write_share = case["write_bytes"] / case["write_banks"]
      measured["ideal_gb_s"] = 64 * (
        case["read_bytes"] + case["write_bytes"]
      ) / max(read_share, write_share)
      measurements.append({
        **case,
        "orientation": "middle-first" if middle_first else "left-first",
        **measured,
      })

  print(
    "\nasymmetric independent DRAM streams (117 cores, median of 3):\n"
    "traffic | banks | best orientation | actual R:W | effective read | "
    "effective write | aggregate | bank model | efficiency | active R/W"
  )
  for weights in traffic_ratios:
    for read_bank_count in read_bank_counts:
      candidates = [
        row for row in measurements
        if row["weights"] == weights and
        row["read_banks"] == read_bank_count
      ]
      best = max(candidates, key=lambda row: row["dram_gb_s"])
      actual_ratio = best["read_bytes"] / best["write_bytes"]
      efficiency = best["dram_gb_s"] / best["ideal_gb_s"]
      print(
        f"  {weights[0]}:{weights[1]:<1d}    | "
        f"{best['read_banks']}:{best['write_banks']}   | "
        f"{best['orientation']:12s} | {actual_ratio:8.3f}:1 | "
        f"{best['read_gb_s']:13.1f} | {best['write_gb_s']:14.1f} | "
        f"{best['dram_gb_s']:9.1f} | {best['ideal_gb_s']:10.1f} | "
        f"{efficiency:9.1%} | {best['read_active_gb_s']:.1f}/"
        f"{best['write_active_gb_s']:.1f}"
      )

  print("  best split by traffic ratio:")
  for weights in traffic_ratios:
    candidates = [row for row in measurements if row["weights"] == weights]
    unrestricted = max(candidates, key=lambda row: row["dram_gb_s"])
    min_two = max(
      (row for row in candidates if row["write_banks"] >= 2),
      key=lambda row: row["dram_gb_s"],
    )
    print(
      f"    {weights[0]}:{weights[1]} traffic: measured best "
      f"{unrestricted['read_banks']}:{unrestricted['write_banks']} "
      f"at {unrestricted['dram_gb_s']:.1f} GB/s; min-two policy "
      f"{min_two['read_banks']}:{min_two['write_banks']} at "
      f"{min_two['dram_gb_s']:.1f} GB/s"
    )

  assert all(row["dram_gb_s"] > 0 for row in measurements)


def test_many_core_interleaved_dram_copy_scaling(bh):
  """Measure the all-core tail while BRISC reads and NCRISC writes DRAM."""
  available = tuple(bh.device.cores)
  counts = tuple(count for count in SCALING_COUNTS if count <= len(available))
  if counts[-1] != len(available):
    counts += (len(available),)
  max_cores = max(counts)
  total_bytes = max(max_cores * SCALING_BYTES_PER_CORE, STRONG_SCALING_BYTES)
  source_bytes = _data(total_bytes)
  source = bh.interleaved_dram_buffer(
    total_bytes, page_size=SCALING_PAGE_BYTES, banks=8,
    initial=source_bytes,
  )
  result = bh.interleaved_dram_buffer(
    total_bytes, page_size=SCALING_PAGE_BYTES, banks=8,
  )

  # Each shard contains a whole number of eight-bank rounds. Therefore its
  # per-bank base is simply advanced by one eighth of the logical shard size.
  per_bank_stride = SCALING_BYTES_PER_CORE // 8
  first_core = available[0]
  first_params = {first_core: (
    source.address, SCALING_BYTES_PER_CORE, result.address,
  )}

  # Tune the synchronization granularity separately from storage capacity.
  # Choosing the shallowest ring within 2% of the best measured copy rate
  # makes the second optimization target (available L1) explicit and stable
  # against normal run-to-run noise.
  tuning = []
  for depth, batch_pages in SCALING_CB_CONFIGS:
    candidate = _scaling_images(bh, depth, batch_pages)
    bh.launch_many(candidate, cores=(first_core,), params=first_params)
    timing = _CoreTiming.read(bh, first_core)
    tuning.append((
      depth, batch_pages, candidate,
      _scaling_row(1, [timing], (first_core,)),
    ))
  best_rate = max(row["copy_gb_s"] for _, _, _, row in tuning)
  eligible = [entry for entry in tuning if entry[3]["copy_gb_s"] >= best_rate * 0.98]
  single_depth, single_batch_pages, _, _ = min(
    eligible, key=lambda entry: (entry[0], entry[1]),
  )
  print("\n16 KiB packet CB tuning (one core):")
  for candidate_depth, candidate_batch, _, row in tuning:
    chosen = " <- smallest within 2%" if (
      candidate_depth, candidate_batch) == (
        single_depth, single_batch_pages) else ""
    print(
      f"  depth {candidate_depth:2d}, batch {candidate_batch:2d}, "
      f"L1 {candidate_depth * SCALING_PAGE_BYTES >> 10:4d} KiB: "
      f"{row['copy_gb_s']:5.1f} GB/s copy{chosen}"
    )

  # The best single-core batch can collide reads and writes on the same DRAM
  # bank at card scale. Retune with every worker active before drawing the
  # curve; this also finds the smallest L1 allocation at the saturation point.
  all_cores = available[:max_cores]
  all_params = {
    core: (
      source.address + index * per_bank_stride,
      SCALING_BYTES_PER_CORE,
      result.address + index * per_bank_stride,
    )
    for index, core in enumerate(all_cores)
  }
  card_tuning = []
  for depth, batch_pages, candidate, _ in tuning:
    bh.launch_many(candidate, cores=all_cores, params=all_params)
    timings = [_CoreTiming.read(bh, core) for core in all_cores]
    card_tuning.append((
      depth, batch_pages, candidate,
      _scaling_row(max_cores, timings, all_cores),
    ))
  best_rate = max(row["dram_gb_s"] for _, _, _, row in card_tuning)
  eligible = [entry for entry in card_tuning
              if entry[3]["dram_gb_s"] >= best_rate * 0.98]
  depth, batch_pages, images, _ = min(
    eligible, key=lambda entry: (entry[0], entry[1]),
  )
  print(f"\n16 KiB packet CB tuning ({max_cores} cores):")
  for candidate_depth, candidate_batch, _, row in card_tuning:
    chosen = " <- smallest within 2%" if (
      candidate_depth, candidate_batch) == (depth, batch_pages) else ""
    print(
      f"  depth {candidate_depth:2d}, batch {candidate_batch:2d}, "
      f"L1 {candidate_depth * SCALING_PAGE_BYTES >> 10:4d} KiB: "
      f"{row['dram_gb_s']:5.1f} GB/s DRAM R+W{chosen}"
    )

  rows = []
  for count in counts:
    cores = available[:count]
    params = {
      core: (
        source.address + index * per_bank_stride,
        SCALING_BYTES_PER_CORE,
        result.address + index * per_bank_stride,
      )
      for index, core in enumerate(cores)
    }
    bh.launch_many(images, cores=cores, params=params)
    timings = [_CoreTiming.read(bh, core) for core in cores]
    assert all(item.brisc_end >= item.brisc_start for item in timings)
    assert all(item.ncrisc_end >= item.ncrisc_start for item in timings)
    rows.append(_scaling_row(count, timings, cores))

  _print_scaling_curve(rows, "weak scaling (1 MiB per core)")

  # Strong scaling keeps the tensor approximately fixed while preserving a
  # whole eight-bank round per shard. This is the Llama-like shape where adding
  # cores can expose a slow tail even when weak-scaling bandwidth is healthy.
  bank_round_bytes = 8 * SCALING_PAGE_BYTES
  strong_rows = []
  for count in counts:
    bytes_per_core = (STRONG_SCALING_BYTES // count) // bank_round_bytes
    bytes_per_core *= bank_round_bytes
    cores = available[:count]
    per_bank_stride = bytes_per_core // 8
    params = {
      core: (
        source.address + index * per_bank_stride,
        bytes_per_core,
        result.address + index * per_bank_stride,
      )
      for index, core in enumerate(cores)
    }
    bh.launch_many(images, cores=cores, params=params)
    timings = [_CoreTiming.read(bh, core) for core in cores]
    strong_rows.append(_scaling_row(
      count, timings, cores, bytes_per_core=bytes_per_core,
    ))
  _print_scaling_curve(strong_rows, "strong scaling (~128 MiB total)")

  # The largest weak-scaling launch and the one-core strong-scaling launch
  # jointly cover the allocation; every later launch rewrites a correct prefix.
  # One readback therefore validates every worker path and all eight banks.
  assert bh.read(result) == source_bytes

  # Spread initiators across the three mirrored ports of every DRAM bank.
  # This preserves interleaving and bank balance while removing the single
  # preferred-port hotspot near each controller.
  endpoint_pairs = bh.device.pcie.dram_endpoints[:8]
  split_tuning = []
  for candidate_depth, candidate_batch in SCALING_CB_CONFIGS:
    variants = [
      _movement_images(
        _explicit_dram_port_coordinates(endpoint_pairs, 0, port),
        _explicit_dram_port_coordinates(endpoint_pairs, 1, port),
        candidate_depth, candidate_batch,
      )
      for port in range(3)
    ]
    mapped_images = {
      core: variants[index % 3] for index, core in enumerate(cores)
    }
    bh.launch_many_mapped(mapped_images, params=all_params)
    timings = [_CoreTiming.read(bh, core) for core in cores]
    split_tuning.append((
      candidate_depth, candidate_batch,
      _scaling_row(max_cores, timings, cores),
    ))
  split_best = max(row["dram_gb_s"] for _, _, row in split_tuning)
  split_eligible = [entry for entry in split_tuning
                    if entry[2]["dram_gb_s"] >= split_best * 0.98]
  split_depth, split_batch, _ = min(
    split_eligible, key=lambda entry: (entry[0], entry[1]),
  )

  endpoint_rows = []
  for name, write_delta in (("split3-same", 0), ("split3-staggered", 1)):
    variants = [
      _movement_images(
        _explicit_dram_port_coordinates(endpoint_pairs, 0, port),
        _explicit_dram_port_coordinates(
          endpoint_pairs, 1, (port + write_delta) % 3,
        ),
        split_depth, split_batch,
      )
      for port in range(3)
    ]
    mapped_images = {
      core: variants[index % 3] for index, core in enumerate(cores)
    }
    bh.launch_many_mapped(mapped_images, params=all_params)
    timings = [_CoreTiming.read(bh, core) for core in cores]
    endpoint_rows.append((name, _scaling_row(
      max_cores, timings, cores,
    )))

  # Diagnose controller contention independently of endpoint/router pressure.
  # The source remains ordinarily interleaved, while destination logical bank
  # i is placed at physical bank i+delta. A nonzero delta is a physical-layout
  # permutation rather than a byte-for-byte standard interleaved destination.
  bank_skew_rows = []
  for bank_delta in (1, 2, 4):
    variants = []
    for port in range(3):
      read_coordinates = _explicit_dram_port_coordinates(
        endpoint_pairs, 0, port,
      )
      write_coordinates = _explicit_dram_port_coordinates(
        endpoint_pairs, 1, port,
      )
      variants.append(_movement_images(
        read_coordinates,
        _rotate_bank_coordinates(write_coordinates, bank_delta),
        split_depth, split_batch,
      ))
    mapped_images = {
      core: variants[index % 3] for index, core in enumerate(cores)
    }
    bh.launch_many_mapped(mapped_images, params=all_params)
    timings = [_CoreTiming.read(bh, core) for core in cores]
    bank_skew_rows.append((bank_delta, _scaling_row(
      max_cores, timings, cores,
    )))

  one_way_rows = []
  for read, noc in ((True, 0), (True, 1), (False, 0), (False, 1)):
    direction_tuning = []
    for candidate_depth, candidate_batch in SCALING_CB_CONFIGS:
      variants = [
        _one_way_images(
          _explicit_dram_port_coordinates(
            endpoint_pairs, noc, port,
          ),
          candidate_depth, candidate_batch, read=read, noc=noc,
        )
        for port in range(3)
      ]
      mapped_images = {
        core: variants[index % 3] for index, core in enumerate(cores)
      }
      bh.launch_many_mapped(mapped_images, params=all_params)
      timings = [_CoreTiming.read(bh, core) for core in cores]
      direction_tuning.append((
        candidate_depth, candidate_batch,
        _scaling_row(max_cores, timings, cores),
      ))
    metric = "read_gb_s" if read else "write_gb_s"
    best = max(entry[2][metric] for entry in direction_tuning)
    eligible = [entry for entry in direction_tuning
                if entry[2][metric] >= best * 0.98]
    best_entry = min(eligible, key=lambda entry: (entry[0], entry[1]))
    one_way_rows.append((
      "read" if read else "write", noc, *best_entry,
    ))

  # Give reads and writes physically disjoint controllers. Four banks provide
  # a 256 GB/s directional ceiling, so a balanced copy can still theoretically
  # reach the card's 512 GB/s aggregate limit. Test both DRAM columns and two
  # alternating assignments to separate controller overlap from route layout.
  four_bank_bytes = max_cores * SCALING_BYTES_PER_CORE
  four_bank_source_bytes = _data(four_bank_bytes)
  lower_bank_buffer = bh.interleaved_dram_buffer(
    four_bank_bytes, page_size=SCALING_PAGE_BYTES, banks=4, bank_start=0,
    initial=four_bank_source_bytes,
  )
  upper_bank_buffer = bh.interleaved_dram_buffer(
    four_bank_bytes, page_size=SCALING_PAGE_BYTES, banks=4, bank_start=4,
  )
  four_bank_stride = SCALING_BYTES_PER_CORE // 4
  bank_partitions = (
    ("banks0-3->4-7", LEFT_DRAM_BANKS, MIDDLE_DRAM_BANKS,
     lower_bank_buffer, upper_bank_buffer, True),
    ("banks4-7->0-3", MIDDLE_DRAM_BANKS, LEFT_DRAM_BANKS,
     upper_bank_buffer, lower_bank_buffer, True),
    ("even->odd", (0, 2, 4, 6), (1, 3, 5, 7),
     lower_bank_buffer, upper_bank_buffer, False),
    ("odd->even", (1, 3, 5, 7), (0, 2, 4, 6),
     upper_bank_buffer, lower_bank_buffer, False),
  )
  four_bank_rows = []
  for name, read_banks, write_banks, source_buffer, result_buffer, validate in bank_partitions:
    four_bank_params = {
      core: (
        source_buffer.address + index * four_bank_stride,
        SCALING_BYTES_PER_CORE,
        result_buffer.address + index * four_bank_stride,
      )
      for index, core in enumerate(cores)
    }
    partition_tuning = []
    for candidate_depth, candidate_batch in SCALING_CB_CONFIGS:
      variants = []
      for port in range(3):
        read_pairs = tuple(endpoint_pairs[bank] for bank in read_banks)
        write_pairs = tuple(endpoint_pairs[bank] for bank in write_banks)
        variants.append(_movement_images(
          _explicit_dram_port_coordinates(read_pairs, 0, port),
          _explicit_dram_port_coordinates(write_pairs, 1, port),
          candidate_depth, candidate_batch,
        ))
      mapped_images = {
        core: variants[index % 3] for index, core in enumerate(cores)
      }
      bh.launch_many_mapped(mapped_images, params=four_bank_params)
      timings = [_CoreTiming.read(bh, core) for core in cores]
      partition_tuning.append((
        candidate_depth, candidate_batch,
        _scaling_row(max_cores, timings, cores),
      ))
    best = max(entry[2]["dram_gb_s"] for entry in partition_tuning)
    eligible = [entry for entry in partition_tuning
                if entry[2]["dram_gb_s"] >= best * 0.98]
    chosen = min(eligible, key=lambda entry: (entry[0], entry[1]))
    four_bank_rows.append((name, *chosen))
    if validate:
      # The final tuning launch used the same input/output pair, so the whole
      # selected bank range now contains the copied logical tensor.
      assert bh.read(result_buffer) == four_bank_source_bytes

  # Establish the steady-state baseline before changing VC allocation or
  # priority. Raw allocations are sufficient because payload values do not
  # affect traffic; avoiding host initialization keeps the 936 MiB case cheap.
  long_bytes_per_core = tuple((1 << 20) * scale for scale in (1, 2, 4, 8))
  long_total_bytes = max_cores * max(long_bytes_per_core)
  long_source = bh.device.alloc_interleaved_dram(
    long_total_bytes, page_size=SCALING_PAGE_BYTES, banks=4, bank_start=4,
  )
  long_result = bh.device.alloc_interleaved_dram(
    long_total_bytes, page_size=SCALING_PAGE_BYTES, banks=4, bank_start=0,
  )
  long_variants = [
    _movement_images(
      _explicit_dram_port_coordinates(
        tuple(endpoint_pairs[bank] for bank in MIDDLE_DRAM_BANKS), 0, port,
      ),
      _explicit_dram_port_coordinates(
        tuple(endpoint_pairs[bank] for bank in LEFT_DRAM_BANKS), 1, port,
      ),
      8, 4,
    )
    for port in range(3)
  ]
  long_images = {
    core: long_variants[index % 3] for index, core in enumerate(cores)
  }
  long_rows = []
  for byte_count in long_bytes_per_core:
    stride = byte_count // 4
    params = {
      core: (
        long_source.address + index * stride,
        byte_count,
        long_result.address + index * stride,
      )
      for index, core in enumerate(cores)
    }
    bh.launch_many_mapped(long_images, params=params)
    timings = [_CoreTiming.read(bh, core) for core in cores]
    long_rows.append(_scaling_row(
      max_cores, timings, cores, bytes_per_core=byte_count,
    ))

  # Sweep all legal static VCs plus dynamic allocation on the long steady-state
  # case. NoC0 and NoC1 are independent, so retain the full pair matrix rather
  # than assuming that their best request VCs are identical.
  sweep_bytes = max(long_bytes_per_core)
  sweep_stride = sweep_bytes // 4
  sweep_params = {
    core: (
      long_source.address + index * sweep_stride,
      sweep_bytes,
      long_result.address + index * sweep_stride,
    )
    for index, core in enumerate(cores)
  }
  read_pairs = tuple(endpoint_pairs[bank] for bank in MIDDLE_DRAM_BANKS)
  write_pairs = tuple(endpoint_pairs[bank] for bank in LEFT_DRAM_BANKS)

  def run_control_case(read_vc, write_vc, priorities=None):
    image_cache, mapped_images = {}, {}
    for index, core in enumerate(cores):
      read_priority, write_priority = (
        (0, 0) if priorities is None else priorities[core]
      )
      key = (index % 3, read_priority, write_priority)
      if key not in image_cache:
        port = key[0]
        image_cache[key] = _movement_images(
          _explicit_dram_port_coordinates(read_pairs, 0, port),
          _explicit_dram_port_coordinates(write_pairs, 1, port),
          8, 4, read_vc=read_vc, write_vc=write_vc,
          read_priority=read_priority, write_priority=write_priority,
        )
      mapped_images[core] = image_cache[key]
    bh.launch_many_mapped(mapped_images, params=sweep_params)
    timings = [_CoreTiming.read(bh, core) for core in cores]
    return _scaling_row(
      max_cores, timings, cores, bytes_per_core=sweep_bytes,
    )

  vc_modes = (None, 0, 1, 2, 3, 4, 5)
  vc_rows = {
    (read_vc, write_vc): run_control_case(read_vc, write_vc)
    for read_vc in vc_modes for write_vc in vc_modes
  }
  best_vcs, best_vc_row = max(
    vc_rows.items(), key=lambda item: item[1]["dram_gb_s"],
  )

  uniform_priority_rows = []
  for priority in (0, 1, 2, 4, 8, 15):
    priorities = {core: (priority, priority) for core in cores}
    uniform_priority_rows.append((
      f"uniform-{priority}",
      run_control_case(*best_vcs, priorities=priorities),
    ))

  confirmation_rows = []
  for name, read_vc, write_vc, priority in (
    ("baseline VC1/VC1 p0", 1, 1, 0),
    ("candidate best p0", *best_vcs, 0),
    ("candidate best p15", *best_vcs, 15),
  ):
    priorities = {core: (priority, priority) for core in cores}
    repeats = [
      run_control_case(read_vc, write_vc, priorities=priorities)
      for _ in range(5)
    ]
    rates = tuple(row["dram_gb_s"] for row in repeats)
    tails = tuple(row["max_cycles"] / row["median_cycles"] for row in repeats)
    confirmation_rows.append((name, rates, tails))

  # Do not mix priorities across workers in this saturation kernel. A probe
  # that assigned priority 15 to the slowest quarter and priority 1 to the rest
  # left 114/117 workers unfinished after ten seconds. Priority is a strict
  # contention/fairness mechanism here, not a safe tail-balancing knob.

  # Compare all-to-all interleaving with a DRAM-sharded layout. In the latter,
  # each worker streams through only one bank, eliminating seven of its eight
  # long cross-chip route families while keeping every controller equally busy.
  cores = available[:max_cores]
  slots_per_bank = (max_cores + 7) // 8
  bytes_per_bank = slots_per_bank * SCALING_BYTES_PER_CORE
  bank_source_bytes = _data(bytes_per_bank)
  buffers = []
  bank_images = []
  for bank, endpoint_pair in enumerate(bh.device.pcie.dram_endpoints[:8]):
    bank_source = bh.dram_buffer(
      bytes_per_bank, bank=bank, initial=bank_source_bytes,
    )
    bank_result = bh.dram_buffer(bytes_per_bank, bank=bank)
    buffers.append((bank_source, bank_result))
    bank_images.append(_movement_images(
      (endpoint_pair[0][0] | endpoint_pair[0][1] << 6,),
      (endpoint_pair[1][0] | endpoint_pair[1][1] << 6,),
      depth, batch_pages,
    ))

  sharded_rows = []
  used_slots = None
  for name, localized in (("round-robin", False), ("route-local", True)):
    assignments = _balanced_bank_assignment(
      cores, bh.device.pcie.dram_endpoints[:8], localized=localized,
    )
    row, used_slots = _run_bank_sharded_case(
      bh, cores, assignments, buffers, bank_images,
    )
    sharded_rows.append((name, row))

  print(f"\n{max_cores}-core layout comparison (1 MiB/core):")
  print(f"  interleaved all-to-all: {rows[-1]['dram_gb_s']:.1f} GB/s DRAM R+W")
  print("  split3 CB tuning:")
  for candidate_depth, candidate_batch, row in split_tuning:
    chosen = " <- smallest within 2%" if (
      candidate_depth, candidate_batch) == (split_depth, split_batch) else ""
    print(
      f"    depth {candidate_depth:2d}, batch {candidate_batch:2d}: "
      f"{row['dram_gb_s']:.1f} GB/s{chosen}"
    )
  for name, row in endpoint_rows:
    print(
      f"  interleaved {name:14s}: {row['dram_gb_s']:.1f} GB/s DRAM R+W, "
      f"tail/median {row['max_cycles'] / row['median_cycles']:.3f}"
    )
  for bank_delta, row in bank_skew_rows:
    print(
      f"  split3 destination bank+{bank_delta}: {row['dram_gb_s']:.1f} GB/s "
      f"DRAM R+W, tail/median "
      f"{row['max_cycles'] / row['median_cycles']:.3f}"
    )
  for name, noc, one_way_depth, one_way_batch, row in one_way_rows:
    print(
      f"  split3 {name + '-only NoC' + str(noc):19s}: "
      f"{row[name + '_gb_s']:.1f} GB/s "
      f"(depth {one_way_depth}, batch {one_way_batch}; smallest within 2%)"
    )
  for name, four_depth, four_batch, row in four_bank_rows:
    print(
      f"  disjoint {name:16s}: {row['dram_gb_s']:.1f} GB/s DRAM R+W "
      f"(depth {four_depth}, batch {four_batch}; smallest within 2%), "
      f"tail/median {row['max_cycles'] / row['median_cycles']:.3f}"
    )
  print("  disjoint 4-7->0-3 size sweep (depth 8, batch 4):")
  for row in long_rows:
    print(
      f"    {row['bytes_per_core'] >> 20:2d} MiB/core: "
      f"{row['dram_gb_s']:.1f} GB/s DRAM R+W, tail/median "
      f"{row['max_cycles'] / row['median_cycles']:.3f}"
    )
  print("  8 MiB/core VC matrix, rows=NoC0 read, columns=NoC1 write:")
  vc_labels = tuple("dyn" if vc is None else str(vc) for vc in vc_modes)
  print("          " + " ".join(f"{label:>7s}" for label in vc_labels))
  for read_vc, read_label in zip(vc_modes, vc_labels):
    rates = " ".join(
      f"{vc_rows[read_vc, write_vc]['dram_gb_s']:7.1f}"
      for write_vc in vc_modes
    )
    print(f"    {read_label:>3s}: {rates}")
  print(
    f"    best: read VC {'dyn' if best_vcs[0] is None else best_vcs[0]}, "
    f"write VC {'dyn' if best_vcs[1] is None else best_vcs[1]}: "
    f"{best_vc_row['dram_gb_s']:.1f} GB/s"
  )
  print("  priority sweep at best VC pair:")
  for name, row in uniform_priority_rows:
    print(
      f"    {name:23s}: {row['dram_gb_s']:.1f} GB/s, tail/median "
      f"{row['max_cycles'] / row['median_cycles']:.3f}"
    )
  print("  repeated VC/priority confirmation (five runs):")
  for name, rates, tails in confirmation_rows:
    print(
      f"    {name:23s}: median {median(rates):.1f} GB/s "
      f"[{min(rates):.1f}, {max(rates):.1f}], "
      f"median tail/median {median(tails):.3f}"
    )
  for name, row in sharded_rows:
    print(
      f"  single-bank {name:11s}: {row['dram_gb_s']:.1f} GB/s DRAM R+W, "
      f"tail/median {row['max_cycles'] / row['median_cycles']:.3f}"
    )

  for used, (_, bank_result) in zip(used_slots, buffers):
    result_bytes = bh.read(bank_result)
    assert result_bytes[:used * SCALING_BYTES_PER_CORE] == (
      bank_source_bytes[:used * SCALING_BYTES_PER_CORE]
    )

  # Run the fire-and-forget diagnostic last. Posted writes have no remote ACK,
  # so this interval ends when the NIU has consumed all local L1 sources. For a
  # long saturated stream backpressure makes that a useful injection-rate
  # measurement, but it is intentionally not called a remote-completion time.
  posted_variants = [
    _one_way_images(
      _explicit_dram_port_coordinates(endpoint_pairs, 1, port),
      split_depth, split_batch, read=False, noc=1, posted_write=True,
    )
    for port in range(3)
  ]
  posted_images = {
    core: posted_variants[index % 3] for index, core in enumerate(cores)
  }
  bh.launch_many_mapped(posted_images, params=all_params)
  posted_timings = [_CoreTiming.read(bh, core) for core in cores]
  posted_row = _scaling_row(max_cores, posted_timings, cores)
  print(
    f"  split3 write-only NoC1 posted/local-complete: "
    f"{posted_row['write_gb_s']:.1f} GB/s"
  )
