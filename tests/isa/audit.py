"""Build a reviewable coverage map, keeping source sightings and proof separate.

python -m tests.isa.audit [--evidence /tmp/isa-existing-evidence.json]
Only reviewed requirements earn behavioral credit. Source sightings are useful
navigation, but fixture calls, timing and dynamic dispatch are not proof.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from tests.isa.requirements import REQUIREMENTS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def scan():
  inventory = json.loads((HERE / 'inventory.json').read_text())
  names = {i['instruction'] for i in inventory['instructions']}
  sites, functions, dynamic = defaultdict(list), {}, []
  for path in sorted((ROOT / 'tests').rglob('*.py')):
    relative = str(path.relative_to(ROOT))
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
      if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name.startswith('test_'):
          functions[f'{relative}::{node.name}'] = {
            'line': node.lineno,
            'parametrize': [ast.unparse(d) for d in node.decorator_list if 'parametrize' in ast.unparse(d)],
            'assertions_in_function': sum(isinstance(n, ast.Assert) for n in ast.walk(node)),
            'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    for node in ast.walk(tree):
      if isinstance(node, ast.Attribute) and node.attr.startswith('TT') and node.attr[2:] in names:
        sites[node.attr[2:]].append({'file': relative, 'line': node.lineno})
      if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'getattr':
        if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in ('TT', 'Tensix'):
          dynamic.append({'file': relative, 'line': node.lineno, 'expression': ast.unparse(node)})
  return inventory, sites, functions, dynamic


def outcome(phases):
  if any(p['outcome'] == 'failed' for p in phases.values()): return 'failed'
  if any('xfail' in p for p in phases.values()): return 'xfail'
  if any(p['outcome'] == 'skipped' for p in phases.values()): return 'skipped'
  if phases.get('call', {}).get('outcome') == 'passed' and phases.get('teardown', {}).get('outcome') == 'passed': return 'passed'
  return 'incomplete'


def compact_evidence(source, target):
  """Keep reproducible per-function counts and all failures without megabytes of timings."""
  run = json.loads(Path(source).read_text())
  tests = run.pop('tests')
  counts = defaultdict(Counter)
  failures = {}
  for node, phases in tests.items():
    status = outcome(phases)
    counts[node.split('[', 1)[0]][status] += 1
    if status != 'passed': failures[node] = phases
  run.update(function_outcomes={k: dict(v) for k, v in counts.items()}, failures=failures,
             selection_sha256=hashlib.sha256('\n'.join(sorted(tests)).encode()).hexdigest())
  Path(target).write_text(json.dumps(run, indent=2) + '\n')


def dependencies(selector):
  """Conservative static local-import closure plus pytest fixtures/firmware."""
  source = selector.split('::')[0]
  pending = [source]
  parent = (ROOT / source).parent
  while parent == ROOT or ROOT in parent.parents:
    config = parent / 'conftest.py'
    if config.exists(): pending.append(str(config.relative_to(ROOT)))
    if parent == ROOT: break
    parent = parent.parent
  seen = set()

  def module_file(parts):
    p = ROOT.joinpath(*parts)
    if p.with_suffix('.py').is_file(): return str(p.with_suffix('.py').relative_to(ROOT))
    if (p / '__init__.py').is_file(): return str((p / '__init__.py').relative_to(ROOT))

  while pending:
    relative = pending.pop()
    if relative in seen: continue
    seen.add(relative)
    path = ROOT / relative
    if not path.is_file() or path.suffix != '.py': continue
    package = list(path.relative_to(ROOT).parts[:-1])
    for node in ast.walk(ast.parse(path.read_text())):
      modules = []
      if isinstance(node, ast.Import): modules = [alias.name.split('.') for alias in node.names]
      elif isinstance(node, ast.ImportFrom):
        base = (package[:len(package) - node.level + 1] if node.level else [])
        base += node.module.split('.') if node.module else []
        modules = [base] + [base + [alias.name] for alias in node.names if alias.name != '*']
      for parts in modules:
        resolved = module_file(parts)
        if resolved and resolved not in seen: pending.append(resolved)
  seen.update(str(p.relative_to(ROOT)) for p in (ROOT / 'firmware').rglob('*')
              if p.is_file() and p.suffix in ('.c', '.h', '.S', '.ld'))
  if source.endswith(('test_encoding.py', 'test_audit.py')): seen.add('tests/isa/inventory.json')
  return seen


def build(evidence_paths=()):
  inventory, sites, functions, dynamic = scan()
  requirements = [dict(req) for req in REQUIREMENTS]
  new_groups = defaultdict(list)
  for item in inventory['instructions']:
    for test in item.get('behavior_tests', []): new_groups[test].append(item['instruction'])
  assertions = {
    'test_sfpu_bits.py': ('Selected mode/immediate cross-products with integer/FP bit edges, aliases, all/none/half masks and observed flags.',
                         'Lane-varying indirect indices, full register/configuration space, cast rounding and interactions remain.'),
    'test_scalar.py': ('Register/immediate scalar arithmetic, all documented ALU selectors, aliases, GPR bank boundaries, all three threads, intermediate results and final 64-GPR contents.',
                       'Exhaustive operand combinations, concurrent threads and scheduling hazards remain.'),
    'test_predicate_stack.py': ('All push/pop/comparison-stack modifiers and truth tables over selected depths including eight; observed masks and complement, deeper-stack preservation.',
                                'Latent flags while predication is disabled are not fully observed; nonuniform lane stacks and backdoor configuration remain.'),
  }
  for filename, instructions in new_groups.items():
    if filename == 'test_sync.py': continue  # More specific reviewed claims are listed explicitly.
    tests = [n for n in functions if n.startswith('tests/isa/' + filename + '::')]
    assertion, gaps = assertions.get(filename, ('See direct hardware assertions in linked tests.', 'Partial coverage; review test parameters and limitations.'))
    requirements.append(dict(id='isa.' + filename.removeprefix('test_').removesuffix('.py'),
      instructions=instructions, assertion=assertion, gaps=gaps, tests=tests, status='partial'))
  ids = [r['id'] for r in requirements]
  if len(ids) != len(set(ids)): raise ValueError('duplicate requirement ID')
  for req in requirements:
    if not set(req['instructions']) <= {i['instruction'] for i in inventory['instructions']}:
      raise ValueError(f'unknown instruction in {req["id"]}')
    for test in req['tests']:
      if test not in functions: raise ValueError(f'{req["id"]}: missing test {test}')
  evidence = []
  results = defaultdict(Counter)
  closures = {}
  for path in evidence_paths:
    run = json.loads(Path(path).read_text())
    changed = [p for p, sha in run['source_sha256'].items()
               if (ROOT / p).exists() and hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != sha
               and p not in ('tests/isa/audit.py', 'tests/isa/requirements.py', 'tests/isa/record.py', 'tests/isa/inventory.py')]
    per_function = defaultdict(Counter)
    if 'tests' in run:
      for node, phases in run['tests'].items():
        per_function[node.split('[', 1)[0]][outcome(phases)] += 1
    else:
      for selector, counts in run['function_outcomes'].items(): per_function[selector].update(counts)
    counts = sum(per_function.values(), Counter())
    evidence.append({k: run.get(k) for k in ('started_unix', 'finished_unix', 'pid', 'python', 'hardware', 'device', 'core', 'complete', 'exitstatus', 'environment')} |
                    {'source': str(path), 'outcomes': dict(counts), 'changed_sources': changed})
    for selector, counts in per_function.items():
      if selector not in closures: closures[selector] = dependencies(selector)
      affected = bool(set(changed) & closures[selector])
      for status, count in counts.items():
        if affected: status = 'stale-' + status
        # Preserve all runs rather than letting a later pass erase a failure.
        results[selector][status] += count
  for req in requirements:
    req['evidence'] = dict(sum((results[test] for test in req['tests']), Counter()))
    req['documents'] = sorted({i.get('source', inventory['llk_source']) for i in inventory['instructions'] if i['instruction'] in req['instructions']})
  instruction_rows = []
  for item in inventory['instructions']:
    name = item['instruction']
    instruction_rows.append({'instruction': name,
      'reviewed_requirements': [r['id'] for r in requirements if name in r['instructions']],
      'source_sightings': sorted({(s['file'], s['line']) for s in sites[name]}),
      'status': 'partial' if any(name in r['instructions'] for r in requirements) else 'no reviewed behavioral claim'})
  modifiers = []
  for page in inventory['pages']:
    if '/TensixCoprocessor/' not in page['source']: continue
    instruction = Path(page['source']).stem.split('_', 1)[0]
    if instruction not in {i['instruction'] for i in inventory['instructions']}: continue
    for modifier in page['modifiers']:
      modifiers.append({'instruction': instruction, 'source': page['source'], **modifier,
        'candidate_requirements': [r['id'] for r in requirements if instruction in r['instructions']],
        'status': 'needs modifier-level review'})
  return {'instructions': instruction_rows, 'requirements': requirements, 'test_functions': functions,
          'modifier_obligations': modifiers,
          'dynamic_dispatch_sites': dynamic, 'runs': evidence}


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--evidence', action='append', default=[])
  args = parser.parse_args()
  data = build(args.evidence)
  (HERE / 'audit.json').write_text(json.dumps(data, indent=2) + '\n')
  counts = Counter(i['status'] for i in data['instructions'])
  print(dict(counts))


if __name__ == '__main__': main()
