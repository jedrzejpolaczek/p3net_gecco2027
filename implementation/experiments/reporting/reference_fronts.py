"""
Frozen best-known fronts and exact oracle fronts.

Audit finding C1: `construct_best_known_front` pools every point evaluated
by every run it is handed, so the denominator of
`hypervolume_relative_to_best_known_front` is a function of the arm set.
Adding an arm that finds better points silently, retroactively changes
every other arm's reported metric -- including numbers already written
into the paper. Any comparison that spans two reporting passes with
different arm sets is therefore not directly comparable unless the front
is pinned.

This module persists the front (and the nadir reference point derived from
the same pooled points) to results/reference_fronts/<search_space>.json,
records the exact run set it was built from, and reloads it on subsequent
passes. `scripts/generate_report.py` builds the frozen set once if it is
absent and reuses it thereafter; `--refreeze` rebuilds it deliberately.

Separately, for a Category 1 benchmark whose search space is small enough
to enumerate exhaustively (NAS-HPO-Bench-II: 4^6 edge combinations x 8
learning rates x 6 batch sizes = 196,608 configurations), the EXACT oracle
front is computable, and IGD+ against it is a genuine absolute metric
rather than a relative one. `build_oracle_front` enumerates it by direct
substrate query; `scripts/build_oracle_front.py` is the entry point.

Reference: chapters/v003/results/main.tex ("Metrics").
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from p3net.problem.objectives import Objectives

from reporting._common import RawRun, construct_best_known_front, nadir_reference_point

DEFAULT_REFERENCE_DIR = Path(__file__).resolve().parent.parent / "results" / "reference_fronts"


@dataclass(frozen=True)
class FrozenFront:
    search_space: str
    front: tuple[Objectives, ...]
    reference_point: Objectives
    #: Hash over the sorted (method, budget, seed) triples the front was
    #: pooled from -- so a later pass can tell whether it is reusing a
    #: front built from a different arm set, rather than silently
    #: assuming otherwise.
    source_run_digest: str
    n_source_runs: int
    n_pooled_points: int

    def to_json(self) -> dict:
        return {
            "search_space": self.search_space,
            "front": [list(p) for p in self.front],
            "reference_point": list(self.reference_point),
            "source_run_digest": self.source_run_digest,
            "n_source_runs": self.n_source_runs,
            "n_pooled_points": self.n_pooled_points,
        }

    @staticmethod
    def from_json(payload: dict) -> FrozenFront:
        return FrozenFront(
            search_space=payload["search_space"],
            front=tuple(tuple(p) for p in payload["front"]),
            reference_point=tuple(payload["reference_point"]),
            source_run_digest=payload["source_run_digest"],
            n_source_runs=payload["n_source_runs"],
            n_pooled_points=payload["n_pooled_points"],
        )


def _run_set_digest(runs: Sequence[RawRun]) -> str:
    keys = sorted(f"{r.method}|{r.budget}|{r.seed}" for r in runs)
    return hashlib.sha256("\n".join(keys).encode("utf-8")).hexdigest()[:16]


def freeze_fronts(runs: Sequence[RawRun]) -> dict[str, FrozenFront]:
    """One FrozenFront per search space present in `runs`, pooled exactly
    the way `fixed_budget_summary_table` pools when it builds them
    on the fly -- per search space, across every budget tier and arm."""
    by_space: dict[str, list[RawRun]] = {}
    for run in runs:
        if run.objectives:
            by_space.setdefault(run.search_space, []).append(run)

    frozen: dict[str, FrozenFront] = {}
    for space, space_runs in by_space.items():
        all_points = [p for r in space_runs for p in r.objectives]
        frozen[space] = FrozenFront(
            search_space=space,
            front=tuple(construct_best_known_front(space_runs)),
            reference_point=nadir_reference_point(all_points),
            source_run_digest=_run_set_digest(space_runs),
            n_source_runs=len(space_runs),
            n_pooled_points=len(all_points),
        )
    return frozen


def save_fronts(frozen: dict[str, FrozenFront], directory: Path = DEFAULT_REFERENCE_DIR) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for space, front in sorted(frozen.items()):
        path = directory / f"{space}.json"
        path.write_text(json.dumps(front.to_json(), indent=2), encoding="utf-8")
        written.append(path)
    return written


def load_fronts(directory: Path = DEFAULT_REFERENCE_DIR) -> dict[str, FrozenFront]:
    if not directory.exists():
        return {}
    frozen: dict[str, FrozenFront] = {}
    for path in sorted(directory.glob("*.json")):
        if path.name.startswith("oracle__"):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        frozen[payload["search_space"]] = FrozenFront.from_json(payload)
    return frozen


def describe_fronts(frozen: dict[str, FrozenFront]) -> str:
    """Markdown provenance table -- what each frozen front was built from.
    Rendered into results/tables/ so the paper can state the front's
    composition rather than leaving a reader to guess it."""
    lines = [
        "| Search space | Front size | Pooled points | Source runs | Run-set digest | Reference point |",
        "|---|---|---|---|---|---|",
    ]
    for space, f in sorted(frozen.items()):
        ref = ", ".join(f"{c:.6g}" for c in f.reference_point)
        lines.append(
            f"| {space} | {len(f.front)} | {f.n_pooled_points} | {f.n_source_runs} | "
            f"`{f.source_run_digest}` | ({ref}) |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Exact oracle front (Category 1 benchmarks only).
# ---------------------------------------------------------------------------


def load_oracle_fronts(directory: Path = DEFAULT_REFERENCE_DIR) -> dict[str, list[Objectives]]:
    """Exact oracle fronts, if any have been built. Keyed by search space,
    in the shape `fixed_budget_summary_table(oracle_fronts=...)` expects
    -- passing one switches that search space from
    hypervolume-relative-to-best-known-front to IGD+."""
    if not directory.exists():
        return {}
    oracles: dict[str, list[Objectives]] = {}
    for path in sorted(directory.glob("oracle__*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        oracles[payload["search_space"]] = [tuple(p) for p in payload["front"]]
    return oracles


def save_oracle_front(
    search_space: str,
    front: Sequence[Objectives],
    *,
    n_enumerated: int,
    n_valid: int,
    directory: Path = DEFAULT_REFERENCE_DIR,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"oracle__{search_space}.json"
    path.write_text(
        json.dumps(
            {
                "search_space": search_space,
                "front": [list(p) for p in front],
                "n_enumerated": n_enumerated,
                "n_valid": n_valid,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def describe_oracle_fronts(directory: Path = DEFAULT_REFERENCE_DIR) -> str:
    """Markdown provenance for every exact oracle front: how many
    configurations were enumerated, how many were valid, how many points
    are nondominated, and each objective's range across the front (the
    normalisation scale igd_plus(normalise=True) uses)."""
    lines = [
        "| Search space | Enumerated | Valid | Front size | f1 min | f1 max | f2 min | f2 max | f2/f1 span ratio |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    if not directory.exists():
        return "\n".join(lines) + "\n"
    for path in sorted(directory.glob("oracle__*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        front = payload["front"]
        f1 = [p[0] for p in front]
        f2 = [p[1] for p in front]
        span1 = max(f1) - min(f1)
        span2 = max(f2) - min(f2)
        ratio = span2 / span1 if span1 else float("nan")
        lines.append(
            f"| {payload['search_space']} | {payload.get('n_enumerated', '')} | "
            f"{payload.get('n_valid', '')} | {len(front)} | {min(f1):.4f} | {max(f1):.4f} | "
            f"{min(f2):.4f} | {max(f2):.4f} | {ratio:.2f} |"
        )
    return "\n".join(lines) + "\n"

