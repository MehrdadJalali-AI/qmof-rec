#!/usr/bin/env python3
"""Build the curated v1.1 COMMT revision reproducibility archive."""
from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v1.1-COMMT-revision"
RELEASES = ROOT / "releases" / VERSION
STAGE = RELEASES / f"qmof-rec-{VERSION}"
ARCHIVE = RELEASES / f"qmof-rec-{VERSION}.tar.gz"

files = [
    "configs/final_diversity_aware_masked_protocol.json",
    "configs/reviewer_revision_requirements.txt",
    "scripts/run_final_diversity_aware_masked_protocol.py",
    "scripts/run_reviewer_revision.py",
    "scripts/verify_config_metadata_v2.py",
    "scripts/build_release_v1_1.py",
    "backend/vector_db/metadata.json",
    "backend/app/evaluation/benchmark_queries.json",
    "backend/app/recommendation/objective_utils.py",
    "backend/tests/test_missing_data_masks.py",
]

artifact_roots = [
    ROOT / "artifacts/final_diversity_aware_masked_protocol",
    ROOT / "artifacts/reviewer_revision",
    ROOT / "artifacts/presubmission_v2",
]

if STAGE.exists():
    shutil.rmtree(STAGE)
STAGE.mkdir(parents=True)

for relative in files:
    source = ROOT / relative
    assert source.is_file(), source
    target = STAGE / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

for source_root in artifact_roots:
    for source in source_root.rglob("*"):
        if not source.is_file():
            continue
        if source.suffix.lower() not in {".csv", ".json", ".md", ".txt"}:
            continue
        if any(part in {"before", "pdf_qa", "figures", "source_snapshots"} for part in source.parts):
            continue
        relative = source.relative_to(ROOT)
        target = STAGE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

readme = f"""# QMOF-Rec {VERSION}

This curated archive contains the authoritative final masked/diversity-aware protocol,
the reviewer-revision experiments, frozen machine-readable outputs, source metadata,
regression tests, and final consistency validation for COMMT-D-26-00255.

Environment: Python 3.9.6 with pinned packages in
`configs/reviewer_revision_requirements.txt`.

From the archive root, reproduce the original final protocol with:

```bash
python3 -m pip install -r configs/reviewer_revision_requirements.txt
python3 -m pytest -q backend/tests/test_missing_data_masks.py
python3 scripts/run_final_diversity_aware_masked_protocol.py \\
  --config configs/final_diversity_aware_masked_protocol.json
```

The reviewer extension runner is included for exact inspection and reproduction:

```bash
python3 scripts/run_reviewer_revision.py
```

That extension performs the 1,750-run joint sensitivity grid, matched top-5 MMR,
differential-evolution comparator, true no-diversity ablation, runtime scaling, and
descriptor-level screening checks. Running it rewrites `artifacts/reviewer_revision`;
compare generated files to the included SHA-256 manifest.

The configuration metadata correction adds the eighth formula-coordinate name only.
`artifacts/presubmission_v2/configuration_metadata_validation.json` records 5,000
identical vector/mask checks, 50 identical ordered top-5 LEA lists, passing regression
tests, and unchanged frozen CSV hashes.

No trained GraphSAGE/GAT model, independent LLM-quality benchmark, adsorption
validation, experimental validation, or new DFT validation is part of this release.
"""
(STAGE / "README.md").write_text(readme)

entries = []
for path in sorted(p for p in STAGE.rglob("*") if p.is_file() and p.name != "MANIFEST.sha256"):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    entries.append((path.relative_to(STAGE).as_posix(), digest, path.stat().st_size))
(STAGE / "MANIFEST.sha256").write_text("".join(f"{digest}  {path}\n" for path, digest, _ in entries))
(STAGE / "release_metadata.json").write_text(json.dumps({
    "version": VERSION,
    "manuscript_id": "COMMT-D-26-00255",
    "baseline_commit": "10082124cf81a90ce40b4bd6306862416a46d2e6",
    "files": len(entries),
    "uncompressed_bytes": sum(size for _, _, size in entries),
    "doi": None,
    "publication_status": "local archive prepared; permanent URL pending",
}, indent=2) + "\n")

with tarfile.open(ARCHIVE, "w:gz", format=tarfile.PAX_FORMAT) as archive:
    archive.add(STAGE, arcname=STAGE.name, recursive=True)
shutil.rmtree(STAGE)

archive_hash = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
(RELEASES / "SHA256SUMS").write_text(f"{archive_hash}  {ARCHIVE.name}\n")
(RELEASES / "RELEASE_NOTES.md").write_text(f"""# {VERSION}

Reproducibility release for the COMMT-D-26-00255 revision. It freezes the reproduced
primary results and adds complete scenario results, coefficient sensitivity, the true
no-diversity ablation, matched top-5 runtime/scalability, a scoped differential-evolution
comparator, descriptor screening checks, tests, source hashes, and exact commands.

This local package is ready for publication. A permanent GitHub release URL or DOI must
be added only after the tag and archive have been uploaded successfully.
""")
(RELEASES / "PUBLISH_COMMANDS.md").write_text(f"""# Manual publication commands

Run after authenticating GitHub CLI for `MehrdadJalali-AI/qmof-rec`:

```bash
git push origin {VERSION}
gh release create {VERSION} \\
  releases/{VERSION}/{ARCHIVE.name} \\
  releases/{VERSION}/SHA256SUMS \\
  --repo MehrdadJalali-AI/qmof-rec \\
  --verify-tag \\
  --title \"QMOF-Rec {VERSION}\" \\
  --notes-file releases/{VERSION}/RELEASE_NOTES.md
```

Expected release URL after successful publication:
`https://github.com/MehrdadJalali-AI/qmof-rec/releases/tag/{VERSION}`
""")
print(json.dumps({"archive": str(ARCHIVE), "sha256": archive_hash, "files": len(entries)}, indent=2))
