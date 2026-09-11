"""Timestamp every launch in real decode traces on one and two P150s.

Markers add dispatch/PCIe overhead, so compare instrumented sums to ordinary
throughput; these are attribution measurements, not headline benchmarks.
"""
import argparse
from collections import defaultdict
import functools
import json
from pathlib import Path
import statistics
import struct
from examples.llama3_8b_fp8 import Llama3Decode
from distributed.tp2.fast import FastRank, L1TensorParallelDecode


class ProfileMixin:
    def _queue(self, name, *args, **kwargs):
        self.names.append(name)
        return super()._queue(name, *args, **kwargs)

    def _build_programs(self):
        self.names = []
        original = self.device.capture_trace
        self.device.capture_trace = functools.partial(original, profile=True)
        try: super()._build_programs()
        finally: self.device.capture_trace = original


class ProfileSingle(ProfileMixin, Llama3Decode): pass
class ProfileRank(ProfileMixin, FastRank): pass
class ProfileParallel(L1TensorParallelDecode): rank_type = ProfileRank


def read_markers(runtime, trace):
    stamps = [struct.unpack('<Q', runtime.device.pcie.sysmem.read(offset+8,8))[0]
              for offset in trace.marker_offsets]
    if len(stamps) != len(runtime.names)+1: raise RuntimeError('marker count mismatch')
    groups = defaultdict(float)
    for name, left, right in zip(runtime.names, stamps, stamps[1:]):
        groups[name] += (right-left)/1350
    return dict(groups)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('validation/tp2-profile.json'))
    parser.add_argument('--context',type=int,default=64)
    args = parser.parse_args()
    results = {}
    single = ProfileSingle(device_index=1)
    try:
        single.load_tokens([128000]+[9906]*(args.context+8))
        samples = []
        for position in range(args.context+8):
            single.decode(position)
            if position >= args.context:
                samples.append(read_markers(single, single.decode_trace))
        results['single_card_kernel_us'] = {key:statistics.median(r[key] for r in samples) for key in samples[0]}
        print(json.dumps(results),flush=True)
    finally: single.close()
    parallel = ProfileParallel()
    try:
        samples = [[],[]]
        erisc = [[],[]]
        for position in range(args.context+8):
            parallel.decode(128000 if position==0 else 9906,position)
            if position >= args.context:
                for rank in (0,1):
                    samples[rank].append(read_markers(parallel.ranks[rank], parallel.ranks[rank].trace))
                    cycles=struct.unpack('<4I',parallel.link.tiles[rank].read(0x60600,16))
                    assert cycles[3]==(position+1)*64
                    erisc[rank].append(dict(zip(('producer_wait','exchange','consumer_and_credit'),[v/1350 for v in cycles[:3]])))
        results['tp_card_kernel_us'] = [{key:statistics.median(r[key] for r in rows) for key in rows[0]} for rows in samples]
        results['erisc_us_per_token'] = [{key:statistics.median(r[key] for r in rows) for key in rows[0]} for rows in erisc]
    finally: parallel.close()
    results.update(context=args.context, clock_mhz=1350,
        note='Real trace device timestamps with one marker per launch; includes marker/dispatch overhead. ERISC intervals overlap Tensix work; do not sum them with kernel intervals.')
    args.output.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2),flush=True)


if __name__=='__main__': main()
