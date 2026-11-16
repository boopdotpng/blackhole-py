#!/usr/bin/env python3
"""smi - tiny tt-smi for Blackhole cards that doesn't wake them up. Press q to quit.

  ./smi.py                 live view of every card (1 s refresh; -n 0.25 for faster, -d 0 for one card)
  ./smi.py --csv           one CSV sample per card and exit (-c N samples, -c 0 forever) - for scripts/agents
  ./smi.py -r [IDX ...]    reset cards (default all) without waiting for eth training, then park them idle
  ./smi.py --park          vote idle on every card (see below); harmless if a process is using the card

tt-smi opens /dev/tenstorrent/N without O_APPEND, so tt-kmd treats it as a legacy client and votes the
card to full power (~+90 W) while it's open. Every fd here is O_APPEND and asks for nothing, so watching
doesn't change power. Telemetry is the ARC table read through the NOC_READ ioctl (no TLB, no locks).

After an in-place reset the KMD sends no power vote, so the card stays in firmware's boot state (GDDR PHY,
Tensix and L2CPU on: ~150 W) until something opens it. -r and --park vote idle, and the KMD powers the
card down after idle_power_down_grace_ms (5 s). The live view flags that state as "boot".

  board  12V-2x6 cable (INA228) + a fixed 20 W fw_table allowance for the unmeasured PCIe slot
  core   VCORE rail only (what hwmon power1 shows)
  state  idle = parked (min aiclk, L2CPU gated) · awake = a client voted for power · boot = never parked

macOS (TTGPU DriverKit driver, no tt-kmd): one card, index 0. Telemetry is read through BAR0 TLB window 200, which
blackhole-py never uses, so watching a running model is safe. -r is system_darwin.reset() (PCIe link reset, then the
timer-interrupt ASIC reset); --park and the post-reset idle vote send the power message straight to ARC, so they
refuse while blackhole-py holds the card (there is no KMD to aggregate votes).
"""
import argparse, csv, fcntl, glob, os, re, select, shutil, signal, struct, sys, termios, time, tty
from collections import deque

SYS = "/sys/class/tenstorrent"
ARC = (8, 0)
SCRATCH = lambda n: 0x80030400 + 4 * n
BOOT_STATUS, TELEM_DATA, TELEM_PTR = SCRATCH(2), SCRATCH(12), SCRATCH(13)

IOCTL = lambda nr: 0xFA00 | nr
RESET_DEVICE, LOCK_CTL, SET_POWER_STATE, NOC_READ = IOCTL(6), IOCTL(8), IOCTL(15), IOCTL(18)
RESET_PCIE_LINK, ASIC_RESET, ASIC_DMC_RESET, POST_RESET = 1, 4, 5, 6
LOCK_TEST, CHIP_IN_USE = 2, 20  # tt-umd lock_manager.cpp: CHIP_IN_USE is resource lock 20

# tt-system-firmware lib/tenstorrent/bh_arc/telemetry.h
TAGS = dict(vcore_mv=6, core_w=7, asic_raw=11, aiclk=14, l2cpuclk=17, eth_live=21, hb=32, fan_rpm=41,
            gddr_ue=50, gddr_c=51, board_limit_w=53, board_w=54, throttle_c=56, trips=60, aiclk_max=63,
            core_limit_w=64, arb_min=65, arb_max=66)
ARB_MAX = ["fmax", "TDP", "fast TDC", "TDC", "thermal", "board power", "voltage", "GDDR thermal",
           "di/dt slow", "di/dt critical", "host fmax"]
PCIE_GEN = {2.5: 1, 5.0: 2, 8.0: 3, 16.0: 4, 32.0: 5, 64.0: 6}

def ioctl(fd, req, fmt, *args):
  b = bytearray(struct.pack("<" + fmt, *args))
  fcntl.ioctl(fd, req, b)
  return struct.unpack("<" + fmt, b)

def rd(path):
  try:
    with open(path) as f: return f.read().strip()
  except OSError: return None

DARWIN = sys.platform == "darwin"
if DARWIN: import system_darwin as sd

def bdf(idx): return "thunderbolt" if DARWIN else os.path.basename(os.path.realpath(f"{SYS}/tenstorrent!{idx}/device"))
def cards():
  if DARWIN:
    try: sd.IOKit().close(); return [0]
    except RuntimeError: return []
  return sorted(int(p.rsplit("!", 1)[1]) for p in glob.glob(f"{SYS}/tenstorrent!*"))
def ports(mask): return ",".join(str(i) for i in range(16) if mask >> i & 1) or "none"

class Card:
  def __init__(self, idx):
    self.idx, self.addr = idx, None
    self.fd = os.open(f"/dev/tenstorrent/{idx}", os.O_RDWR | os.O_APPEND | os.O_CLOEXEC)

  def noc_read(self, addr):  # argsz, flags, x, y, noc, width, addr, value
    return ioctl(self.fd, NOC_READ, "IIHHBB2xQQ", 32, 0, *ARC, 0, 4, addr, 0)[-1]

  def telemetry(self):
    if self.addr is None:
      base, data = self.noc_read(TELEM_PTR), self.noc_read(TELEM_DATA)
      if not base or (self.noc_read(base) >> 16) & 0xFF > 1: raise OSError("no telemetry table")
      n = self.noc_read(base + 4)
      if not 0 < n < 1024: raise OSError("bad telemetry table")
      ents = [self.noc_read(base + 8 + 4 * i) for i in range(n)]
      self.addr = {e & 0xFFFF: data + 4 * (e >> 16) for e in ents}
    return {k: self.noc_read(self.addr[t]) if t in self.addr else None for k, t in TAGS.items()}

  def in_use(self): return bool(ioctl(self.fd, LOCK_CTL, "IIB3xB3x", 4, LOCK_TEST, CHIP_IN_USE, 0)[-1] & 2)
  def reset(self, flag): return ioctl(self.fd, RESET_DEVICE, "IIII", 8, flag, 0, 0)[-1] == 0
  def vote_idle(self): ioctl(self.fd, SET_POWER_STATE, "IIBBH28x", 40, 0, 0, 15, 0)  # 15 flags valid, all off
  def close(self): os.close(self.fd)

class MacCard(Card):
  """Same interface over the TTGPU driver: ARC reads through the SMI TLB window, power votes as ARC messages."""
  def __init__(self, idx):
    self.idx, self.addr = idx, None
    try: self.d = sd.arc_only()
    except RuntimeError as e: raise OSError(str(e)) from None
  def noc_read(self, addr):
    try: return self.d._arc_read32(addr)
    except RuntimeError as e: raise OSError(str(e)) from None
  def card_type(self): return self.d._card()
  def in_use(self): return sd.in_use()
  def vote_idle(self): self.d._set_power(0)
  def close(self): self.d.close()
if DARWIN: Card = MacCard

def one(idx, fn):
  c = Card(idx)
  try: return fn(c)
  finally: c.close()

# ---------------------------------------------------------------- sampling -----

def pcie(idx):
  if DARWIN: return sd.pcie_link()
  dev = f"{SYS}/tenstorrent!{idx}/device"
  def link(kind):
    try: return PCIE_GEN.get(float(rd(f"{dev}/{kind}_link_speed").split()[0])), int(rd(f"{dev}/{kind}_link_width"))
    except (AttributeError, ValueError): return None, None
  return link("current"), link("max")

class Mon:
  def __init__(self, idx):
    self.idx, self.card, self.err, self.retry_at, self.prev_hb = idx, None, None, 0.0, None
    self.type = (one(idx, Card.card_type) if DARWIN else rd(f"{SYS}/tenstorrent!{idx}/tt_card_type")) or "?"
    self.bdf = bdf(idx)
    self.hist = deque(maxlen=120)

  def sample(self):
    t = time.monotonic()
    (gen, width), (max_gen, max_width) = pcie(self.idx)
    s = dict(card=self.idx, pcie_gen=gen, pcie_width=width, pcie_max_gen=max_gen, pcie_max_width=max_width)
    if self.card is None and t >= self.retry_at:
      try: self.card, self.err = Card(self.idx), None
      except OSError as e: self.err, self.retry_at = e.strerror or str(e), t + 5
    if self.card is not None:
      try: s.update(self.card.telemetry())
      except OSError as e:  # reset or removed: reopen later
        self.card.close(); self.card, self.err, self.retry_at = None, e.strerror or str(e), t + 2
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

  def close(self):
    if self.card: self.card.close()

# ---------------------------------------------------------------- drawing ------

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
  if hi - lo < 10: mid = (hi + lo) / 2; lo, hi = mid - 5, mid + 5  # don't amplify 1 W noise
  return ACC + "".join(SPARK[max(0, min(7, int((v - lo) / (hi - lo) * 8)))] for v in vals) + RST

def temp(v, limit):
  if v is None: return "—"
  return (heat(v / limit) if limit and v / limit >= 0.6 else "") + f"{v:.0f}°C" + RST

def render_card(m, s, width):
  dot = {None: DIM + "○", True: OK + "●", False: BAD + "●"}[s.get("alive")] + RST
  link = f"gen{s['pcie_gen']} x{s['pcie_width']}" if s["pcie_gen"] else "pcie ?"
  if (s["pcie_gen"], s["pcie_width"]) != (s["pcie_max_gen"], s["pcie_max_width"]):
    link = f"{WARN}{link}{RST}{DIM} (max gen{s['pcie_max_gen']} x{s['pcie_max_width']}){RST}"
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
  if s["state"] == "boot": alerts.append("never parked: ./smi.py --park")
  if s.get("alive") is False: alerts.append("heartbeat stalled")
  if s["trips"]: alerts.append(f"{s['trips']} thermal trips")
  if s["gddr_ue"]: alerts.append(f"{s['gddr_ue']} uncorrected GDDR errors")
  if alerts: line2 += "   " + WARN + " · ".join(alerts) + RST
  return [head, line1, line2, ""]

def render(mons, samples, args, live=True):
  width = max(72, min(shutil.get_terminal_size((100, 30)).columns, 120))
  hint = f"  every {args.interval:g}s · q to quit" if live else ""
  out = [f" {BOLD}{ACC}smi{RST}{DIM}{hint}{RST}" + " " * max(1, width - 13 - len(hint)) + DIM + time.strftime("%H:%M:%S") + RST, ""]
  for m, s in zip(mons, samples): out += render_card(m, s, width)
  tot = [s["board_w"] for s in samples if s.get("board_w") is not None]
  if len(mons) > 1 and tot: out.append(f" {DIM}total board{RST} {BOLD}{sum(tot)} W{RST}")
  return out

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

# ---------------------------------------------------------------- reset --------

def wait_for(what, cond, timeout, step=0.05):
  end = time.monotonic() + timeout
  while (r := cond()) is None:
    if time.monotonic() > end: raise TimeoutError(f"timed out after {timeout:g}s waiting for {what}")
    time.sleep(step)
  return r

def reset_darwin(force=False):
  if sd.in_use() and not force: sys.exit("card in use by a blackhole-py process; stop it or pass --force")
  t0 = time.monotonic()
  sd.reset()
  c = Card(0)
  try:
    t = wait_for("ARC telemetry", lambda: (lambda t: t if t["hb"] else None)(c.telemetry()), 15)
    c.vote_idle()
  finally: c.close()
  print(f"card 0 ({bdf(0)}): up in {time.monotonic() - t0:.1f}s, board {t['board_w']} W; idle vote sent")

def reset(idxs, sbr=True, dmc=False, force=False):
  if DARWIN:
    if dmc: sys.exit("--dmc isn't supported on macOS")
    return reset_darwin(force)
  bdfs = {i: bdf(i) for i in idxs}
  busy = [i for i in idxs if one(i, Card.in_use)]
  if busy and not force:
    sys.exit(f"card(s) {busy} in use by another process (tt-metal / blackhole-py); stop it or pass --force")

  t0 = time.monotonic()
  if sbr:
    for i in idxs:
      if not one(i, lambda c: c.reset(RESET_PCIE_LINK)): print(f"card {i}: secondary bus reset failed, continuing")
  for i in idxs:
    if not one(i, lambda c: c.reset(ASIC_DMC_RESET if dmc else ASIC_RESET)):
      sys.exit(f"card {i}: {'ASIC+DMC' if dmc else 'ASIC'} reset ioctl failed")
  print(f"reset issued to {', '.join(f'{i} ({bdfs[i]})' for i in idxs)}")
  time.sleep(20 if dmc else max(2, 0.4 * len(idxs)))  # let a hotplug removal happen if it's going to

  failed = []
  for i, b in bdfs.items():
    try:
      def back():
        m = glob.glob(f"/sys/bus/pci/devices/{b}/tenstorrent/tenstorrent!*")
        n = int(m[0].rsplit("!", 1)[1]) if m else None
        return n if n is not None and os.path.exists(f"/dev/tenstorrent/{n}") else None
      n = wait_for(f"{b} to reappear", back, 30)
      def marker_clear():  # KMD sets PCI_COMMAND_PARITY (bit 6) before reset; the chip's reset clears it
        with open(f"/sys/bus/pci/devices/{b}/config", "rb") as f: return True if not os.pread(f.fileno(), 1, 4)[0] & 0x40 else None
      wait_for(f"{b} reset marker to clear", marker_clear, 30)
      if not one(n,lambda c: c.reset(POST_RESET)): raise OSError(f"POST_RESET failed for /dev/tenstorrent/{n}")
      c = Card(n)
      try:
        wait_for("ARC boot", lambda: True if c.noc_read(BOOT_STATUS) & 1 else None, 15)
        def heartbeat():
          try: t = c.telemetry()
          except OSError: c.addr = None; return None
          return t if t["hb"] else None
        t = wait_for("ARC telemetry", heartbeat, 15)
        c.vote_idle()  # nothing else will: the KMD only votes on probe and legacy opens
      finally: c.close()
      print(f"card {i} -> /dev/tenstorrent/{n}: up in {time.monotonic() - t0:.1f}s, board {t['board_w']} W, "
            f"eth link up {ports(t['eth_live'] >> 16)} (not waited for); idle vote sent")
    except (OSError, TimeoutError) as e:
      print(f"card {i} ({b}): {e}"); failed.append(i)
  if failed: sys.exit(1)

# ---------------------------------------------------------------- main ---------

CSV = ["time", "card", "state", "board_w", "core_w", "asic_c", "gddr_c", "fan_rpm", "aiclk", "vcore_mv",
       "pcie_gen", "pcie_width", "pcie_max_gen", "pcie_max_width", "throttle", "gddr_ue", "trips"]

def watch(mons, args):
  live = sys.stdout.isatty() and not args.csv
  keys = live and sys.stdin.isatty()
  count = args.count if args.count is not None else (0 if live else 1)
  if not live:  # one-shot output still wants a heartbeat delta, so prime once
    for m in mons: m.sample()
    time.sleep(0.25)
  signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt))
  old_tc = termios.tcgetattr(sys.stdin) if keys else None
  w = csv.writer(sys.stdout, lineterminator="\n")
  if args.csv: w.writerow(CSV)
  if live: sys.stdout.write(E + "?1049h" + E + "?25l")  # alt screen, hide cursor
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
  ap.add_argument("-r", "--reset", nargs="*", type=int, metavar="IDX", help="reset these cards (default all)")
  ap.add_argument("--dmc", action="store_true", help="with -r: also reset the board-management MCU (~20 s)")
  ap.add_argument("--no-sbr", action="store_true", help="with -r: skip the PCIe secondary bus reset")
  ap.add_argument("--force", action="store_true", help="with -r: reset even if another process holds the card")
  ap.add_argument("--park", action="store_true", help="vote idle so the KMD powers the cards down")
  args = ap.parse_args()

  all_idx = cards()
  if not all_idx: sys.exit("no 'ttgpu' IOService (card connected and TTGPU driver enabled?)" if DARWIN
                           else f"no cards under {SYS} (is tt-kmd loaded?)")
  idxs = sorted(set(args.reset or args.device or all_idx))
  if bad := [i for i in idxs if i not in all_idx]: sys.exit(f"no such card(s): {bad}")
  if args.reset is not None: return reset(idxs, sbr=not args.no_sbr, dmc=args.dmc, force=args.force)
  if args.park:
    if DARWIN and sd.in_use() and not args.force: sys.exit("card in use by a blackhole-py process; --park would cut its power")
    for i in idxs: one(i, Card.vote_idle)
    return print(f"idle vote sent to {idxs}; the KMD powers them down in ~5 s unless a client wants power")
  watch([Mon(i) for i in idxs], args)

if __name__ == "__main__":
  main()
