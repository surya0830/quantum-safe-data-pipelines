from __future__ import annotations

from .crypto_benchmarks import run_crypto_benchmarks, format_results_table
from .spark_pipeline import run_spark_pipeline


def main() -> None:
    crypto_results = run_crypto_benchmarks()
    print("Crypto benchmark results (approximate, stub-based for PQC):")
    print(format_results_table(crypto_results))

    try:
        classical = run_spark_pipeline(records=200_000, pqc=False)
        pqc = run_spark_pipeline(records=200_000, pqc=True)
        print("\nSpark pipeline throughput (smaller is better):")
        print(f"Classical AES-like: {classical.duration_s:.3f} s for {classical.records} records")
        print(f"PQC-style: {pqc.duration_s:.3f} s for {pqc.records} records")
    except Exception as e:  # Spark may not be configured
        print("\n[WARN] Spark benchmark failed; ensure PySpark is configured.")
        print(e)


if __name__ == "__main__":
    main()
