"""Strict banking-service facade that always enforces cross-tier assurance.

Do not call the optional-gate research baseline for protected deployment flows.
The provider signatures must be collected out-of-band; this class does not
mint or forge third-party assertions on behalf of a bank.
"""
from __future__ import annotations

from .access_control import AccessDenied, PostQuantumAccessControl
from .crypto_backend import KeyPair, OpenSSLPQC
from .darp_pqc import (PolicyRegistry, create_protected_record,
                        accept_protected_record)
from .multitier_assurance import CrossTierAssuranceGate


class RiskBoundBankingGateway:
    def __init__(self, crypto: OpenSSLPQC, access: PostQuantumAccessControl,
                 registry: PolicyRegistry, recipients: dict[str, KeyPair],
                 assurance_gate: CrossTierAssuranceGate):
        self.crypto = crypto
        self.access = access
        self.registry = registry
        self.recipients = recipients
        self.assurance_gate = assurance_gate

    def protect(self, signer: KeyPair, *, actor: str, service_id: str,
                action: str, record: dict, external_attestations: list[dict]) -> dict:
        required = self.assurance_gate.required(service_id)
        if not isinstance(external_attestations, list) or len(external_attestations) != len(required):
            raise AccessDenied("The bank must collect each required external attestation")
        # Fail closed before encryption, as well as again on receipt.
        self.assurance_gate.verify(service_id=service_id,
            binding=self.registry.get(service_id).binding(action=action),
            record=record, attestations=external_attestations)
        return create_protected_record(self.crypto, self.access, self.registry,
            self.recipients, signer, actor=actor, service_id=service_id,
            action=action, record=record, dependency_attestations=external_attestations)

    def accept(self, *, service_id: str, action: str, envelope: dict) -> dict:
        return accept_protected_record(self.crypto, self.access, self.registry,
            self.recipients, service_id=service_id, action=action,
            envelope=envelope, tier_gate=self.assurance_gate)
