"""Execute emitted NIU setup instructions to check MMIO semantics on the CPU."""
import unittest

from ttko.asm import Asm
from ttko.isa import R
from ttko.noc import NiuCommand


def execute_setup(words, initial):
  registers = [0] * 32
  for register, value in initial.items(): registers[int(register)] = value
  stores = []
  def signed(value, bits): return value - (1 << bits) if value & (1 << (bits - 1)) else value
  for word in words:
    opcode, rd, rs1, rs2 = word & 127, (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
    if opcode == 0x37:
      registers[rd] = word & 0xFFFFF000
    elif opcode == 0x13 and (word >> 12) & 7 == 0:
      registers[rd] = (registers[rs1] + signed(word >> 20, 12)) & 0xFFFFFFFF
    elif opcode == 0x23 and (word >> 12) & 7 == 2:
      offset = signed(((word >> 25) << 5) | ((word >> 7) & 31), 12)
      stores.append(((registers[rs1] + offset) & 0xFFFFFFFF, registers[rs2]))
    else:
      raise AssertionError(f'unexpected instruction {word:08x}')
    registers[0] = 0
  return stores, registers


class NiuCodegenTest(unittest.TestCase):
  def test_command_words_and_register_preservation(self):
    for niu in (0, 1):
      for values, initial in (
        ((0x12345678, 0, 0x123, 0x62000, 0, 0x345, 1024, 0x2090, 2048, 0, 0, 0), {}),
        # Deliberately leave inputs unallocated: scratch must still avoid them.
        ((R.TP, 0, R.T0, R.T1, 0, R.T2, 1024, 0x2090, 2048, 0, 0, 0),
         {R.TP: 0x12345678, R.T0: 0x123, R.T1: 0x62000, R.T2: 0x345}),
        ((0,) * 12, {}),
      ):
        with self.subTest(niu=niu, values=values):
          asm = Asm('brisc')
          NiuCommand.build(asm, niu, values[:3], values[3:6], values[6:])
          stores, registers = execute_setup(asm.instructions(), initial)
          expected = [(NiuCommand.address(niu, 4 * i), initial[v] if isinstance(v, R) else v)
                      for i, v in enumerate(values)]
          self.assertEqual(stores, expected)
          for register, value in initial.items(): self.assertEqual(registers[int(register)], value)


if __name__ == '__main__':
  unittest.main()
