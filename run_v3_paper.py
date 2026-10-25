#!/usr/bin/env python3
"""Isolated V3 (2100-asset) reproduction runner for DARP-PQC project.

Run from the original PQC_Banking_Risk_Framework_COMPLETE folder:
    python run_v3_paper.py --step quick
    python run_v3_paper.py --step risk
    python run_v3_paper.py --step security
    python run_v3_paper.py --step figures

Runs are isolated under V3_2100_Paper_Results/ and never overwrite results/.
The original modules and risk model are reused; only V1-hardcoding/output labels
are patched in the disposable working copy. NO invented numerical results.
"""
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
RESULTS = PROJECT/'V3_2100_Paper_Results'
WORKSPACE = RESULTS/'workspace'
FIGURES = RESULTS/'figures'
TABLES = RESULTS/'tables'
LOGS = RESULTS/'logs'
MODES = {
  'quick': [('validate','src.data_loader',[]),('topology','experiments.v3_graphs',[])],
  'risk': [('final_migration','experiments.final_evaluation',[]),
           ('budget_sweep','experiments.budget_sweep',[]),
           ('qars_comparison','experiments.compare_qars_paper',[]),
           ('ablation_study','experiments.ablation_study',[]),
           ('scalability','experiments.scalability_analysis',[])],
  'security': [('gateway','experiments.banking_gateway_demo',[]),
              ('adaptive_policy','experiments.darp_policy_migration_demo',[]),
              ('cross_tier','experiments.cross_tier_final_evaluation',['--iterations','20']),
              ('security_comparison','experiments.compare_security_models',['--iterations','20']),
              ('pqc_benchmark','experiments.pqc_benchmark',['--iterations','100'])],
  'figures': [('paper_figures','experiments.generate_final_figures',[])]
}


def replace_once(fp, old, new):
    txt=fp.read_text(encoding='utf-8')
    if old not in txt:
        if new not in txt:
            raise RuntimeError(f'Expected original code fragment not found in {fp}: {old!r}')
        return
    fp.write_text(txt.replace(old,new),encoding='utf-8')


def setup():
    if not (PROJECT/'src'/'data_loader.py').exists() or not (PROJECT/'experiments'/'final_evaluation.py').exists():
        raise SystemExit('Run this script from inside the original PQC_Banking_Risk_Framework_COMPLETE project folder.')
    if not (PROJECT/'data_v3'/'banking_assets.csv').exists():
        raise SystemExit('data_v3/banking_assets.csv is missing. Install the 2100-asset dataset first.')
    for d in [RESULTS, FIGURES, TABLES, LOGS, WORKSPACE]:d.mkdir(parents=True,exist_ok=True)
    for dirname in ['src','experiments','pqc_layer','tests','data','data_v2','data_v3']:
        orig=PROJECT/dirname; dest=WORKSPACE/dirname
        if not orig.exists():continue
        if dest.exists():shutil.rmtree(dest)
        shutil.copytree(orig,dest, ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
    # In the isolated workspace, results/ points to the NEW folder, not original results/.
    result_link=WORKSPACE/'results'
    if result_link.is_symlink():result_link.unlink()
    elif result_link.exists():
        raise RuntimeError('The isolated workspace results/ is not a symlink. Refusing to delete it.')
    result_link.symlink_to('..',target_is_directory=True)
    # Patch v3 dataset selection (Mac installation may have done this already).
    loader=WORKSPACE/'src'/'data_loader.py'
    txt=loader.read_text(encoding='utf-8')
    if 'dataset_version == "v3"' not in txt:
        key='    else:\n        raise ValueError("Invalid PQC_DATASET value. Use v1 or v2.")'
        if key not in txt:
            raise RuntimeError('Could not auto-extend data loader in the disposable worktree.')
        txt=txt.replace(key,'    elif dataset_version == "v3":\n        data_dir = PROJECT_ROOT / "data_v3"\n'+key)
        loader.write_text(txt,encoding='utf-8')
    # Use v3 in scripts that override users' PQC_DATASET or refer to a V1 result.
    final=WORKSPACE/'experiments'/'final_evaluation.py'
    replace_once(final,'setdefault("PQC_DATASET", "v1")','setdefault("PQC_DATASET", "v3")')
    replace_once(final,'_v1.csv','_v3.csv')
    replace_once(final,'FINAL V1 RESULTS','FINAL V3 RESULTS')
    qars=WORKSPACE/'experiments'/'compare_qars_paper.py'
    replace_once(qars,'os.environ["PQC_DATASET"] = "v1"','os.environ["PQC_DATASET"] = "v3"')
    replace_once(qars,'common V1 dataset','common V3 dataset')
    bench=WORKSPACE/'experiments'/'scalability_analysis.py'
    replace_once(bench,'["v1", "v2"]','["v1", "v2", "v3"]')
    security=WORKSPACE/'experiments'/'compare_security_models.py'
    replace_once(security,'final_strategy_comparison_v1.csv','final_strategy_comparison_v3.csv')
    gateway=WORKSPACE/'experiments'/'banking_gateway_demo.py'
    replace_once(gateway,'"V1 synthetic"','"V3 synthetic"')
    # derive_tier_requirements defaults to original data/ even when the
    # PQC_DATASET environment variable is V3. Override only its DATASET path
    # in the disposable workspace, avoiding a V3 risk / V1 attestations mismatch.
    tier=WORKSPACE/'pqc_layer'/'multitier_assurance.py'
    replace_once(tier,'dataset: str = "data"','dataset: str = "data_v3"')
    cross=WORKSPACE/'experiments'/'cross_tier_final_evaluation.py'
    replace_once(cross,'"V1 synthetic banking ecosystem"','"V3 synthetic banking ecosystem"')
    script=PROJECT/'v3_graphs.py'
    if not script.exists():raise RuntimeError('Put v3_graphs.py beside run_v3_paper.py in original project folder.')
    shutil.copy2(script,WORKSPACE/'experiments'/'v3_graphs.py')
    print('\nPrepared isolated workspace:',WORKSPACE)
    print('Your original data/, data_v2/, data_v3/, results/ and paper are unchanged.\n')


def verify_workspace():
    if not (WORKSPACE/'experiments'/'v3_graphs.py').exists():
        raise SystemExit('Run python run_v3_paper.py --step setup first.')
    if not (WORKSPACE/'results').is_symlink():
        raise SystemExit('Isolated results link is missing. Run --step setup first.')


def run_one(name,module,args,force=False):
    outfile=LOGS/(name+'.log'); done=LOGS/(name+'.success')
    if done.exists() and not force:
        print('SKIP previously completed:',name,'(use --force to rerun)'); return True
    done.unlink(missing_ok=True)
    env=os.environ.copy()
    env['PQC_DATASET']='v3'
    env['MPLBACKEND']='Agg'
    cmd=[sys.executable,'-u','-m',module]+args
    print('\n'+'='*76)
    print('RUN',name,':',' '.join(cmd))
    print('NEW OUTPUT FOLDER:',RESULTS)
    print('='*76,flush=True)
    with outfile.open('w',encoding='utf-8') as log:
        log.write('COMMAND: '+' '.join(cmd)+'\nWORKSPACE: '+str(WORKSPACE)+'\n\n');log.flush()
        proc=subprocess.Popen(cmd,cwd=WORKSPACE,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              text=True,bufsize=1,errors='replace')
        try:
            for line in proc.stdout:
                print(line,end='',flush=True);log.write(line)
            exitcode=proc.wait()
        except KeyboardInterrupt:
            proc.terminate();print('\nInterrupted; restart this step later.')
            raise
    if exitcode==0:
        done.write_text('success\n')
        print('\nDONE:',name,' | Saved log:',outfile);return True
    print('\nERROR:',name,' exit code',exitcode,' | Inspect log:',outfile)
    return False


def main():
    p=argparse.ArgumentParser(description='V3(2100) graph and result generation in an isolated folder')
    p.add_argument('--step',choices=['setup','quick','risk','security','figures','all'],required=True)
    p.add_argument('--force',action='store_true',help='Rerun completed modules and overwrite ONLY new-folder files')
    p.add_argument('--continue-on-error',action='store_true',help='Try next experiment even if a module fails')
    args=p.parse_args()
    if args.step=='setup':setup();return
    verify_workspace()
    modes=['quick','risk','security','figures'] if args.step=='all' else [args.step]
    if args.step=='figures':
        required=['budget_sweep.csv','ablation_topology.csv','ablation_prioritization.csv','scalability_analysis.csv']
        missing=[f for f in required if not (TABLES/f).exists()]
        if missing:
            print('These new-folder tables are not available:',', '.join(missing))
            print('Run --step risk first. No old results will be substituted.');sys.exit(2)
    started=time.perf_counter()
    for mode in modes:
        for name,module,params in MODES[mode]:
            if not run_one(name,module,params,args.force) and not args.continue_on_error:
                raise SystemExit(f'Interrupted at {name}; earlier steps remain saved in {RESULTS}')
    print('\nFINISHED (elapsed %.1f min)'%((time.perf_counter()-started)/60))
    print('Paper figures:',FIGURES)
    print('Numeric tables:',TABLES)
    print('Terminal logs:',LOGS)
    print('Note: These are measured V3 outputs. Prior V1 percentages must NOT be reused as V3 results.')

if __name__=='__main__':main()
