"""Execution traces for QMOF-Audit (Phase A).

For every recommended candidate this module records, per property, how the
value used by QMOF-Rec was produced: the raw value, what kind of evidence it
is, whether it was available, which transformation turned it into a score,
which fallback rule (if any) was applied, and whether the result entered the
ranking. QMOF-Audit turns these records into a PROV-O knowledge graph.

The logger is read-only with respect to ranking: it never changes scores,
ranks or candidate pools.

Evidence types (kept separate from availability, as in the expose schema):
    computed         value from a QMOF DFT/structure calculation
    heuristic_proxy  value derived by a hand-written rule standing in for
                     a property that was not calculated
    experimental     measured value (none in the current metadata)
    predicted        model prediction (not used in the current protocol)
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

from app.recommendation.hybrid_ranker import (
    STABILITY_DENSITY_PROXY,
    STABILITY_MEASURED,
    STABILITY_MISSING,
    hybrid_ranker,
)
from app.recommendation.objective_utils import is_observed
from app.recommendation.property_scorer import property_scorer

TRACE_SCHEMA_VERSION = "qmof-rec-trace/1"

BAND_GAP_SOURCE = "qmof:outputs.hse06.bandgap"
DENSITY_SOURCE = "qmof:info.density"
VOID_FRACTION_SOURCE = "qmof:info.void_fraction"


def code_version(root: Path | None = None) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root or Path(__file__).resolve().parents[3],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unavailable"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _raw(value: Any):
    return float(value) if is_observed(value) else None


def _record(context: dict[str, Any], material: dict[str, Any], **fields) -> dict[str, Any]:
    record = {
        "trace_schema": TRACE_SCHEMA_VERSION,
        **context,
        "qmof_id": material.get("qmof_id"),
        "formula": material.get("formula"),
    }
    record.update(fields)
    return record


def trace_material(
    material: dict[str, Any],
    context: dict[str, Any],
    extra_records: Iterable[dict[str, Any]] = (),
    overrides: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return trace records for one candidate.

    material: raw QMOF record (qmof_id, formula, band_gap, density,
        void_fraction, optional stability).
    context: run-level fields copied into every record (run_id, query_id,
        seed, method, rank, code_version, config_sha256, ...).
    extra_records: protocol-specific records built with ``proxy_record``.
    overrides: per-property fields that replace the defaults, e.g. when a
        scenario rule rescores band gap. Keys are property names.
    """

    overrides = overrides or {}
    band_gap = material.get("band_gap")
    density = material.get("density")
    void_fraction = material.get("void_fraction")

    bg_score, bg_status = property_scorer.score_band_gap_with_status(band_gap)
    d_score, d_status = property_scorer.score_density_with_status(density)
    bg_available = is_observed(band_gap)
    d_available = is_observed(density)

    stab_score, stab_available, stab_source = hybrid_ranker._compute_stability_score_with_source(
        material=material,
        density_score=d_score if d_available else 0.0,
        density_available=d_available,
    )

    base = {
        "band_gap": dict(
            property="band_gap",
            raw_value=_raw(band_gap),
            unit="eV",
            evidence_type="computed",
            evidence_source=BAND_GAP_SOURCE,
            method_note="HSE06 band gap; missing means no HSE06 value in this snapshot",
            availability="observed" if bg_available else "missing",
            transformation=property_scorer.BAND_GAP_RULE,
            inputs=["band_gap"],
            fallback_policy=None if bg_available else "score_set_to_0.0_then_masked",
            output_score=bg_score if bg_available else 0.0,
            used_in_ranking=bg_available,
            used_in_diversity=bg_available,
            status=bg_status,
        ),
        "density": dict(
            property="density",
            raw_value=_raw(density),
            unit="g/cm3",
            evidence_type="computed",
            evidence_source=DENSITY_SOURCE,
            method_note="density of the QMOF relaxed structure",
            availability="observed" if d_available else "missing",
            transformation=property_scorer.DENSITY_RULE,
            inputs=["density"],
            fallback_policy=None if d_available else "score_set_to_0.0_then_masked",
            output_score=d_score if d_available else 0.0,
            used_in_ranking=d_available,
            used_in_diversity=d_available,
            status=d_status,
        ),
        "stability": dict(
            property="stability",
            raw_value=_raw(material.get("stability")),
            unit=None,
            evidence_type={
                STABILITY_MEASURED: "experimental",
                STABILITY_DENSITY_PROXY: "heuristic_proxy",
                STABILITY_MISSING: None,
            }[stab_source],
            evidence_source="record:stability" if stab_source == STABILITY_MEASURED else None,
            method_note=(
                "no stability value in metadata; score copied from the density bin"
                if stab_source == STABILITY_DENSITY_PROXY
                else None
            ),
            availability="observed" if stab_source == STABILITY_MEASURED else (
                "derived" if stab_available else "missing"
            ),
            transformation=(
                "stability_from_density_bin_v1" if stab_source == STABILITY_DENSITY_PROXY else None
            ),
            inputs=["density"] if stab_source == STABILITY_DENSITY_PROXY else ["stability"],
            fallback_policy=(
                "use_density_score" if stab_source == STABILITY_DENSITY_PROXY else (
                    "score_set_to_0.0_then_masked" if stab_source == STABILITY_MISSING else None
                )
            ),
            output_score=stab_score,
            used_in_ranking=bool(stab_available),
            used_in_diversity=False,
            status=stab_source,
        ),
        "void_fraction": dict(
            property="void_fraction",
            raw_value=_raw(void_fraction),
            unit="dimensionless",
            evidence_type="computed",
            evidence_source=VOID_FRACTION_SOURCE,
            method_note="absent for all records in the current metadata",
            availability="observed" if is_observed(void_fraction) else "missing",
            transformation=None,
            inputs=["void_fraction"],
            fallback_policy="excluded_from_ranking",
            output_score=None,
            used_in_ranking=False,
            used_in_diversity=False,
            status="excluded",
        ),
    }
    for prop, fields in overrides.items():
        base[prop].update(fields)

    records = [_record(context, material, **fields) for fields in base.values()]
    records.extend(_record(context, material, **r) for r in extra_records)
    return records


def proxy_record(
    property_name: str,
    transformation: str,
    inputs: list[str],
    output_score: float | None,
    used_in_ranking: bool,
    used_in_diversity: bool,
    fallbacks: dict[str, str] | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """A trace record for a protocol-specific heuristic proxy score."""
    fallbacks = fallbacks or {}
    return {
        "property": property_name,
        "raw_value": None,
        "unit": None,
        "evidence_type": "heuristic_proxy",
        "evidence_source": None,
        "method_note": note,
        "availability": "derived",
        "transformation": transformation,
        "inputs": inputs,
        "fallback_policy": "; ".join(f"{k}: {v}" for k, v in fallbacks.items()) or None,
        "output_score": output_score,
        "used_in_ranking": used_in_ranking,
        "used_in_diversity": used_in_diversity,
        "status": "derived_with_fallback" if fallbacks else "derived",
    }


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
            count += 1
    return count
