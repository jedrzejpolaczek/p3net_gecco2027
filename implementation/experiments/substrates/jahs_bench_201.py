"""JAHS-Bench-201 adapter (primary benchmark, Category 2: continuous
surrogate, no enumerable oracle front).

Real, live-queried via a subprocess bridge to vendor/jahsbench-env/ -- a
dedicated Python 3.10 environment, since jahs-bench cannot install in
this project's main Python 3.13 environment (hard-pins
scikit-learn<1.1.0, which has no wheel for Python >=3.11 and can't build
from source since Python 3.12 removed distutils). The bridge
(vendor/jahsbench-env/query_server.py) is a persistent, long-lived
subprocess rather than one spawned per query -- reloading the several-GB
XGBoost surrogate models on every single evaluation would be
impractically slow for even a 50-evaluation budget.

Uses search_spaces/nas_genotype.py's existing genotype UNCHANGED --
unlike NAS-HPO-Bench-II, JAHS-Bench-201's real ConfigSpace (verified by
reading jahs_bench.lib.core.configspace directly, not guessed) matches
what that module already assumed: 5 cell operations (via the package's
own nb201_to_ops translation table), LearningRate/WeightDecay bounds
matching our discretisation grids exactly (1e-3 to 1, and 1e-5 to 1e-2,
both log-scaled), TrivialAugment {True, False}, and the same three
Activation choices (modulo capitalisation, handled in
query_server.py). "Optimizer" exists in the real ConfigSpace but has
only one possible value ("SGD") -- not a real search dimension,
consistent with the paper's "ten dimensions" (not eleven).

Deviation from Substrate's general contract, documented rather than
silently ignored (same situation as substrates/nas_hpo_bench_ii.py):
analytic_f2 is not actually computable independently of query_f1 for
this benchmark either -- one call to the surrogate returns every metric
(accuracy, size, FLOPS, latency, ...) together. Both methods share one
per-(genotype, epoch) query cache.
"""

from __future__ import annotations

import contextlib
import json
import os
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from p3net.problem.genotype import Genotype

from file_locks import FileLock
from search_spaces.nas_genotype import decode_nas_genotype
from substrates.base import FidelityLevel, Substrate

JAHS_DATASETS: tuple[str, ...] = ("cifar10", "colorectal_histology", "fashion_mnist")

_EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
_VENDOR_ENV = _EXPERIMENTS_ROOT / "vendor" / "jahsbench-env"
_BRIDGE_VENV = _VENDOR_ENV / ".venv"
BRIDGE_PYTHON = (
    _BRIDGE_VENV / "Scripts" / "python.exe" if os.name == "nt" else _BRIDGE_VENV / "bin" / "python"
)
BRIDGE_SCRIPT = _VENDOR_ENV / "query_server.py"
DEFAULT_DATA_DIR = _EXPERIMENTS_ROOT / "data" / "cache" / "jahs_bench_201"
#: If set, path of a lock file held while a bridge starts and loads its models
#: (set by scripts/run_pipeline.py for its workers). Only used without a
#: shared bridge.
LOAD_LOCK_ENV = "P3NET_JAHS_LOAD_LOCK"
#: If set, directory holding the shared bridge's port and lock files: every
#: process on this machine then talks to ONE bridge over a local socket
#: instead of starting its own (scripts/run_pipeline.py sets it for workers).
#:
#: One loaded dataset costs about 12 GB resident, so a bridge per worker
#: exhausts a 30 GB machine at three workers; shared, the cost is per
#: dataset. SERVER_MAX_DATASETS_ENV bounds how many stay loaded at once.
SERVER_DIR_ENV = "P3NET_JAHS_SERVER_DIR"
SERVER_MAX_DATASETS_ENV = "P3NET_JAHS_MAX_DATASETS"
#: How many handler processes the shared bridge forks after loading (they
#: share the models copy-on-write, so this costs almost no extra memory).
#: One handler makes the bridge the throughput limit of the whole machine.
SERVER_PARALLEL_ENV = "P3NET_JAHS_PARALLEL"
#: A bridge that has loaded nothing for this long exits and frees its memory.
SERVER_IDLE_TIMEOUT = 3600.0
#: Loading a dataset takes minutes; a worker waits this long for a bridge
#: that another worker is starting.
SERVER_START_TIMEOUT = 1800.0


@dataclass
class JAHSBench201Substrate(Substrate):
    """Adapter for JAHS-Bench-201 -- ten joint search dimensions (six
    architecture edges + four hyperparameters) across three datasets, plus
    further fidelity dimensions (epochs, resolution, cell depth/width)
    tracked separately from the searched genotype. No enumerable oracle
    front exists for this benchmark (Category 2) -- do not compute IGD+
    against it; p3net.metrics.hypervolume's best-known-front fallback
    applies instead."""

    dataset: str = "cifar10"
    data_dir: str | Path = DEFAULT_DATA_DIR
    _process: Any = field(default=None, init=False, repr=False)
    _stderr: Any = field(default=None, init=False, repr=False)
    _socket: Any = field(default=None, init=False, repr=False)
    _stream: Any = field(default=None, init=False, repr=False)
    _query_cache: dict[tuple[Genotype, int], dict[str, float]] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        if self.dataset not in JAHS_DATASETS:
            raise ValueError(
                f"unknown JAHS-Bench-201 dataset {self.dataset!r}, expected one of {JAHS_DATASETS}"
            )

    def fidelity_ladder(self) -> tuple[FidelityLevel, ...]:
        return (FidelityLevel(rank=0, config={"epochs": 200, "resolution": 1.0}),)

    def _ensure_process(self) -> subprocess.Popen:
        if self._process is None or self._process.poll() is not None:
            if not BRIDGE_PYTHON.exists():
                raise RuntimeError(
                    f"jahs-bench bridge environment not found at {BRIDGE_PYTHON} -- "
                    "build it with scripts/bootstrap_env.sh (Linux/macOS) or the "
                    "steps in implementation/README.md (Windows)."
                )
            # stderr goes to a temporary file, not a pipe: nothing reads the
            # bridge's stderr while it runs, and a full pipe buffer (warnings
            # over weeks of queries) would block the bridge and hang the run.
            self._stderr = tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace")
            self._process = subprocess.Popen(
                [str(BRIDGE_PYTHON), str(BRIDGE_SCRIPT), str(self.data_dir)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self._stderr,
                text=True,
                bufsize=1,
            )
        return self._process

    @staticmethod
    def _read_response(process: subprocess.Popen, max_skipped: int = 100) -> tuple[str, int]:
        """The bridge's next JSON response, skipping anything else it printed.

        The bridge sends library output to stderr, but a dependency that writes
        to file descriptor 1 directly would still land between responses; such
        a line is skipped rather than parsed as a result. Returns the line
        (empty if the bridge died) and how many lines were skipped."""
        skipped = 0
        while skipped <= max_skipped:
            line = process.stdout.readline()
            if not line:
                return "", skipped
            stripped = line.strip()
            if stripped.startswith("{"):
                return stripped, skipped
            skipped += 1
        raise RuntimeError(
            f"jahs-bench bridge printed {skipped} lines that are not responses; "
            f"last one: {line.strip()[:200]!r}"
        )

    # -- shared bridge (SERVER_DIR_ENV) ------------------------------------

    @staticmethod
    def _server_files(directory: Path) -> tuple[Path, Path, Path]:
        return (
            directory / "jahs-server.port",
            directory / "jahs-server.lock",
            directory / "jahs-server.log",
        )

    @staticmethod
    def _connect(port_file: Path) -> Any:
        """A connected socket, or None if no bridge is listening."""
        try:
            port = int(port_file.read_text(encoding="utf-8").splitlines()[0])
        except (OSError, ValueError, IndexError):
            return None
        try:
            connection = socket.create_connection(("127.0.0.1", port), timeout=SERVER_START_TIMEOUT)
        except OSError:
            return None
        return connection

    def _start_server(self, directory: Path) -> None:
        """Start the shared bridge, unless another process just did.

        Holds the lock for the whole start so two workers never load the
        models at once (12 GB each)."""
        port_file, lock_file, log_file = self._server_files(directory)
        # The lock is held across the whole model load (minutes), so the
        # deadline has to cover it -- but it must exist: a lock outliving its
        # holder would otherwise stall every worker on the machine silently.
        with FileLock(lock_file, timeout_seconds=SERVER_START_TIMEOUT * 2):
            if self._connect(port_file) is not None:
                return
            port_file.unlink(missing_ok=True)
            with open(log_file, "a", encoding="utf-8") as log:
                server = subprocess.Popen(
                    [
                        str(BRIDGE_PYTHON),
                        str(BRIDGE_SCRIPT),
                        str(self.data_dir),
                        "--serve",
                        str(port_file),
                        "--max-datasets",
                        os.environ.get(SERVER_MAX_DATASETS_ENV, "2"),
                        "--idle-timeout",
                        str(SERVER_IDLE_TIMEOUT),
                        "--parallel",
                        os.environ.get(SERVER_PARALLEL_ENV, "4"),
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=log,
                    start_new_session=True,
                )
            deadline = time.monotonic() + SERVER_START_TIMEOUT
            while time.monotonic() < deadline:
                connection = self._connect(port_file)
                if connection is not None:
                    connection.close()
                    return
                if server.poll() is not None:
                    # Failing fast matters: otherwise every worker waits out
                    # the full start timeout before reporting the same error.
                    raise RuntimeError(
                        f"shared jahs-bench bridge exited with {server.returncode} "
                        f"while starting -- see {log_file}"
                    )
                time.sleep(0.5)
            raise RuntimeError(
                f"shared jahs-bench bridge did not start within "
                f"{SERVER_START_TIMEOUT:.0f}s -- see {log_file}"
            )

    def _ensure_stream(self, directory: Path) -> Any:
        if self._stream is not None:
            return self._stream
        port_file, _, _ = self._server_files(directory)
        connection = self._connect(port_file)
        if connection is None:
            self._start_server(directory)
            connection = self._connect(port_file)
        if connection is None:
            raise RuntimeError("cannot reach the shared jahs-bench bridge")
        self._socket = connection
        self._stream = connection.makefile("rw", encoding="utf-8", newline="\n")
        return self._stream

    def _shared_response(self, request: dict, directory: Path) -> dict[str, float]:
        stream = self._ensure_stream(directory)
        try:
            stream.write(json.dumps(request) + "\n")
            stream.flush()
            line = stream.readline()
        except OSError as exc:
            self._close_stream()
            raise RuntimeError(f"shared jahs-bench bridge connection failed: {exc}") from exc
        if not line:
            self._close_stream()
            raise RuntimeError(
                "shared jahs-bench bridge closed the connection -- see "
                f"{self._server_files(directory)[2]}"
            )
        return json.loads(line)

    def _close_stream(self) -> None:
        for handle in (self._stream, self._socket):
            if handle is not None:
                try:
                    handle.close()
                except OSError:
                    pass
        self._stream = self._socket = None

    def _response(self, genotype: Genotype, epochs: int) -> dict[str, float]:
        cache_key = (genotype, epochs)
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        config = decode_nas_genotype(genotype)
        request = {
            "edges": list(config.edges),
            "learning_rate": config.learning_rate,
            "weight_decay": config.weight_decay,
            "activation": config.activation,
            "trivial_augment": config.trivial_augment,
            "dataset": self.dataset,
            "epochs": epochs,
        }
        server_dir = os.environ.get(SERVER_DIR_ENV)
        if server_dir:
            # One bridge for the whole machine (SERVER_DIR_ENV's docstring).
            response = self._shared_response(request, Path(server_dir))
        else:
            # Own bridge: it loads the surrogate models on the first query,
            # about 12 GB resident per dataset, so with several workers only
            # one bridge may load at a time.
            starting = self._process is None or self._process.poll() is not None
            lock_path = os.environ.get(LOAD_LOCK_ENV) if starting else None
            with FileLock(Path(lock_path)) if lock_path else contextlib.nullcontext():
                process = self._ensure_process()
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()
                line, skipped = self._read_response(process)
            if not line:
                stderr = ""
                if self._stderr is not None:
                    self._stderr.seek(0)
                    stderr = self._stderr.read()[-4000:]
                raise RuntimeError(
                    f"jahs-bench bridge process died (ignored {skipped} "
                    f"non-response line(s)): {stderr}"
                )
            response = json.loads(line)
        if "error" in response:
            raise RuntimeError(f"jahs-bench bridge query failed: {response['error']}")
        self._query_cache[cache_key] = response
        return response

    def _query(self, genotype: Genotype, fidelity: FidelityLevel) -> tuple[float, float]:
        response = self._response(genotype, fidelity.config.get("epochs", 200))
        error_rate = 100.0 - response["valid_acc"]
        return error_rate, response["size_mb"]

    def query_f1(self, genotype: Genotype, fidelity: FidelityLevel) -> float:
        error_rate, _ = self._query(genotype, fidelity)
        return error_rate

    def analytic_f2(self, genotype: Genotype) -> float:
        _, size_mb = self._query(genotype, self.fidelity_ladder()[-1])
        return size_mb

    def training_seconds(self, genotype: Genotype, epochs: int) -> float:
        """The benchmark's cumulative `runtime` up to `epochs`."""
        return float(self._response(genotype, epochs)["runtime"])

    def full_fidelity_metrics(self, genotype: Genotype) -> dict[str, float]:
        response = self._response(genotype, self.max_epochs())
        return {
            "train_acc": float(response["train_acc"]),
            "valid_acc": float(response["valid_acc"]),
            "test_acc": float(response["test_acc"]),
            "training_seconds": float(response["runtime"]),
        }

    def close(self) -> None:
        """Not called automatically -- callers that construct many
        short-lived substrates in one process (e.g. a test suite) should
        call this explicitly rather than leaking bridge processes.

        A shared bridge is left running for the other workers; only this
        substrate's connection to it is closed."""
        self._close_stream()
        if self._process is not None:
            self._process.stdin.close()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
        if self._stderr is not None:
            self._stderr.close()
            self._stderr = None
