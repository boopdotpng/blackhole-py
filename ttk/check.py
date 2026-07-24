"""Buffer precondition checks, so kernels can state their signature in one call.

  check_buffer("embedding weight", weight, dtype=DType.BF16,
               shape=(VOCAB_SIZE, EMBED_DIM), axis=0, global_address=True)

Any mismatch names the buffer, the attribute, what was expected, and what was
passed, which is what a caller actually needs to fix the call.
"""

from ttk import DType

_ALIASES = {"core_count": lambda buffer: len(buffer.cores)}


def check_buffer(name, buffer, **expected):
  """Assert that `buffer` matches every attribute given in `expected`."""
  for attribute, want in expected.items():
    if attribute in _ALIASES: got = _ALIASES[attribute](buffer)
    else:
      try: got = getattr(buffer, attribute)
      except AttributeError:
        raise TypeError(f"buffers have no attribute {attribute!r}") from None
    if attribute == "global_address": got, want = bool(got), bool(want)
    if isinstance(want, tuple) and not isinstance(got, tuple): got = tuple(got)
    if isinstance(want, frozenset):     # frozenset means "any one of these"
      if got in want: continue
      raise ValueError(
        f"{name} must have {attribute} in "
        f"{{{', '.join(_show(option) for option in sorted(want, key=repr))}}}, "
        f"got {_show(got)}",
      )
    if got != want:
      raise ValueError(
        f"{name} must have {attribute}={_show(want)}, got {_show(got)}",
      )
  return buffer


def _show(value):
  if isinstance(value, DType): return value.name
  return repr(value)
