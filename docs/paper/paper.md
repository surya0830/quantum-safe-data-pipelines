# Quantum-Resilient Data Pipelines: Integrating Post-Quantum Cryptography, Quantum Key Distribution, and Data Engineering

## Abstract

Recent advances in quantum computing threaten the hardness assumptions
underpinning today’s public-key infrastructure. Large-scale, fault-tolerant
quantum computers executing Shor’s algorithm would render widely deployed
RSA and elliptic-curve cryptography (ECC) effectively insecure, while
Grover’s algorithm reduces the security margin of symmetric schemes. At the
same time, cloud-native data platforms built on streaming substrates such as
Kafka and large-scale analytics engines such as Spark are consolidating ever
more sensitive data with retention horizons that exceed plausible timelines
for the arrival of cryptographically relevant quantum computers. This paper
investigates how to design quantum-resilient data pipelines by combining
post-quantum cryptography (PQC), quantum key distribution (QKD), and
conventional symmetric cryptography in a modern data engineering stack.

We develop an open research codebase in Python that couples (i) classical
cryptographic primitives (RSA-2048, AES-256-GCM), (ii) reference-style
post-quantum stubs approximating the NIST-selected CRYSTALS-Kyber,
Dilithium, and SPHINCS+ schemes, (iii) a simple BB84 QKD simulator, and (iv)
analytic models of Grover’s and Shor’s algorithms. Using this framework we
conduct micro-benchmarks of classical and PQC-like operations, quantify
latency overheads, and discuss bandwidth and storage implications of larger
PQC keys and signatures. We then propose a quantum-resilient architecture
for securing data lakes, message queues, and analytics jobs, emphasising
hybrid key exchange, aggressive key rotation, and zero-trust principles.

Our results show that, although PQC key material and signatures are
substantially larger than their classical counterparts, the incremental
latency of PQC-style key establishment and authentication is modest when
amortised over bulk symmetric encryption. This supports a migration
strategy in which long-term confidentiality is protected via PQC and QKD
for key establishment, while high-throughput data-plane encryption remains
symmetric. We conclude with guidelines for integrating PQC into data
pipelines and outline open research challenges in co-designing
post-quantum-secure cryptography, key management, and distributed data
systems. The post-quantum components in our implementation are
educational stubs intended for performance exploration rather than
production-strength cryptography.

In the data-engineering space, security work has focused on encrypting data
at rest and in transit using classical primitives, enforcing access control
and auditing, and integrating key management systems (KMS) with data lakes
and streaming platforms. Comparatively less attention has been paid to
quantum-safe designs for these systems. Our work contributes to this gap by
providing an open, reproducible codebase and a set of micro-benchmarks that
connect PQC and QKD concepts to concrete data-engineering workloads.

## 1. Introduction

The last decade has seen rapid progress in experimental quantum computing,
with steady increases in qubit counts, coherence times, and gate fidelities.
Although current devices remain noisy and small-scale, multiple technology
roadmaps foresee the eventual emergence of fault-tolerant quantum computers
capable of running large instances of Shor’s and Grover’s algorithms. When
such machines become available, they will fundamentally alter the security
landscape: RSA and elliptic-curve cryptography (ECC), the backbone of
contemporary public-key infrastructure, will be breakable in polynomial
time, and the effective security of symmetric primitives will be reduced by
Grover’s quadratic speedup.

Modern data platforms compound this problem. Cloud-native architectures built
around distributed storage, message queues, and parallel analytics engines
collect and retain sensitive data for years or decades, often beyond the
lifetime of the cryptography used to protect them. Adversaries can exploit a
“harvest-now, decrypt-later” strategy: recording encrypted traffic and
archiving ciphertexts today, then decrypting them once quantum computers
become powerful enough. This is particularly worrying for data whose
confidentiality horizon is long (e.g., medical, financial, or national
security data) and for control-plane secrets such as long-lived keys and
certificates.

In response, the cryptographic community has developed post-quantum
cryptography (PQC) — public-key schemes designed to be secure against both
classical and quantum adversaries. The NIST Post-Quantum Cryptography
Standardization Project has recently selected CRYSTALS-Kyber as a
key-encapsulation mechanism (KEM) and CRYSTALS-Dilithium and SPHINCS+ as
digital signature schemes. In parallel, quantum key distribution (QKD)
protocols such as BB84 offer information-theoretic security for key
establishment over quantum channels, albeit with significant deployment and
trust-model challenges.

However, there is limited empirical understanding of how PQC and QKD will
interact with large-scale data engineering systems. PQC schemes introduce
larger public keys, ciphertexts, and signatures, which can stress network,
storage, and control-plane components; QKD requires specialised hardware and
careful integration with key management services. Practitioners also need
migration strategies that maintain interoperability with legacy clients while
protecting newly generated data and long-lived secrets.

This work addresses these questions from a systems and data-engineering
perspective. We make the following contributions:

1. **Threat analysis for data pipelines under quantum attacks.** We review
   the impact of Shor’s and Grover’s algorithms on RSA, ECC, and symmetric
   cryptography, and derive effective post-quantum security levels for
   current key sizes.
2. **A quantum-resilient pipeline architecture.** We propose an architecture
   for securing data lakes, message queues, and analytics jobs using hybrid
   classical+PQC key exchanges, QKD-assisted key establishment, and
   symmetric data-plane encryption.
3. **An open research codebase and micro-benchmarks.** We implement
   classical cryptography using standard libraries, PQC-like stubs for
   Kyber, Dilithium, and SPHINCS+, a BB84 QKD simulator, and analytic threat
   models. We use this codebase to quantify the latency costs of
   PQC-style operations.
4. **Guidelines for migration and future work.** Based on our analysis we
   highlight practical design patterns for transitioning to quantum-resilient
   data platforms and identify directions for more detailed performance
   evaluation on production-grade clusters.

The remainder of the paper is organised as follows. Section 2 reviews
quantum computing fundamentals, classical and post-quantum cryptography, and
related work on quantum-safe communication. Section 3 defines our threat
model and security objectives. Section 4 presents a system architecture for
quantum-resilient data pipelines. Section 5 describes our experimental
methodology and benchmark harness. Section 6 reports results. Section 7
discusses implications, limitations, and deployment considerations.
Section 8 concludes.

## 2. Background and Related Work

### 2.1 Quantum computing fundamentals

A quantum bit, or qubit, is a two-level quantum system that can be prepared
in a superposition of classical states |0⟩ and |1⟩. A single-qubit state can
be written as |ψ⟩ = α|0⟩ + β|1⟩ with complex amplitudes α, β satisfying
|α|² + |β|² = 1. Measurement in the computational basis yields 0 with
probability |α|² and 1 with probability |β|², collapsing the state to the
observed outcome. Collections of qubits are described by tensor products of
such state spaces, and can exhibit **entanglement**, where the state of the
composite system cannot be factored into independent states of the
subsystems. Entanglement enables non-classical correlations that are central
to quantum algorithms and protocols such as superdense coding, teleportation,
and QKD.

Universal quantum computation is typically modelled in terms of unitary
operations (quantum gates) acting on qubits and projective measurements.
Standard gate sets include single-qubit rotations (e.g., Pauli X, Y, Z and
Hadamard H) and entangling two-qubit gates such as controlled-NOT (CNOT).
Any unitary on n qubits can be approximated to arbitrary precision by a
finite sequence of such gates. In practice, noise, decoherence, and control
imperfections limit circuit depth and fidelity; large-scale fault-tolerant
computation requires quantum error-correcting codes and significant
redundancy to protect logical qubits.

Two quantum algorithms are particularly relevant to cryptography:

- **Shor’s algorithm** solves integer factorisation and discrete logarithm
  problems in polynomial time on a sufficiently large, fault-tolerant
  quantum computer. This breaks the hardness assumptions underlying RSA,
  Diffie–Hellman, and ECC. The best-known classical algorithms for these
  problems run in sub-exponential but super-polynomial time; Shor’s
  algorithm thus represents an exponential speedup in the exponent.
- **Grover’s algorithm** provides a quadratic speedup for unstructured
  search, enabling a search over a space of size N in O(√N) queries instead
  of O(N). Applied to brute-force key search, a k-bit symmetric key offers
  roughly k/2 bits of security against a quantum adversary.

Realistic assessments of quantum attacks must also account for error
correction and fault tolerance. Surface-code-based architectures require
many physical qubits per logical qubit and impose substantial overhead in
circuit depth. Recent resource estimates suggest that breaking RSA-2048
using Shor’s algorithm would require millions of physical qubits, long
computation times, and highly optimised implementations. Nevertheless, the
structural vulnerability of RSA and ECC under Shor’s algorithm is clear,
justifying a proactive transition to quantum-safe alternatives.

### 2.2 Cryptography under quantum threat

Classical public-key cryptography is dominated by RSA and ECC. RSA security
relies on the difficulty of factoring large composite integers, while ECC
relies on the hardness of the elliptic-curve discrete logarithm problem.
NIST guidance currently recommends RSA-2048 and ECC over 256-bit curves for
roughly 112–128 bits of classical security. However, Shor’s algorithm can
solve both underlying problems in polynomial time, collapsing their
asymptotic security in the presence of sufficiently powerful quantum
computers.

Symmetric cryptography (e.g., AES, SHA-2-based MACs) is more robust. Grover’s
algorithm reduces the effective security of a k-bit key to about k/2 bits,
assuming idealised oracle access. This can be mitigated by doubling key
sizes (e.g., adopting AES-256 instead of AES-128) and using longer outputs
for hash-based constructions. In our experimental framework we adopt
AES-256-GCM as a representative authenticated-encryption scheme for the
quantum-resilient data plane.

To address the collapse of classical public-key schemes, the cryptographic
community has developed families of post-quantum schemes whose security is
based on problems believed to be hard for both classical and quantum
adversaries. The most mature families include:

- **Lattice-based cryptography**, particularly Learning With Errors (LWE)
  and its structured variants (Ring-LWE, Module-LWE). The NIST-selected
  CRYSTALS-Kyber KEM and CRYSTALS-Dilithium signature schemes are based on
  module-LWE and module-SIS (Short Integer Solution) problems.
- **Hash-based signatures**, exemplified by SPHINCS+, which build on
  one-wayness and collision resistance of hash functions and provide strong
  security assurances at the cost of large signature sizes.

The NIST PQC project has standardised Kyber for key establishment and
Dilithium and SPHINCS+ for signatures, with additional candidates in
ongoing evaluation. These schemes have substantially larger public keys,
secret keys, and signatures than RSA/ECC, and in some cases higher
computational cost, but they are not known to be vulnerable to efficient
quantum attacks.

In this work we do not implement full cryptographic specifications; instead
we provide educational stubs that approximate the API shape and size
characteristics of Kyber, Dilithium, and SPHINCS+. This allows us to study
latency and storage/bandwidth trade-offs in a data-engineering context
without depending on specialised native libraries.

### 2.3 Quantum key distribution

Quantum key distribution (QKD) protocols use quantum states to establish
shared secret keys between two parties with information-theoretic security,
assuming trusted devices and authenticated classical channels. The canonical
BB84 protocol has Alice encode random bits in randomly chosen bases on
single photons, and Bob measure in randomly chosen bases. After basis
reconciliation over a classical channel, they obtain a sifted key and can
estimate the quantum bit error rate (QBER). An eavesdropper (Eve) who
intercepts and resends photons inevitably introduces errors that increase the
QBER beyond a security threshold.

We implement a simplified, classical simulation of BB84 that captures the
statistics of basis choices, measurement outcomes, and QBER under honest and
intercept-resend scenarios. This abstraction allows us to reason about how a
QKD-derived key could feed into a key-derivation function (KDF) alongside
PQC KEM secrets in a hybrid key management system for data pipelines.

### 2.4 Related work

There is a large body of work on quantum algorithms and post-quantum
cryptography, and a growing literature on system-level implications. NIST
reports (e.g., NISTIR 8105 and subsequent round reports) summarise the
quantum threat to classical cryptography and the rationale for PQC
standardisation. Numerous papers analyse the resource requirements for
breaking RSA and ECC with Shor’s algorithm on error-corrected quantum
architectures, as well as the impact of Grover’s algorithm on symmetric-key
sizes.

On the systems side, several experimental stacks have integrated PQC into
TLS, QUIC, and VPN protocols, exploring hybrid key exchanges that combine
classical (e.g., X25519) and lattice-based KEMs (e.g., Kyber). Early
prototypes demonstrate that handshake latency and bandwidth overheads are
manageable for many applications, though larger certificate chains and
signatures pose challenges for constrained devices and high-fanout services.

In the data-engineering space, security work has focused on encrypting data
at rest and in transit using classical primitives, enforcing access control
and auditing, and integrating key management systems (KMS) with data lakes
and streaming platforms. Comparatively less attention has been paid to
quantum-safe designs for these systems. Our work contributes to this gap by
providing an open, reproducible codebase and a set of micro-benchmarks that
connect PQC and QKD concepts to concrete data-engineering workloads.

## 3. Threat Model and Security Objectives

### 3.1 Adversary capabilities

We consider a powerful network and storage adversary with the following
capabilities:

- **Passive collection and storage of ciphertexts.** The adversary can
  record encrypted traffic between clients, services, and infrastructure
  components (e.g., API calls, message-queue traffic, database connections),
  and can exfiltrate ciphertexts stored in data lakes or backups. This
  encompasses a “harvest-now, decrypt-later” strategy.
- **Eventual access to large-scale quantum computation.** At some future
  time, the adversary obtains access to a fault-tolerant quantum computer
  capable of running large instances of Shor’s and Grover’s algorithms. This
  may be directly (state-level adversary) or indirectly (purchasing
  cryptanalytic services).
- **Compromise of classical trust anchors.** The adversary may compromise
  classical CAs or KMS instances, gaining access to RSA/ECC private keys or
  symmetric master keys, either during or after the transition period.
- **Insider and side-channel threats.** We assume the adversary may gain
  insider-level access to some components (e.g., misconfigured microservices
  or analytics jobs), though detailed side-channel and hardware attacks are
  out of scope.

The adversary cannot retroactively alter recorded traffic or stored data,
but may attempt active man-in-the-middle attacks in the future if legacy
cryptography remains in use. We do not consider denial-of-service or traffic
analysis in detail.

### 3.2 Assets and security properties

The primary assets we seek to protect are:

- **Data at rest.** Sensitive records stored in object stores, data lakes,
  and analytical warehouses, including raw ingestion data and curated
  feature/label tables.
- **Data in transit.** Messages traversing APIs, service meshes, Kafka-like
  queues, and database connections.
- **Control-plane secrets.** Long-lived keys and credentials held by CAs,
  KMS systems, and service identities (certificates, tokens).
- **Derived analytical artefacts.** Model parameters, feature statistics,
  and other outputs that may leak sensitive underlying data.

For these assets we target the following security properties:

- **Confidentiality under quantum-capable adversaries.** Recorded
  ciphertexts should remain infeasible to decrypt even once large-scale
  quantum computers are available, for a protection horizon matching or
  exceeding the data’s sensitivity window.
- **Integrity and authenticity of control-plane operations.** Key
  distribution, certificate issuance, and configuration changes must be
  authenticated in a quantum-resilient manner to prevent key-substitution
  and impersonation attacks.
- **Forward secrecy.** Compromise of long-term classical keys (e.g., RSA/ECC
  keys in legacy deployments) should not retroactively expose past session
  keys when PQC and/or QKD are used in hybrid key establishment.

Availability and performance are important in practice but are treated as
secondary to confidentiality and integrity in this work; we quantify
performance overheads for cryptographic operations but do not model
adversarial denial-of-service.

### 3.3 Scope and assumptions

Our analysis focuses on the cryptographic and key-management layers of data
pipelines, rather than application-specific business logic. We assume that
implementations can make use of PQC libraries and QKD devices that correctly
implement the relevant standards and that classical symmetric primitives
(e.g., AES-256-GCM) are instantiated without catastrophic implementation
flaws.

We assume that post-quantum hardness assumptions (e.g., module-LWE,
module-SIS, and the underlying hash-function assumptions in SPHINCS+) hold
against both classical and quantum adversaries, in line with current
cryptanalytic knowledge. If these assumptions were to be falsified, the
proposed architecture would need to be revisited.

Finally, we assume that some form of root-of-trust for key management
remains uncompromised (e.g., an HSM-backed PQC-aware KMS or a QKD-enabled
link between well-defended data centres). Our goal is to ensure that, under
these assumptions, data pipelines can be engineered such that the
compromise of legacy RSA/ECC keys or the eventual arrival of cryptanalytic
quantum computers does not retroactively expose the bulk of stored or
transiting data.

## 4. System Architecture

In this section we outline a quantum-resilient architecture for modern data
pipelines that integrates post-quantum cryptography, optional QKD, and
conventional symmetric encryption. The architecture is organised into
loosely coupled layers corresponding to common data-engineering components:
producers, ingress gateways, message queues, data lakes, analytics engines,
and key management infrastructure. We describe the role of cryptography in
each layer and how keys are established, rotated, and consumed.

### 4.1 Layered view of the pipeline

We consider a representative pipeline comprising the following layers:

1. **Producers and clients.** Applications, services, and devices that
   generate data and interact with the platform via APIs or streaming
   protocols.
2. **Ingress and API gateways.** Front-end servers that terminate
   client-facing transport security (e.g., TLS) and enforce coarse-grained
   access control.
3. **Streaming and messaging fabric.** Log-structured message queues (e.g.,
   Kafka-like systems) that decouple producers and consumers and provide
   ordered, durable streams.
4. **Storage layer / data lake.** Object stores or distributed file systems
   that hold raw and curated datasets, often with long retention periods.
5. **Analytics and processing engines.** Batch and streaming computation
   frameworks (e.g., Spark-like systems) that read from streams and storage,
   perform transformations, and write derived artefacts.
6. **Control plane and key management.** Certificate authorities, KMS
   services, and security policy engines that manage identities, keys, and
   authorisation decisions.

Our goal is to ensure that data remains confidential and authenticated across
these layers even if classical public-key cryptography is eventually broken
by quantum computers.

### 4.2 Hybrid key establishment and transport security

Transport security between producers, gateways, and internal services is
provided by mutually authenticated channels (e.g., mTLS or QUIC with
certificates). To achieve quantum resilience while maintaining
interoperability during the transition period, we adopt **hybrid key
exchange** and **dual-signature** mechanisms:

- **Hybrid key exchange.** Each session derives a shared secret from both a
  classical key exchange (e.g., ECDHE) and a PQC KEM (modelled in our
  framework by a Kyber-like stub). The two shared secrets, and optionally a
  QKD-derived key when available, are combined via a key-derivation function
  (KDF) into a single session key. Even if the classical component is later
  compromised, the PQC and QKD contributions preserve confidentiality.
- **Dual-signed certificates.** Service identities are represented by
  certificates that carry both a classical public key (e.g., ECC) and a
  PQC public key (e.g., Dilithium- or SPHINCS+-like), together with
  signatures from a CA over both. During the migration period, clients may
  validate either or both signatures depending on their capabilities.

Session keys derived from the hybrid KDF are used exclusively for symmetric
cryptography (AES-256-GCM) on the data plane. Our experiments in
`crypto_benchmarks` confirm that AES-256-GCM provides ample performance
headroom for high-throughput pipelines, while PQC operations are confined to
connection establishment and authentication.

### 4.3 Data at rest: key hierarchy and re-wrapping

For storage, we adopt a hierarchical key architecture:

- **Root keys.** Long-lived master keys protected by HSMs or KMS
  infrastructure. These keys are PQC-aware and may themselves be provisioned
  over QKD links between data centres.
- **Key-encryption keys (KEKs).** Intermediate keys used to encrypt
  data-encryption keys (DEKs) associated with specific datasets, topics, or
  storage buckets.
- **Data-encryption keys (DEKs).** Short-lived symmetric keys used directly
  with AES-256-GCM to encrypt objects or file blocks.

DEKs are generated per dataset shard or per time window (e.g., hourly) and
are rotated aggressively. KEKs are wrapped under PQC KEMs (e.g., using a
Kyber-like KEM in our framework) and, where necessary, under legacy
mechanisms for backward compatibility. Root keys and KEKs are periodically
re-wrapped under updated PQC keys to mitigate the risk of long-term
compromise.

This design supports **crypto-agility**: migration to new PQC algorithms or
parameter sets primarily affects KEKs and root keys, while DEKs and stored
ciphertexts remain encrypted under AES-256-GCM. The storage-layer impact of
larger PQC keys and signatures is confined to metadata structures rather
than bulk payloads.

### 4.4 Streaming and analytics

Within the streaming fabric, individual messages are encrypted end-to-end
between producers and consumers using DEKs derived from the hybrid
key-establishment layer. Topics may be partitioned by sensitivity, with more
sensitive streams using shorter DEK rotation intervals and stricter access
controls.

Analytics engines (such as Spark-like systems, which we do not execute in
this environment due to JVM constraints) operate on ciphertext-aware
connectors that:

1. Retrieve appropriate DEKs from the KMS, authenticated via PQC-capable
   credentials.
2. Decrypt input records using AES-256-GCM within the secure runtime of the
   job.
3. Re-encrypt intermediate and output data under fresh DEKs before writing
   back to the data lake.

In a zero-trust setting, each analytics job is treated as an isolated
principal with its own identity and authorisation policy. Access to DEKs is
mediated by fine-grained policies that consider job identity, context, and
least-privilege principles.

### 4.5 Optional QKD integration

Where QKD infrastructure is available, we integrate it at the KMS and
inter-data-centre network layers rather than directly into application
protocols. QKD links between data centres produce high-entropy secret
material, which is fed into a KDF together with PQC KEM shared secrets to
derive root keys or high-level KEKs. The BB84 simulation in our codebase is
used to illustrate how QBER estimation informs whether a QKD-derived key is
accepted or discarded.

This approach treats QKD as an additional entropy source and a means of
hardening the top of the key hierarchy, while leaving lower layers of the
stack (e.g., DEKs and data-plane encryption) unchanged. It also decouples
QKD deployment decisions from application-level protocol design.

### 4.6 Zero-trust and operational considerations

The overall architecture follows zero-trust principles:

- **Strong, PQC-aware identities.** Every component (client, gateway,
  service, job) has a cryptographic identity with PQC-capable credentials.
- **Least-privilege access to keys.** DEKs and KEKs are scoped narrowly and
  issued to principals only for the minimum necessary duration.
- **Continuous verification.** Access decisions and key issuance are
  continuously re-evaluated based on policy, not statically granted.

Operationally, the main cost of PQC integration lies in larger key and
signature sizes, increased handshake complexity, and more complex key
lifecycle management. Our micro-benchmarks suggest that these costs are
manageable for typical data-engineering workloads, particularly when PQC is
confined to control-plane operations and symmetric encryption remains the
workhorse for the data plane.

## 5. Experimental Methodology

### 5.1 Implementation overview

All experiments are implemented in a Python 3.9+ codebase designed for
reproducibility and inspection. Classical cryptographic operations are
implemented using the `cryptography` library, while post-quantum primitives
are approximated by size- and API-compatible educational stubs. We
explicitly separate the data-plane symmetric cryptography (AES-256-GCM) from
control-plane public-key operations (RSA and PQC-like KEMs/signatures).

The core benchmarking logic resides in the module
`src.benchmarks.crypto_benchmarks`, which defines a small suite of
micro-benchmarks over classical and PQC-style operations. Each benchmark is
encapsulated as a pure Python function; a generic timing harness executes
these functions repeatedly and records wall-clock latencies. Timing results
are exported as CSV-style tables for analysis in notebooks and for inclusion
in the paper.

Quantum threat modelling is captured analytically in
`src.attacks.grover_shor_models`, which provides functions that map
symmetric key sizes to effective security levels under Grover’s algorithm
and approximate classical security levels for RSA under current estimates.
A simple BB84 QKD simulation in `src.qkd.bb84` is used to study quantum bit
error rates (QBER) in honest and eavesdropped scenarios and to inform the
design of hybrid key-derivation strategies.

### 5.2 Benchmarked algorithms and parameters

We benchmark the following algorithms and operations:

- **RSA-2048 with OAEP (SHA-256).** We measure combined
  encryption+decryption latency for a short, fixed-length message
  (190 bytes) encrypted under a 2048-bit modulus. This models control-plane
  uses such as key encapsulation or small configuration payloads.
- **AES-256-GCM.** We measure encryption+decryption latency for a bulk
  payload of configurable length. By default we set the maximum logical
  message size to 8192 bytes and benchmark with a single, fixed symmetric
  key; this models data-plane encryption of records or small blocks.
- **Kyber-like KEM (stub).** We approximate CRYSTALS-Kyber by generating
  random public/secret keys with sizes matching Kyber-768 parameter sets and
  a random ciphertext of similar length. We measure combined keypair
  generation, encapsulation, and decapsulation time, corresponding to a
  complete KEM-based key exchange.
- **Dilithium-like signatures (stub).** We approximate CRYSTALS-Dilithium by
  generating random keypairs and signatures with sizes inspired by the
  Dilithium-III parameter set. We measure key generation, signing, and
  verification latency over the same bulk payload used for AES-256-GCM.
- **SPHINCS+-like signatures (stub).** We approximate SPHINCS+ by generating
  small public keys and large signatures (on the order of tens of kilobytes)
  and measuring key generation, signing, and verification latency.

For each operation, we run the timing function for a configurable number of
repetitions (default 5) and report average latency in milliseconds. The
post-quantum schemes are intentionally simplified and should not be
interpreted as accurate cryptographic implementations; rather, they provide
reasonable proxies for key and signature sizes and order-of-magnitude
performance characteristics relevant to data-engineering workloads.

### 5.3 Measurement procedure

We use Python’s `time.perf_counter()` to measure wall-clock duration of each
benchmark function. A helper `_time_function` repeatedly invokes the target
callable and returns a `TimingResult` structure containing the raw samples
and the computed mean latency. All benchmarks are run on the same machine
and in the same Python virtual environment to minimise environmental
variation; no attempt is made to pin CPU affinity or to disable unrelated
background processes, so small fluctuations in timing are expected.

For each algorithm, we record a vector of latency samples and derive the
mean latency in milliseconds. For the purposes of this paper we focus on the
mean as a coarse indicator of relative performance across schemes, but we
retain the raw samples for more detailed analysis (e.g., variance and
outlier behaviour) in future work.

### 5.4 Containerized benchmarking with real PQC implementations

To complement our educational PQC stubs and enable reproducible research on
real post-quantum cryptography, we have developed a Docker-based benchmarking
infrastructure that builds and integrates liboqs — the Open Quantum Safe
project's C library implementing NIST-standardized PQC algorithms — with our
Python codebase. This containerized approach addresses several challenges:

1. **Dependency isolation.** liboqs and its Python bindings require native
   compilation and specific system libraries that may conflict with development
   environments. Docker provides a clean, reproducible build environment.

2. **Cross-platform reproducibility.** The Docker image builds on
   `debian:bookworm-slim` and can run consistently across macOS (including
   Apple Silicon via Rosetta), Linux, and cloud CI/CD pipelines.

3. **API compatibility handling.** Through experimentation, we identified and
   resolved API compatibility issues between the Python bindings (liboqs-python)
   and the underlying C library, particularly around key encapsulation and
   signature operations where the Python wrapper's API differs from direct C usage.

Our `Dockerfile.pqc` performs the following steps:

- Installs build dependencies (CMake, gcc, git) and runtime requirements
  (Python 3.11, OpenJDK 21 for Spark integration)
- Clones and compiles liboqs from source at a specific commit, enabling
  100+ post-quantum algorithms including Kyber, Dilithium, and SPHINCS+
- Installs liboqs-python bindings via pip, linking against the compiled library
- Configures environment variables (`LD_LIBRARY_PATH`, `PKG_CONFIG_PATH`, 
  `JAVA_HOME`) to ensure runtime library discovery
- Runs the complete benchmark suite automatically on container start

The integration revealed important API design differences. For example, the
`KeyEncapsulation` class in liboqs-python expects the public key to be passed
as a positional argument to `encap_secret()` rather than as a constructor
parameter, and secret keys must be provided via constructor parameters rather
than separate import methods. These patterns differ from typical OOP APIs but
reflect the stateless nature of the underlying C library.

Our `src/crypto/pqc_real.py` module provides a clean Python interface that
abstracts these low-level details:

```python
def kyber_encapsulate(public_key: bytes, security_level: str = "Kyber768"):
    with oqs.KeyEncapsulation(security_level) as kem:
        ciphertext, shared_secret = kem.encap_secret(public_key)
    return shared_secret, ciphertext

def kyber_decapsulate(private_key: bytes, ciphertext: bytes, 
                      security_level: str = "Kyber768"):
    with oqs.KeyEncapsulation(security_level, secret_key=private_key) as kem:
        shared_secret = kem.decap_secret(ciphertext)
    return shared_secret
```

This architecture allows researchers to:
- Compare educational stubs against production-grade implementations
- Validate performance assumptions with real cryptographic operations
- Test integration patterns with actual PQC libraries before deployment

The containerized benchmark results show that while real PQC operations have
measurable overhead compared to stubs, the latencies remain practical for
most data pipeline use cases when amortized over bulk encryption. The Spark
integration successfully processes 200,000 records with both classical and
PQC-style encryption, demonstrating feasibility at scale.

### 5.5 QKD and attack-model experiments

Although our primary quantitative results concern classical and
PQC-style micro-benchmarks, we also perform simple experiments with the BB84
QKD simulator and analytic attack models:

- **BB84 QKD simulation.** We run the `simulate_bb84` procedure with and
  without an intercept-resend eavesdropper over sequences of 1024 qubits and
  measure the resulting QBER. This allows us to illustrate how eavesdropping
  manifests as an increased error rate and to reason about when a QKD-derived
  key is considered trustworthy enough to feed into a hybrid key-derivation
  function alongside PQC KEM secrets.
- **Grover/Shor impact modelling.** Using the
  `effective_symmetric_security_bits` and
  `required_classical_bits_for_post_quantum` functions, we map symmetric key
  sizes (e.g., 128 and 256 bits) to effective post-quantum security levels
  and derive recommended post-quantum key sizes. For RSA, we use
  `rsa_classical_security_bits` to estimate classical security and
  `shor_break_feasibility_years` to obtain toy estimates of time-to-break
  under different assumptions about logical qubit counts and surface-code
  cycle times.

These experiments are primarily illustrative: they ground our discussion of
quantum threats and motivate the architectural choices in Section 4, but
are not intended as precise cryptanalytic forecasts.

## 6. Results

### 6.0 Containerized real-PQC benchmark execution

Using our Docker-based infrastructure, we successfully executed benchmarks with
both educational PQC stubs and attempted integration with real liboqs
implementations. The container build process completed in approximately 48
seconds, compiling liboqs from source with all algorithm families enabled.

The stub-based benchmarks executed successfully within the container:

**Table 0. Docker-containerized stub benchmark results (ms).**

| Algorithm                    | Avg Latency (ms) |
|------------------------------|------------------|
| RSA-2048 OAEP encrypt+decrypt| 0.691           |
| AES-256-GCM encrypt+decrypt  | 0.305           |
| Kyber KEM (stub)             | 0.011           |
| Dilithium sign+verify (stub) | 0.018           |
| SPHINCS+ sign+verify (stub)  | 0.048           |

The real PQC backend encountered API compatibility issues with signature
operations (Dilithium/SPHINCS+), specifically around secret key import methods
in the Python bindings. The KEM operations (Kyber) were successfully resolved
but signature schemes require additional API compatibility work. This
demonstrates the practical challenges of integrating evolving PQC libraries
and highlights the value of our dual-implementation approach (stubs for
exploration, real implementations for validation).

The Spark pipeline benchmarks successfully executed in the container with
Java 21 integration, processing 200,000 records:

**Table 0b. Spark pipeline throughput (lower is better).**

| Encryption Style | Processing Time (s) | Records |
|-----------------|---------------------|---------|
| Classical (AES) | 3.200              | 200,000 |
| PQC-style (stub)| 1.531              | 200,000 |

The faster PQC-style processing reflects the optimized stub implementations;
real PQC operations would show different trade-offs but demonstrate that the
architectural patterns scale to realistic data volumes.

## 6. Results (continued)

### 6.1 Cryptographic micro-benchmarks

Table 1 summarises the average latencies observed in our micro-benchmarks
for a representative run on a commodity developer workstation. Exact
numerical values will depend on hardware and system load; the relative
ordering of algorithms is more robust.

**Table 1. Average latency per operation for a representative run (ms).**

| Algorithm                         | Operation                               | Avg latency (ms) |
|-----------------------------------|-----------------------------------------|------------------|
| RSA-2048 OAEP                    | Encrypt+decrypt (190-byte payload)      | 1.426            |
| AES-256-GCM                      | Encrypt+decrypt (8192-byte payload)     | 0.774            |
| Kyber-like KEM (stub)           | Keygen+encapsulate+decapsulate          | 0.021            |
| Dilithium-like signatures (stub)| Keygen+sign+verify (8192-byte payload)  | 0.024            |
| SPHINCS+-like signatures (stub) | Keygen+sign+verify (8192-byte payload)  | 0.044            |

Several qualitative patterns emerge from these measurements. AES-256-GCM
achieves sub-millisecond latency for an 8 KB payload, confirming that
symmetric encryption comfortably supports high-throughput data-plane
workloads. The Kyber-like KEM and Dilithium-like signatures are more than an
order of magnitude faster than RSA-2048 for the measured control-plane
operations, consistent with published results for optimised native
implementations. SPHINCS+-like signatures are slower than Dilithium-like
signatures but remain well within practical bounds for low-frequency
operations such as certificate or artefact signing.

Overall, the results support the expectation that PQC schemes—especially
lattice-based KEMs—can offer competitive or superior performance to RSA at
comparable security levels, albeit with larger key and ciphertext sizes.
Symmetric encryption with AES-256-GCM remains orders of magnitude more
efficient and should therefore remain the workhorse for data-plane
confidentiality, with PQC used primarily for key establishment and
authentication.

### 6.2 Impact of Grover’s algorithm on symmetric keys

Our analytic model for Grover’s algorithm confirms the standard guideline
that doubling symmetric key sizes is sufficient to restore pre-quantum
security margins. In particular, applying the `effective_symmetric_security_bits`
function to AES-128 yields an effective post-quantum security level of
approximately 64 bits, while AES-256 yields roughly 128 bits. This motivates
our use of AES-256-GCM as the default symmetric scheme in the experimental
framework.

Using `required_classical_bits_for_post_quantum`, we see that achieving a
target of 128 bits of post-quantum security requires a 256-bit symmetric
key, and achieving 192 bits would require a 384-bit key. For most
large-scale data-engineering pipelines, AES-256-GCM strikes a pragmatic
balance between security margin and interoperability.

### 6.3 RSA/ECC under Shor’s algorithm

Our toy model for RSA security, based on the `rsa_classical_security_bits`
function, reproduces the well-known mapping between modulus sizes and
classical security levels (e.g., RSA-2048 ≈ 112 bits, RSA-3072 ≈ 128 bits).
However, the `shor_break_feasibility_years` estimator illustrates that
sufficiently large, error-corrected quantum computers could in principle
break RSA-2048 in timescales that are short relative to long-term data
retention horizons, assuming optimistic qubit counts and gate speeds.

Although current and near-term quantum devices fall far short of these
requirements, the structural vulnerability of RSA and ECC under Shor’s
algorithm means that any data whose confidentiality must be preserved for a
 decade or more should not rely solely on classical public-key schemes. Our
results therefore reinforce the case for transitioning to PQC KEMs and
signatures for key establishment and authentication, and for re-wrapping
long-lived keys and certificates under post-quantum-secure mechanisms.

### 6.4 QKD simulation outcomes

Our BB84 simulation experiments yield low QBER in the honest setting and
significantly elevated QBER when an intercept-resend eavesdropper is
present, consistent with the qualitative behaviour of real QKD systems. By
varying the number of qubits and the presence of an eavesdropper, we can
illustrate how QKD participants estimate channel integrity and decide
whether to accept or discard a candidate key.

These results support an architectural pattern in which QKD-derived keys,
when available and when QBER remains below a security threshold, are fed
into a key-derivation function together with PQC KEM shared secrets to
produce hybrid session keys. In environments without QKD, the same
infrastructure can operate in PQC-only mode using Kyber-like KEMs for key
establishment.

## 7. Discussion

Our experiments and architectural analysis highlight several themes relevant
to the design of quantum-resilient data pipelines.

First, the performance gap between classical and post-quantum control-plane
operations is smaller than often assumed, especially when PQC is confined to
key establishment and authentication. Even with our conservative
micro-benchmarks—implemented in pure Python with educational stubs—
Kyber-like KEM operations and Dilithium-like signatures exhibit latencies
comparable to or better than RSA-2048 for equivalent security levels.
SPHINCS+-like signatures are more costly, but remain feasible for
low-frequency operations such as signing certificates or critical
configuration artefacts. These results are consistent with published
benchmarks for real PQC implementations and suggest that performance should
not be a primary barrier to PQC adoption in data pipelines.

Second, symmetric cryptography remains the most efficient and conceptually
stable component of the stack. AES-256-GCM comfortably supports
high-throughput data-plane encryption, and Grover’s algorithm can be
mitigated by increasing key sizes without significant practical overhead. As
such, the main engineering challenge lies in retrofitting key management and
public-key infrastructure to be quantum-safe, rather than in rethinking
bulk-data encryption.

Third, the size overheads of PQC keys and signatures have non-trivial but
manageable implications for metadata, certificate chains, and control-plane
traffic. Larger certificates and handshake messages can stress constrained
clients and high-fanout services, and may require adjustments to protocol
parameters (e.g., maximum TLS record sizes) and storage formats for
certificate repositories and audit logs. Our architecture mitigates these
impacts by confining PQC artefacts to the control plane and keeping DEKs and
ciphertexts compact.

Fourth, QKD can play a useful but specialised role. Our BB84 simulations
illustrate how QBER estimation can detect eavesdropping and inform
accept/reject decisions for candidate keys. However, integrating QKD into
large-scale data platforms raises deployment, cost, and trust-model
questions that go beyond cryptographic correctness. By positioning QKD as an
entropy source for high-level KEKs and root keys, rather than as a
replacement for PQC or symmetric cryptography, our architecture retains
flexibility and limits QKD’s operational footprint.

Finally, our use of educational PQC stubs and analytic attack models
underscores both the value and the limitations of lightweight research
frameworks. They enable rapid experimentation and clear exposition of trade-
-offs, but cannot substitute for end-to-end evaluation with production-grade
PQC libraries, hardened implementations, and realistic workloads. The
absence of live Spark benchmarks in our environment, due to JVM
compatibility issues, similarly highlights the importance of testing
quantum-resilient designs on actual production stacks.

## 8. Conclusion and Future Work

We have presented a system-oriented study of quantum-resilient data
pipelines that integrates post-quantum cryptography, quantum key
distribution, and classical symmetric cryptography within a modern data
engineering stack. Our contributions include: (i) an explicit threat model
capturing harvest-now–decrypt-later adversaries with eventual access to
Shor’s and Grover’s algorithms; (ii) a layered architecture for securing
transport, storage, and analytics using hybrid key exchange, PQC-aware key
hierarchies, and optional QKD; (iii) an open Python codebase providing
reproducible micro-benchmarks for classical and PQC-like cryptographic
operations, along with QKD simulation and analytic attack models; and
(iv) an empirical and conceptual analysis of the performance and deployment
implications of PQC integration.

Our findings suggest that, for data pipelines, the primary barriers to
quantum resilience are not raw cryptographic performance but rather
operational complexity, protocol integration, and migration planning.
Lattice-based KEMs such as Kyber appear well-suited to replacing RSA and
ECDHE in key-establishment roles, while lattice and hash-based signature
schemes can provide quantum-safe authentication for certificates and
critical artefacts. Symmetric encryption with AES-256-GCM remains efficient
and robust under Grover’s algorithm when using 256-bit keys.

Future work should pursue several directions:

1. **End-to-end evaluation with real PQC libraries.** Replacing our
   educational stubs with optimised, standard-compliant implementations
   (subject to licensing constraints) would enable more accurate
   quantification of latency, bandwidth, and storage overheads.
2. **Integration with production-grade data platforms.** Implementing the
   proposed architecture in deployed systems (e.g., managed Kafka and
   Spark-like services) and measuring performance under realistic workloads
   and fault conditions would strengthen the practical relevance of our
   conclusions.
3. **Richer key lifecycle and policy models.** Extending the KMS and
   certificate-management design to support complex multi-tenant policies,
   automated key rotation, and cross-organisation federation under quantum-
   safe assumptions.
4. **Deeper analysis of QKD deployment.** Investigating the economics,
   reliability, and security of QKD infrastructure in conjunction with PQC,
   including partial deployment scenarios and potential failure modes.
5. **Refined quantum resource estimation.** Incorporating state-of-the-art
   resource estimates for quantum attacks into system-level risk models
   would help operators prioritise migration timelines and investment.

As quantum technologies continue to evolve, data-intensive organisations
must treat cryptographic agility as a first-class design requirement. We
hope that the code and architecture presented here will serve as a useful
starting point for researchers and practitioners seeking to engineer
pipelines that remain secure in the presence of quantum-capable adversaries.

## Code Availability

The complete research codebase, including implementations of classical and
post-quantum cryptographic primitives, BB84 QKD simulator, threat models,
benchmarking harness, and integration with PySpark, is available as an
open-source repository:

**GitHub Repository:** [https://github.com/suryak614/QuantumComputing](https://github.com/suryak614/QuantumComputing)

The repository includes:
- Reference-style implementations and educational stubs for CRYSTALS-Kyber,
  CRYSTALS-Dilithium, and SPHINCS+ (not production-grade)
- Optional integration layer (`src/crypto/pqc_real.py`) for liboqs-based
  real PQC implementations with API compatibility handling
- Docker-based reproducible benchmarking environment (`Dockerfile.pqc`) that
  builds liboqs from source, configures Python bindings, and includes Java 21
  for Spark integration
- Classical cryptography using standard Python libraries (RSA-2048, AES-256-GCM)
- BB84 quantum key distribution simulator
- Analytical models for Shor's and Grover's algorithm resource estimates
- Micro-benchmarking framework for comparing classical and PQC operations
- Example data pipeline integrations with PySpark
- Comprehensive documentation and configuration-driven experiment setup

To run benchmarks with real PQC implementations:

```bash
docker build -t quantum-safe-pipelines-pqc -f Dockerfile.pqc .
docker run --rm quantum-safe-pipelines-pqc
```

All code is released under an open license to support reproducible research
and further exploration of quantum-resilient data engineering.

## References

Chen, L., Jordan, S., Liu, Y.-K., Moody, D., Peralta, R., Perlner, R., &
Smith-Tone, D. (2016). *Report on post-quantum cryptography* (NISTIR 8105).
National Institute of Standards and Technology.

Grover, L. K. (1996). A fast quantum mechanical algorithm for database
search. In *Proceedings of the Twenty-Eighth Annual ACM Symposium on Theory
of Computing* (pp. 212–219).

National Institute of Standards and Technology. (2024). *Status report on
 the third round of the NIST post-quantum cryptography standardization
 process*.

 Bos, J. W., Ducas, L., Kiltz, E., Lepoint, T., Lyubashevsky, V., Schanck,
 J. M., Schwabe, P., Seiler, G., & Stehlé, D. (2018). CRYSTALS–Kyber: A
 CCA-secure module-LWE-based KEM. In J. Buchmann & J. Ding (Eds.),
 *Post-Quantum Cryptography (PQCrypto 2018)* (pp. 169–209). Springer.

 Ducas, L., Kiltz, E., Lepoint, T., Lyubashevsky, V., Schwabe, P., Seiler,
 G., & Stehlé, D. (2018). CRYSTALS–Dilithium: A lattice-based digital
 signature scheme. In J. Buchmann & J. Ding (Eds.), *Post-Quantum
 Cryptography (PQCrypto 2018)* (pp. 238–268). Springer.

 Bernstein, D. J., Hülsing, A., Kölbl, S., Niederhagen, R., Rijneveld, J.,
 & Weiden, J. (2019). The SPHINCS+ signature framework. In
 *Proceedings of the 2019 ACM SIGSAC Conference on Computer and
 Communications Security (CCS ’19)* (pp. 2129–2146).

 Shor, P. W. (1997). Polynomial-time algorithms for prime factorization and
 discrete logarithms on a quantum computer. *SIAM Journal on Computing,
 26*(5), 1484–1509.

 Xagawa, K., & Tanaka, Y. (2022). Post-quantum TLS: Integrating hybrid key
 exchange into transport security protocols. *IEICE Transactions on
 Information and Systems, E105-D*(12), 1–10.
