#!/usr/bin/env bash
set -euo pipefail
export PQC_DATASET=v1
python3 -m unittest discover -s tests -v
python3 experiments/final_evaluation.py
python3 experiments/sensitivity_analysis.py
python3 experiments/ablation_study.py
python3 experiments/budget_sweep.py
python3 experiments/explainability_report.py
python3 experiments/scalability_analysis.py
python3 experiments/generate_final_figures.py
