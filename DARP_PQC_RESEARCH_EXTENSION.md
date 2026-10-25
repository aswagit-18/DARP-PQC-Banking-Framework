> **October 11 final-edition note:** This file describes the earlier DARP-PQC stage. The newer **cross-tier ML-DSA-signed provider acknowledgement gate, strict gateway, SLH-DSA benchmark, 37 tests, and latest measurements** are documented in `PROJECT_COMPLETION_GUIDE.md`, `EXACT_CODE_CHANGES.md`, and `RESEARCH_COMPARISON.md`. Earlier reported timings are prior prototype measurements and should not be substituted for current output.

# DARP-PQC: Dependency-Aware Risk-Bound Post-Quantum Protection

## 1. Scope and research position

This is a **research prototype** that extends the original PQC Banking Risk Framework while preserving its original risk propagation and migration-prioritization methodology. It implements **real, standardized** post-quantum algorithms for protecting *synthetic* banking transaction records, rather than implementing an original unreviewed cryptographic primitive.

**Working invention hypothesis (NOT an established patentability finding):** A server-controlled, time-versioned security policy derived from multi-tier quantum-risk propagation can be cryptographically bound to each banking transaction's confidentiality and authorization operations, with epoch-enforced updates after migration.

**The proposed system-level algorithm is DARP-PQC.** ML-KEM, ML-DSA, HKDF and AES-GCM are existing standardized/reviewed primitives. Claiming their mathematical invention, a new quantum cipher, provable future resistance, or guaranteed patent novelty would be incorrect.

## 2. Architectural extension (existing framework unchanged)

```text
EXISTING                       DARP-PQC EXTENSION
Asset inventory
  -> Third/sub-tier graph
  -> Direct & inherited risk
  -> Ecosystem risk
  -> Migration ΔER ranking ---> Risk-attested policy + monotonically increasing epoch
                                          |
                                          +--> Category-3 PQC profile
                                          |       ML-KEM-768 / ML-DSA-65
                                          |
                                          +--> Category-5 PQC profile
                                          |       ML-KEM-1024 / ML-DSA-87
                                          |
                                          v
                              ML-DSA-signed actor, transaction & policy
                                          v
                              HKDF-SHA256 from ML-KEM shared secret
                                          v
                              AES-256-GCM-encrypted banking record
                                          v
                              Verify policy, decrypt, verify signature,
                              enforce RBAC + request TTL + replay control
```

The system determines a **minimum** profile for each banking service. The sender does not choose a weaker suite. The minimum is always ML-KEM-768 and ML-DSA-65; elevated service risks select ML-KEM-1024 and ML-DSA-87. NIST does not prescribe this risk-threshold policy; it is a **proposed model** requiring further evaluation.

## 3. Proposed algorithm

For banking service `s`, the existing model supplies:

- `TR_s` = total service risk, including direct and inherited risk;
- `C_s` = business criticality;
- `M_s` = maximum sub-tier strongest-path quantum-risk contribution;
- `H_s` = maximum HNDL exposure among current contributing vulnerable dependencies.

Proposed profile selection:

```text
if TR_s >= 0.85 or M_s >= 0.70 or (C_s >= 0.95 and H_s >= 0.85):
    profile_s = ELEVATED (ML-KEM-1024 + ML-DSA-87)
else:
    profile_s = STANDARD (ML-KEM-768 + ML-DSA-65)
```

Thresholds are preliminary synthetic-research parameters, **not security-strength proofs**. Future experiments must vary them and measure sensitivity, scalability, and overhead.

Define a policy object with `service_id`, `risk_evidence_digest`, selected PQC profile, and `policy_epoch`. The evidence digest is SHA-256 over canonical relevant path contributions, endpoint vulnerabilities, HNDL exposure, and service-risk values. The policy digest is SHA-256 over that evidence digest and the selected profile. An authoritative server-side registry holds this policy. The current binding additionally includes the banking action and exact PQC algorithms.

For a transaction `T`:

1. Obtain the service's **authoritative** policy and bind `(service, action, epoch, evidence digest, policy digest, KEM, signature algorithm)`.
2. Sign `(transaction, binding)` with the policy-required ML-DSA private key.
3. Sign an RBAC authorization request covering the same `(transaction, binding)` and a fresh nonce/time window.
4. Seal the payload using ML-KEM encapsulation; derive an AES-256-GCM key with HKDF-SHA256 and the binding as authenticated additional data (AAD); use a fresh 96-bit AES-GCM nonce.
5. Receiver checks the binding and algorithm against the **server policy**, decapsulates ML-KEM, verifies AES-GCM authentication, then verifies both ML-DSA signatures, registered identity, role, resource/action, expiry, and nonce freshness.
6. After migration, recompute risk, publish a strictly higher policy epoch, and reject messages carrying an old policy binding.

This combines standardized cryptography with an auditable *graph-risk-to-cryptographic-policy enforcement mechanism*. It is the integration—not the raw algorithms—that is proposed for novelty examination.

## 4. Local experimental results — actually executed

### 4.1 Existing synthetic ecosystem

- 50 assets, 10 banking services, 77 dependency input rows, 71 unique directed graph edges.
- Original baseline ecosystem risk: **0.778727**.
- Existing equal-budget (7.5 cost units) migration study: dynamic ΔER/cost **43.61%** ER reduction, compared with criticality-first **24.96%**, direct-risk-first **23.79%**, HNDL-first **22.47%**.
- These results came from the existing synthetic risk framework; the security extension **does not silently change the ER methodology**.

### 4.2 DARP-PQC profile assignments

From fresh V1 recomputation:

- **6/10 services:** elevated ML-KEM-1024 + ML-DSA-87.
- **4/10 services:** standard ML-KEM-768 + ML-DSA-65.
- Category-3 quantum-resistant protection is maintained for every service, including lower-risk ones.

### 4.3 End-to-end synthetic banking workflow (15 runs per scenario)

| Scenario | Service | Median end-to-end ms | p95 ms | JSON envelope bytes |
|---|---|---:|---:|---:|
| Fixed-PQC baseline, no graph-policy binding | S02 | 25.917 | 30.002 | 14,263 |
| DARP-PQC standard | S02 | 27.719 | 32.188 | 15,406 |
| DARP-PQC elevated | S01 | 28.653 | 30.238 | 20,744 |

**Measurement boundary:** Python + OpenSSL CLI process startup + temporary-file I/O + serialization + real ML-KEM, ML-DSA, HKDF, AES-GCM, authorization and decryption/verification. These are **not optimized native primitive timings**. Results are environment-dependent and 15 iterations are preliminary, not a statistically rigorous throughput study. The elevated case uses a different service and stronger algorithms; it is not an isolated performance treatment. Fixed and standard DARP rows are from the same service and host, but also differ in serialized evidence size. Full metadata is in `results/tables/darp_pqc_benchmark_metadata.json`.

Observed artifact sizes:

| Artifact | Measured bytes |
|---|---:|
| ML-KEM-768 ciphertext | 1,088 |
| ML-KEM-1024 ciphertext | 1,568 |
| ML-DSA-65 signature | 3,309 |
| ML-DSA-87 signature | 4,627 |

### 4.4 Security/property tests

The new module passed 12 tests: both profile roundtrips, ciphertext tamper detection, policy digest alteration, wrong-service binding, algorithm downgrade, policy epoch rollback, old-policy rejection, nonce replay, unauthorized role, weaker signing key, and no plaintext/private-key export in the envelope. These are **correctness tests**, not formal protocol proofs or penetration testing. Tests may overlap several conditions in a single case. The legacy framework and earlier PQC demo also remain in the package.

### 4.5 Remediation-triggered policy update demonstration

A **controlled counterfactual** assumes remediation of nine currently vulnerable assets reachable from S01 Core Banking. It does not perform real PQC migration of those assets. Under this assumption:

- ecosystem risk: **0.778727 -> 0.607728**;
- S01 total service-risk score: **0.892631 -> 0.0** in this test scenario;
- S01 approved profile: **elevated -> standard**, while retaining Category-3 PQC;
- policy epoch: **1 -> 2**;
- stale **DARP-PQC** encrypted message from epoch 1 rejected; fresh epoch-2 protected message accepted.
- the **fixed-PQC comparison** (which intentionally has no risk-policy binding) accepted a pre-update encrypted request after the update. That is a policy-enforcement distinction, **not a cryptographic failure** of its ML-KEM/ML-DSA protection.

This is stronger experimental evidence of *risk-to-cryptographic-policy coupling* than a standalone ML-KEM demonstration, but the scenario is deliberately extreme and synthetic.

## 5. Peer-reviewed publication comparison — do not mix unlike latency metrics

**Paper A:** A. Olushola and S. P. Meenakshi, *Design and implementation of an authenticated post-quantum session protocol using ML-KEM (Kyber), ML-DSA (Dilithium), and AES-256-GCM*, **Frontiers in Physics** (published January 8, 2026), DOI: [10.3389/fphy.2025.1723966](https://doi.org/10.3389/fphy.2025.1723966).

- Similarity: real ML-KEM, ML-DSA, and AES-256-GCM for authenticated confidentiality; reports about **0.50–0.70 ms** for its optimized/research session benchmark, and 1,000-run hardware-dependent experiments.
- Difference: our proof-of-concept uses OpenSSL CLI processes and adds dependency-graph policy generation, per-service profile enforcement, signed risk evidence context, epoch invalidation, and RBAC; we do **not** claim our ~26–29 ms full Python/CLI workflows outperform that session handshake.
- This paper establishes that combining ML-KEM, ML-DSA and AES-GCM is **not by itself novel**. Some results and comparisons within the paper use different measurement boundaries; avoid inferring equal implementations/hardware.

**Paper B:** *Cybersecurity in the quantum era: Assessing the impact of quantum computing on infrastructure*, **Computers & Security** (Elsevier, 2026), DOI: [10.1016/j.cose.2026.104917](https://doi.org/10.1016/j.cose.2026.104917).

- Similarity: multi-layer quantum-risk assessment and the need for algorithm selection and migration. Its published table lists illustrative ML-DSA-65 signing **0.136 ms** and verification **0.056 ms**.
- Difference: those are primitive-level timings, while our ~26–29 ms values are whole local CLI workflows; not a valid numerical speed comparison. Our extension measures the additional cost of coupling the banking dependency risk engine to a traceable cryptographic policy.

**Standards / primary references (not peer-reviewed comparison baselines):**

- NIST FIPS 203 (2024), ML-KEM: https://doi.org/10.6028/NIST.FIPS.203
- NIST FIPS 204 (2024), ML-DSA: https://doi.org/10.6028/NIST.FIPS.204
- NIST SP 800-227 (2025), KEM deployment guidance: https://doi.org/10.6028/NIST.SP.800-227
- OpenSSL 3.5 support for PQC: https://openssl-corporation.org/blog/2025-04-08-openssl-35-final-release.html

## 6. Honest novelty and patent positioning

**Do not file claims on:** the standard ML-KEM algorithm, standard ML-DSA algorithm, AES-GCM, use of graph analysis, cryptographic agility, risk scores, or elementary RBAC in isolation.

**Candidate technical claim scope for patent-professional review:**

> A computer-implemented control method that maintains a multi-tier cryptographic dependency graph for banking services; computes direct and inherited quantum-risk provenance; derives a server-authoritative cryptographic protection profile; cryptographically binds both the protection profile and a versioned risk-evidence digest to transaction confidentiality and quantum-resistant authorization; invalidates previously authorized profile epochs upon recalculated migration-risk state; and denies transactions whose cryptographic algorithms, risk-policy digest, or epoch differ from the server-authoritative policy.

This is a research **candidate**. Similar risk-adaptive cryptographic controls and PQC migration systems already exist in literature and patents. No comprehensive novelty/inventive-step examination, freedom-to-operate opinion, or successful patent review is asserted. Jurisdiction-specific patentable-subject-matter rules may also matter. Coordinate with the university IP cell / qualified patent agent before public disclosure.

## 7. Known limitations and security caveats

1. No guarantee against all future quantum attacks. Standardized PQC is believed resistant to known classical/quantum attacks under its assumptions; implementations can still fail.
2. No forward secrecy claim: a recipient KEM private key compromised later can endanger old ciphertexts under this **static-recipient-key demonstration**. A real session design needs suitable ephemeral authenticated key exchange and rekeying, including proper use of TLS where relevant.
3. Recipient public keys and signer identities are provisioned as trusted local keys; no production-grade PQC PKI, certificate verification, HSM or independent key-management service exists here.
4. The in-memory replay cache and policy registry would need durable, shared, synchronized server storage, authenticated deployment and anti-rollback controls across processes.
5. Side channels, endpoint compromise, metadata leakage, transaction fraud, traditional database access, and third-party provider security are outside the direct protection guarantee.
6. The policy formula and cutoffs have not been optimized or externally validated. A changed risk score never proves an asset has been actually migrated.
7. The extension protects a specific **synthetic transaction data flow**, not every current banking privacy exposure or every deployed RSA/ECC system.
8. No financial institution, customer record, quantum computer or real quantum attack was used in testing.

## 8. Files, reproduction, and deliverables

```
pqc_layer/crypto_backend.py           # standardized PQC via OpenSSL 3.5+
pqc_layer/access_control.py          # ML-DSA-signed RBAC
pqc_layer/transaction_demo.py        # fixed-PQC comparison
pqc_layer/darp_pqc.py                # NEW risk-bound security mechanism
experiments/darp_pqc_evaluation.py   # NEW comparison benchmark
experiments/darp_policy_migration_demo.py  # NEW remediation -> policy -> stale rejection
experiments/pqc_operations_demo.py   # encryption + signature baseline
experiments/pqc_benchmark.py         # primitive benchmark demo
tests/test_darp_pqc.py               # NEW security tests
results/tables/darp_pqc_workflow_benchmark.csv
results/tables/darp_pqc_policy_selection.json
results/tables/darp_pqc_benchmark_metadata.json
results/tables/darp_policy_migration_demo.json
```

From project root after installing requirements and ensuring OpenSSL >= 3.5:

```bash
python -m unittest discover -s tests -v
python -m experiments.darp_pqc_evaluation --iterations 15
python -m experiments.darp_policy_migration_demo
python -m experiments.pqc_operations_demo
```

See `RUN_DARP_PQC.md` for macOS setup.
