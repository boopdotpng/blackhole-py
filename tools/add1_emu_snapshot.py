#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TTSIM_ROOT = ROOT.parent / "ttsim"
DEBUG_LIB = TTSIM_ROOT / "src" / "_out" / "debug_bh" / "libttsim.so"
OUT_DIR = Path("/tmp/add1_emu_snapshots")

os.environ.setdefault("EMU", "1")
os.environ.setdefault("TT_USB", "1")
sys.path.insert(0, str(ROOT))

import emu_pcie  # noqa: E402

emu_pcie._default_lib_path = lambda: str(DEBUG_LIB)

from device import Device  # noqa: E402
from examples import add1  # noqa: E402
from pcie import TLBWindow  # noqa: E402
from program import Dtype  # noqa: E402
from ttk.addrs import CircularBuffer as CB, Mailbox, TensixL1  # noqa: E402

TILE_SIZE = 1_678_464
RV32_SIZE = 312
RV32_OFF = 8
RV32_PC_OFF = 12
RV32_XREG_OFF = 16
TENSIX_OFF = 1_568
TENSIX_SIZE = 61_492
TENSIX_ACTIVE_OFF = 4
TENSIX_INST_RD_PTR_OFF = 6_152
TENSIX_INST_WR_PTR_OFF = 6_164
TENSIX_SEM_OFF = 6_708
TENSIX_SEM_MAX_OFF = 6_716
TENSIX_DMA_REGS_OFF = 6_724
TENSIX_SRC_A_VALID_OFF = 57_668
TENSIX_SRC_B_VALID_OFF = 57_680
TENSIX_SRC_A_RWC_OFF = 57_708
TENSIX_SRC_B_RWC_OFF = 57_732
TENSIX_DST_RWC_OFF = 57_756
TENSIX_PACKER_DST_ADDR_OFF = 61_056
TENSIX_PACKER_DST_ADDR_VALID_OFF = 61_088
SRAM_OFF = 63_060
SRAM_SIZE = 1_572_864
LOCAL_RAM_OFF = 1_635_924
LOCAL_RAM_SIZE = 8_192
SOFT_RESET_OFF = 1_678_356
TRISC0_RESET_PC_OFF = 1_678_360

REGION_BOUNDS = [
  ("rv32", RV32_OFF, TENSIX_OFF),
  ("tensix", TENSIX_OFF, SRAM_OFF),
  ("sram", SRAM_OFF, LOCAL_RAM_OFF),
  ("local_ram", LOCAL_RAM_OFF, LOCAL_RAM_OFF + 5 * LOCAL_RAM_SIZE),
  ("tile_regs", LOCAL_RAM_OFF + 5 * LOCAL_RAM_SIZE, TILE_SIZE),
]

HART_NAMES = ["brisc", "trisc0", "trisc1", "trisc2", "ncrisc"]


def u32(buf: bytes, off: int) -> int:
  return struct.unpack_from("<I", buf, off)[0]


def u32s(buf: bytes, off: int, count: int) -> list[int]:
  return list(struct.unpack_from("<" + "I" * count, buf, off))


def hex32(value: int) -> str:
  return f"0x{value:08x}"


def coord_to_ttsim_tile(core: tuple[int, int]) -> int:
  x, y = core
  if 1 <= x <= 7:
    tile_x = x - 1
  elif 10 <= x <= 16:
    tile_x = x - 3
  else:
    raise ValueError(f"not a BH Tensix x coord: {core}")
  if not 2 <= y <= 11:
    raise ValueError(f"not a BH Tensix y coord: {core}")
  return tile_x + (y - 2) * 14


def lib_base(path: Path) -> int:
  path = path.resolve()
  best = None
  with open("/proc/self/maps") as f:
    for line in f:
      if str(path) not in line:
        continue
      cols = line.split()
      start_s, _end_s = cols[0].split("-")
      file_off = int(cols[2], 16)
      base = int(start_s, 16) - file_off
      best = base if best is None else min(best, base)
  if best is None:
    raise RuntimeError(f"{path} not found in /proc/self/maps")
  return best


def local_symbol(path: Path, name: str) -> int:
  out = subprocess.check_output(["nm", str(path)], text=True)
  for line in out.splitlines():
    cols = line.split()
    if len(cols) >= 3 and cols[2] == name:
      return int(cols[0], 16)
  raise RuntimeError(f"symbol {name} not found in {path}")


def tile_bytes(tile_id: int) -> bytes:
  base = lib_base(DEBUG_LIB) + local_symbol(DEBUG_LIB, "g_t_tiles")
  return ctypes.string_at(base + tile_id * TILE_SIZE, TILE_SIZE)


def local_words(raw: bytes, hart: int, off: int, count: int) -> list[str]:
  base = LOCAL_RAM_OFF + hart * LOCAL_RAM_SIZE + off
  return [hex32(v) for v in u32s(raw, base, count)]


def snapshot_l1(dev: Device, core: tuple[int, int]) -> dict:
  words = {}
  addrs = [
    TensixL1.GO_MSG,
    TensixL1.GO_MSG_INDEX,
    Mailbox.SUBORDINATE_SYNC,
    Mailbox.LAUNCH_MSG_RD_PTR,
    add1.SYNC_OUT_RESERVED,
    add1.SYNC_READ,
    add1.SYNC_DONE0,
    add1.SYNC_DONE1,
    add1.SYNC_DONE2,
    add1.SYNC_TRISC_INIT,
    add1.SYNC_TRISC_INIT + 4,
    add1.SYNC_TRISC_INIT + 8,
    add1.SYNC_TENSIX_INIT_ONCE,
    add1.SYNC_TENSIX_INIT_ONCE + 4,
    add1.SYNC_TENSIX_INIT_ONCE + 8,
  ]
  for cb in (0, add1.OUT_CB):
    addrs.append((CB.SYNC_TILES_ACKED_BASE + cb * CB.SYNC_STRIDE) & 0x1FFFFF)
    addrs.append((CB.SYNC_TILES_RECEIVED_BASE + cb * CB.SYNC_STRIDE) & 0x1FFFFF)
  with TLBWindow(dev.dev, start=core) as win:
    for addr in addrs:
      words[f"l1[{addr:#x}]"] = hex32(win.read32(addr))
  return words


def decode_snapshot(label: str, dev: Device, core: tuple[int, int], tile_id: int) -> dict:
  raw = tile_bytes(tile_id)
  harts = {}
  active = u32(raw, 0)
  for i, name in enumerate(HART_NAMES):
    off = RV32_OFF + i * RV32_SIZE
    harts[name] = {
      "active": bool(active & (1 << i)),
      "pc": hex32(u32(raw, off + RV32_PC_OFF)),
      "x": [hex32(x) for x in u32s(raw, off + RV32_XREG_OFF, 32)],
    }
  t = TENSIX_OFF
  tensix = {
    "inst_pipes_active": hex32(u32(raw, t + TENSIX_ACTIVE_OFF)),
    "inst_rd_ptr": [hex32(v) for v in u32s(raw, t + TENSIX_INST_RD_PTR_OFF, 3)],
    "inst_wr_ptr": [hex32(v) for v in u32s(raw, t + TENSIX_INST_WR_PTR_OFF, 3)],
    "sem": list(raw[t + TENSIX_SEM_OFF:t + TENSIX_SEM_OFF + 8]),
    "sem_max": list(raw[t + TENSIX_SEM_MAX_OFF:t + TENSIX_SEM_MAX_OFF + 8]),
    "dma_regs": [[hex32(v) for v in u32s(raw, t + TENSIX_DMA_REGS_OFF + pipe * 64 * 4, 64)] for pipe in range(3)],
    "src_a_valid": hex32(u32(raw, t + TENSIX_SRC_A_VALID_OFF)),
    "src_b_valid": hex32(u32(raw, t + TENSIX_SRC_B_VALID_OFF)),
    "src_a_rwc": [hex32(v) for v in u32s(raw, t + TENSIX_SRC_A_RWC_OFF, 3)],
    "src_b_rwc": [hex32(v) for v in u32s(raw, t + TENSIX_SRC_B_RWC_OFF, 3)],
    "dst_rwc": [hex32(v) for v in u32s(raw, t + TENSIX_DST_RWC_OFF, 3)],
    "packer_dst_addr": [hex32(v) for v in u32s(raw, t + TENSIX_PACKER_DST_ADDR_OFF, 4)],
    "packer_dst_addr_valid": bool(raw[t + TENSIX_PACKER_DST_ADDR_VALID_OFF]),
  }
  local = {
    "brisc_cb0": local_words(raw, 0, 0x48, 8),
    "ncrisc_cb16": local_words(raw, 4, 0x464 + add1.OUT_CB * 32, 8),
    "trisc0_common": local_words(raw, 1, 0, 8),
    "trisc1_data": local_words(raw, 2, 0x20, 8),
    "trisc2_pack": local_words(raw, 3, 0x820, 8),
  }
  raw_hash = hashlib.sha256(raw).hexdigest()
  return {
    "label": label,
    "core": core,
    "tile_id": tile_id,
    "raw_sha256": raw_hash,
    "raw": raw,
    "l1": snapshot_l1(dev, core),
    "rv32_active": hex32(active),
    "harts": harts,
    "tensix": tensix,
    "local_ram": local,
    "tile_regs": {
      "soft_reset_0": hex32(u32(raw, SOFT_RESET_OFF)),
      "trisc0_reset_pc": hex32(u32(raw, TRISC0_RESET_PC_OFF)),
      "trisc1_reset_pc": hex32(u32(raw, TRISC0_RESET_PC_OFF + 4)),
      "trisc2_reset_pc": hex32(u32(raw, TRISC0_RESET_PC_OFF + 8)),
      "ncrisc_reset_pc": hex32(u32(raw, TRISC0_RESET_PC_OFF + 16)),
    },
  }


def strip_raw(snap: dict) -> dict:
  return {k: v for k, v in snap.items() if k != "raw"}


def flatten(obj, prefix=""):
  if isinstance(obj, dict):
    for k, v in obj.items():
      yield from flatten(v, f"{prefix}.{k}" if prefix else str(k))
  elif isinstance(obj, list):
    for i, v in enumerate(obj):
      yield from flatten(v, f"{prefix}[{i}]")
  else:
    yield prefix, obj


def structured_diff(a: dict, b: dict) -> list[tuple[str, object, object]]:
  af = dict(flatten(strip_raw(a)))
  bf = dict(flatten(strip_raw(b)))
  rows = []
  for key in sorted(set(af) | set(bf)):
    if af.get(key) != bf.get(key):
      rows.append((key, af.get(key), bf.get(key)))
  return rows


def raw_region_diff(a: bytes, b: bytes) -> dict:
  out = {}
  for name, start, end in REGION_BOUNDS:
    changed = []
    for off in range(start, end, 4):
      av = a[off:off + 4]
      bv = b[off:off + 4]
      if av != bv:
        changed.append((off, int.from_bytes(av, "little"), int.from_bytes(bv, "little")))
    out[name] = {
      "changed_words": len(changed),
      "first_32": [(hex(off), hex32(av), hex32(bv)) for off, av, bv in changed[:32]],
    }
  return out


def save_snapshot(snap: dict):
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  (OUT_DIR / f"{snap['label']}.json").write_text(json.dumps(strip_raw(snap), indent=2) + "\n")


def run_one(dev: Device, i: int):
  n = add1.TILES_PER_CORE
  src = add1._seed_src_tensor(n)
  src_buf = dev.alloc_write(src, dtype=Dtype.Float16_b, shape=(n, 32, 32), name=f"src{i}")
  dst_buf = dev.dram.alloc(n, dtype=Dtype.Float16_b, shape=(n, 32, 32), name=f"dst{i}")
  timings = dev.run(add1.build_program(src_buf.addr, dst_buf.addr, len(dev.dram.bank_tiles)))
  mismatch = add1._first_mismatch(dev.dram_read(dst_buf), add1._expected_add1(src))
  if mismatch is not None:
    raise AssertionError(f"iter {i} mismatch at byte {mismatch}")
  return timings


def main() -> int:
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  core = add1.TARGET_CORE
  tile_id = coord_to_ttsim_tile(core)
  snaps = []
  print(f"using {DEBUG_LIB}")
  print(f"snapshot dir: {OUT_DIR}")
  print(f"target core {core} -> ttsim tile {tile_id}")
  dev = Device()
  try:
    snap = decode_snapshot("00_after_emu_reset", dev, core, tile_id)
    snaps.append(snap)
    save_snapshot(snap)
    print("snap 00_after_emu_reset")
    for i in range(1, 8):
      try:
        timings = run_one(dev, i)
        print(f"iter {i} PASS {[round(t['us'], 1) for t in timings]}")
        label = f"{i:02d}_after_iter_{i}"
        snap = decode_snapshot(label, dev, core, tile_id)
        snaps.append(snap)
        save_snapshot(snap)
        print(f"snap {label}")
      except Exception as exc:
        print(f"iter {i} FAIL {type(exc).__name__}: {exc}")
        traceback.print_exc()
        label = f"{i:02d}_hang_iter_{i}"
        snap = decode_snapshot(label, dev, core, tile_id)
        snaps.append(snap)
        save_snapshot(snap)
        print(f"snap {label}")
        break
  finally:
    dev.close()

  if len(snaps) >= 2:
    for a, b in zip(snaps, snaps[1:]):
      stem = f"diff_{a['label']}__{b['label']}"
      rows = structured_diff(a, b)
      raw = raw_region_diff(a["raw"], b["raw"])
      report = {
        "from": a["label"],
        "to": b["label"],
        "structured_changed_count": len(rows),
        "structured_first_200": rows[:200],
        "raw_region_diff": raw,
      }
      (OUT_DIR / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n")
      print(f"\n{stem}")
      print(f"  structured changes: {len(rows)}")
      for key, av, bv in rows[:80]:
        print(f"  {key}: {av} -> {bv}")
      print("  raw changed words:")
      for name, info in raw.items():
        print(f"    {name}: {info['changed_words']}")

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
