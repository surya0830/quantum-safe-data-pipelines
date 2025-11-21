# Quantum-Safe Data Pipeline Research Project

This project explores the integration of quantum computing principles, post-quantum cryptography, and modern data engineering (Spark, distributed storage, streaming) to design and evaluate quantum-resistant data pipelines.

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
4. Launch the main benchmark suite:
   ```bash
   python -m src.benchmarks.run_all
   ```

See `docs/paper/paper.md` for the research paper draft and `notebooks/benchmarks.ipynb` for interactive experiments.
