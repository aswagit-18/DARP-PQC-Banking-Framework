# Three-way DARP-PQC comparison — controlled local prototype

Fixed PQC is an **in-project, paper-inspired baseline**; it is NOT the original authors' code.
All versions use synthetic Core Banking (S01), ML-KEM-1024, ML-DSA-87, AES-256-GCM,
the same test payload, the same host and the same number of repetitions.
The cross-tier variant adds signed simulated third-party and sub-tier acknowledgements.

| Variant | Median time (ms) | p95 (ms) | Envelope (bytes) | Extra provider signatures |
|---|---:|---:|---:|---:|
| Fixed PQC (paper-inspired) | 79.280 | 97.337 | 19,556 | 0 |
| DARP-PQC without tier gate | 79.527 | 82.562 | 20,704 | 0 |
| Full DARP-PQC with tier gate | 158.084 | 184.637 | 34,204 | 2 |

## Security enforcement

| Check | Fixed PQC | Risk-bound DARP | Full DARP |
|---|---|---|---|
| Valid encrypted signed transaction | ACCEPT | ACCEPT | ACCEPT |
| Enforce third-party acknowledgement | NOT_IMPLEMENTED | NOT_IMPLEMENTED | ENFORCED |
| Enforce sub-tier acknowledgement | NOT_IMPLEMENTED | NOT_IMPLEMENTED | ENFORCED |
| Missing sub-tier acknowledgement | NOT_IMPLEMENTED | NOT_IMPLEMENTED | REJECT |
| Missing all external acknowledgements | NOT_IMPLEMENTED | NOT_IMPLEMENTED | REJECT |
| Duplicate external acknowledgement | NOT_IMPLEMENTED | NOT_IMPLEMENTED | REJECT |
| Old policy epoch after synthetic revision | NO_POLICY_EPOCH_CHECK | REJECT | REJECT |

## Research interpretation

- Fixed PQC already encrypts and signs data with quantum-resistant algorithms.
- Risk-bound DARP additionally ties transactions to a bank service's authoritative risk policy and epoch.
- Full DARP additionally requires signed acknowledgements from graph-selected third-party and sub-tier dependencies.
- Missing/duplicate acknowledgements are **not protocol checks** in the first two variants; mark N/A, not unsafe.
- These are policy-enforcement differences; they do not prove superior primitive cryptographic strength.
- Median timings include Python/OpenSSL CLI, temp-file I/O, local attestations and JSON serialization.
- No live bank providers, TLS session establishment, network transport or audited identity infrastructure.
- The ecosystem-risk improvement chart is a separate synthetic optimization experiment, not measured in the reference paper.

## Reference context

Olushola and Meenakshi (2026), *Design and implementation of an authenticated post-quantum session protocol using ML-KEM (Kyber), ML-DSA (Dilithium), and AES-256-GCM*, Frontiers in Physics.
https://doi.org/10.3389/fphy.2025.1723966
Their primitive microbenchmarks are **not directly comparable** to this Python/OpenSSL end-to-end experiment.
The published paper's security-session protocol is not reproduced here; fixed PQC is our own functional comparator.

## Plots

- `results/figures/three_way_latency_comparison.png`
- `results/figures/three_way_envelope_size.png`
- `results/figures/three_way_migration_baselines.png` (if the prior V1 result table is present)
