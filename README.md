# blackhole-py

A partial replacement of: 
- tt-metal
- tt-umd
- tt-llk 
- tt-smi
- tt-kmd
- sfpi (c++ compiler) 

Written entirely in Python. Kernels under `examples/` are written in Python, which lowers to risc-v that runs on the cores. 

Try a matmul:

```sh
PYTHONPATH=. python3 examples/matmul_peak.py 1024 1024 1024
```

## caveats

- Unbind tt-kmd and make sure vfio is available
- Blackhole p100a and p150a/b only. p150 support is experimental; I don't have one to test on, but the kernels are equivalent, so it should run. PRs appreciated! 
