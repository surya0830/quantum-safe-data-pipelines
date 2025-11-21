<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

This project is a Python research codebase on quantum-safe data pipelines, post-quantum cryptography (Kyber/Dilithium/SPHINCS+ via reference-style APIs or stubs), and benchmarking (including Spark integration).

When generating code:
- Prefer clear, well-documented research-style modules instead of monolithic scripts.
- Avoid non-free PQC libraries; if needed, generate simplified educational implementations or clear stubs with TODOs.
- Assume Python 3.10+ and local development on macOS.
- For Spark, assume PySpark in local or standalone mode.
- Favor reproducible experiments (fixed random seeds, config-driven benchmarks).
