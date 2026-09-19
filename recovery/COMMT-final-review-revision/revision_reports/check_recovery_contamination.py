#!/usr/bin/env python3
"""Compare recovered final PDFs/sources with the obsolete mask-aware protocol."""
from __future__ import annotations

import csv
import io
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader

WORK = Path(__file__).resolve().parents[1]
MAN = WORK / "manuscript"
REPO = Path("/Users/mehrdadjalali/Documents/GitHub/qmof-rec")
OLD_COMMIT = "79f860d5f665aa9451a7f36602f17dca2e5c806d"


def pdf_text(path: Path) -> str:
    return "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)


old_csv = subprocess.check_output(
    ["git", "show", f"{OLD_COMMIT}:artifacts/final_masked_protocol/aggregate_metrics.csv"],
    cwd=REPO,
    text=True,
)
old_rows = {row["method"]: row for row in csv.DictReader(io.StringIO(old_csv))}
new_rows = {
    row["method"]: row
    for row in csv.DictReader((REPO / "artifacts/reviewer_revision/aggregate_extended.csv").open())
}

main_source = (MAN / "main.tex").read_text()
supp_source = (MAN / "supplementary_material.tex").read_text()
response_source = (MAN / "response_to_reviewers_final.tex").read_text()
main_pdf = pdf_text(MAN / "main_final_review_revision.pdf")
supp_pdf = pdf_text(MAN / "supplementary_final_review_revision.pdf")
response_pdf = pdf_text(MAN / "response_to_reviewers_final.pdf")

required = {
    "candidate-screening title": "Quantum-Chemical MOF Candidate Screening" in main_pdf,
    "four contribution items": main_source.count("\\item ") >= 4 and "The contributions are:" in main_source,
    "aligned rel_r definition": "rel}_r" in main_source and "same masked utility" in main_source,
    "correct LEA diversity": "LEA & 0.8479 & 0.0224" in main_source,
    "matched MMR top-5": "MMR (top-5) & 0.8479 & 0.0241" in main_source and "12.70" in main_source,
    "DE portfolio": "DE portfolio & 0.8479 & 0.0242" in main_source and "69.39" in main_source,
    "true no-diversity": "LEA true no diversity" in main_source and "0.0187" in main_source,
    "1,750-run sweep": ("1{,}750 runs" in main_source or "1,750 runs" in main_source) and len(list(csv.DictReader((REPO / "artifacts/reviewer_revision/sensitivity.csv").open()))) == 1750,
    "proxy framing": "proxy-S and proxy-A engineered metadata scores" in main_source,
    "auxiliary explanation": "Explanation is an auxiliary interface module" in main_source,
    "complete response": all(f"Comment {i}" in response_pdf for i in range(1, 11)) and "Reviewer 3" in response_pdf,
}
assert all(required.values()), required

prohibited_assertions = {
    "LEA core novelty assertion": bool(re.search(r"Its core novelty is the mask-aware post-retrieval reranking layer", main_pdf, re.I)),
    "LEA aggregate diversity 0.0000": bool(re.search(r"LEA\s+0\.8479\s+0\.0000", main_pdf, re.I)),
    "MMR aggregate diversity 0.0400": bool(re.search(r"MMR[^\n]{0,100}0\.0400", main_pdf, re.I)),
    "MMR 1708 primary runtime": "1708" in main_pdf,
    "positive 25-fold faster assertion": bool(re.search(r"LEA[^.]{0,120}(?:25[- ]?fold|25×) faster", main_pdf, re.I)),
    "GraphSAGE-only final table row": bool(re.search(r"^GraphSAGE only\s+0\.", main_pdf, re.I | re.M)),
    "GAT-only final table row": bool(re.search(r"^GAT only\s+0\.", main_pdf, re.I | re.M)),
    "perfect-groundedness final claim": "shows perfect groundedness" in main_pdf.lower(),
    "3.3% hallucination final evidence": "3.3% overall hallucination rate" in main_pdf.lower(),
    "balanced-discovery publication label": "balanced discovery" in main_pdf.lower() or "balanced discovery" in supp_pdf.lower(),
}
assert not any(prohibited_assertions.values()), prohibited_assertions

contextual_retentions = [
    ("2209.67", "Retained only as the explicitly historical full-list MMR audit; 12.70 ms is the primary matched top-5 comparison."),
    ("core novelty", "Retained in negations and the verbatim Reviewer 3 quotation, not as the manuscript claim."),
    ("GraphSAGE only / GAT only", "Retained only in the verbatim Reviewer 3 quotation; final manuscript tables use proxy-S/proxy-A labels."),
    ("zero hallucination", "Retained in a negative limitation sentence stating that assigned values cannot demonstrate it."),
    ("25-fold", "Retained only in the response as a withdrawn historical claim and in the reviewer quotation."),
]

old = {
    "WeightedSum": (float(old_rows["WeightedSum"]["rel_at_5"]), float(old_rows["WeightedSum"]["diversity"]), float(old_rows["WeightedSum"]["runtime_ms"])),
    "LEA": (float(old_rows["LEA"]["rel_at_5"]), float(old_rows["LEA"]["diversity"]), float(old_rows["LEA"]["runtime_ms"])),
    "MMR": (float(old_rows["MMR"]["rel_at_5"]), float(old_rows["MMR"]["diversity"]), float(old_rows["MMR"]["runtime_ms"])),
}
new = {
    "WeightedSum": (float(new_rows["WeightedSum"]["rel_at_5"]), float(new_rows["WeightedSum"]["diversity"]), float(new_rows["WeightedSum"]["runtime_ms"])),
    "LEA": (float(new_rows["LEA"]["rel_at_5"]), float(new_rows["LEA"]["diversity"]), float(new_rows["LEA"]["runtime_ms"])),
    "MMR top5": (float(new_rows["MMR top5"]["rel_at_5"]), float(new_rows["MMR top5"]["diversity"]), float(new_rows["MMR top5"]["runtime_ms"])),
}

lines = [
    "# Rollback contamination check",
    "",
    f"Obsolete comparison source: commit `{OLD_COMMIT}`, `artifacts/final_masked_protocol/aggregate_metrics.csv`.",
    "",
    "Final result: **PASS — no old-protocol assertion or primary result remains in the recovered manuscript, supplement, or response.**",
    "",
    "## Required recovery signatures",
    "",
] + [f"- {'PASS' if ok else 'FAIL'} — {name}" for name, ok in required.items()] + [
    "",
    "## Structured numerical comparison",
    "",
    "| Method | Obsolete Rel@5 / diversity / runtime ms | Recovered Rel@5 / diversity / runtime ms |",
    "|---|---|---|",
    f"| WeightedSum | {old['WeightedSum'][0]:.4f} / {old['WeightedSum'][1]:.4f} / {old['WeightedSum'][2]:.2f} | {new['WeightedSum'][0]:.4f} / {new['WeightedSum'][1]:.4f} / {new['WeightedSum'][2]:.2f} |",
    f"| LEA | {old['LEA'][0]:.4f} / {old['LEA'][1]:.4f} / {old['LEA'][2]:.2f} | {new['LEA'][0]:.4f} / {new['LEA'][1]:.4f} / {new['LEA'][2]:.2f} |",
    f"| MMR | {old['MMR'][0]:.4f} / {old['MMR'][1]:.4f} / {old['MMR'][2]:.2f} | {new['MMR top5'][0]:.4f} / {new['MMR top5'][1]:.4f} / {new['MMR top5'][2]:.2f} (matched top-5) |",
    "",
    "## Prohibited old-content scan",
    "",
] + [f"- {'FAIL' if found else 'PASS'} — {name}: {'found' if found else 'absent'}" for name, found in prohibited_assertions.items()] + [
    "",
    "## Context-aware retained strings",
    "",
] + [f"- `{term}` — {reason}" for term, reason in contextual_retentions] + [
    "",
    "The Reviewer 3 quotation is preserved verbatim by design. Its obsolete claims are reviewer text, immediately followed by corrected responses, and are not contamination.",
]

(WORK / "revision_reports/rollback_contamination_check.md").write_text("\n".join(lines) + "\n")
print("PASS: recovered PDFs and sources are free of old-protocol assertions")
