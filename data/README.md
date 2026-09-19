# Data contract

The reproducibility workflow uses `backend/vector_db/metadata.json`. Each record is identified by `qmof_id` and may contain a chemical formula, descriptive text, density, and band gap.

The executable protocol applies these availability rules:

- density is observed for every bundled local record;
- band gap is scored only when a finite value is present;
- void fraction is unavailable and excluded from all numerical objectives and distances;
- missing physical descriptors are represented by an explicit false mask and are never treated as measured zero;
- proxy A uses a documented zero contribution for its unavailable band-gap input while preserving the physical descriptor mask in relevance and distance calculations.

The vector index and metadata bundled under `backend/vector_db/` support the application and offline evaluation. CIF structure files are optional and are not required for the benchmark.
