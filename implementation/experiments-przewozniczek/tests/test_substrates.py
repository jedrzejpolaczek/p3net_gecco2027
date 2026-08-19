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
from substrates.nas_bench_201 import (
    DEFAULT_DATA_DIR as NAS_BENCH_201_DEFAULT_DATA_DIR,
)
from substrates.nas_bench_201 import (
    NATS_BENCH_DATASETS,
    NASBench201Substrate,
)
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

# glimmering-swimming-book.md, Faza 0: nats_bench's own downloaded archive
# directory layout is not fixed to one filename the way nashpobench2api's
# bench12.pkl is -- check for the directory's existence instead (populated
# by the user manually, per project convention, never by this test suite).
_requires_real_nats_bench_data = pytest.mark.skipif(
    not Path(NAS_BENCH_201_DEFAULT_DATA_DIR).exists(),
    reason="real NATS-Bench (NAS-Bench-201) data not downloaded in this environment",
)

_requires_real_jahs_bench = pytest.mark.skipif(
    not (BRIDGE_PYTHON.exists() and os.environ.get("RUN_JAHS_BENCH_LIVE_TESTS") == "1"),
    reason=(
        "jahs-bench live queries take several minutes just to load the surrogate "
        "models -- opt in explicitly with RUN_JAHS_BENCH_LIVE_TESTS=1 (also requires "
        "vendor/jahsbench-env)"
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


def test_analytic_cost_objectives_computes_f2_fresh_without_a_wasted_f1_query():
    """P3Net's optional analytic_cost hook (methods.p3net.P3Net.analytic_cost)
    needs a Callable[[Genotype], Objectives] -- this adapter shapes
    analytic_f2 (a bare float) into that contract without ever touching
    query_f1 (the real evaluation budget must never be spent computing an
    estimate)."""
    substrate = FakeSubstrate()
    genotype = Genotype(values=(1, 1, 0))
    objectives = substrate.analytic_cost_objectives(genotype)
    assert objectives[1] == 3.0  # == analytic_f2(genotype), independent of query_f1


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


def _nas_bench_201_genotype(edges=("none",) * 6) -> Genotype:
    return Genotype(values=tuple(edges))


def test_nas_bench_201_rejects_unknown_dataset():
    with pytest.raises(ValueError):
        NASBench201Substrate(dataset="not_a_real_dataset")


def test_nas_bench_201_accepts_documented_datasets():
    for dataset in NATS_BENCH_DATASETS:
        NASBench201Substrate(dataset=dataset)  # must not raise


def test_nas_bench_201_fidelity_ladder_has_exactly_one_level_at_200_epochs():
    """Deliberately a single fidelity level (glimmering-swimming-book.md,
    Faza 2 design decision): a real multi-epoch fidelity ladder would
    introduce a second new variable alongside removing Theta, breaking the
    isolation this experiment exists to provide -- not a limitation to
    lift casually."""
    substrate = NASBench201Substrate()
    ladder = substrate.fidelity_ladder()
    assert len(ladder) == 1
    assert ladder[0].config["epochs"] == 200


@_requires_real_nats_bench_data
def test_nas_bench_201_query_f1_is_deterministic_across_repeated_queries():
    """nats_bench's own get_more_info defaults to is_random=True, picking
    a uniformly random trial seed via Python's global random module on
    EVERY call for architectures with more than one logged trial --
    verified directly: the same architecture (edges below) returns two
    different test-accuracy values across repeated calls under that
    default. Substrate.deterministic=True (base.py) is a project-wide
    assumption the rest of the harness (e.g. stopping rules, duplicate
    detection) relies on; NASBench201Substrate must not violate it."""
    edges = ("nor_conv_3x3", "avg_pool_3x3", "skip_connect", "none", "nor_conv_3x3", "none")
    results = set()
    for _ in range(10):
        substrate = NASBench201Substrate()  # fresh instance, no cache reuse
        f1 = substrate.query_f1(_nas_bench_201_genotype(edges=edges), substrate.fidelity_ladder()[-1])
        results.add(f1)
    assert len(results) == 1


@_requires_real_nats_bench_data
def test_nas_bench_201_query_f1_returns_a_real_error_rate():
    substrate = NASBench201Substrate()
    genotype = _nas_bench_201_genotype()
    f1 = substrate.query_f1(genotype, substrate.fidelity_ladder()[-1])
    assert 0.0 <= f1 <= 100.0


@_requires_real_nats_bench_data
def test_nas_bench_201_analytic_f2_returns_real_flops():
    substrate = NASBench201Substrate()
    genotype = _nas_bench_201_genotype()
    f2 = substrate.analytic_f2(genotype)
    assert f2 > 0.0


@_requires_real_nats_bench_data
def test_nas_bench_201_shares_one_query_cache_between_f1_and_f2():
    """query_f1 and analytic_f2 must not double-query the real API for the
    same genotype -- same deviation from Substrate's general contract as
    both existing substrates (see substrates/nas_bench_201.py's module
    docstring)."""
    substrate = NASBench201Substrate()
    genotype = _nas_bench_201_genotype()
    substrate.query_f1(genotype, substrate.fidelity_ladder()[-1])
    assert len(substrate._query_cache) == 1
    substrate.analytic_f2(genotype)
    assert len(substrate._query_cache) == 1


@_requires_real_nats_bench_data
def test_nas_bench_201_objectives_matches_a_direct_real_query():
    from search_spaces.nas_bench_201_genotype import genotype_to_arch_str

    edges = ("nor_conv_3x3", "avg_pool_3x3", "skip_connect", "none", "nor_conv_3x3", "none")
    substrate = NASBench201Substrate()
    genotype = _nas_bench_201_genotype(edges=edges)
    f1, f2 = substrate.objectives(genotype)

    api = substrate._get_api()
    index = api.query_index_by_arch(genotype_to_arch_str(edges))
    info = api.get_more_info(index, "cifar10", hp="200", is_random=False)
    cost = api.get_cost_info(index, "cifar10", hp="200")
    assert f1 == pytest.approx(100.0 - info["test-accuracy"])
    assert f2 == pytest.approx(cost["flops"])
