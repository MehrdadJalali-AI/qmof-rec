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
8 passed in 0.33s
```

## Manuscript builds

From `/Users/mehrdadjalali/Documents/SRH_Research/QMOF-Rec/QMOF_Rec`:

```bash
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
