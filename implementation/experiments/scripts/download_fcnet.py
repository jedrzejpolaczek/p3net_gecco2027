"""Download the FCNet tabular benchmark into data/cache/fcnet/ and verify it.

Source and provenance: substrates/fcnet.py module docstring. Every file is
checked against its SHA-256 (Hugging Face LFS object id); a mismatch stops
with an error and the file is not used. Downloads resume after an
interruption. Already verified files are skipped.

Usage (from implementation/experiments):
    uv run python scripts/download_fcnet.py
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
TARGET = EXPERIMENTS_ROOT / "data" / "cache" / "fcnet"
BASE_URL = "https://huggingface.co/datasets/synetune/blackbox-repository/resolve/main/fcnet"

#: file -> sha256 (None: small metadata file without an LFS hash)
FILES: dict[str, str | None] = {
    "objectives_evaluations.npy": (
        "62091c9c878975846cfc7bac02ea28d8b59eada94806097a1e1836f0d1119e58"
    ),
    "hyperparameters.parquet": "9be9c2cb6353c058c12b6f997edc17670bac4f8ae0cc0eb0177805bf6351d027",
    "fidelities_values.npy": "ebb3fd83456b5a2f0c8bafa43de636ea4aee00ccf0ba57b7bebf7919e7250c72",
    "metadata.json": None,
    "configspace.json": None,
    "fidelityspace.json": None,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(2**24), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(name: str) -> None:
    part = TARGET / f"{name}.part"
    start = part.stat().st_size if part.exists() else 0
    request = urllib.request.Request(f"{BASE_URL}/{name}")
    if start:
        request.add_header("Range", f"bytes={start}-")
    with urllib.request.urlopen(request, timeout=120) as response:
        mode = "ab" if start and response.status == 206 else "wb"
        with open(part, mode) as handle:
            while chunk := response.read(2**20):
                handle.write(chunk)
    part.replace(TARGET / name)


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    for name, expected in FILES.items():
        path = TARGET / name
        if not path.exists():
            print(f"downloading {name}", flush=True)
            download(name)
        if expected is not None:
            actual = sha256(path)
            if actual != expected:
                print(f"SHA-256 MISMATCH for {name}: {actual} != {expected}")
                return 1
            print(f"verified {name}")
    print(f"FCNet data ready in {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
