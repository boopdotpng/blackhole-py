"""Host-side E4M3 row quantization for the optional Llama LM head."""
import numpy as np


def quantize_rows(values):
  """Return native E4M3 bytes and FP32 dequantization scales per row.

  Round normal values to nearest/even and flush subnormals, matching the
  Blackhole unpacker. Zero rows use scale one rather than dividing by zero.
  """
  values = np.asarray(values, dtype=np.float32)
  if values.ndim != 2 or not np.isfinite(values).all():
    raise ValueError("expected a finite matrix")
  maximum = np.max(np.abs(values), axis=1)
  scales = np.where(maximum == 0, np.float32(1),
                    np.maximum(maximum / np.float32(448), np.finfo(np.float32).tiny))
  scaled = values / scales[:, None]
  bits = np.abs(scaled).view(np.uint32)
  rounded = (bits + np.uint32(0x7ffff) + ((bits >> 20) & 1)) >> 20
  code = np.clip(rounded.astype(np.int32) - 960, 0, 126).astype(np.uint8)
  code[rounded < 968] = 0
  # The subnormal/normal midpoint rounds to the even normal code 8.
  below_normal = np.abs(scaled) < np.float32(1 / 64)
  code[below_normal] = np.where(np.abs(scaled[below_normal]) >= np.float32(15 / 1024), 8, 0)
  code |= (np.signbit(scaled).astype(np.uint8) << 7)
  return code, scales
