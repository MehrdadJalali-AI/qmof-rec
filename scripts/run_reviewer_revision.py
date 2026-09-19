#!/usr/bin/env python3
"""Reviewer experiments; preserves the published runner and gates on reproduction."""
from pathlib import Path
import csv, copy, hashlib, json, math, platform, random, sys, time
from collections import defaultdict
import numpy as np
from scipy.optimize import differential_evolution
import scipy
import run_final_diversity_aware_masked_protocol as p
ROOT=p.ROOT
OUT=ROOT/'artifacts/reviewer_revision'
CONFIG=ROOT/'configs/final_diversity_aware_masked_protocol.json'
PRIMARY=['WeightedSum','LEA','TOPSIS','ParetoCrowding','MMR','Random','SemanticOnly']
GAMMAS=[0,.025,.05,.1,.2,.4,.8]
PENALTIES=[0,.025,.05,.1,.2]

def ids(rows): return [r['qmof_id'] for r in rows[:5]]
def write(name,rows): p.write_csv(OUT/name,rows)
def read(name): return p.read_csv(p.FINAL/name)

def gate():
    expected={'WeightedSum':(.8479,.0187,1.),'LEA':(.8479,.0224,1.),'TOPSIS':(.8479,.0187,1.),'ParetoCrowding':(.8447,.0263,.9952),'MMR':(.8479,.0241,1.),'Random':(.7695,.0237,.8809),'SemanticOnly':(.7600,.0240,.8678)}
    actual={r['method']:r for r in read('aggregate_metrics.csv')}
    rows=[]
    for method, values in expected.items():
        for key,target in zip(['rel_at_5','diversity','ndcg_at_5'],values):
            value=float(actual[method][key]); ok=f'{value:.4f}'==f'{target:.4f}'
            rows.append(dict(method=method,metric=key,manuscript=target,reproduced=value,difference=value-target,pass_display_precision=ok))
    write('reproduction/value_comparison.csv',rows)
    if not all(r['pass_display_precision'] for r in rows): raise RuntimeError('Reproduction gate failed; manuscript must not be edited.')
    return actual

def mmr_topk(pool,cfg):
    remaining=list(pool); chosen=[]; lam=cfg['mmr_parameters']['lambda_relevance']
    while remaining and len(chosen)<cfg['top_k']:
        scores=[lam*r['relevance_score']-(1-lam)*max((1-p.item_distance(r,s,'hybrid_material',cfg) for s in chosen),default=0.) for r in remaining]
        chosen.append(remaining.pop(int(np.argmax(scores))))
    return chosen

def distance_matrix(pool,cfg):
    vectors,masks=zip(*(p.vector_for(r,'hybrid_material',cfg) for r in pool))
    v=np.array(vectors); m=np.array(masks); out=np.zeros((len(pool),len(pool)))
    for i in range(len(pool)):
        joint=m&m[i]; n=joint.sum(axis=1); sq=((v-v[i])*joint)**2
        out[i]=np.sqrt(np.divide(sq.sum(axis=1),n,out=np.zeros(len(pool)),where=n>0))
    return out

def de_portfolio(pool,weights,seed,cfg):
    """Fixed list utility; same data/weights but not LEA's history-dependent fitness."""
    d=distance_matrix(pool,cfg); n=len(pool); k=cfg['top_k']
    rel=np.array([r['relevance_score'] for r in pool]); bal=np.array([r['balance_score'] for r in pool])
    pars=cfg['lea_parameters']; calls=0
    def decode(x): return np.argsort(-x,kind='stable')[:k]
    def objective(x):
        nonlocal calls
        calls+=1; ix=decode(x); div=float(d[np.ix_(ix,ix)].sum()/(k*(k-1)))
        return -(rel[ix].mean()+pars['beta']*bal[ix].mean()+pars['gamma']*div-pars['redundancy_penalty']*np.exp(-div))
    rng=np.random.default_rng(seed); init=rng.random((30,n))
    # One transparent constructive seed; remaining 29 are random portfolios.
    ix={r['qmof_id']:i for i,r in enumerate(pool)}
    init[0]=0.; init[0,[ix[r['qmof_id']] for r in p.rank_weighted(pool,weights)[:k]]]=1.
    baseline=objective(init[0]); calls=0
    result=differential_evolution(objective,[(0,1)]*n,init=init,maxiter=59,tol=0,atol=-1,polish=False,seed=seed,updating='immediate',workers=1)
    assert result.fun<=baseline+1e-12
    chosen=[pool[i] for i in decode(result.x)]
    return p.rank_weighted(chosen,weights),dict(function_evaluations=calls,generations=int(result.nit),portfolio_utility=-float(result.fun),initial_weightedsum_utility=-float(baseline))

def metric(method,qd,seed,pool,ranked,ms,cfg):
    return p.metrics_for(method,qd['query_id'],qd['query'],seed,len(pool),ranked,pool,ms,'hybrid_material',cfg)

def screening(group,rows,qd,seed):
    out=[]
    for descriptor in ['density','band_gap']:
        vals=[r[descriptor] for r in rows if r.get(descriptor) is not None and math.isfinite(r[descriptor])]
        out.append(dict(query_id=qd['query_id'],seed=seed,group=group,descriptor=descriptor,n=len(rows),n_observed=len(vals),mean=float(np.mean(vals)) if vals else None,median=float(np.median(vals)) if vals else None,min=min(vals) if vals else None,max=max(vals) if vals else None,missing_fraction=1-len(vals)/len(rows),fraction_density_below_1=sum(r['density']<1 for r in rows)/len(rows),fraction_observed_gap_1_to_3_5=sum(1<=v<=3.5 for v in vals)/len(vals) if vals and descriptor=='band_gap' else None,fraction_observed_gap_at_least_3_5=sum(v>=3.5 for v in vals)/len(vals) if vals and descriptor=='band_gap' else None))
    return out

def self_test(cfg,metadata,ranges):
    qd=cfg['query_scenarios'][0]; w=p.dynamic_weight_engine.generate_weights(qd['query'])
    pool=[p.score_record(r,qd['query_id'],qd['query'],w,ranges) for r in metadata[:8]]
    d=distance_matrix(pool,cfg)
    for i in range(len(pool)):
        for j in range(len(pool)): assert abs(d[i,j]-p.item_distance(pool[i],pool[j],'hybrid_material',cfg))<1e-14
    assert ids(mmr_topk(pool,cfg))==ids(p.rank_mmr(pool,cfg,'hybrid_material'))
    ranked,info=de_portfolio(pool,w,42,cfg)
    assert len(set(ids(ranked)))==5 and info['function_evaluations']==1800
    return 'matrix distances agree with scalar masked distances; MMR prefix agrees; DE returns five unique IDs, uses 1800 evaluations, and preserves initial portfolio utility'

def main():
    OUT.mkdir(parents=True,exist_ok=True); actual=gate(); print('REPRODUCTION GATE PASSED',flush=True)
    cfg=json.loads(CONFIG.read_text()); meta=p.load_metadata(p.BACKEND/'vector_db/metadata.json'); ranges=p.physical_ranges(meta)
    validation=self_test(cfg,meta,ranges)
    original_rankings=read('rankings_all_topk.csv'); original_metrics=read('metrics_per_query_seed.csv')
    ref=defaultdict(list)
    for row in original_rankings: ref[(row['query_id'],int(row['seed']),row['method'])].append(row['qmof_id'])
    sensitivity=[]; ablations=[]; extra=[]; selections=[]; descriptors=[]; timing=[]; deinfo=[]; checks=[]
    for qd in cfg['query_scenarios']:
        qid=qd['query_id']; w=p.dynamic_weight_engine.generate_weights(qd['query']); scored=[p.score_record(r,qid,qd['query'],w,ranges) for r in meta]
        descriptors+=screening('catalog',meta,qd,-1)
        for seed in cfg['random_seeds']:
            pool=p.candidate_pool(scored,qid,qd['query'],seed,100); byid={r['qmof_id']:r for r in pool}
            base=ref[(qid,seed,'LEA')]
            descriptors+=screening('candidate_pool',pool,qd,seed)
            for method in ['Random','WeightedSum','LEA']:
                descriptors+=screening(method,[byid[x] for x in ref[(qid,seed,method)]],qd,seed)
            for gamma in GAMMAS:
                for penalty in PENALTIES:
                    conf=copy.deepcopy(cfg); conf['lea_parameters'].update(gamma=gamma,redundancy_penalty=penalty)
                    start=time.perf_counter(); ranked,history=p.rank_lea(pool,w,seed,conf,'hybrid_material'); ms=(time.perf_counter()-start)*1000
                    row=metric('LEA sensitivity',qd,seed,pool,ranked,ms,cfg)
                    row.update(gamma=gamma,redundancy_penalty=penalty,top5_ids='|'.join(ids(ranked)),same_set_as_baseline=set(ids(ranked))==set(base),same_order_as_baseline=ids(ranked)==base,overlap_baseline=len(set(ids(ranked))&set(base))/5,history_sha256=hashlib.sha256(np.array(history,dtype='<f8').tobytes()).hexdigest())
                    sensitivity.append(row)
                    if gamma==.1 and penalty==.05: assert ids(ranked)==base
                    if (gamma,penalty) in [(0,0),(0,.05)]:
                        ablations.append({**row,'method':'LEA true no diversity' if penalty==0 else 'LEA gamma=0 only'})
            start=time.perf_counter(); mmr=mmr_topk(pool,cfg); ms=(time.perf_counter()-start)*1000
            assert ids(mmr)==ref[(qid,seed,'MMR')]
            extra.append(metric('MMR top5',qd,seed,pool,mmr,ms,cfg)); checks.append(dict(query_id=qid,seed=seed,mmr_top5_matches_full=True))
            start=time.perf_counter(); de,info=de_portfolio(pool,w,seed,cfg); ms=(time.perf_counter()-start)*1000
            extra.append(metric('DE portfolio',qd,seed,pool,de,ms,cfg)); deinfo.append(dict(query_id=qid,seed=seed,**info))
            for rank,r in enumerate(de,1): selections.append(dict(query_id=qid,seed=seed,method='DE portfolio',rank=rank,qmof_id=r['qmof_id']))
            # Same-pool score masking diagnostic: absent objective utility zeroed, denominator unmasked.
            zero=copy.deepcopy(pool)
            for r in zero:
                for name in p.ACTIVE_OBJECTIVES:
                    if not r['availability'][name.replace('_score','')]: r[name]=0.
                r['availability']={key:True for key in r['availability']}
                r['relevance_score']=p.masked_weighted_sum(r,w,r['availability'])
            start=time.perf_counter(); zr=p.rank_weighted(zero,w); ms=(time.perf_counter()-start)*1000
            # Evaluation remains the original masked relevance, regardless of diagnostic scoring.
            ranked=[byid[r['qmof_id']] for r in zr]
            ablations.append(metric('WeightedSum zero-imputation diagnostic',qd,seed,pool,ranked,ms,cfg))
            # Candidate-generation diagnostic: uniformly sampled pool, all downstream scoring unchanged.
            uniform=random.Random(seed).sample(scored,100)
            start=time.perf_counter(); ur,_=p.rank_lea(uniform,w,seed,cfg,'hybrid_material'); ms=(time.perf_counter()-start)*1000
            ablations.append(metric('LEA uniform candidate pool',qd,seed,uniform,ur,ms,cfg))
            if seed in [42,43,44]:
                for size in [50,100,200,500,1000]:
                    sp=p.candidate_pool(scored,qid,qd['query'],seed,size)
                    for method,fn in [('WeightedSum',lambda:p.rank_weighted(sp,w)),('TOPSIS',lambda:p.rank_topsis(sp,w)),('LEA',lambda:p.rank_lea(sp,w,seed,cfg,'hybrid_material')[0]),('MMR top5',lambda:mmr_topk(sp,cfg))]:
                        for repeat in range(3):
                            start=time.perf_counter(); ranked=fn(); ms=(time.perf_counter()-start)*1000
                            timing.append(dict(query_id=qid,seed=seed,pool_size=size,method=method,repeat=repeat,runtime_ms=ms,top5_ids='|'.join(ids(ranked))))
            print(qid,seed,'complete',flush=True)
            for name,rows in [('sensitivity.csv',sensitivity),('ablations.csv',ablations),('additional_methods.csv',extra),('screening.csv',descriptors),('runtime_scaling.csv',timing),('de_diagnostics.csv',deinfo),('additional_rankings.csv',selections),('validation.csv',checks)]: write(name,rows)
    combined=[]
    for r in original_metrics:
        converted={k:(float(v) if k not in ['query','query_id','method'] else v) for k,v in r.items()}
        combined.append(converted)
    combined+=extra+ablations
    write('aggregate_extended.csv',p.aggregate(combined)); write('per_scenario_extended.csv',p.query_stratified(combined))
    manifest=dict(status='complete',validation=validation,python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,gamma_grid=GAMMAS,penalty_grid=PENALTIES,seeds=cfg['random_seeds'],runtime_seeds=[42,43,44],runtime_repeats=3,de_evaluations=1800,de_population=30,de_generations=59,de_policy='random-key five-member subsets; one WeightedSum seed plus 29 random populations; fixed list utility R+.1 B+.1 D-.05 exp(-D); return selected set sorted by masked relevance; cache distances included in runtime; not identical to historical LEA fitness',baseline_config_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest())
    (OUT/'experiment_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); print('ALL REVIEWER EXPERIMENTS COMPLETE',flush=True)
if __name__=='__main__': main()
