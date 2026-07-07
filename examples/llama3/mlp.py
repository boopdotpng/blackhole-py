#!/usr/bin/env python3
"""Llama 3.2 1B MLP bringup.

Reference:

    class MLP:
      def __call__(self, x):
        gate = self.gate_proj(x)        # what features to let through
        up   = self.up_proj(x)          # candidate features
        hidden = gate.silu() * up       # soft conditional filter
        return self.down_proj(hidden)   # residual update, back to emb_dim

Device decomposition (first bringup, one kernel launch per box):

    x @ gate_proj_t  ->  gate         (matmul)
    x @ up_proj_t    ->  up           (matmul)
    silu(gate)       ->  silu_gate    (unary SFPU kernel)
    silu_gate * up   ->  hidden       (elementwise-multiply kernel)
    hidden @ down_proj_t -> out       (matmul)

Everything is built on rmsnorm.py's proven kernel harness (its Trisc/Brisc/
Ncrisc roles, matmul/alloc helpers, unary-SFPU rsqrt path and _run_elwmul_device).
The only new firmware here is the SiLU TRISC1 math body, which is rmsnorm's
rsqrt TRISC1 skeleton with the SFPU sequence swapped for an approximate sigmoid
multiply.  No add1 machinery is copied.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
for path in (ROOT, EXAMPLES):
  if str(path) not in sys.path:
    sys.path.insert(0, str(path))

from device import Device  # noqa: E402
from program import Program  # noqa: E402
from dsl import (  # noqa: E402
  TTINCRWC, TTMOP, TTSEMPOST, TTSEMWAIT, TTSETRWC, TTSTALLWAIT,
  s5, t1, t2, t3,
)
from ttk.sfpu import emit_silu_tile  # noqa: E402
from ttk.tensix import TensixSem, TensixSemWait, TensixStall, TensixWait  # noqa: E402
import matmul_peak as mm  # noqa: E402
from llama3 import rmsnorm as rn  # noqa: E402


EMB_DIM = 2048
MLP_SIZE = 8192
ROWS = 32
TILE = rn.TILE
DTYPE = rn.DTYPE
TILE_BYTES = rn.TILE_BYTES
OUT_CB = rn.OUT_CB
CB_DEPTH = rn.CB_DEPTH


# ---------------------------------------------------------------------------
# Host reference
# ---------------------------------------------------------------------------
def silu(x: np.ndarray) -> np.ndarray:
  return x / (1.0 + np.exp(-x))


def mlp_reference(
  x: np.ndarray,
  gate_proj_t: np.ndarray,
  up_proj_t: np.ndarray,
  down_proj_t: np.ndarray,
) -> np.ndarray:
  gate = x @ gate_proj_t
  up = x @ up_proj_t
  hidden = silu(gate) * up
  return hidden @ down_proj_t


# ---------------------------------------------------------------------------
# SiLU unary kernel
#
# Modeled directly on rmsnorm._rsqrt_trisc1: unpack (TRISC0) lands the tile in
# srcA, MATH_MOVA2D_MOP copies srcA -> DEST, then the SFPU rewrites DEST in
# place.  We only replace rsqrt's SFPU body with the approximate sigmoid used by
# ttk.sfpu (silu(x) = x * sigmoid(x)).
# ---------------------------------------------------------------------------
def _emit_silu_tile(fw) -> None:
  """SFPU pass over one DEST tile: DEST <- silu(DEST), 4 faces x 8 row groups."""
  if os.environ.get("MLP_SILU_DEBUG") == "copy":
    from dsl import TTSFPLOAD, TTSFPNOP, TTSFPSTORE  # identity bisect path
    for _face in range(4):
      for _row in range(8):
        fw.emit(TTSFPLOAD(0, 0, 7, 0))
        fw.emit(TTSFPSTORE(0, 0, 7, 0))
        fw.emit(TTSFPNOP())
        fw.emit(TTINCRWC(0, 2, 0, 0))
      fw.emit(TTSETRWC(0, 4, 8, 0, 0, 4))
      fw.emit(TTSETRWC(0, 4, 8, 0, 0, 4))
    return
  emit_silu_tile(fw)


def _silu_trisc1() -> rn.Trisc:
  fw = rn.Trisc(1, rn.SYNC)
  fw.prologue()
  fw.math.init(dtype=DTYPE, mop_cfg=rn.MATH_MOVA2D_MOP)
  fw.init_barrier()

  with fw.tile_loop():
    fw.emit(TTSEMWAIT(
      rn.STALL_MATH_PACK_ROOM,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_MAX,
    ))
    fw.read32(t1, fw.data["dest_offset_id"])
    rn._write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTMOP(1, 0, 0))                      # mova2d srcA -> DEST
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, fw.data["dest_offset_id"])
    rn._write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
    _emit_silu_tile(fw)                          # DEST <- silu(DEST)
    fw.push_tensix(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.push_tensix(TTSTALLWAIT(TensixStall.SYNC, rn.WAIT_MATH_AND_SFPU))
    fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.MATH_PACK)))
    fw.addi(t2, s5, 1)
    fw.signal_sync(rn.SYNC_DONE1, t2)
    fw.read32(t1, fw.data["dest_offset_id"])
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(fw.data["dest_offset_id"], t2)
    fw.emit(TTSTALLWAIT(TensixStall.CFG, rn.WAIT_MATH_AND_SFPU))
    rn._write_trisc1_dest_offset_instr(fw, t2, t1, t3)
  return fw


def _build_silu_program(
  in_addr: int,
  out_addr: int,
  num_banks: int,
  *,
  core: tuple[int, int],
  tiles: int,
  in_base: int = 0,
  out_base: int = 0,
  in_stride: int = 1,
  out_stride: int = 1,
  dram_bank_coords_noc0: list[int] | None = None,
  dram_bank_coords_noc1: list[int] | None = None,
) -> Program:
  if dram_bank_coords_noc0 is None:
    dram_bank_coords_noc0 = mm.p100_dram_bank_endpoint_coords(None, 0)[:num_banks]
  if dram_bank_coords_noc1 is None:
    dram_bank_coords_noc1 = mm.p100_dram_bank_endpoint_coords(None, 1)[:num_banks]

  brisc_fw = rn._unary_brisc(dram_bank_coords_noc0)
  ncrisc_fw = rn._elwmul_ncrisc(dram_bank_coords_noc1)
  trisc0_fw = rn._rsqrt_trisc0()        # unpack CB0 -> srcA (single input)
  trisc1_fw = _silu_trisc1()            # mova2d + SFPU silu
  trisc2_fw = rn._elwmul_trisc2()       # pack DEST -> OUT_CB

  brisc_fw.rta(lambda _x, _y: [in_addr, in_base, tiles, num_banks, in_stride])
  ncrisc_fw.rta(lambda _x, _y: [out_addr, out_base, tiles, num_banks, out_stride])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "llama3_mlp_silu"
  return prog


def _run_silu_device(device: Device, in_buf, out_buf, *, tiles: int, name: str) -> list[dict]:
  num_banks = len(device.dram.bank_tiles)
  core = device.cores[0]
  prog = _build_silu_program(
    in_buf.addr,
    out_buf.addr,
    num_banks,
    core=core,
    tiles=tiles,
    dram_bank_coords_noc0=mm.p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 0)[:num_banks],
    dram_bank_coords_noc1=mm.p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 1)[:num_banks],
  )
  prog.name = name
  return device.run(prog)


def _run_silu_then_mul_device(
  device: Device,
  gate_buf,
  up_buf,
  out_buf,
  *,
  num_tiles: int,
  name: str = "mlp_hidden",
) -> list[dict]:
  """hidden = silu(gate) * up, as a SiLU unary kernel followed by elwmul."""
  silu_buf = device.dram.alloc(num_tiles, DTYPE, shape=gate_buf.shape, name="silu_gate")
  timings = _run_silu_device(device, gate_buf, silu_buf, tiles=num_tiles, name=f"{name}_silu")
  timings += rn._run_elwmul_device(
    device,
    silu_buf,
    up_buf,
    out_buf,
    tiles=num_tiles,
    bcast=rn.BCAST_NONE,
    b_tile_policy="same",
    name=f"{name}_mul",
  )
  return timings


# ---------------------------------------------------------------------------
# Full MLP
# ---------------------------------------------------------------------------
def _plan_padded(device: Device, m: int, k: int, n: int, cores: list[tuple[int, int]]) -> tuple[int, int, int]:
  """Planned (rows, inner, cols) the peak matmul pads A/B/C to for (m, k, n)."""
  num_banks = len(device.dram.bank_tiles)
  chunks = mm.plan_output_chunks(m, k, n, cores, num_banks)
  return mm.global_padded_shape(m, k, n, chunks)


def _alloc_padded(device: Device, data: np.ndarray, rows: int, cols: int, name: str):
  padded = np.zeros((rows, cols), dtype=np.float32)
  padded[:data.shape[0], :data.shape[1]] = data.astype(np.float32, copy=False)
  return device.alloc_write(mm.to_device_bytes(padded, DTYPE), dtype=DTYPE, shape=(rows, cols), name=name)


def run_mlp_device(
  x: np.ndarray,
  gate_proj_t: np.ndarray,
  up_proj_t: np.ndarray,
  down_proj_t: np.ndarray,
  *,
  cores: list[tuple[int, int]] | None = None,
) -> tuple[np.ndarray, list[dict]]:
  mm.configure_numeric_path(input_dtype=DTYPE, output_dtype=DTYPE, intermediate_dtype=DTYPE)
  device = Device()
  try:
    # Single compute core: this keeps the matmul padding consistent so the
    # gate/up outputs feed straight into the down-proj as its A operand with no
    # host repack (>=2 cores pads down-proj K to 8256 and breaks the chain).
    run_cores = [(cores or device.cores)[0]]

    mp, kp, np_gu = _plan_padded(device, ROWS, EMB_DIM, MLP_SIZE, run_cores)     # gate/up
    md, kd, nd = _plan_padded(device, ROWS, MLP_SIZE, EMB_DIM, run_cores)        # down
    if (mp, np_gu) != (md, kd):
      raise RuntimeError(f"matmul padding does not chain: gate/up C={(mp, np_gu)} vs down A={(md, kd)}")

    x_buf = _alloc_padded(device, x, mp, kp, "x")
    gate_w_buf = _alloc_padded(device, gate_proj_t, kp, np_gu, "gate_proj_t")
    up_w_buf = _alloc_padded(device, up_proj_t, kp, np_gu, "up_proj_t")
    down_w_buf = _alloc_padded(device, down_proj_t, kd, nd, "down_proj_t")

    gate_buf = rn._alloc_empty(device, (mp, np_gu), "gate")
    up_buf = rn._alloc_empty(device, (mp, np_gu), "up")
    hidden_buf = rn._alloc_empty(device, (md, kd), "hidden")
    out_buf = rn._alloc_empty(device, (md, nd), "mlp_out")

    timings: list[dict] = []
    timings += rn._run_matmul(
      device, a_buf=x_buf, b_buf=gate_w_buf, c_buf=gate_buf,
      m=ROWS, k=EMB_DIM, n=MLP_SIZE, cores=run_cores, name="mlp_gate_proj",
    )
    timings += rn._run_matmul(
      device, a_buf=x_buf, b_buf=up_w_buf, c_buf=up_buf,
      m=ROWS, k=EMB_DIM, n=MLP_SIZE, cores=run_cores, name="mlp_up_proj",
    )

    hidden_tiles = (hidden_buf.shape[0] // TILE) * (hidden_buf.shape[1] // TILE)
    timings += _run_silu_then_mul_device(device, gate_buf, up_buf, hidden_buf, num_tiles=hidden_tiles)

    timings += rn._run_matmul(
      device, a_buf=hidden_buf, b_buf=down_w_buf, c_buf=out_buf,
      m=ROWS, k=MLP_SIZE, n=EMB_DIM, cores=run_cores, name="mlp_down_proj",
    )

    return rn._read_matrix(device, out_buf, (ROWS, EMB_DIM)), timings
  finally:
    device.close()


# ---------------------------------------------------------------------------
# Inputs / checking
# ---------------------------------------------------------------------------
def make_inputs(seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
  rng = np.random.default_rng(seed)
  x = rng.normal(0.0, 0.02, size=(ROWS, EMB_DIM)).astype(np.float32)
  gate = rng.normal(0.0, 0.02, size=(EMB_DIM, MLP_SIZE)).astype(np.float32)
  up = rng.normal(0.0, 0.02, size=(EMB_DIM, MLP_SIZE)).astype(np.float32)
  down = rng.normal(0.0, 0.02, size=(MLP_SIZE, EMB_DIM)).astype(np.float32)
  return tuple(rn.bf16_round(t) for t in (x, gate, up, down))


def check_result(got: np.ndarray, ref: np.ndarray, *, min_pcc: float = 0.98, max_rel_l2: float = 0.35) -> tuple[float, float]:
  ref = ref[:got.shape[0], :got.shape[1]]
  if not np.isfinite(got).all():
    raise AssertionError("MLP output contains non-finite values")
  rel_l2 = float(np.linalg.norm(got - ref) / (np.linalg.norm(ref) + 1e-12))
  pcc = float(np.corrcoef(got.reshape(-1), ref.reshape(-1))[0, 1])
  if pcc < min_pcc or rel_l2 > max_rel_l2:
    raise AssertionError(f"MLP check failed: pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  return pcc, rel_l2


def _print_timings(timings: list[dict]) -> None:
  for timing in timings:
    name = f"{timing['name']}: " if timing.get("name") else ""
    print(f"  {name}{timing['us']:,.1f} us")


# ---------------------------------------------------------------------------
# Standalone bringup tests
# ---------------------------------------------------------------------------
def run_silu_test(*, seed: int, tiles: int, max_rel_l2: float = 0.15) -> None:
  if tiles <= 0:
    raise ValueError("--tiles must be positive")
  rng = np.random.default_rng(seed)
  gate = rn.bf16_round(rng.normal(0.0, 1.0, size=(tiles, TILE, TILE)).astype(np.float32))
  expected = silu(gate)

  device = Device()
  try:
    gate_buf = device.dram.alloc(tiles, DTYPE, shape=gate.shape, name="silu_in")
    out_buf = device.dram.alloc(tiles, DTYPE, shape=gate.shape, name="silu_out")
    device.dram_write(gate_buf, mm.to_device_bytes(gate, DTYPE))
    device.dram_write(out_buf, mm.to_device_bytes(np.full(gate.shape, 7.0, np.float32), DTYPE))
    timings = _run_silu_device(device, gate_buf, out_buf, tiles=tiles, name="silu_test")
    got = mm.from_device_bytes(device.dram_read(out_buf), DTYPE, gate.shape)
  finally:
    device.close()

  rel_l2 = float(np.linalg.norm(got - expected) / (np.linalg.norm(expected) + 1e-12))
  pcc = float(np.corrcoef(got.reshape(-1), expected.reshape(-1))[0, 1])
  if not np.isfinite(got).all() or rel_l2 > max_rel_l2 or pcc < 0.98:
    raise AssertionError(f"silu mismatch pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  print(f"silu: ok tiles={tiles} pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  _print_timings(timings)


def run_silu_mul_test(*, seed: int, tiles: int, max_rel_l2: float = 0.15) -> None:
  if tiles <= 0:
    raise ValueError("--tiles must be positive")
  rng = np.random.default_rng(seed)
  gate = rn.bf16_round(rng.normal(0.0, 1.0, size=(tiles, TILE, TILE)).astype(np.float32))
  up = rn.bf16_round(rng.normal(0.0, 1.0, size=(tiles, TILE, TILE)).astype(np.float32))
  expected = silu(gate) * up

  device = Device()
  try:
    gate_buf = device.dram.alloc(tiles, DTYPE, shape=gate.shape, name="gate")
    up_buf = device.dram.alloc(tiles, DTYPE, shape=up.shape, name="up")
    out_buf = device.dram.alloc(tiles, DTYPE, shape=up.shape, name="hidden")
    device.dram_write(gate_buf, mm.to_device_bytes(gate, DTYPE))
    device.dram_write(up_buf, mm.to_device_bytes(up, DTYPE))
    device.dram_write(out_buf, mm.to_device_bytes(np.full(up.shape, 7.0, np.float32), DTYPE))
    timings = _run_silu_then_mul_device(device, gate_buf, up_buf, out_buf, num_tiles=tiles, name="silu_mul_test")
    got = mm.from_device_bytes(device.dram_read(out_buf), DTYPE, up.shape)
  finally:
    device.close()

  rel_l2 = float(np.linalg.norm(got - expected) / (np.linalg.norm(expected) + 1e-12))
  pcc = float(np.corrcoef(got.reshape(-1), expected.reshape(-1))[0, 1])
  if not np.isfinite(got).all() or rel_l2 > max_rel_l2 or pcc < 0.98:
    raise AssertionError(f"silu*mul mismatch pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  print(f"silu*mul: ok tiles={tiles} pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  _print_timings(timings)


def parse_core(value: str) -> tuple[int, int]:
  x, y = value.split(",", 1)
  return int(x, 0), int(y, 0)


def main() -> None:
  parser = argparse.ArgumentParser(description="Bringup Llama 3.2 1B MLP path.")
  sub = parser.add_subparsers(dest="command")

  mlp = sub.add_parser("mlp", help="run the full MLP path on device")
  mlp.add_argument("--run", action="store_true")
  mlp.add_argument("--seed", type=int, default=0)
  mlp.add_argument("--core", type=parse_core, action="append", dest="cores")

  for name in ("silu-test", "silu-mul-test"):
    p = sub.add_parser(name, help=f"DRAM-to-DRAM {name}")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--tiles", type=int, default=4)
    p.add_argument("--max-rel-l2", type=float, default=0.15)

  args = parser.parse_args()

  if args.command == "silu-test":
    run_silu_test(seed=args.seed, tiles=args.tiles, max_rel_l2=args.max_rel_l2)
    return
  if args.command == "silu-mul-test":
    run_silu_mul_test(seed=args.seed, tiles=args.tiles, max_rel_l2=args.max_rel_l2)
    return

  x, gate, up, down = make_inputs(getattr(args, "seed", 0))
  ref = mlp_reference(x, gate, up, down)
  print("host-reference: ok")

  if getattr(args, "run", False):
    got, timings = run_mlp_device(x, gate, up, down, cores=args.cores)
    pcc, rel_l2 = check_result(got, ref)
    print(f"device-mlp: ok pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
    _print_timings(timings)


if __name__ == "__main__":
  main()
