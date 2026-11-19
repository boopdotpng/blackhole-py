#!/bin/bash
# drive.sh CARD "probe|-k a -k b|outname" ...   run steps in order; on a hard failure reset the card, retry the
# broken case once, and if it breaks again skip it (reset again) and carry on. Logs to stdout.
cd "$(dirname "$0")/../.." || exit 1
CARD=$1; shift
R=${PREFIX:-sims/results/$(date +%F)}
reset() { echo "### $(date +%T) RESET card $CARD"; python3 smi.py -r "$CARD" 2>&1 | tail -3; sleep 5; }
last_hard() { python3 -c "
import json,sys
ids=[json.loads(l) for l in open(sys.argv[1])]
h=[r['id'] for r in ids if r.get('failure')=='hard']
print(h[-1] if h else '')" "$1.failed" 2>/dev/null; }
for step in "$@"; do
  IFS='|' read -r probe ks name <<<"$step"
  out=$R-$name-card$CARD.jsonl
  echo "### $(date +%T) STEP $probe $ks -> $out"
  for attempt in $(seq 1 60); do
    if [ "$probe" = launch ]; then python3 sims/probes/launch.py --device "$CARD" --output "$out"; rc=$?
    else python3 sims/probes/run.py --device "$CARD" --output "$out" ${QUIET:+--quiet} $probe $ks; rc=$?; fi
    [ $rc -eq 0 ] && break
    bad=$(last_hard "$out")
    echo "### $(date +%T) HARD rc=$rc at '${bad}'"
    reset
    [ $rc -ne 1 ] || [ -z "$bad" ] || [ "$probe" = launch ] && continue
    echo "### $(date +%T) RETRY $bad"
    python3 sims/probes/run.py --device "$CARD" --output "$out" ${QUIET:+--quiet} $probe $ks -k "$bad" --retry-failed; rc2=$?
    if [ $rc2 -ne 0 ]; then echo "### $(date +%T) RETRY FAILED $bad -> skipping it"; reset
    else echo "### $(date +%T) RETRY OK $bad"; fi
  done
done
echo "### $(date +%T) ALL DONE card $CARD"
