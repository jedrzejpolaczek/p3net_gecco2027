"""Tests for experiments.substrates. Structural only in Stage B: the real
benchmark packages aren't installed yet, so this tests the shared
Substrate base behaviour (via a fake concrete subclass) and each
adapter's guard rails, not real query results."""

import pytest
from p3net.problem.genotype import Genotype

from substrates.base import FidelityLevel, Substrate
from substrates.jahs_bench_201 import JAHS_DATASETS, JAHSBench201Substrate
from substrates.nas_hpo_bench_ii import MAX_TABULATED_EPOCHS, NASHPOBenchIISubstrate


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


def test_jahs_bench_201_query_f1_fails_loudly_not_silently():
    substrate = JAHSBench201Substrate()
    genotype = Genotype(values=("none",) * 6 + (1e-3, 1e-5, "relu", False))
    with pytest.raises(NotImplementedError):
        substrate.query_f1(genotype, substrate.fidelity_ladder()[-1])


def test_jahs_bench_201_analytic_f2_fails_loudly_not_silently():
    substrate = JAHSBench201Substrate()
    genotype = Genotype(values=("none",) * 6 + (1e-3, 1e-5, "relu", False))
    with pytest.raises(NotImplementedError):
        substrate.analytic_f2(genotype)


def test_nas_hpo_bench_ii_fidelity_ladder_fixed_at_tabulated_range():
    substrate = NASHPOBenchIISubstrate()
    ladder = substrate.fidelity_ladder()
    assert ladder[-1].config["epochs"] == MAX_TABULATED_EPOCHS


def test_nas_hpo_bench_ii_never_queries_the_200_epoch_surrogate():
    substrate = NASHPOBenchIISubstrate()
    genotype = Genotype(values=("none",) * 6 + (1e-3, 1e-5, "relu", False))
    beyond_tabulated = FidelityLevel(rank=1, config={"epochs": 200})
    with pytest.raises(ValueError, match="tabulated range"):
        substrate.query_f1(genotype, beyond_tabulated)


def test_nas_hpo_bench_ii_query_f1_within_range_fails_loudly_not_silently():
    substrate = NASHPOBenchIISubstrate()
    genotype = Genotype(values=("none",) * 6 + (1e-3, 1e-5, "relu", False))
    with pytest.raises(NotImplementedError):
        substrate.query_f1(genotype, substrate.fidelity_ladder()[-1])
