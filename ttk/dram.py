BANKS = 7

def noc_coord(x: int, y: int): return x | y << 6

def bank_bases(harvested: int):
  if not 0 <= harvested < 8: raise ValueError("harvested DRAM bank must be in [0, 7]")
  half = 4
  mirror = harvested + half - 1 if harvested < half else harvested - half
  if harvested < half:
    right = list(range(half - 1))
    left = [bank for bank in range(half - 1, 7) if bank != mirror] + [mirror]
  else:
    left = [bank for bank in range(half) if bank != mirror] + [mirror]
    right = list(range(half, 7))
  bases = {bank: (18, 12 + index * 3) for index, bank in enumerate(right)}
  bases.update({bank: (17, 12 + index * 3) for index, bank in enumerate(left)})
  return tuple(bases[bank] for bank in range(BANKS))

def endpoint_coords(harvested: int, noc: int):
  if noc not in (0, 1): raise ValueError("NoC index must be 0 or 1")
  ports = ((2, 1), (0, 1), (0, 1), (0, 1), (2, 1), (2, 1), (2, 1))
  return tuple(noc_coord(x, y + ports[bank][noc])
               for bank, (x, y) in enumerate(bank_bases(harvested)))
