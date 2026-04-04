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
  "ASIC_TEMPERATURE":    ("ASIC temperature",           " C",    "s16.16"),
  "AICLK":               ("AICLK",                      " MHz",  None),
  "AXICLK":              ("AXICLK",                     " MHz",  None),
  "ARCCLK":              ("ARCCLK",                     " MHz",  None),
  "AICLK_LIMIT_MAX":     ("AICLK max",                  " MHz",  None),
  "GDDR_SPEED":          ("GDDR speed",                 " MT/s", None),
  "FAN_SPEED":           ("Fan speed",                  " %",    None),
  "FAN_RPM":             ("Fan RPM",                    " rpm",  None),
  "TDP":                 ("TDP",                        " W",    None),
  "TDP_LIMIT_MAX":       ("TDP max",                    " W",    None),
  "TDC":                 ("TDC",                        " A",    None),
  "TDC_LIMIT_MAX":       ("TDC max",                    " A",    None),
  "VCORE":               ("VCORE",                      " mV",   None),
  "BOARD_POWER_LIMIT":   ("Board power limit",          " W",    None),
  "THM_LIMIT_THROTTLE":  ("Thermal throttle limit",     " C",    None),
  "THM_LIMIT_SHUTDOWN":  ("Thermal shutdown limit",     " C",    None),
  "MAX_GDDR_TEMP":       ("Max GDDR temperature",       " C",    None),
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


def _decode_gddr_modules(dev: PCIDevice, layout: dict) -> list[dict]:
  pairs = ("0_1", "2_3", "4_5", "6_7")
  temp_tags = [TAG_NAME_TO_ID[f"GDDR_{p}_TEMP"] for p in pairs]
  corr_tags = [TAG_NAME_TO_ID[f"GDDR_{p}_CORR_ERRS"] for p in pairs]
  uncorr_tag = TAG_NAME_TO_ID["GDDR_UNCORR_ERRS"]
  if not all(t in layout["tag_to_offset"] for t in temp_tags + corr_tags + [uncorr_tag]):
    return []

  uncorr = read_telemetry_entry(dev, layout, uncorr_tag)
  modules = []
  for pi in range(4):
    tw = read_telemetry_entry(dev, layout, temp_tags[pi])
    cw = read_telemetry_entry(dev, layout, corr_tags[pi])
    for lane in range(2):
      m, sh = pi * 2 + lane, 16 if lane else 0
      modules.append({"module": m, "top": (tw >> (sh + 8)) & 0xFF, "bottom": (tw >> sh) & 0xFF,
                       "corr_rd": (cw >> sh) & 0xFF, "corr_wr": (cw >> (sh + 8)) & 0xFF,
                       "uncorr_rd": 1 if uncorr & (1 << (m * 2)) else 0,
                       "uncorr_wr": 1 if uncorr & (1 << (m * 2 + 1)) else 0})
  return modules


def _device_snapshot(dev: PCIDevice) -> dict:
  layout = telemetry_layout(dev)
  bid_hi, bid_lo = _read_tag(dev, layout, "BOARD_ID_HIGH"), _read_tag(dev, layout, "BOARD_ID_LOW")
  board_id = ((bid_hi & 0xFFFFFFFF) << 32 | (bid_lo & 0xFFFFFFFF)) if bid_hi is not None and bid_lo is not None else None
  tensix_en = _read_tag(dev, layout, "ENABLED_TENSIX_COL")
  gddr_en = _read_tag(dev, layout, "ENABLED_GDDR")
  core_count = None if tensix_en is None else active_tensix_core_count(tensix_en & Arc.DEFAULT_TENSIX_ENABLED)
  board_name = BOARD_UPI_TO_NAME.get((board_id >> 36) & 0xFFFFF) if board_id is not None else None

  active_banks = [b for b in range(Dram.BANK_COUNT) if gddr_en and (gddr_en >> b) & 1] if gddr_en else []
  harv_banks = [b for b in range(Dram.BANK_COUNT) if gddr_en and not (gddr_en >> b) & 1] if gddr_en else []

  def rows(names):
    return [r for name in names if (r := _read_metric_row(dev, layout, name)) is not None]

  left = rows(["ASIC_TEMPERATURE", "MAX_GDDR_TEMP", "FAN_SPEED", "FAN_RPM", "TDP", "TDC", "VCORE", "BOARD_POWER_LIMIT"])

  right = []
  if board_name: right.append(("Board", board_name))
  if core_count is not None: right.append(("Tensix cores", str(core_count)))
  if gddr_en is not None: right.append(("Active GDDR banks", f"{_format_ranges(active_banks)} ({len(active_banks)}/{Dram.BANK_COUNT})"))
  if harv_banks: right.append(("Harvested DRAM bank", _format_ranges(harv_banks)))
  right += rows(["AICLK", "AXICLK", "ARCCLK", "AICLK_LIMIT_MAX", "GDDR_SPEED", "THM_LIMIT_THROTTLE", "THM_LIMIT_SHUTDOWN"])

  return {"layout": layout, "summary_left": left, "summary_right": right,
          "gddr": _decode_gddr_modules(dev, layout), "heartbeat": _read_tag(dev, layout, "TIMER_HEARTBEAT")}


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
      for label, value in rows:
        print(f"  {label:<26} {value}")
    if snap["gddr"]:
      print(f"  ─── GDDR Modules ───")
      print(f"  {'Bank':>4}  {'Top°':>5}  {'Bot°':>5}  {'CRd':>4}  {'CWr':>4}  {'URd':>4}  {'UWr':>4}")
      for m in snap["gddr"]:
        ur, uw = ("✗" if m['uncorr_rd'] else "·"), ("✗" if m['uncorr_wr'] else "·")
        print(f"    {m['module']:>2}  {m['top']:>4}°  {m['bottom']:>4}°  {m['corr_rd']:>4}  {m['corr_wr']:>4}     {ur}     {uw}")
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

def _render_tui(stdscr, devices: list[tuple[int, PCIDevice]], interval_s: float):
  curses.curs_set(0)
  curses.use_default_colors()
  stdscr.nodelay(True)
  stdscr.timeout(max(50, int(interval_s * 1000)))

  C_CYAN, C_GREEN, C_YELLOW, C_MAGENTA, C_RED = 1, 2, 3, 4, 5
  if curses.has_colors():
    curses.start_color()
    for i, color in enumerate([curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_MAGENTA, curses.COLOR_RED], 1):
      curses.init_pair(i, color, -1)

  scroll, tick = 0, 0
  HEART_FRAMES = ["♥·", "♥♥", "·♥", "♥♥"]

  def cpair(n): return curses.color_pair(n) if curses.has_colors() else 0

  def box_lines(width: int, title: str, body: list[str]) -> list[str]:
    inner = max(4, width - 2)
    label = f" {title} " if title else ""
    lines = ["╭" + label + "─" * max(0, inner - len(label)) + "╮"]
    for row in body:
      lines.append("│" + f"{row[:inner]:<{inner}}" + "│")
    lines.append("╰" + "─" * inner + "╯")
    return lines

  def kv_box(width: int, title: str, rows: list[tuple[str, str]], min_rows: int = 0) -> list[str]:
    inner = max(4, width - 4)
    lw = max(8, min(inner // 2, max((len(l) for l, _ in rows), default=8)))
    vw = max(6, inner - lw - 3)
    body = [f" {l[:lw]:<{lw}} {v[:vw]:>{vw}} " for l, v in rows]
    while len(body) < min_rows:
      body.append(" " * inner)
    return box_lines(width, title, body)

  def gddr_box(width: int, modules: list[dict]) -> list[str]:
    cols = [("Bank", 4), ("Top", 4), ("Bot", 4), ("CRd", 4), ("CWr", 4), ("URd", 4), ("UWr", 4)]
    min_w = sum(w for _, w in cols) + len(cols) - 1
    if width - 4 < min_w:
      return box_lines(width, "GDDR", ["terminal too narrow"])
    header = " ".join(f"{n:>{w}}" for n, w in cols)
    body = [header, "─" * len(header)]
    for m in modules:
      ur, uw = ("x" if m['uncorr_rd'] else "."), ("x" if m['uncorr_wr'] else ".")
      body.append(" ".join([f"{m['module']:>4}", f"{m['top']:>4}", f"{m['bottom']:>4}",
                            f"{m['corr_rd']:>4}", f"{m['corr_wr']:>4}", f"   {ur}", f"   {uw}"]))
    return box_lines(width, "GDDR", body)

  def merge_cols(left: list[str], right: list[str], total_w: int) -> list[str]:
    lw, rw = max(20, (total_w - 1) // 2), max(20, total_w - 1 - max(20, (total_w - 1) // 2))
    h = max(len(left), len(right))
    return [f"{(left[i] if i < len(left) else ''):<{lw}} {(right[i] if i < len(right) else ''):<{rw}}" for i in range(h)]

  def render_card(index: int, dev: PCIDevice, width: int) -> list[tuple[str, int]]:
    snap = _device_snapshot(dev)
    cw = max(40, width - 2)
    heart = HEART_FRAMES[tick % len(HEART_FRAMES)] if snap["heartbeat"] is not None else "??"
    lines = [(f"  Device {index}  {dev.bdf}  {heart}"[:cw], cpair(C_CYAN) | curses.A_BOLD)]
    col_w = cw // 2
    pad = max(len(snap["summary_left"]), len(snap["summary_right"]))
    for row in merge_cols(kv_box(col_w, "Thermals / Power", snap["summary_left"], pad),
                          kv_box(cw - col_w, "Clocks / Status", snap["summary_right"], pad), cw):
      lines.append((row, 0))
    if snap["gddr"]:
      for row in gddr_box(cw, snap["gddr"]):
        lines.append((row, cpair(C_GREEN)))
    return lines

  while True:
    lines = []
    tick += 1
    lines.append((f" tt-smi  {time.strftime('%Y-%m-%d %H:%M:%S')}  q:quit  arrows:scroll", cpair(C_MAGENTA) | curses.A_BOLD))
    lines.append(("", 0))

    height, width = stdscr.getmaxyx()
    card_w = max(40, width - 1)
    for index, dev in devices:
      try:
        lines.extend(render_card(index, dev, card_w))
      except Exception as exc:
        lines.append((f"  Device {index}: {dev.bdf}", curses.A_BOLD))
        lines.append((f"  error: {exc}", cpair(C_RED) | curses.A_BOLD))
      lines.append(("", 0))

    visible = max(1, height - 1)
    max_scroll = max(0, len(lines) - visible)
    scroll = min(scroll, max_scroll)

    stdscr.erase()
    for ri, (text, attr) in enumerate(lines[scroll:scroll + visible]):
      try:
        stdscr.addnstr(ri, 0, text, max(1, width - 1), attr)
      except curses.error:
        pass
    if max_scroll:
      footer = f" {scroll}/{max_scroll} "
      try:
        stdscr.addnstr(height - 1, max(0, width - len(footer) - 1), footer, len(footer), curses.A_DIM)
      except curses.error:
        pass
    stdscr.refresh()

    key = stdscr.getch()
    if key == -1: continue
    if key in (ord("q"), ord("Q")): return
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
