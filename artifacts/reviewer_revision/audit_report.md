# Phase 1 reproduction and reviewer revision — authoritative repository

Date: 2026-09-19. This report supersedes the prior blocked audit, which searched the wrong executable location.

## Outcome

**Primary ranking reproduction passed.** Executable repository: `/Users/mehrdadjalali/Documents/GitHub/qmof-rec`, baseline commit `10082124cf81a90ce40b4bd6306862416a46d2e6`. No older sibling implementation was used. All seven original methods reproduce Rel@5, NDCG@5, and hybrid diversity at four-decimal manuscript precision. Focused regression suite: **21 passed**.

Source hashes, descriptor coverage, environment, and the 21 individual comparisons are saved under `artifacts/reviewer_revision/reproduction/`. Density coverage is 20,372; finite band gap 10,810; void fraction 0. Original configuration, runner, objective utilities, mask-aware scoring, hybrid representation, and revised backend LEA are present. The three requested historical artifact directories were absent before execution. The final protocol regenerated final_diversity_aware_masked_protocol and diversity_revision. A new final_consistency_audit records this revision; no absent historical artifacts are invented.

## Completed extensions

- Complete all-method, all-scenario results: five scenarios, ten seeds.
- Gamma × redundancy sensitivity: 35 settings and 1750 runs; selected IDs and history hashes retained.
- True no-diversity ablation: both coefficients zero, diversity 0.01865774.
- Same-pool zero-imputation and uniform-candidate-pool diagnostics.
- DE portfolio baseline: same pools and hybrid distances, 1,800 fixed-list utility evaluations; objective differs explicitly from historical LEA fitness.
- Runtime scaling: four methods × five sizes × five queries × three seeds × three repeats = 900 timings.
- Catalog/pool/Random/WeightedSum/LEA descriptor-level screening summaries.
- Revised main manuscript, supplement, and point-by-point response.

## Corrections that materially affect interpretation

1. Original full-list MMR: 2209.67 ms; exactly matching top-five MMR: 12.70 ms; LEA: 87.26 ms. The previous LEA runtime advantage is withdrawn.
2. Gamma=0 alone leaves the redundancy penalty active. True no diversity differs from the published mislabeled row.
3. Graph-named ranking rows are engineered proxy augmentation, not trained GNNs or graph-only policies. Prior graph-regression numbers/topology counts are not reproduced and have been removed from evidentiary results. CIF files exist but are not consumed by the final ranking protocol.
4. Several explanation scores and all violation flags are assigned by the runner. They are not independent quality or hallucination measurements; the former quality claims are withdrawn.
5. The physical band-gap coordinate is masked, but proxy A internally uses a zero fallback for absent gap. The configuration description lists seven formula features; executed code uses eight including heteroatom fraction. Both are disclosed; the baseline code was not silently changed.
6. LEA stores best-ever candidate fitness across changing contexts. Its trace is not a fixed final-list objective convergence proof.

## Limits and submission actions

No experimental/adsorption/porosity/new-DFT/expert validation, trained transformer or GNN ranking benchmark, live LLM evaluation, or sequential BO/active-learning experiment is claimed. New artifacts remain local and require a versioned deposit before submission. Author review is needed before external submission; no messages or files have been sent externally.
