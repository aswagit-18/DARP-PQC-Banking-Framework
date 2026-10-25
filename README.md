# FINAL INTEGRATED PQC BANKING RESEARCH EDITION — OCTOBER 2026

This edition preserves the original risk propagation and dynamic migration framework, adds real NIST ML-KEM / ML-DSA encrypted transaction processing, an independent SLH-DSA signature benchmark, and **cross-tier, risk-selected, post-quantum-signed provider acknowledgements enforced by a strict bank gateway**.

**START HERE:** [`PROJECT_COMPLETION_GUIDE.md`](PROJECT_COMPLETION_GUIDE.md) | [`EXACT_CODE_CHANGES.md`](EXACT_CODE_CHANGES.md) | [`RESEARCH_COMPARISON.md`](RESEARCH_COMPARISON.md) | [`PATENT_ADDENDUM.md`](PATENT_ADDENDUM.md)

Run `bash run_complete.sh` after installing requirements and providing OpenSSL >=3.5. Research-only and synthetic; not real banking deployment, formal crypto proof or established patent.

---

# PQC Banking Risk Framework

A reproducible research prototype for **multi-tier, path-aware post-quantum cryptography (PQC) risk propagation and migration prioritization in digital banking ecosystems**.

## Core contribution

The framework models cryptographic risk across four dependency levels:

`Banking Service -> Internal Asset -> Third-Party Provider -> Sub-Tier Provider`

It then:

1. computes direct contextual quantum-risk scores for cryptographic assets;
2. identifies strongest service-to-asset dependency paths;
3. propagates vulnerable-asset risk along dependency-strength-weighted paths;
4. estimates inherited service-level quantum risk;
5. computes a criticality-weighted ecosystem risk (ER);
6. simulates each possible remediation as a counterfactual quantum-safe state;
7. measures marginal ecosystem risk reduction, `Delta ER`;
8. ranks actions by `Delta ER / migration cost`; and
9. dynamically recomputes priorities after every selected migration.

The main novelty claim should be framed around the **combination** of multi-tier banking/vendor/sub-tier dependencies, path-aware inherited risk, counterfactual ecosystem-risk reduction, and dynamic cost-aware re-ranking. Do not claim that dependency graphs, PQC algorithms, or HNDL are individually novel.

## Project structure

```text
PQC_Banking_Risk_Framework_Final/
├── data/                  # V1: 50 assets, 10 services
├── data_v2/               # V2: 250 assets, 20 services
├── src/
│   ├── data_loader.py
│   ├── risk_model.py
│   ├── graph_builder.py
│   ├── propagation.py
│   ├── ecosystem_risk.py
│   ├── remediation.py
│   ├── prioritization.py
│   └── baselines.py
├── experiments/
│   ├── final_evaluation.py
│   ├── sensitivity_analysis.py
│   ├── ablation_study.py
│   ├── budget_sweep.py
│   ├── explainability_report.py
│   ├── scalability_analysis.py
│   ├── compare_three_models.py
│   └── generate_final_figures.py
├── results/
│   ├── tables/
│   └── figures/
├── tests/
│   └── test_framework.py
├── main.py
├── dataset_generator.py
├── requirements.txt
└── system_architecture.png
```

## Installation

Python 3.10+ is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the complete V1 framework

```bash
PQC_DATASET=v1 python3 main.py
```

## Run final experiments

```bash
PQC_DATASET=v1 python3 experiments/final_evaluation.py
PQC_DATASET=v1 python3 experiments/sensitivity_analysis.py
PQC_DATASET=v1 python3 experiments/ablation_study.py
PQC_DATASET=v1 python3 experiments/budget_sweep.py
PQC_DATASET=v1 python3 experiments/explainability_report.py
python3 experiments/scalability_analysis.py
python3 experiments/generate_final_figures.py
```

## Run tests

```bash
python3 -m unittest discover -s tests -v
```

## Dataset selection

The loader supports:

```bash
PQC_DATASET=v1 ...
PQC_DATASET=v2 ...
```

- **V1:** 50 assets, 10 banking services, 77 dependency records (71 unique graph edges after strongest-edge handling of six duplicate endpoint pairs).
- **V2:** 250 assets, 20 banking services, 720 unique dependency edges.

V1 is the fully evaluated reference experiment included in this package. V2 is the larger synthetic scalability dataset.

## Final V1 headline result

With an equal migration budget of 7.5 normalized cost units:

| Strategy | Final ER | Risk reduction | Reduction % |
|---|---:|---:|---:|
| Proposed Dynamic DeltaER/Cost | 0.439112 | 0.339614 | 43.61% |
| Business Criticality First | 0.584322 | 0.194405 | 24.96% |
| Direct Risk First | 0.593505 | 0.185221 | 23.79% |
| HNDL Risk First | 0.603723 | 0.175003 | 22.47% |

These results are from the included synthetic V1 dataset and should not be generalized to real banks without external validation.

## Important implementation refinements

This final package includes two scientific/reproducibility fixes:

1. **Duplicate dependency handling:** a NetworkX `DiGraph` silently overwrites repeated source-target edges. V1 contains six duplicate endpoint pairs, so graph construction now retains the strongest dependency strength and validation reports the duplicates.
2. **Quantum-only service direct risk:** PQC-safe/remediated internal assets contribute zero to service-level direct *quantum* risk while the denominator remains fixed over all internal service assets. This makes remediation monotonic and avoids counting non-quantum impact factors as residual quantum risk after remediation.

## Research limitation

The datasets are synthetic and risk parameters are controlled experimental values. The framework is a prototype for methodology evaluation, not a calibrated risk engine for production banking. External empirical validation and institution-specific calibration are required before operational deployment.


## Patent-preparation files

- `PQC_Banking_Patent_Technical_Disclosure_Draft.docx` - technical invention disclosure and draft claim set for professional review.
- `NOVELTY_AND_PATENT_POSITION.md` - recommended novelty focus and preliminary prior-art pressure.
- `SUBMISSION_CHECKLIST.md` - practical research/patent handoff checklist.

These files are drafting aids, not a legal patentability opinion.

---

## October 2026 research extension: DARP-PQC

A **real post-quantum banking-record security demonstration** has been added without replacing the original graph-based framework. It uses OpenSSL 3.5+ ML-KEM-768/1024, ML-DSA-65/87, HKDF-SHA256, AES-256-GCM, cryptographically signed RBAC, and a proposed dependency-risk-bound security-policy algorithm.

Read **`DARP_PQC_RESEARCH_EXTENSION.md`** for experimental findings, differences from peer-reviewed publications, a cautious patent-novelty proposal, and limitations. See **`RUN_DARP_PQC.md`** for exact installation/run commands and results files.

The extension is a research prototype, **not a security-audited banking product**. It claims originality only in the proposed integration and enforcement mechanism, subject to prior-art review—not in the underlying NIST cryptographic algorithms.
