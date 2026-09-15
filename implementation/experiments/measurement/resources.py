"""Per-run resource measurement: the practical-cost dimension of every run.

Recorded for every run (diagnostics["resources"], scripts/run_experiment.py):
  * wall_seconds, cpu_seconds -- wall-clock and CPU time of the run in this
    process (CPU time = user + system, all threads);
  * benchmark_seconds / benchmark_queries -- wall-clock time spent inside
    full-evaluation queries to the benchmark (tabular lookup or surrogate
    benchmark), and how many there were;
  * analytic_cost_seconds / analytic_cost_queries -- time spent computing f2
    for candidates that are not evaluated (P3Net's analytic cost hook);
  * optimizer_seconds = wall_seconds - benchmark_seconds: the optimiser's
    own overhead (surrogate fits, acquisition optimisation, bookkeeping),
    the part of the cost a real deployment would add on top of training;
  * bridge_cpu_seconds -- CPU time of the JAHS-Bench-201 query process
    during the run, where that benchmark is used;
  * process_peak_rss_mb -- peak resident memory of this process since it
    started. With several runs in one process it is an upper bound for the
    run; the sequential timing stage runs each point in a fresh process,
    where it is exact;
  * bridge_peak_rss_mb -- peak resident memory of the JAHS-Bench-201 query
    process and its children since they started (they hold the benchmark's
    surrogate models); the sum of per-process peaks, an upper bound;
  * gpu_peak_memory_mb -- peak PyTorch CUDA memory during the run, only
    when the run used CUDA.

Timings vary between machines and between repeated runs; they are
measurements, not part of the deterministic result (the history).
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Any

import psutil


@dataclass
class _Clock:
    seconds: float = 0.0
    calls: int = 0


class TimedSubstrate:
    """Delegates everything to `substrate`, timing its query methods."""

    def __init__(self, substrate: Any) -> None:
        self._substrate = substrate
        self.benchmark = _Clock()
        self.analytic = _Clock()

    def _timed(self, clock: _Clock, fn, *args):
        started = time.perf_counter()
        try:
            return fn(*args)
        finally:
            clock.seconds += time.perf_counter() - started
            clock.calls += 1

    def objectives(self, genotype):
        return self._timed(self.benchmark, self._substrate.objectives, genotype)

    def objectives_at_epochs(self, genotype, epochs):
        return self._timed(self.benchmark, self._substrate.objectives_at_epochs, genotype, epochs)

    def analytic_cost_objectives(self, genotype):
        return self._timed(self.analytic, self._substrate.analytic_cost_objectives, genotype)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._substrate, name)


def _bridge_process(substrate: Any) -> psutil.Process | None:
    process = getattr(substrate, "_process", None)
    pid = getattr(process, "pid", None)
    if pid is None:
        return None
    try:
        return psutil.Process(pid)
    except psutil.Error:
        return None


def _tree(process: psutil.Process) -> list[psutil.Process]:
    """The process and its descendants. On Windows a virtual-environment
    python.exe is a launcher that runs the real interpreter as a child, so
    the JAHS-Bench-201 bridge's work happens in a child process."""
    try:
        return [process, *process.children(recursive=True)]
    except psutil.Error:
        return [process]


def _cpu_seconds(process: psutil.Process | None, *, tree: bool = False) -> float | None:
    if process is None:
        return None
    total = 0.0
    for member in _tree(process) if tree else [process]:
        try:
            times = member.cpu_times()
        except psutil.Error:
            continue
        total += times.user + times.system
    return total


def _peak_rss_mb(process: psutil.Process) -> float:
    """Peak resident memory (Windows). Elsewhere: this process's ru_maxrss,
    or the current resident memory of another process."""
    info = process.memory_info()
    peak = getattr(info, "peak_wset", None)
    if peak is not None:
        return peak / 2**20
    if process.pid == psutil.Process().pid:
        import resource  # ru_maxrss is in kilobytes on Linux

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    return info.rss / 2**20


def _cuda():
    torch = sys.modules.get("torch")  # never import torch just to measure
    if torch is not None and torch.cuda.is_available() and torch.cuda.is_initialized():
        return torch.cuda
    return None


@dataclass
class ResourceMeter:
    substrate: TimedSubstrate
    _process: psutil.Process = field(default_factory=psutil.Process, init=False)
    _wall: float = field(default=0.0, init=False)
    _cpu: float = field(default=0.0, init=False)
    _bridge_cpu: float | None = field(default=None, init=False)

    def __enter__(self) -> ResourceMeter:
        cuda = _cuda()
        if cuda is not None:
            cuda.reset_peak_memory_stats()
        self._bridge_cpu = _cpu_seconds(_bridge_process(self.substrate), tree=True)
        self._cpu = _cpu_seconds(self._process) or 0.0
        self._wall = time.perf_counter()
        return self

    def __exit__(self, *exc) -> None:
        self.wall_seconds = time.perf_counter() - self._wall
        self.cpu_seconds = (_cpu_seconds(self._process) or 0.0) - self._cpu
        bridge_now = _cpu_seconds(_bridge_process(self.substrate), tree=True)
        # The bridge may only start during the run (first query).
        self.bridge_cpu_seconds = (
            None if bridge_now is None else bridge_now - (self._bridge_cpu or 0.0)
        )
        self.peak_rss_mb = _peak_rss_mb(self._process)
        bridge = _bridge_process(self.substrate)
        try:
            self.bridge_peak_rss_mb = (
                None if bridge is None else sum(_peak_rss_mb(p) for p in _tree(bridge))
            )
        except psutil.Error:
            self.bridge_peak_rss_mb = None
        cuda = _cuda()
        self.gpu_peak_memory_mb = None if cuda is None else cuda.max_memory_allocated() / 2**20

    def as_dict(self) -> dict[str, Any]:
        return {
            "wall_seconds": self.wall_seconds,
            "cpu_seconds": self.cpu_seconds,
            "benchmark_seconds": self.substrate.benchmark.seconds,
            "benchmark_queries": self.substrate.benchmark.calls,
            "analytic_cost_seconds": self.substrate.analytic.seconds,
            "analytic_cost_queries": self.substrate.analytic.calls,
            "optimizer_seconds": self.wall_seconds - self.substrate.benchmark.seconds,
            "bridge_cpu_seconds": self.bridge_cpu_seconds,
            "process_peak_rss_mb": self.peak_rss_mb,
            "bridge_peak_rss_mb": self.bridge_peak_rss_mb,
            "gpu_peak_memory_mb": self.gpu_peak_memory_mb,
        }
