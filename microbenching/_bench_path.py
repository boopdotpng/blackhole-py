"""Path shim so every microbench runs as plain `python3 path/to/script.py` from
any cwd. Adds to sys.path: the repo root (device, program, ttk, ...), examples/
(matmul_peak, drisc_*), the microbenching root, and all microbenching category
subdirs (so flat-era sibling imports keep working). Each script bootstraps with:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import _bench_path  # noqa: F401
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

_paths = [_ROOT, os.path.join(_ROOT, "examples"), _HERE]
for _d in sorted(os.listdir(_HERE)):
  _p = os.path.join(_HERE, _d)
  if os.path.isdir(_p) and _d not in ("docs", "__pycache__"):
    _paths.append(_p)
for _p in _paths:
  if _p not in sys.path:
    sys.path.insert(0, _p)
