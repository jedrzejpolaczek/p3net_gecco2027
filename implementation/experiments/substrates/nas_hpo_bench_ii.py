"""NAS-HPO-Bench-II adapter (Category 1: fixed grid lookup table, exact
oracle front).

Real, live-queried against the downloaded dataset
(data/cache/nashpobench2/ -- fetched via `gdown` from the Google Drive
link in nashpobench2api's own README; see ../TASKS.md for the exact
steps and provenance). query_f1/analytic_f2 query the real
NASHPOBench2API, not a placeholder.

Genotype decoding uses search_spaces/nas_hpo_bench_ii_genotype.py, NOT
search_spaces/nas_genotype.py -- this benchmark's real search space (4
ops, learning_rate x batch_size) differs from what that module assumes
for JAHS-Bench-201 (see that module's own docstring for why).

Deviation from Substrate's general contract, documented rather than
silently ignored: analytic_f2 is NOT actually computable independently
of query_f1 for this benchmark. NASHPOBench2API.query_by_key() returns
accuracy and training cost together, from the same tabulated row --
there is no separate, cheaper way to get one without the other, since
this is a lookup table of completed training runs, not an
analytically-derivable proxy. Both methods therefore share one internal
per-(genotype, epoch) query cache, so a given genotype is only looked up
once against the real API regardless of which method is called first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from p3net.problem.genotype import Genotype

from search_spaces.nas_hpo_bench_ii_genotype import (
    decode_nas_hpo_bench_ii_genotype,
    genotype_to_cellcode,
)
from substrates.base import FidelityLevel, Substrate

MAX_TABULATED_EPOCHS = 12
"""r_K for this benchmark is fixed at the tabulated range only -- the
200-epoch GIN+MLP surrogate extrapolation is never queried by this
substrate (chapters/v003/related_work/main.tex, "Classifying
NAS-HPO-Bench-II as Category 1...")."""

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "nashpobench2"


@dataclass
class NASHPOBenchIISubstrate(Substrate):
    """Adapter for NAS-HPO-Bench-II -- restricted to its exhaustively
    tabulated range (up to MAX_TABULATED_EPOCHS training epochs). An
    exact oracle Pareto front is enumerable for this benchmark
    (Category 1) -- p3net.metrics.igd_plus applies, unlike
    JAHS-Bench-201.
    """

    data_dir: str | Path = DEFAULT_DATA_DIR
    _api: Any = field(default=None, init=False, repr=False)
    _query_cache: dict[tuple[Genotype, int], tuple[float, float]] = field(
        default_factory=dict, init=False, repr=False
    )

    def _get_api(self) -> Any:
        if self._api is None:
            from nashpobench2api import NASHPOBench2API

            self._api = NASHPOBench2API(str(self.data_dir), verbose=False)
        return self._api

    def fidelity_ladder(self) -> tuple[FidelityLevel, ...]:
        return (FidelityLevel(rank=0, config={"epochs": MAX_TABULATED_EPOCHS}),)

    def _query(self, genotype: Genotype, fidelity: FidelityLevel) -> tuple[float, float]:
        requested_epochs = fidelity.config.get("epochs", 0)
        if requested_epochs > MAX_TABULATED_EPOCHS:
            raise ValueError(
                f"NAS-HPO-Bench-II is restricted to its tabulated range "
                f"(<= {MAX_TABULATED_EPOCHS} epochs); the 200-epoch surrogate "
                f"extrapolation is never queried by this substrate "
                f"(requested {requested_epochs})"
            )
        cache_key = (genotype, requested_epochs)
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        config = decode_nas_hpo_bench_ii_genotype(genotype)
        cellcode = genotype_to_cellcode(config.edges)
        api = self._get_api()
        accuracy, cost = api.query_by_key(
            cellcode=cellcode,
            lr=config.learning_rate,
            batch_size=config.batch_size,
            epoch=requested_epochs,
        )
        error_rate = 100.0 - accuracy  # this project's minimisation convention: lower f1 = better
        result = (error_rate, float(cost))
        self._query_cache[cache_key] = result
        return result

    def query_f1(self, genotype: Genotype, fidelity: FidelityLevel) -> float:
        error_rate, _ = self._query(genotype, fidelity)
        return error_rate

    def analytic_f2(self, genotype: Genotype) -> float:
        # See module docstring: not actually analytic for this benchmark
        # -- shares the real query cache with query_f1, always at r_K.
        _, cost = self._query(genotype, self.fidelity_ladder()[-1])
        return cost
