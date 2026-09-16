#!/usr/bin/env bash
# Crash-safe wrapper around scripts/run_pipeline.py -- the Linux/macOS
# counterpart of scripts/run_pipeline.ps1.
#
# Run from implementation/experiments:
#     bash scripts/run_pipeline.sh                      # everything, plan order
#     bash scripts/run_pipeline.sh --dry-run            # counts and preflight
#     bash scripts/run_pipeline.sh --workers 8
#     bash scripts/run_pipeline.sh --shard 0/3          # this machine's third
#     nohup bash scripts/run_pipeline.sh --workers 8 > pipeline.log 2>&1 &
#
# Every argument is passed through to run_pipeline.py (--stages, --shard,
# --workers, --status-every, --unlock-after, ...).
#
# Resuming: run the same command again. Completed runs are kept and validated;
# only missing, truncated or failed runs are re-run.
#
# If the Python process itself dies (out-of-memory killer, crash), this wrapper
# starts it again, up to MAX_RESTARTS times (default 20, override with the
# environment variable). Ctrl+C is not restarted.
set -uo pipefail
cd "$(dirname "$0")/.."

MAX_RESTARTS="${MAX_RESTARTS:-20}"
restarts=0

while true; do
  echo
  echo "=== run_pipeline.py (attempt $((restarts + 1))) ==="
  uv run python scripts/run_pipeline.py "$@"
  code=$?

  case "$code" in
    0)
      echo "All requested stages complete."
      exit 0
      ;;
    1)
      echo "Pipeline refused to start or checks failed -- see above. Not restarting."
      exit 1
      ;;
    2)
      echo "Finished with points remaining (failures, given-up points, or Ctrl+C)."
      echo "See the run root's failures.jsonl; rerun to retry (--retry-failed resets attempts)."
      exit 2
      ;;
    130)
      echo "Interrupted."
      exit 130
      ;;
  esac

  restarts=$((restarts + 1))
  if [ "$restarts" -gt "$MAX_RESTARTS" ]; then
    echo "Process died $restarts times (last exit code $code); giving up. Rerun to resume."
    exit "$code"
  fi
  echo "Process died with exit code $code -- restarting in 30 s and resuming ($restarts/$MAX_RESTARTS)."
  sleep 30
done
