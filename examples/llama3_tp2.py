"""Run experimental mixed FP8/BF16 TP=2 decode on two cabled P150s."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from transformers import AutoTokenizer
from distributed.tp2.runtime import TensorParallelDecode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--devices', nargs=2, type=int, default=(0, 1))
    parser.add_argument('--weights', default='weights/llama3-8b-fp8')
    parser.add_argument('--prompt', default='The capital of France is')
    parser.add_argument('--steps', type=int, default=4)
    parser.add_argument('--transport', choices=('host', 'l1'), default='l1')
    parser.add_argument('--output', type=Path, default=Path('validation/tp2-run.json'))
    parser.add_argument('--reference', type=Path, help='NPZ logits for the same history, keyed by position')
    parser.add_argument('--tokens', type=Path, help='JSON token list for teacher-forced validation')
    args = parser.parse_args()
    if args.steps < 1: parser.error('--steps must be positive')
    tokenizer = AutoTokenizer.from_pretrained(args.weights, local_files_only=True)
    ids = json.loads(args.tokens.read_text()) if args.tokens else tokenizer.encode(args.prompt, add_special_tokens=True)
    if not ids or len(ids) + args.steps > 8192: parser.error('invalid history length')
    reference = np.load(args.reference) if args.reference else None
    started = time.perf_counter()
    if args.transport == 'l1':
        from distributed.tp2.fast import L1TensorParallelDecode
        runtime_class = L1TensorParallelDecode
    else:
        runtime_class = TensorParallelDecode
    runtime = runtime_class(args.weights, tuple(args.devices))
    startup = time.perf_counter() - started
    rows, saved, generated = [], {}, []
    try:
        for position in range(len(ids) + args.steps - 1):
            token = ids[position] if position < len(ids) else generated[-1]
            result = runtime.decode(int(token), position, return_logits=True)
            logits = result.pop('logits')
            saved[str(position)] = logits
            row = dict(position=position, input_token=int(token), **result)
            if reference is not None and str(position) in reference:
                expected = reference[str(position)].astype('f4')
                row.update(reference_token=int(expected.argmax()),
                    relative_rms=float(np.linalg.norm(logits - expected) / max(np.linalg.norm(expected), 1e-30)),
                    max_abs_error=float(np.max(np.abs(logits - expected))))
            rows.append(row)
            if position >= len(ids) - 1: generated.append(result['token'])
            print(json.dumps(row), flush=True)
        generation = rows[len(ids)-1:]
        report = dict(transport=args.transport,
            devices=args.devices, startup_seconds=startup,
            tokens_per_second=len(generation) / sum(r['seconds'] for r in generation),
            prompt_tokens=ids, generated_tokens=generated,
            text=tokenizer.decode(generated), rows=rows)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        np.savez(args.output.with_suffix('.npz'), **saved)
        print(report['text'], flush=True)
        print(f"{report['tokens_per_second']:.2f} tok/s ({args.transport} transport)", flush=True)
    finally:
        runtime.close()


if __name__ == '__main__': main()
