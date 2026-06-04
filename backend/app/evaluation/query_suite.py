from __future__ import annotations

from typing import Dict, List


QUERY_SUITE: List[Dict] = [
    {
        "query_id": "q1_co2_adsorption",
        "query": "stable porous MOFs for CO2 adsorption",
        "weights": {
            "semantic": 0.22,
            "band_gap": 0.08,
            "density": 0.15,
            "porosity": 0.32,
            "stability": 0.23,
        },
        "keywords": ["co2", "adsorption", "porous", "carbon"],
    },
    {
        "query_id": "q2_photocatalysis",
        "query": "semiconducting MOFs for photocatalysis with suitable band gap",
        "weights": {
            "semantic": 0.25,
            "band_gap": 0.42,
            "density": 0.08,
            "porosity": 0.10,
            "stability": 0.15,
        },
        "keywords": ["photocatalysis", "semiconductor", "band", "gap"],
    },
    {
        "query_id": "q3_lightweight_storage",
        "query": "lightweight low density MOFs for gas storage",
        "weights": {
            "semantic": 0.20,
            "band_gap": 0.05,
            "density": 0.38,
            "porosity": 0.25,
            "stability": 0.12,
        },
        "keywords": ["lightweight", "low", "density", "storage"],
    },
    {
        "query_id": "q4_balanced_discovery",
        "query": "balanced stable MOF candidates for general materials discovery",
        "weights": {
            "semantic": 0.25,
            "band_gap": 0.20,
            "density": 0.20,
            "porosity": 0.15,
            "stability": 0.20,
        },
        "keywords": ["stable", "mof", "materials", "discovery"],
    },
    {
        "query_id": "q5_insulating_frameworks",
        "query": "wide band gap insulating MOFs with low density",
        "weights": {
            "semantic": 0.20,
            "band_gap": 0.45,
            "density": 0.22,
            "porosity": 0.05,
            "stability": 0.08,
        },
        "keywords": ["wide", "band", "gap", "insulating"],
    },
]
