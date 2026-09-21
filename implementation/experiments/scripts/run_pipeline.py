"""
Crash-safe, resumable from-scratch experiment pipeline.

Runs every stage of a plan (configs/pipeline/<name>.yaml) into one run root,
`results/runs/<commit>/` by default, and can be restarted at any time --
after a crash, a reboot, Ctrl+C, or a killed process -- to continue from the
last completed run. Nothing already completed is ever recomputed.

How resumption stays correct
----------------------------
* One file per grid point, written atomically (scripts/run_experiment.py
  `persist_run`: temp file, fsync, rename). A crash leaves either no file or
  a complete one.
* On every start, each expected file is VALIDATED, not merely checked for
  existence: it must parse, name the right method/search space/budget/seed,
  and have a history consistent with its own evaluation count. Anything that
  fails is moved to `quarantine/` (never deleted) and re-run.
* Leftover `*.tmp` files from an interrupted write are removed.
* Failures (a run raising) are appended to `failures.jsonl` with the full
  traceback; the pipeline moves on to the next point instead of stopping.
  A failed point is retried on the next invocation, up to `--max-retries`
  attempts, then reported as given up (`--retry-failed` resets that).
* After a failure the benchmark substrate is rebuilt, so a dead JAHS bridge
  process does not poison every following run.

How it stays one experiment
---------------------------
`manifest.json` records the git commit, whether tracked code was modified,
a hash of any such modification, the plan hash, and a hash of every method
and search-space config the plan uses. Resuming into a run root whose
manifest disagrees with the current code or configs is refused: mixing code
versions inside one set of results is exactly what this pipeline exists to
prevent. Start a new run root instead.

Parallel execution
------------------
`--workers N` runs grid stages in N worker processes sharing one run root.
A worker claims a grid point by creating `locks/<point>.lock` exclusively
(os.O_EXCL -- atomic on the same filesystem), so no point runs twice at
once; a lock left behind by a dead process (its PID no longer exists on
this host) is removed and the point runs again. Methods that need an
exclusive resource (the GPU, or a lot of memory) name a slot in the plan's
`parallel.slots`; a worker runs such a point only while it also holds one
of that slot's `capacity` slot locks, and otherwise leaves it for later.
Every worker runs its numerical libraries with the plan's
`parallel.threads_per_run` threads, whatever N is, so N changes neither
results nor per-run CPU accounting. Worker output goes to
`logs/worker-<i>.log`.

Several machines
----------------
`--shard i/N` runs only the points whose key hashes to shard `i` of `N`, so N
machines (or N run roots) can split one plan with no coordination at all: each
machine gets a disjoint, deterministic subset, and the raw files are merged
afterwards by copying them into one directory. Sharding is the recommended way
to split work across machines; a shared network directory also works, but a
lock left behind by a crashed process on another host is only broken by
`--unlock-after <hours>` (a process is never assumed dead on a host this one
cannot see).

Timing stage
------------
`kind: timing` stages run after all grid stages, one point at a time, each
in a fresh process with no other run on the machine (D5): wall-clock, CPU
and memory measurements from contended parallel runs are not reported as
costs. Results go to `timing/raw/`. Each invocation also appends the
hardware and software manifest (measurement/hardware.py) to
`sessions.jsonl`.

Usage (from implementation/experiments):
    uv run python scripts/run_pipeline.py --dry-run
    uv run python scripts/run_pipeline.py --workers 4
    uv run python scripts/run_pipeline.py --stages s1_headline s3_final
Exit codes: 0 = every requested stage complete; 2 = incomplete (failures or
given-up points remain); 1 = refused to start (preflight or manifest).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import traceback
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = EXPERIMENTS_ROOT.parents[1]
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

import psutil  # noqa: E402
import yaml  # noqa: E402

from file_locks import FileLock, lock_is_stale, release_lock, try_lock  # noqa: E402
from scripts import run_experiment  # noqa: E402

DEFAULT_PLAN = EXPERIMENTS_ROOT / "configs" / "pipeline" / "v004.yaml"
RUNS_DIR = EXPERIMENTS_ROOT / "results" / "runs"

#: Tracked paths whose modification changes what an experiment computes.
#: Results, notes, and the paper are deliberately excluded.
CODE_PATHS = (
    "implementation/lib/src",
    "implementation/lib/pyproject.toml",
    "implementation/experiments/methods",
    "implementation/experiments/scripts",
    "implementation/experiments/configs",
    "implementation/experiments/reporting",
    "implementation/experiments/search_spaces",
    "implementation/experiments/substrates",
    "implementation/experiments/stats",
    "implementation/experiments/metrics",
    "implementation/experiments/measurement",
    "implementation/experiments/vendor/jahsbench-env/query_server.py",
    "implementation/experiments/stopping_rules.py",
    "implementation/experiments/file_locks.py",
    "implementation/experiments/pyproject.toml",
    "implementation/experiments/uv.lock",
)


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Point:
    stage: str
    method: str
    search_space: str
    budget: int
    seed: int

    @property
    def filename(self) -> str:
        return f"{self.method}__{self.search_space}__budget{self.budget}__seed{self.seed}.json"

    @property
    def key(self) -> str:
        return self.filename[: -len(".json")]


def _expand_seeds(spec: Any) -> list[int]:
    if isinstance(spec, dict):
        return list(range(int(spec["from"]), int(spec["to"]) + 1))
    return [int(s) for s in spec]


def shard_of(key: str, shards: int) -> int:
    """Stable shard index for a point key: sha256, not hash(), so it does not
    depend on the interpreter's per-process hash seed."""
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % shards


def select_shard(points: list[Point], shard: tuple[int, int] | None) -> list[Point]:
    if shard is None:
        return points
    index, shards = shard
    return [p for p in points if shard_of(p.key, shards) == index]


def parse_shard(text: str | None) -> tuple[int, int] | None:
    if text is None:
        return None
    index, _, shards = text.partition("/")
    index, shards = int(index), int(shards)
    if not 0 <= index < shards:
        raise ValueError(f"--shard {text}: index must be in 0..{shards - 1}")
    return index, shards


def stage_methods(stage: dict[str, Any]) -> list[str]:
    """A stage's methods, with nested lists (method groups referenced through
    YAML anchors) flattened and duplicates removed, order kept."""
    flat: list[str] = []

    def walk(items: Any) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item)
            elif item not in flat:
                flat.append(item)

    walk(stage.get("methods", []))
    return flat


def load_plan(path: Path) -> dict[str, Any]:
    plan = yaml.safe_load(path.read_text(encoding="utf-8"))
    names = [s["name"] for s in plan["stages"]]
    if len(names) != len(set(names)):
        raise ValueError(f"duplicate stage names in {path}")
    return plan


def expand_stage(stage: dict[str, Any]) -> list[Point]:
    if stage.get("kind", "grid") not in ("grid", "timing"):
        return []
    seeds = _expand_seeds(stage["seeds"])
    return [
        Point(stage["name"], method, space, int(budget), seed)
        for space in stage["search_spaces"]
        for method in stage_methods(stage)
        for budget in sorted(stage["budgets"])
        for seed in seeds
    ]


# ---------------------------------------------------------------------------
# Fingerprint and manifest
# ---------------------------------------------------------------------------


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True, check=True
    ).stdout


def git_fingerprint() -> dict[str, Any]:
    """Commit, whether tracked experiment code differs from it, and a hash
    of that difference (so two different dirty states never look equal)."""
    commit = _git("rev-parse", "HEAD").strip()
    status = _git("status", "--porcelain", "--", *CODE_PATHS)
    dirty_files = sorted(line[3:] for line in status.splitlines() if line.strip())
    diff_hash = None
    if dirty_files:
        diff = _git("diff", "HEAD", "--", *CODE_PATHS).encode("utf-8")
        untracked = b""
        for line in status.splitlines():
            if line.startswith("??"):
                p = REPO_ROOT / line[3:].strip()
                for f in sorted(p.rglob("*") if p.is_dir() else [p]):
                    if f.is_file() and "__pycache__" not in f.parts:
                        untracked += str(f.relative_to(REPO_ROOT)).encode() + f.read_bytes()
        diff_hash = _sha256_bytes(diff + untracked)
    return {
        "commit": commit,
        "dirty": bool(dirty_files),
        "dirty_files": dirty_files,
        "diff_hash": diff_hash,
    }


def config_hashes(
    points: Iterable[Point],
    *,
    method_path: Callable[[str], Path],
    search_space_path: Callable[[str], Path],
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for point in points:
        for label, path in (
            (f"methods/{point.method}", method_path(point.method)),
            (f"search_spaces/{point.search_space}", search_space_path(point.search_space)),
        ):
            if label not in hashes and path.exists():
                hashes[label] = _sha256_bytes(path.read_bytes())
    return dict(sorted(hashes.items()))


def build_manifest(
    *, plan_path: Path, fingerprint: dict[str, Any], hashes: dict[str, str]
) -> dict[str, Any]:
    return {
        "plan": str(plan_path.relative_to(REPO_ROOT))
        if plan_path.is_relative_to(REPO_ROOT)
        else str(plan_path),
        "plan_hash": _sha256_bytes(plan_path.read_bytes()),
        "git": fingerprint,
        "config_hashes": hashes,
        "python": sys.version.split()[0],
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
    }


def manifest_mismatches(stored: dict[str, Any], current: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if stored["plan_hash"] != current["plan_hash"]:
        problems.append("the plan file changed")
    if stored["git"]["commit"] != current["git"]["commit"]:
        problems.append(
            f"commit changed ({stored['git']['commit'][:8]} -> {current['git']['commit'][:8]})"
        )
    if stored["git"].get("diff_hash") != current["git"].get("diff_hash"):
        problems.append("uncommitted code changes differ from when this run root was started")
    for label, digest in current["config_hashes"].items():
        if label in stored["config_hashes"] and stored["config_hashes"][label] != digest:
            problems.append(f"config {label} changed")
    return problems


# ---------------------------------------------------------------------------
# Validation of persisted runs
# ---------------------------------------------------------------------------


def validate_run_file(path: Path, point: Point) -> str | None:
    """None if `path` is a complete, consistent result for `point`;
    otherwise a short reason."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"unreadable ({exc.__class__.__name__})"
    expected = {
        "method": point.method,
        "search_space": point.search_space,
        "budget": point.budget,
        "seed": point.seed,
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            return f"{field} is {payload.get(field)!r}, expected {value!r}"
    history = payload.get("history")
    used = payload.get("evaluations_used")
    if not isinstance(history, list) or not isinstance(used, int):
        return "missing history or evaluations_used"
    if len(history) != used:
        return f"history has {len(history)} entries but evaluations_used is {used}"
    if used > point.budget or used == 0:
        return f"evaluations_used {used} outside (0, {point.budget}]"
    return None


# ---------------------------------------------------------------------------
# Failure ledger
# ---------------------------------------------------------------------------


class FailureLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.refresh()

    def refresh(self) -> None:
        """Re-read attempt counts -- other workers append to the same file."""
        self.attempts: dict[str, int] = defaultdict(int)
        path = self.path
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue  # a line cut short by a crash is simply ignored
                if record.get("event") == "failure":
                    self.attempts[record["key"]] += 1
                elif record.get("event") == "reset":
                    self.attempts.pop(record["key"], None)

    def _append(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(self.path.with_name(self.path.name + ".lock")):
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    def record_failure(self, point: Point, exc: BaseException) -> None:
        self.attempts[point.key] += 1
        self._append(
            {
                "event": "failure",
                "key": point.key,
                "point": asdict(point),
                "attempt": self.attempts[point.key],
                "error": f"{exc.__class__.__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "at": dt.datetime.now().isoformat(timespec="seconds"),
            }
        )

    def reset(self, point: Point) -> None:
        if point.key in self.attempts:
            self.attempts.pop(point.key)
            self._append({"event": "reset", "key": point.key})


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


@dataclass
class StageReport:
    stage: str
    total: int
    complete: int = 0
    ran: int = 0
    failed_now: int = 0
    given_up: int = 0
    quarantined: int = 0
    busy: int = 0  # held by another worker, or waiting for a resource slot

    @property
    def done(self) -> bool:
        return self.complete == self.total


class Pipeline:
    def __init__(
        self,
        *,
        run_root: Path,
        max_retries: int = 3,
        retry_failed: bool = False,
        stop_on_error: bool = False,
        run_single: Callable[..., Any] | None = None,
        persist_run: Callable[..., Path] | None = None,
        load_method_config: Callable[[str], dict[str, Any]] | None = None,
        load_search_space_config: Callable[[str], dict[str, Any]] | None = None,
        build_substrate: Callable[[dict[str, Any]], Any] | None = None,
        log: Callable[[str], None] | None = None,
        slots: dict[str, dict[str, Any]] | None = None,
        worker: str = "main",
        raw_dir: Path | None = None,
    ) -> None:
        self.run_root = run_root
        self.raw_dir = raw_dir or run_root / "raw"
        self.lock_dir = run_root / "locks"
        self.worker = worker
        #: method -> (slot name, capacity), from the plan's parallel.slots
        self.method_slot: dict[str, tuple[str, int]] = {
            method: (name, int(spec.get("capacity", 1)))
            for name, spec in (slots or {}).items()
            for method in spec.get("methods", [])
        }
        self.quarantine_dir = run_root / "quarantine"
        self.max_retries = max_retries
        self.retry_failed = retry_failed
        self.stop_on_error = stop_on_error
        self.run_single = run_single or run_experiment.run_single
        self.persist_run = persist_run or run_experiment.persist_run
        self.load_method_config = load_method_config or run_experiment.load_method_config
        self.load_search_space_config = (
            load_search_space_config or run_experiment.load_search_space_config
        )
        self.build_substrate = build_substrate or run_experiment.build_substrate
        self.ledger = FailureLedger(run_root / "failures.jsonl")
        self._log = log or print
        self.progress_log = run_root / "logs" / "progress.log"

    def log(self, message: str) -> None:
        stamped = f"{dt.datetime.now().isoformat(timespec='seconds')} [{self.worker}] {message}"
        self._log(stamped)
        self.progress_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_log, "a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    # -- bookkeeping ------------------------------------------------------

    def remove_temp_files(self) -> int:
        if not self.raw_dir.exists():
            return 0
        removed = 0
        for tmp in self.raw_dir.glob("*.tmp"):
            tmp.unlink()
            removed += 1
        return removed

    def classify(self, points: list[Point], report: StageReport) -> list[Point]:
        """Returns points still to run; quarantines invalid files."""
        pending: list[Point] = []
        for point in points:
            path = self.raw_dir / point.filename
            if path.exists():
                reason = validate_run_file(path, point)
                if reason is None:
                    report.complete += 1
                    continue
                self.quarantine_dir.mkdir(parents=True, exist_ok=True)
                stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
                try:
                    shutil.move(str(path), str(self.quarantine_dir / f"{point.key}.{stamp}.json"))
                except FileNotFoundError:
                    pass  # another worker quarantined it first
                report.quarantined += 1
                self.log(f"QUARANTINE {point.key}: {reason}")
            if self.retry_failed:
                self.ledger.reset(point)
            if self.ledger.attempts.get(point.key, 0) >= self.max_retries:
                report.given_up += 1
                continue
            pending.append(point)
        return pending

    # -- running ----------------------------------------------------------

    def _claim(self, point: Point) -> list[Path] | None:
        """Locks for `point` (and its resource slot), or None if not now."""
        point_lock = self.lock_dir / f"{point.key}.lock"
        if not try_lock(point_lock):
            return None
        slot = self.method_slot.get(point.method)
        if slot is None:
            return [point_lock]
        name, capacity = slot
        for index in range(capacity):
            slot_lock = self.lock_dir / f"slot-{name}-{index}.lock"
            if try_lock(slot_lock):
                return [point_lock, slot_lock]
        release_lock(point_lock)
        return None

    def execute(self, point: Point, space_config: dict[str, Any], substrate: Any) -> None:
        """Run one point and persist it. Overridden by the timing stage."""
        result = self.run_single(
            self.load_method_config(point.method),
            space_config,
            point.budget,
            point.seed,
            substrate=substrate,
        )
        self.persist_run(
            result,
            method_name=point.method,
            search_space_name=point.search_space,
            budget=point.budget,
            seed=point.seed,
            out_dir=self.raw_dir,
        )

    def needs_substrate(self) -> bool:
        return True

    def run_stage(self, stage_name: str, points: list[Point]) -> StageReport:
        report = StageReport(stage=stage_name, total=len(points))
        pending = self.classify(points, report)
        self.log(
            f"STAGE {stage_name}: {report.complete}/{report.total} complete, "
            f"{len(pending)} to run, {report.given_up} given up, {report.quarantined} quarantined"
        )
        if not pending:
            return report

        by_space: dict[str, list[Point]] = defaultdict(list)
        for point in pending:
            by_space[point.search_space].append(point)

        session_start = time.monotonic()
        session_done = 0
        for space_name, space_points in by_space.items():
            space_config = self.load_search_space_config(space_name)
            substrate = None
            try:
                for point in space_points:
                    locks = self._claim(point)
                    if locks is None:
                        report.busy += 1
                        continue
                    try:
                        path = self.raw_dir / point.filename
                        if path.exists() and validate_run_file(path, point) is None:
                            report.complete += 1  # finished by another worker meanwhile
                            continue
                        self.ledger.refresh()
                        if self.ledger.attempts.get(point.key, 0) >= self.max_retries:
                            report.given_up += 1
                            continue
                        started = time.monotonic()
                        try:
                            if substrate is None and self.needs_substrate():
                                substrate = self.build_substrate(space_config)
                            self.execute(point, space_config, substrate)
                        except KeyboardInterrupt:
                            raise
                        except Exception as exc:  # noqa: BLE001 -- every failure is recorded, not hidden
                            self.ledger.record_failure(point, exc)
                            report.failed_now += 1
                            self.log(
                                f"FAIL {point.key} (attempt {self.ledger.attempts[point.key]}/"
                                f"{self.max_retries}): {exc.__class__.__name__}: {exc}"
                            )
                            _close(substrate)
                            substrate = None  # rebuilt before the next point
                            if self.stop_on_error:
                                raise
                            continue
                    finally:
                        for lock in reversed(locks):
                            release_lock(lock)
                    report.complete += 1
                    report.ran += 1
                    session_done += 1
                    elapsed = time.monotonic() - session_start
                    remaining = len(pending) - session_done - report.failed_now - report.busy
                    eta = elapsed / session_done * max(remaining, 0)
                    self.log(
                        f"OK {stage_name} {report.complete}/{report.total} {point.key} "
                        f"{time.monotonic() - started:.1f}s eta {_format_duration(eta)}"
                    )
            finally:
                _close(substrate)
        return report


class TimingPipeline(Pipeline):
    """Timing stage: every point in a fresh `run_experiment.py` process, one
    at a time, so wall-clock time and peak memory belong to that run alone."""

    def __init__(self, *, env: dict[str, str], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.env = env

    def needs_substrate(self) -> bool:
        return False

    def execute(self, point: Point, space_config: dict[str, Any], substrate: Any) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.run_experiment",
                "--method",
                point.method,
                "--search-space",
                point.search_space,
                "--budget",
                str(point.budget),
                "--seed",
                str(point.seed),
                "--out-dir",
                str(self.raw_dir),
            ],
            cwd=EXPERIMENTS_ROOT,
            env=self.env,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            tail = "\n".join((proc.stderr or proc.stdout).strip().splitlines()[-5:])
            raise RuntimeError(f"run_experiment.py exited with {proc.returncode}: {tail}")


def _close(substrate: Any) -> None:
    close = getattr(substrate, "close", None)
    if callable(close):
        try:
            close()
        except Exception:  # noqa: BLE001 -- closing a broken bridge must not mask the real error
            pass


def _format_duration(seconds: float) -> str:
    seconds = int(seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}h{minutes:02d}m" if hours else f"{minutes}m{secs:02d}s"


# ---------------------------------------------------------------------------
# Preflight and checks stage
# ---------------------------------------------------------------------------


def preflight(points: Iterable[Point]) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for point in points:
        m = f"methods/{point.method}"
        if m not in seen:
            seen.add(m)
            path = run_experiment.CONFIGS_DIR / "methods" / f"{point.method}.yaml"
            if not path.exists():
                problems.append(f"missing config {path.relative_to(EXPERIMENTS_ROOT)}")
            elif run_experiment.load_method_config(point.method).get("not_yet_implemented", False):
                problems.append(f"config {point.method} is marked not_yet_implemented")
        s = f"search_spaces/{point.search_space}"
        if s not in seen:
            seen.add(s)
            path = run_experiment.CONFIGS_DIR / "search_spaces" / f"{point.search_space}.yaml"
            if not path.exists():
                problems.append(f"missing config {path.relative_to(EXPERIMENTS_ROOT)}")
    return problems


def run_checks(
    stage: dict[str, Any],
    plan_points: list[Point],
    run_root: Path,
    fingerprint: dict[str, Any],
    pipeline: Pipeline,
) -> bool:
    marker = run_root / "checks.json"
    if marker.exists():
        stored = json.loads(marker.read_text(encoding="utf-8"))
        if stored.get("passed") and stored.get("git") == fingerprint:
            pipeline.log("CHECKS already passed for this code state -- skipped")
            return True

    results: dict[str, Any] = {"git": fingerprint, "suites": {}, "determinism": {}}
    lib_root = EXPERIMENTS_ROOT.parent / "lib"
    env = dict(os.environ, PYTHONPATH=str(lib_root / "src"))
    for name, cwd in (("lib", lib_root), ("experiments", EXPERIMENTS_ROOT)):
        pipeline.log(f"CHECKS running {name} test suite")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"], cwd=cwd, env=env, capture_output=True, text=True
        )
        tail = proc.stdout.strip().splitlines()[-1:] if proc.stdout else []
        results["suites"][name] = {"returncode": proc.returncode, "summary": tail}
        pipeline.log(f"CHECKS {name}: {'passed' if proc.returncode == 0 else 'FAILED'} {tail}")

    spec = stage["determinism"]
    space_config = run_experiment.load_search_space_config(spec["search_space"])
    substrate = run_experiment.build_substrate(space_config)
    try:
        for method in sorted({p.method for p in plan_points}):
            config = run_experiment.load_method_config(method)
            histories = []
            for _ in range(2):
                r = run_experiment.run_single(
                    config, space_config, spec["budget"], spec["seed"], substrate=substrate
                )
                histories.append(
                    json.dumps([run_experiment._observation_to_dict(o) for o in r.state.history])
                )
            same = histories[0] == histories[1]
            results["determinism"][method] = same
            pipeline.log(f"CHECKS determinism {method}: {'identical' if same else 'DIFFERS'}")
    finally:
        _close(substrate)

    passed = all(s["returncode"] == 0 for s in results["suites"].values()) and all(
        results["determinism"].values()
    )
    results["passed"] = passed
    marker.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return passed


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


def worker_env(
    threads: int, run_root: Path, jahs_max_datasets: int = 1, jahs_parallel: int = 4
) -> dict[str, str]:
    env = dict(os.environ)
    # One JAHS-Bench-201 bridge for the whole machine, shared by every worker:
    # a loaded dataset holds about 12 GB, so a bridge per worker exhausts a
    # 30 GB machine at three workers (substrates/jahs_bench_201.py).
    server_dir = run_root / "jahs"
    server_dir.mkdir(parents=True, exist_ok=True)
    env["P3NET_JAHS_SERVER_DIR"] = str(server_dir)
    env["P3NET_JAHS_MAX_DATASETS"] = str(jahs_max_datasets)
    env["P3NET_JAHS_PARALLEL"] = str(jahs_parallel)
    env["P3NET_JAHS_LOAD_LOCK"] = str(run_root / "locks" / "jahs-bridge-load.lock")
    for name in THREAD_VARIABLES:
        env[name] = str(threads)
    env["PYTHONUNBUFFERED"] = "1"
    return env


def shutdown_jahs_server(run_root: Path, log: Callable[[str], None]) -> None:
    """Ask the shared JAHS bridge to exit, freeing its ~12 GB.

    Best effort: it also exits by itself once idle, and a bridge that is
    already gone is not an error."""
    port_file = run_root / "jahs" / "jahs-server.port"
    try:
        port = int(port_file.read_text(encoding="utf-8").splitlines()[0])
    except (OSError, ValueError, IndexError):
        return
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=30) as connection:
            connection.sendall(b'{"command": "shutdown"}\n')
            connection.recv(1024)
    except OSError as exc:
        log(f"shared JAHS bridge did not acknowledge shutdown: {exc}")
        return
    log("shared JAHS bridge shut down")


def remove_stale_locks(lock_dir: Path, unlock_after_hours: float | None = None) -> int:
    """Break locks whose owning process no longer exists on this host, and --
    if `unlock_after_hours` is given -- any lock older than that, whatever host
    holds it (for a shared directory, where this host cannot see the other
    machine's processes)."""
    removed = 0
    if not lock_dir.exists():
        return 0
    for lock in lock_dir.glob("*.lock"):
        too_old = (
            unlock_after_hours is not None
            and time.time() - lock.stat().st_mtime > unlock_after_hours * 3600
        )
        if too_old or lock_is_stale(lock, grace_seconds=0.0):
            release_lock(lock)
            removed += 1
    return removed


def status_line(run_root: Path, stages: list[dict[str, Any]], shard) -> str:
    """One-line progress summary from the files and locks on disk: cheap
    enough (one directory listing) to print every few minutes."""
    raw = run_root / "raw"
    present = {p.name for p in raw.glob("*.json")} if raw.exists() else set()
    parts = []
    for stage in stages:
        points = select_shard(expand_stage(stage), shard)
        if not points:
            continue
        done = sum(1 for point in points if point.filename in present)
        if done < len(points):
            parts.append(f"{stage['name']} {done}/{len(points)}")
        if len(parts) >= 3:
            break
    running = []
    lock_dir = run_root / "locks"
    if lock_dir.exists():
        for lock in sorted(lock_dir.glob("*.lock")):
            if lock.name.startswith("slot-") or lock.name.startswith("jahs-"):
                continue
            minutes = (time.time() - lock.stat().st_mtime) / 60
            running.append(f"{lock.stem.split('__')[0]} {minutes:.0f}m")
    memory = psutil.virtual_memory()
    return (
        f"STATUS {', '.join(parts) or 'all stages complete'} | running: "
        f"{', '.join(running) or 'none'} | RAM free {memory.available / 2**30:.1f} GB"
    )


def spawn_workers(
    *,
    n: int,
    args: argparse.Namespace,
    run_root: Path,
    stages: list[str],
    env: dict[str, str],
    log: Callable[[str], None],
    status: Callable[[], str] | None = None,
    status_every: float = 600.0,
) -> list[int]:
    """Start `n` worker processes on the grid stages and wait for all of
    them. A worker that dies (not a clean exit) is restarted, up to
    --max-worker-restarts times each. Returns the workers' final exit codes."""
    (run_root / "logs").mkdir(parents=True, exist_ok=True)
    base = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--plan",
        str(args.plan),
        "--run-root",
        str(run_root),
        "--max-retries",
        str(args.max_retries),
        "--stages",
        *stages,
    ]
    if args.stop_on_error:
        base.append("--stop-on-error")
    if args.shard:
        base += ["--shard", args.shard]

    def start(i: int) -> tuple[subprocess.Popen, Any]:
        handle = open(run_root / "logs" / f"worker-{i}.log", "a", encoding="utf-8")
        proc = subprocess.Popen(
            [*base, "--worker-name", f"w{i}"],
            cwd=EXPERIMENTS_ROOT,
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
        )
        log(f"WORKER w{i} started (pid {proc.pid})")
        return proc, handle

    running = {i: start(i) for i in range(n)}
    restarts = defaultdict(int)
    codes: dict[int, int] = {}
    next_status = time.monotonic() + status_every
    try:
        while running:
            time.sleep(2.0)
            if status is not None and time.monotonic() >= next_status:
                next_status = time.monotonic() + status_every
                log(status())
            for i, (proc, handle) in list(running.items()):
                code = proc.poll()
                if code is None:
                    continue
                handle.close()
                del running[i]
                if code in (0, 2) or restarts[i] >= args.max_worker_restarts:
                    codes[i] = code
                    log(f"WORKER w{i} exited with {code}")
                    continue
                restarts[i] += 1
                log(f"WORKER w{i} died with {code}; restarting ({restarts[i]})")
                running[i] = start(i)
    except KeyboardInterrupt:
        for proc, handle in running.values():
            proc.terminate()
        for proc, handle in running.values():
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
            handle.close()
        raise
    return [codes[i] for i in sorted(codes)]


def run_worker(args: argparse.Namespace, plan: dict[str, Any], stages: list[dict[str, Any]]) -> int:
    """Worker mode: grid stages only, repeated until nothing is left that
    this worker could run. The parent has already validated the manifest."""
    run_root = args.run_root
    if not (run_root / "manifest.json").exists():
        print(f"worker: {run_root / 'manifest.json'} missing -- start through the parent process")
        return 1
    parallel = plan.get("parallel", {})
    try:
        import torch

        torch.set_num_threads(int(parallel.get("threads_per_run", 2)))
    except ImportError:
        pass
    pipeline = Pipeline(
        run_root=run_root,
        max_retries=args.max_retries,
        stop_on_error=args.stop_on_error,
        slots=parallel.get("slots"),
        worker=args.worker_name,
    )
    grid = [s for s in stages if s.get("kind", "grid") == "grid"]
    shard = parse_shard(args.shard)
    try:
        while True:
            ran = busy = failed = 0
            for s in grid:
                report = pipeline.run_stage(s["name"], select_shard(expand_stage(s), shard))
                ran += report.ran
                busy += report.busy
                failed += report.failed_now
            if ran == 0 and failed == 0:
                if busy == 0:
                    return 0
                time.sleep(30.0)  # everything left is held by other workers or a slot
    except KeyboardInterrupt:
        return 2


def stage_reports(
    pipeline: Pipeline,
    stages: list[dict[str, Any]],
    shard: tuple[int, int] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Completion of each stage from the files on disk, without running."""
    status: dict[str, Any] = {}
    incomplete = False
    for s in stages:
        points = select_shard(expand_stage(s), shard)
        report = StageReport(stage=s["name"], total=len(points))
        for point in points:
            path = pipeline.raw_dir / point.filename
            if path.exists() and validate_run_file(path, point) is None:
                report.complete += 1
            elif pipeline.ledger.attempts.get(point.key, 0) >= pipeline.max_retries:
                report.given_up += 1
        status[s["name"]] = asdict(report) | {"done": report.done}
        incomplete |= not report.done
    return status, incomplete


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument(
        "--run-root", type=Path, default=None, help="default: results/runs/<short commit>[-dirty]"
    )
    parser.add_argument(
        "--stages", nargs="*", default=None, help="default: every stage, in plan order"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="report counts and preflight, run nothing"
    )
    parser.add_argument(
        "--allow-dirty", action="store_true", help="allow uncommitted changes to experiment code"
    )
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument(
        "--retry-failed", action="store_true", help="reset attempt counts of failed points"
    )
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument(
        "--skip-checks", action="store_true", help="skip the checks stage (not for final runs)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="worker processes (default: plan's parallel.workers, else 1)",
    )
    parser.add_argument(
        "--max-worker-restarts",
        type=int,
        default=20,
        help="restarts per worker before it is given up (a worker killed by the "
        "out-of-memory killer should be restarted, not abandoned)",
    )
    parser.add_argument(
        "--shard", default=None, help="run only shard i of N points, e.g. 0/4 (see --help)"
    )
    parser.add_argument(
        "--unlock-after",
        type=float,
        default=None,
        metavar="HOURS",
        help="also break locks older than HOURS, whatever host holds them "
        "(shared run root, after a crash on another machine)",
    )
    parser.add_argument(
        "--status-every",
        type=float,
        default=600.0,
        metavar="SECONDS",
        help="how often to print a progress summary while workers run (0 = never)",
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--worker-name", default="main", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    plan = load_plan(args.plan)
    stages = [s for s in plan["stages"] if args.stages is None or s["name"] in args.stages]
    unknown = set(args.stages or []) - {s["name"] for s in plan["stages"]}
    if unknown:
        print(f"unknown stage(s): {', '.join(sorted(unknown))}")
        return 1
    if args.worker:
        return run_worker(args, plan, stages)
    shard = parse_shard(args.shard)
    grid_points = [p for s in stages for p in select_shard(expand_stage(s), shard)]
    all_plan_points = [p for s in plan["stages"] for p in expand_stage(s)]
    parallel = plan.get("parallel", {})
    workers = args.workers or int(parallel.get("workers", 1))
    threads = int(parallel.get("threads_per_run", 2))
    jahs_max_datasets = int(parallel.get("jahs_max_datasets", 1))
    # One handler per worker: the bridge must not become the bottleneck.
    jahs_parallel = int(parallel.get("jahs_parallel", 0)) or workers

    fingerprint = git_fingerprint()
    short = fingerprint["commit"][:8] + ("-dirty" if fingerprint["dirty"] else "")
    run_root = args.run_root or (RUNS_DIR / short)

    print(
        f"plan {plan['name']}: {len(stages)} stage(s), {len(grid_points)} point(s), "
        f"{workers} worker(s), {threads} thread(s) per run"
        + (f", shard {args.shard}" if shard else "")
    )
    for s in stages:
        n = len(select_shard(expand_stage(s), shard))
        print(f"  {s['name']:22} {s.get('kind', 'grid'):6} {n:6} point(s)")
    print(
        f"commit {fingerprint['commit'][:12]}{' (DIRTY)' if fingerprint['dirty'] else ''} -> run root {run_root}"  # noqa: E501
    )

    problems = preflight(
        all_plan_points if any(s.get("kind") == "checks" for s in stages) else grid_points
    )
    if problems:
        print(
            f"\npreflight: {len(problems)} problem(s){'' if args.dry_run else ' -- refusing to start'}:"  # noqa: E501
        )
        for p in problems:
            print(f"  - {p}")
        if not args.dry_run:
            return 1
    if fingerprint["dirty"] and not args.allow_dirty and not args.dry_run:
        print(
            "\nexperiment code has uncommitted changes -- commit first, or pass --allow-dirty for a non-final run:"  # noqa: E501
        )
        for f in fingerprint["dirty_files"][:20]:
            print(f"  {f}")
        return 1

    hashes = config_hashes(
        all_plan_points,
        method_path=lambda m: run_experiment.CONFIGS_DIR / "methods" / f"{m}.yaml",
        search_space_path=lambda s: run_experiment.CONFIGS_DIR / "search_spaces" / f"{s}.yaml",
    )
    current = build_manifest(plan_path=args.plan, fingerprint=fingerprint, hashes=hashes)
    manifest_path = run_root / "manifest.json"
    if manifest_path.exists():
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
        mismatches = manifest_mismatches(stored, current)
        if mismatches:
            print(
                f"\n{manifest_path} was started with different code or configs -- refusing to resume:"  # noqa: E501
            )
            for m in mismatches:
                print(f"  - {m}")
            print("Start a new run root (--run-root) instead of mixing versions.")
            return 1
        print("resuming existing run root (manifest matches)")
    elif not args.dry_run:
        run_root.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

    pipeline = Pipeline(
        run_root=run_root,
        max_retries=args.max_retries,
        retry_failed=args.retry_failed,
        stop_on_error=args.stop_on_error,
        slots=parallel.get("slots"),
    )

    if args.dry_run:
        print("\ncompletion in this run root:")
        for s in stages:
            pts = select_shard(expand_stage(s), shard)
            if not pts:
                continue
            directory = (
                run_root / "timing" / "raw" if s.get("kind") == "timing" else pipeline.raw_dir
            )
            done = sum(
                1
                for p in pts
                if (directory / p.filename).exists()
                and validate_run_file(directory / p.filename, p) is None
            )
            print(f"  {s['name']:22} {done}/{len(pts)} complete")
        if fingerprint["dirty"] and not args.allow_dirty:
            print(
                "\nnote: experiment code has uncommitted changes; a real run will refuse to start"
            )
        return 0

    removed = pipeline.remove_temp_files()
    if removed:
        pipeline.log(f"removed {removed} leftover .tmp file(s) from an interrupted write")
    stale = remove_stale_locks(run_root / "locks", args.unlock_after)
    if stale:
        pipeline.log(f"removed {stale} lock(s) left by processes that no longer exist")

    from measurement.hardware import manifest as hardware_manifest

    with open(run_root / "sessions.jsonl", "a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "argv": sys.argv[1:],
                    "workers": workers,
                    "threads_per_run": threads,
                    "hardware": hardware_manifest(),
                }
            )
            + "\n"
        )

    if args.retry_failed:
        for point in grid_points:
            pipeline.ledger.reset(point)

    grid_stages = [s for s in stages if s.get("kind", "grid") == "grid"]
    timing_stages = [s for s in stages if s.get("kind") == "timing"]
    try:
        for s in stages:
            if s.get("kind") == "checks":
                if args.skip_checks:
                    pipeline.log("CHECKS skipped by --skip-checks")
                    continue
                if not run_checks(s, all_plan_points, run_root, fingerprint, pipeline):
                    pipeline.log("CHECKS FAILED -- see checks.json; not running experiment stages")
                    return 1
        if grid_stages:
            spawn_workers(
                n=workers,
                args=args,
                run_root=run_root,
                stages=[s["name"] for s in grid_stages],
                env=worker_env(threads, run_root, jahs_max_datasets, jahs_parallel),
                log=pipeline.log,
                status=(
                    None
                    if args.status_every <= 0
                    else lambda: status_line(run_root, grid_stages, shard)
                ),
                status_every=args.status_every,
            )
        pipeline.ledger.refresh()
        status, incomplete = stage_reports(pipeline, grid_stages, shard)
        for s in timing_stages:
            timing = TimingPipeline(
                run_root=run_root,
                raw_dir=run_root / "timing" / "raw",
                max_retries=args.max_retries,
                env=worker_env(threads, run_root, jahs_max_datasets, jahs_parallel),
                worker="timing",
            )
            report = timing.run_stage(s["name"], select_shard(expand_stage(s), shard))
            status[s["name"]] = asdict(report) | {"done": report.done}
            incomplete |= not report.done
        shutdown_jahs_server(run_root, pipeline.log)
        status_path = run_root / "stage_status.json"
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
        for name, st in status.items():
            if not st["done"]:
                pipeline.log(
                    f"STAGE {name} incomplete: {st['total'] - st['complete']} point(s) remain "
                    f"({st['given_up']} given up after {args.max_retries} attempts)"
                )
    except KeyboardInterrupt:
        pipeline.log(
            "INTERRUPTED -- every completed run is saved; rerun the same command to resume"
        )
        return 2

    pipeline.log(
        "ALL REQUESTED STAGES COMPLETE" if not incomplete else "FINISHED WITH INCOMPLETE STAGES"
    )
    return 2 if incomplete else 0


#: Exit code for an unexpected crash of the orchestrator itself. Distinct from
#: 1 (refused to start), so scripts/run_pipeline.ps1 knows a restart can help.
EXIT_CRASH = 3


if __name__ == "__main__":
    try:
        code = main()
    except KeyboardInterrupt:
        code = 2
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        code = EXIT_CRASH
    sys.exit(code)
