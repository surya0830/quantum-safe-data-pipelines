"""Utility script to regenerate cryptographic micro-benchmark results.

This script is intentionally simple and is meant to support reproducible
experiments for the research paper and notebooks.

It always regenerates stub-based results and *optionally* attempts to
regenerate real-PQC results if a suitable backend is available.

Usage (from the project root):

    python -m scripts.regenerate_crypto_results

The generated files live under ``results/``:

- ``crypto_benchmarks_stub.csv``: always produced, uses educational stubs
  from ``src.crypto.pqc_stubs``.
- ``crypto_benchmarks_real.csv``: produced only if the optional
  ``src.crypto.pqc_real`` backend is available and can access a liboqs/
  pyoqs installation.
"""

from __future__ import annotations

from pathlib import Path

from src.benchmarks.crypto_benchmarks import write_results_csv


def main() -> None:
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    stub_path = results_dir / "crypto_benchmarks_stub.csv"
    print(f"[INFO] Regenerating stub-based crypto benchmarks -> {stub_path}")
    write_results_csv(stub_path, use_real_pqc=False)

    real_path = results_dir / "crypto_benchmarks_real.csv"
    try:
        print(f"[INFO] Attempting to regenerate real-PQC crypto benchmarks -> {real_path}")
        write_results_csv(real_path, use_real_pqc=True)
    except Exception as e:
        print("[WARN] Real PQC backend not available; skipping real-PQC results.")
        print(f"       Reason: {e}")


if __name__ == "__main__":
    main()
