"""Measure single-card and cable-backed TP decode alongside independent tt-smi sampling."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import numpy as np
from examples.llama3_8b_fp8 import Llama3Decode
from distributed.tp2.fast import L1TensorParallelDecode


def power_summary(samples, start, end, tokens):
    cards = {}
    for card in (0,1):
        rows = [r for sample in samples for r in sample['cards'] if r['device']==card]
        times = np.array([r['monotonic'] for r in rows])
        inside = (times>=start)&(times<=end)
        if inside.sum()<10 or times[0]>start or times[-1]<end:
            raise RuntimeError('insufficient power samples spanning inference')
        result = dict(samples=int(inside.sum()))
        for field in ('board_watts','asic_watts'):
            if any(r[field] is None for r in rows):
                result[field] = None
                continue
            values = np.array([r[field] for r in rows],dtype=float)
            x = np.concatenate(([start],times[inside],[end]))
            y = np.interp(x,times,values)
            joules = float(np.trapezoid(y,x))
            result[field] = dict(mean=joules/(end-start),peak=float(values[inside].max()),
                                joules=joules,joules_per_token=joules/tokens)
        cards[str(card)] = result
    total_j = sum(row['board_watts']['joules'] for row in cards.values())
    return dict(cards=cards, combined_mean_board_watts=total_j/(end-start),
                combined_board_joules=total_j,combined_board_joules_per_token=total_j/tokens)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps',type=int,default=1024)
    parser.add_argument('--output',type=Path,default=Path('validation/tp2-power.json'))
    parser.add_argument('--telemetry-python',default='/home/boop/tenstorrent/.venv/bin/python')
    args = parser.parse_args()
    if not 64<=args.steps<=8000: parser.error('steps must be 64..8000')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    raw = args.output.with_suffix('.jsonl')
    raw.write_text('')
    sampler = subprocess.Popen([args.telemetry_python,str(Path(__file__).with_name('sample_power.py')),
                                '--output',str(raw)])
    phases = []
    runs = {}
    try:
        deadline = time.monotonic()+10
        while not raw.exists() or raw.stat().st_size==0:
            if sampler.poll() is not None: raise RuntimeError('power sampler exited')
            if time.monotonic()>deadline: raise TimeoutError('power sampler startup')
            time.sleep(.05)
        for transport in ('single','tp2'):
            started=time.monotonic()
            runtime = Llama3Decode(device_index=1) if transport=='single' else L1TensorParallelDecode()
            phases.append(dict(name=transport+'_load',start=started,end=time.monotonic()))
            try:
                token=9906
                if transport=='single': runtime.load_tokens([128000,9906])
                started=time.monotonic()
                for position in range(66):
                    if transport=='single': token=runtime.decode(position,append=position>=1)[0]
                    else:
                        input_token = (128000,9906)[position] if position<2 else token
                        token=runtime.decode(input_token,position)['token']
                phases.append(dict(name=transport+'_warmup',start=started,end=time.monotonic()))
                start=time.monotonic()
                for position in range(66,66+args.steps):
                    if transport=='single': token=runtime.decode(position,append=True)[0]
                    else: token=runtime.decode(token,position)['token']
                end=time.monotonic()
                phases.append(dict(name=transport+'_generation',start=start,end=end))
                runs[transport]=dict(start=start,end=end,tokens=args.steps,seconds=end-start,tps=args.steps/(end-start))
                print(f'{transport}: {args.steps/(end-start):.2f} tokens/s',flush=True)
            finally: runtime.close()
        time.sleep(.3)  # One sample after the final phase for boundary interpolation.
    finally:
        sampler.terminate()
        sampler.wait(timeout=10)
        args.output.with_suffix('.phases.json').write_text(json.dumps(phases,indent=2)+'\n')
    samples=[json.loads(line) for line in raw.read_text().splitlines()]
    for run in runs.values(): run.update(power_summary(samples,run['start'],run['end'],run['tokens']))
    report=dict(runs=runs,speedup=runs['tp2']['tps']/runs['single']['tps'],
        sampling_interval_seconds=.1, source='tt-smi backend INPUT_POWER (total board) and TDP (ASIC)',
        initial_tokens=[128000,9906],
        timing='Independent continuous batch-one greedy decode from the same initial tokens, after 66 warmup tokens; fixed token count, including continuation after EOS; no full-logit readbacks.',
        energy='Time-integrated board telemetry; includes board idle draw, excludes host CPU/system. Single run combined power includes the idle second card.',
        raw_samples=str(raw),phases=phases)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__': main()
