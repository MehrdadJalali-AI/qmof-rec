# Reviewer revision deliverables

Primary reproduction passed at manuscript precision. See `audit_report.md`, `revision_summary.json`, and `final_validation.json` for findings and final checks. `file_checksums.csv` records source/result/document hashes.

## Reproduce

From the authoritative repository, with Python 3.9.6 and packages in `configs/reviewer_revision_requirements.txt`:

```bash
PYTHONPATH=backend python3 -m pytest -q backend/tests/test_missing_data_masks.py
python3 scripts/run_final_diversity_aware_masked_protocol.py
python3 scripts/run_reviewer_revision.py
python3 scripts/build_reviewer_revision.py
```

The builder targets the designated manuscript workspace. Compile its three TeX documents with latexmk. Rendering QA requires Poppler, Pillow, and pypdf; the bundled runtime was used for this step.

The original final-protocol files and metadata remain unchanged. Reviewer scripts are additions. Raw sensitivity, runtime, screening, ablation, baseline, and scenario results are retained here. The pre-revision manuscript sources are preserved in `source_snapshots/`.

New files are local and uncommitted. A versioned release/archive and author review are needed before submission. No external publication was performed.
