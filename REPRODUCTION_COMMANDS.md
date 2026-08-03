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

Observed result during revision:

```text
12 passed in 0.25s
```

## Final mask-aware rerun

Run the complete final protocol from the repository root:

```bash
python scripts/run_final_mask_aware_protocol.py \
  --config configs/final_mask_aware_protocol.json
```

This creates:

```text
artifacts/final_masked_protocol/
artifacts/protocol_comparison/
artifacts/historical_protocol/
```

The final rerun generates candidate pools, top-K outputs for every method/query/seed, aggregate metrics, query-stratified summaries, variance decomposition, candidate-pool sensitivity, historical-versus-final comparisons, implementation audits, and final figures.

## Manuscript builds

From `manuscript/`:

```bash
cd manuscript
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex
```

Observed result during revision:

```text
main.pdf generated successfully
supplementary_material.pdf generated successfully
```

The main manuscript log has minor overfull table-box warnings only.

## Descriptor coverage audit

The revision artifacts in the manuscript folder report:

```text
band_gap: 10,810 / 20,372 observed
density: 20,372 / 20,372 observed
void_fraction: 0 / 20,372 observed
```

Because void fraction is unavailable for all local metadata records, porosity is excluded from active numerical objectives.
