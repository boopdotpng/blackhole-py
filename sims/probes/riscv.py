"""RISC-V core timing on the five baby RISCs (k_riscv.c): one fixed asm body in a counted loop, 64/128/256
iterations, one discarded warmup + 7 measured samples per point, all inside one launch. Slope = difference of
adjacent medians / difference of body operations (the old tests/timing/test_instruction_timing.py method, so the
`old` group compares 1:1 with boop-docs/timing/evidence/riscv-card0.jsonl). See RISCV.md.

  python3 sims/probes/run.py --device 0 --output sims/results/<date>-riscv-card0.jsonl riscv
  python3 sims/probes/riscv.py --verify          # build every case, prove the timed bytes are exactly our asm
  python3 sims/probes/riscv.py --disasm addi_dep-brisc

Each case dict carries its asm (so the jsonl keeps the experiment), 'sink' (expected a1 after FINISH per iteration
count, None if not deterministic) and 'expect' (what the slope should be: the old measurement for ported cases,
DOC = tt-isa-documentation BabyRISCV/README.md, HYP = a hypothesis this case tests).
"""
import hashlib, re, struct, sys
from statistics import median

from tile import LAYOUT, build

TILE = (1, 2)
ROLES = ('brisc', 'ncrisc', 'trisc0', 'trisc1', 'trisc2')
TRISCS = ROLES[2:]
BT = ('brisc',) + TRISCS  # roles that map TENSIX_CFG / GPRs / TDMA (not NCRISC)
COUNTS, SAMPLES, BODY, HEADER = (64, 128, 256), 8, 16, 8
MASK = 0xFFFFFFFF

# cfg0 (CSR 0x7c0) bits, tt-isa-documentation BabyRISCV/CSRs.md
DIS_BP, DIS_L0, DIS_CSR_SYNC, DIS_TRISC_FUSION, NO_PERIODIC_FLUSH = 1 << 1, 1 << 3, 1 << 10, 1 << 18, 1 << 24
def BP_HIST(n): return n << 26
L0_ON = dict(cfg0_clear=DIS_L0, cfg0_set=NO_PERIODIC_FLUSH)  # L0 data cache on, without the ~0.8% random flush

WALL = 0xFFB121F0
LOCAL = 0xFFB00080  # own local data RAM (fast path); the stack is at the top, firmware uses none of this
LOCAL_SLOW = {'brisc': 0xFFB14080, 'ncrisc': 0xFFB16080, 'trisc0': 0xFFB18080, 'trisc1': 0xFFB1A080, 'trisc2': 0xFFB1C080}
NOP = 0x02000000  # Tensix NOP
PC_BUF_SYNC = 0xFFE80004  # TRISC: CoprocessorDoneCheck
def scratch(role): return LAYOUT[role]['res'] + 0x8000  # per-role L1 scratch, inside the role's (unused) log area
def f32(x): return struct.unpack('<I', struct.pack('<f', x))[0]

# ---- old evidence: riscv-card0.jsonl / riscv-l0-enabled-card0.jsonl / context-card0.jsonl (2026-09-09, card 0)
# (mean of the two adjacent slopes per body op, medians at 64/128/256 iterations), per role in ROLES order
_OLD = {
  'empty': [(0.125, (158, 286, 542)), (0.125, (159, 287, 543)), (0.1248, (159, 287, 542)), (0.1252, (158, 286, 543)), (0.1248, (159, 287, 542))],
  'addi_dep': [(1.1248, (1186, 2337, 4642)), (1.125, (1182, 2334, 4638)), (1.125, (1182, 2334, 4638)), (1.125, (1182, 2334, 4638)), (1.125, (1182, 2334, 4638))],
  'add_dep': [(1.1252, (1186, 2338, 4643)), (1.125, (1182, 2334, 4638)), (1.1255, (1182, 2335, 4639)), (1.125, (1182, 2334, 4638)), (1.125, (1182, 2334, 4638))],
  'xor_dep': [(1.1248, (1186, 2337, 4642)), (1.125, (1182, 2334, 4638)), (1.125, (1182, 2334, 4638)), (1.125, (1182, 2334, 4638)), (1.1235, (1185, 2334, 4638))],
  'mul_dep': [(2.0625, (2144, 4256, 8480))] * 5,
  'mul_ind4': [(1.125, (1186, 2337, 4643)), (1.125, (1182, 2334, 4638)), (1.1252, (1182, 2334, 4639)), (1.125, (1182, 2334, 4638)), (1.125, (1185, 2337, 4641))],
  'divu_one': [(2.125, (2208, 4384, 8736))] * 5,
  'divu_large': [(33.125, (33952, 67872, 135712))] * 5,
  'remu_large': [(33.125, (33952, 67872, 135712))] * 5,
  'fence': [(4.125, (4260, 8484, 16932))] * 5,
  'csr_cycle': [(4.125, (4256, 8480, 16928))] * 5,
  'load_l1_hot_dep': [(8.0, (8224, 16416, 32800)), (7.9988, (8231, 16422, 32803)), (8.0002, (8214, 16406, 32791)), (8.0, (8214, 16406, 32790)), (8.0002, (8214, 16407, 32790))],
  'load_l1_miss_dep': [(7.9993, (8224, 16413, 32800)), (8.001, (8227, 16421, 32805)), (8.0007, (8214, 16408, 32791)), (8.0, (8214, 16406, 32790)), (7.9995, (8215, 16406, 32790))],
  'store_l1_same': [(1.1245, (1193, 2344, 4648)), (1.125, (1184, 2336, 4640)), (1.1255, (1188, 2341, 4645)), (1.1265, (1184, 2339, 4643)), (1.1252, (1187, 2339, 4644))],
  'store_l1_coalesced': [(1.1248, (1192, 2344, 4647)), (1.125, (1184, 2336, 4640)), (1.1255, (1188, 2342, 4644)), (1.126, (1184, 2340, 4640)), (1.1238, (1191, 2342, 4643))],
  'fadd_dep': [(2.1252, (2209, 4386, 8737)), (2.125, (2207, 4383, 8735)), (2.125, (2207, 4383, 8735)), (2.125, (2207, 4383, 8735)), (2.125, (2207, 4383, 8735))],
  'fadd_ind4': [(1.125, (1191, 2343, 4647)), (1.125, (1183, 2335, 4639)), (1.125, (1183, 2335, 4639)), (1.125, (1183, 2335, 4639)), (1.1245, (1185, 2335, 4641))],
  'fmul_dep': [(2.1245, (2209, 4383, 8737)), (2.125, (2207, 4383, 8735)), (2.125, (2207, 4383, 8735)), (2.125, (2207, 4383, 8735)), (2.125, (2207, 4383, 8735))],
  'fmadd_dep': [(2.125, (2209, 4385, 8737)), (2.125, (2207, 4383, 8735)), (2.125, (2207, 4383, 8735)), (2.125, (2207, 4383, 8735)), (2.1255, (2206, 4383, 8735))],
}
_OLD_L0ON = {
  'load_l1_hot_dep': [(2.1301, (2245, 4453, 8762)), (2.1301, (2251, 4459, 8768)), (2.1306, (2246, 4455, 8764)), (2.1299, (2245, 4453, 8761)), (2.1299, (2246, 4454, 8762))],
  'load_l1_miss_dep': [(8.0, (8222, 16414, 32798)), (7.9993, (8231, 16423, 32804)), (7.9998, (8215, 16407, 32790)), (8.0, (8215, 16407, 32791)), (7.9995, (8215, 16406, 32790))],
}
_OLD_LOCAL = [(2.0625, (2145, 4257, 8481))] * 5  # context-card0.jsonl local_load_points, every role


def _old(table, name, role, src):
  slope, medians = table[name][ROLES.index(role)]
  return dict(slope=slope, medians=list(medians), src=src)


def _hyp(per_iter, ops, src='HYP', **kw):
  return dict(slope=round(per_iter / ops, 4), per_iter=per_iter, src=src, **kw)


# ---- asm helpers
def lines(*xs): return ''.join(x if x.endswith('\n') else x + '\n' for x in xs if x)
def li(reg, v): return f'li {reg}, {v & MASK:#x}\n'
def store_word(addr, value): return li('t3', addr) + li('t4', value) + 'sw t4, 0(t3)\n'
def chain(base, n, stride):  # pointer ring: word at base + i*stride holds base + ((i+1) % n)*stride
  return ''.join(store_word(base + i * stride, base + (i + 1) % n * stride) for i in range(n))
ROT = ('t3', 't4', 't5', 't6', 'a4', 'a5', 'a6', 'a7')  # destinations for independent loads: 8, one per retire slot
SINK_A6 = 'mv a1, a6\nsw a1, 0(s11)\n'
SINK_A3 = 'mv a1, a3\nsw a1, 0(s11)\n'
FP_FINISH = 'fmv.x.w a1, f0\nsw a1, 0(s11)\n'


def base_setup(role, ptr=None):
  ptr = scratch(role) + 0x100 if ptr is None else ptr
  return lines(li('a1', 3), li('a2', 1), li('a3', ptr), *(li(r, 3) for r in ('a4', 'a5', 'a6', 'a7')))


CASES = []


def add(name, role, group, body, ops=BODY, setup='', init='', finish=None, tail='', sink=None, expect=None,
        cfg0_set=0, cfg0_clear=0, restore=None, count0=COUNTS[0], pair=False, note='', **extra):
  counts = [count0, 2 * count0, 4 * count0]
  if callable(sink): sink = {str(c): sink(c) & MASK for c in counts}
  elif sink is not None: sink = {str(c): sink & MASK for c in counts}
  CASES.append(dict(id=f'{name}-{role}', case=name, role=role, group=group, tiles=[TILE], counts=counts, ops=ops,
                    asm=dict(init=init, setup=setup, body=body, finish=finish, tail=tail), sink=sink, expect=expect,
                    cfg0_set=cfg0_set, cfg0_clear=cfg0_clear, restore=restore, pair=pair, note=note, **extra))


# ---- 1. old cases (test_instruction_timing.py rv_body), every role; ids '<case>-<role>' as in riscv-card0.jsonl
def _old_cases(role):
  P = scratch(role) + 0x100
  base = base_setup(role, P)
  fp = base + li('t3', 0x3F800000) + ''.join(f'fmv.w.x f{i}, t3\n' for i in range(5)) + 'fmv.w.x f5, zero\n'
  ring = lambda n: chain(P, n, 16)
  rep = lambda f: ''.join(f(i) + '\n' for i in range(BODY))
  big = lines(base, li('a3', MASK), li('a2', 3))
  table = {  # name: (body, setup, init, finish, sink(n))
    'empty': ('', base, '', None, lambda n: 3),
    'addi_dep': (rep(lambda i: 'addi a1, a1, 1'), base, '', None, lambda n: 3 + BODY * n),
    'add_dep': (rep(lambda i: 'add a1, a1, a2'), base, '', None, lambda n: 3 + BODY * n),
    'xor_dep': (rep(lambda i: 'xor a1, a1, a2'), base, '', None, lambda n: 3),
    'mul_dep': (rep(lambda i: 'mul a1, a1, a2'), base, '', None, lambda n: 3),
    'mul_ind4': (rep(lambda i: f'mul a{4 + i % 4}, a{4 + i % 4}, a2'), base, '', None, lambda n: 3),
    'divu_one': (rep(lambda i: 'divu a1, a1, a2'), base, '', None, lambda n: 3),
    'divu_large': (rep(lambda i: 'divu a1, a3, a2'), big, '', None, lambda n: 0x55555555),
    'remu_large': (rep(lambda i: 'remu a1, a3, a2'), big, '', None, lambda n: 0),
    'fence': (rep(lambda i: 'fence'), base, '', None, lambda n: 3),
    'csr_cycle': (rep(lambda i: 'csrrs a1, cycle, zero'), base, '', None, None),
    'load_l1_hot_dep': (rep(lambda i: 'lw a1, 0(a1)'), base + li('a1', P), ring(1), None, lambda n: P),
    'load_l1_miss_dep': (rep(lambda i: 'lw a1, 0(a1)'), base + li('a1', P), ring(8), None, lambda n: P),
    'store_l1_same': (rep(lambda i: 'sw a2, 0(a3)'), base, '', None, lambda n: 3),
    'store_l1_coalesced': (rep(lambda i: f'sw a2, {i % 4 * 4}(a3)'), base, '', None, lambda n: 3),
    'fadd_dep': (rep(lambda i: 'fadd.s f0, f0, f4, rne'), fp, '', FP_FINISH, lambda n: f32(1 + BODY * n)),
    'fadd_ind4': (rep(lambda i: f'fadd.s f{i % 4}, f{i % 4}, f4, rne'), fp, '', FP_FINISH, lambda n: f32(1 + BODY // 4 * n)),
    'fmul_dep': (rep(lambda i: 'fmul.s f0, f0, f4, rne'), fp, '', FP_FINISH, lambda n: f32(1.0)),
    'fmadd_dep': (rep(lambda i: 'fmadd.s f0, f0, f4, f5, rne'), fp, '', FP_FINISH, lambda n: f32(1.0)),
  }
  for name, (body, setup, init, finish, sink) in table.items():
    # the firmware runs with the L0 data cache on, so the L1 load chains compare with the old L0-enabled run
    old = (_OLD_L0ON, 'riscv-l0-enabled-card0.jsonl') if name in _OLD_L0ON else (_OLD, 'riscv-card0.jsonl')
    add(name, role, 'old', body, setup=setup, init=init, finish=finish, sink=sink, expect=_old(old[0], name, role, old[1]))
  for name in ('load_l1_hot_dep', 'load_l1_miss_dep'):  # riscv-l0-enabled-card0.jsonl: TIMING_CLEAR_CFG0_BITS=0x8
    body, setup, init, _, sink = table[name]
    add(name + '-l0on', role, 'old', body, setup=setup, init=init, sink=sink, cfg0_clear=DIS_L0,
        expect=_old(_OLD_L0ON, name, role, 'riscv-l0-enabled-card0.jsonl'))
    add(name + '-l0on-noflush', role, 'l1', body, setup=setup, init=init, sink=sink, **L0_ON,
        expect=_hyp(16 * 2 + 1 if 'hot' in name else 16 * 8 + 2, BODY),
        note='periodic L0 flush off: the old 2.13 should drop to the local-RAM 2.0625')
  # context-card0.jsonl: dependent load chain in own local data RAM (fast path)
  add('local_load_dep', role, 'old', rep(lambda i: 'lw a1, 0(a1)'), setup=base + li('a1', LOCAL),
      init=store_word(LOCAL, LOCAL), sink=LOCAL, expect=dict(slope=_OLD_LOCAL[0][0], medians=list(_OLD_LOCAL[0][1]),
                                                              src='context-card0.jsonl'))


# ---- 2. branches, jumps, calls
def _rotl(x, k): k %= 32; return (x << k | x >> (32 - k)) & MASK if k else x


PATTERNS = {'always': 0xFFFFFFFF, 'never': 0, 'alt': 0xAAAAAAAA, 'p4': 0xCCCCCCCC, 'p4_1': 0x88888888,
            'p8': 0xF0F0F0F0, 'p8_1': 0x80808080, 'p16': 0xFF00FF00, 'p32': 0xFFFF0000, 'p32_1': 0x80000000,
            'p32_31': 0x7FFFFFFF, 'rand32': 0x9E3779B9}


def _not_taken(pat, n, per_iter):  # a5 rotated left by 1 at the top of every iteration; bltz = taken when bit 31 set
  return sum(per_iter for k in range(1, n + 1) if not _rotl(pat, k) >> 31)


def _branch_cases(role):
  setup = lines(li('a1', 3), li('a6', 0))
  skip = 'addi a6, a6, 1\n'  # executed only on the not-taken path, so a6 counts not-taken branches
  # straight-line forms, 16 per iteration
  forms = {
    'br_taken_skip': 'beq zero, zero, 1f\n' + skip + '1:\n',
    'br_taken_next': 'beq zero, zero, 1f\n1:\n',
    'br_nottaken': 'bne zero, zero, 89f\n',
    'jal_skip': 'j 1f\n' + skip + '1:\n',
    'jal_next': 'j 1f\n1:\n',
  }
  for name, op in forms.items():
    add(name, role, 'branch', op * BODY, setup=setup, finish=SINK_A6, tail='89:\nj 99f\n', sink=0,
        expect=_hyp(18, BODY, 'DOC', model='1 per correctly predicted branch/jump + 2 loop'))
  for name in ('br_taken_skip', 'br_nottaken', 'jal_next'):
    taken = name != 'br_nottaken'
    add(name + '-disbp', role, 'branch', forms[name] * BODY, setup=setup, finish=SINK_A6, tail='89:\nj 99f\n',
        sink=0, cfg0_set=DIS_BP, expect=_hyp(16 * (5 if taken else 1) + 2 + 4, BODY,
                                             model='predictor off = static not-taken: +4 per taken (loop branch too)'))
  add('empty-disbp', role, 'branch', '', setup=setup, finish=SINK_A6, sink=0, cfg0_set=DIS_BP,
      expect=_hyp(2 + 4, BODY, model='loop branch mispredicted every iteration: +4 (DOC)'))
  # indirect: auipc + jalr to the next pair (8 pairs), and to skip one instruction
  add('jalr_next', role, 'branch', 'auipc t3, 0\njalr zero, 8(t3)\n' * 8, setup=setup, finish=SINK_A6, sink=0,
      expect=_hyp(18, BODY, 'DOC'))
  add('jalr_skip', role, 'branch', ('auipc t3, 0\njalr zero, 12(t3)\n' + skip) * 8, setup=setup, finish=SINK_A6,
      sink=0, expect=_hyp(18, BODY, 'DOC'))
  # calls: 16 call sites to one shared leaf (its ret has 16 targets) vs 16 private leaves (one target each)
  leaf = 'addi a6, a6, 1\nret\n'
  add('call_ret_shared', role, 'branch', 'jal ra, 50f\n' * BODY, setup=setup, finish=SINK_A6,
      tail='50:\n' + leaf, sink=lambda n: BODY * n,
      expect=_hyp(16 * (3 + 4) + 2, BODY, model='no return-address stack (WH docs): ret predicted from its last target'))
  add('call_ret_private', role, 'branch', ''.join(f'jal ra, {50 + i}f\n' for i in range(BODY)), setup=setup,
      finish=SINK_A6, tail=''.join(f'{50 + i}:\n' + leaf for i in range(BODY)), sink=lambda n: BODY * n,
      expect=_hyp(16 * 3 + 2, BODY, model='every ret has one target: predicted'))
  add('call_ret_private-disbp', role, 'branch', ''.join(f'jal ra, {50 + i}f\n' for i in range(BODY)), setup=setup,
      finish=SINK_A6, tail=''.join(f'{50 + i}:\n' + leaf for i in range(BODY)), sink=lambda n: BODY * n,
      cfg0_set=DIS_BP, expect=_hyp(16 * (3 + 8) + 6, BODY))
  add('call_ret_one', role, 'branch', 'jal ra, 50f\n' + 'addi a1, a1, 1\n' * 15, setup=setup, finish=SINK_A6,
      tail='50:\n' + leaf, sink=lambda n: n, expect=_hyp(3 + 15 + 2, BODY))
  # taken-branch density: k of 16 slots are an always-taken branch over one instruction, the rest addi a1
  for k in (1, 2, 4, 8):
    slots = ''.join('beq zero, zero, 1f\naddi a1, a1, 1000\n1:\n' if i % (BODY // k) == 0 else 'addi a1, a1, 1\n'
                    for i in range(BODY))
    add(f'bd_taken-k{k}', role, 'branch', slots, setup=setup, sink=lambda n, k=k: 3 + (BODY - k) * n,
        expect=_hyp(18, BODY, 'DOC'))
    slots = ''.join('bne zero, zero, 89f\n' if i % (BODY // k) == 0 else 'addi a1, a1, 1\n' for i in range(BODY))
    add(f'bd_nottaken-k{k}', role, 'branch', slots, setup=setup, tail='89:\nj 99f\n',
        sink=lambda n, k=k: 3 + (BODY - k) * n, expect=_hyp(18, BODY, 'DOC'))
  # direction patterns. bp15: rori a5 + 15 bltz on a5 (all 15 see the same direction this iteration).
  # bp1: rori a5 + one bltz + 14 addi a1 (one pattern branch per iteration: penalty per mispredict directly).
  for pname, pat in PATTERNS.items():
    z = sum(1 for k in range(32) if not _rotl(pat, k) >> 31) / 32  # fraction of iterations not taken
    s = lines(li('a1', 3), li('a5', pat), li('a6', 0))
    br = 'bltz a5, 1f\n' + skip + '1:\n'
    add(f'bp15-{pname}', role, 'branch', 'rori a5, a5, 31\n' + br * 15, setup=s, finish=SINK_A6,
        sink=lambda n, pat=pat: _not_taken(pat, n, 15),
        expect=_hyp(1 + 15 + 15 * z + 2, BODY, model='perfect prediction; +4 per mispredict on top (DOC)'))
    add(f'bp1-{pname}', role, 'branch', 'rori a5, a5, 31\n' + br + 'addi a1, a1, 1\n' * 14, setup=s,
        finish=SINK_A6, sink=lambda n, pat=pat: _not_taken(pat, n, 1),
        expect=_hyp(1 + 1 + z + 14 + 2, BODY, model='perfect prediction; +4 per mispredict on top (DOC)'))
    if pname in ('always', 'never', 'alt', 'p4'):
      add(f'bp1-{pname}-disbp', role, 'branch', 'rori a5, a5, 31\n' + br + 'addi a1, a1, 1\n' * 14, setup=s,
          finish=SINK_A6, sink=lambda n, pat=pat: _not_taken(pat, n, 1), cfg0_set=DIS_BP,
          expect=_hyp(1 + 1 + z + (1 - z) * 4 + 14 + 2 + 4, BODY, model='static not-taken, +4 per taken'))
    if pname in ('alt', 'p4', 'p8', 'rand32'):
      for h in (1, 2, 3):
        add(f'bp15-{pname}-histsel{h}', role, 'branch', 'rori a5, a5, 31\n' + br * 15, setup=s, finish=SINK_A6,
            sink=lambda n, pat=pat: _not_taken(pat, n, 15), cfg0_set=BP_HIST(h),
            expect=_hyp(1 + 15 + 15 * z + 2, BODY), note='cfg0 BpHistSel (undocumented) = %d' % h)
  # inner loop of L iterations inside the timed loop: the inner exit branch mispredicts unless L is learned
  for L in (1, 2, 3, 4, 6, 8, 16):
    add(f'bp_inner-L{L}', role, 'branch', li('a4', L) + '1:\naddi a6, a6, 1\naddi a4, a4, -1\nbnez a4, 1b\n',
        ops=1 + 3 * L, setup=setup, finish=SINK_A6, sink=lambda n, L=L: L * n,
        expect=_hyp(1 + 3 * L + 2 + (4 if L > 1 else 0), 1 + 3 * L, model='exit mispredicted once per inner loop'))


# ---- 3. MMIO and memory-region loads/stores
def _targets(role):
  t = {  # name: (address, roles, writable, documented load latency)
    'wallclock': (WALL, ROLES, False, 7),
    'niu0_id': (0xFFB20148, ROLES, False, 7),
    'niu1_id': (0xFFB30148, ROLES, False, 7),
    'niu0_status': (0xFFB20200, ROLES, False, 7),  # NIU_MST_ATOMIC_RESP_RECEIVED counter
    'niu0_cmdbuf': (0xFFB21800, ROLES, True, 7),  # NoC0 command buffer 3, TARG_LO (restored after the launch)
    'overlay': (0xFFB40000 + 39 * 0x1000 + 8 * 4, ROLES, True, 7),  # stream 39 reg 8 (a CB counter; fw resets it)
    'tdma': (0xFFB11024, BT, False, 4),  # TDMA_CLK_GATE_EN
    'cfg': (0xFFEF0000 + 100 * 4, BT, True, 4),  # Tensix backend config word 100 (bank 0; fw zeroes it per launch)
    'gpr': (0xFFE00000 + 63 * 4, BT, True, 4),  # Tensix GPR 63 (TRISC: own thread; BRISC: thread 0)
    'pcbuf_sync': (PC_BUF_SYNC, TRISCS, False, 3),  # CoprocessorDoneCheck: returns at once with the thread idle
    'mop_sync': (0xFFE80008, TRISCS, False, 3),  # MOPExpanderDoneCheck
    'sem': (0xFFE80020, TRISCS, False, 3),  # Tensix semaphore 0 value
    'local': (LOCAL, ROLES, True, 2),
    'local_slow': (LOCAL_SLOW[role], ROLES, True, 8),
    'l1': (scratch(role) + 0x200, ROLES, True, 8),
  }
  return {k: v for k, v in t.items() if role in v[1]}


# the ISA documents a hang if a TRISC starts a second load from PC_BUF/semaphores before the first returned: those
# targets only get the dependent form, where each load's result is consumed before the next load issues
NO_BURST = ('pcbuf_sync', 'mop_sync', 'sem')


def _mmio_cases(role):
  for name, (addr, _, writable, lat) in _targets(role).items():
    s = lines(li('a1', 3), li('a2', 1), li('a3', addr))
    restore = addr if name in ('niu0_cmdbuf', 'overlay') else None
    # latency: lw t3 ; andi t4,t3,0 ; add a3,a3,t4 -- the next load's address depends on this load's data
    add(f'mmio_lat-{name}', role, 'mmio', 'lw t3, 0(a3)\nandi t4, t3, 0\nadd a3, a3, t4\n' * BODY, setup=s,
        finish=SINK_A3, sink=addr, expect=_hyp(16 * (lat + 2) + 2, BODY, 'DOC', latency=lat,
                                               model='load latency + 2 ALU per op'))
    if name not in NO_BURST:
      add(f'mmio_ldtput-{name}', role, 'mmio', ''.join(f'lw {ROT[i % 8]}, 0(a3)\n' for i in range(BODY)), setup=s,
          sink=3, expect=_hyp(16 * max(1, lat / 8) + 2, BODY, model='8 retire slots: max(1, latency/8) per load'))
    if writable:
      add(f'mmio_st-{name}', role, 'mmio', 'sw a2, 0(a3)\n' * BODY, setup=s + 'mv a2, a0\n', restore=restore,
          finish='lw a1, 0(a3)\nsw a1, 0(s11)\n', sink=lambda n: n,
          expect=_hyp(18, BODY, 'DOC', model='1 store/cycle outside L1; L1 same word coalesces'))
      add(f'mmio_rw-{name}', role, 'mmio', 'sw a1, 0(a3)\nlw a1, 0(a3)\naddi a1, a1, 1\n' * BODY, setup=s,
          restore=restore, sink=lambda n: 3 + BODY * n,
          expect=_hyp(16 * (lat + 2) + 2, BODY, model='store, overlapping load waits for the drain, then latency'))
  if role in TRISCS:  # stores that do not read back
    s = lines(li('a2', NOP), li('a3', 0xFFE40000), li('t3', PC_BUF_SYNC), 'sw zero, 0(t3)', 'lw t4, 0(t3)',
              'andi t4, t4, 0', li('a1', 3))  # drain this thread's Tensix work before each sample (untimed)
    add('mmio_st-instrn_buf', role, 'mmio', 'sw a2, 0(a3)\n' * BODY, setup=s, sink=3,
        expect=_hyp(18, BODY, 'DOC', model='Tensix NOP pushes: 1/cycle, FIFO dequeues 1/cycle'))
    tt = (NOP << 2 | NOP >> 30) & MASK
    add('mmio_st-ttinsn', role, 'mmio', f'.word {tt:#x}\n' * BODY, setup=s, sink=3,
        expect=_hyp(18, BODY, 'DOC', model='.ttinsn NOP, fused by 4 on TRISC, still dequeued 1/cycle'))
    drain = f'li t3, {PC_BUF_SYNC:#x}\nsw zero, 0(t3)\nlw t4, 0(t3)\nandi t4, t4, 0\nsw a1, 0(s11)\n'
    add('mmio_st-instrn_buf-drain', role, 'mmio', 'sw a2, 0(a3)\n' * BODY, setup=s, finish=drain, sink=3,
        expect=_hyp(18, BODY, model='timed until the Tensix thread has executed every NOP'))
    add('mmio_st-pcbuf_sync', role, 'mmio', 'sw a2, 0(a3)\n' * BODY, setup=lines(li('a1', 3), li('a2', 1), li('a3', PC_BUF_SYNC)),
        sink=3, expect=_hyp(18, BODY, 'DOC', model='discarded store'))


# ---- 4. L1 loads: width, alignment, L0 data cache, throughput
LOADS = [('lw', 0), ('lw', 4), ('lw', 12), ('lh', 0), ('lh', 2), ('lh', 14), ('lhu', 0), ('lb', 0), ('lb', 1),
         ('lb', 15), ('lbu', 0)]


def _l1_cases(role):
  Z = scratch(role) + 0x300  # 16 zero bytes: lX t3 ; add a3, a3, t3 keeps a3 and chains on the load data
  zero = store_word(Z, 0) + store_word(Z + 4, 0) + store_word(Z + 8, 0) + store_word(Z + 12, 0)
  s = lines(li('a1', 3), li('a3', Z))
  for l0, kw in (('', {}), ('-l0on', L0_ON)):
    lat = 2 if l0 else 8
    for op, off in LOADS:
      add(f'l1_ld-{op}-o{off}{l0}', role, 'l1', f'{op} t3, {off}(a3)\nadd a3, a3, t3\n' * BODY, setup=s, init=zero,
          finish=SINK_A3, sink=Z, expect=_hyp(16 * (lat + 1) + 2, BODY, 'DOC', latency=lat), **kw)
    add(f'l1_ldtput-same{l0}', role, 'l1', ''.join(f'lw {ROT[i % 8]}, 0(a3)\n' for i in range(BODY)), setup=s,
        init=zero, sink=3, expect=_hyp(18, BODY), **kw)
    add(f'l1_ldtput-lines{l0}', role, 'l1', ''.join(f'lw {ROT[i % 8]}, {16 * i}(a3)\n' for i in range(BODY)),
        setup=s, sink=3, expect=_hyp(18, BODY), **kw)
  # L0 capacity: dependent ring over N lines, L0 on (doc: 4 lines x 16 B)
  P = scratch(role) + 0x800
  for n, stride in ((1, 16), (2, 16), (3, 16), (4, 16), (5, 16), (6, 16), (8, 16), (4, 64), (4, 1024)):
    add(f'l0_ring-n{n}-s{stride}', role, 'l1', 'lw a1, 0(a1)\n' * BODY, setup=lines(li('a1', P)),
        init=chain(P, n, stride), sink=lambda c, n=n, stride=stride: P + BODY * c % n * stride, expect=_hyp(16 * 2 + 1 if n <= 4 else 16 * 8 + 2, BODY), **L0_ON)
  # L0 hit after a store to the same line (doc: the store flushes that line)
  add('l0_store_inval', role, 'l1', 'sw a2, 4(a1)\nlw a1, 0(a1)\n' * BODY, setup=lines(li('a1', P), li('a2', 1)),
      init=chain(P, 1, 16), sink=P, expect=_hyp(16 * 8 + 2, BODY, model='every load misses: line flushed by the store'),
      **L0_ON)


# ---- 5. stores, fences, store->load, atomics
def _store_cases(role):
  B = scratch(role) + 0x2000  # stores: up to + 0x780 (stride128)
  s = lines(li('a1', 3), li('a3', B), 'mv a2, a0')  # stored value = iteration count, read back as the sink
  pats = {  # name: (offsets (16), op, expected cycles per iteration)
    'seq64': ([4 * i for i in range(16)], 'sw', 18),
    'rev64': ([60 - 4 * i for i in range(16)], 'sw', 18),
    'stride16': ([16 * i for i in range(16)], 'sw', 16 * 5 + 2),
    'stride64': ([64 * i for i in range(16)], 'sw', 16 * 5 + 2),
    'stride128': ([128 * i for i in range(16)], 'sw', 16 * 5 + 2),
    'alt8': ([8 * (i % 2) for i in range(16)], 'sw', 16 * 5 + 2),
    'pairs16': ([16 * (i // 2) + 4 * (i % 2) for i in range(16)], 'sw', 8 * 5 + 2),
    'seqbyte': (list(range(16)), 'sb', 18),
    'seqhalf': ([2 * i for i in range(16)], 'sh', 18),
  }
  for name, (offs, op, it) in pats.items():
    last = offs[-1]
    rd = {'sw': 'lw', 'sh': 'lhu', 'sb': 'lbu'}[op]
    mask = {'sw': MASK, 'sh': 0xFFFF, 'sb': 0xFF}[op]
    add(f'st-{name}', role, 'store', ''.join(f'{op} a2, {o}(a3)\n' for o in offs), setup=s,
        finish=f'{rd} a1, {last}(a3)\nsw a1, 0(s11)\n', sink=lambda n, mask=mask: n & mask,
        expect=_hyp(it, BODY, 'DOC', model='L1 store queue: whole 16 B blocks 1/cycle, else 1 coalesced store / 5'))
  for k in (1, 2, 4):
    add(f'st-stride16-gap{k}', role, 'store', ''.join(f'sw a2, {16 * i}(a3)\n' + 'addi a1, a1, 1\n' * k
                                                         for i in range(BODY)),
        setup=s, sink=lambda n, k=k: 3 + k * BODY * n, expect=_hyp(16 * max(5, 1 + k) + 2, BODY))
  sl = lines(li('a1', 3), li('a3', LOCAL), 'mv a2, a0')
  add('st-local-same', role, 'store', 'sw a2, 0(a3)\n' * BODY, setup=sl, finish='lw a1, 0(a3)\nsw a1, 0(s11)\n',
      sink=lambda n: n, expect=_hyp(18, BODY, 'DOC'))
  add('st-local-seq', role, 'store', ''.join(f'sw a2, {4 * i}(a3)\n' for i in range(BODY)), setup=sl,
      finish='lw a1, 60(a3)\nsw a1, 0(s11)\n', sink=lambda n: n, expect=_hyp(18, BODY, 'DOC'))
  add('st-mixed-l1-local', role, 'store', ''.join(f'sw a2, {16 * i}(a3)\nsw a2, {4 * i}(a4)\n' for i in range(8)),
      setup=s + li('a4', LOCAL), finish='lw a1, 112(a3)\nsw a1, 0(s11)\n', sink=lambda n: n,
      expect=_hyp(8 * 5 + 2, BODY, model='local stores hide under the L1 store queue'))

  # fences with work outstanding: ops = fences per iteration
  nb = 0xFFB21800  # NoC0 cmdbuf 3 TARG_LO
  fences = {  # name: (group, n groups, setup extra, restore, expected cycles per group)
    'fe-st_l1': ('sw a2, 0(a3)\nfence\n', 8, '', None, 1 + 4),
    'fe-st4seq_l1': ('sw a2, 0(a3)\nsw a2, 4(a3)\nsw a2, 8(a3)\nsw a2, 12(a3)\nfence\n', 4, '', None, 4 + 4),
    'fe-st4stride_l1': ('sw a2, 0(a3)\nsw a2, 16(a3)\nsw a2, 32(a3)\nsw a2, 48(a3)\nfence\n', 4, '', None, 20 + 4),
    'fe-st_local': ('sw a2, 0(a4)\nfence\n', 8, li('a4', LOCAL), None, 1 + 4),
    'fe-st_niu': ('sw a2, 0(a4)\nfence\n', 8, li('a4', nb), nb, 1 + 4),
    'fe-ld_l1': ('lw t3, 0(a3)\nfence\n', 8, '', None, 8 + 4),
    'fe-ld_wall': ('lw t3, 0(t0)\nfence\n', 8, '', None, 7 + 4),
  }
  if role in BT:
    fences['fe-st_cfg'] = ('sw a2, 0(a4)\nfence\n', 8, li('a4', 0xFFEF0000 + 100 * 4), None, 1 + 4)
  for name, (grp, n, extra, restore, per) in fences.items():
    add(name, role, 'fence', grp * n, ops=n, setup=s + extra, restore=restore, sink=3,
        expect=_hyp(n * per + 2, n, model='fence 4 + drain of what is outstanding; StMergeTimer (16) may add'))
  add('fence-nosync', role, 'fence', 'fence\n' * BODY, setup=s, sink=3, cfg0_set=DIS_CSR_SYNC,
      expect=_hyp(16 * 4 + 2, BODY, model='DisCsrSync: fence no longer holds the frontend; LSU still serialises'))

  # store -> load
  P = scratch(role) + 0x500
  ring = chain(P, 1, 16)
  sp = lines(li('a1', P), li('a2', 1), li('a3', P))
  add('stld-bypass', role, 'stld', 'sw a2, 64(a3)\nlw a1, 0(a1)\n' * BODY, setup=sp, init=ring, sink=P,
      expect=_hyp(16 * 8 + 2, BODY, 'DOC', model='non-overlapping load bypasses the store queue'))
  add('stld-sameline', role, 'stld', 'sw a2, 4(a3)\nlw a1, 0(a1)\n' * BODY, setup=sp, init=ring, sink=P,
      expect=_hyp(16 * 8 + 2, BODY, 'DOC', model='same 16 B line, no byte overlap: bypass'))
  add('stld-overlap', role, 'stld', 'sw a1, 0(a1)\nlw a1, 0(a1)\n' * BODY, setup=sp, init=ring, sink=P,
      expect=_hyp(16 * 9 + 2, BODY, model='overlap: queue drains first, then 8'))
  add('stld-overlap-local', role, 'stld', 'sw a1, 0(a1)\nlw a1, 0(a1)\n' * BODY, setup=lines(li('a1', LOCAL)),
      init=store_word(LOCAL, LOCAL), sink=LOCAL, expect=_hyp(16 * 3 + 2, BODY))
  add('ldbuf_bypass_off', role, 'stld', 'sw a2, 64(a3)\nlw a1, 0(a1)\n' * BODY, setup=sp, init=ring, sink=P,
      cfg0_set=1, expect=_hyp(16 * 9 + 2, BODY, model='cfg0 DisLdBufByp: loads wait for an empty store queue'))
  # atomics (L1 only)
  add('amo_dep', role, 'stld', 'amoadd.w a1, zero, (a1)\n' * BODY, setup=lines(li('a1', P)), init=ring, sink=P,
      expect=_hyp(16 * 12 + 2, BODY, 'DOC', latency=12))
  add('amo_tput', role, 'stld', 'amoadd.w zero, a2, (a3)\n' * BODY, setup=sp + 'sw zero, 64(a3)\naddi a3, a3, 64\n',
      finish='lw a1, 0(a3)\nsw a1, 0(s11)\n', sink=lambda n: BODY * n, expect=_hyp(16 * 12 + 2, BODY))


# ---- 6. CSRs, timer, integer divide
def _misc_cases(role):
  s = lines(li('a1', 3), li('a2', 1))
  reads = {'csr_instret': 'instret', 'csr_cfg0': '0x7c0', 'csr_misa': 'misa', 'csr_mhartid': 'mhartid',
           'csr_fcsr': 'fcsr', 'csr_mcycle': 'mcycle'}
  if role in TRISCS: reads['csr_qstatus'] = '0xbc0'  # tt_cfg_qstatus (Tensix frontend status); not tried elsewhere
  for name, csr in reads.items():
    add(name, role, 'csr', f'csrr a1, {csr}\n' * BODY, setup=s, expect=_hyp(16 * 4 + 2, BODY, model='csr = 4 (old csr_cycle)'))
  add('csr_cycle-nosync', role, 'csr', 'csrr a1, cycle\n' * BODY, setup=s, cfg0_set=DIS_CSR_SYNC,
      expect=_hyp(18, BODY, model='DisCsrSync: CSR reads stop holding the frontend'))
  add('csrw_cfg1', role, 'csr', 'csrw 0x7c3, a2\n' * BODY, setup=s, finish='csrr a1, 0x7c3\nsw a1, 0(s11)\n', sink=1,
      expect=_hyp(16 * 4 + 2, BODY))
  add('csrrwi_cfg1', role, 'csr', 'csrrwi a1, 0x7c3, 5\n' * BODY, setup=s, sink=5, expect=_hyp(16 * 4 + 2, BODY))
  add('csr_cycle_alu', role, 'csr', 'csrr a1, cycle\n' + 'addi a2, a2, 1\n' * 7 + 'csrr a1, cycle\n' + 'addi a2, a2, 1\n' * 7,
      setup=s, finish='mv a1, a2\nsw a1, 0(s11)\n', sink=lambda n: 1 + 14 * n,
      expect=_hyp(2 * 4 + 14 + 2, BODY, model='does an ALU op behind a CSR wait for its retirement?'))

  # the timer itself: two wall-clock reads with nothing / a dependency / a fence / a CSR read between them
  pairs = {'tm-pair-none': ('', 1), 'tm-pair-dep': ('andi t3, t1, 0\nadd t0, t0, t3\n', 9),
           'tm-pair-fence': ('fence\n', 11), 'tm-pair-csr': ('csrr t3, cycle\n', 5)}
  for name, (body, exp) in pairs.items():
    add(name, role, 'timer', body, pair=True, setup=s, expect=dict(cycles=exp, src='HYP'))
  add('tm-cycle_ratio', role, 'timer', 'addi a2, a2, 1\n' * BODY, setup=s + 'csrr a6, cycle\n',
      finish='csrr a7, cycle\nsub a1, a7, a6\nsw a1, 0(s11)\n', expect=_hyp(18, BODY, ratio=1.0),
      note='sink = mcycle delta over the timed loop; run() reports mcycle / wall clock')

  # integer divide: dividend magnitude (divisor 3), divisor magnitude (dividend 0xffffffff), special operands
  for k in (2, 3, 4, 6, 8, 12, 16, 20, 24, 28, 31, 32):
    d = (1 << k) - 1
    add(f'divu_mag-b{k}', role, 'div', 'divu a1, a3, a2\n' * BODY, setup=lines(li('a3', d), li('a2', 3)),
        sink=d // 3, expect=_hyp(16 * max(6, k + 1) + 2, BODY, model='DOC 6..33 by dividend magnitude: guess bits+1'))
  for k in (2, 8, 16, 24, 31):
    d = (1 << k) - 1
    add(f'divu_dvsr-b{k}', role, 'div', 'divu a1, a3, a2\n' * BODY, setup=lines(li('a3', MASK), li('a2', d)),
        sink=MASK // d, expect=_hyp(16 * 33 + 2, BODY, model='dividend-only dependence'))
  special = {  # name: (op, dividend, divisor, result, cycles/op)
    'divu_zero': ('divu', 12345, 0, MASK, 2), 'div_intmin_m1': ('div', 0x80000000, MASK, 0x80000000, 2),
    'rem_intmin_m1': ('rem', 0x80000000, MASK, 0, 2), 'div_m1_3': ('div', MASK, 3, 0, 6),
    'div_m2p31_3': ('div', 0x80000001, 3, -0x2AAAAAAA, 33), 'rem_large': ('rem', 0x7FFFFFFF, 3, 1, 32),
  }
  for name, (op, a, b, r, c) in special.items():
    add(name, role, 'div', f'{op} a1, a3, a2\n' * BODY, setup=lines(li('a3', a), li('a2', b)), sink=r,
        expect=_hyp(16 * c + 2, BODY, 'DOC' if c == 2 else 'HYP'))
  add('mulhu_dep', role, 'div', 'mulhu a1, a1, a2\n' * BODY, setup=lines(li('a1', 3), li('a2', 1)), sink=0,
      expect=_hyp(16 * 2 + 1, BODY, model='as mul_dep'))


# ---- 7. predictor fit (2026-11-18, after the first full run): a counter-driven branch with run length K, so the
# patterns are not limited to periods dividing 32 (the rori patterns). 'rare': taken once every K iterations;
# 'often': not taken once every K. Same arithmetic in every case (branchless reset with mul), so the controls
# (bpk-ctl-never / bpk-ctl-always) give the perfectly predicted cost and the excess / 4 = mispredicts per iteration.
# jalr: one indirect jump whose target alternates (or stays put) every iteration.
BPK = (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 24, 32, 48, 64)


def _bpfit_cases(role):
  def body(br):
    return ('addi a5, a5, -1\nseqz t3, a5\nmul t4, t3, a7\nadd a5, a5, t4\n' + br + '\naddi a6, a6, 1\n1:\n')
  for K in BPK:
    s = lines(li('a5', K), li('a7', K), li('a6', 0))
    add(f'bpk-rare-K{K}', role, 'bpfit', body('bnez t3, 1f'), ops=7, setup=s, finish=SINK_A6,
        sink=lambda n, K=K: n - n // K, note=f'taken once per {K} iterations')
    add(f'bpk-often-K{K}', role, 'bpfit', body('beqz t3, 1f'), ops=7, setup=s, finish=SINK_A6,
        sink=lambda n, K=K: n // K, note=f'not taken once per {K} iterations')
  s = lines(li('a5', 5), li('a7', 5), li('a6', 0))
  add('bpk-ctl-never', role, 'bpfit', body('bnez zero, 1f'), ops=7, setup=s, finish=SINK_A6, sink=lambda n: n)
  add('bpk-ctl-always', role, 'bpfit', body('beqz zero, 1f'), ops=7, setup=s, finish=SINK_A6, sink=0)
  ind = 'auipc t3, 0\nadd t3, t3, a4\njalr zero, 0(t3)\naddi a6, a6, 1\nxori a4, a4, {x}\n'
  for name, a4, x, sink in (('jalr-alt', 12, 12 ^ 16, lambda n: (n + 1) // 2), ('jalr-const12', 12, 0, lambda n: n),
                            ('jalr-const16', 16, 0, 0)):
    add(f'bpk-{name}', role, 'bpfit', ind.format(x=x), ops=5, setup=lines(li('a4', a4), li('a6', 0)),
        finish=SINK_A6, sink=sink)
  # the rori patterns of the branch group (bp1-p32_1 mispredicts every iteration, the counter form does not):
  # gap instructions between the rori and the bltz, and the same direction through srli + bnez
  for pname in ('p32_1', 'p32', 'p32_31', 'p16', 'p8_1'):
    pat = PATTERNS[pname]
    s = lines(li('a1', 3), li('a5', pat), li('a6', 0))
    for g in (0, 1, 2, 4, 8):
      add(f'bpr-{pname}-gap{g}', role, 'bpfit', 'rori a5, a5, 31\n' + 'addi a1, a1, 1\n' * g + 'bltz a5, 1f\naddi a6, a6, 1\n1:\n'
          + 'addi a1, a1, 1\n' * (14 - g), setup=s, finish=SINK_A6, sink=lambda n, pat=pat: _not_taken(pat, n, 1))
    add(f'bpr-{pname}-srli', role, 'bpfit', 'rori a5, a5, 31\nsrli t3, a5, 31\n' + 'addi a1, a1, 1\n' * 2
        + 'bnez t3, 1f\naddi a6, a6, 1\n1:\n' + 'addi a1, a1, 1\n' * 10, setup=s, finish=SINK_A6,
        sink=lambda n, pat=pat: _not_taken(pat, n, 1))
    add(f'bpr-{pname}-slli', role, 'bpfit', 'slli t3, a5, 1\nsrli t4, a5, 31\nor a5, t3, t4\n' + 'addi a1, a1, 1\n' * 2
        + 'bltz a5, 1f\naddi a6, a6, 1\n1:\n' + 'addi a1, a1, 1\n' * 9, setup=s, finish=SINK_A6,
        sink=lambda n, pat=pat: _not_taken(pat, n, 1), note='rotate without rori')
  # aliasing: an always-taken branch (to the next instruction) and a never-taken one d instructions later, in a loop of
  # fixed length (72 instructions + loop control). No aliasing: 74 cycles per iteration. Shared entry: both mispredict.
  for d in (*range(1, 34), 40, 48, 56, 63, 64, 65):
    body = 'beq zero, zero, 1f\n1:\n' + 'addi a1, a1, 1\n' * (d - 1) + 'bne zero, zero, 89f\n' + 'addi a1, a1, 1\n' * (70 - d)
    add(f'bpa-d{d}', role, 'bpfit', body, ops=72, setup=lines(li('a1', 3)), tail='89:\nj 99f\n',
        sink=lambda n, d=d: 3 + 69 * n, note=f'taken and not-taken branch {4 * d} bytes apart')


# order: the ported cases first, then plain-memory groups, branches, and the MMIO targets last (a run stops at the
# first hard failure, so the cases most likely to upset the tile run after everything else is recorded)
for _gen in (_old_cases, _l1_cases, _store_cases, _misc_cases, _branch_cases, _mmio_cases):
  for _r in ROLES: _gen(_r)
for _r in ('brisc', 'trisc1'): _bpfit_cases(_r)
assert len({c['id'] for c in CASES}) == len(CASES), 'duplicate case ids'


# ---- static checks on the asm: harness registers are never written, loops stay below the I-cache knee (128)
_RESERVED = re.compile(r'\b(sp|gp|tp|s0|fp|x[2348])\b')
_DEST = re.compile(r'^\s*(?!s[bhw]\b|b\w*\b|j\b|jr\b|ret\b|fence\b|\.|amo\w*\.w\s+zero)\w[\w.]*\s+(t0|t1|t2|a0|s11)\b')


def _lint(case):
  a = case['asm']
  for part in ('init', 'setup', 'body', 'finish', 'tail'):
    text = a[part] or ''
    if _RESERVED.search(text): raise AssertionError(f'{case["id"]}: {part} uses a reserved register')
    for ln in text.splitlines():
      m = _DEST.match(ln)
      if m and not (case['case'] == 'tm-pair-dep' and m.group(1) == 't0'):
        raise AssertionError(f'{case["id"]}: {part} writes harness register {m.group(1)}: {ln!r}')
  insns = sum(1 for ln in (a['body'] + (a['tail'] or '')).splitlines() if ln.strip() and not ln.strip().endswith(':'))
  if insns > 120: raise AssertionError(f'{case["id"]}: {insns} instructions in the loop, past the I-cache knee')


for _c in CASES: _lint(_c)


# ---- build and run
def _lit(s): return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def defines(case):
  a, d = case['asm'], {}
  for key, part in (('RV_INIT', 'init'), ('RV_SETUP', 'setup'), ('RV_BODY', 'body'), ('RV_FINISH', 'finish'),
                    ('RV_TAIL', 'tail')):
    if a[part] is not None and (a[part] or part != 'finish'): d[key] = _lit(a[part])
  if case['cfg0_set']: d['CFG0_SET'] = hex(case['cfg0_set'])
  if case['cfg0_clear']: d['CFG0_CLEAR'] = hex(case['cfg0_clear'])
  if case['restore'] is not None: d['RESTORE_ADDR'] = hex(case['restore'])
  if case['counts'][0] != COUNTS[0]: d['COUNT0'] = str(case['counts'][0])
  if case['pair']: d['RV_PAIR'] = '1'
  return d


def image(case): return build('k_riscv.c', case['role'], **defines(case))


START = 0x0002A303  # lw t1, 0(t0): first word of the timed region


def cfg0_expected(role):
  """cfg0 bits fw/hw.h configure_csr guarantees at kernel entry: (must be set, must be clear)."""
  if role in TRISCS: return 0, DIS_L0 | DIS_BP | DIS_TRISC_FUSION
  return DIS_TRISC_FUSION, DIS_L0 | DIS_BP


def run(card, case, timeout):
  role, img = case['role'], image(case)
  card.run([(TILE, {role: img}, [], None)], timeout)
  w = card.log(TILE, HEADER + 3 * 3 * SAMPLES, role)
  hdr = dict(zip(('points', 'samples', 'cfg0', 'cfg0_during', 'pmacfg0', 'pmacfg1', 'misa', 'mstatus'), w[:HEADER]))
  rec = {k: hex(v) if k not in ('points', 'samples') else v for k, v in hdr.items()}
  must, mustnt = cfg0_expected(role)
  rec['cfg0_ok'] = hdr['cfg0'] & must == must and not hdr['cfg0'] & mustnt and \
      hdr['cfg0_during'] == (hdr['cfg0'] | case['cfg0_set']) & ~case['cfg0_clear'] & MASK
  points, sinks_ok = [], True
  for p, n in enumerate(case['counts']):
    rows = [w[HEADER + 3 * (p * SAMPLES + s):][:3] for s in range(SAMPLES)]
    cyc = [(t1 - t0) & MASK for t0, t1, _ in rows]
    xs = [x for _, _, x in rows]
    want = case['sink'] and case['sink'][str(n)]
    # the warmup sample is not checked: on BRISC it can race TRISC0's firmware zeroing its GPRs at launch
    if want is not None and any(x != want for x in xs[1:]): sinks_ok = False
    raw = cyc[1:]
    pt = dict(iterations=n, body_operations=case['ops'] * n, warmup=cyc[0], raw_cycles=raw, min=min(raw),
              median=median(raw), max=max(raw), sinks=sorted(set(xs)))
    if case['case'] == 'tm-cycle_ratio': pt['mcycle_per_wall'] = [x / c for x, c in zip(xs[1:], raw)]
    points.append(pt)
  rec.update(points=points, sink_ok=sinks_ok if case['sink'] is not None else None, image_bytes=len(img),
             image_sha256=hashlib.sha256(img).hexdigest())
  words = struct.unpack(f'<{len(img) // 4}I', img[:len(img) // 4 * 4])
  if START in words: rec['loop_addr'] = hex(__import__('fw').CODE[role] + 4 * words.index(START) + 4)
  exp = case['expect'] or {}
  if case['pair']:
    allc = [c for pt in points for c in pt['raw_cycles']]
    rec['median'] = median(allc)
    if 'cycles' in exp: rec['expect_ok'] = abs(rec['median'] - exp['cycles']) <= 0.5
  else:
    ops = case['ops']
    slopes = [(b['median'] - a['median']) / (b['body_operations'] - a['body_operations']) for a, b in zip(points, points[1:])]
    rec.update(adjacent_slopes=slopes, slope=sum(slopes) / len(slopes), per_iter=sum(slopes) / len(slopes) * ops)
    rec['median'] = round(rec['slope'], 4)
    if 'slope' in exp: rec['expect_ok'] = abs(rec['slope'] - exp['slope']) <= max(0.03 * exp['slope'], 0.01)
  flags = [f for f, bad in (('SINK MISMATCH', rec['sink_ok'] is False), ('cfg0 unexpected', not rec['cfg0_ok']),
                            ('differs from expect', rec.get('expect_ok') is False)) if bad]
  if flags: print(f'  {case["id"]}: {", ".join(flags)} (got {rec["median"]}, expect {exp.get("slope", exp.get("cycles"))}'
                  f' [{exp.get("src")}], sinks {[pt["sinks"] for pt in points]})', flush=True)
  return rec


# ---- offline checks (no hardware)
def _reference(case):
  """Assemble the timed region on its own; the built image must contain exactly these bytes."""
  import subprocess, tempfile, os
  a = case['asm']
  fin = a['finish'] if a['finish'] is not None else 'sw a1, 0(s11)\n'
  if case['pair']: timed = 'fence\nlw t1, 0(t0)\n' + a['body'] + 'lw t2, 0(t0)\n'
  else: timed = 'fence\nlw t1, 0(t0)\n90:\n' + a['body'] + 'addi a0, a0, -1\nbnez a0, 90b\n' + fin + 'fence\nlw t2, 0(t0)\n'
  text = '.option arch, +f, +zba, +zbb, +zaamo\n' + timed + 'j 99f\n' + (a['tail'] or '') + '99:\n'
  with tempfile.TemporaryDirectory() as d:
    open(f'{d}/t.s', 'w').write(text)
    for cmd in (['clang', '--target=riscv32-none-unknown-elf', '-march=rv32im_zicsr', '-mabi=ilp32', '-mno-relax', '-c',
                 f'{d}/t.s', '-o', f'{d}/t.o'], ['llvm-objcopy', '-O', 'binary', '--only-section=.text', f'{d}/t.o', f'{d}/t.bin']):
      r = subprocess.run(cmd, capture_output=True, text=True)
      if r.returncode: raise RuntimeError(r.stderr)
    return open(f'{d}/t.bin', 'rb').read()


def verify(cases):
  from concurrent.futures import ThreadPoolExecutor
  def one(c):
    img, ref = image(c), _reference(c)
    return c['id'], len(img), ref in img and img.count(ref) == 1
  bad = 0
  with ThreadPoolExecutor(16) as ex:
    for cid, n, ok in ex.map(one, cases):
      if not ok: bad += 1; print(f'MISMATCH {cid}')
  print(f'{len(cases)} cases built; {bad} with a timed region that differs from the asm')
  return bad


def disasm(case):
  import subprocess, tempfile, fw
  img = image(case)
  with tempfile.TemporaryDirectory() as d:
    open(f'{d}/k.bin', 'wb').write(img)
    subprocess.run(['llvm-objcopy', '-I', 'binary', '-O', 'elf32-littleriscv', '--rename-section',
                    '.data=.text,code,alloc,load,readonly', f'{d}/k.bin', f'{d}/k.elf'], check=True)
    out = subprocess.run(['llvm-objdump', '-d', '--no-show-raw-insn', '--mattr=+m,+f,+zba,+zbb,+zaamo,+zicsr',
                          f'--adjust-vma={fw.CODE[case["role"]]:#x}', f'{d}/k.elf'],
                         check=True, capture_output=True, text=True).stdout
  return out


if __name__ == '__main__':
  import argparse
  ap = argparse.ArgumentParser()
  ap.add_argument('--verify', action='store_true', help='build every case (or -k matches) and check the timed bytes')
  ap.add_argument('--disasm', metavar='ID')
  ap.add_argument('-k', action='append', default=[])
  ap.add_argument('--summary', action='store_true')
  a = ap.parse_args()
  sel = [c for c in CASES if all(k in c['id'] for k in a.k)]
  if a.summary:
    from collections import Counter
    print(Counter(c['group'] for c in sel), len(sel))
  if a.disasm: print(disasm(next(c for c in CASES if c['id'] == a.disasm)))
  if a.verify: sys.exit(1 if verify(sel) else 0)
