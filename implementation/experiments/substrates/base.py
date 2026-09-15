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

    def max_epochs(self) -> int:
        """Training epochs of a full evaluation (r_K's epoch count)."""
        return int(self.fidelity_ladder()[-1].config["epochs"])

    def objectives_at_epochs(self, genotype: Genotype, epochs: int) -> Objectives:
        """(f1 after `epochs` training epochs, f2) -- the multi-fidelity
        track's query (methods/multi_fidelity.py). f2 stays the r_K value,
        exactly as in `objectives`; only f1 depends on the fidelity. At
        epochs == max_epochs() this is identical to `objectives`."""
        fidelity = FidelityLevel(rank=-1, config={"epochs": epochs})
        return (self.query_f1(genotype, fidelity), self.analytic_f2(genotype))

    def training_seconds(self, genotype: Genotype, epochs: int) -> float | None:
        """Training time, in seconds, the benchmark records for training
        `genotype` for `epochs` epochs (measurement/training_cost.py). None
        if the benchmark records none."""
        return None

    def full_fidelity_metrics(self, genotype: Genotype) -> dict[str, float]:
        """Every accuracy the benchmark records for `genotype` at r_K --
        keys among train_acc, valid_acc, test_acc (percent) and
        training_seconds. Queried after a run, outside the evaluation
        budget, for the test-set front and the generalisation gaps
        (scripts/posthoc_metrics.py)."""
        return {}

    def analytic_cost_objectives(self, genotype: Genotype) -> Objectives:
        """Objectives-shaped adapter around analytic_f2, for search engines
        that need every non-f1 objective computed fresh without a wasted f1
        query (p3net.methods.p3net.P3Net's optional `analytic_cost` hook --
        Proposed Optimizer's "Known simplification 2"). f1's own slot is a
        placeholder never read by callers of this adapter -- never call
        query_f1 here, that would spend real evaluation budget on an
        estimate."""
        return (0.0, self.analytic_f2(genotype))
