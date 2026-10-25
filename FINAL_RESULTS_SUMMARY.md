# Final Experimental Results Summary

## 1. Reference dataset

Primary reported results use **V1** because the complete baseline, dynamic, sensitivity, ablation and budget experiments were executed end-to-end on it.

- Banking services: 10
- Cryptographic/system assets: 50
- Asset tiers: 25 Internal, 15 Third-Party, 10 Sub-Tier
- Dependency rows: 77
- Unique directed graph edges after strongest-edge duplicate handling: 71
- Vulnerable assets (`quantum_vulnerability > 0.25`): 36
- Strongest vulnerable dependency paths in baseline evaluation: 63

A second synthetic scalability dataset (**V2**) contains 20 services, 250 assets and 720 unique dependency edges.

## 2. Baseline ecosystem risk

After direct risk, multi-tier propagation, inherited service risk and service-criticality weighting:

**Baseline Ecosystem Risk (ER) = 0.778727**

Highest inherited-risk services in the V1 baseline included ATM Network, Card Payments and Core Banking. The exact service-level results are stored in `results/tables/final_service_risks_v1.csv`.

## 3. Equal-budget strategy comparison

Migration budget: **7.5 normalized cost units**.

| Rank | Strategy | Budget used | Assets migrated | Final ER | Risk reduction | Risk reduction % | Reduction / cost |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | Proposed Dynamic DeltaER/Cost | 7.45 | 10 | 0.439112 | 0.339614 | 43.6115% | 0.045586 |
| 2 | Business Criticality First | 7.20 | 9 | 0.584322 | 0.194405 | 24.9645% | 0.027001 |
| 3 | Direct Risk First | 7.15 | 9 | 0.593505 | 0.185221 | 23.7851% | 0.025905 |
| 4 | HNDL Risk First | 7.40 | 9 | 0.603723 | 0.175003 | 22.4730% | 0.023649 |

On this synthetic dataset, the proposed method reduced ER by **43.61%**, compared with **24.96%**, **23.79%**, and **22.47%** for the three simpler baselines under the same nominal budget.

The improvement over the strongest baseline (Business Criticality First) is:

- absolute additional ER reduction: `0.339614 - 0.194405 = 0.145209`
- relative improvement in achieved risk reduction: approximately **74.7%**

This is an experimental result for the synthetic V1 scenario, not a claim about real banking networks.

## 4. Dynamic migration sequence

First ten dynamically selected remediations:

1. A022 - Fraud Detection API
2. A018 - Loan Processing API
3. A005 - Mobile API Gateway
4. A008 - Internet API Gateway
5. A009 - Internet Authentication
6. A020 - KYC API
7. A016 - Customer Identity Server
8. A025 - Enterprise Message Broker
9. A014 - Instant Payment Gateway
10. A001 - Core Banking PKI

The sequence is not merely the original ranking. The framework recalculates marginal ecosystem risk reduction after each migration. This is visible in cases where an asset's later marginal `Delta ER` differs from its original one-step estimate.

## 5. Budget robustness

The proposed strategy remained best at all three tested budgets:

| Budget | Proposed reduction | Best baseline reduction |
|---:|---:|---:|
| 2.5 | 12.85% | HNDL 12.71% |
| 5.0 | 30.53% | Business Criticality 20.99% |
| 7.5 | 43.61% | Business Criticality 24.96% |

Full table: `results/tables/budget_sweep.csv`.

## 6. Sensitivity analysis

Five direct-risk weight scenarios were tested:

- Equal Weights
- Quantum Emphasis
- Business Criticality Emphasis
- Data Lifetime Emphasis
- Exposure Emphasis

Across all five, the top one-step priority remained **A022 - Fraud Detection API**.

Baseline ER ranged from **0.774293 to 0.781640**, and A022's `Delta ER` ranged from **0.038166 to 0.038667**. This indicates local stability of the top recommendation to the tested weight perturbations.

Full table: `results/tables/sensitivity_analysis.csv`.

## 7. Ablation study

### 7.1 Multi-tier topology ablation

| Topology | ER |
|---|---:|
| Full Internal + Third-Party + Sub-Tier | 0.778727 |
| No Sub-Tier | 0.770724 |
| Internal Only | 0.753983 |

Removing sub-tier dependencies hides **0.008003** ER in this scenario. Modeling only internal assets hides **0.024744** ER relative to the full multi-tier model.

This supports the research motivation that vendor and sub-tier dependencies contribute inherited quantum risk that is not visible in internal-only assessment.

### 7.2 Prioritization ablation

Equal budget: 7.5.

| Variant | Risk reduction % |
|---|---:|
| Full dynamic DeltaER/Cost | 43.61% |
| Static initial DeltaER/Cost | 41.94% |
| Dynamic DeltaER only (no cost normalization) | 40.41% |

The full method outperformed both removal of dynamic re-ranking and removal of cost normalization on the V1 scenario.

Full tables: `results/tables/ablation_topology.csv` and `results/tables/ablation_prioritization.csv`.

## 8. Explainability evidence

The framework now produces an explainable priority table containing:

- asset and tier;
- algorithm;
- one-step `Delta ER`;
- migration cost;
- priority score;
- affected service count;
- strongest path risk;
- maximum dependency path depth;
- strongest named dependency path.

Examples:

- **A026 Cloud KMS** is a Third-Party asset affecting 4 banking services with maximum path depth 3.
- **A041 Cloud Sub-KMS** is a Sub-Tier asset affecting 7 banking services with maximum path depth 4.

This supports human review of why a third- or fourth-party remediation appears in the migration plan.

Full table: `results/tables/explainable_priorities.csv`.

## 9. Scalability prototype benchmark

Measured in the supplied execution environment:

| Dataset | Services | Assets | Dependency edges | Vulnerable assets | Baseline evaluation | Full initial candidate ranking |
|---|---:|---:|---:|---:|---:|---:|
| V1 | 10 | 50 | 71 | 36 | 0.0168 s | 0.5709 s |
| V2 | 20 | 250 | 720 | 216 | 0.0476 s | 10.5903 s |

V2 baseline ER was **0.850527** and the top one-step priority was **A032 Card Payments API Gateway 4**.

These timings are engineering measurements from one local environment and are not formal complexity guarantees.

## 10. What can be claimed from the experiments

Supported by the included synthetic experiments:

1. Multi-tier modeling exposes risk that is missed by reduced topologies.
2. Counterfactual ecosystem-risk reduction produces a migration ranking different from direct-risk, criticality and HNDL-only ranking.
3. Dynamic re-ranking adds value compared with a frozen initial ranking on the evaluated scenario.
4. Cost normalization improves equal-budget risk reduction on the evaluated scenario.
5. The top priority is stable across the tested direct-risk weight scenarios.
6. The prototype runs on a larger 250-asset / 720-edge synthetic ecosystem and produces a full initial candidate ranking.

## 11. What should NOT be claimed

Do not claim:

- the formulas are universally calibrated for all banks;
- the synthetic scores are real institutional measurements;
- the framework guarantees 43.61% improvement in production;
- the framework is the first ever PQC dependency graph;
- the framework is legally patentable without a professional prior-art and claim analysis.

The strongest defensible contribution is the integrated workflow combining **banking-specific multi-tier dependencies, path-aware inherited risk, counterfactual ecosystem-wide remediation impact, dynamic cost-aware re-ranking, and explainable path provenance**.


---
## October 2026: Final multi-tier post-quantum security extension

**See `PROJECT_COMPLETION_GUIDE.md` for authoritative current results and limitations.** Original V1 migration/risk results were rerun unchanged (ER 0.778727; proposed risk reduction 43.61%). Added standardized SLH-DSA-SHA2-128s alternative signature benchmark; ML-KEM/ML-DSA/AES-256-GCM remain the operational protocol. Added fail-closed third-party/sub-tier ML-DSA-signed acknowledgements cryptographically bound to service, current risk evidence, policy epoch and banking record.

On this host for V1 Core Banking, 20 repetitions of identical elevated PQC profile: DARP-PQC **37.083 ms** median and **20,704 bytes** vs strict cross-tier gateway **62.510 ms** median and **34,204 bytes**. This extra overhead reflects additional provider signatures and verification and full Python/OpenSSL process/file I/O.

All **37 tests passed**, including new cross-tier signature, freshness, record/policy binding, duplicate/missing provider and replay checks. V2 requirement selector ran on 20 services/250 assets with 40 selected signed-evidence requirements.

**These are simulated supplier acknowledgements, not proof the providers deploy PQC. Static ML-KEM recipient keys lack forward secrecy. This is not a production-grade banking-security evaluation or established patent novelty.**
