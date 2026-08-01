# QMOF-Rec Reviewer Revision Changelog

Branch: `reviewer-arnd-revision`

## Descriptor handling

- Added explicit descriptor availability utilities in `backend/app/recommendation/objective_utils.py`.
- Changed feature extraction so missing values are represented by masks rather than being silently treated as observed zeros.
- Removed void fraction and porosity from active numerical objectives because the local metadata audit found 0/20,372 observed void-fraction values.
- Updated weighted scoring, similarity, novelty, and LEA remapping to use masked objectives and jointly observed dimensions.

## Ranking and recommendation behavior

- Updated dynamic query weights to exclude a `porosity` weight for CO2/gas-storage queries.
- Updated hybrid ranking to report `porosity_score = None` and a void-fraction availability note instead of scoring unavailable porosity.
- Updated explanatory text so unavailable void fraction is surfaced as a limitation and not used as a numerical rationale.
- Added focused regression tests for missing descriptors, genuine zeros, dynamic weights, hybrid ranking, masked similarity, and LEA porosity exclusion.

## Vector/RAG/frontend behavior

- Updated vector-index serialization so unavailable void fraction is written as unavailable metadata rather than an empty numeric-looking value.
- Kept LLM guardrails requiring limitation statements for porosity/adsorption queries.
- Removed void-fraction plotting from dashboard analytics and changed the material card to display unavailable void fraction explicitly.

## Manuscript and supplement

- Revised the manuscript to describe QMOF-Rec as a hybrid scientific recommender with a strong content-based focus.
- Added descriptor masks to the formalism and algorithms.
- Regenerated the active-objective radar figure without a porosity axis.
- Added descriptor coverage and repeated-seed caveats to the supplementary material.
- Added reviewer-requested Seko et al. and Qu et al. references, plus a narrow KadiAssistant comparison.
- Added a generative-AI-use declaration.
