"""JAHS-Bench-201 adapter (primary benchmark, Category 2: continuous
surrogate, no enumerable oracle front).

Real, live-queried via a subprocess bridge to vendor/jahsbench-env/ -- a
dedicated Python 3.10 environment, since jahs-bench cannot install in
this project's main Python 3.13 environment (hard-pins
scikit-learn<1.1.0, which has no wheel for Python >=3.11 and can't build
from source since Python 3.12 removed distutils; see ../TASKS.md). The
bridge (vendor/jahsbench-env/query_server.py) is a persistent, long-lived
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

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from p3net.problem.genotype import Genotype

from search_spaces.nas_genotype import decode_nas_genotype
from substrates.base import FidelityLevel, Substrate

JAHS_DATASETS: tuple[str, ...] = ("cifar10", "colorectal_histology", "fashion_mnist")

_EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
_VENDOR_ENV = _EXPERIMENTS_ROOT / "vendor" / "jahsbench-env"
BRIDGE_PYTHON = _VENDOR_ENV / ".venv" / "Scripts" / "python.exe"
BRIDGE_SCRIPT = _VENDOR_ENV / "query_server.py"
DEFAULT_DATA_DIR = _EXPERIMENTS_ROOT / "data" / "cache" / "jahs_bench_201"


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
    _query_cache: dict[tuple[Genotype, int], tuple[float, float]] = field(
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
                    "see ../TASKS.md for how it was built (vendor/jahsbench-env)."
                )
            self._process = subprocess.Popen(
                [str(BRIDGE_PYTHON), str(BRIDGE_SCRIPT), str(self.data_dir)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        return self._process

    def _query(self, genotype: Genotype, fidelity: FidelityLevel) -> tuple[float, float]:
        epochs = fidelity.config.get("epochs", 200)
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
        process = self._ensure_process()
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        line = process.stdout.readline()
        if not line:
            stderr = process.stderr.read()
            raise RuntimeError(f"jahs-bench bridge process died: {stderr}")
        response = json.loads(line)
        if "error" in response:
            raise RuntimeError(f"jahs-bench bridge query failed: {response['error']}")

        error_rate = 100.0 - response["valid_acc"]
        result = (error_rate, response["size_mb"])
        self._query_cache[cache_key] = result
        return result

    def query_f1(self, genotype: Genotype, fidelity: FidelityLevel) -> float:
        error_rate, _ = self._query(genotype, fidelity)
        return error_rate

    def analytic_f2(self, genotype: Genotype) -> float:
        _, size_mb = self._query(genotype, self.fidelity_ladder()[-1])
        return size_mb

    def close(self) -> None:
        """Not called automatically -- callers that construct many
        short-lived substrates in one process (e.g. a test suite) should
        call this explicitly rather than leaking bridge processes."""
        if self._process is not None:
            self._process.stdin.close()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
