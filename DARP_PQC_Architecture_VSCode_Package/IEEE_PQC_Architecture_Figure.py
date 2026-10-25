"""Publication-ready DARP-PQC architecture diagram.

Run in VS Code terminal:
    python IEEE_PQC_Architecture_Figure.py

Dependencies: matplotlib  (pip install matplotlib)
Writes editable vector SVG, print-quality PDF and 350 dpi PNG in
'PQC_Architecture_Figure/' next to this script.

Nodes are based on the actual modules in the supplied PQC banking project.
Planning risk reductions are model-based; vendor attestations are simulated.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import rcParams

OUT = Path(__file__).resolve().parent / 'PQC_Architecture_Figure'
OUT.mkdir(parents=True, exist_ok=True)

INK = '#18293F'
SUB = '#586579'
NAVY = '#183C5B'
TEAL = '#087F82'
PURPLE = '#6B508A'
AMBER = '#AA7016'
BACKGROUND = '#FFFFFF'
EDGE = '#DCE4EB'
LIGHT = '#F6F8FB'

rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','pdf.fonttype':42})
fig, ax = plt.subplots(figsize=(16,10.25), dpi=160)
fig.patch.set_facecolor(BACKGROUND)
ax.set_xlim(0, 16)
ax.set_ylim(0, 10.25)
ax.axis('off')
fig.subplots_adjust(left=0.022, right=0.978, top=0.98, bottom=0.025)

# Visual primitives

def txt(x,y,t, size=11, color=INK, weight='regular',ha='left',va='center',z=20):
    ax.text(x,y,t,fontsize=size,color=color,fontweight=weight,ha=ha,va=va,zorder=z,
            linespacing=1.23)

def plate(x,y,w,h,fill='#FFFFFF',stroke=EDGE,rad=0.14,lw=1.1):
    p=FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0.012,rounding_size={rad}',
                     facecolor=fill,edgecolor=stroke,lw=lw,zorder=1)
    ax.add_patch(p)
    return p

def box(x,y,w,h,head,desc,code='', accent=NAVY,fill='#FFFFFF',head_size=13,desc_size=11):
    plate(x,y,w,h,fill=fill,stroke=EDGE,rad=0.10)
    ax.plot([x+0.12,x+0.12],[y+0.14,y+h-0.14],color=accent,lw=4.3,solid_capstyle='round',zorder=3)
    txt(x+0.31,y+h-0.31,head,size=head_size,color=accent,weight='bold',va='top')
    txt(x+0.31,y+h-0.63,desc,size=desc_size,va='top',color=INK)
    if code:
        txt(x+0.31,y+0.11,code,size=8.3,va='center',color=SUB)

def arrow(x1,y1,x2,y2,color='#5D6B7B',lw=1.7,ls='-',rad=0.0,style='-|>',mutation=15):
    p=FancyArrowPatch((x1,y1),(x2,y2),arrowstyle=style,mutation_scale=mutation,
                      linewidth=lw,linestyle=ls,color=color,connectionstyle=f'arc3,rad={rad}',zorder=10,
                      shrinkA=0,shrinkB=0)
    ax.add_patch(p)

def group_header(y,number,title,subtitle,color):
    plate(0.46,y-0.13,0.39,0.31,fill=color,stroke=color,rad=0.07)
    txt(0.655,y+0.022,number,size=12,color='#FFFFFF',weight='bold',ha='center')
    txt(0.99,y+0.03,title,size=14.5,color=INK,weight='bold')
    txt(15.24,y+0.03,subtitle,size=9.3,color=SUB,ha='right')

# Title
txt(0.46,9.88,'DEPENDENCY AWARE PQC MIGRATION FRAMEWORK FOR DIGITAL BANKING',size=19.6,color=NAVY,weight='bold',va='center')
txt(0.46,9.53,'End-to-end system architecture  |  Graph-aware migration planning and risk-bound banking transactions',
    size=12.4,color=SUB)
ax.plot([0.46,15.56],[9.34,9.34],color=NAVY,lw=1.7)

# 1. Dataset and graph
plate(0.38,7.05,15.25,2.09,fill='#F6F8FB',stroke='#EDF1F4',rad=0.14)
group_header(8.82,'1','ASSET INVENTORY & DEPENDENCY MODEL','Synthetic data and service-weighted risk index',NAVY)
box(0.53,7.29,3.42,1.23,'Banking inventory','2,100 assets  |  60 services\n2,862 dependency records','Assets / services / dependencies CSVs',NAVY,head_size=13,desc_size=10.9)
box(4.33,7.29,3.25,1.23,'Load & validate','Schema, tiers, IDs, ranges,\ndependency endpoints','src/data_loader.py',NAVY,head_size=13,desc_size=10.8)
box(7.96,7.29,3.26,1.23,'Build directed graph','Internal / third-party / sub-tier\n2,856 unique weighted edges','src/graph_builder.py',NAVY,head_size=13,desc_size=10.6)
box(11.6,7.29,3.67,1.23,'Evaluate ecosystem risk','Direct risk + strongest dependency\npaths + service-weighted ER','src/risk_model.py  |  src/propagation.py',NAVY,head_size=12.5,desc_size=10.6)
for x1,x2 in [(3.96,4.32),(7.59,7.95),(11.23,11.59)]: arrow(x1,7.9,x2,7.9,color=NAVY)

# 2. Migration planner
plate(0.38,4.69,15.25,2.17,fill='#F1F9F7',stroke='#E3F2EE',rad=0.14)
group_header(6.55,'2','RISK-BASED MIGRATION PLANNER','Budgeted counterfactual planning, not live deployment',TEAL)
box(0.53,4.93,3.45,1.22,'Candidate risk impact','Temporarily set vulnerability to 0\nRecompute modeled ΔER','src/remediation.py',TEAL,head_size=12.7,desc_size=10.7)
box(4.35,4.93,3.22,1.22,'Priority calculation','Choose largest positive ΔER / cost\nwithin remaining budget','src/prioritization.py',TEAL,head_size=12.7,desc_size=10.6)
box(7.95,4.93,3.34,1.22,'Dynamic migration plan','Select asset; update model; rerank\nBudget ceilings: 2.5 / 5.0 / 7.5','experiments/final_evaluation.py',TEAL,head_size=12.2,desc_size=10.5)
box(11.67,4.93,3.6,1.22,'Planning outputs','Ranked asset list, migration trace\nNew modeled ER; comparison CSVs','results/tables  |  results/figures',TEAL,head_size=12.7,desc_size=10.7)
for x1,x2 in [(3.99,4.34),(7.58,7.94),(11.3,11.66)]: arrow(x1,5.54,x2,5.54,color=TEAL)
# risk informs candidate ranking
arrow(13.42,7.28,13.42,6.93,color=TEAL,rad=0)
arrow(13.42,6.93,2.25,6.93,color=TEAL,ls='--',style='-',mutation=14)
arrow(2.25,6.93,2.25,6.17,color=TEAL,ls='--')
txt(7.8,7.02,'risk context',size=9.8,color=TEAL,weight='bold',ha='center')

# 3. Transaction layer
plate(0.38,1.91,15.25,2.59,fill='#F8F6FB',stroke='#EEE9F3',rad=0.14)
group_header(4.18,'3','TRANSACTION-TIME PQC ENFORCEMENT','ML-KEM / ML-DSA with simulated supplier evidence',PURPLE)
box(0.53,2.70,3.37,1.22,'Risk-bound policy','Standard: ML-KEM-768 / ML-DSA-65\nElevated: ML-KEM-1024 / ML-DSA-87','pqc_layer/darp_pqc.py',PURPLE,head_size=12.3,desc_size=10.3)
box(4.25,2.70,3.35,1.22,'Banking gateway + RBAC','Service policy, actor authorization\nEpoch & policy-digest binding','pqc_layer/banking_gateway.py',PURPLE,head_size=12.3,desc_size=10.7)
box(7.95,2.70,3.34,1.22,'Cryptographic protection','OpenSSL ML-KEM, ML-DSA\nHKDF-SHA256 + AES-256-GCM','pqc_layer/crypto_backend.py',PURPLE,head_size=12.0,desc_size=10.7)
box(11.64,2.70,3.63,1.22,'Verify and accept','Signature + binding + replay checks\nReject missing / invalid tier evidence','pqc_layer/multitier_assurance.py',PURPLE,head_size=12.2,desc_size=10.6)
for x1,x2 in [(3.91,4.24),(7.61,7.94),(11.30,11.63)]: arrow(x1,3.3,x2,3.3,color=PURPLE)
# policy derived from ecosystem context (dashed diagonal down at x=1.2)
arrow(12.98,7.25,15.5,7.25,color=PURPLE,style='-',ls=':',lw=1.1)
arrow(15.5,7.24,15.5,4.54,color=PURPLE,style='-',ls='--',lw=1.25)
arrow(15.5,4.54,1.25,4.54,color=PURPLE,style='-',ls='--',lw=1.25)
arrow(1.25,4.54,1.25,3.94,color=PURPLE,ls='--',lw=1.25)
txt(12.75,4.63,'policy refresh',size=9.0,color=PURPLE,ha='center',weight='bold')
# tier providers supporting cross-tier assurance
plate(0.53,2.08,14.74,0.49,fill='#FFFFFF',stroke='#E1DBEB',rad=0.08)
txt(0.77,2.32,'Cross-tier evidence',size=11.3,color=PURPLE,weight='bold')
txt(4.18,2.32,'Simulated third-party + sub-tier signed acknowledgements',size=10.8,color=INK)
txt(11.75,2.32,'enforced at gateway',size=10.2,color=PURPLE,weight='bold')
arrow(13.43,2.57,13.43,2.69,color=PURPLE,ls='--',lw=1.5,mutation=11)

def eval_box(x,y,w,h,head,desc):
    plate(x,y,w,h,fill='#FFFFFF',stroke=EDGE,rad=0.08)
    ax.plot([x+0.12,x+0.12],[y+0.11,y+h-0.11],color=AMBER,lw=4.1,solid_capstyle='round',zorder=3)
    txt(x+0.31,y+h-0.21,head,size=11.8,color=AMBER,weight='bold',va='center')
    txt(x+0.31,y+0.15,desc,size=10.0,color=INK,va='center')

# 4. Evidence
plate(0.38,0.35,15.25,1.32,fill='#FBF8F1',stroke='#F2EBD7',rad=0.14)
group_header(1.44,'4','EVALUATION & ARTIFACTS','Planning and cryptographic tests reported separately',AMBER)
eval_box(0.53,0.54,7.00,0.65,'Migration / graph evaluation','Baselines, adapted QARS, budget sweeps, ablation, scalability')
eval_box(8.02,0.54,7.25,0.65,'Security / performance checks','PQC operations, policy changes, tier-gate tests, latency, envelope size')
# small connectors vertically
arrow(13.32,4.9,13.32,4.61,color=TEAL,style='-',ls=':',lw=1.1)
arrow(13.32,1.91,13.32,1.74,color=AMBER,style='-',ls='--',lw=1.5)
arrow(4.0,4.69,4.0,4.6,color=TEAL,style='-',lw=1)
# Footer disclaimer
txt(0.5,0.12,'Interpretation: migration reduces a synthetic modeled-risk index; supplier evidence is issued by simulated providers, not independently attested real vendors.',
    size=9.6,color=SUB)

for ext in ['svg','pdf','png']:
    kwargs={'bbox_inches':'tight','pad_inches':0.12, 'facecolor':'white'}
    if ext=='png': kwargs['dpi']=320
    fig.savefig(OUT / f'DARP_PQC_Full_System_Architecture.{ext}',**kwargs)
print('Exported architecture diagram to',OUT)
plt.close(fig)
