"""NAS-Bench-201 adapter, architecture-only (isolation experiment,
glimmering-swimming-book.md).

Real, live-queried against the downloaded NATS-Bench archive
(data/cache/nats_bench/ -- fetched by the user, never this test suite, from
the Google Drive link in the `nats-bench` package's own README). query_f1/
analytic_f2 query the real `nats_bench` API, not a placeholder.

Genotype decoding uses search_spaces/nas_bench_201_genotype.py, NOT
search_spaces/nas_genotype.py -- this is the architecture-only variant
(six edges, no Theta), built specifically to test P3Net without this
project's own joint architecture+hyperparameter extension, isolating
whether that extension is what's behind P3Net's failure to separate from
random_search on the two joint benchmarks (Results, ``Diagnostics:
population-pyramid bootstrap share''; Conclusions, ``Why the results are
what they are'').

Deviation from Substrate's general contract, documented rather than
silently ignored (same situation as substrates/nas_hpo_bench_ii.py and
substrates/jahs_bench_201.py): analytic_f2 is not actually computable
independently of query_f1 here either -- nats_bench's own
get_more_info/get_cost_info are two separate calls against the same
tabulated architecture record, not independently derivable quantities.
Both methods therefore share one internal per-(genotype, epoch) query
cache.

f2 = FLOPs, not Bartnik's own measured GPU energy consumption
(bartnik2026evolutionary): the NATS-Bench archive/`nats_bench` API expose
FLOPs, params, and latency (nats_bench.api_utils.ArchResults.
get_compute_costs, key "flops"), but not energy -- Bartnik measured
energy herself, on her own hardware, so it is not a queryable field of
this benchmark at all (chapters/v003/related_work/main.tex documents
this). FLOPs is used instead as a deterministic, architecture-only,
hardware-independent cost proxy -- a documented deviation, not a silent
substitution.

Single fidelity level (200 epochs, `nats_bench`'s own `hp="200"` setting)
by deliberate design, not an oversight: NAS-Bench-201 logs checkpoints up
through 200 epochs, so a real multi-fidelity ladder is technically
possible, but Bartnik's own SA-P3-GOMEA is not a multi-fidelity
algorithm, and adding a second axis of novelty here (a fidelity ladder)
alongside the one this experiment is built to isolate (removing Theta)
would break that isolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from p3net.problem.genotype import Genotype

from search_spaces.nas_bench_201_genotype import decode_nas_bench_201_genotype, genotype_to_arch_str
from substrates.base import FidelityLevel, Substrate

NATS_BENCH_DATASETS: tuple[str, ...] = ("cifar10", "cifar100", "ImageNet16-120")
FULL_TRAINING_EPOCHS = 200

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "nats_bench"


@dataclass
class NASBench201Substrate(Substrate):
    """Adapter for architecture-only NAS-Bench-201, via the `nats_bench`
    package. dataset defaults to "cifar10" (glimmering-swimming-book.md,
    Faza 0.3: the standard default across the NAS-Bench-201 literature,
    including the original Dong & Yang paper; not independently confirmed
    against Bartnik's own choice, flagged as an assumption)."""

    dataset: str = "cifar10"
    data_dir: str | Path = DEFAULT_DATA_DIR
    _api: Any = field(default=None, init=False, repr=False)
    _query_cache: dict[tuple[Genotype, int], tuple[float, float]] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        if self.dataset not in NATS_BENCH_DATASETS:
            raise ValueError(
                f"unknown NATS-Bench dataset {self.dataset!r}, expected one of {NATS_BENCH_DATASETS}"
            )

    def _get_api(self) -> Any:
        if self._api is None:
            from nats_bench import create

            self._api = create(str(self.data_dir), "tss", fast_mode=True, verbose=False)
        return self._api

    def fidelity_ladder(self) -> tuple[FidelityLevel, ...]:
        return (FidelityLevel(rank=0, config={"epochs": FULL_TRAINING_EPOCHS}),)

    def _query(self, genotype: Genotype, fidelity: FidelityLevel) -> tuple[float, float]:
        requested_epochs = fidelity.config.get("epochs", 0)
        if requested_epochs != FULL_TRAINING_EPOCHS:
            raise ValueError(
                f"NASBench201Substrate has a single fidelity level "
                f"({FULL_TRAINING_EPOCHS} epochs) by design (module docstring); "
                f"requested {requested_epochs}"
            )
        cache_key = (genotype, requested_epochs)
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        config = decode_nas_bench_201_genotype(genotype)
        arch_str = genotype_to_arch_str(config.edges)
        api = self._get_api()
        index = api.query_index_by_arch(arch_str)
        hp = str(FULL_TRAINING_EPOCHS)
        # is_random=False: nats_bench.get_more_info defaults to is_random=True,
        # which draws a uniformly random trial seed via Python's global
        # `random` module on EVERY call for architectures with more than one
        # logged trial (verified directly against real data -- the same
        # architecture returns different test-accuracy values across
        # repeated default calls). Substrate.deterministic=True (base.py) is
        # a project-wide assumption; is_random=False averages across the
        # architecture's own logged trials instead, deterministically.
        info = api.get_more_info(index, self.dataset, hp=hp, is_random=False)
        cost = api.get_cost_info(index, self.dataset, hp=hp)
        error_rate = 100.0 - info["test-accuracy"]  # this project's minimisation convention
        result = (error_rate, float(cost["flops"]))
        self._query_cache[cache_key] = result
        return result

    def query_f1(self, genotype: Genotype, fidelity: FidelityLevel) -> float:
        error_rate, _ = self._query(genotype, fidelity)
        return error_rate

    def analytic_f2(self, genotype: Genotype) -> float:
        # See module docstring: not actually analytic for this benchmark --
        # shares the real query cache with query_f1, always at r_K.
        _, flops = self._query(genotype, self.fidelity_ladder()[-1])
        return flops
