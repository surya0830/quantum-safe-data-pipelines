from __future__ import annotations

"""Cryptographic micro-benchmarks for classical vs. post-quantum (stub) schemes.

This module provides a small, well-defined set of experiments that can be
reproduced on a single machine without special hardware:

- RSA-2048 (OAEP, SHA-256) encryption+decryption of a short control-sized
  message, modelling key encapsulation or control-plane messages.
- AES-256-GCM encryption+decryption of a bulk payload, modelling data-at-rest
  or data-in-transit encryption at the data-plane.
- Kyber-like KEM keygen + encapsulation + decapsulation, using educational
  stubs that approximate key/ciphertext sizes and CPU cost.
- Dilithium-like signatures (keygen + sign + verify) on bulk payloads.
- SPHINCS+-like signatures (keygen + sign + verify) on bulk payloads.

The PQC primitives are *not* real implementations and MUST NOT be used for
security; they are intentionally simplified to support performance-oriented
pipeline design and academic discussion.
"""

import time
from dataclasses import dataclass
from statistics import mean
from typing import Callable, Dict, List, Optional, Union
from pathlib import Path

from ..crypto.classical import (
    generate_rsa_keypair,
    rsa_encrypt,
    rsa_decrypt,
    aes_gcm_encrypt,
    aes_gcm_decrypt,
)
from ..crypto.pqc_stubs import (
    kyber_generate_keypair as kyber_generate_keypair_stub,
    kyber_encapsulate as kyber_encapsulate_stub,
    kyber_decapsulate as kyber_decapsulate_stub,
    dilithium_generate_keypair as dilithium_generate_keypair_stub,
    dilithium_sign as dilithium_sign_stub,
    dilithium_verify as dilithium_verify_stub,
    sphincs_generate_keypair as sphincs_generate_keypair_stub,
    sphincs_sign as sphincs_sign_stub,
    sphincs_verify as sphincs_verify_stub,
)

try:
    from ..crypto import pqc_real
except Exception:  # pragma: no cover - optional dependency
    pqc_real = None


@dataclass
class TimingResult:
    """Simple container for timing samples from a micro-benchmark.

    Only the mean is used in the paper, but the raw samples are preserved so
    that additional statistics (e.g., median, standard deviation) can be
    computed in notebooks or downstream analysis code.
    """

    name: str
    samples: List[float]

    @property
    def avg_ms(self) -> float:
        """Average latency in milliseconds."""

        return mean(self.samples) * 1000


def _time_function(fn: Callable[[], None], repeats: int = 10) -> TimingResult:
    """Measure wall-clock time for a side-effecting callable.

    The callable is assumed to be deterministic enough that averaging over a
    modest number of repetitions is meaningful for coarse-grained
    cryptographic latency comparisons.
    """

    samples: List[float] = []
    name = getattr(fn, "__name__", "unknown")
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        samples.append(t1 - t0)
    return TimingResult(name=name, samples=samples)


def run_crypto_benchmarks(
    message_sizes: Optional[List[int]] = None,
    repeats: int = 5,
    use_real_pqc: bool = False,
) -> Dict[str, TimingResult]:
    """Run a fixed suite of crypto micro-benchmarks.

    Parameters
    ----------
    message_sizes:
        Logical payload sizes (in bytes) used to select the maximum bulk
        message length for symmetric and PQC-style operations. RSA always uses
        a small, fixed-size message that is safe for RSA-2048 with OAEP.
    repeats:
        Number of repetitions per benchmarked function.
    use_real_pqc:
        If ``True``, and if ``src.crypto.pqc_real`` is available and
        successfully imported, run KEM/signature benchmarks against the real
        backend instead of the educational stubs. If the real backend is not
        available, a ``RuntimeError`` is raised.

    Returns
    -------
    Dict[str, TimingResult]
        Mapping from human-readable benchmark labels to timing results.
    """

    if message_sizes is None:
        message_sizes = [128, 1024, 8192]

    results: Dict[str, TimingResult] = {}

    # RSA: operate on a small control-sized payload to avoid OAEP size limits.
    rsa_kp = generate_rsa_keypair(2048)
    rsa_message = b"0" * 190

    def rsa_enc_dec() -> None:
        ct = rsa_encrypt(rsa_kp.public_key, rsa_message)
        _ = rsa_decrypt(rsa_kp.private_key, ct)

    results["rsa_oaep_2048_encrypt_decrypt"] = _time_function(rsa_enc_dec, repeats=repeats)

    # Bulk message size for symmetric and PQC-style operations.
    import os

    max_len = max(message_sizes)
    bulk_message = b"0" * max_len
    key = os.urandom(32)

    def aes_gcm_round() -> None:
        iv, ct, tag = aes_gcm_encrypt(key, bulk_message)
        _ = aes_gcm_decrypt(key, iv, ct, tag)

    results["aes_gcm_256_encrypt_decrypt"] = _time_function(aes_gcm_round, repeats=repeats)

    # Select backend for PQC-style operations.
    if use_real_pqc:
        if pqc_real is None or not getattr(pqc_real, "available", False):
            raise RuntimeError(
                "use_real_pqc=True but real PQC backend is not available. "
                "Install 'oqs' (pyoqs/liboqs) and ensure 'src.crypto.pqc_real' "
                "can import it, or run with use_real_pqc=False."
            )

        kyber_gen = pqc_real.kyber_generate_keypair
        kyber_enc = pqc_real.kyber_encapsulate
        kyber_dec = pqc_real.kyber_decapsulate

        dilithium_gen = pqc_real.dilithium_generate_keypair
        dilithium_sig = pqc_real.dilithium_sign
        dilithium_ver = pqc_real.dilithium_verify

        sphincs_gen = pqc_real.sphincs_generate_keypair
        sphincs_sig = pqc_real.sphincs_sign
        sphincs_ver = pqc_real.sphincs_verify

        label_suffix = "_real"
    else:
        kyber_gen = kyber_generate_keypair_stub
        kyber_enc = kyber_encapsulate_stub
        kyber_dec = kyber_decapsulate_stub

        dilithium_gen = dilithium_generate_keypair_stub
        dilithium_sig = dilithium_sign_stub
        dilithium_ver = dilithium_verify_stub

        sphincs_gen = sphincs_generate_keypair_stub
        sphincs_sig = sphincs_sign_stub
        sphincs_ver = sphincs_verify_stub

        label_suffix = "_stub"

    def kyber_kem_round() -> None:
        kp = kyber_gen()
        ss, ct = kyber_enc(kp.public_key)
        _ = kyber_dec(kp.private_key, ct)
        _ = ss

    results[f"kyber_kem_keygen_encap_decap{label_suffix}"] = _time_function(kyber_kem_round, repeats=repeats)

    def dilithium_sig_round() -> None:
        kp = dilithium_gen()
        sig = dilithium_sig(kp.private_key, bulk_message)
        _ = dilithium_ver(kp.public_key, bulk_message, sig)

    results[f"dilithium_sign_verify{label_suffix}"] = _time_function(dilithium_sig_round, repeats=repeats)

    def sphincs_sig_round() -> None:
        kp = sphincs_gen()
        sig = sphincs_sig(kp.private_key, bulk_message)
        _ = sphincs_ver(kp.public_key, bulk_message, sig)

    results[f"sphincs_sign_verify{label_suffix}"] = _time_function(sphincs_sig_round, repeats=repeats)

    return results


def format_results_table(results: Dict[str, TimingResult]) -> str:
    """Return a minimal CSV-style string for inclusion in the paper/notebooks."""

    lines = ["Algorithm,Avg Latency (ms)"]
    for name, res in results.items():
        lines.append(f"{name},{res.avg_ms:.3f}")
    return "\n".join(lines)


def write_results_csv(path: Union[str, Path], message_sizes: Optional[List[int]] = None, repeats: int = 5, use_real_pqc: bool = False) -> None:
    """Run crypto benchmarks and write results to a CSV file.

    The file will contain the same header and rows as ``format_results_table``.
    Parent directories of ``path`` are created if they do not already exist.

    Parameters
    ----------
    path:
        Destination file path. May be a string or :class:`pathlib.Path`.
    message_sizes:
        Optional list of candidate message sizes for the AES/PQC-style
        benchmarks. If ``None``, the default sizes in ``run_crypto_benchmarks``
        are used.
    repeats:
        Number of repetitions per benchmark.
    use_real_pqc:
        If ``True``, and if ``src.crypto.pqc_real`` is available and
        successfully imported, run KEM/signature benchmarks against the real
        backend instead of the educational stubs. If the real backend is not
        available, a ``RuntimeError`` is raised.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results = run_crypto_benchmarks(message_sizes=message_sizes, repeats=repeats, use_real_pqc=use_real_pqc)
    csv_text = format_results_table(results)
    output_path.write_text(csv_text + "\n", encoding="utf-8")
