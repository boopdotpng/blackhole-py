"""Matched-history single-P150 versus two-P150 L1 decode benchmark.

Both measurements include host launch and greedy-token readback. Weight load,
prompt ingestion and optional diagnostic full-logit reads are excluded from
generation throughput. TP consumes baseline history so every comparison has
the same context, even if a greedy choice differs.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from transformers import AutoTokenizer
from examples.llama3_8b_fp8 import Llama3Decode
from distributed.tp2.fast import L1TensorParallelDecode
from distributed.tp2.link import Link
from distributed.tp2.runtime import k

PROMPTS = ('What is the capital of France? Answer in one short sentence.',
           'Explain why the sky is blue.',
           'Write a Python function that returns the Fibonacci sequence.')


def unpack_logits(runtime):
    compact = runtime.logits.to_numpy(runtime.device.read(runtime.logits))
    return np.concatenate([row[:count] for row, count in zip(compact, runtime.lm_weight.item_counts)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=64)
    parser.add_argument('--output', type=Path, default=Path('validation/tp2-comparison.json'))
    args = parser.parse_args()
    if args.steps < 1: parser.error('--steps must be positive')
    tokenizer = AutoTokenizer.from_pretrained('weights/llama3-8b-fp8', local_files_only=True)
    cases, references = [], {}
    before = time.perf_counter()
    single = Llama3Decode(device_index=1)
    baseline_startup = time.perf_counter()-before
    try:
        for index, prompt in enumerate(PROMPTS):
            ids = tokenizer.apply_chat_template([{'role':'user','content':prompt}],
                tokenize=True, add_generation_prompt=True)
            if not isinstance(ids, list): ids = ids['input_ids']
            if ids and isinstance(ids[0], list): ids = ids[0]
            length = len(ids)
            if length + args.steps > 8191: raise ValueError('history exceeds cache')
            single.load_tokens(ids)
            history, tokens, seconds = list(ids), [], []
            samples = {0, length-1, 31, 32, 63, 64, length+args.steps-2}
            for position in range(length+args.steps-1):
                generating = position >= length-1
                started = time.perf_counter()
                token, _ = single.decode(position, append=generating)
                elapsed = time.perf_counter()-started
                tokens.append(token)
                if generating:
                    seconds.append(elapsed)
                    if position < length+args.steps-2: history.append(token)
                if position in samples:
                    references[f'{index}:{position}'] = unpack_logits(single)
            row = dict(prompt=prompt, prompt_length=length, history=history,
                baseline_tokens=tokens, baseline_seconds=seconds,
                baseline_tps=len(seconds)/sum(seconds))
            cases.append(row)
            print(f'Baseline prompt {index}: {row["baseline_tps"]:.2f} tok/s', flush=True)
    finally: single.close()
    before = time.perf_counter()
    parallel = L1TensorParallelDecode()
    tp_startup = time.perf_counter()-before
    try:
        for index, case in enumerate(cases):
            if index:
                parallel.link.close()
                parallel.link = Link(service='collective', producers=k.LLAMA_CORES)
                parallel.next_position = 0
            seconds, rows = [], []
            for position, input_token in enumerate(case['history']):
                key = f'{index}:{position}'
                result = parallel.decode(int(input_token), position, return_logits=key in references)
                if position >= case['prompt_length']-1: seconds.append(result['seconds'])
                row = dict(position=position, baseline_token=case['baseline_tokens'][position],
                           tp_token=result['token'], seconds=result['seconds'])
                if key in references:
                    expected, actual = references[key], result['logits']
                    row.update(relative_rms=float(np.linalg.norm(actual-expected)/np.linalg.norm(expected)),
                        pcc=float(np.corrcoef(actual, expected)[0,1]),
                        max_abs_error=float(np.max(np.abs(actual-expected))))
                rows.append(row)
            case.update(tp_tps=len(seconds)/sum(seconds), tp_seconds=seconds, comparisons=rows,
                        token_matches=sum(r['baseline_token']==r['tp_token'] for r in rows))
            case['speedup'] = case['tp_tps']/case['baseline_tps']
            print(f'TP prompt {index}: {case["tp_tps"]:.2f} tok/s, '
                  f'{case["speedup"]:.3f}x, {case["token_matches"]}/{len(rows)} token matches', flush=True)
    finally: parallel.close()
    base_s = sum(sum(case['baseline_seconds']) for case in cases)
    tp_s = sum(sum(case['tp_seconds']) for case in cases)
    samples = [r for c in cases for r in c['comparisons'] if 'pcc' in r]
    count = len(cases)*args.steps
    report = dict(steps_per_prompt=args.steps, baseline_device=1, tp_devices=[0,1],
        baseline_startup_seconds=baseline_startup, tp_startup_seconds=tp_startup,
        transport='Tensix L1 -> ERISC L1 -> cable -> peer ERISC L1 -> Tensix FP32 reduction',
        timing='generation decode wall time; excludes startup, prefill and full-logit diagnostics',
        baseline_tps=count/base_s, tp_tps=count/tp_s, speedup=base_s/tp_s,
        max_relative_rms=max(r['relative_rms'] for r in samples),
        min_pcc=min(r['pcc'] for r in samples), cases=cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    np.savez(args.output.with_suffix('.npz'), **references)
    print(json.dumps({key:value for key,value in report.items() if key!='cases'}, indent=2), flush=True)
    if report['min_pcc'] < .99 or report['max_relative_rms'] > .05:
        raise SystemExit('logit comparison failed (PCC .99 / relative RMS .05)')


if __name__ == '__main__': main()
