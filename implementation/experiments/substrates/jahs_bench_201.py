"""JAHS-Bench-201 adapter (primary benchmark, Category 2: continuous
surrogate, no enumerable oracle front).

Unverified-against-live-data note: structured against JAHS-Bench-201's
published description, not a live query -- the jahs-bench package isn't
installed yet (Stage C, ../TASKS.md). query_f1/analytic_f2 deliberately
raise NotImplementedError rather than silently returning a fake value, so
any accidental use before Stage C fails loudly.
"""

from __future__ import annotations

from dataclasses import dataclass

from p3net.problem.genotype import Genotype

from substrates.base import FidelityLevel, Substrate

JAHS_DATASETS: tuple[str, ...] = ("cifar10", "colorectal_histology", "fashion_mnist")


@dataclass
class JAHSBench201Substrate(Substrate):
    """Adapter for JAHS-Bench-201 -- ten joint search dimensions (six
    architecture edges + four hyperparameters) across three datasets, plus
    four further fidelity dimensions (epochs, resolution, ...) tracked
    separately from the searched genotype. No enumerable oracle front
    exists for this benchmark (Category 2) -- do not compute IGD+ against
    it; p3net.metrics.hypervolume's best-known-front fallback applies
    instead."""

    dataset: str = "cifar10"

    def __post_init__(self) -> None:
        if self.dataset not in JAHS_DATASETS:
            raise ValueError(
                f"unknown JAHS-Bench-201 dataset {self.dataset!r}, expected one of {JAHS_DATASETS}"
            )

    def fidelity_ladder(self) -> tuple[FidelityLevel, ...]:
        # TODO(Stage C): replace with JAHS-Bench-201's real epoch/resolution
        # fidelity axes once the package is installed and its API examined.
        return (FidelityLevel(rank=0, config={"epochs": 200, "resolution": 1.0}),)

    def query_f1(self, genotype: Genotype, fidelity: FidelityLevel) -> float:
        raise NotImplementedError(
            "JAHSBench201Substrate.query_f1 needs the jahs-bench package "
            "installed and its real query API wired up (Stage C, "
            "../TASKS.md) -- deliberately not stubbed with a fake value."
        )

    def analytic_f2(self, genotype: Genotype) -> float:
        raise NotImplementedError(
            "JAHSBench201Substrate.analytic_f2 needs the jahs-bench "
            "package's cost/size accessor wired up (Stage C, ../TASKS.md)."
        )
