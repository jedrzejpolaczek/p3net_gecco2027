#!/usr/bin/env bash
# v005 run status in one command: progress of both parts (v005.yaml: main, gp, elympus, mf; v005-vizier.yaml),
# what is running now and for how long, ETA per part, failures, RAM, disk, last log lines.
#
#   bash scripts/v005_status.sh                  # from implementation/experiments
#   watch -n 600 bash scripts/v005_status.sh     # refresh every 10 minutes (Ctrl+C ends the view, not the run)
#   V005_PYTHON=<interpreter> overrides "uv run python" (local testing)
#
# Run roots are found by their manifest (newest one per plan). ETA: each pending point is estimated from the
# median wall time of the same method at the same budget among finished points (else the same method at
# another budget, scaled by the budget ratio; else the median of all finished points at that budget), summed
# and divided by the part's worker count. Rough until every method has one finished point.
set -uo pipefail
[ -f scripts/run_pipeline.py ] || cd "$(dirname "$0")/.."
${V005_PYTHON:-uv run --quiet python} - "$@" <<'EOF'
import json, statistics, sys, time
from pathlib import Path

sys.path.insert(0, ".")
from scripts import run_pipeline as rp

PARTS = [("v005 main + gp + elympus + mf", "configs/pipeline/v005.yaml", ("main", "gp", "elympus", "mf"), 6),
         ("v005 Vizier", "configs/pipeline/v005-vizier.yaml", ("vizier",), 1)]


def fmt(sec):
    sec = max(0, int(sec))
    d, h, m = sec // 86400, sec % 86400 // 3600, sec % 3600 // 60
    return f"{d}d {h}h {m:02d}m" if d else f"{h}h {m:02d}m"


def run_root(plan_path):
    roots = []
    for m in Path("results/runs").glob("*/manifest.json"):
        try:
            if Path(json.loads(m.read_text(encoding="utf-8")).get("plan", "")).name == Path(plan_path).name:
                roots.append(m.parent)
        except (OSError, ValueError):
            pass
    return max(roots, key=lambda p: (p / "manifest.json").stat().st_mtime) if roots else None


def wall(path):
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for r in (d.get("diagnostics", {}).get("resources") or {}, d.get("resources") or {}):
        if r.get("wall_seconds") is not None:
            return r["wall_seconds"]
    return None


now = time.time()
print(f"=== v005 status {time.strftime('%Y-%m-%d %H:%M')} ===")
for title, plan_path, names, workers in PARTS:
    root = run_root(plan_path)
    plan = rp.load_plan(Path(plan_path))
    stages = {s["name"]: s for s in plan["stages"]}
    points = [p for n in names for p in rp.expand_stage(stages[n])]
    if root is None:
        print(f"\n## {title}: not started (no run root with {Path(plan_path).name}), {len(points)} points")
        continue
    raw = root / "raw"
    present = {p.name for p in raw.glob("*.json")} if raw.exists() else set()
    locks = {p.stem: now - p.stat().st_mtime for p in (root / "locks").glob("*.lock")
             if not p.name.startswith(("slot-", "jahs-"))} if (root / "locks").exists() else {}
    done = [p for p in points if p.filename in present]
    times = {}
    for p in done:
        w = wall(raw / p.filename)
        if w is not None:
            times.setdefault((p.method, p.budget), []).append(w)
    by_budget = {}
    for (m, b), ws in times.items():
        by_budget.setdefault(b, []).extend(ws)

    def estimate(p):
        if (p.method, p.budget) in times:
            return statistics.median(times[(p.method, p.budget)]), True
        for (m, b), ws in times.items():
            if m == p.method:
                return statistics.median(ws) * p.budget / b, True
        pool = by_budget.get(p.budget) or [w for ws in by_budget.values() for w in ws]
        return (statistics.median(pool) if pool else None), False

    left, guessed, unknown, running = 0.0, 0, 0, []
    for p in points:
        if p.filename in present:
            continue
        est, own = estimate(p)
        spent = locks.get(p.key)
        if spent is not None:
            running.append((p, spent, est))
        if est is None:
            unknown += 1
            continue
        guessed += not own
        left += max(est - (spent or 0.0), 0.0)
    pct = 100 * len(done) / len(points) if points else 0
    print(f"\n## {title}: {len(done)}/{len(points)} ({pct:.1f}%)   run root: {root}")
    per_stage = {n: sum(1 for p in done if p.stage == n) for n in names}
    totals = {n: sum(1 for p in points if p.stage == n) for n in names}
    print("   stages: " + ", ".join(f"{n} {per_stage[n]}/{totals[n]}" for n in names))
    fails = root / "failures.jsonl"
    n_fail = sum(1 for _ in fails.open(encoding="utf-8")) if fails.exists() else 0
    print(f"   failures logged: {n_fail}" + (f"  (tail -3 {fails})" if n_fail else ""))
    if len(done) == len(points):
        print("   done")
        continue
    if running:
        print("   running now:")
        for p, spent, est in sorted(running, key=lambda x: -x[1]):
            tail = f" / ~{fmt(est)} expected" if est else ""
            print(f"     {p.method:24s} {p.search_space:34s} b={p.budget:<4d} s={p.seed:<3d} {fmt(spent)}{tail}")
    else:
        print("   running now: none (not started yet, or stopped -- see 'process' below)")
    if unknown == len(points) - len(done):
        print("   ETA: not yet (no finished point to estimate from)")
    else:
        note = f"; {guessed} point(s) guessed from other methods" if guessed else ""
        note += f"; {unknown} without an estimate" if unknown else ""
        print(f"   ETA: ~{fmt(left / workers)} with {workers} worker(s){note}")
EOF

echo
echo "## process"
if pgrep -f "run_pipeline.py" > /dev/null; then
  pgrep -af "run_pipeline.py --plan" | grep -v -- "--worker" | cut -c1-150 | sed 's/^/   /'
  echo "   workers: $(pgrep -fc -- "run_pipeline.py --worker")"
else
  echo "   nothing running"
fi
free -g | awk 'NR==2 {print "   RAM: " $3 " GB used, " $7 " GB available of " $2 " GB"}'
df -h . | awk 'NR==2 {print "   disk: " $4 " free of " $2}'
for f in ~/v005_main.log ~/v005_vizier.log; do
  [ -f "$f" ] && echo "   last line of $f: $(tail -n 1 "$f" | cut -c1-140)"
done
