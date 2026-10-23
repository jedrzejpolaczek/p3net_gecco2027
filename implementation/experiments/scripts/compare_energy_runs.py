"""BM-2 pilot / quality control: agreement of two measurement runs of the same
architectures (tags in one JSONL written by measure_nb201_energy.py).

Pass criterion (benchmarks.md, fixed before the pilot): Spearman >= 0.95 and
median relative difference <= 3 %.

    vendor/energy-env/.venv/Scripts/python.exe scripts/compare_energy_runs.py \
        results/energy/nb201_energy.jsonl pilot-run1 pilot-run2
"""

from __future__ import annotations

import json
import statistics
import sys


def ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=xs.__getitem__)
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def pearson(a: list[float], b: list[float]) -> float:
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return cov / (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5


def corrected(records: list[dict]) -> dict[str, float]:
    """Energy relative to the reference cell, linearly interpolated (by measurement
    order) between the reference measurements around each record. Records of a run
    without reference measurements are returned raw (in joules)."""
    refs = sorted((r["seq"], r["energy_j"]) for r in records if r.get("reference"))
    out = {}
    for r in records:
        if r.get("reference"):
            continue
        if len(refs) < 2:
            out[r["arch"]] = r["energy_j"]
            continue
        s = r["seq"]
        lo = max((x for x in refs if x[0] < s), default=refs[0])
        hi = min((x for x in refs if x[0] > s), default=refs[-1])
        w = 0.0 if hi[0] == lo[0] else (s - lo[0]) / (hi[0] - lo[0])
        out[r["arch"]] = r["energy_j"] / (lo[1] + w * (hi[1] - lo[1]))
    return out


def main() -> None:
    path, tag1, tag2 = sys.argv[1:4]
    raw = "--raw" in sys.argv
    recs: dict[str, list[dict]] = {tag1: [], tag2: []}
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if r["tag"] in recs:
            recs[r["tag"]].append(r)
    if raw:
        runs = {t: {r["arch"]: r["energy_j"] for r in rs if not r.get("reference")} for t, rs in recs.items()}
    else:
        runs = {t: corrected(rs) for t, rs in recs.items()}
    print("values:", "raw joules" if raw else "relative to the reference cell (drift-corrected)")
    common = sorted(set(runs[tag1]) & set(runs[tag2]))
    if len(common) < 3:
        sys.exit(f"too few architectures measured under both tags: {tag1}={len(runs[tag1])}, "
                 f"{tag2}={len(runs[tag2])}, common={len(common)}")
    a = [runs[tag1][k] for k in common]
    b = [runs[tag2][k] for k in common]
    rho = pearson(ranks(a), ranks(b))
    rel = statistics.median(abs(x - y) / ((x + y) / 2) for x, y in zip(a, b))
    ok = rho >= 0.95 and rel <= 0.03
    print(f"architectures: {len(common)}")
    print(f"Spearman: {rho:.4f}  (>= 0.95)")
    print(f"median relative difference: {100 * rel:.2f} %  (<= 3 %)")
    print("PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
