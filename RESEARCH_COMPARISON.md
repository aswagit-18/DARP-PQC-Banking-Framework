# Peer-reviewed literature comparison and research positioning

**Caution:** The referenced studies have different objectives, testbeds and overhead definitions. Do not numerically compare milliseconds across studies as an algorithm-performance ranking.

| Peer-reviewed paper | Evidence available in the paper | What our synthetic research prototype investigates differently | Numerical comparison |
|---|---|---|---|
| Hasan et al., *A Framework for Migrating to Post-Quantum Cryptography: Security Dependency Analysis and Case Studies*, **IEEE Access** 12 (2024), 23427–23450. DOI: [10.1109/ACCESS.2024.3360412](https://doi.org/10.1109/ACCESS.2024.3360412) | Enterprise cryptographic asset inventory, migration steps and graph-based dependency case studies useful for prioritizing crypto-system replacement | Banking-specific external-provider + sub-tier risk propagation, marginal ecosystem-wide risk-reduction ranking, and enforcement of provider-signed risk acknowledgements on protected transactions | Not the same experiment; qualitative methodological comparison only |
| *Migrating Software Systems Toward Post-Quantum Cryptography — A Systematic Literature Review*, **IEEE Access** 12 (2024), 132107–132126. DOI: [10.1109/ACCESS.2024.3450306](https://doi.org/10.1109/ACCESS.2024.3450306) | Identifies phases, complexity and organizational difficulties across reported migrations | Directly experiments on linked inter-organizational banking risk and a cryptographically enforced policy-bound record rather than presenting a systematic review | Not comparable |
| Olushola and Meenakshi, *Design and implementation of an authenticated post-quantum session protocol using ML-KEM, ML-DSA, and AES-256-GCM*, **Frontiers in Physics** 13:1723966 (published Jan 2026). DOI: [10.3389/fphy.2025.1723966](https://doi.org/10.3389/fphy.2025.1723966) | Authenticated post-quantum session design, primitive and system benchmarks; details session key schedule and forward secrecy in its proposed setting | Our code focuses on *risk-graph-governed, multi-party dependency attestations and migration-policy enforcement*, not a new handshaking protocol. Our static recipient KEM **does not achieve the study's forward secrecy properties** | Our Python/OpenSSL CLI end-to-end wall time is NOT comparable to their native primitive timings |

## Our within-prototype controlled comparisons

1. **Risk-model baseline comparison:** 43.61% modeled V1 ecosystem-risk reduction at budget 7.5 vs 24.96% (best baseline in the tested set).
2. **Same service, same cryptographic profile:** DARP-PQC with cross-tier gate vs DARP-PQC without gate. Only the gate provides short-lived cryptographic third-party/sub-tier acknowledgements; extra work and bytes are measured and disclosed.
3. **Signature-family exploration:** ML-DSA default vs optional SLH-DSA hash-based implementation, signed and verified on the same host. Only laboratory cost/size, not an argument for arbitrary substitution.
4. **Adversarial functional tests:** missing proof, duplicate proof, altered signature, changed record, expired *validly signed* proof, replay, and stale policy state are rejected. This is behavior under the implemented threat model, not a mathematical security proof.

## Research gap (defensible wording)

“Prior research has established PQC migration frameworks, graph-based dependency analysis, and authenticated post-quantum session protocols. This work investigates whether **risk evidence from banking internal, direct third-party and sub-tier cryptographic chains can be connected to dynamic ecosystem-level remediation and enforced transaction-specific, post-quantum-signed provider acknowledgements**. Its contribution is evaluated as a system-level integration and security-policy enforcement mechanism rather than a newly invented encryption algorithm.”

## Sources / standards (not sources of algorithm originality)

- NIST **FIPS 203** ML-KEM (2024): https://csrc.nist.gov/pubs/fips/203/final
- NIST **FIPS 204** ML-DSA (2024): https://csrc.nist.gov/pubs/fips/204/final
- NIST **FIPS 205** SLH-DSA (2024): https://csrc.nist.gov/pubs/fips/205/final
- NIST **SP 800-227** recommendations for KEMs (2025): https://csrc.nist.gov/pubs/sp/800/227/final

A focused patent prior-art investigation is still required. Merely integrating existing components does not guarantee inventive step or patentability.
