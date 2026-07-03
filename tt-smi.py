#!/usr/bin/env python3
import argparse
import csv
import curses
import sys
import time
from dataclasses import dataclass, field
from pcie import PCIDevice

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

@dataclass
class TuiState:
  scroll: int = 0
  tick: int = 0
  cur_dev: int = 0
  fan_edit: bool = False
  fan_edit_mode: str = "forced"
  fan_edit_target: int = 50
  fan_mode: dict[int, str] = field(default_factory=dict)
  top_text: str = ""
  top_attr: int = 0
  top_expire: int = 0
  status_text: str = ""
  status_attr: int = 0
  status_expire: int = 0

  def flash_top(self, msg: str, attr: int = 0, ticks: int = 6) -> None:
    self.top_text, self.top_attr, self.top_expire = msg, attr, self.tick + ticks

  def flash(self, msg: str, attr: int = 0, ticks: int = 8) -> None:
    self.status_text, self.status_attr, self.status_expire = msg, attr, self.tick + ticks

  def expire_messages(self) -> None:
    if self.status_expire and self.tick >= self.status_expire:
      self.status_text, self.status_expire = "", 0
    if self.top_expire and self.tick >= self.top_expire:
      self.top_text, self.top_expire = "", 0

METRICS = {
  "ASIC_TEMPERATURE":    ("ASIC temp",       " C",    "s16.16"),
  "AICLK":               ("AICLK",           " MHz",  None),
  "AXICLK":              ("AXICLK",          " MHz",  None),
  "ARCCLK":              ("ARCCLK",          " MHz",  None),
  "AICLK_LIMIT_MAX":     ("AICLK max",       " MHz",  None),
  "GDDR_SPEED":          ("GDDR speed",      " MT/s", None),
  "FAN_SPEED":           ("Fan speed",       " %",    None),
  "FAN_RPM":             ("Fan RPM",         " rpm",  None),
  "TDP":                 ("TDP",             " W",    None),
  "TDP_LIMIT_MAX":       ("TDP max",         " W",    None),
  "TDC":                 ("TDC",             " A",    None),
  "TDC_LIMIT_MAX":       ("TDC max",         " A",    None),
  "VCORE":               ("VCORE",           " mV",   None),
  "BOARD_POWER_LIMIT":   ("Power limit",     " W",    None),
  "THM_LIMIT_THROTTLE":  ("Throttle limit",  " C",    None),
  "THM_LIMIT_SHUTDOWN":  ("Shutdown limit",  " C",    None),
  "MAX_GDDR_TEMP":       ("GDDR temp",       " C",    None),
}

def _fmt_metric(tag_name: str, raw: int) -> str:
  _, unit, decode = METRICS[tag_name]
  if decode == "s16.16":
    return f"{_s16_16(raw):.2f}{unit}"
  return f"{raw & 0xFFFFFFFF}{unit}"

def _csv_metric_value(tag_name: str, raw: int) -> tuple[str, str]:
  _, unit, decode = METRICS[tag_name]
  unit = unit.strip()
  if decode == "s16.16":
    return f"{_s16_16(raw):.2f}", unit
  return str(raw & 0xFFFFFFFF), unit

def _s16_16(raw: int) -> float:
  raw &= 0xFFFFFFFF
  return (raw - (1 << 32) if raw & 0x80000000 else raw) / 65536.0

def _fmt_fw_bundle(raw: int | None) -> str | None:
  if raw is None or raw in (0, 0xFFFFFFFF):
    return None
  raw &= 0xFFFFFFFF
  return ".".join(str((raw >> shift) & 0xFF) for shift in (24, 16, 8, 0))

def _read_tag(dev: PCIDevice, layout: dict, tag_name: str) -> int | None:
  return dev.telemetry_tag(layout, TAG_NAME_TO_ID[tag_name])

# ---- Fan control ----
# TT_SMC_MSG_FORCE_FAN_SPEED (see tt-zephyr-platforms/include/tenstorrent/smc_msg.h).
# arg0 = fan percent (0..100), or 0xFFFFFFFF to revert to the automatic fan curve.
MSG_FORCE_FAN_SPEED = 0xAC
FAN_AUTO_SENTINEL = 0xFFFFFFFF
TUI_REFRESH_S = 0.5

def _set_fan(dev: PCIDevice, pct: int | None) -> None:
  """pct=None → automatic fan curve; 0..100 → forced percent."""
  arg = FAN_AUTO_SENTINEL if pct is None else max(0, min(100, int(pct)))
  dev.arc_msg(MSG_FORCE_FAN_SPEED, arg0=arg)

def _read_sysfs(path: str) -> str | None:
  try:
    with open(path) as f:
      return f.read().strip()
  except OSError:
    return None

def _pcie_link(dev: PCIDevice) -> str | None:
  speed = _read_sysfs(f"{dev.sysfs}/current_link_speed")
  width = _read_sysfs(f"{dev.sysfs}/current_link_width")
  if not speed:
    return None
  return f"{speed} x{width}" if width else speed

def _device_snapshot(dev: PCIDevice) -> dict:
  layout = dev.telemetry_layout()
  tag_cache: dict[str, int | None] = {}
  def tag(name: str) -> int | None:
    if name not in tag_cache:
      tag_cache[name] = _read_tag(dev, layout, name)
    return tag_cache[name]

  board = dev.board_info(layout)
  core_count = board.core_count
  board_name = board.board
  harv_bank = board.harvested_dram_bank

  shutdown = tag("THM_LIMIT_SHUTDOWN")
  throttle = tag("THM_LIMIT_THROTTLE")
  temp_ref = shutdown or throttle or 100
  power_ref = tag("TDP_LIMIT_MAX")
  tdc_ref = tag("TDC_LIMIT_MAX")
  aiclk_ref = tag("AICLK_LIMIT_MAX")

  def asic_temp_value() -> float | None:
    raw = tag("ASIC_TEMPERATURE")
    return None if raw is None else _s16_16(raw)

  def frac(value: float | int | None, ref: float | int | None) -> float | None:
    if value is None or not ref:
      return None
    return float(value) / float(ref)

  fracs = {
    "ASIC_TEMPERATURE": frac(asic_temp_value(), temp_ref),
    "MAX_GDDR_TEMP":    frac(tag("MAX_GDDR_TEMP"), temp_ref),
    "FAN_SPEED":        frac(tag("FAN_SPEED"), 100),
    "TDP":              frac(tag("TDP"), power_ref),
    "TDC":              frac(tag("TDC"), tdc_ref),
    "AICLK":            frac(tag("AICLK"), aiclk_ref),
  }

  def rows(names):
    return [(METRICS[n][0], _fmt_metric(n, raw), fracs.get(n))
            for n in names if (raw := tag(n)) is not None]

  left = rows(["ASIC_TEMPERATURE", "MAX_GDDR_TEMP", "FAN_SPEED", "FAN_RPM", "TDP", "TDC", "VCORE", "BOARD_POWER_LIMIT"])

  right: list[tuple[str, str, float | None]] = []
  if board_name: right.append(("Board", board_name, None))
  if fw_bundle := _fmt_fw_bundle(tag("FLASH_BUNDLE_VERSION")):
    right.append(("FW bundle", fw_bundle, None))
  if link := _pcie_link(dev): right.append(("PCIe link", link, None))
  if core_count is not None: right.append(("Tensix cores", str(core_count), None))
  if harv_bank is not None: right.append(("Harvested DRAM Bank", str(harv_bank), None))
  right += rows(["AICLK", "AXICLK", "ARCCLK", "AICLK_LIMIT_MAX"])

  return {"layout": layout, "left": left, "right": right, "board": board_name, "heartbeat": tag("TIMER_HEARTBEAT")}

CSV_COLUMNS = [
  "device_index",
  "bdf",
  "kind",
  "name",
  "label",
  "value",
  "unit",
  "raw_hex",
  "raw_uint",
]

def _device_csv_rows(index: int, dev: PCIDevice) -> list[dict[str, str]]:
  layout = dev.telemetry_layout()
  board = dev.board_info(layout)
  rows: list[dict[str, str]] = []

  def row(kind: str, name: str, label: str, value: object | None,
          unit: str = "", raw: int | None = None) -> None:
    raw_u32 = None if raw is None else raw & 0xFFFFFFFF
    rows.append({
      "device_index": str(index),
      "bdf": dev.bdf,
      "kind": kind,
      "name": name,
      "label": label,
      "value": "" if value is None else str(value),
      "unit": unit,
      "raw_hex": "" if raw_u32 is None else f"0x{raw_u32:08x}",
      "raw_uint": "" if raw_u32 is None else str(raw_u32),
    })

  row("metadata", "telemetry_table", "Telemetry table", f"0x{layout['table_base']:08x}")
  row("metadata", "telemetry_data", "Telemetry data", f"0x{layout['data_base']:08x}")
  row("metadata", "telemetry_entry_count", "Telemetry entry count", layout["entry_count"])
  row("metadata", "board", "Board", board.board)
  row("metadata", "pcie_link", "PCIe link", _pcie_link(dev))
  row("metadata", "tensix_cores", "Tensix cores", board.core_count)
  row("metadata", "harvested_dram_bank", "Harvested DRAM Bank", board.harvested_dram_bank)

  for tag in sorted(layout["tag_to_offset"]):
    name = TAG_ID_TO_NAME.get(tag, f"TAG_{tag}")
    raw = dev.telemetry_tag(layout, tag)
    label = METRICS[name][0] if name in METRICS else name
    if name in METRICS:
      value, unit = _csv_metric_value(name, raw)
    elif name == "FLASH_BUNDLE_VERSION":
      value, unit = _fmt_fw_bundle(raw) or "", ""
    else:
      value, unit = str(raw & 0xFFFFFFFF), ""
    row("telemetry", name, label, value, unit, raw)

  return rows

def write_csv(indices: list[int]) -> None:
  writer = csv.DictWriter(sys.stdout, fieldnames=CSV_COLUMNS, lineterminator="\n")
  writer.writeheader()
  for index in indices:
    with PCIDevice(index=index, use_vfio=False) as dev:
      writer.writerows(_device_csv_rows(index, dev))

def show_device(index: int):
  with PCIDevice(index=index, use_vfio=False) as dev:
    snap = _device_snapshot(dev)
    layout = snap["layout"]
    print(f"◆ Device {index}: {dev.bdf}")
    print(f"  Telemetry table            0x{layout['table_base']:08x}")
    print(f"  Telemetry data             0x{layout['data_base']:08x}")
    print(f"  Telemetry entry count      {layout['entry_count']}")
    for section, rows in [("Thermals / Power", snap["left"]), ("Clocks / Status", snap["right"])]:
      print(f"  ─── {section} ───")
      for label, value, _ in rows:
        print(f"  {label:<20} {value}")
    print("  Raw telemetry")
    for tag in sorted(layout["tag_to_offset"]):
      name = TAG_ID_TO_NAME.get(tag, f"TAG_{tag}")
      print(f"    {tag:>2} {name:<24} 0x{dev.telemetry_tag(layout, tag):08x}")

def reset_device(index: int):
  devices = PCIDevice.list_devices()
  if index >= len(devices):
    raise RuntimeError(f"Blackhole device {index} not found (found {len(devices)})")
  bdf = devices[index].split('/')[-1]
  print(f"Resetting device {index} ({bdf}) ...")
  PCIDevice.reset_index(index)
  # Post-reset init: open device to send ARC A0 + watchdog (same as tt-kmd's init_hardware)
  with PCIDevice(index=index, use_vfio=False) as dev:
    print(f"  ARC ready, telemetry base 0x{dev.read_arc_apb32(dev.SCRATCH_RAM_12):08x}")
  print(f"Reset complete.")

def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Standalone Blackhole telemetry and reset tool")
  parser.add_argument("-r", "--reset", type=int, metavar="DEVICE", nargs="?", const=0, default=None,
                      help="reset a Blackhole device (default: device 0)")
  parser.add_argument("--csv", type=int, metavar="DEVICE", nargs="?", const=-1, default=None,
                      help="print a one-shot CSV report, optionally for one device")
  parser.add_argument("--snapshot", dest="csv", type=int, metavar="DEVICE", nargs="?", const=-1,
                      help=argparse.SUPPRESS)
  return parser.parse_args()

# Row type: (label, value, frac_or_None). A line is a list of (text, attr) segments.
Segment = tuple[str, int]
Line = list[Segment]

def _bar(frac: float, width: int) -> str:
  if width <= 0:
    return ""
  frac = max(0.0, min(1.0, frac))
  cells = max(1, (width + 1) // 2)
  filled = round(frac * cells)
  return " ".join("▮" if i < filled else "·" for i in range(cells))[:width].ljust(width)

def _render_tui(stdscr, devices: list[tuple[int, PCIDevice]]):
  curses.curs_set(0)
  curses.use_default_colors()
  stdscr.nodelay(True)
  stdscr.timeout(int(TUI_REFRESH_S * 1000))

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

  state = TuiState()

  def seg_len(segs: Line) -> int:
    return sum(len(t) for t, _ in segs)

  def pad_segs(segs: Line, width: int) -> Line:
    n = seg_len(segs)
    if n < width:
      return [*segs, (" " * (width - n), 0)]
    out: Line = []
    for text, attr in segs:
      if width <= 0:
        break
      out.append((text[:width], attr))
      width -= len(text)
    return out

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
    lw = max(8, min(20, max((len(l) for l, *_ in rows), default=8)))
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

  def merge_cols(left: list[Line], right: list[Line]) -> list[Line]:
    lw = max((seg_len(line) for line in left), default=0)
    rw = max((seg_len(line) for line in right), default=0)
    return [pad_segs(left[i] if i < len(left) else [], lw) + [(" ", 0)] +
            pad_segs(right[i] if i < len(right) else [], rw)
            for i in range(max(len(left), len(right)))]

  def render_card(index: int, dev: PCIDevice, width: int, dev_slot: int = 0,
                  editing: bool = False, target: int = 50) -> list[Line]:
    snap = _device_snapshot(dev)
    cw = max(40, width - 2)
    alive = snap["heartbeat"] is not None
    dot_attr = cpair(C_GREEN if alive else C_RED) | curses.A_BOLD
    dot = "●" if (state.tick % 2 == 0 or not alive) else "○"
    left_rows = snap["left"]
    if editing:
      left_rows = [
        (lbl, f"▶ {target}% ◀", target / 100.0) if lbl == "Fan speed" else (lbl, val, frac)
        for (lbl, val, frac) in left_rows
      ]
    elif mode := state.fan_mode.get(dev_slot):
      left_rows = [
        (lbl, f"{val} [{mode}]", frac) if lbl == "Fan speed" else (lbl, val, frac)
        for (lbl, val, frac) in left_rows
      ]
    pager = f"  ◀ {state.cur_dev + 1}/{len(devices)} ▶" if len(devices) > 1 else ""
    title_text = f"  Blackhole {index}  {snap['board'] or ''}  {dev.bdf}{pager}  "
    header: Line = [
      (title_text[:cw - 2], cpair(C_CYAN) | curses.A_BOLD),
      (dot, dot_attr),
    ]
    lines: list[Line] = [header]
    col_w = (cw - 1) // 2
    pad = max(len(left_rows), len(snap["right"]))
    left_box = kv_box(col_w, "Thermals / Power", left_rows, pad, show_bars=True)
    right_box = kv_box(cw - 1 - col_w, "Clocks / Status", snap["right"], pad)
    lines.extend(merge_cols(left_box, right_box))
    return lines

  def render_fan_modal(width: int, height: int, preferred_y: int) -> tuple[int, int, list[Line]]:
    dev_idx = devices[state.cur_dev][0]
    w = max(28, min(width - 2, 46))
    inner = max(4, w - 4)
    mode = state.fan_edit_mode
    badge = f"[{mode.upper()}]"
    bar = _bar(state.fan_edit_target / 100.0, inner - 2)
    title = f"Fan · dev {dev_idx}" if w < 38 else f"Fan control · dev {dev_idx}"
    if w < 38:
      rows = [
        [(" ", 0), (f"{state.fan_edit_target:>3}% ", curses.A_BOLD), (badge, cpair(C_CYAN) | curses.A_BOLD)],
        [(" ", 0), (bar, bar_attr(state.fan_edit_target / 100.0))],
        [(" ←/→ ±5    +/- ±1", curses.A_DIM)],
        [(" 0-9 tens  Tab mode", curses.A_DIM)],
        [(" Enter apply  Esc cancel", curses.A_DIM)],
      ]
    else:
      auto = "(*) Auto" if mode == "auto" else "( ) Auto"
      forced = "(*) Forced" if mode == "forced" else "( ) Forced"
      rows = [
        [(" Target  ", 0), (f"{state.fan_edit_target:>3}%", curses.A_BOLD), ("  ", 0), (badge, cpair(C_CYAN) | curses.A_BOLD)],
        [(" ", 0), (bar, bar_attr(state.fan_edit_target / 100.0))],
        [(" Mode    ", 0), (f"{auto}   {forced}", 0)],
        [(" ←/→ ±5    +/- ±1    0-9 set tens", curses.A_DIM)],
        [(" Tab/A toggle mode    Enter apply", curses.A_DIM)],
        [(" Esc cancel", curses.A_DIM)],
      ]
    lines = [box_top(w, title), *[box_row(w, row) for row in rows], box_bot(w)]
    centered_y = max(0, (height - len(lines)) // 2)
    y = preferred_y if preferred_y + len(lines) < height else centered_y
    return max(0, y), max(0, (width - w) // 2), lines

  while True:
    state.tick += 1
    height, width = stdscr.getmaxyx()
    state.expire_messages()

    hints = "    q quit  ·  f fan" + ("  ·  ←/→ device" if len(devices) > 1 else "")
    lines: list[Line] = []
    header_line: Line = [
      (" tt-smi  ", cpair(C_MAGENTA) | curses.A_BOLD),
      (time.strftime("%Y-%m-%d %H:%M:%S"), 0),
      (hints, curses.A_DIM),
    ]
    if state.top_text:
      header_line += [("  ·  ", curses.A_DIM), (state.top_text, state.top_attr)]
    lines.append(header_line)
    lines.append([("", 0)])

    card_w = max(40, width - 1)
    index, dev = devices[state.cur_dev]
    try:
      lines.extend(render_card(index, dev, card_w, dev_slot=state.cur_dev,
                               editing=state.fan_edit, target=state.fan_edit_target))
    except Exception as exc:
      lines.append([(f"  Blackhole {index}: {dev.bdf}", curses.A_BOLD)])
      lines.append([(f"  could not read telemetry: {exc}", cpair(C_RED) | curses.A_BOLD)])
    modal_y = len(lines) - state.scroll + 1
    lines.append([("", 0)])

    visible = max(1, height - 1)
    max_scroll = max(0, len(lines) - visible)
    state.scroll = min(state.scroll, max_scroll)

    stdscr.erase()
    for ri, segs in enumerate(lines[state.scroll:state.scroll + visible]):
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
    if state.status_text:
      try:
        stdscr.addnstr(height - 1, 1, state.status_text[:width - 2], width - 2, state.status_attr)
      except curses.error:
        pass
    elif max_scroll:
      footer = f" {state.scroll}/{max_scroll} "
      try:
        stdscr.addnstr(height - 1, max(0, width - len(footer) - 1), footer, len(footer), curses.A_DIM)
      except curses.error:
        pass
    if state.fan_edit:
      y0, x0, modal = render_fan_modal(width, height, preferred_y=max(2, modal_y))
      for yi, segs in enumerate(modal):
        x = x0
        for text, attr in segs:
          if x >= width - 1:
            break
          try:
            stdscr.addnstr(y0 + yi, x, text, max(1, width - 1 - x), attr)
          except curses.error:
            pass
          x += len(text)
    stdscr.refresh()

    key = stdscr.getch()
    if key == -1: continue

    if state.fan_edit:
      if key in (27, ord("q"), ord("Q"), ord("f"), ord("F")):
        state.fan_edit = False
        state.flash("fan edit cancelled", curses.A_DIM)
      elif key in (10, 13, curses.KEY_ENTER):
        _, tgt = devices[state.cur_dev]
        try:
          _set_fan(tgt, None if state.fan_edit_mode == "auto" else state.fan_edit_target)
          if state.fan_edit_mode == "auto":
            state.fan_mode[state.cur_dev] = "auto"
            msg = f"fan mode auto  [dev {devices[state.cur_dev][0]}]"
          else:
            state.fan_mode[state.cur_dev] = "forced"
            msg = f"fan forced to {state.fan_edit_target}%  [dev {devices[state.cur_dev][0]}]"
          state.flash(msg, cpair(C_GREEN) | curses.A_BOLD)
        except Exception as exc:
          state.flash(f"fan set failed: {exc}", cpair(C_RED) | curses.A_BOLD, ticks=16)
        state.fan_edit = False
      elif key in (9, ord(" "), ord("a"), ord("A")):
        state.fan_edit_mode = "forced" if state.fan_edit_mode == "auto" else "auto"
      elif key == curses.KEY_LEFT:
        state.fan_edit_mode = "forced"; state.fan_edit_target = max(0, state.fan_edit_target - 5)
      elif key == curses.KEY_RIGHT:
        state.fan_edit_mode = "forced"; state.fan_edit_target = min(100, state.fan_edit_target + 5)
      elif key in (ord("-"), ord("_")):
        state.fan_edit_mode = "forced"; state.fan_edit_target = max(0, state.fan_edit_target - 1)
      elif key in (ord("+"), ord("=")):
        state.fan_edit_mode = "forced"; state.fan_edit_target = min(100, state.fan_edit_target + 1)
      elif ord("0") <= key <= ord("9"):
        state.fan_edit_mode = "forced"; state.fan_edit_target = (key - ord("0")) * 10
      continue

    if key in (ord("q"), ord("Q")): return
    if key in (ord("f"), ord("F")):
      # Seed the target from the current FAN_SPEED reading so ±5 is relative to "now".
      try:
        _, tgt = devices[state.cur_dev]
        cur = _read_tag(tgt, tgt.telemetry_layout(), "FAN_SPEED")
        if cur is not None:
          cur &= 0xFFFFFFFF
          if 0 <= cur <= 100:
            state.fan_edit_target = cur
      except Exception:
        pass
      state.fan_edit_mode = state.fan_mode.get(state.cur_dev, "forced")
      state.fan_edit = True
      continue
    if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
      if len(devices) <= 1:
        state.flash_top("only one Tenstorrent device", cpair(C_YELLOW) | curses.A_BOLD)
      elif key == curses.KEY_LEFT and state.cur_dev > 0:
        state.cur_dev -= 1; state.scroll = 0
      elif key == curses.KEY_RIGHT and state.cur_dev < len(devices) - 1:
        state.cur_dev += 1; state.scroll = 0
      else:
        state.flash_top("end of device list", cpair(C_YELLOW) | curses.A_BOLD)
      continue
    scroll_map = {curses.KEY_UP: -1, curses.KEY_DOWN: 1,
                  curses.KEY_PPAGE: -visible, curses.KEY_NPAGE: visible}
    if key in scroll_map:
      state.scroll = max(0, min(max_scroll, state.scroll + scroll_map[key]))
    elif key == curses.KEY_HOME: state.scroll = 0
    elif key == curses.KEY_END: state.scroll = max_scroll

def _run_tui(indices: list[int]):
  devices = []
  try:
    for index in indices:
      devices.append((index, PCIDevice(index=index, use_vfio=False)))
    try:
      curses.wrapper(_render_tui, devices)
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

  indices = [args.csv] if isinstance(args.csv, int) and args.csv >= 0 else list(range(len(devices)))
  if args.csv is not None or not sys.stdout.isatty() or not sys.stdin.isatty():
    write_csv(indices)
  else:
    _run_tui(indices)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    pass
