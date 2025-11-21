"""Educational stubs for NIST PQC algorithms (Kyber, Dilithium, SPHINCS+).

These DO NOT implement the real algorithms and must not be used for
production security. They emulate performance characteristics and API
shapes so we can benchmark data engineering pipelines under PQC-like
constraints without depending on specialized native libraries.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple


@dataclass
class KEMKeyPair:
    public_key: bytes
    private_key: bytes


def kyber_generate_keypair(security_level: str = "kyber768") -> KEMKeyPair:
    # Simulate key sizes (approximate, not exact)
    sizes = {"kyber512": (800, 1600), "kyber768": (1184, 2400), "kyber1024": (1568, 3168)}
    pk_size, sk_size = sizes.get(security_level, sizes["kyber768"])
    return KEMKeyPair(public_key=os.urandom(pk_size), private_key=os.urandom(sk_size))


def kyber_encapsulate(public_key: bytes) -> Tuple[bytes, bytes]:
    # Simulate shared secret + ciphertext sizes
    shared_secret = os.urandom(32)
    ciphertext = os.urandom(len(public_key))
    return shared_secret, ciphertext


def kyber_decapsulate(private_key: bytes, ciphertext: bytes) -> bytes:
    # In a true implementation this would use both; here we just mock.
    _ = (private_key, ciphertext)
    return os.urandom(32)


@dataclass
class signature_keypair:
    public_key: bytes
    private_key: bytes


def dilithium_generate_keypair(level: str = "dilithium3") -> signature_keypair:
    sizes = {"dilithium2": (1312, 2528), "dilithium3": (1952, 4000), "dilithium5": (2592, 4864)}
    pk_size, sk_size = sizes.get(level, sizes["dilithium3"])
    return signature_keypair(public_key=os.urandom(pk_size), private_key=os.urandom(sk_size))


def dilithium_sign(private_key: bytes, message: bytes) -> bytes:
    _ = (private_key, message)
    return os.urandom(2700)  # rough average signature size


def dilithium_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    _ = (public_key, message, signature)
    # Always succeed in stub
    return True


def sphincs_generate_keypair(level: str = "sphincs+-sha2-128f-robust") -> signature_keypair:
    # Rough sizes, just for overhead estimation
    return signature_keypair(public_key=os.urandom(64), private_key=os.urandom(128))


def sphincs_sign(private_key: bytes, message: bytes) -> bytes:
    _ = (private_key, message)
    return os.urandom(17000)  # SPHINCS+ signatures are large


def sphincs_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    _ = (public_key, message, signature)
    return True
