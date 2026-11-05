"""Regenerate the ISA inventory from local manuals, never from encoder bodies.

Run: ../.venv/bin/python -m tests.isa.inventory
The website catalog supplies source links only. Expected bits come from the
manual's SVG diagrams; syntax determines positional argument correspondence.
"""
import hashlib
import inspect
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from ttko.isa import Tensix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOCS = ROOT / 'tt-isa-documentation'
NS = {'s': 'http://www.w3.org/2000/svg'}


def resolve(path):
  text = path.read_text()
  if 'This document is shared with the Wormhole tree' in text:
    target = re.search(r'\]\(([^)]+\.md)\)', text).group(1)
    return resolve((path.parent / target).resolve())
  return path, text


def diagram_fields(path):
  pending, fields = [], []
  for node in ET.parse(path).getroot().findall('s:text', NS):
    label = ''.join(node.itertext())
    if node.find('s:tspan', NS) is None:
      if label.isdecimal(): pending.append(int(label))
    elif pending:
      fields.append({'name': label, 'lo': min(pending), 'hi': max(pending)})
      pending = []
  return fields


def build():
  llk_path = ROOT / 'tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h'
  llk_text = llk_path.read_text().replace('\\\n', ' ')
  llk = {}
  for name, params, opcode, expression in re.findall(
      r'^#define TT_OP_(\w+)\(([^)]*)\)\s+TT_OP\(\s*(0x[\da-fA-F]+),([^\n]+)', llk_text, re.M):
    valid = re.search(r'^#define TT_' + name + r'_VALID\([^\n]+', llk_text, re.M)
    widths = dict((n, int(w)) for n, w in re.findall(r'is_valid\((\w+), (\d+)\)', valid.group() if valid else ''))
    shifts = dict((n, int(s)) for n, s in re.findall(r'\(\((\w+)\) << (\d+)\)', expression))
    arguments = []
    for parameter in filter(None, map(str.strip, params.split(','))):
      if parameter not in widths or parameter not in shifts:
        raise ValueError(f'Cannot parse LLK field {name}.{parameter}')
      lo = shifts[parameter]
      arguments.append({'parameter': parameter, 'name': parameter, 'lo': lo, 'hi': lo + widths[parameter] - 1})
    llk[name] = {'opcode': int(opcode, 16), 'arguments': arguments}
  for name, opcode in re.findall(r'^#define TT_OP_(\w+)\s+TT_OP\((0x[\da-fA-F]+), 0\)', llk_text, re.M):
    llk[name] = {'opcode': int(opcode, 16), 'arguments': []}
  llk['SFPSTOCHRND'] = llk['SFP_STOCH_RND']
  catalog = json.loads((ROOT / 'tt-ins-docs/lib/instructions.json').read_text())
  links = {i['name']: i['manualUrl'].split('/blob/')[1].split('/', 1)[1]
           for i in catalog['instructions']}
  records = []
  for name in sorted(n for n in dir(Tensix) if n.startswith('TT')):
    record = {'instruction': name[2:], 'behavior': 'not audited', 'encodings': []}
    record['llk_encoding'] = llk.get(name[2:])
    if record['llk_encoding']:
      params = list(inspect.signature(getattr(Tensix, name)).parameters)
      arguments = record['llk_encoding']['arguments']
      if name in ('TTADDRCRZW', 'TTINCADCZW'):
        # LLK names the Z/W channel fields X/Y; blackhole-py uses Z/W.
        aliases = {'Ch1_Y': 'Ch1_W', 'Ch1_X': 'Ch1_Z', 'Ch0_Y': 'Ch0_W', 'Ch0_X': 'Ch0_Z'}
        for argument in arguments: argument['parameter'] = aliases.get(argument['parameter'], argument['parameter'])
      if params != [a['parameter'] for a in arguments]: raise ValueError(f'LLK signature mismatch: {name}')
    direct = DOCS / 'BlackholeA0/TensixTile/TensixCoprocessor' / (name[2:] + '.md')
    source = direct if direct.exists() else DOCS / links[name] if name in links else None
    if source is None:
      record['gap'] = 'No Blackhole manual page or website source link.'
      records.append(record)
      continue
    path, text = resolve(source)
    record.update(source=str(source.relative_to(DOCS)), resolved_source=str(path.relative_to(DOCS)),
                  blackhole_contract=str(source.relative_to(DOCS)).startswith('BlackholeA0/'),
                  source_sha256=hashlib.sha256(text.encode()).hexdigest(),
                  modifiers=[{'name': n, 'value': v.strip()} for n, v in
                    re.findall(r'^#define\s+(\w+)\s+([^\n]+)', text, re.M)
                    if '_MOD' in n or '_IMM' in n],
                  sections=re.findall(r'^##+ (.+)$', text, re.M))
    # Parse only syntax for this exact instruction, not calls in functional models.
    syntax = re.search(r'## Syntax\s+```c\s+(.*?)```', text, re.S)
    diagrams = re.findall(r'!\[\]\(([^)]+Bits32_[^)]+\.svg)\)', text)
    params = list(inspect.signature(getattr(Tensix, name)).parameters)
    if syntax:
      call = re.search(r'TT_' + name[2:] + r'\((.*)\)', syntax.group(1))
      args = re.sub(r'/\*.*?\*/', '', call.group(1)).split(',') if call else []
    else: args = []
    record['syntax'] = syntax.group(1).strip() if syntax else None
    for link in diagrams:
      diagram = (path.parent / link).resolve()
      fields = diagram_fields(diagram)
      constants = [f for f in fields if f['lo'] == 24 and re.fullmatch(r'0x[0-9A-Fa-f]+', f['name'])]
      if len(constants) != 1: continue
      encoding = {'diagram': str(diagram.relative_to(DOCS)), 'opcode': int(constants[0]['name'], 16),
                  'fields': fields, 'arguments': []}
      if len(args) == len(params):
        for param, arg in zip(params, args, strict=True):
          identifiers = re.findall(r'\b[A-Za-z_]\w*\b', arg)
          matches = [f for f in fields if f['name'] in identifiers]
          if len(matches) == 1:
            encoding['arguments'].append({'parameter': param, **matches[0]})
      record['encodings'].append(encoding)
    records.append(record)
  from tests.isa.test_sfpu_bits import CASES
  from tests.isa.test_scalar import OPERATIONS
  from tests.isa.test_predicate_stack import CASES as STACK_CASES
  for record in records:
    covered = [{'modifier': case.values[1], 'immediate': case.values[2]} for case in CASES
               if case.values[0] == record['instruction']]
    if covered:
      record['behavior'] = 'partial: test_sfpu_bits'
      record['behavior_cases'] = covered
    tests = []
    if covered: tests.append('test_sfpu_bits.py')
    if record['instruction'] in {op for op, _ in OPERATIONS}:
      tests.append('test_scalar.py')
      record['scalar_modes'] = [mode for op, mode in OPERATIONS if op == record['instruction']]
    if record['instruction'] in {op for op, _, _ in STACK_CASES}:
      tests.append('test_predicate_stack.py')
      record['stack_cases'] = [{'modifier': mode, 'depth': depth} for op, mode, depth in STACK_CASES
                               if op == record['instruction']]
    if tests:
      record['behavior'] = 'partial'
      record['behavior_tests'] = tests
    if record['instruction'] in ('SEMINIT', 'SEMPOST', 'SEMGET', 'SEMWAIT', 'ATGETM', 'ATRELM'):
      record['behavior'] = 'partial'
      record.setdefault('behavior_tests', []).append('test_sync.py')
  from tests.isa.requirements import REQUIREMENTS
  for record in records:
    matches = [r for r in REQUIREMENTS if record['instruction'] in r['instructions']]
    record['reviewed_requirements'] = [r['id'] for r in matches]
    record['reviewed_test_selectors'] = sorted({t for r in matches for t in r['tests']})
    if matches: record['behavior'] = 'partial'
  pages = []
  for path in sorted((DOCS / 'BlackholeA0').rglob('*.md')):
    resolved, text = resolve(path)
    pages.append({'source': str(path.relative_to(DOCS)),
                  'resolved_source': str(resolved.relative_to(DOCS)),
                  'sections': re.findall(r'^##+ (.+)$', text, re.M),
                  'modifiers': [{'name': n, 'value': v.strip()} for n, v in
                    re.findall(r'^#define\s+(\w+)\s+([^\n]+)', text, re.M)
                    if '_MOD' in n or '_IMM' in n],
                  'status': 'not audited'})
  return {'llk_source': str(llk_path.relative_to(ROOT)),
          'llk_commit': subprocess.check_output(['git', '-C', str(ROOT / 'tt-llk'), 'rev-parse', 'HEAD'], text=True).strip(),
          'llk_sha256': hashlib.sha256(llk_path.read_bytes()).hexdigest(),
          'manual_commit': subprocess.check_output(['git', '-C', str(DOCS), 'rev-parse', 'HEAD'], text=True).strip(),
          'instructions': records, 'pages': pages}


def main():
  data = build()
  (HERE / 'inventory.json').write_text(json.dumps(data, indent=2) + '\n')


if __name__ == '__main__': main()
