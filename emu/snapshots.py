from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


class SnapshotRecorder:
  """Optional per-core searchable state recorder.

  Records are kept in memory during the run and written as one JSON document:
    {"schema": 1, "cores": {"x,y": [{...}, ...]}}

  This is intentionally opt-in; normal emulator runs should not pay for
  snapshot construction.
  """

  DEFAULT_PATH = Path("./emu-snapshots.json")

  def __init__(self, path: str | os.PathLike[str] | None = None,
               *, max_per_core: int | None = None):
    self.path = Path(path) if path else self.DEFAULT_PATH
    self.max_per_core = (
      int(os.environ.get("EMU_SNAPSHOT_MAX_PER_CORE", "20000"))
      if max_per_core is None else int(max_per_core)
    )
    self.cores: dict[str, list[dict[str, Any]]] = defaultdict(list)
    self.dropped: dict[str, int] = defaultdict(int)

  @property
  def enabled(self) -> bool:
    return True

  def record(self, core: str, event: str, **state: Any) -> None:
    arr = self.cores[str(core)]
    if len(arr) >= self.max_per_core:
      self.dropped[str(core)] += 1
      return
    rec = {"event": event}
    rec.update(_jsonable(state))
    arr.append(rec)

  def write(self, path: str | os.PathLike[str] | None = None) -> None:
    out_path = Path(path) if path is not None else self.path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
      "schema": 1,
      "cores": dict(sorted(self.cores.items())),
      "dropped": dict(sorted(self.dropped.items())),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _jsonable(value: Any) -> Any:
  if isinstance(value, dict):
    return {str(k): _jsonable(v) for k, v in value.items()}
  if isinstance(value, (list, tuple)):
    return [_jsonable(v) for v in value]
  if isinstance(value, (str, int, float, bool)) or value is None:
    return value
  return repr(value)


def sample_words16(mem, addr: int, count: int = 8) -> list[str]:
  return [f"{mem.read16(addr + i * 2) & 0xFFFF:04x}" for i in range(count)]


def nonzero_counts(src_regfile) -> list[int]:
  return [
    sum(1 for row in bank.rows for val in row if val)
    for bank in src_regfile.banks
  ]


def nonzero_row_sample(bank, *, max_rows: int = 8,
                       cols: int = 4) -> list[dict[str, Any]]:
  out = []
  for r, row in enumerate(bank.rows):
    nz = sum(1 for val in row if val)
    if not nz:
      continue
    out.append({
      "row": r,
      "nz": nz,
      "first": [f"0x{val:x}" for val in row[:cols]],
    })
    if len(out) >= max_rows:
      break
  return out


def dest_valid_sample(dest, *, max_rows: int = 16,
                      cols: int = 4) -> list[dict[str, Any]]:
  out = []
  for r, valid in enumerate(dest.valid):
    if not valid:
      continue
    out.append({
      "row": r,
      "first": [f"0x{val & 0xFFFFFFFF:x}" for val in dest.bits[r][:cols]],
    })
    if len(out) >= max_rows:
      break
  return out
