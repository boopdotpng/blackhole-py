#!/usr/bin/env python3
"""Resumable probe runner. One process, one PCIe open; never resets the card.

  python3 sims/probes/run.py --device 1 --output sims/results/2026-11-18-noc-events-card1.jsonl events [-k single-write]

A probe module (events.py, ...) defines CASES (dicts with a unique 'id' and the 'tiles' they touch) and
run(card, case, timeout) -> dict. Results append to --output (one JSON line per case, keyed by 'id'); failures to
<output>.failed.

  soft  KernelTimeout: the kernel's own bounded wait gave up and it returned to firmware. Recorded, the run continues.
  hard  anything else (HostTimeout: a tile never came back; an exception): stop at once, leave the tiles as they
        are, don't touch the card again. Look at it (python3 smi.py -d N), reset by hand if needed
        (python3 smi.py -r N), then rerun the same command: it resumes after the case that broke.

Before opening the card, one read-only `smi.py --csv` sample must show telemetry, no uncorrected GDDR errors and
no thermal trips.
"""
import argparse, csv, importlib, json, os, subprocess, sys, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))


def card_ok(device):
  try:
    r = subprocess.run([sys.executable, 'smi.py', '--csv', '-d', str(device)], cwd=ROOT, capture_output=True,
                       text=True, timeout=15)
    rows = list(csv.DictReader(r.stdout.splitlines()))
  except (OSError, subprocess.TimeoutExpired) as e:
    return False, f'smi.py failed: {e}'
  if not rows: return False, f'smi.py gave no sample: {(r.stderr or r.stdout).strip()[-300:]}'
  row = rows[-1]
  summary = ' '.join(f'{k}={row.get(k)}' for k in ('state', 'aiclk', 'asic_c', 'board_w', 'pcie_gen', 'pcie_width'))
  if not row.get('state') or not row.get('aiclk'): return False, f'no telemetry ({summary})'
  if row.get('gddr_ue') not in ('', '0'): return False, f"{row['gddr_ue']} uncorrected GDDR errors"
  if row.get('trips') not in ('', '0'): return False, f"{row['trips']} thermal trips"
  return True, summary


def ids_in(path, kind=None):
  p, out = Path(path), set()
  if not p.exists(): return out
  for line in p.read_text().splitlines():
    try: r = json.loads(line)
    except ValueError: continue
    if 'id' in r and (kind is None or r.get('failure') == kind): out.add(r['id'])
  return out


def append(path, rec):
  with Path(path).open('a') as f: f.write(json.dumps(rec, sort_keys=True) + '\n')


class _Stop(Exception): pass


class _DryCard:
  """Stands in for tile.Card in a prebuild dry run: launches do nothing and every read returns zeros, so a case's run()
  goes on to the images it builds after its first launch. A case stops after `limit` card calls (no endless polls)."""
  def __init__(self, index, limit=2000):
    self.index, self.quiet, self.quiet_applied, self.quiet_roles, self.iface, self.limit, self.calls = \
      index, False, False, None, self, limit, 0
  workers = type('All', (), {'__contains__': lambda self, t: True, '__iter__': lambda self: iter([(1, 2)])})()
  def _tick(self):
    self.calls += 1
    if self.calls > self.limit: raise _Stop()
  def log(self, tile, n, role='brisc'): self._tick(); return (0,) * n
  def aux(self, tile, n, role='brisc'): self._tick(); return (0,) * n
  def read(self, tile, addr, n): self._tick(); return bytes(n)
  def read32(self, tile, addr): self._tick(); return 0
  def __getattr__(self, name):  # run, launch, wait, write, write32, clock, ...
    def call(*a, **k): self._tick(); return 0
    return call


def prebuild(mod, cases, jobs):
  """Dry-run every case with fw.compile recording instead of compiling, then compile what it recorded in parallel
  (into the on-disk cache, so the real run finds every image built). Runs in its own process (see main)."""
  import fw
  from concurrent.futures import ThreadPoolExecutor
  fw.images()  # real firmware first: images() is memoised
  real, calls = fw.compile, {}
  def record(srcs, slot, flags=["-Os"]):
    calls[(tuple(map(str, srcs)), tuple(slot), tuple(flags))] = None
    return bytes(64)
  fw.compile = record
  try:
    for c in cases:
      try: mod.run(_DryCard(0), c, c.get('timeout', 0.25))
      except Exception: pass
  finally: fw.compile = real
  t0 = time.monotonic()
  with ThreadPoolExecutor(jobs) as ex: list(ex.map(lambda k: real(list(k[0]), k[1], list(k[2])), calls))
  print(f'prebuild: {len(calls)} images for {len(cases)} cases ({jobs} jobs) in {time.monotonic() - t0:.1f} s', flush=True)


def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--device', type=int, required=True)
  ap.add_argument('--output', required=True)
  ap.add_argument('probe', help='probe module in sims/probes, e.g. events')
  ap.add_argument('-k', action='append', default=[], help='only cases whose id contains this (repeat = all must match)')
  ap.add_argument('--timeout', type=float, default=0.25, help='host timeout per launch, s (a case may set its own)')
  ap.add_argument('--limit', type=int, default=0, help='run at most N pending cases')
  ap.add_argument('--retry-failed', action='store_true')
  ap.add_argument('--quiet', action='store_true', help='roles a probe does not use spin in registers (k_quiet.c) '
                  'instead of polling L1 in firmware')
  ap.add_argument('--list', action='store_true', help='print pending cases and exit (does not open the card)')
  ap.add_argument('--jobs', type=int, default=os.cpu_count(), help='parallel kernel builds before the run (0: build lazily)')
  ap.add_argument('--prebuild-only', action='store_true', help=argparse.SUPPRESS)
  a = ap.parse_args()

  from tile import Card, KernelTimeout
  mod = importlib.import_module(a.probe)
  out, failed_path = Path(a.output).resolve(), Path(a.output + '.failed').resolve()
  cases = [c for c in mod.CASES if all(k in c['id'] for k in a.k)]
  done, failed = ids_in(out), ids_in(failed_path)
  todo = [c for c in cases if c['id'] not in done and (a.retry_failed or c['id'] not in failed)]
  if a.limit: todo = todo[:a.limit]
  print(f'{len(cases)} selected, {sum(c["id"] in done for c in cases)} done, '
        f'{sum(c["id"] in failed for c in cases)} failed before, {len(todo)} to run', flush=True)
  if a.list:
    for c in todo: print(' ', c['id'])
    return 0
  if not todo: return 0
  if a.prebuild_only: return prebuild(mod, todo, a.jobs) or 0
  if a.jobs:  # in a child process, so the dry run cannot leave state behind in this one
    subprocess.run([sys.executable, __file__, *sys.argv[1:], '--prebuild-only'], check=False)

  good, reason = card_ok(a.device)
  print(f'card {a.device}: {reason}', flush=True)
  if not good: return print(f'card {a.device} looks unhealthy; not opening it') or 2

  out.parent.mkdir(parents=True, exist_ok=True)
  card, hard, n_ok, n_soft, t0 = None, None, 0, 0, time.monotonic()
  try:
    card = Card(a.device)
    card.quiet = a.quiet
    for i, case in enumerate(todo):
      tag = f'[{i + 1}/{len(todo)}] {case["id"]}'
      missing = [t for t in case.get('tiles', ()) if t not in card.workers]
      if missing:
        append(failed_path, dict(id=case['id'], failure='skip', error=f'tiles not present: {missing}', time=time.time()))
        print(f'{tag}  skip (no tile {missing})', flush=True)
        continue
      try:
        rec = mod.run(card, case, case.get('timeout', a.timeout))
      except KernelTimeout as e:
        n_soft += 1
        append(failed_path, dict(id=case['id'], failure='soft', error=str(e), time=time.time()))
        print(f'{tag}  soft: {e}', flush=True)
        continue
      except BaseException as e:
        hard = (case, e)
        if not isinstance(e, KeyboardInterrupt):
          append(failed_path, dict(id=case['id'], failure='hard', error=f'{type(e).__name__}: {e}'[:500], time=time.time()))
        raise
      n_ok += 1
      meta = {k: v for k, v in case.items() if k not in ('tiles', 'timeout')}
      append(out, dict(meta, **rec, card=a.device, probe=a.probe, quiet=card.quiet_applied, time=time.time()))
      if 'median' in rec: print(f'{tag}  median {rec["median"]}', flush=True)
      elif 'total_median' in rec: print(f'{tag}  {rec["bytes_per_cycle"]:.1f} B/cyc', flush=True)
      else: print(f'{tag}  ok', flush=True)
  except BaseException as e:
    if hard is None: hard = (None, e)
    traceback.print_exc()
  finally:
    if card is not None:
      try: card.close(hold=hard is None)  # after a hard failure leave the tiles exactly as they are
      except Exception as e: print(f'close: {e}')

  print(f'\n{n_ok} recorded, {n_soft} soft failures, {"1 hard failure" if hard else "no hard failure"}; '
        f'{time.monotonic() - t0:.2f} s')
  if hard:
    case, e = hard
    good, reason = card_ok(a.device)
    print(f'STOPPED at {case["id"] if case else "(setup)"}: {type(e).__name__}: {e}')
    print(f'card {a.device}: {"telemetry ok" if good else "UNHEALTHY"} ({reason}). Nothing was reset.')
    print(f'  watch:   python3 smi.py -d {a.device}')
    print(f'  reset:   python3 smi.py -r {a.device}   (by hand, only if needed)')
    print('  resume:  rerun the same command (the broken case is skipped; --retry-failed to rerun it)')
    return 1
  return 0


if __name__ == '__main__':
  sys.exit(main())
