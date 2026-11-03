"""Regenerate the reviewed Tensix timing reference: python -m tests.timing.tensix_catalog.

Numbers are backend cycles, not RISC-V instruction costs. No hardware access.
Every public encoder must be classified explicitly; missing entries are errors.
"""
import json
from pathlib import Path
import subprocess

from ttko.isa import Tensix

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
DOCS = WORKSPACE / 'tt-isa-documentation'
BH = 'BlackholeA0/TensixTile/TensixCoprocessor/'
WH = 'WormholeB0/TensixTile/TensixCoprocessor/'
LLK = 'tt_llk_blackhole/instructions/assembly.yaml'


def build():
    records = {}

    def add(names, unit, latency, interval, basis, note, source):
        for name in names.split():
            assert name not in records, name
            records[name] = dict(instruction=name, unit=unit, latency_cycles=latency,
                                 issue_interval_cycles=interval, basis=basis, notes=note,
                                 source=source)

    add('SFPABS SFPAND SFPARECIP SFPCAST SFPCOMPC SFPCONFIG SFPDIVP2 SFPENCC '
        'SFPEXEXP SFPEXMAN SFPGT SFPIADD SFPLE SFPLOAD SFPLOADI SFPLZ SFPMOV '
        'SFPNOP SFPNOT SFPOR SFPPOPC SFPPUSHC SFPSETCC SFPSETEXP SFPSETMAN '
        'SFPSETSGN SFPSTOCHRND SFPSTORE SFPTRANSP SFPXOR SFPSHFT',
        'SFPU', '1', '1', 'Blackhole manual',
        'Ordinary direct mode; 32 lanes per instruction. Dst access, resource conflicts and macros can add stalls.', BH+'VectorUnit.md')
    add('SFPADD SFPADDI SFPMAD SFPMUL SFPMULI SFPMUL24 SFPLUT SFPLUTFP32',
        'SFPU', '2', '1', 'Blackhole manual',
        'Dependent consumer needs a 2-cycle separation; independent instructions can issue each cycle. Indirect operands and macro hazards require additional care.', BH+'VectorUnit.md')
    add('SFPSWAP', 'SFPU', '2', '2 useful ops', 'Blackhole manual',
        'Next SFPU slot permits only SFPNOP; SWAP+SFPNOP costs 2 cycles total, not 3.', BH+'SFPSWAP.md')
    add('SFPSHFT2', 'SFPU', '1 or 2', '1 or 2', 'Blackhole manual',
        'Bit shifts: 1. Lane shuffle modes 2/3/4: 2; next SFPU slot permits only SFPNOP.', BH+'SFPSHFT2.md')
    add('SFPLOADMACRO', 'SFPU', '1 load; scheduled tail', '>=1', 'Blackhole manual',
        'Expand configured sub-ops and delays. Cycle-delay tail ends at max(1+delay+op_latency); instruction-count delays need the actual stream. Internal hazards are not automatically interlocked.', BH+'SFPLOADMACRO.md')

    add('MVMUL DOTPV GAPOOL ELWMUL GMPOOL ELWADD ELWSUB', 'FPU', '5', '1', 'shared manual',
        'Rotate through >=5 independent aligned 8x16 Dst blocks for accumulating ops. Reusing a dependent block costs about 5 cycles/op. Count each fidelity phase separately.', BH+'MatrixUnit.md')
    add('SETRWC INCRWC CLEARDVALID CLREXPHIST GATESRCRST SHIFTXA ZEROACC ZEROSRC TRNSPSRCB',
        'FPU', '1', '1', 'shared manual', 'Subject to source ownership and backend resource readiness.', BH+'MatrixUnit.md')
    add('SHIFTXB', 'FPU', '2', '2', 'shared manual', 'Not a one-cycle source shift.', BH+'MatrixUnit.md')
    add('MOVA2D MOVB2D MOVDBGA2D', 'FPU', '4', '1', 'shared manual',
        'Only selected instructions hide latency; avoid consuming the written Dst region for the next 3 cycles.', BH+'MatrixUnit.md')
    add('MOVB2A', 'FPU', '4', '1', 'shared manual',
        'Table gives 4-cycle latency; next FPU cycle accepts only MOVD2A or MOVB2A. Do not model as unrestricted pipelining.', BH+'MOVB2A.md')
    add('MOVD2A', 'FPU', '2', '1', 'shared manual',
        'Next FPU cycle accepts only MOVD2A or MOVB2A.', BH+'MOVD2A.md')
    add('MOVD2B', 'FPU', '~4', '1 (same op)', 'scheduling inference',
        'Next 3 cycles accept only MOVD2B in FPU; allow 4 cycles before a different FPU instruction.', BH+'MOVD2B.md')
    add('MOVDBGB2D', 'FPU', '~4', '~1', 'analogy estimate',
        'Debug SrcB-to-Dst move: estimate from MOVB2D, unmeasured; debug bypasses ready signals.', LLK)
    add('APOOL3S1 APOOL3S2 CONV3S1 CONV3S2 MFCONV3S1 MPOOL3S1 MPOOL3S2',
        'FPU legacy', '~5', '~1', 'legacy analogy estimate',
        'Noncontractual legacy operations; estimate only from FPU pipeline. Not a supported convolution/pooling timing guarantee.', BH+'MatrixUnit.md')
    add('TRNSPSRCA RAREB', 'FPU legacy', 'unknown', 'unknown', 'unknown',
        'LLK names the operation but supplies no dependable timing. Requires a dedicated behavior/timing probe.', LLK)
    add('SETASHRMH SETASHRMH0 SETASHRMH1 SETASHRMV SETIBRWC SETPKEDGOF',
        'FPU control', '~1', '~1', 'analogy estimate',
        'LLK describes mask/counter/control writes; assume one backend slot for rough budgeting only. Not measured.', LLK)

    add('ADDDMAREG SUBDMAREG MULDMAREG BITWOPDMAREG SHIFTDMAREG CMPDMAREG',
        'scalar', '3 or 4', '3 or 4', 'Wormhole estimate; Blackhole measured',
        '3 for immediate or operands in same aligned group of 4 GPRs; 4 across groups. Nonpipelined, blocks issuing thread.', WH+'ScalarUnit.md')
    add('DMANOP SETDMAREG', 'scalar', '1', '1', 'shared/manual + measured',
        'SETDMAREG immediate mode. Nonpipelined scalar unit; resource contention can add issue gaps.', WH+'ScalarUnit.md')
    add('REG2FLOP', 'scalar', '>=2', '>=2', 'Wormhole estimate',
        'Usually 2; config contention extends occupancy and blocks issuing thread.', WH+'REG2FLOP_ADC.md')
    add('FLUSHDMA', 'scalar', '>=2 + wait', '>=2 + wait', 'Wormhole estimate',
        'Blocks scalar unit and issuing thread until selected work completes.', WH+'FLUSHDMA.md')
    add('STOREIND STOREREG ATSWAP', 'scalar/memory', '>=3 issue; completion variable', '>=3', 'Wormhole estimate',
        'At least 3 scalar occupancy cycles; memory service/visibility and contention need separate completion dependencies.', WH+'ScalarUnit.md')
    add('LOADIND LOADREG ATINCGET', 'scalar/memory', '>=3 issue; result later', '>=3', 'Wormhole estimate',
        'Load result is asynchronous; do not use 3 as result-ready latency. Wait for completion before consuming GPR.', WH+'ScalarUnit.md')
    add('ATCAS ATINCGETPTR', 'scalar/memory', '>=15 per attempt', '>=15 + retries', 'Wormhole estimate',
        'Retries until comparison/FIFO condition succeeds; can block indefinitely, plus L1 contention.', WH+'ScalarUnit.md')
    add('RSTDMA', 'scalar legacy', 'unknown', 'unknown', 'unknown',
        'Legacy TDMA reset encoder; no defensible completion bound.', LLK)

    add('ADDRCRXY ADDRCRZW INCADCXY INCADCZW SETADC SETADCXX SETADCXY SETADCZW SETDVALID NOP',
        'misc', '1', '1 per thread', 'Wormhole estimate',
        'Misc unit accepts one instruction per thread per cycle; NOP additionally measured on Blackhole.', WH+'MiscellaneousUnit.md')
    add('SETC16', 'config', '1', '1 per thread', 'Blackhole manual',
        'Up to 3 across threads; separate from shared config pipeline. StateID writes have fusion ordering restrictions.', BH+'ConfigurationUnit.md')
    add('RMWCIB0 RMWCIB1 RMWCIB2 RMWCIB3', 'config', '1', '1', 'Blackhole manual',
        'Shared configuration pipeline across threads.', BH+'ConfigurationUnit.md')
    add('WRCFG', 'config', '2', '1', 'Blackhole manual', 'Pipelined; configuration consumers need correct ordering.', BH+'ConfigurationUnit.md')
    add('RDCFG', 'config', '>=2', '1', 'Blackhole manual', 'GPR write contention can delay completion.', BH+'ConfigurationUnit.md')
    add('CFGSHIFTMASK', 'config', '2', '2', 'Blackhole manual', 'Not pipelined; next non-config consumer needs an intervening slot.', BH+'CFGSHIFTMASK.md')
    add('STREAMWRCFG', 'config', '>=5', '1', 'Blackhole manual', 'Overlay read contention and pipeline ordering/starvation can add stalls.', BH+'STREAMWRCFG.md')

    add('ATGETM ATRELM', 'sync', '1 + acquisition wait', '1 per distinct mutex', 'Blackhole manual',
        'ATGETM waits until available; ATRELM has no acquisition wait. Up to 3 distinct mutex operations across threads/cycle.', BH+'SyncUnit.md')
    add('SEMINIT SEMPOST SEMGET', 'sync', '1', '1 shared', 'Blackhole manual', 'Shared with wait instructions and RISC semaphore writes.', BH+'SyncUnit.md')
    add('STALLWAIT SEMWAIT STREAMWAIT', 'sync', '1 latch + condition wait', '1 shared', 'Blackhole manual',
        'Blocks selected instruction classes; unblock has 1-cycle lag even if condition is already met. Condition may never occur.', BH+'SyncUnit.md')
    add('MOP', 'frontend', 'expanded body + transition', '1 emitted op/cycle', 'shared manual',
        'Expand actual loop/template/replay counts; downstream stalls apply. MOP to non-MOP transition adds 1 cycle unless hidden.', BH+'MOPExpander.md')
    add('MOP_CFG', 'frontend', 'payload-dependent', '1 word/cycle estimate', 'shared model estimate',
        'Configuration plus payload ingestion, not one arithmetic operation. Account for emitted setup words.', BH+'MOPExpander.md')
    add('REPLAY', 'frontend', 'Count emitted slots', '1 emitted op/cycle', 'shared manual',
        'Execute replaces command with first replay op; do not charge an extra command slot. Load-only costs 1+Count ingestion slots. Downstream stalls still apply.', BH+'REPLAY.md')
    add('RESOURCEDECL', 'frontend', '~1', '~1', 'analogy estimate',
        'Resource declaration changes later hazard tracking; one slot estimate, unmeasured.', LLK)
    add('UNPACR', 'unpack', '>=2 setup + transfer + drain', 'workload-dependent', 'shared manual',
        'Uncompressed setup 2 cycles; L1 rate at most 16/32/64 bytes/cycle at x1/x2/x4. Approx 2+ceil(bytes/rate)+pipeline tail; compression, format, ownership and contention add time.', BH+'UNPACR_Regular.md')
    add('UNPACR_NOP', 'unpack', '1 in NOP mode; other modes vary', '>=1', 'mode-dependent estimate',
        'Sequenced after prior unpack work; set-valid/zero/context modes need their own dependencies, not a blanket 1-cycle completion.', WH+'UNPACR_NOP.md')
    add('PACR PACR_SETREG', 'pack', 'workload-dependent', '>=1 acceptance', 'shared model estimate',
        'At most 1 command accepted/cycle; issue can wait for packers. PACR completion scales with data, format, masks and L1. SETREG waits behind prior pack conversions.', WH+'Packers/README.md')
    add('XMOV', 'mover', '1 launch + transfer', 'wait for mover availability', 'Wormhole estimate',
        '1-cycle launch once mover ready; model bytes/bandwidth plus tail separately. Launch is not completion.', WH+'XMOV.md')
    add('TBUFCMD', 'reserved', 'unknown', 'unknown', 'reserved', 'LLK explicitly reserves this opcode for future use; do not execute to estimate timing.', LLK)

    for name in ('MVMUL', 'ELWMUL', 'SFPLOAD', 'SFPSTORE'):
        records[name]['notes'] += (' Measured FP32 Dst: alternating FPU and SFPU memory operations in the same Dst half adds burst-dependent stalls; opposite halves avoid the penalty. Separate threads alone do not remove same-half contention. See tests/timing/fpu_sfpu_interleave.md.')

    names = {n[2:] for n in dir(Tensix) if n.startswith('TT')}
    assert names == records.keys(), (names - records.keys(), records.keys() - names)
    rev = lambda repo: subprocess.check_output(['git', '-C', str(WORKSPACE/repo), 'rev-parse', 'HEAD'], text=True).strip()
    revisions = {'manual': rev('tt-isa-documentation'), 'llk': rev('tt-llk')}
    for row in records.values():
        llk = row['source'] == LLK
        path = WORKSPACE/'tt-llk'/LLK if llk else DOCS/row['source']
        if not path.exists() and row['source'].startswith(BH):
            row['source'] = row['source'].replace(BH, WH, 1)
            path = DOCS/row['source']
        assert path.exists(), path
        repo, commit = ('tt-llk', revisions['llk']) if llk else ('tt-isa-documentation', revisions['manual'])
        row['source_url'] = f'https://github.com/tenstorrent/{repo}/blob/{commit}/{row["source"]}'
    return dict(schema_version=1, units='Tensix backend cycles', revisions=revisions,
                instructions=[records[n] for n in sorted(records)])


def main():
    data = build()
    (HERE/'tensix_timing.json').write_text(json.dumps(data, indent=2)+'\n')
    lines = ['# Tensix instruction cycle reference', '',
             'Generated with `python -m tests.timing.tensix_catalog`. All 137 public encoders are classified.',
             'See [the kernel timing guide](README.md) before summing these numbers.',
             'Issue interval means spacing between independent operations on the same unit; latency means result readiness.',
             'A `~` is an unmeasured analogy, `>=` is a lower bound, and unknown is not zero.',
             'Wormhole-only references are estimates for Blackhole, not Blackhole contracts.', '',
             '| Instruction | Unit | Latency (cycles) | Issue interval (cycles) | Basis | Conditions |',
             '|---|---|---|---|---|---|']
    for r in data['instructions']:
        lines.append(f'| [{r["instruction"]}]({r["source_url"]}) | {r["unit"]} | {r["latency_cycles"]} | {r["issue_interval_cycles"]} | {r["basis"]} | {r["notes"]} |')
    (HERE/'tensix_timing.md').write_text('\n'.join(lines)+'\n')
    samples = [json.loads(line) for line in (HERE/'tensix_measured.jsonl').read_text().splitlines()]
    lines = ['# Blackhole Tensix measured timing', '',
             'Card 0, physical core index 0, T0/T1/T2; 2026-09-17. See [method and limitations](README.md).',
             'These are completed-loop median slopes, not isolated result latencies.',
             'Two slopes use successive 1,024 / 2,048 / 4,096-operation points.',
             '`empty` counts empty body slots; `swap_nop`/`shuffle_nop` include a padding SFPNOP in each body operation.', '',
             'Each cell gives the range of the two slopes, in cycles per body operation.', '',
             '| Probe | T0 | T1 | T2 |', '|---|---:|---:|---:|']
    by_case = {}
    for row in samples:
        by_case.setdefault(row['case'], {})[row['role']] = row['adjacent_slopes_cycles_per_body_op']
    for case, roles in by_case.items():
        values = []
        for role in ('trisc0', 'trisc1', 'trisc2'):
            slopes = roles[role]
            values.append(f'{min(slopes):.3f}–{max(slopes):.3f}')
        lines.append(f'| {case} | ' + ' | '.join(values) + ' |')
    lines.extend(['', 'Raw samples and image/source SHA-256 hashes are in [tensix_measured.jsonl](tensix_measured.jsonl).',
                  'Only `swap_nop`/`shuffle_nop` contain padding instructions; `dma_nop` is one DMANOP per body operation.', ''])
    (HERE/'tensix_measured.md').write_text('\n'.join(lines))


if __name__ == '__main__': main()
