"""Offline checks against Blackhole LLK and applicable manual diagrams.

Only syntax arguments unambiguously mapped to a named diagram field are tested.
Every encoder is also checked against the independent Blackhole LLK header.
"""
import json
from pathlib import Path
import random

import pytest

from ttko.isa import Tensix

INVENTORY = json.loads(Path(__file__).with_name('inventory.json').read_text())


def test_inventory_covers_public_encoders():
  expected = {name[2:] for name in dir(Tensix) if name.startswith('TT')}
  actual = [instruction['instruction'] for instruction in INVENTORY['instructions']]
  assert set(actual) == expected
  assert len(actual) == len(expected), 'duplicate instruction in inventory'


OPCODES, FIELDS, COMBINED, INVALID = [], [], [], []
for instruction in INVENTORY['instructions']:
  name = instruction['instruction']
  encodings = []
  if instruction['llk_encoding']: encodings.append(instruction['llk_encoding'])
  if instruction.get('blackhole_contract'): encodings.extend(instruction['encodings'])
  assert encodings, f'{name} has no independent encoding source'
  for index, encoding in enumerate(encodings):
    OPCODES.append(pytest.param(name, encoding['opcode'], id=f'{name}-{index}'))
    for field in encoding['arguments']:
      width = field['hi'] - field['lo'] + 1
      # Walking bits distinguish adjacent/swapped fields; boundary and mixed
      # patterns expose accidental narrowing and incorrect field placement.
      values = sorted({0, (1 << width) - 1, *((1 << b) for b in range(width)),
                       0x55555555 & ((1 << width) - 1), 0xaaaaaaaa & ((1 << width) - 1)})
      for value in values:
        FIELDS.append(pytest.param(name, encoding['opcode'], field, value,
                                  id=f'{name}-{index}-{field["name"]}-{value:x}'))
    if encoding is instruction['llk_encoding']:
      for field in encoding['arguments']:
        for value in (-1, 1 << (field['hi'] - field['lo'] + 1)):
          INVALID.append(pytest.param(name, field['parameter'], value, id=f'{name}-{field["name"]}-{value}'))
      rng = random.Random(name)
      for trial in range(16):
        arguments, expected = {}, encoding['opcode'] << 24
        for field in encoding['arguments']:
          width = field['hi'] - field['lo'] + 1
          value = (1 << width) - 1 if trial == 0 else rng.randrange(1 << width)
          arguments[field['parameter']] = value
          expected |= value << field['lo']
        COMBINED.append(pytest.param(name, arguments, expected, id=f'{name}-{trial}'))


@pytest.mark.parametrize('name,opcode', OPCODES)
def test_documented_opcode(name, opcode):
  assert int(getattr(Tensix, 'TT' + name)()) >> 24 == opcode


@pytest.mark.parametrize('name,opcode,field,value', FIELDS)
def test_documented_field(name, opcode, field, value):
  actual = int(getattr(Tensix, 'TT' + name)(**{field['parameter']: value}))
  assert actual == (opcode << 24) | (value << field['lo'])


@pytest.mark.parametrize('name,arguments,expected', COMBINED)
def test_combined_fields(name, arguments, expected):
  assert int(getattr(Tensix, 'TT' + name)(**arguments)) == expected


@pytest.mark.parametrize('name,parameter,value', INVALID)
def test_reject_field_overflow(name, parameter, value):
  with pytest.raises(ValueError):
    getattr(Tensix, 'TT' + name)(**{parameter: value})
