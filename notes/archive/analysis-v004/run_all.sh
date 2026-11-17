#!/bin/sh
# Exploratory v004 analysis end to end. Usage: V004_OUT=<dir outside the repo> sh run_all.sh
# Extraction reads ~19 GB of raw JSON in parallel (about 1-2 min on 16 cores); the rest takes under a minute.
set -e
: "${V004_OUT:?set V004_OUT to a directory outside the repo}"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PY="${PY:-$REPO/implementation/experiments/.venv/Scripts/python.exe}"
RUNS="$REPO/implementation/experiments/results/runs"
mkdir -p "$V004_OUT"
export V004_OUT
"$PY" -I "$HERE/extract.py" "$RUNS/b4d25cac/raw" "$V004_OUT/runs.pkl"
"$PY" -I "$HERE/extract.py" "$RUNS/gp-small/raw" "$V004_OUT/runs_gp.pkl"
"$PY" -I "$HERE/analyze.py"
"$PY" -I "$HERE/timing.py"
"$PY" -I "$HERE/ladder.py"
"$PY" -I "$HERE/summaries.py" > "$V004_OUT/summaries.txt"
echo "done: $V004_OUT"
