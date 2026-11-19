"""SFPU probes: issue/latency/hazard timing and old-vs-new value checks, SFPLOADMACRO, FPU -> SFPU through Dst.
Ports of the old pytest probes (test_sfpu_hazards.py, test_sfpu_matrix.py, test_sfpu_loadmacro.py, test_sfpu_dst.py,
built on blackhole-py 718843a^'s Asm/Profiler harness) to plain C kernels: k_sfpu_loop.c (timing, trisc1),
k_sfpu_value.c (unpack -> SFPU -> pack, three TRISCs), k_sfpu_dst.c (FPU + SFPU, three TRISCs). Case map, firmware
differences and risks: SFPU.md.

  python3 sims/probes/run.py --device 1 --output sims/results/<date>-sfpu-hazards-card1.jsonl sfpu -k hazards
  (groups: hazards, matrix, loadmacro, dst)

Every case carries 'expect': what the old runs measured (sims/results/2026-11-18-sfpu-*.jsonl), keyed by card, and
the result says whether the rerun agrees ('match'). Methodology is the old one, case for case: one launch per sample,
first launch of each point discarded, raw samples kept, same slope definitions.
"""
import json
from pathlib import Path
from statistics import median
from struct import pack, unpack

from tile import LAYOUT, build

TILE = (1, 2)  # the old harness's core 0
RESULTS = Path(__file__).resolve().parents[1] / 'results'
SITES = {1: 'unpack_config_sync', 2: 'math_done', 3: 'unpack_to_dest', 4: 'math_pack'}
DST_SITES = {1: 'unpack_config_a', 2: 'unpack_config_b', 3: 'ready', 4: 'math_pack'}
TOL = 0.02  # slope agreement, as sims/test_sfpu_model.py


# ---------------------------------------------------------------- Tensix words (field layouts of the old ttko/isa.py)

def tt(op, *fields):
  w = op << 24
  for v, hi, lo in fields:
    if not 0 <= v < 1 << (hi - lo + 1): raise ValueError(f'{v} does not fit in bits {hi}:{lo}')
    w |= v << lo
  assert w < 0xC0000000, hex(w)
  return w


def _i12(op): return lambda imm=0, c=0, d=0, mod=0: tt(op, (imm, 23, 12), (c, 11, 8), (d, 7, 4), (mod, 3, 0))
def _abc(op): return lambda a=0, b=0, c=0, d=0, mod=0: tt(op, (a, 23, 16), (b, 15, 12), (c, 11, 8), (d, 7, 4), (mod, 3, 0))


SFPMAD, SFPMOV, SFPIADD, SFPSETSGN, SFPAND = _abc(0x84), _i12(0x7C), _i12(0x79), _i12(0x89), _i12(0x7E)
SFPSWAP, SFPSHFT2, SFPARECIP, SFPENCC = _i12(0x92), _i12(0x94), _i12(0x99), _i12(0x8A)
def SFPLOADI(d, mod0, imm): return tt(0x71, (d, 23, 20), (mod0, 19, 16), (imm, 15, 0))
def SFPLOAD(d, mod0, am, addr): return tt(0x70, (d, 23, 20), (mod0, 19, 16), (am, 15, 13), (addr, 12, 0))
def SFPSTORE(d, mod0, am, addr): return tt(0x72, (d, 23, 20), (mod0, 19, 16), (am, 15, 13), (addr, 12, 0))
def ELWMUL(cd=0, acc=0, mod=0, am=0, dst=0): return tt(0x27, (cd, 23, 22), (acc, 21, 21), (mod, 20, 19), (am, 18, 14), (dst, 13, 0))
SFPNOP, TTNOP = 0x8F000000, 0x02000000
DRAIN = 'D'  # emit.drain(): STALLWAIT(SYNC, SFPU) + PC_BUF_SYNC round trip


def rot(w): return (w << 2 | w >> 30) & 0xFFFFFFFF  # .ttinsn: the word as the RISC fetches it


def words(ws): return ','.join(f'{rot(w):#010x}' for w in ws)


def stream(items):
  """[word | DRAIN, ...] -> T(w,...) D ... : each run of words is one asm block (sfpu.h)."""
  out, run_ = [], []
  for it in [*items, None]:
    if isinstance(it, int): run_.append(it); continue
    if run_: out.append(f'T({words(run_)})'); run_ = []
    if it == DRAIN: out.append('D')
  return ' '.join(out)


def li32(reg, bits): return [SFPLOADI(reg, 8, bits >> 16), SFPLOADI(reg, 10, bits & 0xFFFF)]
def f2b(x): return unpack('<I', pack('<f', x))[0]
def constant(reg, value): return li32(reg, f2b(value))  # emit.constant


# ---------------------------------------------------------------- old results -> expect

def _records(name):
  p = RESULTS / name
  return [json.loads(line) for line in p.read_text().splitlines() if line.strip()] if p.exists() else []


def _by_card(*sources, key, value):
  """{key: {'card<N>': value(record)}} over (file, card) sources."""
  out = {}
  for name, card in sources:
    for r in _records(name):
      if (k := key(r)) is not None: out.setdefault(k, {})[f'card{card}'] = value(r)
  return out


# ---------------------------------------------------------------- shared run helpers

def _cfg(card, role):
  a = card.aux(TILE, 5, role)
  return dict(cfg0_entry=hex(a[0]), cfg0_timed=hex(a[1]), prefetch=hex(a[2]), dest_cg=hex(a[3]), tdma_cg=hex(a[4]))


def _stamps(card, role):
  """(start, stop) of the timed region: PROF0/PROF1 = the role's LOG + 0xFC0 (sfpu.h)."""
  t0, t1 = unpack('<2I', card.iface.read(TILE, LAYOUT[role]['log'] + 0xFC0, 8))
  return (t1 - t0) & 0xFFFFFFFF


def _sample(card, image, params, timeout):
  card.run([(TILE, {'trisc1': image}, {'trisc1': params}, None)], timeout, SITES)
  return _stamps(card, 'trisc1')


def _loop_image(setup, body, tail=()):
  defines = dict(BODY=words(body))
  if setup: defines['SETUP'] = stream(setup)
  if tail: defines['TAIL_WORDS'] = words(tail)
  return build('k_sfpu_loop.c', 'trisc1', **defines)


def _points(card, image, counts, launches, timeout, params=(0, 0, 0)):
  """Per count: `launches` launches, the first discarded (warmup)."""
  rows = []
  for count in counts:
    s = [_sample(card, image, [count, *params], timeout) for _ in range(launches)][1:]
    rows.append(dict(iterations=count, raw_cycles=s, median=median(s), min=min(s), max=max(s)))
  return rows


INPUT, OUTPUT, SIZE = 0x100000, 0x110000, 8192  # old 0x50000 / 0x60000: now trisc0/trisc1 RES and LOG


def _value_images(compute):
  return {'trisc0': build('k_sfpu_value.c', 'trisc0', PART=0),
          'trisc1': build('k_sfpu_value.c', 'trisc1', PART=1, COMPUTE=stream(compute)),
          'trisc2': build('k_sfpu_value.c', 'trisc2', PART=2)}


def _value_launch(card, images, fill, timeout, params=None):
  card.run([(TILE, images, params or {}, {INPUT: pack('<I', fill) * SIZE, OUTPUT: b'\x5a' * (SIZE * 4)})], timeout, SITES)
  return unpack(f'<{SIZE}I', card.iface.read(TILE, OUTPUT, SIZE * 4))


def _slopes_match(got, want):
  return len(got) == len(want) and all(abs(a - b) <= TOL for a, b in zip(got, want))


def _expected(case, card):
  return (case.get('expect') or {}).get(f'card{card.index}')


# ================================================================ hazards (old test_sfpu_hazards.py)

H_COUNTS, BODY = (64, 128, 256), 16
MAD_L0 = SFPMAD(1, 10, 9, 0, 0)  # L0 = L1 * 1 + 0, does not read L0
H_UNITS = {
  'nop': [SFPNOP],
  'mad_chain': [SFPMAD(0, 10, 9, 0, 0)],
  'mad_nop_chain': [SFPMAD(0, 10, 9, 0, 0), SFPNOP],
  'mad_ind4': None,  # SFPMAD(i % 4, 10, 9, i % 4, 0), see h_unit
  'mad_indep_mov': [MAD_L0, SFPMOV(0, 3, 4, 0)],
  'mad_dep_mov': [MAD_L0, SFPMOV(0, 0, 4, 0)],
  'mad_nop_dep_mov': [MAD_L0, SFPNOP, SFPMOV(0, 0, 4, 0)],
  'mad_nop_indep_mov': [MAD_L0, SFPNOP, SFPMOV(0, 3, 4, 0)],
  'mad_iadd_vc': [MAD_L0, SFPIADD(0, 0, 4, 4)],
  'mad_iadd_vd': [MAD_L0, SFPIADD(0, 3, 0, 4)],
  'mad_setsgn_vd': [MAD_L0, SFPSETSGN(0, 3, 0, 0)],
  'mad_and_vb': [MAD_L0, SFPAND(0, 3, 4, 1)],
  'mad_minmax': [MAD_L0, SFPSWAP(0, 3, 0, 1)],
  'mad_nop_minmax': [MAD_L0, SFPNOP, SFPSWAP(0, 3, 0, 1)],
  'mad_swap': [MAD_L0, SFPSWAP(0, 3, 0, 0)],
  'mad_shuf': [MAD_L0, SFPSHFT2(0, 0, 4, 3)],
  'mad_loadi_lo': [MAD_L0, SFPLOADI(0, 10, 0x1234)],
  'swap_mov': [SFPSWAP(0, 3, 2, 1), SFPMOV(0, 5, 6, 0)],
  'swap_nop_mov': [SFPSWAP(0, 3, 2, 1), SFPNOP, SFPMOV(0, 5, 6, 0)],
  'swap_nop2_mov': [SFPSWAP(0, 3, 2, 1), SFPNOP, SFPNOP, SFPMOV(0, 5, 6, 0)],
  'shuf_mov': [SFPSHFT2(0, 1, 2, 3), SFPMOV(0, 5, 6, 0)],
  'shuf_nop_mov': [SFPSHFT2(0, 1, 2, 3), SFPNOP, SFPMOV(0, 5, 6, 0)],
  'shft2_lreg_mov': [SFPSHFT2(0, 1, 2, 5), SFPMOV(0, 5, 6, 0)],
  'loadi_pair': [SFPLOADI(4, 8, 0x3f80), SFPLOADI(4, 10, 0)],
  'sfpload': [SFPLOAD(4, 3, 0, 0)],
  'sfpstore': [SFPSTORE(4, 3, 0, 0)],
  'load_mad_store': [SFPLOAD(0, 3, 0, 0), SFPMAD(0, 10, 9, 0, 0), SFPSTORE(0, 3, 0, 0)],
  'load_mad_nop_store': [SFPLOAD(0, 3, 0, 0), SFPMAD(0, 10, 9, 0, 0), SFPNOP, SFPSTORE(0, 3, 0, 0)],
  'arecip_mad': [SFPARECIP(0, 1, 0, 0), SFPMAD(0, 10, 9, 4, 0)],
  'tt_nop_mad_dep': [MAD_L0, TTNOP, SFPMOV(0, 0, 4, 0)],
}


def h_unit(case, i): return [SFPMAD(i % 4, 10, 9, i % 4, 0)] if case == 'mad_ind4' else H_UNITS[case]
def h_setup(): return [SFPENCC(0, 0, 0, 2), *(w for reg in range(8) for w in constant(reg, 1.))]
def h_body(case): return [w for i in range(BODY) for w in h_unit(case, i)]


OLD, NEW, C3, POS5 = 0x3F800000, 0xC0A00000, 0x40400000, 0x40A00000  # 1.0, -5.0, 3.0, 5.0
POISON = 0xA5A5A5A5
# name: (consumer words, LReg stored, L3 value, NEW-read result, OLD-read result)
H_VALUES = {
  'mov_detected': ([SFPMOV(0, 0, 4, 0)], 4, C3, NEW, OLD),
  'iadd_vd': ([SFPIADD(0, 3, 0, 4)], 0, 1, (NEW + 1) & 0xFFFFFFFF, OLD + 1),
  'iadd_vc_imm': ([SFPIADD(1, 0, 4, 5)], 4, C3, NEW + 1, OLD + 1),
  'and_vb': ([SFPAND(0, 3, 4, 1)], 4, 0xFFFFFFFF, NEW, OLD),
  'setsgn_vd': ([SFPSETSGN(0, 3, 0, 0)], 0, C3, C3 | 0x80000000, C3),
  'minmax_min': ([SFPSWAP(0, 3, 0, 1)], 0, C3, NEW, OLD),
  'minmax_max': ([SFPSWAP(0, 3, 0, 1)], 3, C3, C3, C3),
  'shuffle': ([SFPSHFT2(0, 0, 4, 3)], 4, C3, NEW, OLD),
  'loadi_lower': ([SFPLOADI(0, 10, 0x1234)], 0, C3, (NEW & 0xFFFF0000) | 0x1234, None),
  'minmax5_min': ([SFPSWAP(0, 3, 0, 1)], 0, C3, C3, POS5),  # NEW = +5.0 for the minmax5 cases
  'minmax5_max': ([SFPSWAP(0, 3, 0, 1)], 3, C3, POS5, C3),
}
H_NEW = {'minmax5_min': POS5, 'minmax5_max': POS5}


def h_compute(case, gap):
  cons, out, l3, _, _ = H_VALUES[case]
  s = []
  for pos in range(4):
    s += [SFPENCC(0, 0, 0, 2), *li32(0, OLD), *li32(1, H_NEW.get(case, NEW)), *li32(3, l3), *li32(4, 0), DRAIN,
          MAD_L0, *[SFPNOP] * gap, *cons, DRAIN, SFPSTORE(out, 3, 0, 8 + pos * 2)]
  return s + [DRAIN]


H_FILES = {'': [('2026-11-18-sfpu-hazards-card0.jsonl', 0), ('2026-11-18-sfpu-hazards-card1.jsonl', 1)],
           'prefetchoff': [('2026-11-18-sfpu-hazards-prefetchoff-card1.jsonl', 1)],
           'prefetchoff-clr40000': [('2026-11-18-sfpu-hazards-prefetchoff-card0.jsonl', 0)]}
# variant: (cfg0 bits cleared, prefetch control written or None)
H_VARIANTS = {'': (0, None), 'prefetchoff': (0, 0), 'prefetchoff-clr40000': (0x40000, 0)}


def _hazard_cases():
  for var, (clear, prefetch) in H_VARIANTS.items():
    tag = f'-{var}' if var else ''
    timing = _by_card(*H_FILES[var], key=lambda r: r['case'] if r['kind'] == 'timing' else None,
                      value=lambda r: r['slopes_cycles_per_unit'])
    for case in H_UNITS:
      yield dict(id=f'hazards-timing{tag}-{case}', group='hazards', kind='timing', case=case, cfg0_clear=clear,
                 prefetch_write=prefetch, expect=timing.get(case), tiles=[TILE])
    if var == 'prefetchoff-clr40000': continue  # that run recorded no value checks
    values = _by_card(*H_FILES[var], key=lambda r: (r['case'], r['gap']) if r['kind'] == 'value' else None,
                      value=lambda r: dict(verdict=r['verdict'], seen=r['seen']))
    if not var:  # the minmax5 cases were first run on their own
      for k, v in _by_card(('2026-11-18-sfpu-minmax5-card1.jsonl', 1), key=lambda r: (r['case'], r['gap']),
                           value=lambda r: dict(verdict=r['verdict'], seen=r['seen'])).items():
        values.setdefault(k, {}).setdefault('card1', v['card1'])
    for case in H_VALUES:
      if var and case.startswith('minmax5'): continue  # added after the prefetch-off run
      for gap in (0, 1):
        yield dict(id=f'hazards-value{tag}-{case}-gap{gap}', group='hazards', kind='value', case=case, gap=gap,
                   cfg0_clear=clear, prefetch_write=prefetch, expect=values.get((case, gap)), tiles=[TILE])


def _prefetch_params(case):
  p = case['prefetch_write']
  return (case['cfg0_clear'], 0 if p is None else 1, p or 0)


def run_hazard(card, case, timeout):
  if case['kind'] == 'timing':
    image = _loop_image(h_setup(), h_body(case['case']))
    rows = _points(card, image, H_COUNTS, 8, timeout, _prefetch_params(case))
    for r in rows: r['units'] = BODY * r['iterations']
    slopes = [(b['median'] - a['median']) / (b['units'] - a['units']) for a, b in zip(rows, rows[1:])]
    want = _expected(case, card)
    return dict(sfpu_insns_per_unit=len(h_unit(case['case'], 0)), slopes_cycles_per_unit=slopes,
                loop_overhead_insns_per_unit=2 / BODY, points=rows, cfg=_cfg(card, 'trisc1'),
                match=None if want is None else _slopes_match(slopes, want))
  images, p = _value_images(h_compute(case['case'], case['gap'])), case['prefetch_write']
  params = {r: [0, 0] if p is None else [1, p] for r in images}
  seen = sorted({v for _ in range(4) for v in _value_launch(card, images, POISON, timeout, params)[128:256]})
  _, _, _, new, old = H_VALUES[case['case']]
  verdict = 'new' if seen == [new] else 'old' if seen == [old] else 'other'
  want = _expected(case, card)
  return dict(seen=[hex(v) for v in seen], verdict=verdict, expect_new=hex(new),
              expect_old=None if old is None else hex(old), cfg=_cfg(card, 'trisc1'),
              match=None if want is None else (verdict == want['verdict'] and [hex(v) for v in seen] == want['seen']))


# ================================================================ matrix (old test_sfpu_matrix.py)

OP = dict(ABS=0x7d, ADD=0x85, ADDI=0x75, AND=0x7e, ARECIP=0x99, CAST=0x90, COMPC=0x8b, CONFIG=0x91, DIVP2=0x76,
          ENCC=0x8a, EXEXP=0x77, EXMAN=0x78, GT=0x97, IADD=0x79, LE=0x96, LOAD=0x70, LOADI=0x71, LOADMACRO=0x93,
          LUT=0x73, LUTFP32=0x95, LZ=0x81, MAD=0x84, MOV=0x7c, MUL=0x86, MUL24=0x98, MULI=0x74, NOP=0x8f, NOT=0x80,
          OR=0x7f, POPC=0x88, PUSHC=0x87, SETCC=0x7b, SETEXP=0x82, SETMAN=0x83, SETSGN=0x89, SHFT=0x7a, SHFT2=0x94,
          STORE=0x72, SWAP=0x92, TRANSP=0x8c, XOR=0x8d, STOCHRND=0x8e)


def W(op, vd=0, vc=0, vb=0, va=0, mod=0, imm12=None, imm16=None, mod0=None, low=0, mirror=0, rnd=0, imm5=0):
  o = OP[op] << 24
  if op in ('LOAD', 'LOADI', 'STORE', 'LUT', 'LOADMACRO'): return o | vd << 20 | (mod0 or 0) << 16 | low
  if op in ('ADDI', 'MULI', 'CONFIG'): return o | (imm16 or 0) << 8 | vd << 4 | mod
  if op == 'LUTFP32': return o | mirror << 16 | vd << 4 | mod
  if op == 'STOCHRND': return o | rnd << 21 | imm5 << 16 | vb << 12 | vc << 8 | vd << 4 | mod
  if op in ('MAD', 'MUL', 'ADD', 'MUL24'): return o | va << 16 | vb << 12 | vc << 8 | vd << 4 | mod
  return o | (vb if imm12 is None else imm12) << 12 | vc << 8 | vd << 4 | mod


NOP = W('NOP')
INIT = {0: 0x3F800003, 1: 0x40200001, 2: 0xBF400000, 3: 0x3FC00000, 4: 0x12345678, 5: 0x00000003, 6: 0x3F000000,
        7: 0x00000004}
PRODUCERS = [
  ('MAD', W('MAD', 0, va=1, vb=2, vc=3)), ('MUL', W('MUL', 0, va=1, vb=2, vc=9)), ('ADD', W('ADD', 0, va=10, vb=1, vc=2)),
  ('ADDI', W('ADDI', 0, imm16=0x4000)), ('MULI', W('MULI', 0, imm16=0xC000)), ('MUL24', W('MUL24', 0, va=1, vb=2, vc=9)),
  ('MUL24.upper', W('MUL24', 0, va=1, vb=2, vc=9, mod=1)),
  ('LUT', W('LUT', 0, mod0=0)), ('LUTFP32.m0', W('LUTFP32', 0, mod=0)), ('LUTFP32.m2', W('LUTFP32', 0, mod=2)),
  ('MOV', W('MOV', 0, vc=1)), ('ABS.f', W('ABS', 0, vc=2, mod=1)), ('IADD.imm', W('IADD', 0, vc=1, imm12=5, mod=5)),
  ('IADD.reg', W('IADD', 0, vc=1, mod=4)), ('SHFT.imm', W('SHFT', 0, imm12=3, mod=1)), ('AND.vb', W('AND', 0, vc=2, vb=1, mod=1)),
  ('OR.vb', W('OR', 0, vc=2, vb=1, mod=1)), ('XOR', W('XOR', 0, vc=1)), ('NOT', W('NOT', 0, vc=1)), ('LZ', W('LZ', 0, vc=1)),
  ('EXEXP', W('EXEXP', 0, vc=1)), ('EXMAN', W('EXMAN', 0, vc=1)), ('SETEXP.imm', W('SETEXP', 0, vc=1, imm12=0x80, mod=1)),
  ('SETMAN.imm', W('SETMAN', 0, vc=1, imm12=0x123, mod=1)), ('SETSGN.imm', W('SETSGN', 0, vc=1, imm12=1, mod=1)),
  ('DIVP2', W('DIVP2', 0, vc=1, imm12=2, mod=1)), ('ARECIP', W('ARECIP', 0, vc=1)), ('ARECIP.exp', W('ARECIP', 0, vc=2, mod=2)),
  ('CAST', W('CAST', 0, vc=5, mod=0)), ('STOCHRND.f16b', W('STOCHRND', 0, vc=1, mod=1)),
  ('STOCHRND.u8', W('STOCHRND', 0, vc=5, mod=4 | 8, imm5=1)),
  ('LOADI', W('LOADI', 0, mod0=0, low=0x4321)), ('LOAD', W('LOAD', 0, mod0=3, low=0)),
  ('GT.setvd', W('GT', 0, vc=2, mod=8)), ('LE.setvd', W('LE', 0, vc=2, mod=8)),
  ('SWAP.m0', W('SWAP', 0, vc=1, mod=0)), ('SWAP.m1', W('SWAP', 0, vc=1, mod=1)),
  ('SHFT2.m0', W('SHFT2', 0, vc=5, mod=0)), ('SHFT2.m2', W('SHFT2', 0, vc=1, mod=2)), ('SHFT2.m3', W('SHFT2', 0, vc=1, mod=3)),
  ('SHFT2.m4', W('SHFT2', 0, vc=1, mod=4)), ('SHFT2.m5', W('SHFT2', 0, vb=1, vc=5, mod=5)),
  ('SHFT2.m6', W('SHFT2', 0, vb=1, imm12=(3 << 4) | 1, mod=6)), ('TRANSP', W('TRANSP')),
]
CONSUMERS = [
  ('MOV.vc', W('MOV', 4, vc=0)), ('ABS.vc', W('ABS', 4, vc=0, mod=1)),
  ('MAD.va', W('MAD', 4, va=0, vb=5, vc=6)), ('MAD.vb', W('MAD', 4, va=6, vb=0, vc=5)), ('MAD.vc', W('MAD', 4, va=6, vb=5, vc=0)),
  ('MUL.va', W('MUL', 4, va=0, vb=6, vc=9)), ('ADD.vc', W('ADD', 4, va=10, vb=6, vc=0)),
  ('ADDI.vd', W('ADDI', 0, imm16=0x3F80)), ('MULI.vd', W('MULI', 0, imm16=0x4000)),
  ('MUL24.va', W('MUL24', 4, va=0, vb=6, vc=9)), ('MUL24.vb', W('MUL24', 4, va=6, vb=0, vc=9)),
  ('LUT.impl', W('LUT', 4, mod0=0)), ('LUTFP32.impl', W('LUTFP32', 4, mod=0)),
  ('LUTFP32.mirror8', W('LUTFP32', 4, mod=0, mirror=8)),
  ('IADD.vc.imm', W('IADD', 4, vc=0, imm12=1, mod=5)), ('IADD.vc.reg', W('IADD', 4, vc=0, mod=4)),
  ('IADD.vd.reg', W('IADD', 0, vc=5, mod=4)), ('IADD.vd.sub', W('IADD', 0, vc=5, mod=6)),
  ('SHFT.vd.imm', W('SHFT', 0, imm12=2, mod=1)), ('SHFT.vd.reg', W('SHFT', 0, vc=5, mod=0)), ('SHFT.vc.reg', W('SHFT', 4, vc=0, mod=0)),
  ('SHFT.vc.immvc', W('SHFT', 4, vc=0, imm12=2, mod=5)),
  ('AND.vc', W('AND', 4, vc=0, vb=6, mod=1)), ('AND.vd', W('AND', 0, vc=6, mod=0)), ('AND.vb', W('AND', 4, vc=6, vb=0, mod=1)),
  ('OR.vb', W('OR', 4, vc=6, vb=0, mod=1)), ('OR.vd', W('OR', 0, vc=6, mod=0)),
  ('XOR.vc', W('XOR', 4, vc=0)), ('XOR.vd', W('XOR', 0, vc=6)), ('NOT.vc', W('NOT', 4, vc=0)), ('LZ.vc', W('LZ', 4, vc=0)),
  ('EXEXP.vc', W('EXEXP', 4, vc=0)), ('EXMAN.vc', W('EXMAN', 4, vc=0)),
  ('SETEXP.vc.imm', W('SETEXP', 4, vc=0, imm12=0x81, mod=1)), ('SETEXP.vd', W('SETEXP', 0, vc=6, mod=0)),
  ('SETEXP.vc.reg', W('SETEXP', 4, vc=0, mod=0)),
  ('SETMAN.vc.imm', W('SETMAN', 4, vc=0, imm12=0x7, mod=1)), ('SETMAN.vd', W('SETMAN', 0, vc=6, mod=0)),
  ('SETSGN.vc.imm', W('SETSGN', 4, vc=0, imm12=1, mod=1)), ('SETSGN.vd', W('SETSGN', 0, vc=6, mod=0)),
  ('DIVP2.vc', W('DIVP2', 4, vc=0, imm12=1, mod=1)), ('ARECIP.vc', W('ARECIP', 4, vc=0)),
  ('ARECIP.cond.vb', W('ARECIP', 4, vc=6, vb=0, mod=1)), ('ARECIP.cond.vc', W('ARECIP', 4, vc=0, vb=2, mod=1)),
  ('CAST.vc', W('CAST', 4, vc=0)), ('STOCHRND.vc', W('STOCHRND', 4, vc=0, mod=1)),
  ('STOCHRND.vb', W('STOCHRND', 4, vc=5, vb=0, mod=4)),
  ('SETCC.vc', W('SETCC', 0, vc=0, mod=0)), ('GT.vc', W('GT', 4, vc=0, mod=1)), ('GT.vd', W('GT', 0, vc=6, mod=1)),
  ('LE.vd', W('LE', 0, vc=6, mod=1)),
  ('SWAP.m0.vd', W('SWAP', 0, vc=6, mod=0)), ('SWAP.m0.vc', W('SWAP', 6, vc=0, mod=0)),
  ('SWAP.m1.vd', W('SWAP', 0, vc=6, mod=1)), ('SWAP.m1.vc', W('SWAP', 6, vc=0, mod=1)),
  ('SHFT2.m0.impl', W('SHFT2', 4, vc=6, mod=0)), ('SHFT2.m1.impl', W('SHFT2', 4, vc=6, mod=1)),
  ('SHFT2.m2.vc', W('SHFT2', 4, vc=0, mod=2)), ('SHFT2.m3.vc', W('SHFT2', 4, vc=0, mod=3)), ('SHFT2.m4.vc', W('SHFT2', 4, vc=0, mod=4)),
  ('SHFT2.m5.vb', W('SHFT2', 4, vb=0, vc=5, mod=5)), ('SHFT2.m5.vc', W('SHFT2', 4, vb=6, vc=0, mod=5)),
  ('SHFT2.m6.vb', W('SHFT2', 4, vb=0, imm12=(2 << 4), mod=6)),
  ('TRANSP.impl', W('TRANSP')), ('STORE', W('STORE', 0, mod0=3, low=0)),
  ('CONFIG.L12', W('CONFIG', 12, mod=0)),
  ('LOADI.lower', W('LOADI', 0, mod0=10, low=0x1234)), ('LOADI.upper', W('LOADI', 0, mod0=8, low=0x4110)),
  ('LOAD.lo16', W('LOAD', 0, mod0=14, low=0)), ('LOAD.hi16', W('LOAD', 0, mod0=15, low=0)),
  ('LOADI.full', W('LOADI', 0, mod0=0, low=0x4110)), ('MOV.waw', W('MOV', 0, vc=6)),
]
M_COUNTS = (32, 96)


def init_regs(): return [w for r, v in INIT.items() for w in li32(r, v)]
def m_setup(): return [SFPENCC(0, 0, 0, 2), *init_regs()]


def m_slope(card, unit, timeout, setup=None, tail=()):
  """The old slope(): unit x16 per iteration, 32 vs 96 iterations, 4 launches per point (first discarded)."""
  image = _loop_image(m_setup() if setup is None else setup, [w for _ in range(BODY) for w in unit], tail)
  rows = _points(card, image, M_COUNTS, 4, timeout)
  slope = (rows[1]['median'] - rows[0]['median']) / ((M_COUNTS[1] - M_COUNTS[0]) * BODY)
  return slope, max(r['max'] - r['min'] for r in rows), rows


VARIANTS = ('ref', 'noprod', 'gap0', 'gap1')
SLOTS = 11  # L0..L7, flags probe, store target, L12


def m_compute(prod, cons):
  s = []
  for v, variant in enumerate(VARIANTS):
    base = 1 + v * SLOTS
    c = cons | (base + 9) * 8 if cons >> 24 == OP['STORE'] else cons
    s += [SFPENCC(0, 0, 0, 2), *init_regs(), *li32(0, 0x0BADF00D), NOP, W('CONFIG', 12, mod=0), NOP, *init_regs(),
          SFPENCC(3, 0, 0, 10), DRAIN, NOP if variant == 'noprod' else prod,
          *[NOP] * {'ref': 3, 'noprod': 3, 'gap0': 0, 'gap1': 1}[variant], c, *[NOP] * 4, DRAIN]
    s += [SFPSTORE(r, 3, 0, (base + r) * 8 + pos * 2) for r in range(8) for pos in range(4)]
    s += [SFPLOADI(4, 8, 0x7777), *[SFPSTORE(4, 3, 0, (base + 8) * 8 + pos * 2) for pos in range(4)]]
    s += [SFPENCC(0, 0, 0, 2), W('MOV', 4, vc=12), NOP, *[SFPSTORE(4, 3, 0, (base + 10) * 8 + pos * 2) for pos in range(4)],
          DRAIN]
  return s


def m_values(card, prod, cons, timeout):
  images = _value_images(m_compute(prod, cons))
  runs = []
  for _ in range(2):
    got = _value_launch(card, images, POISON, timeout)
    runs.append({var: got[(1 + v * SLOTS) * 128:(1 + (v + 1) * SLOTS) * 128] for v, var in enumerate(VARIANTS)})
  stable, r = runs[0] == runs[1], runs[0]
  if r['ref'] == r['noprod']: out = {'gap0': 'insensitive', 'gap1': 'insensitive'}
  else: out = {g: 'new' if r[g] == r['ref'] else 'old' if r[g] == r['noprod'] else 'other' for g in ('gap0', 'gap1')}
  diff = sorted({i // 128 for i in range(len(r['ref'])) if r['ref'][i] != r['noprod'][i]})
  first_bad = {g: [i // 128 for i in range(len(r['ref'])) if r[g][i] != r['ref'][i]][:1] for g in ('gap0', 'gap1')}
  return out, stable, diff, first_bad


def _matrix_cases():
  m = _records('2026-11-18-sfpu-matrix-card1.jsonl')
  single = {r['name']: dict(slope=r['slope'], spread=r['spread']) for r in m if r['kind'] == 'single'}
  pair = {(r['producer'], r['consumer']): {k: r[k] for k in ('slope_gap0', 'slope_gap1', 'value_gap0', 'value_gap1',
                                                              'stable', 'sensitive_slots', 'first_bad')}
          for r in m if r['kind'] == 'pair'}
  ex = lambda v: None if v is None else {'card1': v}
  for p, pw in PRODUCERS:
    yield dict(id=f'matrix-single-{p}', group='matrix', kind='single', name=p, word=hex(pw), expect=ex(single.get(p)),
               tiles=[TILE])
    for c, cw in CONSUMERS:
      yield dict(id=f'matrix-pair-{p}-{c}', group='matrix', kind='pair', producer=p, consumer=c, pword=hex(pw),
                 cword=hex(cw), expect=ex(pair.get((p, c))), tiles=[TILE])
  for c, cw in CONSUMERS:
    yield dict(id=f'matrix-consumer-{c}', group='matrix', kind='single', name='C:' + c, word=hex(cw),
               expect=ex(single.get('C:' + c)), tiles=[TILE])


def run_matrix(card, case, timeout):
  want = _expected(case, card)
  if case['kind'] == 'single':
    s, spread, rows = m_slope(card, [int(case['word'], 16)], timeout)
    return dict(slope=s, spread=spread, points=rows, cfg=_cfg(card, 'trisc1'),
                match=None if want is None else abs(s - want['slope']) <= TOL)
  prod, cons = int(case['pword'], 16), int(case['cword'], 16)
  rec = {}
  for gap in (0, 1):
    s, spread, rows = m_slope(card, [prod, *[NOP] * gap, cons], timeout)
    rec.update({f'slope_gap{gap}': s, f'spread_gap{gap}': spread, f'points_gap{gap}': rows})
  v, stable, slots, first_bad = m_values(card, prod, cons, timeout)
  rec.update(value_gap0=v['gap0'], value_gap1=v['gap1'], stable=stable, sensitive_slots=slots, first_bad=first_bad,
             cfg=_cfg(card, 'trisc1'))
  if want is not None:
    rec['match'] = (all(abs(rec[k] - want[k]) <= TOL for k in ('slope_gap0', 'slope_gap1'))
                    and all(rec[k] == want[k] for k in ('value_gap0', 'value_gap1', 'sensitive_slots', 'first_bad')))
  return rec


# ================================================================ loadmacro (old test_sfpu_loadmacro.py)

SIMPLE, MADU, ROUND, STORE = range(4)
def lm(slot=0, vd=0, mod0=3, addrmod=0, addr=0): return 0x93 << 24 | slot << 22 | (vd & 3) << 20 | mod0 << 16 | addrmod << 13 | addr
def byte(sel, delay=0, x_in_vb=0, l16=0): return sel | delay << 3 | l16 << 6 | x_in_vb << 7


def lm_configure(slot, templates, units, misc=3):
  """templates: up to 4 words (VD replaced by 12+i, backdoor write). units: {unit: byte}."""
  s = [t & ~0xF0 | (12 + i) << 4 for i, t in enumerate(templates)]
  seq = sum(b << 8 * u for u, b in units.items())
  return s + [SFPLOADI(0, 8, seq >> 16), SFPLOADI(0, 10, seq & 0xFFFF), NOP, W('CONFIG', 4 + slot, mod=0),
              W('CONFIG', 8, imm16=misc, mod=1), NOP]


NEG, HALF, RND = W('MOV', 0, vc=0, mod=1), W('MUL', 0, va=6, vb=0, vc=9), W('STOCHRND', 0, vc=0, mod=1)
TEMPLATES = [NEG, HALF, RND]
LM_CONFIGS = {
  'none': {},
  'simple': {SIMPLE: byte(4)},
  'mad': {MADU: byte(5, x_in_vb=1)},
  'round': {ROUND: byte(6)},
  'store': {STORE: byte(3, delay=2)},
  'simple+store': {SIMPLE: byte(4), STORE: byte(3, delay=1)},
  'simple+mad': {SIMPLE: byte(4), MADU: byte(5, delay=1, x_in_vb=1)},
  'all4': {SIMPLE: byte(4), MADU: byte(5, delay=1, x_in_vb=1), ROUND: byte(6, delay=3, l16=1), STORE: byte(3, delay=4)},
}
LM_TIMED = list(LM_CONFIGS)  # test_throughput ran these; the rest were added by test_execution_cycle / test_collisions
LM_CONFIGS.update({f'simple_d{d}': {SIMPLE: byte(4, delay=d)} for d in range(4)})
LM_CONFIGS.update({f'mad_d{d}': {MADU: byte(5, delay=d, x_in_vb=1)} for d in range(3)})
LM_CONFIGS['store_d0'] = {STORE: byte(3, delay=0)}
LM_UNITS = {
  'lm': lambda i: [lm(vd=i % 4)],
  'lm_nop': lambda i: [lm(vd=i % 4), NOP],
  'lm_mov': lambda i: [lm(vd=i % 4), W('MOV', 5, vc=6)],
  'lm_mul': lambda i: [lm(vd=i % 4), W('MUL', 5, va=6, vb=6, vc=9)],
  'lm_load': lambda i: [lm(vd=i % 4), W('LOAD', 5, mod0=3, low=0)],
}
LM_COLLISIONS = {
  'simple_vs_regular_simple': ('simple', [lm(vd=0), W('MOV', 4, vc=6)]),
  'simple_vs_regular_mad': ('simple', [lm(vd=0), W('MUL', 4, va=6, vb=6, vc=9)]),
  'mad_vs_regular_mad': ('mad', [lm(vd=0), W('MUL', 4, va=6, vb=6, vc=9)]),
  'mad_vs_regular_simple': ('mad', [lm(vd=0), W('MOV', 4, vc=6)]),
  'store_d0_vs_regular_store': ('store_d0', [lm(vd=0), SFPSTORE(6, 3, 0, 0)]),
  'none_regular_mov': ('none', [lm(vd=0), W('MOV', 4, vc=6)]),
}
DST0 = 0x40000000  # 2.0 in every Dst word


def lm_setup(config): return [SFPENCC(0, 0, 0, 2), *init_regs(), *lm_configure(0, TEMPLATES, LM_CONFIGS[config])]
def lm_body(unit): return [w for i in range(BODY) for w in LM_UNITS[unit](i)]
def lm_exec_body(k): return [lm(vd=0), *[NOP] * (k - 1), W('MOV', 4, vc=0)]


def lm_compute(config, body, misc=3):
  return [SFPENCC(0, 0, 0, 2), *lm_configure(0, TEMPLATES, LM_CONFIGS[config], misc), *init_regs(), DRAIN, *body,
          *[NOP] * 8, DRAIN, *[SFPSTORE(r, 3, 0, (1 + r) * 8 + pos * 2) for r in range(8) for pos in range(4)], DRAIN]


def _loadmacro_cases():
  recs = _records('2026-11-18-sfpu-loadmacro-card1.jsonl')
  regs = lambda r: {k: r[k] for k in (*(f'L{i}' for i in range(8)), 'dst0')}
  timing = {(r['config'], r['unit']): {'card1': dict(slope=r['slope'])} for r in recs if r['kind'] == 'loadmacro_timing'}
  execs = {(r['unit'], r['delay'], r['k']): {'card1': regs(r)} for r in recs if r['kind'] == 'loadmacro_exec'}
  coll = {r['case']: {'card1': regs(r)} for r in recs if r['kind'] == 'loadmacro_collision'}
  for config in LM_TIMED:
    for unit in LM_UNITS:
      yield dict(id=f'loadmacro-timing-{config}-{unit}', group='loadmacro', kind='timing', config=config, unit=unit,
                 expect=timing.get((config, unit)), tiles=[TILE])
  for unit, delays in (('simple', 4), ('mad', 3)):
    for d in range(delays):
      for k in range(1, 7):
        yield dict(id=f'loadmacro-exec-{unit}-d{d}-k{k}', group='loadmacro', kind='exec', unit=unit, delay=d, k=k,
                   config=f'{unit}_d{d}', expect=execs.get((unit, d, k)), tiles=[TILE])
  for name, (config, _) in LM_COLLISIONS.items():
    yield dict(id=f'loadmacro-collision-{name}', group='loadmacro', kind='collision', case=name, config=config,
               expect=coll.get(name), tiles=[TILE])


def run_loadmacro(card, case, timeout):
  want = _expected(case, card)
  if case['kind'] == 'timing':
    image = _loop_image(lm_setup(case['config']), lm_body(case['unit']), [NOP] * 8)
    rows = _points(card, image, M_COUNTS, 4, timeout)
    slope = (rows[1]['median'] - rows[0]['median']) / ((M_COUNTS[1] - M_COUNTS[0]) * BODY)
    return dict(slope=slope, points=rows, cfg=_cfg(card, 'trisc1'),
                match=None if want is None else abs(slope - want['slope']) <= TOL)
  body = lm_exec_body(case['k']) if case['kind'] == 'exec' else LM_COLLISIONS[case['case']][1]
  got = _value_launch(card, _value_images(lm_compute(case['config'], body)), DST0, timeout)
  rec = {f'L{r}': hex(got[(1 + r) * 128]) for r in range(8)}
  rec['dst0'] = sorted({hex(v) for v in got[0:128]})
  return dict(rec, cfg=_cfg(card, 'trisc1'), match=None if want is None else rec == want)


# ================================================================ dst (old test_sfpu_dst.py)

A, B, READY, DOUT = 0x40000, 0x40800, 0x41000, 0x42000
STAMPS = 0x41100


def d_initial():  # test_fpu_sfpu_interleave.initial(): A = B = 1/64 (bf16), READY = 0, OUTPUT poisoned
  return {A: pack('<1024H', *[0x3c80] * 1024), B: pack('<1024H', *[0x3c80] * 1024), READY: bytes(16), STAMPS: bytes(32),
          DOUT: b'\xa5' * (3 * 4096 + 64)}


def d_setup(): return [SFPENCC(0, 0, 0, 2), *(w for reg in range(8) for w in constant(reg, 0.))]


def d_body(gap, gap_kind, batch=1, sf_row=None, sfpu='load'):
  gapw, w = TTNOP if gap_kind == 'ttnop' else SFPNOP, []
  for start in range(0, 16, batch):
    w += [ELWMUL(0, 0, 0, 0, (i % 8) * 8) for i in range(start, start + batch)]
    w += [gapw] * gap
    for i in range(start, start + batch):
      row = (i % 8) * 8 if sf_row is None else sf_row + 2 * (i % 16)
      w.append(SFPLOAD(i % 4, 3, 0, row) if sfpu == 'load' else SFPSTORE(i % 4, 3, 0, row) if sfpu == 'store'
               else SFPMAD(10, 10, i % 4, i % 4, 0))
  return w


def d_value_words(gap, gap_kind): return [ELWMUL(0, 0, 0, 0, 0), *[TTNOP if gap_kind == 'ttnop' else SFPNOP] * gap, SFPLOAD(0, 3, 0, 0)]


def d_images(math_defines):
  return {'trisc0': build('k_sfpu_dst.c', 'trisc0', PART=0),
          'trisc1': build('k_sfpu_dst.c', 'trisc1', PART=1, SETUP=stream(d_setup()), **math_defines),
          'trisc2': build('k_sfpu_dst.c', 'trisc2', PART=2)}


def d_value_images(gap, gap_kind): return d_images(dict(COMPUTE=stream(d_value_words(gap, gap_kind))))
def d_loop_images(*a, **k): return d_images(dict(LOOP=1, BODY=words(d_body(*a, **k))))


def d_timing(card, images, timeout):
  meds, pts = [], []
  for n in (16, 48):
    s = []
    for _ in range(4):
      card.run([(TILE, images, {'trisc1': [n]}, d_initial())], timeout, DST_SITES)
      s.append(_stamps(card, 'trisc1'))
    meds.append(median(s[1:]))
    pts.append(dict(iterations=n, raw_cycles=s[1:], median=meds[-1]))
  return (meds[1] - meds[0]) / (32 * 16), pts


def _dst_cases():
  recs = _records('2026-11-18-sfpu-dst-card1.jsonl')
  f2s = {(r['gap_kind'], r['gap']): {'card1': dict(values=r['values'], slope_per_pair=r['slope_per_pair'])}
         for r in recs if r['kind'] == 'fpu_to_sfpload'}
  half = {(r['sfpu'], r['where'], r['batch']): {'card1': dict(slope_per_pair=r['slope_per_pair'])}
          for r in recs if r['kind'] == 'dst_half'}
  for gap_kind in ('ttnop', 'sfpnop'):
    for gap in range(7):
      yield dict(id=f'dst-fpu_to_sfpload-{gap_kind}-gap{gap}', group='dst', kind='fpu_to_sfpload', gap=gap,
                 gap_kind=gap_kind, expect=f2s.get((gap_kind, gap)), tiles=[TILE])
  for sfpu in ('load', 'store', 'mad'):
    for where, row in (('same_rows', None), ('same_half', 128), ('other_half', 256 + 128)):
      if sfpu == 'mad' and where != 'same_rows': continue
      for batch in (1, 2, 4, 8, 16):
        yield dict(id=f'dst-half-{sfpu}-{where}-b{batch}', group='dst', kind='dst_half', sfpu=sfpu, where=where,
                   sf_row=row, batch=batch, expect=half.get((sfpu, where, batch)), tiles=[TILE])


def run_dst(card, case, timeout):
  want = _expected(case, card)
  if case['kind'] == 'dst_half':
    slope, pts = d_timing(card, d_loop_images(0, 'ttnop', batch=case['batch'], sf_row=case['sf_row'], sfpu=case['sfpu']),
                          timeout)
    return dict(slope_per_pair=slope, points=pts, cfg=_cfg(card, 'trisc1'),
                match=None if want is None else abs(slope - want['slope_per_pair']) <= TOL)
  gap, kind = case['gap'], case['gap_kind']
  images, seen = d_value_images(gap, kind), []
  for _ in range(3):
    card.run([(TILE, images, {}, d_initial())], timeout, DST_SITES)
    seen.append(sorted(set(unpack('<128f', card.iface.read(TILE, DOUT + 2 * 4096, 512)))))
  slope, pts = d_timing(card, d_loop_images(gap, kind), timeout)
  rec = dict(values=[[float(x) for x in s] for s in seen], expected_new=1 / 64 + 1 / 4096, expected_old=1 / 64,
             slope_per_pair=slope, pair_insns=2 + gap, points=pts, cfg=_cfg(card, 'trisc1'))
  if want is not None: rec['match'] = rec['values'] == want['values'] and abs(slope - want['slope_per_pair']) <= TOL
  return rec


# ================================================================ runner interface

CASES = [*_hazard_cases(), *_matrix_cases(), *_loadmacro_cases(), *_dst_cases()]
RUN = {'hazards': run_hazard, 'matrix': run_matrix, 'loadmacro': run_loadmacro, 'dst': run_dst}


def run(card, case, timeout):
  return RUN[case['group']](card, case, timeout)
