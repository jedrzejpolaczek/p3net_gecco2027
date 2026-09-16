"""Fetch the benchmark data caches this project needs, into data/cache/.

  fcnet                 FCNet, from Syne Tune's mirror (SHA-256 verified)
  jahs_bench_201        JAHS-Bench-201 surrogate models, from the authors'
                        server (assembled_surrogates.tar, ~1.6 GB)
  nas_hpo_bench_ii      not automated: the dataset is published on Google
  nats_bench            Drive only, and those links need a browser or gdown
                        with a file id that the packages do not embed

The two manual ones are also the two smallest to copy from a machine that
already has them, which is what the cloud runbook recommends for all four
(notes/plans/v004-cloud-run.md): copying the exact bytes that produced the
local results avoids any chance of a different dataset version.

Usage (from implementation/experiments):
    uv run python scripts/download_data.py            # everything automated
    uv run python scripts/download_data.py --only fcnet
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

CACHE = EXPERIMENTS_ROOT / "data" / "cache"
JAHS_SURROGATE_URL = (
    "https://ml.informatik.uni-freiburg.de/research-artifacts/"
    "jahs_bench_201/v1.1.0/assembled_surrogates.tar"
)
#: Benchmarks published on Google Drive only -> copy them from a machine that
#: has them (see the module docstring).
MANUAL = {
    "nas_hpo_bench_ii": CACHE / "nashpobench2",
    "nats_bench": CACHE / "nats_bench",
}


def fetch_fcnet() -> int:
    from scripts.download_fcnet import main as fcnet_main

    return fcnet_main()


def fetch_jahs() -> int:
    target = CACHE / "jahs_bench_201"
    if (target / "assembled_surrogates").exists():
        print(f"jahs_bench_201: already present in {target}")
        return 0
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "assembled_surrogates.tar"
        print(f"downloading {JAHS_SURROGATE_URL}", flush=True)
        with (
            urllib.request.urlopen(JAHS_SURROGATE_URL, timeout=120) as response,
            open(archive, "wb") as handle,
        ):
            shutil.copyfileobj(response, handle, length=2**20)
        print("extracting", flush=True)
        with tarfile.open(archive) as tar:
            tar.extractall(target, filter="data")
    print(f"jahs_bench_201: ready in {target}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["fcnet", "jahs_bench_201"], default=None)
    args = parser.parse_args(argv)

    status = 0
    for name, fetch in (("fcnet", fetch_fcnet), ("jahs_bench_201", fetch_jahs)):
        if args.only in (None, name):
            status |= fetch()

    for name, path in MANUAL.items():
        if path.exists() and any(path.iterdir()):
            print(f"{name}: present in {path}")
        else:
            print(
                f"{name}: MISSING in {path} -- not downloadable from here "
                "(Google Drive only); copy it from a machine that has it, see "
                "notes/plans/v004-cloud-run.md"
            )
            status |= 1
    return status


if __name__ == "__main__":
    sys.exit(main())
