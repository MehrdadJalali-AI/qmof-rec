# QMOF-Rec manuscript package

This folder contains the send-to-Arnd manuscript package.

- `main.tex` / `main.pdf`: main manuscript.
- `supplementary_material.tex` / `supplementary_material.pdf`: supplementary material.
- `RESPONSE_TO_COMMENTS.docx` / `RESPONSE_TO_COMMENTS.pdf`: response package.
- `protocol_audit.csv` and `final_configuration.json`: protocol-boundary audit files documenting archived numerical results versus post-review mask-aware code updates.
- `figures/`, `lea_evaluation/`, and `reviewer_revision_artifacts/`: figures and saved evaluation/revision artifacts used by the manuscript.

Build from this folder with:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex
```
