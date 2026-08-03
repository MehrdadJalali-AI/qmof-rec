# Final Revision Audit

## Completed

- Created and worked on branch `reviewer-arnd-revision`.
- Implemented mask-aware descriptor handling for missing values.
- Removed void fraction and porosity from active numerical ranking objectives.
- Added focused regression tests for missing descriptor behavior.
- Updated frontend metric displays so void fraction is not plotted as an active metric.
- Updated manuscript and supplementary material in `/Users/mehrdadjalali/Documents/SRH_Research/QMOF-Rec/QMOF_Rec`.
- Added `configs/final_mask_aware_protocol.json`.
- Added `scripts/run_final_mask_aware_protocol.py`.
- Reran the final mask-aware protocol across five queries, ten seeds, shared candidate pools, primary rankers, LEA ablations, graph-aware variants, and candidate-pool sizes 50/100/200.
- Preserved historical artifacts under `artifacts/historical_protocol/`.
- Created final comparison and audit outputs under `artifacts/protocol_comparison/`.
- Regenerated `figures/figure_6_objective_radar.*` without a porosity axis.
- Built `main.pdf` and `supplementary_material.pdf`.

## Validation

- `PYTHONPATH=backend pytest -q backend/tests/test_missing_data_masks.py`: passed, 12 tests.
- `python scripts/run_final_mask_aware_protocol.py --config configs/final_mask_aware_protocol.json`: completed and wrote `artifacts/final_masked_protocol/`.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`: passed.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex`: passed.

## Final rerun interpretation

- WeightedSum, TOPSIS, ParetoCrowding, and baseline LEA tie on final Rel@5 = 0.8479 and NDCG@5 = 1.0000.
- Baseline LEA no longer shows a diversity advantage under the final deterministic mask-aware protocol; masked diversity is 0.0000 for the tied top objective profiles.
- MMR gives nonzero diversity (0.0400) but lower Rel@5 (0.8400) and NDCG@5 (0.9871).
- Graph-aware LEA variants preserve Rel@5 = 0.8479 and introduce small nonzero diversity.
- WeightedSum and LEA-no-diversity are not list-identical: same top-K set in 10/50 query/seed rows, same exact order in 0/50 rows, mean top-K overlap 0.596.

## Remaining operational note

Pushing the branch to GitHub still depends on local GitHub authentication. Earlier push attempts failed because the HTTPS remote could not read credentials in this environment.
