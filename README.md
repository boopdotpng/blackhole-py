# blackhole-py

Write kernels in TTRV, run them on a Tenstorrent Blackhole card from Python, CUDA style.

```python
import numpy as np
from ttrv import Device, Var

with Device(0) as dev:
  x = dev.array(np.ones(1024, np.float32))           # DRAM buffer, filled from the host
  y = dev.empty(1024, "fp32")
  scale = dev.kernel("scale.ttrv", N=1024)           # compile with N defined, install
  scale(x=x, y=y, k=2)                               # queued; returns at once
  print(y.numpy())                                   # waits for the device, copies back

  k = Var("k")
  with dev.graph() as g:                             # launches are recorded, not run
    scale(x=x, y=y, k=k)
  g(k=3).wait()                                      # replay with k bound to 3
```

`dev.array` also takes safetensors tensors (`helpers.safe_load`), so a checkpoint goes to the card as stored.

## Requirements

- `tt-kmd` >= 2.12.0 (`smi.py` reads telemetry with the `NOC_READ` ioctl, added in 2.12.0)
- Python with `numpy` and `tiktoken`
- `clang` and `llvm-objcopy`

## Examples

[examples/llama3.py](examples/llama3.py) runs Llama 3 decode in 90 lines: it loads the checkpoint, compiles the kernels in [examples/llama3](examples/llama3), captures one decode step as a graph and replays it per position. Weights go in `weights/llama3-1b/`, `weights/llama3-8b-bf16/` or `weights/llama3-8b-fp8/`.

```sh
python examples/llama3.py --model 1b --tokens 64
```

| Model | tok/s (p150a) |
| --- | ---: |
| 1B BF16 | 157.6 |
| 8B FP8 | 38.1 |
| 8B BF16 | 29.3 |
