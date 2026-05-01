#!/usr/bin/env python3
import argparse
import curses
import struct
import sys
import time

from hw import Arc, Dram, active_tensix_core_count
from pcie import PCIDevice, TLB_2M_SIZE


# ---- ARC telemetry ----

def _read_arc_noc32(dev: PCIDevice, addr: int, tlb: int) -> int:
  base = addr & ~(TLB_2M_SIZE - 1)
  dev.configure_tlb(tlb, base, *dev.ARC_TILE, *dev.ARC_TILE, ordering=1)
  bar, bar_off = dev.tlb_window(tlb)
  return struct.unpack_from("<I", bar, bar_off + (addr - base))[0]

def telemetry_layout(dev: PCIDevice) -> dict:
  table_base = dev.read_arc_apb32(dev.SCRATCH_RAM_13)
  data_base = dev.read_arc_apb32(dev.SCRATCH_RAM_12)
  if table_base in (0, 0xFFFFFFFF) or data_base in (0, 0xFFFFFFFF):
    raise RuntimeError(f"invalid ARC telemetry pointers table=0x{table_base:x} data=0x{data_base:x}")
  tlb = dev.alloc_tlb(TLB_2M_SIZE)
  try:
    version = _read_arc_noc32(dev, table_base, tlb)
    entry_count = _read_arc_noc32(dev, table_base + 4, tlb)
    tag_to_offset = {}
    for i in range(entry_count):
      tag_offset = _read_arc_noc32(dev, table_base + 8 + i * 4, tlb)
      tag_to_offset[tag_offset & 0xFFFF] = (tag_offset >> 16) & 0xFFFF
  finally:
    dev.free_tlb(tlb)
  return {"version": version, "table_base": table_base, "data_base": data_base,
          "entry_count": entry_count, "tag_to_offset": tag_to_offset}

def read_telemetry_entry(dev: PCIDevice, layout: dict, tag: int) -> int:
  tlb = dev.alloc_tlb(TLB_2M_SIZE)
  try:
    return _read_arc_noc32(dev, layout["data_base"] + 4 * layout["tag_to_offset"][tag], tlb)
  finally:
    dev.free_tlb(tlb)


TAG_NAME_TO_ID = {
  "BOARD_ID_HIGH": 1, "BOARD_ID_LOW": 2, "ASIC_ID": 3, "HARVESTING_STATE": 4,
  "UPDATE_TELEM_SPEED": 5, "VCORE": 6, "TDP": 7, "TDC": 8, "VDD_LIMITS": 9,
  "THM_LIMIT_SHUTDOWN": 10, "ASIC_TEMPERATURE": 11, "VREG_TEMPERATURE": 12,
  "BOARD_TEMPERATURE": 13, "AICLK": 14, "AXICLK": 15, "ARCCLK": 16,
  "L2CPUCLK0": 17, "L2CPUCLK1": 18, "L2CPUCLK2": 19, "L2CPUCLK3": 20,
  "ETH_LIVE_STATUS": 21, "GDDR_STATUS": 22, "GDDR_SPEED": 23,
  "ETH_FW_VERSION": 24, "GDDR_FW_VERSION": 25, "DM_APP_FW_VERSION": 26,
  "DM_BL_FW_VERSION": 27, "FLASH_BUNDLE_VERSION": 28, "CM_FW_VERSION": 29,
  "L2CPU_FW_VERSION": 30, "FAN_SPEED": 31, "TIMER_HEARTBEAT": 32,
  "ENABLED_TENSIX_COL": 34, "ENABLED_ETH": 35, "ENABLED_GDDR": 36,
  "ENABLED_L2CPU": 37, "PCIE_USAGE": 38, "NOC_TRANSLATION": 40, "FAN_RPM": 41,
  "GDDR_0_1_TEMP": 42, "GDDR_2_3_TEMP": 43, "GDDR_4_5_TEMP": 44, "GDDR_6_7_TEMP": 45,
  "GDDR_0_1_CORR_ERRS": 46, "GDDR_2_3_CORR_ERRS": 47,
  "GDDR_4_5_CORR_ERRS": 48, "GDDR_6_7_CORR_ERRS": 49,
  "GDDR_UNCORR_ERRS": 50, "MAX_GDDR_TEMP": 51, "ASIC_LOCATION": 52,
  "BOARD_POWER_LIMIT": 53, "TDC_LIMIT_MAX": 55, "THM_LIMIT_THROTTLE": 56,
  "TT_FLASH_VERSION": 58, "THERM_TRIP_COUNT": 60, "ASIC_ID_HIGH": 61,
  "ASIC_ID_LOW": 62, "AICLK_LIMIT_MAX": 63, "TDP_LIMIT_MAX": 64,
}
TAG_ID_TO_NAME = {tag: name for name, tag in TAG_NAME_TO_ID.items()}

BOARD_UPI_TO_NAME = {
  0x36: "p100", 0x43: "p100", 0x40: "p150", 0x41: "p150", 0x42: "p150",
  0x44: "p300", 0x45: "p300", 0x46: "p300", 0x18: "n150", 0x14: "n300",
  0x35: "ubb", 0x47: "ubb_blackhole",
}

# Metric definitions: (tag_name, label, unit, decode)
# decode: "s16.16" = signed fixed-point, "hex" = hex display, None = raw integer
METRICS = {
  "ASIC_TEMPERATURE":    ("ASIC temp",          " C",    "s16.16"),
  "AICLK":               ("AICLK",              " MHz",  None),
  "AXICLK":              ("AXICLK",             " MHz",  None),
  "ARCCLK":              ("ARCCLK",             " MHz",  None),
  "AICLK_LIMIT_MAX":     ("AICLK max",          " MHz",  None),
  "GDDR_SPEED":          ("GDDR speed",         " MT/s", None),
  "FAN_SPEED":           ("Fan speed",          " %",    None),
  "FAN_RPM":             ("Fan RPM",            " rpm",  None),
  "TDP":                 ("TDP",                " W",    None),
  "TDP_LIMIT_MAX":       ("TDP max",            " W",    None),
  "TDC":                 ("TDC",                " A",    None),
  "TDC_LIMIT_MAX":       ("TDC max",            " A",    None),
  "VCORE":               ("VCORE",              " mV",   None),
  "BOARD_POWER_LIMIT":   ("Power limit",        " W",    None),
  "THM_LIMIT_THROTTLE":  ("Throttle limit",     " C",    None),
  "THM_LIMIT_SHUTDOWN":  ("Shutdown limit",     " C",    None),
  "MAX_GDDR_TEMP":       ("GDDR temp",          " C",    None),
}


def _fmt_metric(tag_name: str, raw: int) -> str:
  label, unit, decode = METRICS[tag_name]
  if decode == "s16.16":
    raw &= 0xFFFFFFFF
    val = (raw - (1 << 32) if raw & 0x80000000 else raw) / 65536.0
    return f"{val:.2f}{unit}"
  if decode == "hex":
    return f"0x{raw:08x}"
  return f"{raw & 0xFFFFFFFF}{unit}"


def _read_tag(dev: PCIDevice, layout: dict, tag_name: str) -> int | None:
  tag = TAG_NAME_TO_ID[tag_name]
  if tag not in layout["tag_to_offset"]:
    return None
  return read_telemetry_entry(dev, layout, tag)


# ---- Fan control ----
# TT_SMC_MSG_FORCE_FAN_SPEED (see tt-zephyr-platforms/include/tenstorrent/smc_msg.h).
# arg0 = fan percent (0..100), or 0xFFFFFFFF to revert to the automatic fan curve.
MSG_FORCE_FAN_SPEED = 0xAC
FAN_AUTO_SENTINEL = 0xFFFFFFFF

def _set_fan(dev: PCIDevice, pct: int | None) -> None:
  """pct=None → automatic fan curve; 0..100 → forced percent."""
  arg = FAN_AUTO_SENTINEL if pct is None else max(0, min(100, int(pct)))
  dev.arc_msg(MSG_FORCE_FAN_SPEED, arg0=arg)


def _read_metric_row(dev: PCIDevice, layout: dict, tag_name: str) -> tuple[str, str] | None:
  raw = _read_tag(dev, layout, tag_name)
  if raw is None:
    return None
  return (METRICS[tag_name][0], _fmt_metric(tag_name, raw))


def _format_ranges(values: list[int]) -> str:
  if not values:
    return "none"
  ranges, start, prev = [], values[0], values[0]
  for v in values[1:]:
    if v == prev + 1:
      prev = v
    else:
      ranges.append(f"{start}-{prev}" if start != prev else str(start))
      start = prev = v
  ranges.append(f"{start}-{prev}" if start != prev else str(start))
  return ",".join(ranges)


def _device_snapshot(dev: PCIDevice) -> dict:
  layout = telemetry_layout(dev)
  bid_hi, bid_lo = _read_tag(dev, layout, "BOARD_ID_HIGH"), _read_tag(dev, layout, "BOARD_ID_LOW")
  board_id = ((bid_hi & 0xFFFFFFFF) << 32 | (bid_lo & 0xFFFFFFFF)) if bid_hi is not None and bid_lo is not None else None
  tensix_en = _read_tag(dev, layout, "ENABLED_TENSIX_COL")
  gddr_en = _read_tag(dev, layout, "ENABLED_GDDR")
  core_count = None if tensix_en is None else active_tensix_core_count(tensix_en & Arc.DEFAULT_TENSIX_ENABLED)
  board_name = BOARD_UPI_TO_NAME.get((board_id >> 36) & 0xFFFFF) if board_id is not None else None

  harv_banks = [b for b in range(Dram.BANK_COUNT) if gddr_en and not (gddr_en >> b) & 1] if gddr_en else []

  # Denominators for progress bars
  shutdown = _read_tag(dev, layout, "THM_LIMIT_SHUTDOWN")
  throttle = _read_tag(dev, layout, "THM_LIMIT_THROTTLE")
  temp_ref = shutdown or throttle or 100
  power_ref = _read_tag(dev, layout, "BOARD_POWER_LIMIT") or _read_tag(dev, layout, "TDP_LIMIT_MAX")
  tdc_ref = _read_tag(dev, layout, "TDC_LIMIT_MAX")
  aiclk_ref = _read_tag(dev, layout, "AICLK_LIMIT_MAX")

  def asic_temp_value() -> float | None:
    r = _read_tag(dev, layout, "ASIC_TEMPERATURE")
    if r is None:
      return None
    r &= 0xFFFFFFFF
    return (r - (1 << 32) if r & 0x80000000 else r) / 65536.0

  def frac(value: float | int | None, ref: float | int | None) -> float | None:
    if value is None or not ref:
      return None
    return float(value) / float(ref)

  fracs = {
    "ASIC_TEMPERATURE": frac(asic_temp_value(), temp_ref),
    "MAX_GDDR_TEMP":    frac(_read_tag(dev, layout, "MAX_GDDR_TEMP"), temp_ref),
    "FAN_SPEED":        frac(_read_tag(dev, layout, "FAN_SPEED"), 100),
    "TDP":              frac(_read_tag(dev, layout, "TDP"), power_ref),
    "TDC":              frac(_read_tag(dev, layout, "TDC"), tdc_ref),
    "AICLK":            frac(_read_tag(dev, layout, "AICLK"), aiclk_ref),
  }

  def rows(names):
    out = []
    for name in names:
      r = _read_metric_row(dev, layout, name)
      if r is None:
        continue
      out.append((r[0], r[1], fracs.get(name)))
    return out

  left = rows(["ASIC_TEMPERATURE", "MAX_GDDR_TEMP", "FAN_SPEED", "FAN_RPM", "TDP", "TDC", "VCORE", "BOARD_POWER_LIMIT"])

  right: list[tuple[str, str, float | None]] = []
  if board_name: right.append(("Board", board_name, None))
  if core_count is not None: right.append(("Tensix cores", str(core_count), None))
  if harv_banks: right.append(("Harvested DRAM", _format_ranges(harv_banks), None))
  right += rows(["AICLK", "AXICLK", "ARCCLK", "AICLK_LIMIT_MAX", "GDDR_SPEED"])

  return {"layout": layout, "summary_left": left, "summary_right": right,
          "board_name": board_name,
          "heartbeat": _read_tag(dev, layout, "TIMER_HEARTBEAT")}


def show_device(index: int):
  with PCIDevice(index=index) as dev:
    snap = _device_snapshot(dev)
    layout = snap["layout"]
    print(f"◆ Device {index}: {dev.bdf}")
    print(f"  Telemetry table            0x{layout['table_base']:08x}")
    print(f"  Telemetry data             0x{layout['data_base']:08x}")
    print(f"  Telemetry entry count      {layout['entry_count']}")
    for section, rows in [("Thermals / Power", snap["summary_left"]), ("Clocks / Status", snap["summary_right"])]:
      print(f"  ─── {section} ───")
      for label, value, _ in rows:
        print(f"  {label:<20} {value}")
    # raw dump
    print("  Raw telemetry")
    for tag in sorted(layout["tag_to_offset"]):
      name = TAG_ID_TO_NAME.get(tag, f"TAG_{tag}")
      print(f"    {tag:>2} {name:<24} 0x{read_telemetry_entry(dev, layout, tag):08x}")


def reset_device(index: int):
  devices = PCIDevice.list_devices()
  if index >= len(devices):
    raise RuntimeError(f"Blackhole device {index} not found (found {len(devices)})")
  bdf = devices[index].split('/')[-1]
  print(f"Resetting device {index} ({bdf}) ...")
  PCIDevice.reset_index(index)
  # Post-reset init: open device to send ARC A0 + watchdog (same as tt-kmd's init_hardware)
  with PCIDevice(index=index) as dev:
    print(f"  ARC ready, telemetry base 0x{dev.read_arc_apb32(dev.SCRATCH_RAM_12):08x}")
  print(f"Reset complete.")


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Standalone Blackhole telemetry and reset tool")
  parser.add_argument("-r", "--reset", type=int, metavar="DEVICE", nargs="?", const=0, default=None,
                      help="reset a Blackhole device (default: device 0)")
  parser.add_argument("-d", "--device", type=int, metavar="DEVICE", help="show telemetry for one device only")
  parser.add_argument("--plain", action="store_true", help="disable the curses UI and print a one-shot snapshot")
  parser.add_argument("--interval", type=float, default=0.5, help="refresh interval in seconds for the TUI")
  return parser.parse_args()


# ---- TUI ----

# Row type: (label, value, frac_or_None). A line is a list of (text, attr) segments.
Segment = tuple[str, int]
Line = list[Segment]

_BAR_BLOCKS = " ▏▎▍▌▋▊▉"  # empty + seven partial eighths; full block is handled separately

def _bar(frac: float, width: int) -> str:
  if width <= 0:
    return ""
  frac = max(0.0, min(1.0, frac))
  eighths = int(round(frac * width * 8))
  full, rem = divmod(eighths, 8)
  out = "█" * min(full, width)
  if full < width:
    out += _BAR_BLOCKS[rem]
    out = out.ljust(width)
  return out[:width]


def _render_tui(stdscr, devices: list[tuple[int, PCIDevice]], interval_s: float):
  curses.curs_set(0)
  curses.use_default_colors()
  stdscr.nodelay(True)
  stdscr.timeout(max(50, int(interval_s * 1000)))

  C_CYAN, C_GREEN, C_YELLOW, C_MAGENTA, C_RED = 1, 2, 3, 4, 5
  if curses.has_colors():
    curses.start_color()
    for i, color in enumerate([curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_YELLOW,
                               curses.COLOR_MAGENTA, curses.COLOR_RED], 1):
      curses.init_pair(i, color, -1)

  def cpair(n): return curses.color_pair(n) if curses.has_colors() else 0
  BORDER = curses.A_DIM
  def bar_attr(frac: float) -> int:
    return cpair(C_RED if frac >= 0.85 else C_YELLOW if frac >= 0.60 else C_GREEN)

  scroll, tick = 0, 0
  cur_dev = 0          # index into `devices` of the device currently on screen
  fan_edit = False     # are we in fan-edit mode?
  fan_edit_target = 50 # pending fan percent (preserved across edits)
  # Per-device fan mode, populated only after *we* send a successful arc_msg.
  # The SMC doesn't expose fan_speed_forced, so we can't know on startup — an
  # entry is absent (=unknown) until the user sets it within this session.
  fan_mode: dict[int, str] = {}  # cur_dev index -> "auto"
  status_text = ""     # transient message shown on the bottom line
  status_attr = 0
  status_expire = 0    # tick after which status_text is cleared

  def flash(msg: str, attr: int = 0, ticks: int = 8) -> None:
    nonlocal status_text, status_attr, status_expire
    status_text, status_attr, status_expire = msg, attr, tick + ticks

  def seg_len(segs: Line) -> int:
    return sum(len(t) for t, _ in segs)

  def pad_segs(segs: Line, width: int) -> Line:
    n = seg_len(segs)
    if n < width:
      return [*segs, (" " * (width - n), 0)]
    if n > width:
      out: Line = []
      remaining = width
      for t, a in segs:
        if remaining <= 0:
          break
        if len(t) <= remaining:
          out.append((t, a)); remaining -= len(t)
        else:
          out.append((t[:remaining], a)); remaining = 0
      return out
    return list(segs)

  def box_top(width: int, title: str) -> Line:
    inner = max(4, width - 2)
    label = f" {title} " if title else ""
    bar = "─" * max(0, inner - len(label))
    return [("╭", BORDER), (label, curses.A_BOLD), (bar, BORDER), ("╮", BORDER)]

  def box_bot(width: int) -> Line:
    inner = max(4, width - 2)
    return [("╰" + "─" * inner + "╯", BORDER)]

  def box_row(width: int, segs: Line) -> Line:
    inner = max(4, width - 2)
    return [("│", BORDER), *pad_segs(segs, inner), ("│", BORDER)]

  def kv_box(width: int, title: str, rows: list[tuple[str, str, float | None]],
             min_rows: int = 0, show_bars: bool = False) -> list[Line]:
    inner = max(4, width - 4)  # minus borders + one space each side
    lw = max(8, min(18, max((len(l) for l, *_ in rows), default=8)))
    vw = max(6, min(12, max((len(v) for _, v, *_ in rows), default=6)))
    bw = max(0, inner - lw - vw - 3) if show_bars else 0
    lines: list[Line] = [box_top(width, title)]
    for label, value, frac in rows:
      segs: Line = [
        (" ", 0),
        (f"{label[:lw]:<{lw}}", 0),
        (" ", 0),
        (f"{value[:vw]:>{vw}}", curses.A_BOLD),
        (" ", 0),
      ]
      if show_bars and bw >= 3:
        if frac is not None:
          segs.append((_bar(frac, bw - 1), bar_attr(frac)))
          segs.append((" ", 0))
        else:
          segs.append((" " * bw, 0))
      lines.append(box_row(width, segs))
    while len(lines) - 1 < min_rows:
      lines.append(box_row(width, [(" ", 0)]))
    lines.append(box_bot(width))
    return lines

  def merge_cols(left: list[Line], right: list[Line], total_w: int) -> list[Line]:
    lw = max(20, (total_w - 1) // 2)
    rw = max(20, total_w - 1 - lw)
    h = max(len(left), len(right))
    out: list[Line] = []
    for i in range(h):
      l = left[i] if i < len(left) else []
      r = right[i] if i < len(right) else []
      out.append(pad_segs(l, lw) + [(" ", 0)] + pad_segs(r, rw))
    return out

  def render_card(index: int, dev: PCIDevice, width: int, dev_slot: int = 0,
                  editing: bool = False, target: int = 50) -> list[Line]:
    snap = _device_snapshot(dev)
    cw = max(40, width - 2)
    alive = snap["heartbeat"] is not None
    dot_attr = cpair(C_GREEN if alive else C_RED) | curses.A_BOLD
    # Subtle blink every 2 ticks so it's visible but not noisy
    dot = "●" if (tick % 2 == 0 or not alive) else "○"
    # While editing, overwrite the Fan speed row so the user sees the pending target.
    # Otherwise, if *we* last set this device to auto, annotate the row with "auto".
    if editing:
      snap["summary_left"] = [
        (lbl, f"▶ {target}% ◀", target / 100.0) if lbl == "Fan speed" else (lbl, val, frac)
        for (lbl, val, frac) in snap["summary_left"]
      ]
    elif fan_mode.get(dev_slot) == "auto":
      snap["summary_left"] = [
        (lbl, f"{val} auto", frac) if lbl == "Fan speed" else (lbl, val, frac)
        for (lbl, val, frac) in snap["summary_left"]
      ]
    # "◀ 1/3 ▶" pagination indicator only shows when we actually have siblings.
    pager = f"  ◀ {cur_dev + 1}/{len(devices)} ▶" if len(devices) > 1 else ""
    title_text = f"  Device {index}"
    if snap.get("board_name"):
      title_text += f"  {snap['board_name']}"
    title_text += f"  {dev.bdf}{pager}  "
    header: Line = [
      (title_text[:cw - 2], cpair(C_CYAN) | curses.A_BOLD),
      (dot, dot_attr),
    ]
    lines: list[Line] = [header]
    col_w = cw // 2
    pad = max(len(snap["summary_left"]), len(snap["summary_right"]))
    left_box = kv_box(col_w, "Thermals / Power", snap["summary_left"], pad, show_bars=True)
    right_box = kv_box(cw - col_w, "Clocks / Status", snap["summary_right"], pad)
    lines.extend(merge_cols(left_box, right_box, cw))
    return lines

  while True:
    tick += 1
    height, width = stdscr.getmaxyx()

    if status_expire and tick >= status_expire:
      status_text, status_expire = "", 0

    hints = "    q:quit  f:fan" + ("  ←/→:device" if len(devices) > 1 else "")
    lines: list[Line] = []
    header_line: Line = [
      (" tt-smi  ", cpair(C_CYAN) | curses.A_BOLD),
      (time.strftime("%Y-%m-%d %H:%M:%S"), 0),
      (hints, curses.A_DIM),
    ]
    lines.append(header_line)
    lines.append([("", 0)])

    # Single-device view: render only the currently-selected card.
    card_w = max(40, width - 1)
    index, dev = devices[cur_dev]
    try:
      lines.extend(render_card(index, dev, card_w, dev_slot=cur_dev,
                               editing=fan_edit, target=fan_edit_target))
    except Exception as exc:
      lines.append([(f"  Device {index}: {dev.bdf}", curses.A_BOLD)])
      lines.append([(f"  error: {exc}", cpair(C_RED) | curses.A_BOLD)])
    lines.append([("", 0)])

    visible = max(1, height - 1)
    max_scroll = max(0, len(lines) - visible)
    scroll = min(scroll, max_scroll)

    stdscr.erase()
    for ri, segs in enumerate(lines[scroll:scroll + visible]):
      x = 0
      for text, attr in segs:
        if x >= width - 1:
          break
        if not text:
          continue
        try:
          stdscr.addnstr(ri, x, text, max(1, width - 1 - x), attr)
        except curses.error:
          pass
        x += len(text)
    # Bottom line: fan-edit prompt > transient status > scroll indicator.
    if fan_edit:
      tgt_idx = devices[cur_dev][0]
      footer = (f" FAN EDIT  dev {tgt_idx}  target: {fan_edit_target:>3}%   "
                f"←/→ ±5   S-←/S-→ ±1   a:auto   Enter:apply   Esc:cancel ")
      try:
        stdscr.addnstr(height - 1, 0, footer[:width - 1], width - 1,
                       cpair(C_CYAN) | curses.A_BOLD | curses.A_REVERSE)
      except curses.error:
        pass
    elif status_text:
      try:
        stdscr.addnstr(height - 1, 1, status_text[:width - 2], width - 2, status_attr)
      except curses.error:
        pass
    elif max_scroll:
      footer = f" {scroll}/{max_scroll} "
      try:
        stdscr.addnstr(height - 1, max(0, width - len(footer) - 1), footer, len(footer), curses.A_DIM)
      except curses.error:
        pass
    stdscr.refresh()

    key = stdscr.getch()
    if key == -1: continue

    if fan_edit:
      # In edit mode, arrow keys retarget to fan adjustment (no scrolling).
      if key == 27:  # Esc
        fan_edit = False
        flash("fan edit cancelled", curses.A_DIM)
      elif key in (10, 13, curses.KEY_ENTER):
        _, tgt = devices[cur_dev]
        try:
          _set_fan(tgt, fan_edit_target)
          fan_mode.pop(cur_dev, None)  # no longer auto; we don't label "forced"
          flash(f"fan → {fan_edit_target}%  [dev {devices[cur_dev][0]}]",
                cpair(C_GREEN) | curses.A_BOLD)
        except Exception as exc:
          flash(f"fan set failed: {exc}", cpair(C_RED) | curses.A_BOLD, ticks=16)
        fan_edit = False
      elif key in (ord("a"), ord("A")):
        _, tgt = devices[cur_dev]
        try:
          _set_fan(tgt, None)
          fan_mode[cur_dev] = "auto"
          flash(f"fan → auto  [dev {devices[cur_dev][0]}]", cpair(C_GREEN) | curses.A_BOLD)
        except Exception as exc:
          flash(f"fan auto failed: {exc}", cpair(C_RED) | curses.A_BOLD, ticks=16)
        fan_edit = False
      elif key == curses.KEY_LEFT:  fan_edit_target = max(0,   fan_edit_target - 5)
      elif key == curses.KEY_RIGHT: fan_edit_target = min(100, fan_edit_target + 5)
      elif key == curses.KEY_SLEFT: fan_edit_target = max(0,   fan_edit_target - 1)
      elif key == curses.KEY_SRIGHT:fan_edit_target = min(100, fan_edit_target + 1)
      elif key in (ord("-"), ord("_")): fan_edit_target = max(0,   fan_edit_target - 1)
      elif key in (ord("+"), ord("=")): fan_edit_target = min(100, fan_edit_target + 1)
      continue

    if key in (ord("q"), ord("Q")): return
    if key in (ord("f"), ord("F")):
      # Seed the target from the current FAN_SPEED reading so ±5 is relative to "now".
      try:
        _, tgt = devices[cur_dev]
        cur = _read_tag(tgt, telemetry_layout(tgt), "FAN_SPEED")
        if cur is not None:
          cur &= 0xFFFFFFFF
          if 0 <= cur <= 100:
            fan_edit_target = cur
      except Exception:
        pass
      fan_edit = True
      continue
    # Left/Right flip between devices; when there's only one, they're no-ops.
    if key == curses.KEY_LEFT and len(devices) > 1:
      cur_dev = (cur_dev - 1) % len(devices); scroll = 0; continue
    if key == curses.KEY_RIGHT and len(devices) > 1:
      cur_dev = (cur_dev + 1) % len(devices); scroll = 0; continue
    scroll_map = {curses.KEY_UP: -1, curses.KEY_DOWN: 1,
                  curses.KEY_PPAGE: -visible, curses.KEY_NPAGE: visible}
    if key in scroll_map:
      scroll = max(0, min(max_scroll, scroll + scroll_map[key]))
    elif key == curses.KEY_HOME: scroll = 0
    elif key == curses.KEY_END: scroll = max_scroll


def _run_tui(indices: list[int], interval_s: float):
  devices = []
  try:
    for index in indices:
      devices.append((index, PCIDevice(index=index)))
    try:
      curses.wrapper(_render_tui, devices, interval_s)
    except KeyboardInterrupt:
      pass
  finally:
    for _, dev in devices:
      try: dev.close()
      except Exception: pass


def main():
  args = parse_args()
  if args.reset is not None:
    reset_device(args.reset)
    return

  devices = PCIDevice.list_devices()
  if not devices:
    raise SystemExit("no Blackhole PCIe devices found")

  indices = [args.device] if args.device is not None else list(range(len(devices)))
  if args.plain or not sys.stdout.isatty() or not sys.stdin.isatty():
    for i, index in enumerate(indices):
      if i: print()
      show_device(index)
  else:
    _run_tui(indices, args.interval)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    pass
