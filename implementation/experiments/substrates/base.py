"""Common substrate interface: the thing that answers full evaluations of
f1 for this paper's two benchmarks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives


@dataclass(frozen=True)
class FidelityLevel:
    """One resource configuration a substrate can be queried at (epochs,
    resolution, ...). Mirrors p3net.problem.objectives.FidelityLevel's
    shape but lives here since it's substrate-specific configuration, not
    generic library machinery."""

    rank: int
    config: dict


class Substrate(ABC):
    """The thing that answers full evaluations of f1 (and, where
    applicable, an analytic f2) for a concrete benchmark. Concrete
    subclasses (jahs_bench_201.py, nas_hpo_bench_ii.py) implement
    query_f1/analytic_f2/fidelity_ladder; `objectives()` -- the
    harness.Runner-compatible callable -- is shared here so it can't drift
    between the two benchmarks."""

    deterministic: bool = True
    """Both of this paper's benchmarks are deterministic (s=1 throughout,
    Problem Formulation "Evaluation noise")."""

    @abstractmethod
    def fidelity_ladder(self) -> tuple[FidelityLevel, ...]:
        """r_1 < ... < r_K for this benchmark."""

    @abstractmethod
    def query_f1(self, genotype: Genotype, fidelity: FidelityLevel) -> float:
        """A full evaluation of f1 at the given fidelity level. This is
        the cost unit p3net.harness.Runner's budget counts -- never call
        this from a surrogate."""

    @abstractmethod
    def analytic_f2(self, genotype: Genotype) -> float:
        """The computational cost proxy, computed without querying the
        benchmark's f1 machinery, held fixed at the highest fidelity
        level's resolution setting regardless of which fidelity f1 is
        queried at (Problem Formulation)."""

    def objectives(self, genotype: Genotype) -> Objectives:
        """(f1 at r_K, f2), as a harness.Runner-compatible objective
        callable: Runner(objective=substrate.objectives, ...)."""
        r_k = self.fidelity_ladder()[-1]
        return (self.query_f1(genotype, r_k), self.analytic_f2(genotype))
