"""One-command guide demonstration using the strict cross-tier gateway."""
from pathlib import Path
import json
from pqc_layer.crypto_backend import OpenSSLPQC
from pqc_layer.access_control import PostQuantumAccessControl, AccessDenied
from pqc_layer.darp_pqc import build_policies
from pqc_layer.multitier_assurance import derive_tier_requirements, CrossTierAssuranceGate
from pqc_layer.banking_gateway import RiskBoundBankingGateway

ROOT = Path(__file__).resolve().parent.parent


def main():
    registry, er = build_policies(ROOT)
    requirements = derive_tier_requirements(ROOT)
    service_id = "S01"
    policy = registry.get(service_id)
    record = {"transaction_id": "DEMO-QUANTUM-SAFE-0001",
              "customer_alias": "synthetic", "amount_minor_units": 7000, "currency": "INR"}
    with OpenSSLPQC() as crypto:
        recipient = {a: crypto.keypair(a) for a in ("ML-KEM-768", "ML-KEM-1024")}
        employee = crypto.keypair(policy.signature)
        access = PostQuantumAccessControl(crypto)
        access.register("demo_employee", "teller", employee)
        gate = CrossTierAssuranceGate(crypto, requirements)
        providers = {}
        for req in requirements[service_id]:
            # Simulated providers hold SEPARATE private keys. Real providers must
            # sign independently through a trusted enrollment infrastructure.
            key = crypto.keypair("ML-DSA-65")
            providers[req.asset_id] = key
            gate.register_provider_key(req.asset_id, key)
        gateway = RiskBoundBankingGateway(crypto, access, registry, recipient, gate)
        binding = policy.binding(action="initiate_payment")
        signed_acknowledgements = [
            gate.issue(req, providers[req.asset_id], binding=binding, record=record)
            for req in requirements[service_id]
        ]
        envelope = gateway.protect(employee, actor="demo_employee", service_id=service_id,
            action="initiate_payment", record=record,
            external_attestations=signed_acknowledgements)
        accepted = gateway.accept(service_id=service_id, action="initiate_payment", envelope=envelope)
        assert accepted["record"] == record
        try:
            gateway.accept(service_id=service_id, action="initiate_payment", envelope=envelope)
            replay_status = "INCORRECTLY ACCEPTED"
        except AccessDenied:
            replay_status = "REJECTED"
        assert replay_status == "REJECTED"
        output = {"dataset": "V1 synthetic", "banking_service": service_id,
                  "ecosystem_risk": er,
                  "algorithm": "DARP-PQC + Cross-Tier Assurance Gate",
                  "key_establishment": policy.kem,
                  "authenticated_encryption": "AES-256-GCM + HKDF-SHA256",
                  "bank_signature": policy.signature,
                  "vendor_signatures": ["ML-DSA-65"] * len(signed_acknowledgements),
                  "required_providers": [r.report() for r in requirements[service_id]],
                  "encrypted_decryption_successful": accepted["accepted"],
                  "signed_third_party_and_subtier_evidence_verified": accepted["cross_tier_assurance"],
                  "access_control": "teller role authorized",
                  "replay_attack": replay_status,
                  "not_a_proof_of_vendor_pqc_migration": True}
        path = ROOT / "results" / "tables" / "banking_gateway_demo.json"
        path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(output, indent=2))
        print("Saved:", path)


if __name__ == '__main__':
    main()
