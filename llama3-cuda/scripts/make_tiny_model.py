#!/usr/bin/env python3
import argparse
import struct
from pathlib import Path

import numpy as np


MAGIC = b"L32CU001"
VERSION = 2  # bf16 payload


def to_bf16_bits(f32: np.ndarray) -> np.ndarray:
    # numpy has no bfloat16; round fp32 to nearest-even and keep the top 16 bits.
    bits = f32.astype(np.float32).view(np.uint32)
    rounded = bits + 0x7FFF + ((bits >> 16) & 1)
    return (rounded >> 16).astype(np.uint16)


def write_tensor(f, rng, shape, scale=0.02):
    data = rng.standard_normal(shape).astype(np.float32) * scale
    f.write(to_bf16_bits(data).tobytes())


def write_ones(f, dim):
    f.write(to_bf16_bits(np.ones((dim,), dtype=np.float32)).tobytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="build/tiny.l3cu")
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    dim = 32
    hidden_dim = 64
    n_layers = 2
    n_heads = 4
    n_kv_heads = 2
    vocab_size = 128
    max_pos = 128
    rope_dim = dim // n_heads
    header_size = struct.calcsize("<8s9i6fQ")

    rng = np.random.default_rng(1234)
    with out.open("wb") as f:
        f.write(
            struct.pack(
                "<8s9i6fQ",
                MAGIC,
                VERSION,
                dim,
                hidden_dim,
                n_layers,
                n_heads,
                n_kv_heads,
                vocab_size,
                max_pos,
                rope_dim,
                1e-5,
                500000.0,
                1.0,
                1.0,
                1.0,
                float(max_pos),
                0,
            )
        )
        write_tensor(f, rng, (vocab_size, dim))
        kv_dim = n_kv_heads * rope_dim
        for _ in range(n_layers):
            write_ones(f, dim)
            write_tensor(f, rng, (dim, dim))
            write_tensor(f, rng, (kv_dim, dim))
            write_tensor(f, rng, (kv_dim, dim))
            write_tensor(f, rng, (dim, dim))
            write_ones(f, dim)
            write_tensor(f, rng, (hidden_dim, dim))
            write_tensor(f, rng, (hidden_dim, dim))
            write_tensor(f, rng, (dim, hidden_dim))
        write_ones(f, dim)
        end = f.tell()
        f.seek(0)
        f.write(
            struct.pack(
                "<8s9i6fQ",
                MAGIC,
                VERSION,
                dim,
                hidden_dim,
                n_layers,
                n_heads,
                n_kv_heads,
                vocab_size,
                max_pos,
                rope_dim,
                1e-5,
                500000.0,
                1.0,
                1.0,
                1.0,
                float(max_pos),
                end - header_size,
            )
        )
    print(out)


if __name__ == "__main__":
    main()
