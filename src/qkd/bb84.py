"""Simplified BB84 QKD simulation.

This module simulates:
- Preparation of qubits in random bases
- Measurement by Bob
- Basis reconciliation
- Estimation of quantum bit error rate (QBER)
- Optional eavesdropper (Eve) performing intercept-resend

We abstract away actual quantum state evolution and instead
use classical random variables approximating measurement
statistics.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class BB84RunResult:
    raw_key_alice: List[int]
    raw_key_bob: List[int]
    sifted_key_alice: List[int]
    sifted_key_bob: List[int]
    qber: float
    eavesdropped: bool


def simulate_bb84(num_bits: int = 1024, eavesdrop: bool = False, seed: int | None = None) -> BB84RunResult:
    if seed is not None:
        random.seed(seed)

    alice_bits = [random.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [random.randint(0, 1) for _ in range(num_bits)]  # 0 = Z, 1 = X
    bob_bases = [random.randint(0, 1) for _ in range(num_bits)]

    # Eve's bases if she exists
    eve_bases = [random.randint(0, 1) for _ in range(num_bits)] if eavesdrop else [None] * num_bits

    transmitted_bits = []
    for i in range(num_bits):
        bit = alice_bits[i]
        basis = alice_bases[i]

        if eavesdrop:
            if eve_bases[i] == basis:
                intercepted_bit = bit
            else:
                intercepted_bit = random.randint(0, 1)
            transmitted_bits.append(intercepted_bit)
        else:
            transmitted_bits.append(bit)

    bob_bits = []
    for i in range(num_bits):
        if bob_bases[i] == alice_bases[i]:
            bob_bits.append(transmitted_bits[i])
        else:
            bob_bits.append(random.randint(0, 1))

    sifted_alice, sifted_bob = [], []
    for i in range(num_bits):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_bits[i])

    errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    qber = errors / len(sifted_alice) if sifted_alice else math.nan

    return BB84RunResult(
        raw_key_alice=alice_bits,
        raw_key_bob=bob_bits,
        sifted_key_alice=sifted_alice,
        sifted_key_bob=sifted_bob,
        qber=qber,
        eavesdropped=eavesdrop,
    )
