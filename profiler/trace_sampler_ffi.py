"""
ctypes wrapper for the C trace sampler hot loop.

Usage from _TraceSampler:
    from profiler.trace_sampler_ffi import CSampler
    cs = CSampler()  # compiles + loads .so on first use
    cs.run(tlb_mm, ctrl_off, data_off, config_words, max_samples,
           timestamps_ns, raw_words, event_ids, cq_hw, stop_flag, fast=True)
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from array import array
from ctypes import (
    POINTER,
    Structure,
    c_int,
    c_uint32,
    c_uint64,
    c_uint8,
)
from pathlib import Path

_DIR = Path(__file__).resolve().parent
_SRC = _DIR / "trace_sampler.c"
_SO  = _DIR / "trace_sampler.so"


def _compile():
    """Compile the C sampler if the .so is missing or stale."""
    if _SO.exists() and _SO.stat().st_mtime >= _SRC.stat().st_mtime:
        return
    cmd = ["gcc", "-O3", "-march=native", "-shared", "-fPIC", "-o", str(_SO), str(_SRC)]
    print(f"[trace_sampler_ffi] compiling: {' '.join(cmd)}", file=sys.stderr)
    subprocess.check_call(cmd)


class _CQState(Structure):
    _fields_ = [
        ("sysmem",         POINTER(c_uint8)),
        ("noc_local",      c_uint32),
        ("cq_wr_off",      c_uint32),
        ("cursor_16b",     c_uint32),
        ("cursor_toggle",  c_uint32),
        ("page_16b",       c_uint32),
        ("end_16b",        c_uint32),
        ("base_16b",       c_uint32),
    ]


class _Boundary(Structure):
    _fields_ = [
        ("event_id",     c_uint32),
        ("sample_count", c_uint32),
        ("timestamp_ns", c_uint64),
    ]


class _SamplerResult(Structure):
    _fields_ = [
        ("sample_count",     c_uint32),
        ("truncated",        c_int),
        ("mmio_write_ns",    c_uint64),
        ("mmio_read_ns",     c_uint64),
        ("mmio_write_count", c_uint32),
        ("mmio_read_count",  c_uint32),
        ("capture_start_ns", c_uint64),
        ("capture_end_ns",   c_uint64),
        ("boundary_count",   c_uint32),
    ]


# Shared function signature for both run and run_fast
_FUNC_ARGTYPES = [
    POINTER(c_uint8),       # tlb_base
    c_uint32,               # ctrl_off
    c_uint32,               # data_off
    POINTER(c_uint32),      # config_words
    c_uint32,               # words_per_sample
    c_uint32,               # max_samples
    POINTER(c_uint64),      # timestamps_ns
    POINTER(c_uint32),      # raw_words
    POINTER(c_uint32),      # event_ids
    c_uint32,               # num_events
    POINTER(_Boundary),     # boundaries
    POINTER(_CQState),      # cq
    POINTER(c_int),         # stop_flag
    POINTER(_SamplerResult),# result
]


class CSampler:
    def __init__(self):
        _compile()
        self._lib = ctypes.CDLL(str(_SO))
        for name in ("trace_sampler_run", "trace_sampler_run_fast"):
            fn = getattr(self._lib, name)
            fn.argtypes = _FUNC_ARGTYPES
            fn.restype = None

    def run(
        self,
        tlb_mm: "mmap.mmap",
        ctrl_off: int,
        data_off: int,
        config_words: list[int],
        max_samples: int,
        timestamps_ns: array,
        raw_words: array,
        event_ids: list[int],
        cq_hw: "CQSysmem | None",
        stop_flag: "ctypes.c_int",
        fast: bool = True,
    ) -> tuple[_SamplerResult, list[_Boundary]]:
        """
        Run the C sampling loop.  Returns (result, boundaries).

        tlb_mm:     the mmap object from TLBWindow.mm
        stop_flag:  a ctypes.c_int — set to nonzero from another thread to stop
        """
        words_per_sample = len(config_words)

        # Get raw pointer to mmap buffer without exporting (avoids BufferError on close)
        tlb_addr = ctypes.addressof(ctypes.c_char.from_buffer(tlb_mm))
        tlb_ptr = ctypes.cast(tlb_addr, POINTER(c_uint8))

        # Config words array
        c_configs = (c_uint32 * words_per_sample)(*config_words)

        # Output arrays — get raw pointers via buffer_info()
        ts_addr, _ = timestamps_ns.buffer_info()
        rw_addr, _ = raw_words.buffer_info()
        ts_ptr = ctypes.cast(ts_addr, POINTER(c_uint64))
        rw_ptr = ctypes.cast(rw_addr, POINTER(c_uint32))

        # Event IDs
        num_events = len(event_ids)
        c_event_ids = (c_uint32 * max(num_events, 1))(*event_ids) if event_ids else (c_uint32 * 1)(0)

        # Boundaries output
        max_boundaries = max(num_events, 1)
        c_boundaries = (_Boundary * max_boundaries)()

        # CQ state
        cq = _CQState()
        if cq_hw is not None:
            sysmem_addr = ctypes.addressof(ctypes.c_char.from_buffer(cq_hw.sysmem))
            cq.sysmem = ctypes.cast(sysmem_addr, POINTER(c_uint8))
            cq.noc_local = cq_hw.noc_local
            cq.cq_wr_off = 3 * 64  # _HOST_CQ_WR_OFF = 3 * PCIE_ALIGN; PCIE_ALIGN = 64
            cursor_16b, cursor_toggle = cq_hw.completion_cursor
            cq.cursor_16b = cursor_16b
            cq.cursor_toggle = cursor_toggle
            cq.page_16b = cq_hw.completion_page_16b
            cq.end_16b = cq_hw.completion_end_16b
            cq.base_16b = cq_hw.completion_base_16b
        else:
            cq.sysmem = None

        result = _SamplerResult()

        fn = self._lib.trace_sampler_run_fast if fast else self._lib.trace_sampler_run
        fn(
            tlb_ptr,
            c_uint32(ctrl_off),
            c_uint32(data_off),
            c_configs,
            c_uint32(words_per_sample),
            c_uint32(max_samples),
            ts_ptr,
            rw_ptr,
            c_event_ids,
            c_uint32(num_events),
            c_boundaries,
            ctypes.byref(cq),
            ctypes.byref(stop_flag),
            ctypes.byref(result),
        )

        boundaries = [c_boundaries[i] for i in range(result.boundary_count)]
        return result, boundaries
