## style
- use 2 space indents everywhere 
- max 150 characters per line
- refer to the zen of python

## repo-specific

This is a low level driver for blackhole p100a (i don't have a p150a so i can't test that). After you make a big change, run an example to verify correctness (use a short timeout — kernels should finish in <10 seconds). There is a .venv at ~/tenstorrent that has `tt-smi` installed so you can reset the device (`tt-smi -r`). If that errors, then the card is broken beyond repair and a reboot is required. In this case, stop and inform the user that they may need to reboot.
Do not run multiple device-using commands in parallel. Only one process can own the device at a time, so run hardware tests strictly sequentially.

**Definition of done:** A feature is not complete until it passes both dispatch modes:
1. Fast dispatch (default): `PYTHONPATH=. uv run examples/matmul_peak.py`
2. Slow dispatch: `PYTHONPATH=. TT_USB=1 uv run examples/matmul_peak.py`

**Device queue:** Multiple agents may be working in this repo concurrently. A queue server on `localhost:5741` serializes all device access. If the queue server is running, **always use `claude-collide` instead of running device commands directly.** If `claude-collide` fails to connect (server not running), fall back to running the command normally.

```bash
# Async: submit and get a job ID + output file path back immediately
claude-collide queue PYTHONPATH=. uv run examples/matmul_peak.py
# Returns: job_id=a1b2c3d4 output_file=/tmp/tt-device-logs/a1b2c3d4/output position=2 estimated_wait_sec=30

# Then sleep for the estimated wait, and poll for the result:
claude-collide result a1b2c3d4
# Returns: status=done exit_code=0 output_file=/tmp/tt-device-logs/a1b2c3d4/output
# Read the output file with your Read tool.

# Or blocking: submit and wait for completion (simpler, ties up your shell)
claude-collide exec PYTHONPATH=. uv run examples/matmul_peak.py

# USB dispatch variant:
claude-collide queue env TT_USB=1 PYTHONPATH=. uv run examples/matmul_peak.py

# Device reset:
claude-collide reset

# See what's running:
claude-collide status
```

The `claude-collide` client lives at `~/tenstorrent/tt-device-queue/claude-collide`.

**Kernel/FW cache note:** `~/.cache/tt-cache` can reuse previously built firmware/kernel artifacts for this repo.
After firmware/dispatch changes, stale cache entries can mask real behavior (something can look broken or fixed when
it isn't). If results look inconsistent, clear the relevant cache entries and re-run once before concluding.

When you write kernels, refer to tt-metal for syntax, and note that our kernels will always use every available core (minus 2 if using fast dispatch), and we will write compute kernels exclusively in SFPI/SFPU/FPU ops, not high level tt-llk functions.
