"""Post-hoc benchmark queries for finished runs, outside the evaluation budget.

For every raw run file, writes `<posthoc dir>/<same file name>` with:
  * "history_metrics": for every evaluated configuration, every accuracy the
    benchmark records at full fidelity (train/valid/test, where recorded)
    and its training time -- the test-set front and the train-validation
    and validation-test gaps are computed from these;
  * "decisions": the run's logged surrogate decisions
    (diagnostics.surrogate_decisions), each labelled with real full-fidelity
    f1 values -- true_f1_reference, true_f1_candidate, true_improvement for
    "improvement" records; true_f1 for "selection" records -- ready for
    measurement/decisions.py.

These queries never influence a run: they happen after it, and the method
never sees them. They are not counted in any budget and are reported as
analysis, not as search cost.

Crash-safe and resumable like scripts/run_pipeline.py: output is written
atomically, existing complete outputs are skipped.

Usage (from implementation/experiments):
    uv run python scripts/posthoc_metrics.py --raw results/runs/<commit>/raw
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

from p3net.problem.genotype import Genotype  # noqa: E402

from scripts import run_experiment  # noqa: E402

POSTHOC_VERSION = 1


def label_decisions(records: list[dict[str, Any]], true_f1) -> list[dict[str, Any]]:
    labelled = []
    for record in records:
        out = dict(record)
        candidate = true_f1(record["candidate"])
        if record["kind"] == "improvement":
            reference = true_f1(record["reference"])
            out["true_f1_reference"] = reference
            out["true_f1_candidate"] = candidate
            out["true_improvement"] = reference - candidate
        else:
            out["true_f1"] = candidate
        labelled.append(out)
    return labelled


def posthoc_for_run(payload: dict[str, Any], substrate: Any) -> dict[str, Any]:
    full = substrate.fidelity_ladder()[-1]
    f1_cache: dict[tuple, float] = {}

    def true_f1(values: list) -> float:
        key = tuple(values)
        if key not in f1_cache:
            f1_cache[key] = substrate.query_f1(Genotype(values=key), full)
        return f1_cache[key]

    history_metrics = [
        substrate.full_fidelity_metrics(Genotype(values=tuple(entry["genotype"])))
        for entry in payload["history"]
    ]
    decisions = payload.get("diagnostics", {}).get("surrogate_decisions")
    return {
        "posthoc_version": POSTHOC_VERSION,
        "method": payload["method"],
        "search_space": payload["search_space"],
        "budget": payload["budget"],
        "seed": payload["seed"],
        "history_metrics": history_metrics,
        "decisions": None
        if decisions is None
        else {
            "offered": decisions["offered"],
            "limit": decisions["limit"],
            "records": label_decisions(decisions["records"], true_f1),
        },
    }


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(data))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _complete(path: Path) -> bool:
    try:
        return (
            json.loads(path.read_text(encoding="utf-8")).get("posthoc_version") == POSTHOC_VERSION
        )
    except (OSError, ValueError):
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True, help="directory of raw run files")
    parser.add_argument("--out", type=Path, default=None, help="default: <raw>/../posthoc")
    args = parser.parse_args(argv)
    out_dir = args.out or args.raw.parent / "posthoc"

    by_space: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(args.raw.glob("*.json")):
        if _complete(out_dir / path.name):
            continue
        by_space[path.name.split("__")[1]].append(path)

    done = 0
    for space_name, paths in by_space.items():
        substrate = run_experiment.build_substrate(
            run_experiment.load_search_space_config(space_name)
        )
        try:
            for path in paths:
                payload = json.loads(path.read_text(encoding="utf-8"))
                _write_atomic(out_dir / path.name, posthoc_for_run(payload, substrate))
                done += 1
                print(f"posthoc {done} {path.name}", flush=True)
        finally:
            close = getattr(substrate, "close", None)
            if callable(close):
                close()
    print(f"posthoc: {done} file(s) written to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
