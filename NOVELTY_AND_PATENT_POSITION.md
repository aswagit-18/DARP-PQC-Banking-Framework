# Novelty and Patent Positioning Note

## Recommended invention title

**System and Method for Dynamic Multi-Tier Post-Quantum Cryptographic Risk Propagation and Ecosystem-Aware Migration Prioritization in Digital Banking Networks**

## Recommended novelty focus

Do not position the invention as merely:

- a PQC risk score;
- a cryptographic inventory;
- a dependency graph;
- a banking migration plan; or
- cost-aware ranking.

Those ideas individually have substantial prior art.

The most defensible technical combination in this prototype is:

1. a directed banking cryptographic dependency graph with explicit **banking service, internal asset, direct external provider, and sub-tier provider** roles;
2. **path-aware inherited quantum-risk propagation** from vulnerable cryptographic assets through dependency-strength-weighted paths into banking services;
3. a service-criticality-weighted **ecosystem risk state**;
4. **counterfactual remediation simulation** for each candidate, where the candidate is changed to a quantum-safe state and the entire downstream ecosystem risk is recomputed;
5. calculation of a candidate-specific **marginal ecosystem risk reduction (`Delta ER`)** rather than ranking only the candidate's own local risk;
6. cost-normalized priority using `Delta ER / migration cost`;
7. **dynamic re-ranking after every selected remediation**, so the next candidate is selected from the changed ecosystem rather than from a fixed initial list; and
8. an explanation record linking each selected action to affected services, path depth, and strongest dependency path.

The combination above should be emphasized as the inventive concept. Each sub-feature alone is weaker from a patentability perspective.

## Important prior-art pressure

A preliminary, non-legal search identified several close references that materially narrow the claim space.

### 1. Cisco - US20250045422A1
**Post-quantum risk analysis using cipher suite dependency graphs and risk scoring using call paths**

Priority date: 4 Aug 2023.

Relevant overlap:
- PQC risk analysis;
- dependency graphs;
- cryptographic call paths;
- safe/unsafe scoring;
- remediation of unsafe cipher suites;
- aggregate target risk.

Distinction to emphasize:
- the proposed framework is not primarily a call-graph safety classifier;
- it models a banking ecosystem with service/internal/provider/sub-tier roles;
- it quantifies inherited risk across organizational dependency tiers;
- it counterfactually recomputes **ecosystem-wide** risk for every remediation candidate;
- it dynamically re-ranks candidates by marginal ecosystem risk reduction per cost.

### 2. AT&T - US12519809B2 / US20250150466A1
**Scalable assessment and prioritization of network asset cryptography for quantum risk mitigation**

Priority date: 8 Nov 2023. Granted 6 Jan 2026.

Relevant overlap:
- enterprise quantum-risk scoring;
- asset ranking;
- metadata such as business criticality and exposure;
- remediation actions and financial considerations.

Distinction to emphasize:
- the proposed framework is graph/path-driven rather than ML-based asset scoring;
- risk is inherited through explicit multi-tier banking dependencies;
- selection uses a counterfactual whole-ecosystem recomputation after each action.

### 3. Wells Fargo - US20250103720A1
**Post-quantum cryptography risk modeling**

Priority date: 16 Nov 2021. Application status shown as abandoned in the preliminary search, but it remains important prior art.

Relevant overlap:
- financial institution context;
- network/data-flow modeling;
- PQC risk;
- remediation cost;
- prioritization of valuable remediation;
- third-party indicator in node data;
- data shelf life and Q-Day modeling.

This is especially important. Broad claims such as "PQC risk modeling for a bank with remediation cost" are unlikely to be strong.

Distinction to emphasize:
- explicit multi-tier provider and sub-tier cryptographic dependency roles;
- deterministic dependency-strength path propagation into banking services;
- service-criticality-weighted ecosystem state;
- per-candidate counterfactual recalculation of the complete ecosystem state;
- dynamic marginal-risk/cost sequence rather than selecting a remediation only from an application/node risk score.

### 4. Hasan et al., IEEE Access (2024)
**A Framework for Migrating to Post-Quantum Cryptography: Security Dependency Analysis and Case Studies**

Relevant overlap:
- cryptographic inventories;
- graph-theoretic security dependency analysis;
- prioritization of cryptosystems for replacement.

Distinction:
- the project operationalizes banking service -> internal -> vendor -> sub-tier inherited risk and evaluates marginal ecosystem-risk reduction under a remediation budget.

### 5. Sharma et al., IEEE conference (2026)
**Dependency-Aware Post-Quantum Cryptography Migration Planning: Graph-Based Optimization for Enterprise Infrastructure**

Relevant overlap:
- dependency-aware PQC migration;
- dependency graph;
- risk-weighted prioritization;
- optimized migration ordering.

Distinction:
- that work emphasizes interoperability-safe migration ordering using reversed topological processing and graph centrality;
- this prototype emphasizes multi-tier banking/vendor inherited risk and counterfactual ecosystem-risk reduction per migration cost.

### 6. Europol / financial-services PQC migration guidance (2026)
Relevant overlap:
- financial-sector prioritization;
- shelf life, exposure, severity and migration time.

Distinction:
- guidance prioritizes business use cases using risk factors;
- this project implements graph-based inherited risk and per-remediation ecosystem recomputation across external dependency tiers.

## Draft claim strategy

A patent professional should consider claims around the **ordered computer-implemented process**, not around any single risk formula.

Potential independent method concept:

1. receive a banking cryptographic inventory and dependency records;
2. construct a directed graph distinguishing banking services, internal assets, direct providers and sub-tier providers;
3. determine a quantum-risk score for each cryptographic asset;
4. determine, for each banking service and each reachable asset, a selected dependency path and a dependency attenuation value derived from the path;
5. compute an inherited service risk from vulnerable reachable assets;
6. generate an ecosystem risk state from the service risks and service criticalities;
7. for each candidate remediation, create a counterfactual candidate state representing a quantum-safe replacement and recompute the ecosystem risk state;
8. compute the candidate's marginal ecosystem-risk reduction;
9. compute a migration priority from the marginal reduction and migration cost;
10. select a remediation, update the ecosystem state, and repeat steps 7-9 for remaining candidates; and
11. output a migration sequence and path-based explanation record.

Dependent claims may narrow to:

- strongest dependency path selection;
- product of edge dependency strengths;
- separate first-tier and sub-tier external provider nodes;
- HNDL/data-lifetime metadata;
- budget-constrained selection;
- affected-service count and path provenance output;
- threshold-based exclusion of quantum-safe assets;
- iterative recomputation until a cost budget is exhausted;
- separate handling of internal, third-party and sub-tier remediation ownership.

## Patentability caution

This package is a strong **technical invention disclosure and research prototype**, not a legal patentability opinion. The preliminary search shows substantial existing PQC risk/prioritization patents. Before filing a full specification, an Indian patent agent or other qualified patent professional should conduct a jurisdiction-specific novelty/inventive-step search and rewrite the claims around the narrow distinguishing combination above.

## Public-disclosure caution

If a patent filing is planned, coordinate filing timing before publishing a paper, GitHub repository, conference poster, thesis chapter, or public demo. Public disclosure can affect patent rights depending on jurisdiction.
