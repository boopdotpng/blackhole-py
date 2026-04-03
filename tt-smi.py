#!/usr/bin/env python3
import argparse
import curses
import sys
import time
from typing import Callable

from hw import Arc, Dram, active_tensix_core_count
from pcie import PCIDevice


TAG_NAME_TO_ID = {
  "BOARD_ID_HIGH": 1,
  "BOARD_ID_LOW": 2,
  "ASIC_ID": 3,
  "HARVESTING_STATE": 4,
  "UPDATE_TELEM_SPEED": 5,
  "VCORE": 6,
  "TDP": 7,
  "TDC": 8,
  "VDD_LIMITS": 9,
  "THM_LIMIT_SHUTDOWN": 10,
  "ASIC_TEMPERATURE": 11,
  "VREG_TEMPERATURE": 12,
  "BOARD_TEMPERATURE": 13,
  "AICLK": 14,
  "AXICLK": 15,
  "ARCCLK": 16,
  "L2CPUCLK0": 17,
  "L2CPUCLK1": 18,
  "L2CPUCLK2": 19,
  "L2CPUCLK3": 20,
  "ETH_LIVE_STATUS": 21,
  "GDDR_STATUS": 22,
  "GDDR_SPEED": 23,
  "ETH_FW_VERSION": 24,
  "GDDR_FW_VERSION": 25,
  "DM_APP_FW_VERSION": 26,
  "DM_BL_FW_VERSION": 27,
  "FLASH_BUNDLE_VERSION": 28,
  "CM_FW_VERSION": 29,
  "L2CPU_FW_VERSION": 30,
  "FAN_SPEED": 31,
  "TIMER_HEARTBEAT": 32,
  "ENABLED_TENSIX_COL": 34,
  "ENABLED_ETH": 35,
  "ENABLED_GDDR": 36,
  "ENABLED_L2CPU": 37,
  "PCIE_USAGE": 38,
  "NOC_TRANSLATION": 40,
  "FAN_RPM": 41,
  "GDDR_0_1_TEMP": 42,
  "GDDR_2_3_TEMP": 43,
  "GDDR_4_5_TEMP": 44,
  "GDDR_6_7_TEMP": 45,
  "GDDR_0_1_CORR_ERRS": 46,
  "GDDR_2_3_CORR_ERRS": 47,
  "GDDR_4_5_CORR_ERRS": 48,
  "GDDR_6_7_CORR_ERRS": 49,
  "GDDR_UNCORR_ERRS": 50,
  "MAX_GDDR_TEMP": 51,
  "ASIC_LOCATION": 52,
  "BOARD_POWER_LIMIT": 53,
  "TDC_LIMIT_MAX": 55,
  "THM_LIMIT_THROTTLE": 56,
  "TT_FLASH_VERSION": 58,
  "THERM_TRIP_COUNT": 60,
  "ASIC_ID_HIGH": 61,
  "ASIC_ID_LOW": 62,
  "AICLK_LIMIT_MAX": 63,
  "TDP_LIMIT_MAX": 64,
}
TAG_ID_TO_NAME = {tag: name for name, tag in TAG_NAME_TO_ID.items()}
BOARD_UPI_TO_NAME = {
  0x36: "p100",
  0x43: "p100",
  0x40: "p150",
  0x41: "p150",
  0x42: "p150",
  0x44: "p300",
  0x45: "p300",
  0x46: "p300",
  0x18: "n150",
  0x14: "n300",
  0x35: "ubb",
  0x47: "ubb_blackhole",
}


def _s16_16(raw: int) -> float:
  raw &= 0xFFFFFFFF
  if raw & 0x80000000:
    raw -= 1 << 32
  return raw / 65536.0


def _u16_16(raw: int) -> float:
  return (raw & 0xFFFFFFFF) / 65536.0


def _identity(raw: int) -> int:
  return raw & 0xFFFFFFFF


class Metric:
  def __init__(self, tag_name: str, label: str, unit: str = "", decode: Callable[[int], object] = _identity, hex_value: bool = False):
    self.tag_name = tag_name
    self.tag = TAG_NAME_TO_ID[tag_name]
    self.label = label
    self.unit = unit
    self.decode = decode
    self.hex_value = hex_value

  def format(self, raw: int) -> str:
    value = self.decode(raw)
    if self.hex_value:
      return f"0x{raw:08x}"
    if isinstance(value, float):
      return f"{value:.2f}{self.unit}"
    return f"{value}{self.unit}"


SUMMARY_METRICS = [
  Metric("ASIC_TEMPERATURE", "ASIC temperature", " C", _s16_16),
  Metric("VREG_TEMPERATURE", "VREG temperature", " C", _s16_16),
  Metric("BOARD_TEMPERATURE", "Board temperature", " C", _s16_16),
  Metric("AICLK", "AICLK", " MHz"),
  Metric("AXICLK", "AXICLK", " MHz"),
  Metric("ARCCLK", "ARCCLK", " MHz"),
  Metric("AICLK_LIMIT_MAX", "AICLK max", " MHz"),
  Metric("GDDR_SPEED", "GDDR speed", " MT/s"),
  Metric("FAN_SPEED", "Fan speed", " %"),
  Metric("FAN_RPM", "Fan RPM", " rpm"),
  Metric("TDP", "TDP", " W"),
  Metric("TDP_LIMIT_MAX", "TDP max", " W"),
  Metric("TDC", "TDC", " A"),
  Metric("TDC_LIMIT_MAX", "TDC max", " A"),
  Metric("VCORE", "VCORE", " mV"),
  Metric("BOARD_POWER_LIMIT", "Board power limit", " W"),
  Metric("THM_LIMIT_THROTTLE", "Thermal throttle limit", " C"),
  Metric("THM_LIMIT_SHUTDOWN", "Thermal shutdown limit", " C"),
  Metric("MAX_GDDR_TEMP", "Max GDDR temperature", " C"),
]

DETAIL_METRICS = [
  Metric("BOARD_ID_HIGH", "Board ID high", hex_value=True),
  Metric("BOARD_ID_LOW", "Board ID low", hex_value=True),
  Metric("ASIC_ID", "ASIC ID", hex_value=True),
  Metric("ASIC_ID_HIGH", "ASIC ID high", hex_value=True),
  Metric("ASIC_ID_LOW", "ASIC ID low", hex_value=True),
  Metric("ASIC_LOCATION", "ASIC location"),
  Metric("HARVESTING_STATE", "Harvesting state", hex_value=True),
  Metric("UPDATE_TELEM_SPEED", "Telemetry update speed"),
  Metric("VDD_LIMITS", "VDD limits", hex_value=True),
  Metric("ETH_LIVE_STATUS", "ETH live status", hex_value=True),
  Metric("GDDR_STATUS", "GDDR status", hex_value=True),
  Metric("ETH_FW_VERSION", "ETH FW version", hex_value=True),
  Metric("GDDR_FW_VERSION", "GDDR FW version", hex_value=True),
  Metric("DM_APP_FW_VERSION", "DM app FW version", hex_value=True),
  Metric("DM_BL_FW_VERSION", "DM bootloader FW version", hex_value=True),
  Metric("FLASH_BUNDLE_VERSION", "Flash bundle version", hex_value=True),
  Metric("CM_FW_VERSION", "CM FW version", hex_value=True),
  Metric("L2CPU_FW_VERSION", "L2CPU FW version", hex_value=True),
  Metric("TT_FLASH_VERSION", "TT flash version", hex_value=True),
  Metric("TIMER_HEARTBEAT", "Telemetry heartbeat"),
  Metric("ENABLED_TENSIX_COL", "Enabled Tensix columns", hex_value=True),
  Metric("ENABLED_ETH", "Enabled ETH", hex_value=True),
  Metric("ENABLED_GDDR", "Enabled GDDR", hex_value=True),
  Metric("ENABLED_L2CPU", "Enabled L2CPU", hex_value=True),
  Metric("PCIE_USAGE", "PCIe usage", hex_value=True),
  Metric("NOC_TRANSLATION", "NOC translation", hex_value=True),
  Metric("GDDR_0_1_CORR_ERRS", "GDDR 0/1 corrected errors", hex_value=True),
  Metric("GDDR_2_3_CORR_ERRS", "GDDR 2/3 corrected errors", hex_value=True),
  Metric("GDDR_4_5_CORR_ERRS", "GDDR 4/5 corrected errors", hex_value=True),
  Metric("GDDR_6_7_CORR_ERRS", "GDDR 6/7 corrected errors", hex_value=True),
  Metric("GDDR_UNCORR_ERRS", "GDDR uncorrected errors", hex_value=True),
  Metric("THERM_TRIP_COUNT", "Thermal trip count"),
]
METRICS_BY_NAME = {metric.tag_name: metric for metric in SUMMARY_METRICS + DETAIL_METRICS}


def _format_metric(metric: Metric, raw: int) -> str:
  return metric.format(raw)


def _read_tag_value(dev: PCIDevice, tag_name: str) -> int | None:
  tag = TAG_NAME_TO_ID[tag_name]
  if not dev.has_telemetry_tag(tag):
    return None
  return dev.read_telemetry_entry(tag)


def _read_metric_row(dev: PCIDevice, metric: Metric) -> tuple[str, str] | None:
  if not dev.has_telemetry_tag(metric.tag):
    return None
  return (metric.label, _format_metric(metric, dev.read_telemetry_entry(metric.tag)))


def _read_metric_row_by_name(dev: PCIDevice, tag_name: str) -> tuple[str, str] | None:
  return _read_metric_row(dev, METRICS_BY_NAME[tag_name])


def _combine_u64(high: int | None, low: int | None) -> int | None:
  if high is None or low is None:
    return None
  return ((high & 0xFFFFFFFF) << 32) | (low & 0xFFFFFFFF)


def _format_u64(value: int | None) -> str | None:
  if value is None:
    return None
  return f"0x{value:016x}"


def _format_ranges(values: list[int]) -> str:
  if not values:
    return "none"
  ranges = []
  start = prev = values[0]
  for value in values[1:]:
    if value == prev + 1:
      prev = value
      continue
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    start = prev = value
  ranges.append(f"{start}-{prev}" if start != prev else str(start))
  return ",".join(ranges)


def _decode_board_name(board_id: int | None) -> str | None:
  if board_id is None:
    return None
  upi = (board_id >> 36) & 0xFFFFF
  board_name = BOARD_UPI_TO_NAME.get(upi)
  if board_name is None:
    return None
  return board_name


def _decode_gddr_mask(mask: int | None) -> tuple[list[int], list[int]]:
  if mask is None:
    return [], []
  enabled = [bank for bank in range(Dram.BANK_COUNT) if ((mask >> bank) & 1) != 0]
  harvested = [bank for bank in range(Dram.BANK_COUNT) if ((mask >> bank) & 1) == 0]
  return enabled, harvested


def _format_harvested_dram_bank(harvested_banks: list[int]) -> str:
  return _format_ranges(harvested_banks)


def _decode_gddr_modules(dev: PCIDevice) -> list[dict]:
  gddr_temp_tags = [TAG_NAME_TO_ID[f"GDDR_{pair}_TEMP"] for pair in ("0_1", "2_3", "4_5", "6_7")]
  gddr_corr_tags = [TAG_NAME_TO_ID[f"GDDR_{pair}_CORR_ERRS"] for pair in ("0_1", "2_3", "4_5", "6_7")]
  has_gddr = all(dev.has_telemetry_tag(tag) for tag in gddr_temp_tags + gddr_corr_tags + [TAG_NAME_TO_ID["GDDR_UNCORR_ERRS"]])
  if not has_gddr:
    return []

  modules = []
  uncorr = dev.read_telemetry_entry(TAG_NAME_TO_ID["GDDR_UNCORR_ERRS"])
  for pair_index in range(4):
    temp_word = dev.read_telemetry_entry(gddr_temp_tags[pair_index])
    corr_word = dev.read_telemetry_entry(gddr_corr_tags[pair_index])
    for lane in range(2):
      module = pair_index * 2 + lane
      shift = 16 if lane else 0
      modules.append({
        "module": module,
        "top": (temp_word >> (shift + 8)) & 0xFF,
        "bottom": (temp_word >> shift) & 0xFF,
        "corr_rd": (corr_word >> shift) & 0xFF,
        "corr_wr": (corr_word >> (shift + 8)) & 0xFF,
        "uncorr_rd": 1 if (uncorr & (1 << (module * 2))) else 0,
        "uncorr_wr": 1 if (uncorr & (1 << (module * 2 + 1))) else 0,
      })
  return modules


def _device_snapshot(dev: PCIDevice) -> dict:
  layout = dev.telemetry_layout()
  board_id = _combine_u64(_read_tag_value(dev, "BOARD_ID_HIGH"), _read_tag_value(dev, "BOARD_ID_LOW"))
  tensix_enabled = _read_tag_value(dev, "ENABLED_TENSIX_COL")
  gddr_enabled = _read_tag_value(dev, "ENABLED_GDDR")
  core_count = None if tensix_enabled is None else active_tensix_core_count(tensix_enabled & Arc.DEFAULT_TENSIX_ENABLED)
  board_name = _decode_board_name(board_id)
  active_gddr_banks, harvested_gddr_banks = _decode_gddr_mask(gddr_enabled)
  heartbeat = _read_tag_value(dev, "TIMER_HEARTBEAT")

  left_metrics = [
    "ASIC_TEMPERATURE",
    "BOARD_TEMPERATURE",
    "VREG_TEMPERATURE",
    "MAX_GDDR_TEMP",
    "FAN_SPEED",
    "FAN_RPM",
    "TDP",
    "TDC",
    "VCORE",
    "BOARD_POWER_LIMIT",
  ]
  right_metrics = ["AICLK", "AXICLK", "ARCCLK", "AICLK_LIMIT_MAX", "GDDR_SPEED", "THM_LIMIT_THROTTLE", "THM_LIMIT_SHUTDOWN"]

  summary_left = []
  for name in left_metrics:
    row = _read_metric_row_by_name(dev, name)
    if row is not None:
      summary_left.append(row)

  summary_right = []
  if board_name is not None:
    summary_right.append(("Board", board_name))
  if core_count is not None:
    summary_right.append(("Tensix cores", str(core_count)))
  if gddr_enabled is not None:
    summary_right.append(("Active GDDR banks", f"{_format_ranges(active_gddr_banks)} ({len(active_gddr_banks)}/{Dram.BANK_COUNT})"))
  if harvested_gddr_banks:
    summary_right.append(("Harvested DRAM bank", _format_harvested_dram_bank(harvested_gddr_banks)))
  for name in right_metrics:
    row = _read_metric_row_by_name(dev, name)
    if row is not None:
      summary_right.append(row)

  modules = _decode_gddr_modules(dev)

  return {
    "layout": layout,
    "summary_left": summary_left,
    "summary_right": summary_right,
    "gddr": modules,
    "extra": [],
    "heartbeat": heartbeat,
  }


def _print_metric_group(dev: PCIDevice, metrics: list[Metric]):
  for metric in metrics:
    if not dev.has_telemetry_tag(metric.tag):
      continue
    raw = dev.read_telemetry_entry(metric.tag)
    print(f"  {metric.label:<24} {_format_metric(metric, raw)}")


def _print_raw_dump(dev: PCIDevice):
  print("  Raw telemetry")
  for tag in dev.telemetry_tags():
    name = TAG_ID_TO_NAME.get(tag, f"TAG_{tag}")
    raw = dev.read_telemetry_entry(tag)
    print(f"    {tag:>2} {name:<24} 0x{raw:08x}")


def show_device(index: int):
  with PCIDevice(index=index) as dev:
    snapshot = _device_snapshot(dev)
    layout = snapshot["layout"]
    print(f"◆ Device {index}: {dev.bdf}")
    print(f"  Telemetry table            0x{layout['table_base']:08x}")
    print(f"  Telemetry data             0x{layout['data_base']:08x}")
    print(f"  Telemetry entry count      {layout['entry_count']}")
    print(f"  ─── Thermals / Power ───")
    for label, value in snapshot["summary_left"]:
      print(f"  {label:<26} {value}")
    print(f"  ─── Clocks / Status ───")
    for label, value in snapshot["summary_right"]:
      print(f"  {label:<26} {value}")
    if snapshot["gddr"]:
      print(f"  ─── GDDR Modules ───")
      print(f"  {'Bank':>4}  {'Top°':>5}  {'Bot°':>5}  {'CRd':>4}  {'CWr':>4}  {'URd':>4}  {'UWr':>4}")
      for module in snapshot["gddr"]:
        uncorr_rd = "✗" if module['uncorr_rd'] else "·"
        uncorr_wr = "✗" if module['uncorr_wr'] else "·"
        print(f"    {module['module']:>2}  {module['top']:>4}°  {module['bottom']:>4}°  {module['corr_rd']:>4}  {module['corr_wr']:>4}     {uncorr_rd}     {uncorr_wr}")
    for label, value in snapshot["extra"]:
      print(f"  {label:<26} {value}")
    _print_raw_dump(dev)


def reset_device(index: int):
  devices = PCIDevice.list_devices()
  if index >= len(devices):
    raise RuntimeError(f"Blackhole device {index} not found (found {len(devices)})")
  bdf = devices[index].split("/")[-1]
  PCIDevice.reset_index(index)
  print(f"Reset device {index}: {bdf}")


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Standalone Blackhole telemetry and reset tool")
  parser.add_argument("-r", "--reset", type=int, metavar="DEVICE", help="reset the selected Blackhole device")
  parser.add_argument("-d", "--device", type=int, metavar="DEVICE", help="show telemetry for one device only")
  parser.add_argument("--plain", action="store_true", help="disable the curses UI and print a one-shot snapshot")
  parser.add_argument("--interval", type=float, default=0.5, help="refresh interval in seconds for the TUI")
  return parser.parse_args()


def _render_tui(stdscr, devices: list[tuple[int, PCIDevice]], interval_s: float):
  curses.curs_set(0)
  curses.use_default_colors()
  stdscr.nodelay(True)
  stdscr.timeout(max(50, int(interval_s * 1000)))

  C_CYAN = 1; C_GREEN = 2; C_YELLOW = 3; C_MAGENTA = 4; C_RED = 5
  if curses.has_colors():
    curses.start_color()
    curses.init_pair(C_CYAN, curses.COLOR_CYAN, -1)
    curses.init_pair(C_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(C_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_MAGENTA, curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_RED, curses.COLOR_RED, -1)

  header_attr = curses.A_BOLD
  value_attr = curses.A_NORMAL
  muted_attr = curses.A_DIM
  scroll = 0
  tick = 0

  HEART_FRAMES = ["♥·", "♥♥", "·♥", "♥♥"]

  def add_line(lines: list[tuple[str, int]], text: str = "", attr: int = value_attr):
    lines.append((text, attr))

  def box_top(width: int, title: str) -> str:
    inner = max(4, width - 2)
    if title:
      label = f" {title} "
      fill = max(0, inner - len(label))
      return "╭" + label + "─" * fill + "╮"
    return "╭" + "─" * inner + "╮"

  def box_mid(width: int, text: str) -> str:
    inner = max(4, width - 2)
    return "│" + f"{text[:inner]:<{inner}}" + "│"

  def box_bot(width: int) -> str:
    inner = max(4, width - 2)
    return "╰" + "─" * inner + "╯"

  def box_lines(width: int, title: str, body: list[str]) -> list[str]:
    lines = [box_top(width, title)]
    for row in body:
      lines.append(box_mid(width, row))
    lines.append(box_bot(width))
    return lines

  def render_kv_box(width: int, title: str, rows: list[tuple[str, str]], min_rows: int = 0) -> list[str]:
    inner = max(4, width - 4)
    label_w = max(8, min(inner // 2, max((len(label) for label, _ in rows), default=8)))
    value_w = max(6, inner - label_w - 3)
    body = []
    for label, value in rows:
      body.append(f" {label[:label_w]:<{label_w}} {value[:value_w]:>{value_w}} ")
    while len(body) < min_rows:
      body.append(" " * (inner))
    return box_lines(width, title, body)

  def render_gddr_box(width: int, modules: list[dict]) -> list[str]:
    cols = [("Bank", 4), ("Top", 4), ("Bot", 4), ("CRd", 4), ("CWr", 4), ("URd", 4), ("UWr", 4)]
    sep = " "
    min_table_w = sum(col_w for _, col_w in cols) + len(sep) * (len(cols) - 1)
    if width - 4 < min_table_w:
      body = ["terminal too narrow"]
      return box_lines(width, "GDDR", body)
    header = sep.join(f"{name:>{col_w}}" for name, col_w in cols)
    divider = "─" * len(header)
    body = [header, divider]
    for module in modules:
      uncorr_rd = "x" if module['uncorr_rd'] else "."
      uncorr_wr = "x" if module['uncorr_wr'] else "."
      body.append(sep.join([
        f"{module['module']:>4}",
        f"{module['top']:>4}",
        f"{module['bottom']:>4}",
        f"{module['corr_rd']:>4}",
        f"{module['corr_wr']:>4}",
        f"   {uncorr_rd}",
        f"   {uncorr_wr}",
      ]))
    return box_lines(width, "GDDR", body)

  def combine_columns(left: list[str], right: list[str], total_width: int) -> list[str]:
    gap = 1
    left_w = max(20, (total_width - gap) // 2)
    right_w = max(20, total_width - gap - left_w)
    height = max(len(left), len(right))
    out = []
    for i in range(height):
      l = left[i] if i < len(left) else " " * left_w
      r = right[i] if i < len(right) else " " * right_w
      out.append(f"{l:<{left_w}}{' ' * gap}{r:<{right_w}}")
    return out

  def render_device_card(index: int, dev: PCIDevice, width: int) -> list[tuple[str, int]]:
    snapshot = _device_snapshot(dev)
    content_w = max(40, width - 2)
    lines = []

    heartbeat = snapshot["heartbeat"]
    heart = HEART_FRAMES[tick % len(HEART_FRAMES)] if heartbeat is not None else "??"
    title = f"  Device {index}  {dev.bdf}  {heart}"
    add_line(lines, title[:content_w], curses.color_pair(C_CYAN) | curses.A_BOLD if curses.has_colors() else header_attr)

    col_w = content_w // 2
    n_left = len(snapshot["summary_left"])
    n_right = len(snapshot["summary_right"])
    pad_rows = max(n_left, n_right)
    top_left = render_kv_box(col_w, "Thermals / Power", snapshot["summary_left"], min_rows=pad_rows)
    top_right = render_kv_box(content_w - col_w, "Clocks / Status", snapshot["summary_right"], min_rows=pad_rows)
    for line in combine_columns(top_left, top_right, content_w):
      add_line(lines, line)

    if snapshot["gddr"]:
      for line in render_gddr_box(content_w, snapshot["gddr"]):
        add_line(lines, line, curses.color_pair(C_GREEN) if curses.has_colors() else value_attr)

    return lines

  while True:
    lines = []
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    tick += 1

    banner = f" tt-smi  {timestamp}  q:quit  arrows:scroll"
    add_line(lines, banner, curses.color_pair(C_MAGENTA) | curses.A_BOLD if curses.has_colors() else header_attr)
    add_line(lines, "")

    height, width = stdscr.getmaxyx()
    card_width = max(40, width - 1)

    for index, dev in devices:
      try:
        card_lines = render_device_card(index, dev, card_width)
        lines.extend(card_lines)
      except Exception as exc:
        add_line(lines, f"  Device {index}: {dev.bdf}", header_attr)
        add_line(lines, f"  error: {exc}", curses.color_pair(C_RED) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
      add_line(lines, "")

    visible_rows = max(1, height - 1)
    max_scroll = max(0, len(lines) - visible_rows)
    scroll = min(scroll, max_scroll)

    stdscr.erase()
    for row_idx, (text, attr) in enumerate(lines[scroll:scroll + visible_rows]):
      try:
        stdscr.addnstr(row_idx, 0, text, max(1, width - 1), attr)
      except curses.error:
        pass
    if max_scroll:
      footer = f" {scroll}/{max_scroll} "
      try:
        stdscr.addnstr(height - 1, max(0, width - len(footer) - 1), footer, len(footer), muted_attr)
      except curses.error:
        pass
    stdscr.refresh()

    key = stdscr.getch()
    if key in (-1,):
      continue
    if key in (ord("q"), ord("Q")):
      return
    if key == curses.KEY_UP:
      scroll = max(0, scroll - 1)
    elif key == curses.KEY_DOWN:
      scroll = min(max_scroll, scroll + 1)
    elif key == curses.KEY_PPAGE:
      scroll = max(0, scroll - visible_rows)
    elif key == curses.KEY_NPAGE:
      scroll = min(max_scroll, scroll + visible_rows)
    elif key == curses.KEY_HOME:
      scroll = 0
    elif key == curses.KEY_END:
      scroll = max_scroll


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
      try:
        dev.close()
      except Exception:
        pass


def _run_plain(indices: list[int]):
  for i, index in enumerate(indices):
    if i:
      print()
    show_device(index)


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
    _run_plain(indices)
    return

  _run_tui(indices, args.interval)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    pass
