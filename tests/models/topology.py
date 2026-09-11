# Additional compiler-only topology from the forks; central boots 120 tiles.
P150_WORKER_CORES = tuple(
  (x, y) for x in (*range(1, 8), *range(10, 17)) for y in range(2, 12)
  if (x, y) not in ((16, 2), (16, 3), (16, 4))
)
