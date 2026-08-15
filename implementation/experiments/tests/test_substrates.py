"""Tests for experiments.substrates. Both benchmarks are real (Stage C):
nashpobench2api and jahs-bench are both installed (the latter via a
subprocess bridge to a dedicated Python 3.10 environment -- see
substrates/jahs_bench_201.py's module docstring) and their data
downloaded. Live-query tests are guarded by skips so a fresh clone
(where vendor/jahsbench-env and data/cache/ don't exist -- both
gitignored) still collects and passes everything else; the JAHS-Bench-201
live test is additionally opt-in (RUN_JAHS_BENCH_LIVE_TESTS=1) since
starting that bridge takes several minutes just to load its surrogate
models, which would otherwise slow down every routine `uv run pytest`."""

import os
from pathlib import Path

import pytest
from p3net.problem.genotype import Genotype

from substrates.base import FidelityLevel, Substrate
from substrates.jahs_bench_201 import BRIDGE_PYTHON, JAHS_DATASETS, JAHSBench201Substrate
from substrates.nas_hpo_bench_ii import (
    DEFAULT_DATA_DIR,
    MAX_TABULATED_EPOCHS,
    NASHPOBenchIISubstrate,
)

_HAS_REAL_NASHPOBENCH_DATA = Path(DEFAULT_DATA_DIR, "bench12.pkl").exists()
_requires_real_nashpobench_data = pytest.mark.skipif(
    not _HAS_REAL_NASHPOBENCH_DATA,
    reason="real NAS-HPO-Bench-II data not downloaded in this environment",
)

_requires_real_jahs_bench = pytest.mark.skipif(
    not (BRIDGE_PYTHON.exists() and os.environ.get("RUN_JAHS_BENCH_LIVE_TESTS") == "1"),
    reason=(
        "jahs-bench live queries take several minutes just to load the surrogate "
        "models -- opt in explicitly with RUN_JAHS_BENCH_LIVE_TESTS=1 (also requires "
        "vendor/jahsbench-env, see ../TASKS.md)"
    ),
)


def _nas_hpo_bench_ii_genotype(
    edges=("none",) * 6, lr: float = 0.1, batch_size: int = 256
) -> Genotype:
    return Genotype(values=tuple(edges) + (lr, batch_size))


class FakeSubstrate(Substrate):
    """A fully-implemented fake, used only to test Substrate's shared
    objectives() composition without depending on either real benchmark
    (which aren't queryable yet)."""

    def fidelity_ladder(self):
        return (
            FidelityLevel(rank=0, config={"epochs": 1}),
            FidelityLevel(rank=1, config={"epochs": 10}),
        )

    def query_f1(self, genotype, fidelity):
        return float(sum(genotype.values)) * fidelity.config["epochs"]

    def analytic_f2(self, genotype):
        return float(len(genotype.values))


def test_objectives_composes_f1_at_highest_fidelity_with_f2():
    substrate = FakeSubstrate()
    genotype = Genotype(values=(1, 1, 0))
    f1, f2 = substrate.objectives(genotype)
    # highest fidelity level has epochs=10
    assert f1 == 2.0 * 10
    assert f2 == 3.0


def test_deterministic_flag_defaults_true():
    assert FakeSubstrate().deterministic is True


def test_jahs_bench_201_rejects_unknown_dataset():
    with pytest.raises(ValueError):
        JAHSBench201Substrate(dataset="not_a_real_dataset")


def test_jahs_bench_201_accepts_documented_datasets():
    for dataset in JAHS_DATASETS:
        JAHSBench201Substrate(dataset=dataset)  # must not raise


def test_jahs_bench_201_bridge_environment_documented_when_missing():
    """Without the bridge built, querying must fail with a clear
    explanation, not an opaque FileNotFoundError from subprocess.Popen."""
    substrate = JAHSBench201Substrate(data_dir="unused")
    if BRIDGE_PYTHON.exists():
        pytest.skip("bridge environment is present in this environment")
    genotype = Genotype(values=("none",) * 6 + (1e-3, 1e-5, "relu", False))
    with pytest.raises(RuntimeError, match="bridge environment not found"):
        substrate.query_f1(genotype, substrate.fidelity_ladder()[-1])


@_requires_real_jahs_bench
def test_jahs_bench_201_live_query_end_to_end():
    """One consolidated test covering the full substrate lifecycle
    (query_f1, analytic_f2 sharing the query cache, close()) rather than
    separate tests each paying the multi-minute bridge-startup cost."""
    substrate = JAHSBench201Substrate(dataset="cifar10")
    try:
        genotype = Genotype(values=("none",) * 6 + (0.1, 5e-4, "relu", False))
        f1 = substrate.query_f1(genotype, substrate.fidelity_ladder()[-1])
        assert 0.0 <= f1 <= 100.0  # error rate

        assert len(substrate._query_cache) == 1
        f2 = substrate.analytic_f2(genotype)
        assert f2 > 0.0  # model size in MB
        assert len(substrate._query_cache) == 1  # shared cache, no second query

        f1_again, f2_again = substrate.objectives(genotype)
        assert f1_again == pytest.approx(f1)
        assert f2_again == pytest.approx(f2)
    finally:
        substrate.close()


def test_nas_hpo_bench_ii_fidelity_ladder_fixed_at_tabulated_range():
    substrate = NASHPOBenchIISubstrate()
    ladder = substrate.fidelity_ladder()
    assert ladder[-1].config["epochs"] == MAX_TABULATED_EPOCHS


def test_nas_hpo_bench_ii_never_queries_the_200_epoch_surrogate():
    substrate = NASHPOBenchIISubstrate()
    beyond_tabulated = FidelityLevel(rank=1, config={"epochs": 200})
    with pytest.raises(ValueError, match="tabulated range"):
        substrate.query_f1(_nas_hpo_bench_ii_genotype(), beyond_tabulated)


@_requires_real_nashpobench_data
def test_nas_hpo_bench_ii_query_f1_returns_a_real_error_rate():
    substrate = NASHPOBenchIISubstrate()
    # cellcode '3|33|333' (all edges "none") is the fully-disconnected,
    # chance-level-accuracy network -- verified empirically (see
    # search_spaces/nas_hpo_bench_ii_genotype.py's module docstring).
    genotype = _nas_hpo_bench_ii_genotype()
    f1 = substrate.query_f1(genotype, substrate.fidelity_ladder()[-1])
    assert 85.0 <= f1 <= 95.0  # error rate = 100 - ~10% chance-level accuracy


@_requires_real_nashpobench_data
def test_nas_hpo_bench_ii_analytic_f2_returns_the_real_training_cost():
    substrate = NASHPOBenchIISubstrate()
    genotype = _nas_hpo_bench_ii_genotype()
    cost = substrate.analytic_f2(genotype)
    assert cost > 0.0


@_requires_real_nashpobench_data
def test_nas_hpo_bench_ii_shares_one_query_cache_between_f1_and_f2():
    """query_f1 and analytic_f2 must not double-query the real API for
    the same genotype -- see substrates/nas_hpo_bench_ii.py's module
    docstring on why analytic_f2 isn't actually analytic here."""
    substrate = NASHPOBenchIISubstrate()
    genotype = _nas_hpo_bench_ii_genotype()
    substrate.query_f1(genotype, substrate.fidelity_ladder()[-1])
    assert len(substrate._query_cache) == 1
    substrate.analytic_f2(genotype)
    assert len(substrate._query_cache) == 1


@_requires_real_nashpobench_data
def test_nas_hpo_bench_ii_objectives_matches_a_direct_real_query():
    from nashpobench2api import NASHPOBench2API

    from search_spaces.nas_hpo_bench_ii_genotype import genotype_to_cellcode

    edges = ("nor_conv_3x3", "avg_pool_3x3", "skip_connect", "none", "nor_conv_3x3", "none")
    substrate = NASHPOBenchIISubstrate()
    genotype = _nas_hpo_bench_ii_genotype(edges=edges)
    f1, f2 = substrate.objectives(genotype)

    api = NASHPOBench2API(str(DEFAULT_DATA_DIR), verbose=False)
    accuracy, cost = api.query_by_key(cellcode=genotype_to_cellcode(edges), lr=0.1, batch_size=256)
    assert f1 == pytest.approx(100.0 - accuracy)
    assert f2 == pytest.approx(cost)
