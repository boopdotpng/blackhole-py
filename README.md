# blackhole-py

A partial replacement for:

- tt-metal
- tt-umd
- tt-llk
- tt-kmd
- sfpi (C++ compiler)

Written entirely in Python, without any Tenstorrent software. Kernels under
`examples/` are written in Python and lowered to RISC-V that runs on the cores.

See [`docs/TTK.md`](docs/TTK.md) for the kernel-authoring design and
[`docs/tenstorrent-lowering.md`](docs/tenstorrent-lowering.md) for lowering
details.

Build and inspect the add1 kernels without running hardware:

```sh
python3 examples/add1.py
```

Run add1 on hardware:

```sh
python3 examples/add1.py --run
```

Build or run the 32x2048 Llama 3.2 RMSNorm example:

```sh
python3 examples/rmsnorm.py
python3 examples/rmsnorm.py --run --repeats 20
```

## Caveats

- Unbind tt-kmd and make sure VFIO is available.
- P150 support is tentative.
- No distributed or multi-card support yet.
