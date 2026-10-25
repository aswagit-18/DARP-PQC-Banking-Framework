"""A graph-remediation what-if creates a new cryptographic policy epoch.

This is NOT a claim that these assets have been deployed or migrated.
The scenario is deliberately synthetic, for controlled model evaluation.
"""
import json
import tempfile
from pathlib import Path
import sys
import pandas as pd

from pqc_layer.crypto_backend import OpenSSLPQC
from pqc_layer.access_control import PostQuantumAccessControl, AccessDenied
from pqc_layer.transaction_demo import create_transaction_envelope, accept_transaction_envelope
from pqc_layer.darp_pqc import build_policies, create_protected_record, accept_protected_record

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
from data_loader import load_data
from graph_builder import build_graph
from propagation import find_service_paths


def main():
    registry, initial_er = build_policies(ROOT, epoch=1)
    selected = 'S01'
    before = registry.get(selected)

    assets, services, edges = load_data()
    graph = build_graph(assets, services, edges)
    reachable_assets = {str(path[-1]) for path in find_service_paths(graph, selected)}
    changed = assets[assets['asset_id'].astype(str).isin(reachable_assets) & (assets['quantum_vulnerability'] > .25)].copy()
    if changed.empty:
        raise RuntimeError('No source vulnerabilities to simulate')
    # Controlled research *counterfactual*: every reachable vulnerable asset of
    # S01 is assumed remediated; this does not perform live cryptographic migration.
    mask = assets['asset_id'].astype(str).isin(set(changed['asset_id']))
    assets.loc[mask, 'algorithm'] = 'SIMULATED-PQC-REMEDIATED'
    assets.loc[mask, 'quantum_vulnerability'] = 0.10
    with tempfile.TemporaryDirectory(prefix='darp_whatif_', dir=ROOT) as folder:
        dst = Path(folder)
        assets.to_csv(dst/'banking_assets.csv', index=False)
        services.to_csv(dst/'banking_services.csv', index=False)
        edges.to_csv(dst/'banking_dependencies.csv', index=False)
        candidate_reg, after_er = build_policies(ROOT, epoch=2, data_dir=dst.name)
    after = candidate_reg.get(selected)
    if before.policy_digest == after.policy_digest:
        raise AssertionError('Expected provenance-bound policy revision')
    if after.total_risk >= before.total_risk:
        raise AssertionError('What-if remediation should reduce S01 risk')
    if after.profile != 'standard':
        raise AssertionError('Synthetic S01 scenario did not reach standard PQC profile')

    with OpenSSLPQC() as crypto:
        recipient = {a: crypto.keypair(a) for a in ['ML-KEM-768', 'ML-KEM-1024']}
        signing = {a: crypto.keypair(a) for a in ['ML-DSA-65', 'ML-DSA-87']}
        acl = PostQuantumAccessControl(crypto)
        acl.register('teller_elevated','teller',signing['ML-DSA-87'])
        acl.register('teller_standard','teller',signing['ML-DSA-65'])
        record={'transaction_id':'SYNTHETIC-POLICY-EPOCH-DEMO','amount_minor_units':1000,'currency':'INR'}
        old = create_protected_record(crypto, acl, registry, recipient, signing[before.signature], actor='teller_elevated', service_id=selected, action='initiate_payment', record=record)
        fixed_old = create_transaction_envelope(crypto, acl, recipient['ML-KEM-768'], signing['ML-DSA-65'], actor='teller_standard', service_id=selected, action='initiate_payment', transaction=record)
        registry.replace(after)
        stale_blocked = False
        try:
            accept_protected_record(crypto, acl, registry, recipient, service_id=selected, action='initiate_payment', envelope=old)
        except AccessDenied:
            stale_blocked = True
        fixed_accepted = accept_transaction_envelope(crypto, acl, recipient['ML-KEM-768'], service_id=selected, action='initiate_payment', envelope=fixed_old)
        new = create_protected_record(crypto, acl, registry, recipient, signing[after.signature], actor='teller_standard', service_id=selected, action='initiate_payment', record=record)
        accepted = accept_protected_record(crypto, acl, registry, recipient, service_id=selected, action='initiate_payment', envelope=new)
    summary = {
        'kind':'Synthetic counterfactual risk-model scenario, not live migration',
        'service_id':selected,
        'assumed_remediated_reachable_assets':int(len(changed)),
        'before_er':float(initial_er),'after_er':float(after_er),
        'before_service_risk':before.total_risk,'after_service_risk':after.total_risk,
        'before_policy':before.profile,'after_policy':after.profile,
        'before_kem':before.kem,'after_kem':after.kem,
        'old_message_blocked_after_policy_revision':stale_blocked,
        'fixed_pqc_baseline_old_message_still_accepted_without_policy_binding':fixed_accepted['accepted'],
        'new_message_accepted':accepted['accepted'] and accepted['record']==record,
        'policy_epoch_incremented':after.epoch==before.epoch+1,
        'minimum_PQC_profile_retained':after.kem=='ML-KEM-768' and after.signature=='ML-DSA-65',
    }
    out=ROOT/'results'/'tables'/'darp_policy_migration_demo.json'
    out.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    if not all([stale_blocked, summary['fixed_pqc_baseline_old_message_still_accepted_without_policy_binding'], summary['new_message_accepted'],summary['policy_epoch_incremented'],summary['minimum_PQC_profile_retained']]):
        raise AssertionError('Risk-policy migration check failed')
    print(json.dumps(summary,indent=2))
    print('Saved',out)


if __name__ == '__main__':
    main()
