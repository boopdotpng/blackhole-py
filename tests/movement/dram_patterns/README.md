# DRAM traffic-pattern experiments

Scripts, case lists and raw results for
[docs/dram-traffic-patterns.md](../../../docs/dram-traffic-patterns.md), which explains
every experiment, result and caveat. Not pytest tests; each script runs directly against a
device: `../.venv/bin/python -I tests/movement/dram_patterns/<script>.py <device> <out.json> [cases.json]`.
