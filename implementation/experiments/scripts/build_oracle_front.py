"""
Enumerate a Category 1 benchmark's EXACT oracle Pareto front.

NAS-HPO-Bench-II is a fixed lookup table over 4^6 edge combinations x 8
learning rates x 6 batch sizes = 196,608 configurations, every one of them
answerable at r_K (12 tabulated epochs) without training anything. The
exact oracle front is therefore enumerable, which is the whole reason
Related Work classifies this benchmark as Category 1 -- and it is what
makes IGD+, an absolute metric, available here where the JAHS-Bench-201
family only admits hypervolume relative to a pooled best-known front.

The Results section has promised IGD+ on this benchmark since the first
draft and reported hypervolume-relative instead. This script closes that
gap. Invalid genotypes (no input-output path through the cell) are
excluded, matching the search's own feasible set Lambda*.

FCNet (all four tasks, 62,208 configurations each, no infeasible ones) is
Category 1 in the same sense (phase 2d, substrates/fcnet.py).

Writes results/reference_fronts/oracle__<search space>.json, which
scripts/generate_report.py picks up automatically via
reporting.reference_fronts.load_oracle_fronts.
"""

from __future__ import annotations

import argparse
import itertools
import sys
import time
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

from p3net.problem.decoding import is_valid
from p3net.problem.genotype import Genotype

from reporting._common import _nondominated_front_2d
from reporting.reference_fronts import save_oracle_front
from search_spaces.nas_hpo_bench_ii_genotype import (
    nas_hpo_bench_ii_search_space,
    nas_hpo_bench_ii_validity,
)
from substrates.nas_hpo_bench_ii import NASHPOBenchIISubstrate


def build_nas_hpo_bench_ii_oracle(*, progress_every: int = 20000) -> tuple[list, int, int]:
    space = nas_hpo_bench_ii_search_space()
    substrate = NASHPOBenchIISubstrate()
    r_k = substrate.fidelity_ladder()[-1]

    domains = [d.values for d in space.domains]
    n_enumerated = 0
    n_valid = 0
    points: list[tuple[float, float]] = []
    started = time.time()

    for combo in itertools.product(*domains):
        n_enumerated += 1
        genotype = Genotype(values=tuple(combo))
        if not is_valid(genotype, nas_hpo_bench_ii_validity):
            continue
        n_valid += 1
        f1 = substrate.query_f1(genotype, r_k)
        f2 = substrate.analytic_f2(genotype)
        points.append((float(f1), float(f2)))

        if progress_every and n_enumerated % progress_every == 0:
            elapsed = time.time() - started
            print(
                f"  {n_enumerated} enumerated, {n_valid} valid, {elapsed:.0f}s elapsed",
                flush=True,
            )

    front = _nondominated_front_2d(points)
    return front, n_enumerated, n_valid


def build_fcnet_oracle(task: str) -> tuple[list, int, int]:
    """FCNet: every one of the 62,208 configurations is tabulated and valid;
    (f1, f2) read straight from the substrate's arrays at 100 epochs."""
    from substrates.fcnet import FCNetSubstrate

    genotypes, objectives = FCNetSubstrate(task=task).all_objectives()
    points = [(float(f1), float(f2)) for f1, f2 in objectives]
    return _nondominated_front_2d(points), len(genotypes), len(genotypes)


FCNET_SPACES = {
    f"fcnet_{task}": task
    for task in (
        "protein_structure",
        "naval_propulsion",
        "parkinsons_telemonitoring",
        "slice_localization",
    )
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-space", default="nas_hpo_bench_ii")
    args = parser.parse_args(argv)

    if args.search_space in FCNET_SPACES:
        print(f"enumerating {args.search_space} (62,208 configurations)...", flush=True)
        front, n_enumerated, n_valid = build_fcnet_oracle(FCNET_SPACES[args.search_space])
    elif args.search_space == "nas_hpo_bench_ii":
        print("enumerating NAS-HPO-Bench-II (196,608 configurations)...", flush=True)
        front, n_enumerated, n_valid = build_nas_hpo_bench_ii_oracle()
    else:
        raise SystemExit(
            f"no exhaustive enumeration is defined for {args.search_space!r} -- "
            f"Category 1 spaces here: nas_hpo_bench_ii, {', '.join(FCNET_SPACES)}"
        )
    path = save_oracle_front(args.search_space, front, n_enumerated=n_enumerated, n_valid=n_valid)
    print(
        f"oracle front: {len(front)} nondominated points "
        f"from {n_valid} valid / {n_enumerated} enumerated -> {path}"
    )


if __name__ == "__main__":
    main()
