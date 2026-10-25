> **Final version:** Use `PROJECT_COMPLETION_GUIDE.md` and `bash run_complete.sh` for all current commands, including the cross-tier gate and SLH-DSA tests. This older run guide covers the preceding DARP stage only.

# Run the DARP-PQC extension in VS Code (macOS)

The original graph/risk framework is preserved. The new files live in `pqc_layer`, `experiments`, and `tests`.

## Setup

In the extracted project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Post-quantum cryptography requires OpenSSL 3.5 or later** (ML-KEM and ML-DSA available in its default provider). On macOS, the system `/usr/bin/openssl` may be LibreSSL/older OpenSSL and may not support these algorithms. If using Homebrew:

```bash
brew install openssl@3
export OPENSSL_BIN="$(brew --prefix openssl@3)/bin/openssl"
"$OPENSSL_BIN" version
"$OPENSSL_BIN" list -kem-algorithms | grep ML-KEM
"$OPENSSL_BIN" list -signature-algorithms | grep ML-DSA
```

If your Homebrew OpenSSL is not 3.5+, update/upgrade it before running. `OPENSSL_BIN` is consumed automatically by the implementation.

## Run

```bash
# Existing risk framework (unchanged)
python main.py

# Functional security tests: old PQC + new DARP-PQC
python -m unittest discover -s tests -v

# Actual encrypted and digitally signed synthetic banking records
python -m experiments.pqc_operations_demo

# Fixed PQC vs two risk-bound profiles: measured performance
python -m experiments.darp_pqc_evaluation --iterations 15

# Simulated dependency migration -> new risk policy -> stale policy rejection
python -m experiments.darp_policy_migration_demo
```

Outputs are written into `results/tables/`. The experiments use **synthetic** bank records only. They do not connect to a banking API or network or transfer money.

## How to demonstrate to the guide

1. Show `results/tables/final_strategy_comparison_v1.csv` (original risk/migration novelty).
2. Show `results/tables/darp_pqc_policy_selection.json` (risk-derived PQC choices for all ten banking services).
3. Run `experiments.darp_pqc_evaluation` (real ML-KEM / ML-DSA / AES-256-GCM and fixed-PQC comparison).
4. Run `experiments.darp_policy_migration_demo` (risk change -> enforced policy revision and replay/downgrade protection).
5. Show `tests/test_darp_pqc.py` (targeted security assertions).
6. Open `DARP_PQC_RESEARCH_EXTENSION.md` for method, novelty positioning and published-paper comparison.

## Security notice

A successful demo does not establish production security or guaranteed patentability. In particular, this prototype has **static KEM recipient keys** and does not implement forward-secret network session negotiation, production key custody or trustworthy distributed replay/policy persistence.
