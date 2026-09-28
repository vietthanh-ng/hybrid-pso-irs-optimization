# Direct Hardware RLC Parameter Optimization for Reconfigurable Intelligent Surfaces via Adaptive Swarm Intelligence

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced optimization framework for **Intelligent Reflecting Surfaces (IRS / RIS)** in 6G wireless communication systems. This project transitions from conventional abstract phase-only beamforming to **direct optimization of equivalent lumped RLC circuit hardware parameters** under practical amplitude-phase coupling, utilizing a **Hybrid Adaptive Particle Swarm Optimization (PSO) and Nelder-Mead Simplex** pipeline.

---

## Overview

Conventional research on IRS predominantly relies on the **ideal phase-shift model**, assuming unity reflection amplitude ($|\beta_n| = 1$) regardless of phase shift ($\theta_n$). In physical hardware implementations (e.g., varactor diode-loaded microstrip patches):
- Severe **amplitude-phase coupling** occurs: reflection amplitude plummets (down to $\beta_n \approx 0.2$, dissipating over 96% of reflected power) when the phase approaches resonance ($0^\circ$).
- Classical **Alternating Optimization (AO)** algorithms optimize phase angles in the abstract domain and frequently fall into deep attenuation dips by enforcing rigid phase alignment.

### Proposed Solution
Instead of searching in the abstract phase domain, this project models each unit cell as an equivalent **lumped resonant RLC circuit** and directly searches the **$4N$-dimensional physical hardware component space**:
$$\mathbf{x} = [L_{1,1..N},\ L_{2,1..N},\ C_{1..N},\ R_{1..N}] \in \mathbb{R}^{4N}$$
where:
- $L_{1,n}$: Bottom-layer microstrip inductance ($2.0 - 10.0\text{ nH}$)
- $L_{2,n}$: Top-layer microstrip inductance ($1.0 - 5.0\text{ nH}$)
- $C_n$: Microwave varactor diode capacitance ($0.2 - 5.0\text{ pF}$)
- $R_n$: Parasitic ohmic & dielectric resistance ($0.1 - 0.5\ \Omega$)

---

## Key Features & Pipeline

1. **Equivalent RLC Circuit Modeling:** Direct calculation of surface impedance $Z_n(L_{1,n}, L_{2,n}, C_n, R_n)$ and physical complex reflection coefficient $v_n = \frac{Z_n - Z_0}{Z_n + Z_0}$.
2. **Physics Inverse Solver (Nelder-Mead):** Independently solves the inverse electromagnetic matching problem per element to generate physics-informed seeding vectors.
3. **Adaptive Particle Swarm Optimization (PSO):**
   - **Intelligent Swarm Seeding:** Injects the inverse solver solution as the elite leader, augmented with Gaussian perturbation scouts and uniform global explorers.
   - **Dynamic Inertia Weight:** Linearly decays from $w_{\max} = 0.9$ to $w_{\min} = 0.3$ to seamlessly shift from global exploration to localized exploitation.
   - **Local Perturbation Refinement:** Fine-tunes top-performing particles to avoid deceptive local sub-optima in high-dimensional continuous space.
4. **Superior Performance:** Outperforms traditional phase-only AO algorithms by up to **+66.7% achievable rate gain** at near-field distances ($d = 495\text{ m}$) with $N = 40$ elements.

---

## Project Structure

```bash
├── Hybrid_PSO_Nelder_Mead_IRS_Report.pdf   # Comprehensive 19-page IEEE-format Technical Report
├── hybrid_pso_nelder_mead_irs.py          # Complete simulation & optimization pipeline in Python
├── .gitignore                         # Standard Python gitignore
└── README.md                          # Project documentation
```

---

## 🛠️ Installation & Requirements

Ensure you have Python 3.8+ installed, then install the required dependencies:

```bash
pip install numpy scipy matplotlib
```

---

## 💻 Usage

Run the complete Monte Carlo simulation and benchmark script:

```bash
python hybrid_pso_nelder_mead_irs.py
```

The script will:
1. Initialize hardware configuration ($M=2$ AP antennas, $N=40$ IRS elements, carrier frequency $f=2.4\text{ GHz}$).
2. Execute Monte Carlo channel realizations across distances $d \in [470\text{m}, 500\text{m}]$.
3. Benchmark 4 schemes:
   - **Practical IRS (Proposed Hardware RLC via PSO)**
   - **Ideal IRS (Theoretical Upper Bound)**
   - **Practical IRS (Conventional AO Baseline)**
   - **No IRS (Direct Channel Lower Bound)**
4. Plot and display the achievable rate comparison figure.

---

## Results Summary

| Distance $d$ (m) | No IRS (bps/Hz) | Practical AO (bps/Hz) | Proposed Hardware PSO (bps/Hz) | Ideal IRS (bps/Hz) | Proposed Gain vs AO |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **470** | 0.196 | 0.280 | **0.390** | 0.449 | **+39.3%** |
| **480** | 0.196 | 0.380 | **0.569** | 0.655 | **+49.7%** |
| **490** | 0.194 | 0.812 | **1.267** | 1.488 | **+56.0%** |
| **495** | 0.192 | 1.401 | **2.336** | 2.658 | **+66.7%** |
| **500** | 0.190 | 3.011 | **4.411** | 4.887 | **+46.5%** |

---

## Authors

- **Mac Minh Phuc** (Student ID: 202517046)
- **Nguyen Viet Thanh** (Student ID: 202517062)

*Group 3 — Project Electronics for IT*

---

## License
This project is open-source under the MIT License.
