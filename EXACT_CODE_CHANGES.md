# Exact changes — original DARP project to final cross-tier PQC security edition

Original graph, risk, propagation, prioritization and synthetic datasets remain intact.

## New source files

- `pqc_layer/multitier_assurance.py`: compute service-specific provider and sub-tier attestation requirements from the original risk graph; ML-DSA sign/verify policy-bound short-lived acknowledgement; fail closed for missing/stale/duplicate/wrong-service/wrong-record/wrong-issuer assertions.
- `pqc_layer/banking_gateway.py`: strict entry point, requires and validates external attestations; enforces the gate again on receipt. Call this rather than the gate-optional research baseline in your final demo.
- `experiments/banking_gateway_demo.py`: end-to-end ML-KEM + AES-GCM encrypted transaction, bank ML-DSA signature, simulated vendor ML-DSA-65 signatures, RBAC, replay rejection.
- `experiments/cross_tier_final_evaluation.py`: same-service, same-security-profile ablation with and without cross-tier controls; repeats; JSON envelope sizes; missing/duplicated evidence checks.
- `experiments/cross_tier_scalability.py`: compare graph-derived signer requirements on both the 50-asset V1 and 250-asset V2 synthetic datasets.
- `tests/test_cross_tier.py`: 11 new multi-tier security tests.
- `tests/test_hash_based_signature.py`: hash-based PQ digital signature alternative verification test.
- `PROJECT_COMPLETION_GUIDE.md`, `RESEARCH_COMPARISON.md`, `PATENT_ADDENDUM.md`, `EXACT_CODE_CHANGES.md`, `run_complete.sh`: guide/experiment documentation.

## Modified existing files

- `pqc_layer/darp_pqc.py`: backward-compatible optional `dependency_attestations` at message creation and optional `tier_gate` on acceptance. When enabled, attestation digest is included in both bank ML-DSA signature and signed employee authorization; the server verifies the complete claims against its trusted policy before accepting. Existing original workflows remain supported.
- `pqc_layer/crypto_backend.py`: added optional `SLH-DSA-SHA2-128s` FIPS 205 signature family (experimental only; production default remains ML-DSA).
- `experiments/pqc_benchmark.py`: added SLH-DSA key generation, signing and verification comparison.
- `README.md`, `SUBMISSION_CHECKLIST.md`: cross-tier run instructions and scientific limitations.

## Existing files preserved

- `src/*`, `data/*`, `data_v2/*`
- Risk/migration scenarios and original figures
- `PQC_Banking_Patent_Technical_Disclosure_Draft.docx` (older draft, read with **new addendum**; not legally finalized)
- Prior DARP code and evaluation results (new benchmarks rerun on current host)

## Integration commands

```bash
python -m unittest discover -s tests -v
python -m experiments.banking_gateway_demo
python -m experiments.cross_tier_final_evaluation --iterations 20
python -m experiments.pqc_benchmark --iterations 12
```
