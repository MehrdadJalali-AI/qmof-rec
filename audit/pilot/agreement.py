#!/usr/bin/env python3
"""Inter-annotator agreement for the QMOF-Audit pilot set.

Compares labeller 1's draft verdicts (pilot_cases.jsonl) with labeller 2's
blind verdicts (a filled copy of pilot_blind.csv) and reports Cohen's kappa,
per-category agreement and every disagreement for adjudication.

Usage:
    python3 audit/pilot/agreement.py audit/pilot/pilot_blind_filled.csv
    python3 audit/pilot/agreement.py FILLED.csv --write-adjudication OUT.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

VERDICTS = ("supported", "contradicted", "insufficient_evidence")
ALIASES = {"insufficient": "insufficient_evidence", "insufficient evidence": "insufficient_evidence",
           "support": "supported", "contradict": "contradicted"}
HERE = Path(__file__).resolve().parent


def normalise(label: str | None) -> str | None:
    if label is None:
        return None
    label = label.strip().lower()
    label = ALIASES.get(label, label)
    if not label:
        return None
    if label not in VERDICTS:
        raise ValueError(f"unknown verdict {label!r}; use one of {VERDICTS}")
    return label


def cohen_kappa(a: list[str], b: list[str]) -> float:
    """Cohen's kappa for two raters over the same items."""
    if len(a) != len(b) or not a:
        raise ValueError("need two equal-length, non-empty label lists")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if expected == 1.0:
        return 1.0
    return (observed - expected) / (1.0 - expected)


def load(cases_path: Path, filled_path: Path) -> list[tuple[dict, str]]:
    cases = {c["case_id"]: c for c in map(json.loads, cases_path.read_text().splitlines())}
    pairs = []
    with filled_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            v2 = normalise(row.get("labeller_2_verdict"))
            if v2 is None:
                continue
            pairs.append((cases[row["case_id"]], v2))
    return pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("filled_blind_csv", type=Path)
    parser.add_argument("--cases", type=Path, default=HERE / "pilot_cases.jsonl")
    parser.add_argument("--write-adjudication", type=Path)
    args = parser.parse_args(argv)

    pairs = load(args.cases, args.filled_blind_csv)
    if not pairs:
        print("No labeller-2 verdicts found.")
        return 1
    a = [c["labeller_1_verdict"] for c, _ in pairs]
    b = [v for _, v in pairs]
    kappa = cohen_kappa(a, b)
    agree = sum(x == y for x, y in zip(a, b))
    print(f"labelled cases: {len(pairs)}   raw agreement: {agree}/{len(pairs)} = {agree / len(pairs):.2f}")
    print(f"Cohen's kappa: {kappa:.3f}")

    per_cat: dict[str, list[bool]] = defaultdict(list)
    for (case, v2) in pairs:
        per_cat[case["category"]].append(case["labeller_1_verdict"] == v2)
    for cat, hits in sorted(per_cat.items()):
        print(f"  {cat:28s} {sum(hits)}/{len(hits)}")

    disagreements = [(c, v2) for c, v2 in pairs if c["labeller_1_verdict"] != v2]
    if disagreements:
        print("\nDisagreements to adjudicate:")
        for case, v2 in disagreements:
            print(f"  {case['case_id']}: L1={case['labeller_1_verdict']}  L2={v2}  | {case['claim']}")

    if args.write_adjudication:
        with args.write_adjudication.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["case_id", "claim", "labeller_1_verdict", "labeller_2_verdict",
                             "expected_verdict", "adjudication_note"])
            for case, v2 in pairs:
                agreed = case["labeller_1_verdict"] == v2
                writer.writerow([case["case_id"], case["claim"], case["labeller_1_verdict"], v2,
                                 v2 if agreed else "", "" if agreed else "TO ADJUDICATE"])
        print(f"\nAdjudication sheet written to {args.write_adjudication}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
