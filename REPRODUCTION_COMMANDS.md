# Reproduction Commands

## Focused backend tests

Clean-clone setup:

```bash
git clone https://github.com/MehrdadJalali-AI/qmof-rec.git
cd qmof-rec
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Run the focused mask-aware regression suite:

```bash
PYTHONPATH=backend pytest -q backend/tests/test_missing_data_masks.py
```

Observed result during final diversity revision:

```text
21 passed in 0.26s
```

## Final diversity-aware mask-aware rerun

Run the complete final protocol from the repository root:

```bash
python3 scripts/run_final_diversity_aware_masked_protocol.py \
  --config configs/final_diversity_aware_masked_protocol.json
```

This creates:

```text
artifacts/final_diversity_aware_masked_protocol/
artifacts/final_masked_protocol_before_diversity_revision/
artifacts/diversity_revision/
```

The final rerun generates candidate pools, top-K outputs for every method/query/seed, aggregate metrics, query-stratified summaries, variance decomposition, candidate-pool sensitivity, catalog coverage, top-K overlap, diversity-representation comparisons, zero-diversity diagnosis, final figures, and a deterministic local candidate-conditioned explanation rerun.

The same command reproduces the principal manuscript tables: the aggregate ranking table, the ablation/graph-aware table, and the 30-query candidate-conditioned explanation table. The reported explanation table is not a live LLM benchmark; it uses saved LEA candidate lists and deterministic local explanations so it can run without `OPENAI_API_KEY`.

## Final consistency audit artifacts

The final consistency pass saved machine-readable audit outputs in:

```text
artifacts/final_consistency_audit/
```

Key files:

```text
diversity_distance_audit.csv
hybrid_weight_sensitivity.csv
lea_vs_weightedsum_query_block_diversity.csv
manuscript_code_consistency.csv
```

These artifacts verify that active objective-space distance is used for LEA candidate remapping, while the hybrid material distance is used for reported list diversity, MMR redundancy, and Pareto crowding. The hybrid-weight sensitivity rescored saved top-K lists under alternative distance weights; it did not rerun primary rankings.

## Manuscript builds

From `manuscript/`:

```bash
cd manuscript
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex
cp main.pdf main_submission_ready.pdf
cp supplementary_material.pdf supplementary_material_submission_ready.pdf
cp main.pdf main_submission_final.pdf
cp supplementary_material.pdf supplementary_material_submission_final.pdf
```

Observed result during revision:

```text
main.pdf generated successfully
supplementary_material.pdf generated successfully
```

The main and supplementary manuscript logs have minor overfull/underfull table-box warnings only.

## Descriptor coverage audit

The revision artifacts in the manuscript folder report:

```text
band_gap: 10,810 / 20,372 observed
density: 20,372 / 20,372 observed
void_fraction: 0 / 20,372 observed
```

Because void fraction is unavailable for all local metadata records, porosity is excluded from active numerical objectives.
