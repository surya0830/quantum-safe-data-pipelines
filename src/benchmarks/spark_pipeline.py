"""Spark pipeline benchmark with and without PQC-style overhead.

We simulate a data pipeline that encrypts records per-partition.
For PQC, we add artificial CPU and bandwidth overhead to mimic
larger key sizes and more expensive key exchange.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


@dataclass
class SparkPipelineResult:
    mode: str
    records: int
    duration_s: float


def _fake_pqc_overhead(payload: bytes, factor: int = 5) -> bytes:
    return payload * factor


def run_spark_pipeline(records: int = 1_000_000, pqc: bool = False) -> SparkPipelineResult:
    spark = (
        SparkSession.builder.appName("quantum_safe_pipeline_benchmark")
        .master("local[*]")
        .getOrCreate()
    )

    data = [(i, os.urandom(64)) for i in range(records)]
    df = spark.createDataFrame(data, ["id", "payload"])

    if pqc:
        factor = 8

        @F.udf("binary")
        def pqc_encrypt_udf(col):
            return _fake_pqc_overhead(col, factor)

        transform = df.withColumn("ciphertext", pqc_encrypt_udf("payload"))
    else:
        @F.udf("binary")
        def aes_encrypt_udf(col):
            return col

        transform = df.withColumn("ciphertext", aes_encrypt_udf("payload"))

    t0 = time.perf_counter()
    _ = transform.agg(F.count("ciphertext")).collect()
    t1 = time.perf_counter()

    mode = "pqc" if pqc else "classical"
    duration = t1 - t0

    spark.stop()
    return SparkPipelineResult(mode=mode, records=records, duration_s=duration)
