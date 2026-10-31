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
  * process_peak_rss_mb -- peak resident memory of this process during the
    run. On Linux the kernel's peak (VmHWM) is reset when the run starts
    (/proc/self/clear_refs = 5), so a worker that runs many points in turn
    reports each run's own peak (memory still held from earlier runs
    included); `process_peak_scope` = "run". Elsewhere it is the peak since
    the process started ("process"), exact only for a fresh process per run
    (A8, v005-a8-analysis.md: the per-worker peak made ~20 methods identical);
  * bridge_peak_rss_mb -- peak memory of the JAHS-Bench-201 query process and
    its children (they hold the surrogate models), sampled at the run's start
    and end and after benchmark queries (at most every SAMPLE_SECONDS). The
    bridge is either the run's own process or the machine's shared bridge
    (substrate.bridge_pid()); the shared one serves all workers at once, so
    its value is a machine-level cost, not one run's. On Linux each sample is
    the sum of PSS (shared copy-on-write pages of the forked handlers split
    between them, not counted once per handler); elsewhere the sum of RSS.
    `bridge_memory_method` names which;
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


#: Minimum seconds between two bridge-memory samples taken after queries.
SAMPLE_SECONDS = 5.0


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
        #: called after each benchmark query (ResourceMeter samples the bridge's memory)
        self.after_query = None

    def _timed(self, clock: _Clock, fn, *args):
        started = time.perf_counter()
        try:
            return fn(*args)
        finally:
            clock.seconds += time.perf_counter() - started
            clock.calls += 1
            if clock is self.benchmark and self.after_query is not None:
                self.after_query()

    def objectives(self, genotype):
        return self._timed(self.benchmark, self._substrate.objectives, genotype)

    def objectives_at_epochs(self, genotype, epochs):
        return self._timed(self.benchmark, self._substrate.objectives_at_epochs, genotype, epochs)

    def analytic_cost_objectives(self, genotype):
        return self._timed(self.analytic, self._substrate.analytic_cost_objectives, genotype)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._substrate, name)


def _bridge_process(substrate: Any) -> psutil.Process | None:
    bridge_pid = getattr(substrate, "bridge_pid", None)
    if callable(bridge_pid):
        pid = bridge_pid()
    else:
        pid = getattr(getattr(substrate, "_process", None), "pid", None)
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


def _proc_kb(path: str, key: str) -> float | None:
    """The `key:` line of a /proc file in kB, None if unreadable."""
    try:
        with open(path, encoding="ascii") as handle:
            for line in handle:
                if line.startswith(key + ":"):
                    return float(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def _reset_peak(pid: int) -> bool:
    """Reset the kernel's peak resident memory (VmHWM) of `pid` (Linux >= 4.0)."""
    try:
        with open(f"/proc/{pid}/clear_refs", "w", encoding="ascii") as handle:
            handle.write("5")
        return True
    except OSError:
        return False


def _peak_rss_mb(process: psutil.Process, *, since_reset: bool = False) -> float:
    """Peak resident memory: VmHWM if the peak was reset at the run start (Linux);
    otherwise the process-lifetime peak (Windows: peak working set; else ru_maxrss of
    this process, or the current RSS of another one)."""
    if since_reset:
        hwm = _proc_kb(f"/proc/{process.pid}/status", "VmHWM")
        if hwm is not None:
            return hwm / 1024.0
    info = process.memory_info()
    peak = getattr(info, "peak_wset", None)
    if peak is not None:
        return peak / 2**20
    if process.pid == psutil.Process().pid:
        import resource  # ru_maxrss is in kilobytes on Linux

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    return info.rss / 2**20


def _tree_memory_mb(process: psutil.Process) -> tuple[float | None, str]:
    """Current memory of the process tree: sum of PSS on Linux, of RSS elsewhere."""
    members = _tree(process)
    if not members:
        return None, "none"
    pss = [_proc_kb(f"/proc/{m.pid}/smaps_rollup", "Pss") for m in members]
    if all(v is not None for v in pss):
        return sum(pss) / 1024.0, "pss_sum"
    total = 0.0
    for member in members:
        try:
            total += member.memory_info().rss / 2**20
        except psutil.Error:
            continue
    return total, "rss_sum"


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
    _peak_reset: bool = field(default=False, init=False)
    _bridge_peak: float | None = field(default=None, init=False)
    _bridge_method: str | None = field(default=None, init=False)
    _last_sample: float = field(default=float("-inf"), init=False)

    def _sample_bridge(self, *, force: bool = False) -> None:
        now = time.perf_counter()
        if not force and now - self._last_sample < SAMPLE_SECONDS:
            return
        self._last_sample = now
        bridge = _bridge_process(self.substrate)
        if bridge is None:
            return
        try:
            mb, method = _tree_memory_mb(bridge)
        except psutil.Error:
            return
        if mb is not None and (self._bridge_peak is None or mb > self._bridge_peak):
            self._bridge_peak, self._bridge_method = mb, method

    def __enter__(self) -> ResourceMeter:
        cuda = _cuda()
        if cuda is not None:
            cuda.reset_peak_memory_stats()
        self._peak_reset = sys.platform.startswith("linux") and _reset_peak(self._process.pid)
        self._sample_bridge(force=True)
        if hasattr(self.substrate, "after_query"):
            self.substrate.after_query = self._sample_bridge
        self._bridge_cpu = _cpu_seconds(_bridge_process(self.substrate), tree=True)
        self._cpu = _cpu_seconds(self._process) or 0.0
        self._wall = time.perf_counter()
        self._load0 = self._load_total()
        return self

    def _load_total(self) -> float | None:
        inner = getattr(self.substrate, "_substrate", self.substrate)
        return getattr(inner, "surrogate_load_seconds_total", None)

    def __exit__(self, *exc) -> None:
        self.wall_seconds = time.perf_counter() - self._wall
        load = self._load_total()
        # BM-5: bridge load time within this run (0.0 if it was already loaded); None = no bridge
        self.surrogate_load_seconds = None if load is None else load - (self._load0 or 0.0)
        self.cpu_seconds = (_cpu_seconds(self._process) or 0.0) - self._cpu
        bridge_now = _cpu_seconds(_bridge_process(self.substrate), tree=True)
        # The bridge may only start during the run (first query).
        self.bridge_cpu_seconds = (
            None if bridge_now is None else bridge_now - (self._bridge_cpu or 0.0)
        )
        self.peak_rss_mb = _peak_rss_mb(self._process, since_reset=self._peak_reset)
        self.process_peak_scope = "run" if self._peak_reset else "process"
        self._sample_bridge(force=True)
        if hasattr(self.substrate, "after_query"):
            self.substrate.after_query = None
        self.bridge_peak_rss_mb = self._bridge_peak
        self.bridge_memory_method = self._bridge_method
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
            "process_peak_scope": self.process_peak_scope,
            "bridge_peak_rss_mb": self.bridge_peak_rss_mb,
            "bridge_memory_method": self.bridge_memory_method,
            "gpu_peak_memory_mb": self.gpu_peak_memory_mb,
            "surrogate_load_seconds": getattr(self, "surrogate_load_seconds", None),
        }
