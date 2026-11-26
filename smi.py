import argparse, csv, glob, os, re, select, shutil, signal, sys, termios, time, tty
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pci import open_monitor
MAC = sys.platform == "darwin"
if MAC: import pci_macos
else: from pci_linux import RESET_ASIC, RESET_ASIC_DMC, RESET_PCIE_LINK, RESET_POST

SYS = "/sys/class/tenstorrent"
BOOT_STATUS = 0x80030408

TAGS = dict(vcore_mv=6, core_w=7, asic_raw=11, aiclk=14, l2cpuclk=17, eth_live=21, hb=32, eth_on=35, fan_rpm=41,
            gddr_ue=50, gddr_c=51, board_limit_w=53, board_w=54, throttle_c=56, trips=60, aiclk_max=63,
            core_limit_w=64, arb_min=65, arb_max=66)
ARB_MAX = ["fmax", "TDP", "fast TDC", "TDC", "thermal", "board power", "voltage", "GDDR thermal",
           "di/dt slow", "di/dt critical", "host fmax"]
PCIE_GEN = {2.5: 1, 5.0: 2, 8.0: 3, 16.0: 4, 32.0: 5, 64.0: 6}

ETH_X = [1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10]
BOOT_RESULTS = 0x7CC00
P150_QSFP = {11: 1, 9: 1, 8: 2, 10: 2, 7: 3, 5: 3, 4: 4, 6: 4}

def rd(path):
  try:
    with open(path) as f: return f.read().strip()
  except OSError: return None

def mac_cards():
  try: return [0] if "ttgpu" in __import__("subprocess").run(["ioreg", "-n", "ttgpu"], capture_output=True, text=True).stdout else []
  except OSError: return []

def bdf(idx):
  if MAC: return "thunderbolt"
  return os.path.basename(os.path.realpath(f"{SYS}/tenstorrent!{idx}/device"))
def cards():
  if MAC: return mac_cards()
  return sorted(int(p.rsplit("!", 1)[1]) for p in glob.glob(f"{SYS}/tenstorrent!*"))
def ports(mask): return ",".join(str(i) for i in range(16) if mask >> i & 1) or "none"

def eth(card, on):
  # per enabled Ethernet channel: (training status, ?, retrain count, peer (asic id, channel, logical port) if up)
  out = {}
  for ch in (c for c in range(14) if on >> c & 1):
    r = lambda off: card.noc_read(BOOT_RESULTS + off, (ETH_X[ch], 1))
    st, peer = r(4), None
    if st == 1:
      w = r(992)
      peer = (r(992 + 20) << 32 | r(992 + 24), w >> 16 & 0xFF, w >> 24)
    out[ch] = (st, r(960) >> 24, r(12) if st == 1 else 0, peer)
  return out

def one(idx, fn):
  c = open_monitor(idx)
  try: return fn(c)
  finally: c.close()

def pcie(idx, card=None):
  if MAC:
    try: return pci_macos.pcie_link(card.io if card else None)
    except (OSError, RuntimeError): return (None, None), (None, None)
  dev = f"{SYS}/tenstorrent!{idx}/device"
  def link(kind):
    try: return PCIE_GEN.get(float(rd(f"{dev}/{kind}_link_speed").split()[0])), int(rd(f"{dev}/{kind}_link_width"))
    except (AttributeError, ValueError): return None, None
  return link("current"), link("max")

class Mon:
  def __init__(self, idx):
    self.idx, self.card, self.err, self.retry_at, self.prev_hb = idx, None, None, 0.0, None
    self.type = rd(f"{SYS}/tenstorrent!{idx}/tt_card_type") or "?"
    self.bdf = bdf(idx)
    self.hist = deque(maxlen=120)
    self.eth, self.eth_live, self.eth_at = {}, None, 0.0

  def sample(self):
    t = time.monotonic()
    (gen, width), (max_gen, max_width) = pcie(self.idx, self.card)
    s = dict(card=self.idx, pcie_gen=gen, pcie_width=width, pcie_max_gen=max_gen, pcie_max_width=max_width)
    if self.card is None and t >= self.retry_at:
      try: self.card, self.err = open_monitor(self.idx), None
      except OSError as e: self.err, self.retry_at = getattr(e, "strerror", None) or str(e), t + 5
    if self.card is not None:
      try:
        s.update(self.card.telemetry(TAGS))
        if MAC and self.type == "?": self.type = self.card.board_type()
        if (k := (s["eth_on"], s["eth_live"] >> 16)) != self.eth_live or t >= self.eth_at:
          self.eth, self.eth_live, self.eth_at = eth(self.card, k[0]), k, t + 10
      except OSError as e:
        self.card.close(); self.card, self.err, self.retry_at, self.eth_live = None, getattr(e, "strerror", None) or str(e), t + 2, None
    s["eth_links"] = " ".join(f"{ch}>{p[0]}:{p[1]}" for ch, p in self.links())
    if s.get("asic_raw") is None: return s
    a = s.pop("asic_raw")
    s["asic_c"] = round((a - (1 << 32) if a & 0x80000000 else a) / 65536, 1)
    s["state"] = "awake" if s["aiclk"] > (s["arb_min"] or 0) & 0xFFFF else "boot" if s["l2cpuclk"] else "idle"
    s["alive"] = None if self.prev_hb is None else s["hb"] != self.prev_hb
    self.prev_hb = s["hb"]
    arb = s["arb_max"]
    s["throttle"] = ARB_MAX[arb >> 16] if (arb >> 16) < len(ARB_MAX) else f"#{arb >> 16}"
    s["throttle"] = s["throttle"] if s["state"] == "awake" and (arb & 0xFFFF) < s["aiclk_max"] else ""
    self.hist.append(s["board_w"])
    return s

  def links(self):
    ids = {} if MAC else {int(rd(f"{SYS}/tenstorrent!{i}/tt_asic_id") or "0", 16): i for i in cards()}
    def peer(asic, ch, lg):
      i = ids.get(asic)
      p150 = i is not None and (rd(f"{SYS}/tenstorrent!{i}/tt_card_type") or "").startswith("p150")
      return (f"{asic:x}" if i is None else i, ch, P150_QSFP.get(lg) if p150 else None)
    return [(ch, peer(*e[3])) for ch, e in sorted(self.eth.items()) if e[3]]

  def close(self):
    if self.card: self.card.close()

E = "\x1b["
RST, BOLD = E + "0m", E + "1m"
def fg(n): return f"{E}38;5;{n}m"
DIM, ACC, OK, WARN, BAD = fg(244), fg(81), fg(78), fg(221), fg(203)
SPARK, EIGHTHS = "▁▂▃▄▅▆▇█", " ▏▎▍▌▋▊▉"

def heat(frac): return OK if frac < 0.6 else WARN if frac < 0.85 else BAD

def bar(v, vmax, width):
  if v is None or not vmax: return DIM + "·" * width + RST
  cells = max(0.0, min(1.0, v / vmax)) * width
  full, part = int(cells), int((cells - int(cells)) * 8)
  s = "█" * full + (EIGHTHS[part] if full < width and part else "")
  return heat(v / vmax) + s + RST + DIM + "·" * (width - len(s)) + RST

def spark(vals, width):
  vals = list(vals)[-width:]
  if not vals: return ""
  lo, hi = min(vals), max(vals)
  if hi - lo < 10: mid = (hi + lo) / 2; lo, hi = mid - 5, mid + 5
  return ACC + "".join(SPARK[max(0, min(7, int((v - lo) / (hi - lo) * 8)))] for v in vals) + RST

def temp(v, limit):
  if v is None: return "—"
  return (heat(v / limit) if limit and v / limit >= 0.6 else "") + f"{v:.0f}°C" + RST

def render_card(m, s, width):
  dot = {None: DIM + "○", True: OK + "●", False: BAD + "●"}[s.get("alive")] + RST
  link = f"gen{s['pcie_gen']} x{s['pcie_width']}" if s["pcie_gen"] else "pcie ?"
  if (s["pcie_gen"], s["pcie_width"]) != (s["pcie_max_gen"], s["pcie_max_width"]):
    link = f"{WARN}{link}{RST}{DIM} of gen{s['pcie_max_gen']} x{s['pcie_max_width']}{RST}"
  state = s.get("state")
  state = {"idle": DIM + "idle", "awake": OK + "awake", "boot": WARN + "boot"}.get(state, DIM + "—") + RST
  head = f" {dot} {BOLD}{m.idx}{RST} {DIM}{m.type} {m.bdf}{RST}  {link}  {state}"
  if s.get("board_w") is None:
    return [head, f"     {DIM}telemetry unavailable: {m.err or '?'}{RST}", ""]
  bw = max(12, min(30, width - 70))
  line1 = (f"     {BOLD}{s['board_w']:3d} W{RST} {DIM}board{RST} {bar(s['board_w'], s['board_limit_w'], bw)} "
           f"{spark(m.hist, max(8, width - bw - 44))}  {DIM}core{RST} {s['core_w']} W")
  line2 = (f"     {DIM}asic{RST} {temp(s['asic_c'], s['throttle_c'])}  {DIM}gddr{RST} {temp(s['gddr_c'], 85)}  "
           f"{DIM}fan{RST} {s['fan_rpm']} rpm  {DIM}aiclk{RST} {s['aiclk']} MHz  {DIM}vcore{RST} {s['vcore_mv']} mV")
  alerts = []
  if s["throttle"]: alerts.append(f"aiclk capped at {s['arb_max'] & 0xFFFF} MHz by {s['throttle']}")
  if s["state"] == "boot": alerts.append("never parked: ./smi.py -r")
  if s.get("alive") is False: alerts.append("heartbeat stalled")
  if s["trips"]: alerts.append(f"{s['trips']} thermal trips")
  if s["gddr_ue"]: alerts.append(f"{s['gddr_ue']} uncorrected GDDR errors")
  if alerts: line2 += "   " + WARN + " · ".join(alerts) + RST
  return [head, line1, line2] + ([render_eth(m)] if m.eth else []) + [""]

def render_eth(m):
  def glyph(ch):
    st = m.eth[ch][0] if ch in m.eth else None
    return (OK + "●" if st == 1 else DIM + {None: "×", 2: "○"}.get(st, "·")) + RST
  q = {ch: P150_QSFP.get(e[1]) for ch, e in m.eth.items()} if m.type.startswith("p150") else {}
  if q: ports = "  ".join(f"{i} " + "".join(glyph(ch) for ch in sorted(c for c in q if q[c] == i)) for i in range(1, 5))
  else: ports = "".join(glyph(ch) for ch in range(14))
  groups = {}
  for ch, (card, rch, rq) in m.links(): groups.setdefault((q.get(ch), card, rq), []).append((ch, rch))
  links = []
  for (lq, card, rq), chs in groups.items():
    speed = {m.eth[ch][2] for ch, _ in chs}
    links.append(f"{f'qsfp{lq} ' if lq else ''}⇄ {BOLD}{'card ' if isinstance(card, int) else 'asic '}{card}{RST}"
                 f"{f' qsfp{rq}' if rq else ''}  {DIM}{len(chs)}×{'/'.join(map(str, sorted(speed)))}G  "
                 + " ".join(f"ch{a}↔{b}" for a, b in chs) + RST)
  return f"     {DIM}eth {'qsfp' if q else 'ch'}{RST} {ports}   " + ("   ".join(links) or DIM + "no links" + RST)

def render(mons, samples, args, live=True):
  width = max(72, min(shutil.get_terminal_size((100, 30)).columns, 120))
  hint = f"  every {args.interval:g}s · q to quit" if live else ""
  out = [f" {BOLD}{ACC}smi{RST}{DIM}{hint}{RST}" + " " * max(1, width - 13 - len(hint)) + DIM + time.strftime("%H:%M:%S") + RST, ""]
  for m, s in zip(mons, samples): out += render_card(m, s, width)
  tot = [s["board_w"] for s in samples if s.get("board_w") is not None]
  if len(mons) > 1 and tot: out.append(f" {DIM}total board{RST} {BOLD}{sum(tot)} W{RST}")
  return out

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

def wait_for(what, cond, timeout, step=0.05):
  end = time.monotonic() + timeout
  while (r := cond()) is None:
    if time.monotonic() > end: raise TimeoutError(f"timed out after {timeout:g}s waiting for {what}")
    time.sleep(step)
  return r

def reset_mac(force=False):
  t0 = time.monotonic()
  try:
    pci_macos.reset(force=force)
    c = pci_macos.MacMonitor(0)
    try:
      def heartbeat():
        try: t = c.telemetry(TAGS)
        except OSError: c.table = None; return None
        return t if t["hb"] else None
      t = wait_for("ARC telemetry", heartbeat, 15)
    finally: c.close()
    pci_macos.park(force=force)
  except (OSError, RuntimeError, TimeoutError) as e: sys.exit(f"card 0: {e}")
  print(f"card 0: up in {time.monotonic() - t0:.1f}s, board {t['board_w']} W, eth link up {ports(t['eth_live'] >> 16)}; idle vote sent")

def reset(idxs, sbr=True, dmc=False, force=False):
  if MAC:
    if dmc or not sbr: sys.exit("--dmc and --no-sbr aren't supported on macOS")
    return reset_mac(force)
  bdfs = {i: bdf(i) for i in idxs}
  busy = [i for i in idxs if one(i, lambda c: c.in_use())]
  if busy and not force:
    sys.exit(f"card(s) {busy} in use by another process (tt-metal / blackhole-py); stop it or pass --force")

  t0 = time.monotonic()
  if sbr:
    for i in idxs:
      if not one(i, lambda c: c.reset(RESET_PCIE_LINK)): print(f"card {i}: secondary bus reset failed, continuing")
  for i in idxs:
    if not one(i, lambda c: c.reset(RESET_ASIC_DMC if dmc else RESET_ASIC)):
      sys.exit(f"card {i}: {'ASIC+DMC' if dmc else 'ASIC'} reset ioctl failed")
  print(f"reset issued to {', '.join(f'{i} ({bdfs[i]})' for i in idxs)}")
  time.sleep(20 if dmc else max(2, 0.4 * len(idxs)))

  failed = []
  for i, b in bdfs.items():
    try:
      def back():
        m = glob.glob(f"/sys/bus/pci/devices/{b}/tenstorrent/tenstorrent!*")
        n = int(m[0].rsplit("!", 1)[1]) if m else None
        return n if n is not None and os.path.exists(f"/dev/tenstorrent/{n}") else None
      n = wait_for(f"{b} to reappear", back, 30)
      def marker_clear():
        with open(f"/sys/bus/pci/devices/{b}/config", "rb") as f: return True if not os.pread(f.fileno(), 1, 4)[0] & 0x40 else None
      wait_for(f"{b} reset marker to clear", marker_clear, 30)
      if not one(n, lambda c: c.reset(RESET_POST)): raise OSError(f"POST_RESET failed for /dev/tenstorrent/{n}")
      c = open_monitor(n)
      try:
        wait_for("ARC boot", lambda: True if c.noc_read(BOOT_STATUS) & 1 else None, 15)
        def heartbeat():
          try: t = c.telemetry(TAGS)
          except OSError: c.table = None; return None
          return t if t["hb"] else None
        t = wait_for("ARC telemetry", heartbeat, 15)
        c.vote_idle()
      finally: c.close()
      print(f"card {i} -> /dev/tenstorrent/{n}: up in {time.monotonic() - t0:.1f}s, board {t['board_w']} W, "
            f"eth link up {ports(t['eth_live'] >> 16)} (not waited for); idle vote sent")
    except (OSError, TimeoutError) as e:
      print(f"card {i} ({b}): {e}"); failed.append(i)
  if failed: sys.exit(1)

CSV = ["time", "card", "state", "board_w", "core_w", "asic_c", "gddr_c", "fan_rpm", "aiclk", "vcore_mv",
       "pcie_gen", "pcie_width", "pcie_max_gen", "pcie_max_width", "throttle", "gddr_ue", "trips", "eth_links"]

def watch(mons, args):
  live = sys.stdout.isatty() and not args.csv
  keys = live and sys.stdin.isatty()
  count = args.count if args.count is not None else (0 if live else 1)
  if not live:
    for m in mons: m.sample()
    time.sleep(0.25)
  signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt))
  old_tc = termios.tcgetattr(sys.stdin) if keys else None
  w = csv.writer(sys.stdout, lineterminator="\n")
  if args.csv: w.writerow(CSV)
  if live: sys.stdout.write(E + "?1049h" + E + "?25l")
  if keys: tty.setcbreak(sys.stdin)
  try:
    n, nxt = 0, time.monotonic()
    while True:
      samples = [m.sample() for m in mons]
      if args.csv:
        now = f"{time.time():.3f}"
        for s in samples: w.writerow([now if k == "time" else "" if s.get(k) is None else s[k] for k in CSV])
      elif live:
        sys.stdout.write(E + "H" + "".join(ln + E + "K\n" for ln in render(mons, samples, args)) + E + "J")
      else:
        print(ANSI.sub("", "\n".join(render(mons, samples, args, live=False))))
      sys.stdout.flush()
      n += 1
      if count and n >= count: return
      nxt += args.interval
      while (left := nxt - time.monotonic()) > 0:
        if not keys: time.sleep(left); break
        if select.select([sys.stdin], [], [], left)[0] and os.read(sys.stdin.fileno(), 64)[:1] in (b"q", b"Q"): return
  except KeyboardInterrupt:
    pass
  finally:
    if keys: termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tc)
    if live: sys.stdout.write(E + "?25h" + E + "?1049l"); sys.stdout.flush()
    for m in mons: m.close()

def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("-n", "--interval", type=float, default=1.0, help="seconds between samples (default 1)")
  ap.add_argument("-d", "--device", type=int, action="append", help="card index (repeatable; default all)")
  ap.add_argument("--csv", action="store_true", help="CSV rows instead of the live view (default: 1 sample)")
  ap.add_argument("-c", "--count", type=int, help="number of samples, 0 = forever (default: live forever, else 1)")
  ap.add_argument("-r", "--reset", action="store_true", help="reset all cards together (cabled cards must reset together)")
  ap.add_argument("--dmc", action="store_true", help="with -r: also reset the board-management MCU (~20 s)")
  ap.add_argument("--no-sbr", action="store_true", help="with -r: skip the PCIe secondary bus reset")
  ap.add_argument("--force", action="store_true", help="with -r: reset even if another process holds the card")
  args = ap.parse_args()

  all_idx = cards()
  if not all_idx: sys.exit("no ttgpu device (is the card connected and the TTGPU driver enabled? ioreg -n ttgpu)" if MAC
                           else f"no cards under {SYS} (is tt-kmd loaded?)")
  if args.reset:
    if args.device: ap.error("-r/--reset always resets all cards; cannot combine with -d/--device")
    return reset(all_idx, sbr=not args.no_sbr, dmc=args.dmc, force=args.force)
  idxs = sorted(set(args.device or all_idx))
  if bad := [i for i in idxs if i not in all_idx]: sys.exit(f"no such card(s): {bad}")
  watch([Mon(i) for i in idxs], args)

if __name__ == "__main__":
  main()
