#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m unittest discover -s tests -v
python -m experiments.final_evaluation
python -m experiments.banking_gateway_demo
python -m experiments.cross_tier_final_evaluation --iterations 20
python -m experiments.cross_tier_scalability
python -m experiments.darp_policy_migration_demo
python -m experiments.pqc_benchmark --iterations 12
printf '\nAll research prototype validation steps completed. Read PROJECT_COMPLETION_GUIDE.md.\n'
