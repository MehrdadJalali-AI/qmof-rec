#!/usr/bin/env python3
"""Check that two protocol runs produced the same rankings and metrics.

Plain file hashes do not work here because runtime columns change on every
run. This script compares every CSV in two artifact folders while ignoring
timing values, and exits non-zero on any other difference.

Usage:
    python3 scripts/check_ranking_invariance.py BASELINE_DIR NEW_DIR
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Folders and columns that legitimately differ between runs or were added by
# QMOF-Audit Phase A (labelling only, no effect on rankings).
IGNORED_DIRS = {"execution_traces", "figures"}
ALLOWED_NEW_COLUMNS = {"scoring_note"}


def timing_column(column: str) -> bool:
    return "runtime" in column or column.endswith("time_ms")


def timing_row(row: dict[str, str]) -> bool:
    # Long-format tables store the metric name in a column, e.g. metric=runtime_ms.
    return any("runtime" in str(row.get(key, "")) for key in ("metric", "measure"))


def load(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def csv_files(root: Path) -> set[Path]:
    return {
        p.relative_to(root) for p in root.rglob("*.csv")
        if not (set(p.relative_to(root).parts) & IGNORED_DIRS)
    }


def compare(base: Path, new: Path) -> list[str]:
    problems: list[str] = []
    base_files, new_files = csv_files(base), csv_files(new)
    for missing in sorted(base_files - new_files):
        problems.append(f"missing in new run: {missing}")
    checked = 0
    for rel in sorted(base_files & new_files):
        b_cols, b_rows = load(base / rel)
        n_cols, n_rows = load(new / rel)
        extra = set(n_cols) - set(b_cols) - ALLOWED_NEW_COLUMNS
        lost = set(b_cols) - set(n_cols)
        if extra or lost:
            problems.append(f"{rel}: column mismatch, extra {sorted(extra)}, missing {sorted(lost)}")
            continue
        if len(b_rows) != len(n_rows):
            problems.append(f"{rel}: {len(b_rows)} vs {len(n_rows)} rows")
            continue
        cols = [c for c in b_cols if not timing_column(c)]
        for i, (b, n) in enumerate(zip(b_rows, n_rows)):
            if timing_row(b) and timing_row(n):
                continue
            diff = [c for c in cols if b[c] != n[c]]
            if diff:
                problems.append(f"{rel} row {i}: differs in {diff[:5]}")
                break
        checked += 1
    print(f"compared {checked} CSV files")
    return problems


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    problems = compare(Path(sys.argv[1]), Path(sys.argv[2]))
    if problems:
        print("NOT INVARIANT")
        for p in problems:
            print(" -", p)
        return 1
    print("OK: rankings, candidate pools and metrics are identical (timing values ignored)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
