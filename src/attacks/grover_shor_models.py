"""Analytical models for Grover's and Shor's algorithm impacts.

We do not simulate full quantum circuits; instead, we provide
complexity-based estimators for:
- Effective security level of symmetric keys under Grover
- Bit-length requirements for post-quantum symmetric security
- Break feasibility for RSA/ECC under Shor
"""

from __future__ import annotations

import math


def effective_symmetric_security_bits(classical_bits: int) -> int:
    """Return approximate security bits under Grover.

    Grover yields a quadratic speedup, effectively halving the
    exponent of brute-force search. So a k-bit key offers roughly
    k/2 bits of security.
    """

    return classical_bits // 2


def required_classical_bits_for_post_quantum(target_security_bits: int) -> int:
    """Return symmetric key size so that Grover-reduced security >= target.

    If Grover halves the effective bits, we need 2 * target.
    """

    return 2 * target_security_bits


def rsa_classical_security_bits(modulus_bits: int) -> int:
    """Approximate classical security of RSA modulus in bits.

    We use the Lenstra–Verheul heuristic mapping (very roughly).
    This is only for illustrative comparison.
    """

    if modulus_bits == 1024:
        return 80
    if modulus_bits == 2048:
        return 112
    if modulus_bits == 3072:
        return 128
    if modulus_bits == 4096:
        return 152
    return int(0.3 * modulus_bits ** (1 / 3) * (math.log(modulus_bits) ** (2 / 3)))


def shor_break_feasibility_years(rsa_bits: int, logical_qubits: int, surface_code_cycle_ns: float = 1.0) -> float:
    """Toy estimator of years to break RSA with a fault-tolerant quantum computer.

    This uses extremely rough scaling relationships from the
    literature and is *not* a precise prediction. It is intended
    only to illustrate why large-scale, error-corrected devices
    are required for breaking RSA-2048.
    """

    base_qubits_for_2048 = 20_000
    depth_cycles_for_2048 = 10**12

    scale = rsa_bits / 2048
    required_qubits = base_qubits_for_2048 * scale
    required_cycles = depth_cycles_for_2048 * (scale ** 3)

    speed_factor = logical_qubits / required_qubits
    if speed_factor <= 0:
        return math.inf

    effective_cycles = required_cycles / speed_factor
    seconds = effective_cycles * (surface_code_cycle_ns * 1e-9)
    years = seconds / (60 * 60 * 24 * 365)
    return years
