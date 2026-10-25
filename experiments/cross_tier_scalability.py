"""Graph-derived external tier requirements across V1 and V2 synthetic datasets."""
import csv
import statistics
from pathlib import Path
from time import perf_counter
from pqc_layer.multitier_assurance import derive_tier_requirements
from pqc_layer.darp_pqc import build_policies

ROOT = Path(__file__).resolve().parent.parent


def main():
    rows=[]
    for dataset in ('data', 'data_v2'):
        elapsed, reqs = [], None
        for _ in range(5):
            start=perf_counter()
            reqs=derive_tier_requirements(ROOT,dataset=dataset)
            elapsed.append((perf_counter()-start)*1000)
        reg,er=build_policies(ROOT,data_dir=dataset)
        rows.append({
            'dataset': dataset,'service_count':len(reqs),
            'required_external_signers':sum(map(len,reqs.values())),
            'services_with_third_party':sum(any(r.tier=='Third-Party' for r in v) for v in reqs.values()),
            'services_with_sub_tier':sum(any(r.tier=='Sub-Tier' for r in v) for v in reqs.values()),
            'median_requirement_derivation_ms':round(statistics.median(elapsed),4),
            'ecosystem_risk_index':round(er,6),
            'elevated_pqc_policies':sum(p.profile=='elevated' for p in reg.policies.values()),
            'interpretation': 'Synthetic topology + model timing; no cryptographic signing work'
        })
    destination=ROOT/'results'/'tables'/'cross_tier_scalability.csv'
    with destination.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    for row in rows:print(row)
    print('Saved:',destination)

if __name__=='__main__': main()
