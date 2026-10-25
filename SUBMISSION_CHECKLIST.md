# Project / Patent Submission Checklist

## Research project submission

- [ ] Use V1 results as the primary complete experiment set.
- [ ] State clearly that V1 and V2 are synthetic banking ecosystems.
- [ ] Report baseline ER = 0.778727 for V1.
- [ ] Report the equal-budget 7.5 comparison from `results/tables/final_strategy_comparison_v1.csv`.
- [ ] Include sensitivity, topology ablation, prioritization ablation, budget sweep, explainability and scalability results.
- [ ] Do not describe the risk coefficients as universally calibrated banking probabilities.
- [ ] Do not claim the 43.61% result generalizes to production banks.
- [ ] Keep the novelty centered on the ordered integration of multi-tier dependency propagation, ecosystem counterfactual risk reduction and dynamic cost-aware re-ranking.

## Patent-preparation package

Provide the patent professional with:

1. `PQC_Banking_Patent_Technical_Disclosure_Draft.docx`
2. this source-code/project ZIP;
3. `NOVELTY_AND_PATENT_POSITION.md`;
4. `FINAL_RESULTS_SUMMARY.md`;
5. `system_architecture.png`;
6. the final result CSV files under `results/tables/`;
7. dated source-code snapshots and the dataset-generation code.

## Before public disclosure

- [ ] Obtain institutional/inventor approval for ownership and inventor names.
- [ ] Have a qualified patent professional review close prior art and revise the claims.
- [ ] Coordinate filing before publishing source code, a paper, poster, thesis chapter, or public demo when patent protection is a priority.
- [ ] Replace inventor/applicant placeholders in the technical disclosure.

## Reproduce final results

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run_final.sh
```

The complete run includes the V2 scalability ranking and may take longer than the V1 experiments.


## Final cross-tier extension (October 2026)

- [x] The original migration strategy results were rechecked after integration (V1 43.61% modeled risk reduction at cost budget 7.5).
- [x] Real ML-KEM + AES-256-GCM encryption/decryption and ML-DSA signatures verified.
- [x] Independent ML-DSA-signed mock third-party and sub-tier risk acknowledgements and strict server enforcement implemented.
- [x] SLH-DSA-SHA2-128s alternative signature tested, not used as production default.
- [x] 37 automated tests passed on current host.
- [x] 20-run same-profile cross-tier ablation and results generated.
- [ ] Re-run benchmarks on the actual submission laptop and record local platform/OpenSSL version.
- [ ] Have guide review limitations and verify that simulated claims are not presented as proof of actual vendor deployment.
- [ ] Ask university IP cell/patent agent to review the **original disclosure + PATENT_ADDENDUM.md** before any public release.
- [ ] Formal patentability prior-art search and legal specification drafting pending.
