"""Simulated training cost of a run: the training time the benchmark records
for every training the run asked for, summed.

This is what the run would have cost if every evaluation had been a real
training on the benchmark authors' hardware -- the dominant part of the
practical cost, which tabular and surrogate benchmarks otherwise hide.

  * single-fidelity arms: the full-length training time of every evaluated
    configuration;
  * multi-fidelity arms: for every query, the training time up to the
    queried epoch minus the time up to the epoch this configuration was
    already trained to (the same checkpoint-resumption accounting as
    methods/multi_fidelity.py's cost model).

Substrates report training time through `training_seconds(genotype,
epochs)` (substrates/base.py); None where a benchmark records none.
Queries are served from the substrate's own cache, so this costs no
additional benchmark queries.
"""

from __future__ import annotations

from typing import Any

from p3net.harness.runner import RunState


def simulated_training_seconds(substrate: Any, state: RunState, method: Any) -> float | None:
    training_seconds = getattr(substrate, "training_seconds", None)
    if training_seconds is None:
        return None
    total = 0.0
    queries = getattr(method, "fidelity_queries", None)
    if queries is not None:
        trained: dict[Any, float] = {}
        for query in queries:
            seconds = training_seconds(query.genotype, query.epochs)
            if seconds is None:
                return None
            total += seconds - trained.get(query.genotype, 0.0)
            trained[query.genotype] = seconds
        return total
    full = substrate.max_epochs()
    for observation in state.history:
        seconds = training_seconds(observation.genotype, full)
        if seconds is None:
            return None
        total += seconds
    return total
