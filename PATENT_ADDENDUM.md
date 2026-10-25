# Draft technical addendum to original PQC banking invention disclosure

**Provisional descriptive name:** Cross-Tier Attestation and Risk-Bound Quantum-Safe Transaction Enforcement (part of DARP-PQC)

**Legal status:** Technical disclosure *draft for institutional IP cell / patent counsel review*. This is not a vetted patent claim, patentability opinion, or filing-ready specification. Do not publish publicly before coordinating any intended filing with authorized counsel.

## Technical problem

Banks often depend on cryptographic assets operated by direct suppliers and sub-tier subcontractors. Identifying risk in a graph does not itself enforce any provider accountability at transaction processing time. A bank can encrypt its own messages using PQC while external cryptographic dependencies remain unacknowledged or outside its direct control.

## Proposed technical mechanism

1. Ingest bank/third-party/sub-tier dependency data and determine direct quantum-risk factors for reachable cryptographic assets.
2. Calculate maximum propagated path risk for each reachable asset, and for each service select risk-significant external assets by dependency tier under configurable threshold and count limits.
3. Compute a service policy including NIST-standardized PQC profile, risk-evidence digest and monotonic policy epoch.
4. Obtain short-lived ML-DSA-signed acknowledgements from registered signers representing the selected provider assets. Each message signs service ID, provider and tier, transaction record hash, action, policy digest, risk evidence digest, epoch, timestamps and a nonce.
5. Use an enforcing banking gateway that **refuses transaction creation and acceptance** when signed dependency evidence is missing, inconsistent, expired, duplicated or signed by an unregistered key.
6. Encrypt the transaction using an ML-KEM-derived AES-256-GCM key; bind the same risk evidence to bank signature, employee signed authorization and authenticated encryption context.
7. Upon assumed remediation, recompute risk and update the authoritative policy epoch; previously bound transactions fail on stale epoch/digest.

## Technical effects demonstrated in synthetic V1

- Encrypted and authenticated banking-record roundtrip succeeded with standardized PQC algorithms.
- The gateway required signatures from a direct third-party asset (A026 Cloud KMS) and a distinct sub-tier asset (A041 Cloud Sub-KMS), both selected by path-risk contribution for S01.
- Missing/substituted provider evidence, stale evidence, wrong transaction payload, duplicated claims, unauthorized bank actor, and replay were rejected in controlled tests.
- Added cross-tier assurance increased local median workflow time from 37.083 ms to 62.510 ms, and median serialized envelope size from 20,704 to 34,204 bytes (20 runs). Do not claim reduced computational latency.
- Existing dynamic graph remediation improved synthetic ecosystem risk index by 43.61% at normalized migration budget 7.5; no real bank migration was carried out.

## Potential inventive-step emphasis (subject to prior-art search)

Claim a *technical interaction* between graph-derived external dependency thresholds, risk-evidence hashing, versioned crypto-policy enforcement, independently signed transaction-scoped third-party/sub-tier acknowledgements, and fail-closed banking data protection. **Do not claim new ML-KEM/ML-DSA/SLH-DSA mathematics or that signed acknowledgements prove actual PQC migration.** The idea is system-level; prior art in supply-chain attestations, policy tokens and PQC migration could materially narrow what is patentable.

## Threat model and weaknesses still to resolve before production

- Authentic enrollment of independent provider keys and certificate revocation are assumed, not implemented.
- Provider signatures certify an acknowledgement statement only; they do not independently verify vendor migration or prevent vendor mishandling of plaintext.
- Static ML-KEM recipient keys do not provide forward secrecy if later compromised; HNDL threat mitigation requires dedicated forward-secret key establishment, secure retention and key rotation designs.
- Distributed, persistent anti-replay, nonce tracking, policy synchronization and HSM key custody are not implemented.
- Synthetic scoring thresholds and provider selection require sensitivity and empirical validation.
- Real bank interface integration, security review, formal methods and independent testing are not completed.

## Supporting evidence artifacts

`pqc_layer/multitier_assurance.py`, `pqc_layer/banking_gateway.py`, `pqc_layer/darp_pqc.py`, `experiments/banking_gateway_demo.py`, `experiments/cross_tier_final_evaluation.py`, `tests/test_cross_tier.py`, `results/tables/cross_tier_ablation.csv`, `results/tables/cross_tier_proof_demo.json`.

**Original disclosure compatibility:** Retain the previous technical disclosure as background and add the above feature; revise any earlier claim of complete, forward-secret, end-to-end quantum safety or absolute novelty before a formal filing.
