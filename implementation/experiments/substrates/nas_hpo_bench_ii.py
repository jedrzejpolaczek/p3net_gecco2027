"""NAS-HPO-Bench-II adapter (Category 1: fixed grid lookup table, exact
oracle front).

Unverified-against-live-data note: structured against NAS-HPO-Bench-II's
published description, not a live query -- the nashpobench2api package
isn't installed yet (Stage C, ../TASKS.md). query_f1/analytic_f2
deliberately raise NotImplementedError rather than silently returning a
fake value.
"""

from __future__ import annotations

from dataclasses import dataclass

from p3net.problem.genotype import Genotype

from substrates.base import FidelityLevel, Substrate

MAX_TABULATED_EPOCHS = 12
"""r_K for this benchmark is fixed at the tabulated range only -- the
200-epoch GIN+MLP surrogate extrapolation is never queried by this
substrate (chapters/v003/related_work/main.tex, "Classifying
NAS-HPO-Bench-II as Category 1...")."""


@dataclass
class NASHPOBenchIISubstrate(Substrate):
    """Adapter for NAS-HPO-Bench-II -- restricted to its exhaustively
    tabulated range (up to 12 training epochs, three recorded seeds per
    entry). An exact oracle Pareto front is enumerable for this benchmark
    (Category 1) -- p3net.metrics.igd_plus applies, unlike JAHS-Bench-201.
    """

    def fidelity_ladder(self) -> tuple[FidelityLevel, ...]:
        return (FidelityLevel(rank=0, config={"epochs": MAX_TABULATED_EPOCHS}),)

    def query_f1(self, genotype: Genotype, fidelity: FidelityLevel) -> float:
        requested_epochs = fidelity.config.get("epochs", 0)
        if requested_epochs > MAX_TABULATED_EPOCHS:
            raise ValueError(
                f"NAS-HPO-Bench-II is restricted to its tabulated range "
                f"(<= {MAX_TABULATED_EPOCHS} epochs); the 200-epoch surrogate "
                f"extrapolation is never queried by this substrate "
                f"(requested {requested_epochs})"
            )
        raise NotImplementedError(
            "NASHPOBenchIISubstrate.query_f1 needs the nashpobench2api "
            "package installed and its real lookup-table API wired up "
            "(Stage C, ../TASKS.md) -- deliberately not stubbed with a fake value."
        )

    def analytic_f2(self, genotype: Genotype) -> float:
        raise NotImplementedError(
            "NASHPOBenchIISubstrate.analytic_f2 needs the nashpobench2api "
            "package's cost accessor wired up (Stage C, ../TASKS.md)."
        )
