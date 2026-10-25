"""Traceable bridge from existing risk recommendation to real PQC primitives.

Does not alter the original ER values: migration in the risk model is a
counterfactual, while this script executes a security-control demonstration.
"""
from pathlib import Path
import json
import pandas as pd

from pqc_layer.crypto_backend import OpenSSLPQC, canon
from pqc_layer.access_control import PostQuantumAccessControl
from pqc_layer.transaction_demo import create_transaction_envelope, accept_transaction_envelope

ROOT = Path(__file__).resolve().parent.parent


def mapped_pq_control(old_algorithm: str) -> str:
    old = old_algorithm.upper()
    if old in {"RSA-2048", "RSA-3072", "ECDSA-256"}:
        return "ML-DSA-65 for signatures; ML-KEM-768 for confidentiality"
    if old in {"ECDH-256", "ECC-256"}:
        return "ML-KEM-768 key establishment + AES-256-GCM data encryption"
    if old.startswith("AES-"):
        return "AES-256-GCM authenticated encryption (symmetric quantum margin)"
    return "PQC suitability requires role-specific evaluation"


def main():
    ranking = pd.read_csv(ROOT / "results/tables/final_sequence_proposed_dynamic_deltaer_cost.csv")
    assets = pd.read_csv(ROOT / "data/banking_assets.csv")
    services = pd.read_csv(ROOT / "data/banking_services.csv")
    selected = ranking.iloc[0]
    asset = assets.loc[assets.asset_id == selected.asset_id].iloc[0]
    service = services.loc[services.service_id == asset.service_id].iloc[0]
    alert = {"event_id": "SYNTHETIC-FRAUD-EVENT-1", "status": "flagged", "assessed_asset": str(asset.asset_id), "service_id": str(service.service_id), "synthetic": True}

    with OpenSSLPQC() as crypto:
        recipient = crypto.keypair("ML-KEM-768")
        auditor = crypto.keypair("ML-DSA-65")
        acl = PostQuantumAccessControl(crypto)
        acl.register("auditor_01", "auditor", auditor)
        package = create_transaction_envelope(crypto, acl, recipient, auditor, actor="auditor_01", service_id=str(service.service_id), action="read_audit", transaction=alert)
        result = accept_transaction_envelope(crypto, acl, recipient, service_id=str(service.service_id), action="read_audit", envelope=package)
        report = {
            "risk_ranking_first_asset": str(asset.asset_id),
            "risk_ranking_first_asset_name": str(asset.asset_name),
            "original_algorithm": str(asset.algorithm),
            "banking_service": str(service.service_name),
            "old_algorithm_target_control": mapped_pq_control(str(asset.algorithm)),
            "remediation_delta_er_from_existing_simulation": float(selected.delta_er),
            "demonstration": "Read synthetic fraud alert with ML-KEM-768 sealed payload + ML-DSA-65 RBAC/signature",
            "transaction_recovered": result["transaction"] == alert,
            "authorization_accepted": result["accepted"],
            "limitations": "Demonstration is not a live replacement of the API cryptosystem; the existing counterfactual ER simulation is unchanged."
        }
    out = ROOT / "results/tables/pqc_priority_control_bridge.json"
    out.write_text(json.dumps(report, indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["authorization_accepted"] or not report["transaction_recovered"]:
        raise AssertionError('Integration bridge demonstration failed')


if __name__ == "__main__":
    main()
