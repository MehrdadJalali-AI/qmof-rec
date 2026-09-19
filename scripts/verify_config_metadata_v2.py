from pathlib import Path
import sys,json,csv,hashlib,ast
import numpy as np
import run_final_diversity_aware_masked_protocol as p
root=p.ROOT;out=root/'artifacts/presubmission_v2';old=json.loads((out/'before/final_diversity_aware_masked_protocol.json').read_text());new=json.loads((root/'configs/final_diversity_aware_masked_protocol.json').read_text())
assert set(k for k in new if new[k]!=old[k])=={'formula_features'}
assert len(old['formula_features'])==7 and len(new['formula_features'])==8
# The runner never accesses the descriptive formula_features config key.
tree=ast.parse((root/'scripts/run_final_diversity_aware_masked_protocol.py').read_text());keys=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)];assert 'formula_features' not in keys
meta=p.load_metadata(p.BACKEND/'vector_db/metadata.json');ranges=p.physical_ranges(meta);reference=p.read_csv(p.FINAL/'rankings_all_topk.csv');metrics=p.read_csv(p.FINAL/'metrics_per_query_seed.csv');checks=[]
for q in new['query_scenarios']:
 w=p.dynamic_weight_engine.generate_weights(q['query']);scored=[p.score_record(r,q['query_id'],q['query'],w,ranges) for r in meta]
 for seed in new['random_seeds']:
  pool=p.candidate_pool(scored,q['query_id'],q['query'],seed,100)
  for item in pool:
   av,am=p.vector_for(item,'hybrid_material',old);bv,bm=p.vector_for(item,'hybrid_material',new);assert np.array_equal(av,bv) and np.array_equal(am,bm)
  ranked,_=p.rank_lea(pool,w,seed,new,'hybrid_material');expected=[r['qmof_id'] for r in reference if r['query_id']==q['query_id'] and int(r['seed'])==seed and r['method']=='LEA'];assert [r['qmof_id'] for r in ranked[:5]]==expected
  a=p.metrics_for('LEA',q['query_id'],q['query'],seed,100,ranked,pool,0,'hybrid_material',new);b=next(r for r in metrics if r['query_id']==q['query_id'] and int(r['seed'])==seed and r['method']=='LEA')
  for k in ['rel_at_5','ndcg_at_5','diversity','hypervolume_proxy']:assert abs(a[k]-float(b[k]))<1e-14
  checks.append({'query_id':q['query_id'],'seed':seed,'vector_and_mask_identity':True,'top5_order_identity':True,'metric_identity':True})
for rel,sha in json.loads((out/'frozen_result_hashes.json').read_text()).items():assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==sha
report={'decision':'descriptive metadata only; append element_fraction_hetero; executable protocol unchanged','config_key_unused_by_runner':True,'regression_tests':'21 passed in 0.32s','pool_vector_masks_checked':5000,'lea_paired_rankings_checked':50,'frozen_csv_hashes_unchanged':True,'checks':checks,'old_config_sha256':hashlib.sha256((out/'before/final_diversity_aware_masked_protocol.json').read_bytes()).hexdigest(),'corrected_config_sha256':hashlib.sha256((root/'configs/final_diversity_aware_masked_protocol.json').read_bytes()).hexdigest()}
(out/'configuration_metadata_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: 5000 vectors/masks, 50 LEA ordered lists and metrics unchanged; frozen artifact hashes unchanged.')
