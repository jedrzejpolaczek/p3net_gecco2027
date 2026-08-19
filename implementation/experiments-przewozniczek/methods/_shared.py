"""Shared method scaffolding: rejection-sampling batch generation (used by
every arm), plus NSGA-II-specific variation operators and mu+lambda
survivor selection (used by nsga_net/nsganetv2 only). Internal module, not
re-exported -- kept here once rather than duplicated across call sites
(the same mistake the p3net library's maintainability audit caught in the
two surrogate files)."""

from __future__ import annotations

import random

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace

from search_engines.nsga2.crowding_distance import crowding_distance
from search_engines.nsga2.nondominated_sort import fast_nondominated_sort


def random_valid_batch(
    n: int,
    search_space: SearchSpace,
    validity: Validity,
    rng: random.Random,
    cache: EvaluationCache,
    *,
    experiment_type: str,
    protocol_version: str,
) -> list[Genotype]:
    """Rejection-sample up to n distinct, valid, not-yet-proposed
    genotypes. Every arm that needs fresh random genotypes -- initial
    population bootstrap (nsga_net, nsganetv2, p3_absolute), sanity-check
    sampling (random_search), or stall-recovery diversity injection
    (p3_alone) -- goes through this one implementation rather than its own
    copy of the same loop."""
    proposals: list[Genotype] = []
    attempts = 0
    while len(proposals) < n and attempts < n * 50 + 50:
        attempts += 1
        candidate = search_space.sample_uniform(rng)
        if not is_valid(candidate, validity):
            continue
        if candidate in proposals:
            continue
        if cache.record_proposal(
            candidate, experiment_type=experiment_type, protocol_version=protocol_version
        ):
            continue
        proposals.append(candidate)
    return proposals


def uniform_crossover(parent_a: Genotype, parent_b: Genotype, rng: random.Random) -> Genotype:
    values = tuple(rng.choice((a, b)) for a, b in zip(parent_a.values, parent_b.values))
    return Genotype(values=values)


def mutate(
    genotype: Genotype, search_space: SearchSpace, rng: random.Random, rate: float
) -> Genotype:
    values = list(genotype.values)
    for i, domain in enumerate(search_space.domains):
        if rng.random() < rate:
            values[i] = domain.sample(rng)
    return Genotype(values=tuple(values))


def select_survivors(
    population: list[Genotype],
    history: dict[Genotype, Observation],
    target_size: int,
) -> list[Genotype]:
    """mu+lambda elitist selection: nondominated sort, fill fronts until
    exceeding capacity, then trim the last admitted front by crowding
    distance."""
    fronts = fast_nondominated_sort(population, lambda g: history[g].objectives)
    survivors: list[Genotype] = []
    for front in fronts:
        if len(survivors) + len(front) <= target_size:
            survivors.extend(front)
            continue
        distances = crowding_distance(front, lambda g: history[g].objectives)
        ranked = sorted(range(len(front)), key=lambda i: distances[i], reverse=True)
        remaining = target_size - len(survivors)
        survivors.extend(front[i] for i in ranked[:remaining])
        break
    return survivors
