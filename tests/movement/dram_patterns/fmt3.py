import sys,json
for l in sys.stdin:
  try: r=json.loads(l); print(f"{str(r['label'])[:44]:44} total={r['gb_s']:6} R={r['read_gb_s']:6} W={r['write_gb_s']:6} per-dir={r['tags']}")
  except Exception: print(l.rstrip()[-300:])
