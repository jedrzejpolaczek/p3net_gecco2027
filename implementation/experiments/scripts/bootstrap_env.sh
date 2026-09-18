#!/usr/bin/env bash
# Build both Python environments this project needs, on a fresh Linux (or
# macOS) machine. Idempotent: safe to re-run.
#
#   1. uv (installed to ~/.local/bin if missing)
#   2. the main environment from uv.lock (Python 3.13, CPU-only PyTorch here)
#   3. the JAHS-Bench-201 query bridge: its own Python 3.10 environment with
#      jahs-bench 1.1.0, which cannot coexist with the main one (it pins
#      scikit-learn<1.1.0)
#
# Run from implementation/experiments:
#     bash scripts/bootstrap_env.sh
#
# Benchmark data is NOT downloaded here -- see scripts/download_data.py and
# notes/plans/v004-cloud-run.md.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "== installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv --version

echo "== main environment (uv.lock)"
uv sync --extra dev

echo "== JAHS-Bench-201 bridge environment (Python 3.10, jahs-bench 1.1.0)"
BRIDGE=vendor/jahsbench-env
if [ ! -x "$BRIDGE/.venv/bin/python" ]; then
  uv venv --python 3.10 "$BRIDGE/.venv"
fi
# setuptools is listed explicitly: `uv venv` does not install it (unlike
# python -m venv), and xgboost 1.5.2 imports pkg_resources, which ships with
# setuptools. Pinned below 81, the release that removes pkg_resources.
VIRTUAL_ENV="$BRIDGE/.venv" uv pip install --python "$BRIDGE/.venv/bin/python" \
  "setuptools<81" "jahs-bench==1.1.0" "xgboost==1.5.2" "scikit-learn==1.0.2" \
  "pandas==1.3.5" "numpy==1.26.4"

echo "== versions"
uv run python -c "import sys, torch; print('main', sys.version.split()[0], 'torch', torch.__version__)"
"$BRIDGE/.venv/bin/python" -c "import sys, jahs_bench; print('bridge', sys.version.split()[0], 'jahs_bench', jahs_bench.__version__ if hasattr(jahs_bench, '__version__') else '1.1.0')"

cat <<'EOF'

Environments ready. Next:
  uv run python scripts/download_data.py     # FCNet + JAHS surrogates
  # copy data/cache/nashpobench2 and data/cache/nats_bench from a machine
  # that has them (Google Drive only) -- see notes/plans/v004-cloud-run.md
  uv run python scripts/check_data.py        # one real query per benchmark
  bash scripts/run_pipeline.sh --workers 8   # the experiments
EOF
