# QMOF-Rec Reviewer Revision Changelog

Branch: `reviewer-arnd-revision`

## Descriptor handling

- Added explicit descriptor availability utilities in `backend/app/recommendation/objective_utils.py`.
- Changed feature extraction so missing values are represented by masks rather than being silently treated as observed zeros.
- Removed void fraction and porosity from active numerical objectives because the local metadata audit found 0/20,372 observed void-fraction values.
- Updated weighted scoring, similarity, novelty, and LEA remapping to use masked objectives and jointly observed dimensions.

## Ranking and recommendation behavior

- Updated dynamic query weights to exclude a `porosity` weight for CO2/gas-storage queries.
- Updated hybrid ranking to report `porosity_score = None` and a void-fraction availability note instead of scoring unavailable porosity.
- Updated explanatory text so unavailable void fraction is surfaced as a limitation and not used as a numerical rationale.
- Added focused regression tests for missing descriptors, genuine zeros, dynamic weights, hybrid ranking, masked similarity, and LEA porosity exclusion.

## Vector/RAG/frontend behavior

- Updated vector-index serialization so unavailable void fraction is written as unavailable metadata rather than an empty numeric-looking value.
- Kept LLM guardrails requiring limitation statements for porosity/adsorption queries.
- Removed void-fraction plotting from dashboard analytics and changed the material card to display unavailable void fraction explicitly.

## Manuscript and supplement

- Revised the manuscript to describe QMOF-Rec as a hybrid scientific recommender with a strong content-based focus.
- Added descriptor masks to the formalism and algorithms.
- Regenerated the active-objective radar figure without a porosity axis.
- Added descriptor coverage and repeated-seed caveats to the supplementary material.
- Added reviewer-requested Seko et al. and Qu et al. references, plus a narrow KadiAssistant comparison.
- Added a generative-AI-use declaration.

## Final mask-aware rerun

- Added a single final configuration at `configs/final_mask_aware_protocol.json`.
- Added `scripts/run_final_mask_aware_protocol.py` to create candidate pools, run all final rankers and ablations, calculate metrics, generate figures, preserve historical artifacts, and write protocol comparisons.
- Reran the final mask-aware protocol over 20,372 local QMOF metadata records, five query scenarios, ten seeds, top-K = 5, and candidate-pool sizes 50/100/200.
- Updated the manuscript interpretation: baseline LEA ties WeightedSum/TOPSIS/ParetoCrowding on the aligned masked relevance metrics in the final deterministic protocol and does not show a baseline diversity advantage.
- Added list-level WeightedSum versus LEA-no-diversity comparison with saved top-K IDs.

## Final diversity-aware correction

- Preserved the previous final-mask-aware outputs under `artifacts/final_masked_protocol_before_diversity_revision/`.
- Added `configs/final_diversity_aware_masked_protocol.json`.
- Added `scripts/run_final_diversity_aware_masked_protocol.py`.
- Diagnosed the previous zero-diversity result as utility-score binning/saturation rather than identical raw materials or a distance bug.
- Selected a full-precision hybrid material diversity representation using observed density, observed band gap, formula-derived descriptors, and formula-derived graph proxies.
- Reran all ranking methods, ablations, graph-aware variants, candidate-pool sensitivity, diversity-representation comparisons, and a local grounded explanation evaluation.
- Updated the manuscript and supplement with final values: LEA Rel@5 = 0.8479, NDCG@5 = 1.0000, diversity = 0.0224; WeightedSum diversity = 0.0187; MMR diversity = 0.0241.
- Corrected `Unique@K` versus actual catalog coverage terminology.
- Created `manuscript/main_submission_ready.pdf`, `manuscript/supplementary_material_submission_ready.pdf`, and `manuscript/title_page.docx`.
