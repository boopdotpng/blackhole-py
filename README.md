# blackhole-py

A partial replacement for:

- tt-metal
- tt-umd
- tt-llk
- sfpi (C++ compiler)
- ttlang (technically, soon)
- basically their entire software stack above tt-kmd

Build or run the 32x2048 Llama 3.2 RMSNorm example:

```sh
python3 examples/rmsnorm.py
python3 examples/rmsnorm.py --run --repeats 20
```

Build and inspect the 118-core FP32-accumulating mean kernel, or benchmark it
on hardware:

```sh
python3 examples/mean.py
python3 examples/mean.py --run --tiles 118 --repeats 10
```

## Caveats
- P150 support is tentative.
- No distributed or multi-card support yet.
