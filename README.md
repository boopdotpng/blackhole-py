# blackhole-py

A partial replacement of: 
- tt-metal
- tt-umd
- tt-llk 
- tt-kmd
- sfpi (c++ compiler) 

Written entirely in Python, without any tenstorrent software. Kernels under `examples/` are written in Python, which lowers to risc-v that runs on the cores.

Compiler/target IR design (tinygrad intercept → tile SSA → Tensix): see [TTIR.md](TTIR.md).

Try a matmul:

```sh
PYTHONPATH=. python3 examples/matmul_peak.py 5000 5000 5000

```

## caveats
- Unbind tt-kmd and make sure vfio is available
- p150 support tentative
- No distributed / multi-card support yet. 
