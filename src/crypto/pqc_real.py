"""Optional bindings to real PQC implementations (e.g., via liboqs / pyoqs).

This module is intentionally thin and optional. It mirrors the high-level
API shape of ``pqc_stubs`` but delegates to standards-compliant
implementations when available.

By default, this module tries to import ``oqs`` (the Python bindings for
liboqs). If the import fails, the ``available`` flag is set to ``False`` and
all functions will raise ``RuntimeError`` when called.

This keeps the core research codebase free of hard dependencies on PQC
libraries, while allowing users who have installed such libraries locally
(e.g., via Homebrew + pip on macOS) to obtain realistic benchmarks.

NOTE: This is a convenience wrapper for experimentation only. For
production use, applications should integrate directly with supported PQC
libraries, follow their documentation carefully, and track upstream
security advisories.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

try:  # optional dependency
    import oqs  # type: ignore
except Exception:  # pragma: no cover - environment-dependent
    oqs = None


available: bool = oqs is not None


@dataclass
class KEMKeyPair:
    public_key: bytes
    private_key: bytes


@dataclass
class SignatureKeyPair:
    public_key: bytes
    private_key: bytes


def _require_available() -> None:
    if not available:
        raise RuntimeError(
            "Real PQC backend not available: install 'oqs' (pyoqs/liboqs) and its "
            "native dependencies, or use 'src.crypto.pqc_stubs' instead."
        )


# --- Kyber KEM ---


def kyber_generate_keypair(security_level: str = "Kyber768") -> KEMKeyPair:
    """Generate a Kyber keypair using liboqs/pyoqs, if available.

    ``security_level`` should match one of the Kyber variants exposed by
    liboqs (e.g., "Kyber512", "Kyber768", "Kyber1024").
    """

    _require_available()
    with oqs.KeyEncapsulation(security_level) as kem:  # type: ignore[union-attr]
        public_key = kem.generate_keypair()
        private_key = kem.export_secret_key()
    return KEMKeyPair(public_key=public_key, private_key=private_key)


def kyber_encapsulate(public_key: bytes, security_level: str = "Kyber768") -> Tuple[bytes, bytes]:
    """Encapsulate a shared secret to ``public_key`` using Kyber via liboqs."""

    _require_available()
    with oqs.KeyEncapsulation(security_level) as kem:  # type: ignore[union-attr]
        ciphertext, shared_secret = kem.encap_secret(public_key)
    return shared_secret, ciphertext


def kyber_decapsulate(private_key: bytes, ciphertext: bytes, security_level: str = "Kyber768") -> bytes:
    """Decapsulate a Kyber ciphertext using the given private key."""

    _require_available()
    with oqs.KeyEncapsulation(security_level, secret_key=private_key) as kem:  # type: ignore[union-attr]
        shared_secret = kem.decap_secret(ciphertext)
    return shared_secret


# --- Signatures (Dilithium / SPHINCS+) ---


def dilithium_generate_keypair(algorithm: str = "Dilithium3") -> SignatureKeyPair:
    """Generate a Dilithium keypair using liboqs/pyoqs.

    ``algorithm`` should be one of the Dilithium variants supported by
    liboqs (e.g., "Dilithium2", "Dilithium3", "Dilithium5").
    """

    _require_available()
    with oqs.Signature(algorithm) as sig:  # type: ignore[union-attr]
        public_key = sig.generate_keypair()
        private_key = sig.export_secret_key()
    return SignatureKeyPair(public_key=public_key, private_key=private_key)


def dilithium_sign(private_key: bytes, message: bytes, algorithm: str = "Dilithium3") -> bytes:
    _require_available()
    with oqs.Signature(algorithm) as sig:  # type: ignore[union-attr]
        sig.import_secret_key(private_key)
        return sig.sign(message)


def dilithium_verify(public_key: bytes, message: bytes, signature: bytes, algorithm: str = "Dilithium3") -> bool:
    _require_available()
    with oqs.Signature(algorithm) as sig:  # type: ignore[union-attr]
        return sig.verify(message, signature, public_key)


def sphincs_generate_keypair(algorithm: str = "SPHINCS+-SHA2-128f-robust") -> SignatureKeyPair:
    """Generate a SPHINCS+ keypair using liboqs/pyoqs.

    The default algorithm name follows typical liboqs naming, but users
    should check ``oqs.get_enabled_sig_mechanisms()`` to see what is
    available in their build.
    """

    _require_available()
    with oqs.Signature(algorithm) as sig:  # type: ignore[union-attr]
        public_key = sig.generate_keypair()
        private_key = sig.export_secret_key()
    return SignatureKeyPair(public_key=public_key, private_key=private_key)


def sphincs_sign(private_key: bytes, message: bytes, algorithm: str = "SPHINCS+-SHA2-128f-robust") -> bytes:
    _require_available()
    with oqs.Signature(algorithm) as sig:  # type: ignore[union-attr]
        sig.import_secret_key(private_key)
        return sig.sign(message)


def sphincs_verify(public_key: bytes, message: bytes, signature: bytes, algorithm: str = "SPHINCS+-SHA2-128f-robust") -> bool:
    _require_available()
    with oqs.Signature(algorithm) as sig:  # type: ignore[union-attr]
        return sig.verify(message, signature, public_key)
