import sys,json
for l in sys.stdin:
  try: r=json.loads(l); L=r['label']; print(f"{L['dir']:6} {L['noc']:5} {str(L['ports']):7} posted={L['posted']!s:5} c={L.get('cores')} total={r['gb_s']:6} R={r['read_gb_s']:6} W={r['write_gb_s']:6} tags={r['tags']}")
  except Exception: print(l.rstrip()[-300:])
