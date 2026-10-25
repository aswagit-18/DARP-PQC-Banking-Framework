"""Exact algebraic acceleration of the project's existing banking ecosystem-risk model.

Path strengths, vulnerability threshold, weighted inherited risk, service direct risk,
service risk fusion, and the remediation operation are unchanged. Graph paths are
computed ONCE; scores are recomputed algebraically when quantum_vulnerability -> 0.

See QUICKSTART_FAST_V3.md for validation procedure, scope, and reproducibility.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from graph_builder import build_graph
from propagation import find_service_paths, calculate_dependency_weight
from risk_model import calculate_direct_risk

class ExactRiskModel:
    def __init__(self, assets, services, dependencies, weights=None):
        self.assets=assets.reset_index(drop=True).copy()
        self.services=services.reset_index(drop=True).copy()
        self.dependencies=dependencies.copy()
        self.n=len(assets); self.m=len(services)
        self.asset_ids=self.assets.asset_id.astype(str).to_numpy()
        self.service_ids=self.services.service_id.astype(str).to_numpy()
        self.lookup={aid:i for i,aid in enumerate(self.asset_ids)}
        self.q=self.assets.quantum_vulnerability.to_numpy(dtype=float)
        self.cost=self.assets.migration_complexity.to_numpy(dtype=float)
        self.critical=self.services.criticality.to_numpy(dtype=float)
        self.sw=self.critical/self.critical.sum()
        self.original_direct=calculate_direct_risk(self.assets,weights=weights).direct_risk.to_numpy(dtype=float)
        self.vulnerable=self.q>0.25
        self.graph=build_graph(self.assets,self.services,self.dependencies)
        self.inherited=np.zeros((self.m,self.n),dtype=float)
        self.direct=np.zeros((self.m,self.n),dtype=float)
        self.weights_per_service=np.zeros((self.m,self.n),dtype=float)
        self.reachable_paths={}
        self._precompute()
        self.reset()

    def _precompute(self):
        internal=self.assets.tier.astype(str).to_numpy()=='Internal'
        a_services=self.assets.service_id.astype(str).to_numpy()
        for s,sid in enumerate(self.service_ids):
            local=np.where(internal & (a_services==sid))[0]
            if len(local):
                live=local[self.vulnerable[local]]
                self.direct[s,live]=self.original_direct[live]/len(local)
            best={}
            for path in find_service_paths(self.graph,sid):
                if not path: continue
                ix=self.lookup.get(str(path[-1]))
                if ix is None: continue
                w=calculate_dependency_weight(self.graph,path)
                if w<=0: continue
                if ix not in best or w>best[ix][0]:best[ix]=(w,path)
            self.reachable_paths[sid]=best
            denom=sum(w for w,_ in best.values())
            if denom>0:
                for ix,(w,path) in best.items():
                    self.weights_per_service[s,ix]=w
                    if self.vulnerable[ix]:self.inherited[s,ix]=self.original_direct[ix]*w*w/denom

    def reset(self):
        self.live=self.vulnerable.copy()
        self.d=self.direct.sum(axis=1)
        self.h=self.inherited.sum(axis=1)

    def risk(self):
        return float(np.dot(self.sw,1-(1-self.d)*(1-self.h)))

    def candidate_impacts(self):
        # Exact two-factor service risk difference for q_i -> 0:
        # delta_i=sum_s c_s*(d_si*(1-h_s)+h_si*(1-d_s)+d_si*h_si)
        score=(self.sw*(1-self.h))@self.direct + (self.sw*(1-self.d))@self.inherited + self.sw@(self.direct*self.inherited)
        score[~self.live]=0.
        score[np.abs(score)<1e-12]=0.
        return score

    def remediate(self,i):
        if not self.live[i]:raise ValueError('Asset already remediated or not vulnerable')
        self.live[i]=False
        self.d-=self.direct[:,i]
        self.h-=self.inherited[:,i]

    def state(self):
        return {'er':self.risk(),'direct_service_risk':self.d.copy(),'inherited_service_risk':self.h.copy(), 'service_total_risk':1-(1-self.d)*(1-self.h)}

    def simulate(self,order_mode,budget=7.5,weights=(1/3,1/3,1/3),save_seq=False):
        self.reset()
        init=self.risk(); spent=0.; rows=[]
        if order_mode.startswith('QARS'):
            x=1+14*self.assets.data_lifetime.to_numpy(dtype=float)
            y=1+4*self.cost
            t=np.minimum(1.,(x+y)/12.)
            s=self.assets.data_sensitivity.to_numpy(dtype=float)
            e=self.vulnerable.astype(float)*self.assets.external_exposure.to_numpy(dtype=float)
            rankscore=weights[0]*t+weights[1]*s+weights[2]*e
        elif order_mode=='Direct Risk First':rankscore=self.original_direct.copy()
        elif order_mode=='Business Criticality First':rankscore=self.assets.business_criticality.to_numpy(dtype=float)
        elif order_mode=='HNDL Risk First':rankscore=self.assets.hndl_exposure.to_numpy(dtype=float)
        elif order_mode=='Static initial DeltaER/Cost':rankscore=self.candidate_impacts()/self.cost
        else:rankscore=None
        remaining_steps=self.live.sum()
        for step in range(int(remaining_steps)):
            possible=np.where(self.live & (self.cost<=budget-spent+1e-12))[0]
            if len(possible)==0:break
            if order_mode in ('Proposed Dynamic DeltaER/Cost','Dynamic DeltaER only (no cost normalization)'):
                impacts=self.candidate_impacts()
                rankscore=impacts/self.cost if order_mode=='Proposed Dynamic DeltaER/Cost' else impacts
            # static ranking: score desc, ID asc; dynamic ties: score desc, delta desc, then initial csv order.
            if order_mode=='Proposed Dynamic DeltaER/Cost':
                order=sorted(possible,key=lambda i:(-float(rankscore[i]),-float(impacts[i]),int(i)))
            elif order_mode=='Static initial DeltaER/Cost':
                order=sorted(possible,key=lambda i:(-float(rankscore[i]),-float(self.candidate_impacts()[i]),int(i)))
            else:order=sorted(possible,key=lambda i:(-float(rankscore[i]),str(self.asset_ids[i])))
            i=order[0]
            if order_mode in ('Proposed Dynamic DeltaER/Cost','Static initial DeltaER/Cost','Dynamic DeltaER only (no cost normalization)'):
                if self.candidate_impacts()[i]<=0:break
            before=self.risk(); self.remediate(i); after=self.risk(); spent+=self.cost[i]
            if save_seq:
                rows.append({'strategy':order_mode,'step':step+1,'asset_id':self.asset_ids[i],'asset_name':self.assets.asset_name.iloc[i], 'tier':self.assets.tier.iloc[i], 'algorithm':self.assets.algorithm.iloc[i], 'strategy_score':rankscore[i],'migration_cost':self.cost[i],'cumulative_cost':spent,'ecosystem_risk_before':before,'ecosystem_risk_after':after,'delta_er':before-after,'cumulative_delta_er':init-after})
        reduction=init-self.risk()
        info={'strategy':order_mode,'migration_budget':budget,'budget_used':spent,'number_of_assets_migrated':int(len(rows)) if save_seq else int(self.vulnerable.sum()-self.live.sum()),'initial_er':init,'final_er':self.risk(),'cumulative_delta_er':reduction,'risk_reduction_per_cost':reduction/spent if spent>0 else 0.,'risk_reduction_percent':100*reduction/init if init>0 else 0.}
        return info,pd.DataFrame(rows)
