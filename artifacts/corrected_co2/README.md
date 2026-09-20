# Corrected CO2 token-overlap run

This artifact tree was generated from commit `9d685df34608d8e5eb18715ad1c08f9a074086d9`.

The offline semantic proxy uses exact case-folded alphanumeric tokens from metadata text. Formula strings do not contribute to query-token overlap, so a `CO2` query does not match cobalt stoichiometry such as `Co2`. The historical outputs under `artifacts/benchmark/` are preserved unchanged.

Reproduction commands are documented in `docs/REPRODUCIBILITY.md`. `benchmark/environment.txt` records the source commit and platform. `extended_evaluation/experiment_manifest.json` records package versions and optimizer settings.
