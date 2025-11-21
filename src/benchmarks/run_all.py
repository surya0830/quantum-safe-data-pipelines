from __future__ import annotations

from .crypto_benchmarks import run_crypto_benchmarks, format_results_table
from .spark_pipeline import run_spark_pipeline


def main() -> None:
    # Stub-based PQC benchmarks (default, always available)
    crypto_results_stub = run_crypto_benchmarks(use_real_pqc=False)
    print("Crypto benchmark results (PQC = educational stubs):")
    print(format_results_table(crypto_results_stub))

    # Optional real PQC backend benchmarks, if available
    try:
        crypto_results_real = run_crypto_benchmarks(use_real_pqc=True)
    except Exception as e:
        print("\n[INFO] Real PQC backend not available or failed; skipping real PQC benchmarks.")
        print(f"Reason: {e}")
    else:
        print("\nCrypto benchmark results (PQC = real backend via liboqs/pyoqs):")
        print(format_results_table(crypto_results_real))

    # Spark pipeline benchmarks (may not be configured in all environments)
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
