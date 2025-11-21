# Quantum-Safe Data Pipeline Research Project

[![GitHub](https://img.shields.io/badge/GitHub-QuantumComputing-blue)](https://github.com/suryak614/QuantumComputing)

This project explores the integration of quantum computing principles, post-quantum cryptography, and modern data engineering (Spark, distributed storage, streaming) to design and evaluate quantum-resistant data pipelines.

**Research Paper:** See [`docs/paper/paper.md`](docs/paper/paper.md) for the full research paper on *Quantum-Resilient Data Pipelines: Integrating Post-Quantum Cryptography, Quantum Key Distribution, and Data Engineering*.


## Contents
- src/: Core source code (crypto primitives, PQC, QKD simulation, attacks, benchmarking)
- notebooks/: Benchmark and analysis notebooks
- docs/: Draft research paper, figures, and supporting material

## Quick Start
1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run basic tests:
   ```bash
   python -m pytest
   ```
4. Launch the main benchmark suite (stub PQC backend by default):
   ```bash
   python -m src.benchmarks.run_all
   ```
5. Regenerate cryptographic micro-benchmark CSVs for the paper/notebooks:
   ```bash
   python -m scripts.regenerate_crypto_results
   ```

See `docs/paper/paper.md` for the research paper draft and `notebooks/benchmarks.ipynb` for interactive experiments.

### Optional: enable real PQC backend (experimental)

If you have liboqs and its Python bindings (`oqs`) installed locally, you can
run the crypto benchmarks against a real Kyber/Dilithium/SPHINCS+ backend via
`src.crypto.pqc_real` by passing `use_real_pqc=True` in the
`run_crypto_benchmarks`/`write_results_csv` APIs (see
`src/benchmarks/crypto_benchmarks.py`). If the real backend is unavailable,
benchmarks will fall back to the educational stubs.

### Docker: reproducible PQC benchmark environment

For a fully reproducible environment with liboqs and its Python bindings
pre-installed, you can use the provided `Dockerfile.pqc`:

```bash
# Build the image (from the project root)
docker build -f Dockerfile.pqc -t quantum-safe-pipelines-pqc .

# Run benchmarks inside the container (results written under /app/results)
docker run --rm -v "$(pwd)/results:/app/results" quantum-safe-pipelines-pqc
```

This image builds liboqs and its Python bindings from source, installs the
project's Python dependencies, and then runs
`python -m scripts.regenerate_crypto_results` followed by
`python -m src.benchmarks.run_all` by default. This is suitable for
re-running the cryptographic micro-benchmarks and pipeline benchmarks in a
controlled environment.

## Next Steps

This repository is currently a research scaffold with educational PQC stubs and simplified models. Planned next steps are:

1. **Integrate real PQC backends where licensing permits.**
   - Keep the existing `src.crypto.pqc_stubs` API, but add optional backends using standards-compliant Kyber/Dilithium/SPHINCS+ implementations (e.g., via liboqs bindings), clearly separated from the toy `os.urandom`-based stubs.
   - Regenerate all cryptographic micro-benchmarks and update `results/` and the paper with measurements from real implementations.

2. **Build an end-to-end data pipeline benchmark.**
   - Implement a minimal but realistic pipeline (producer → queue → Spark job → data lake) with two modes: classical-only and hybrid PQC+classical for key establishment.
   - Measure throughput, latency, and storage overhead under realistic workloads and hardware.

3. **Harden experimental methodology and reproducibility.**
   - Move all benchmark parameters into explicit config files, fix random seeds, and add scripts/notebooks that regenerate every table/figure in the paper from scratch.
   - Document hardware/OS/Python and library versions used for each set of results.

4. **Refine the research questions and contributions.**
   - Focus on a small number of concrete, novel questions around quantum-safe data pipelines (e.g., impact of PQC certificate sizes on large Spark clusters, or cost of PQC-wrapped KEKs in streaming systems).
   - Rework the paper to emphasise methods, results, and discussion around those questions, trimming generic background where appropriate.

5. **Target a peer-reviewed publication and external adoption.**
   - Polish the codebase (tests, CI, docs, minimal examples) and align the paper with a specific venue (e.g., systems/security/data-engineering workshop or conference).
   - Encourage external users to run the benchmarks and, where possible, integrate the ideas into real deployments to build a track record of impact.
