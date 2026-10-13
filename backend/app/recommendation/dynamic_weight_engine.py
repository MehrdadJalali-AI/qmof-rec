"""Prespecified, deterministic application rules; no substring matching."""
import re
from app.recommendation.objective_utils import normalize_weights

BASE_WEIGHTS = {"semantic": .35, "band_gap": .25, "density": .20, "stability": .20}
RULES = {
    "co2_adsorption": {"phrases": ["co2", "carbon dioxide", "gas adsorption"], "increments": {"density": .15}},
    "photocatalysis": {"phrases": ["photocatalysis", "photocatalytic", "photocatalyst"], "increments": {"band_gap": .25}},
    "lightweight_storage": {"phrases": ["lightweight", "low density", "gas storage"], "increments": {"density": .15}},
    "balanced_screening": {"phrases": ["balanced", "multi objective"], "increments": {}},
    "insulating_frameworks": {"phrases": ["insulating", "insulator", "wide band gap", "wide gap"], "increments": {"band_gap": .25}},
    "stability": {"phrases": ["stable", "stability"], "increments": {"stability": .20}},
}

def tokens(text):
    # Preserve the chemical distinction before case normalization. Formula
    # fields are excluded separately by callers of application-text overlap.
    raw = re.findall(r"[A-Za-z0-9]+", str(text).replace("₂", "2"))
    return tuple("__cobalt_stoichiometry__" if t == "Co2" else t.casefold() for t in raw)

def has_phrase(text_tokens, phrase):
    pattern = tokens(phrase)
    return any(text_tokens[i:i+len(pattern)] == pattern for i in range(len(text_tokens)-len(pattern)+1))

class DynamicWeightEngine:
    def activated_rules(self, query):
        ts = tokens(query)
        return [name for name, rule in RULES.items() if any(has_phrase(ts, phrase) for phrase in rule["phrases"])]

    def generate_weights(self, query):
        weights = dict(BASE_WEIGHTS)
        # Each objective increment is applied at most once, even when several
        # synonymous application phrases match (e.g. CO2 gas storage).
        increments = {}
        for name in self.activated_rules(query):
            for key, value in RULES[name]["increments"].items():
                increments[key] = max(increments.get(key, 0), value)
        for key, value in increments.items():
            weights[key] += value
        return normalize_weights(weights)

dynamic_weight_engine = DynamicWeightEngine()
