#!/usr/bin/env bash
# A8 status in one command: progress of the three phases (main+MF, Vizier, JAHS posthoc), what is running
# now, memory, failures, and an ETA estimated per method.
#
#   bash scripts/a8_status.sh                 # from implementation/experiments
#   bash scripts/a8_status.sh <run root>      # default: newest results/runs/* holding a v005-resources manifest
#   watch -n 300 bash scripts/a8_status.sh    # refresh every 5 minutes
#   A8_PYTHON=<interpreter> overrides "uv run python" (local testing)
#
# ETA: each pending point is estimated from the median wall time of the same method at the same budget among
# finished points (else the same method at the other budget, scaled by the budget ratio; else the median of
# all finished points at that budget). Running points count with their estimate minus time already spent.
# The sum is divided by the number of workers (6 for main+MF, 1 for Vizier). Early on, few methods have
# finished, so the ETA is rough; it firms up once every method has one point done.
set -uo pipefail
# Run from implementation/experiments, or keep the script there; a copy outside the repo works from that directory.
[ -f scripts/run_pipeline.py ] || cd "$(dirname "$0")/.."
${A8_PYTHON:-uv run --quiet python} - "$@" <<'EOF'
import json, statistics, sys, time
from pathlib import Path

sys.path.insert(0, ".")
from scripts import run_pipeline as rp

PLAN = Path("configs/pipeline/v005-resources.yaml")
PHASES = [("A8 main + MF", ("resources_main", "resources_mf"), 6), ("A8 Vizier", ("resources_vizier",), 1)]
POSTHOC = [("b4d25cac", 28080), ("gp-small", 1080)]


def fmt(sec):
    sec = max(0, int(sec))
    d, h, m = sec // 86400, sec % 86400 // 3600, sec % 3600 // 60
    return f"{d}d {h}h {m:02d}m" if d else f"{h}h {m:02d}m"


def run_root():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    roots = []
    for m in Path("results/runs").glob("*/manifest.json"):
        try:
            if "v005-resources" in json.loads(m.read_text(encoding="utf-8")).get("plan", ""):
                roots.append(m.parent)
        except (OSError, ValueError):
            pass
    return max(roots, key=lambda p: (p / "manifest.json").stat().st_mtime) if roots else None


def wall(path):
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    r = d.get("resources") or d.get("diagnostics", {}).get("resources") or {}
    return r.get("wall_seconds")


root = run_root()
plan = rp.load_plan(PLAN)
stages = {s["name"]: s for s in plan["stages"]}
now = time.time()
print(f"=== A8 status {time.strftime('%Y-%m-%d %H:%M')} ===")
if root is None:
    print("no run root with the v005-resources plan in results/runs/ -- has A8 started?")
else:
    print(f"run root: {root}")
    raw = root / "raw"
    present = {p.name for p in raw.glob("*.json")} if raw.exists() else set()
    locks = {p.stem: now - p.stat().st_mtime for p in (root / "locks").glob("*.lock")
             if not p.name.startswith(("slot-", "jahs-"))} if (root / "locks").exists() else {}
    for title, names, workers in PHASES:
        points = [p for n in names for p in rp.expand_stage(stages[n])]
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

        left, guessed, unknown = 0.0, 0, 0
        running = []
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
        print(f"\n## {title}: {len(done)}/{len(points)} ({pct:.0f}%)")
        if len(done) == len(points):
            print("   done")
            continue
        if running:
            print("   running now:")
            for p, spent, est in sorted(running, key=lambda x: -x[1]):
                tail = f" / ~{fmt(est)} expected" if est else ""
                print(f"     {p.method:24s} {p.search_space:28s} b={p.budget:<4d} {fmt(spent)}{tail}")
        else:
            print("   running now: none (not started yet, or stopped -- see 'process' below)")
        if unknown == len(points) - len(done):
            print("   ETA: not yet (no finished point to estimate from)")
        else:
            note = f"; {guessed} point(s) of methods with no finished run guessed from other methods" if guessed else ""
            note += f"; {unknown} without an estimate" if unknown else ""
            print(f"   ETA: ~{fmt(left / workers)} with {workers} worker(s){note}")
    fails = root / "failures.jsonl"
    n_fail = sum(1 for _ in fails.open(encoding="utf-8")) if fails.exists() else 0
    print(f"\nfailures logged: {n_fail}" + (f"  (tail -3 {fails})" if n_fail else ""))

print("\n## JAHS posthoc (after A8)")
for name, total in POSTHOC:
    d = Path("results/runs") / name / "posthoc"
    files = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime) if d.exists() else []
    line = f"   {name}: {len(files)}/{total}"
    if 20 <= len(files) < total:
        recent = files[-200:]
        rate = (len(recent) - 1) / max(recent[-1].stat().st_mtime - recent[0].stat().st_mtime, 1e-9)
        line += f", {rate * 60:.0f} files/min, ETA ~{fmt((total - len(files)) / rate)}"
    elif len(files) >= total:
        line += " done"
    print(line)
EOF

echo
echo "## process"
if pgrep -f "run_pipeline.py|posthoc_metrics.py" > /dev/null; then
  pgrep -af "run_pipeline.py --plan|posthoc_metrics.py" | grep -v -- "--worker" | cut -c1-150 | sed 's/^/   /'
  echo "   workers: $(pgrep -fc -- "run_pipeline.py --worker")"
else
  echo "   nothing running"
fi
free -g | awk 'NR==2 {print "   RAM: " $3 " GB used, " $7 " GB available of " $2 " GB"}'
df -h . | awk 'NR==2 {print "   disk: " $4 " free of " $2}'
for f in ~/a8_main.log ~/a8_vizier.log ~/posthoc_jahs.log; do
  [ -f "$f" ] && echo "   last line of $f: $(tail -n 1 "$f" | cut -c1-140)"
done
