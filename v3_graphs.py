"""Generate paper-oriented, truthful topology overview figures from selected dataset.

Run from a working copy of the original project with PQC_DATASET=v3.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from data_loader import load_data, validate_data
from graph_builder import build_graph
from remediation import evaluate_ecosystem
from propagation import find_service_paths

TIERS = ["Service", "Internal", "Third-Party", "Sub-Tier"]
PALETTE = {"Service":"#23395d", "Internal":"#2980b9", "Third-Party":"#e09f3e", "Sub-Tier":"#8b5cf6"}


def main():
    dataset = os.environ.get("PQC_DATASET", "v1").upper()
    assets, services, deps = load_data()
    validate_data(assets, services, deps)
    outfig = ROOT / "results" / "figures"; outfig.mkdir(parents=True, exist_ok=True)
    outtab = ROOT / "results" / "tables"; outtab.mkdir(parents=True, exist_ok=True)
    evaluated = evaluate_ecosystem(assets, services, deps)
    graph = evaluated["graph"]
    stats = {"dataset": dataset, "assets": len(assets), "services": len(services),
             "dependency_rows": len(deps), "unique_graph_edges":graph.number_of_edges(),
             "graph_nodes":graph.number_of_nodes(),
             "vulnerable_assets":int((assets['quantum_vulnerability']>.25).sum()),
             "baseline_ecosystem_risk":float(evaluated["ecosystem_risk"]),
             "asset_tiers":{k:int(v) for k,v in assets['tier'].value_counts().items()}}
    (outtab / "v3_dataset_and_risk_summary.json").write_text(json.dumps(stats,indent=2)+'\n')
    evaluated['service_risk_results'].to_csv(outtab/'v3_service_risks.csv', index=False)
    pd.DataFrame(evaluated['path_results']).to_csv(outtab/'v3_path_risks.csv', index=False)

    # Complete network (not a misleading reduced graph). The nodes are grouped by tier;
    # labels are intentionally suppressed to keep 2160 nodes readable at figure scale.
    by_tier = defaultdict(list)
    for n, info in graph.nodes(data=True):
        by_tier[info.get('tier','Other')].append(str(n))
    positions = {}
    for i, tier in enumerate(TIERS):
        nodes = sorted(by_tier.get(tier, []))
        total = len(nodes)
        if not total: continue
        # Deterministic vertical ordering, one coordinate per unique node.
        order = np.linspace(0, 1, total)
        for n,y in zip(nodes, order): positions[n] = (float(i),float(y))
    fig, ax = plt.subplots(figsize=(14,8))
    segments = [[positions[u],positions[v]] for u,v in graph.edges if u in positions and v in positions]
    ax.add_collection(LineCollection(segments, colors='#7f8c8d', linewidths=.28, alpha=.085, zorder=1))
    for tier in TIERS:
        pts=[positions[n] for n in by_tier.get(tier,[]) if n in positions]
        if not pts: continue
        xy=np.array(pts)
        ax.scatter(xy[:,0],xy[:,1],s=15 if tier=='Service' else 5,c=PALETTE[tier],label=f'{tier} ({len(pts)})',alpha=.88,zorder=3)
    ax.set_xticks(range(len(TIERS)), TIERS, fontsize=10)
    ax.set_xlim(-.4,3.4); ax.set_ylim(-.025,1.025)
    ax.set_yticks([]); ax.set_ylabel('Assets schematically ordered within tier')
    ax.set_title(f'{dataset}: Complete Multi-Tier Banking Cryptographic Dependency Network\n{graph.number_of_nodes():,} nodes | {graph.number_of_edges():,} unique directed edges',fontsize=14)
    ax.grid(axis='x',alpha=.12)
    ax.legend(loc='lower center',bbox_to_anchor=(.5,-.12),ncol=4,frameon=False)
    fig.text(.5,.015,'Edges show recorded directed dependencies; vertical positions are for display, not measured risk.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.045,1,1]); fig.savefig(outfig/'multi_tier_dependency_graph_v3.png',dpi=220); plt.close(fig)

    # Clearly labelled detail figure. Only service S01 and a subset of reachable nodes.
    if 'S01' in graph:
        paths = find_service_paths(graph,'S01')
        reachable = sorted({str(n) for path in paths for n in path})
        selected = ['S01'] + [n for n in reachable if n!='S01'][:75]
        sub = graph.subgraph(selected).copy()
        if sub.number_of_nodes()>1:
            pos = nx.spring_layout(sub,seed=42,iterations=100)
            fig,ax=plt.subplots(figsize=(14,9))
            nx.draw_networkx_edges(sub,pos,ax=ax,alpha=.19,arrows=True,arrowsize=8,width=.7)
            for tier in TIERS:
                nodes=[n for n,info in sub.nodes(data=True) if info.get('tier')==tier]
                nx.draw_networkx_nodes(sub,pos,nodelist=nodes,node_size=80 if tier=='Service' else 35, node_color=PALETTE[tier],alpha=.85,ax=ax,label=tier)
            keep_labels={'S01':'Core Banking (S01)'}
            for n in list(sub.nodes)[:14]:
                if n!='S01':keep_labels[n]=str(n)
            nx.draw_networkx_labels(sub,pos,labels=keep_labels,font_size=7,ax=ax)
            ax.set_title(f'{dataset} Core Banking Dependency Detail — Illustrative subset of {len(selected)} nodes',fontsize=13)
            ax.legend(frameon=False,loc='lower left'); ax.axis('off')
            fig.tight_layout(); fig.savefig(outfig/'s01_dependency_subgraph_v3.png',dpi=220); plt.close(fig)

    print('\nV3 DATASET AND ECOSYSTEM BASELINE:')
    print(json.dumps(stats, indent=2))
    print('Saved:',outfig/'multi_tier_dependency_graph_v3.png')
    print('Saved:',outtab/'v3_dataset_and_risk_summary.json')

if __name__ == '__main__': main()
