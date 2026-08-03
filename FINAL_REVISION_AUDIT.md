# Final Revision Audit

## Completed

- Preserved the prior final-mask-aware outputs under `artifacts/final_masked_protocol_before_diversity_revision/`.
- Added `configs/final_diversity_aware_masked_protocol.json`.
- Added `scripts/run_final_diversity_aware_masked_protocol.py`.
- Diagnosed the zero-diversity result and saved the report under `artifacts/diversity_revision/zero_diversity_diagnosis.md`.
- Added final diversity-revision artifacts, including active-vector audits, pairwise distances, diversity-representation comparison, aggregate metrics, per-query/seed metrics, catalog coverage, top-K overlap, candidate-pool sensitivity, and RAG/explanation rerun outputs.
- Extended missing-data and diversity regression tests.
- Updated the main manuscript and supplementary material for the final diversity-aware protocol.
- Created `manuscript/main_submission_ready.pdf`.
- Created `manuscript/supplementary_material_submission_ready.pdf`.
- Created a separate `manuscript/title_page.docx` with authors and affiliation while keeping the main manuscript anonymous per prior author-list removal request.

## Validation

- `PYTHONPATH=backend pytest -q backend/tests`: passed, 21 tests.
- `python3 scripts/run_final_diversity_aware_masked_protocol.py --config configs/final_diversity_aware_masked_protocol.json`: completed.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`: passed.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex`: passed.
- `title_page.docx` rendered successfully and was visually checked.

## Zero-Diversity Diagnosis

The zero diversity in the prior final-mask-aware run was a representation limitation, not a distance bug and not identical raw materials. The diversity distance was computed over binned active utility scores. Band gaps between 1.0 and 3.5 eV mapped to 1.0, densities between 1.0 and 2.0 g/cm3 mapped to 0.7, and the stability proxy often inherited the binned density score. The CO2 top candidates had different raw density and band-gap values but identical transformed active objective vectors.

## Final Result Interpretation

- Final selected diversity representation: hybrid material distance using full-precision observed density, observed band gap, formula-derived descriptors, and formula-derived graph proxies.
- WeightedSum, TOPSIS, MMR, and baseline LEA tie on Rel@5 = 0.8479 and NDCG@5 = 1.0000.
- Baseline LEA diversity = 0.0224 versus WeightedSum diversity = 0.0187.
- MMR diversity = 0.0241 and remains the highest among relevance-preserving primary methods, but runtime is highest at about 2114 ms.
- ParetoCrowding diversity = 0.0263, but Rel@5 drops to 0.8447 and NDCG@5 to 0.9952.
- LEA no-diversity is not list-identical to WeightedSum: same top-K set in 11/50 rows, same exact order in 0/50 rows, mean overlap 0.576.
- Candidate-pool sizes 50, 100, and 200 preserve Rel@5 = 0.8479 and NDCG@5 = 1.0000, with diversity 0.0225, 0.0224, and 0.0229.
- Actual catalog coverage for baseline LEA is 32/20,372 = 0.001571.
- Final local grounded explanation rerun: 30 queries, 5.0/5 groundedness, 5.0/5 metadata consistency, 5.0/5 limitation awareness, 4.5/5 explanation quality, 0% automated hallucination flags.

## Remaining Limitations

No experimental synthesis, adsorption simulation, DFT validation, porosity validation, expert relevance labels, online user study, CIF-derived graph benchmark, or live expert-human explanation evaluation is claimed.

## Operational Note

Pushing to GitHub still depends on local GitHub authentication. Do not use any token pasted into chat; revoke exposed tokens and push with a fresh PAT or SSH credential from a secure terminal session.
