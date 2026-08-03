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

The final rerun generates candidate pools, top-K outputs for every method/query/seed, aggregate metrics, query-stratified summaries, variance decomposition, candidate-pool sensitivity, catalog coverage, top-K overlap, diversity-representation comparisons, zero-diversity diagnosis, final figures, and a local grounded explanation rerun.

## Manuscript builds

From `manuscript/`:

```bash
cd manuscript
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex
cp main.pdf main_submission_ready.pdf
cp supplementary_material.pdf supplementary_material_submission_ready.pdf
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
