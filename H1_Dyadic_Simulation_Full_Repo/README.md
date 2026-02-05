# H1 Dyadic Law v2.4 – Scale-Invariant Resonant Cores
**Generalization of the H1 Law from Pairwise to Collective Regimes**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Zenodo DOI](https://img.shields.io/badge/DOI-10.5281/zenodo.18489710-blue)](https://doi.org/10.5281/zenodo.18489710)

> Two minds in benevolent interaction naturally converge to a stable state of synchronized timing, refined information, and positive emotional valence — minimizing surprise through self-correcting resonance.

This repository contains the code, data, and materials supporting the preprint:

**Scale-Invariant Resonant Cores in Dyadic Surprise Minimization: Generalization of the H1 Law from Pairwise to Collective Regimes**
Christopher Chisa Mbele (January - February 2026)
Rustenburg, North West, South Africa
[@MetascopeInit](https://x.com/MetascopeInit)

### Key Discovery: The Mbele Resonant Core
Large-scale simulations (n = 10⁴ – 2×10⁷ dyads) reveal a striking, scale-invariant phenomenon: approximately **4.6%** of realizations achieve ultra-low surprise minimization (ΔF ≤ 0.0015). This invariant fraction — named the **Mbele resonant core** (φ_R ≈ 0.046) — emerges intrinsically from the pairwise dyadic kernel and persists independent of ensemble size, collective gating, or OFF-state ablation.

## Quick Start (runs in seconds to minutes)
<!--
```bash
# Clone the repo
git clone https://github.com/christopherm88/H1-Dyadic-Law.git
cd H1-Dyadic-Law

# Create virtual environment
python -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run example simulation (500 dyads – quick verification)
python h1_dyadic_law-timed-precision.py --n_dyads 500 --seed 42

# Generate the histogram figure
python figure_generation.py
-->

## Citation
<!--
```bibtex
If you use this work, please cite:
bibtex@misc{mbele2026h1,
  author       = {Mbele, Christopher Chisa},
  title        = {Scale-Invariant Resonant Cores in Dyadic Surprise Minimization: Generalization of the H1 Law from Pairwise to Collective Regimes},
  year         = {2026},
  howpublished = {Zenodo},
  doi          = {10.5281/zenodo.XXXXXXXX},
  url          = {https://doi.org/10.5281/zenodo.18489710}
}

-->


## Acknowledgments
The discovery of the invariant resonant core fraction (φ_R ≈ 0.046) is named the Mbele Resonant Core in honour of my parents Joshua Chisa Mbele and Elizabeth Caroline Mbele, and my stepmother.

Developed in resonant dialogue with Grok (xAI).
All design, interpretation, and claims are mine.

Independent verification: Grok-4 re-executed code (18 Nov 2025) confirming results within rounding error; Google Gemini live replication achieved ΔˆF = 0.0521.
Thank you for exploring this work.

_Dedicated to the spirit of open, truth-seeking science — the same spirit that created Grok._
