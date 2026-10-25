#!/usr/bin/env python3
"""Fast reproducible V3 research evaluation; writes only to a NEW folder.

Runs exact risk objective after analytically reusing the same graph paths,
not approximating risk reductions. Supports the original project's risk
ranking, literature-adapted QARS, budget and model ablations.
"""
from __future__ import annotations
import argparse,json,os,sys,time,traceback
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'src'))
from fast_v3_exact import ExactRiskModel
from remediation import evaluate_ecosystem, simulate_asset_remediation

OUT=ROOT/'V3_2100_Paper_Results_Fast'; TAB=OUT/'tables';FIG=OUT/'figures';LOG=OUT/'logs'
for p in [OUT,TAB,FIG,LOG]:p.mkdir(parents=True,exist_ok=True)

ALIASES={
'Proposed Dynamic DeltaER/Cost':'Proposed dynamic ΔER/cost',
'Business Criticality First':'Business criticality first',
'Direct Risk First':'Direct risk first',
'HNDL Risk First':'HNDL risk first',
'QARS equal':'QARS equal weights (adapted)',
'QARS finance':'QARS finance weights (adapted)'}

def load_csvs(path):
    return tuple(pd.read_csv(path / f'banking_{x}.csv') for x in ['assets','services','dependencies'])

def chart_series(name, frame, x, ys, xlabel, ylabel, title, percent=False):
    fig,ax=plt.subplots(figsize=(8.2,4.5))
    for col in ys:ax.plot(frame[x],frame[col],marker='o',linewidth=1.8,label=ALIASES.get(col,col))
    ax.set(xlabel=xlabel,ylabel=ylabel,title=title)
    ax.grid(alpha=.2)
    if len(ys)>1:ax.legend(fontsize=8,loc='best')
    fig.tight_layout();fig.savefig(FIG/name,dpi=220);plt.close(fig)

def bar(name,x,values,title,ylabel,rot=12,ylim=None):
    fig,ax=plt.subplots(figsize=(8.2,4.35))
    positions=np.arange(len(x));bars=ax.bar(positions,values,width=.72)
    ax.set_xticks(positions,labels=x,rotation=rot,ha='right' if rot else 'center',fontsize=9)
    ax.set(title=title,ylabel=ylabel)
    if ylim:ax.set_ylim(*ylim)
    else:ax.set_ylim(0,max(values)*1.16 if len(values) and max(values)>0 else 1)
    for patch,v in zip(bars,values):
        ax.annotate(f'{v:.2f}' if abs(v)>=1 else f'{v:.4f}',(patch.get_x()+patch.get_width()/2,patch.get_height()),ha='center',va='bottom',fontsize=8)
    ax.grid(axis='y',alpha=.17);ax.set_axisbelow(True)
    fig.tight_layout();fig.savefig(FIG/name,dpi=220);plt.close(fig)

def run_risk():
    stamp=time.perf_counter()
    A,S,E=load_csvs(ROOT/'data_v3');M=ExactRiskModel(A,S,E)
    original=evaluate_ecosystem(A,S,E)['ecosystem_risk']
    assert abs(original-M.risk())<1e-10, 'Exact-model baseline verification failed'
    print('2,100 ASSETS | 60 SERVICES | V3 INITIAL ER',f'{original:.9f}')
    assert len(A)==2100, 'This runner requires the 2100-asset V3 dataset'
    (TAB/'v3_dataset_and_risk_summary.json').write_text(json.dumps({'assets':len(A),'services':len(S),'dependency_rows':len(E),'unique_edges':M.graph.number_of_edges(),'initial_er':original,'vulnerable_assets':int(M.vulnerable.sum()),'synthetic':True},indent=2))
    details=[]
    for sid,row in zip(M.service_ids,range(M.m)):
        details.append({'service_id':sid,'service_name':S.service_name.iloc[row], 'criticality':M.critical[row], 'direct_service_risk':M.d[row], 'inherited_quantum_risk':M.h[row], 'total_service_risk':1-(1-M.d[row])*(1-M.h[row])})
    pd.DataFrame(details).to_csv(TAB/'v3_service_risks.csv',index=False)
    impacts=M.candidate_impacts(); scores=impacts/M.cost
    ranked=A.copy();ranked['delta_er']=impacts;ranked['migration_cost']=M.cost;ranked['priority_score']=scores
    ranked.sort_values(['priority_score','delta_er'],ascending=False).to_csv(TAB/'v3_all_candidate_priorities.csv',index=False)
    budgets=[2.5,5.0,7.5]
    methods=['Proposed Dynamic DeltaER/Cost','Business Criticality First','Direct Risk First','HNDL Risk First']
    sweeps=[];saved={}
    for b in budgets:
        for met in methods:
            info,seq=M.simulate(met,b,save_seq=True)
            sweeps.append({'budget_scenario':b,**info})
            if b==7.5:
                seq.to_csv(TAB/f'v3_sequence_{met.replace(" ","_").replace("/","_")}.csv',index=False)
                saved[met]=info
            print('budget',b,met,round(info['risk_reduction_percent'],4),'assets',info['number_of_assets_migrated'],flush=True)
    sweep=pd.DataFrame(sweeps);sweep.to_csv(TAB/'budget_sweep.csv',index=False)
    pd.DataFrame(saved.values()).to_csv(TAB/'final_strategy_comparison_v3.csv',index=False)
    pivot=sweep.pivot(index='budget_scenario',columns='strategy',values='risk_reduction_percent').reset_index()
    chart_series('budget_sweep_risk_reduction.png',pivot,'budget_scenario',methods,'Normalized migration budget','Reduction in modeled ecosystem-risk index (%)','V3: Migration strategy comparison across budget ceilings')
    bar('three_way_migration_baselines.png',[ALIASES[k] for k in methods],[saved[k]['risk_reduction_percent'] for k in methods], 'V3: Migration priorities at budget ceiling 7.5', 'Modeled risk reduction (%)')
    qa=[];qars=[]
    for method,ww in [('QARS equal',(1/3,1/3,1/3)),('QARS finance',(.4,.4,.2))]:
        info,seq=M.simulate(method,7.5,weights=ww,save_seq=True);qa.append(info)
        seq.to_csv(TAB/f'v3_{method.replace(" ","_").lower()}_sequence.csv',index=False)
    qa.append(saved['Proposed Dynamic DeltaER/Cost']);qars=pd.DataFrame(qa)
    qars.to_csv(TAB/'qars_paper_vs_darp_comparison.csv',index=False)
    bar('qars_paper_vs_darp_risk_reduction.png',['QARS equal-weight\n(adapted)','QARS finance-weighted\n(adapted)','Proposed DARP-PQC'],qars.risk_reduction_percent.to_numpy(),'V3: Adapted published QARS rankings vs proposed dynamic method','Modeled ecosystem-risk reduction (%)',rot=0)
    # Topology ablation is an evaluation on changed graphs, NOT evidence of reduced threat.
    trows=[]
    for name,allowed in [('Full Internal + Third-Party + Sub-Tier',{'Internal','Third-Party','Sub-Tier'}),('No Sub-Tier',{'Internal','Third-Party'}),('Internal Only',{'Internal'})]:
        sub=A[A.tier.isin(allowed)].copy(); keep=set(sub.asset_id.astype(str))|set(S.service_id.astype(str))
        edges=E[E.source_id.astype(str).isin(keep)&E.target_id.astype(str).isin(keep)].copy()
        trial=ExactRiskModel(sub,S,edges)
        trows.append({'topology_variant':name,'assets':len(sub),'dependencies':len(edges),'ecosystem_risk':trial.risk(),'risk_change_vs_full':trial.risk()-original})
    topology=pd.DataFrame(trows);topology.to_csv(TAB/'ablation_topology.csv',index=False)
    bar('topology_ablation.png',[r.replace('Full Internal + Third-Party + Sub-Tier','Full three-tier model') for r in topology.topology_variant],topology.ecosystem_risk.to_numpy(),'V3: Inherited risk omitted when external tiers are excluded','Modeled ecosystem-risk index',rot=7,ylim=(0,1.1*max(topology.ecosystem_risk)))
    arows=[]
    for mode in ['Proposed Dynamic DeltaER/Cost','Static initial DeltaER/Cost','Dynamic DeltaER only (no cost normalization)']:
        info,seq=M.simulate(mode,7.5,save_seq=True)
        info['variant']={'Proposed Dynamic DeltaER/Cost':'Full dynamic DeltaER/Cost','Static initial DeltaER/Cost':'Static initial DeltaER/Cost','Dynamic DeltaER only (no cost normalization)':'Dynamic DeltaER only (no cost normalization)'}[mode]
        arows.append(info);seq.to_csv(TAB/f'v3_ablation_{mode.replace(" ","_").replace("/","_")}.csv',index=False)
    ablation=pd.DataFrame(arows);ablation.to_csv(TAB/'ablation_prioritization.csv',index=False)
    bar('prioritization_ablation.png',ablation.variant.to_list(),ablation.risk_reduction_percent.to_numpy(),'V3: Prioritization ablation at budget ceiling 7.5','Modeled ecosystem-risk reduction (%)',rot=8)
    # Compare models from *original* V1/V2 with present V3 using the same accelerated engine.
    sizes=[]
    for id,loc in [('V1',ROOT/'data'),('V2',ROOT/'data_v2'),('V3',ROOT/'data_v3')]:
        a,s,d=load_csvs(loc)
        t=time.perf_counter();instance=ExactRiskModel(a,s,d);build=time.perf_counter()-t
        t=time.perf_counter();_impact=instance.candidate_impacts();ranktime=time.perf_counter()-t
        sizes.append({'dataset':id,'assets':len(a),'services':len(s),'dependency_rows':len(d),'unique_edges':instance.graph.number_of_edges(),'vulnerable_assets':int(instance.vulnerable.sum()),'baseline_ecosystem_risk':instance.risk(),'path_precomputation_seconds':build,'initial_all_candidate_ranking_seconds':build+ranktime,'cached_candidate_scoring_seconds':ranktime})
    sc=pd.DataFrame(sizes);sc.to_csv(TAB/'scalability_analysis.csv',index=False)
    bar('scalability_runtime.png',[f'{x}\n({n:,} assets)' for x,n in zip(sc.dataset,sc.assets)],sc.initial_all_candidate_ranking_seconds.to_numpy(),'Original risk model, accelerated exact candidate ranking','Precompute + first ranking wall time (seconds)',rot=0)
    # Complete graph, labelled by 4 tiers and summary rather than unreadable 2160 names.
    from matplotlib.collections import LineCollection
    from collections import defaultdict
    groups=defaultdict(list)
    for node,atr in M.graph.nodes(data=True):groups[atr.get('tier','Other')].append(node)
    tiers=['Service','Internal','Third-Party','Sub-Tier'];coords={}
    for i,tier in enumerate(tiers):
        for node,y in zip(sorted(groups[tier]),np.linspace(0,1,len(groups[tier]))):coords[node]=(i,float(y))
    fig,ax=plt.subplots(figsize=(11,6))
    seg=[[coords[u],coords[v]] for u,v in M.graph.edges if u in coords and v in coords]
    ax.add_collection(LineCollection(seg,colors='#777777',alpha=.055,linewidth=.25))
    for i,tier in enumerate(tiers):
        pts=np.asarray([coords[n] for n in groups[tier] if n in coords]);ax.scatter(pts[:,0],pts[:,1],s=18 if i==0 else 4,label=f'{tier} ({len(pts)})',alpha=.8)
    ax.set(xticks=list(range(4)),xticklabels=tiers,xlim=(-.4,3.4),ylim=(-.02,1.02),yticks=[],title=f'V3: Entire directed banking cryptographic dependency graph ({M.graph.number_of_nodes():,} nodes, {M.graph.number_of_edges():,} edges)')
    ax.legend(fontsize=8,ncol=4,loc='lower center',bbox_to_anchor=(.5,-.14));fig.tight_layout()
    fig.savefig(FIG/'multi_tier_dependency_graph_v3.png',dpi=220);plt.close(fig)
    print('\nFINISHED V3 RISK COMPARISONS in',round(time.perf_counter()-stamp,2),'seconds')
    print(pd.DataFrame(saved.values())[['strategy','final_er','risk_reduction_percent','budget_used']].to_string(index=False))
    print('\nQARS V3\n',qars[['strategy','final_er','risk_reduction_percent']].to_string(index=False))
    return {'dataset':{'assets':len(A),'services':len(S),'dependencies':len(E)},'risk_methods':saved,'qars_methods':qa,'topology':trows,'ablation':arows,'scalability':sizes}


def main():
    parser=argparse.ArgumentParser(description='Create V3 (2100) figures and measured results quickly')
    parser.add_argument('--step',choices=['risk','all'],default='all')
    args=parser.parse_args()
    tic=time.perf_counter()
    summary=run_risk()
    with (TAB/'v3_full_risk_summary.json').open('w') as f:json.dump(summary,f,indent=2,default=float)
    print('Elapsed',round(time.perf_counter()-tic,2),'seconds; output:',OUT)
    print('Old results folder untouched.')

if __name__=='__main__':main()
