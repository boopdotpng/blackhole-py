"""Replay every SFPU hardware record in sims/results through sims/hw.py. No hardware needed.

  python -m pytest sims/test_sfpu_model.py
"""
import json
from pathlib import Path

import pytest
from sims.hw import sfpu_slope, sfpu_hazards, dst_half_pair_cycles

RESULTS = Path(__file__).parent / "results"
NOP = 0x8F000000
TOL = 0.02  # slopes are medians of two loop lengths; measured spread is <= 0.005


def records(name):
  return [json.loads(line) for line in (RESULTS / name).read_text().splitlines()]


# ---------------------------------------------------------------- matrix

MATRIX = records("2026-11-18-sfpu-matrix-card1.jsonl")


def test_matrix_singles():
  for r in (r for r in MATRIX if r["kind"] == "single"):
    assert abs(sfpu_slope([int(r["word"], 16)]) - r["slope"]) < TOL, r


@pytest.mark.parametrize("gap", (0, 1))
def test_matrix_pairs(gap):
  confirmed, predicted = set(), set()
  for r in (r for r in MATRIX if r["kind"] == "pair"):
    words = [int(r["pword"], 16)] + [NOP] * gap + [int(r["cword"], 16)]
    assert abs(sfpu_slope(words) - r[f"slope_gap{gap}"]) < TOL, (r["producer"], r["consumer"], gap)
    wrong = bool(r["first_bad"][f"gap{gap}"])  # some stored LReg/Dst slot differs from the 3-NOP reference
    hazard = bool(sfpu_hazards(words))
    assert hazard or not wrong, (r["producer"], r["consumer"], gap, "hardware wrong, model silent")
    if hazard: predicted.add(r["consumer"])
    if hazard and wrong: confirmed.add(r["consumer"])
  # every consumer class the model flags was seen to go wrong with at least one producer
  assert predicted == confirmed, predicted - confirmed


# ---------------------------------------------------------------- earlier pair probes (test_sfpu_hazards.py)

HAZARD_UNITS = {
  "nop": ["0x8f000000"], "mad_chain": ["0x8400a900"], "mad_nop_chain": ["0x8400a900", "0x8f000000"],
  "mad_indep_mov": ["0x8401a900", "0x7c000340"], "mad_dep_mov": ["0x8401a900", "0x7c000040"],
  "mad_nop_dep_mov": ["0x8401a900", "0x8f000000", "0x7c000040"],
  "mad_nop_indep_mov": ["0x8401a900", "0x8f000000", "0x7c000340"], "mad_iadd_vc": ["0x8401a900", "0x79000044"],
  "mad_iadd_vd": ["0x8401a900", "0x79000304"], "mad_setsgn_vd": ["0x8401a900", "0x89000300"],
  "mad_and_vb": ["0x8401a900", "0x7e000341"], "mad_minmax": ["0x8401a900", "0x92000301"],
  "mad_nop_minmax": ["0x8401a900", "0x8f000000", "0x92000301"], "mad_swap": ["0x8401a900", "0x92000300"],
  "mad_shuf": ["0x8401a900", "0x94000043"], "mad_loadi_lo": ["0x8401a900", "0x710a1234"],
  "swap_mov": ["0x92000321", "0x7c000560"], "swap_nop_mov": ["0x92000321", "0x8f000000", "0x7c000560"],
  "swap_nop2_mov": ["0x92000321", "0x8f000000", "0x8f000000", "0x7c000560"],
  "shuf_mov": ["0x94000123", "0x7c000560"], "shuf_nop_mov": ["0x94000123", "0x8f000000", "0x7c000560"],
  "shft2_lreg_mov": ["0x94000125", "0x7c000560"], "loadi_pair": ["0x71483f80", "0x714a0000"],
  "sfpload": ["0x70430000"], "sfpstore": ["0x72430000"],
  "load_mad_store": ["0x70030000", "0x8400a900", "0x72030000"],
  "load_mad_nop_store": ["0x70030000", "0x8400a900", "0x8f000000", "0x72030000"],
  "arecip_mad": ["0x99000100", "0x8400a940"], "tt_nop_mad_dep": ["0x8401a900", "0x2000000", "0x7c000040"],
  "mad_ind4": ["0x8400a900", "0x8401a910", "0x8402a920", "0x8403a930"] * 4,
}


@pytest.mark.parametrize("name", ["2026-11-18-sfpu-hazards-card0.jsonl", "2026-11-18-sfpu-hazards-card1.jsonl",
                                  "2026-11-18-sfpu-hazards-prefetchoff-card0.jsonl",
                                  "2026-11-18-sfpu-hazards-prefetchoff-card1.jsonl"])
def test_hazard_probes(name):
  for r in (r for r in records(name) if r["kind"] == "timing"):
    words = [int(w, 16) for w in HAZARD_UNITS[r["case"]]]
    per_unit = sfpu_slope(words) / (16 if r["case"] == "mad_ind4" else 1)
    for s in r["slopes_cycles_per_unit"]: assert abs(per_unit - s) < TOL, (r["case"], s, per_unit)


# ---------------------------------------------------------------- SFPLOADMACRO

def lm(vd): return 0x93 << 24 | (vd & 3) << 20 | 3 << 16


def byte(sel, delay=0, x_in_vb=0, l16=0): return sel | delay << 3 | l16 << 6 | x_in_vb << 7


def seq(units): return sum(b << 8 * u for u, b in units.items())


SIMPLE, MAD, ROUND, STORE = range(4)
LM_CONFIGS = {
  "none": {}, "simple": {SIMPLE: byte(4)}, "mad": {MAD: byte(5, x_in_vb=1)}, "round": {ROUND: byte(6)},
  "store": {STORE: byte(3, delay=2)}, "simple+store": {SIMPLE: byte(4), STORE: byte(3, delay=1)},
  "simple+mad": {SIMPLE: byte(4), MAD: byte(5, delay=1, x_in_vb=1)},
  "all4": {SIMPLE: byte(4), MAD: byte(5, delay=1, x_in_vb=1), ROUND: byte(6, delay=3, l16=1), STORE: byte(3, delay=4)},
  "store_d0": {STORE: byte(3)},
  **{f"simple_d{d}": {SIMPLE: byte(4, delay=d)} for d in range(4)},
  **{f"mad_d{d}": {MAD: byte(5, delay=d, x_in_vb=1)} for d in range(3)},
}
MOV_4_6, MUL_4, LOAD_5 = 0x7C000640, 0x86066940, 0x70530000
LM_UNITS = {"lm": [], "lm_nop": [NOP], "lm_mov": [0x7C000650], "lm_mul": [0x86066950], "lm_load": [LOAD_5]}
LM = records("2026-11-18-sfpu-loadmacro-card1.jsonl")


def test_loadmacro_throughput():
  for r in (r for r in LM if r["kind"] == "loadmacro_timing"):
    words = [w for i in range(16) for w in [lm(i % 4)] + LM_UNITS[r["unit"]]]
    model = sfpu_slope(words, {0: seq(LM_CONFIGS[r["config"]])}) / 16
    assert abs(model - r["slope"]) < TOL, (r["config"], r["unit"], r["slope"], model)


def test_loadmacro_exec_cycle():
  for r in (r for r in LM if r["kind"] == "loadmacro_exec"):
    body = [lm(0)] + [NOP] * (r["k"] - 1) + [0x7C000040]  # MOV L4 <- L0
    hz = sfpu_hazards(body, {0: seq(LM_CONFIGS[f"{r['unit']}_d{r['delay']}"])})
    kind = hz[0][1][0] if hz else None
    observed = {r["L0"]: None, "0x12345678": "dropped", "0x40000000": "stale"}[r["L4"]]
    assert kind == observed, (r["unit"], r["delay"], r["k"], kind, observed)


def test_loadmacro_collisions():
  bodies = {
    "simple_vs_regular_simple": ("simple", MOV_4_6, "dropped"), "simple_vs_regular_mad": ("simple", MUL_4, None),
    "mad_vs_regular_mad": ("mad", MUL_4, "dropped"), "mad_vs_regular_simple": ("mad", MOV_4_6, None),
    "store_d0_vs_regular_store": ("store_d0", 0x72630000, "dropped"), "none_regular_mov": ("none", MOV_4_6, None),
  }
  for r in (r for r in LM if r["kind"] == "loadmacro_collision"):
    config, second, expect = bodies[r["case"]]
    hz = sfpu_hazards([lm(0), second], {0: seq(LM_CONFIGS[config])})
    assert (hz[0][1][0] if hz else None) == expect, r["case"]
    executed = "0x3f000000" in r["dst0"] if second == 0x72630000 else r["L4"] != "0x12345678"
    assert executed == (expect is None), r


# ---------------------------------------------------------------- Dst halves

def test_dst_half():
  for r in (r for r in records("2026-11-18-sfpu-dst-card1.jsonl") if r["kind"] == "dst_half"):
    if r["sfpu"] == "mad": assert abs(r["slope_per_pair"] - 2.0) < TOL; continue
    model = dst_half_pair_cycles(r["batch"], r["where"] != "other_half") / r["batch"]
    assert abs(model - r["slope_per_pair"]) < TOL, r


def test_fpu_to_sfpload_interlocked():
  for r in (r for r in records("2026-11-18-sfpu-dst-card1.jsonl") if r["kind"] == "fpu_to_sfpload"):
    assert all(v == [r["expected_new"]] for v in r["values"]), r
