# QMOF-Rec Final Revision Change Log

## Manuscript files

- `main.tex`: added retrieval-versus-reranking missingness explanation, moved availability-mask definitions into the general formulation, changed relevance/diversity/remapping equations to masked forms, corrected LEA mutation/self-cleaning prose to match the current implementation, clarified Table 4 versus Table 7 protocol differences, added query/seed dependence caveats, improved table captions with best/second-best guidance, corrected KadiAssistant metadata, and reduced instruction-like prose.
- `supplementary_material.tex`: added descriptor coverage, retrieval missingness, masked scoring, query-stratified repeated-seed results, variance decomposition, candidate-pool-size sensitivity, LEA-no-diversity metric identity status, missing-data ablation status, and all-records-versus-selected active-descriptor Figure S3.
- `references.bib`: added Seko et al., Qu et al., and corrected KadiAssistant author/title metadata.
- Final technical audit: changed the abstract and result captions to identify the reported numerical values as saved offline/historical artifacts rather than a new mask-aware rerun; replaced the balance equation with the observed-objective evenness definition; distinguished masked cosine similarity from the masked distance used by LEA diversity/remapping; and changed the statistical-analysis paragraph to a query-blocked descriptive interpretation.
- Final supplementary audit: revised candidate-pool-size wording so pool size 100 is described as the predefined main setting for consistency, not as an optimized setting; renamed Figure S3 and captioned it as an observed physical descriptor comparison using only band gap and density.
- Final pre-submission audit: corrected the Seko citation context, defined graph convolutional network (GCN) at first use, changed the retrieval formulation from cosine similarity to FAISS L2 distance to match the live vector store, added an explicit archived-results versus post-review mask-aware-code protocol statement before the results section, changed the Table 7 LEA baseline note to the historical configurable LEA parameters, and improved the abstract missing-descriptor test wording.
- Length reduction: moved Algorithms 1--3 and the detailed RAG/LLM rubric and hallucination-flag definitions from the main manuscript to the supplementary material. The main manuscript build decreased from 39 pages to 37 pages.
- Final polish: clarified that Figures 4--6 summarize the archived evaluation while Figure 7 illustrates the revised active objective representation, defined GAT in the abstract, defined MAE/RMSE/$R^2$/Spearman before Table 6, made the Table 4 TOPSIS hypervolume entry math-bold, changed Contribution 5 to query-blocked statistical robustness analyses, and revised the Table 5 caption to refer to the saved offline evaluation artifact.
- Final presentation cleanup: split the crowded Table 7 NDCG/Diversity headers over two lines, removed the internal ``Table B'' label from the RAG/LLM results caption, and changed the Table 3 caption to refer to the saved offline QMOF-Rec evaluation artifact.

## Figures and artifacts

- `figures/figure_6_objective_radar.*`: regenerated without the unavailable porosity axis.
- `figures/figure_s3_all_vs_selected_active_descriptors.*`: added and then renamed all-records-versus-selected observed physical descriptor comparison.
- `reviewer_revision_artifacts/query_stratified_seed_results.csv`: added query-stratified repeated-seed results.
- `reviewer_revision_artifacts/variance_decomposition.csv`: added direct between-query versus within-query seed variance decomposition.
- `reviewer_revision_artifacts/candidate_pool_size_summary.csv`: added available pool-size sensitivity summary for pool sizes 50, 100, and 200.
- `reviewer_revision_artifacts/lea_no_diversity_metric_identity.csv`: added metric-level LEA-no-diversity versus WeightedSum identity check.
- `reviewer_revision_artifacts/all_vs_selected_objective_summary.csv`: added source values for Figure S3.
- `protocol_audit.csv`: added a result-by-result protocol map covering the Abstract, Table 4, Table 7, statistical summaries, candidate-pool sensitivity, LEA-no-diversity check, Figure S3, and current repository mask-aware tests.
- `final_configuration.json`: added a machine-readable summary of the final reporting choice and protocol boundaries.
- `RESPONSE_TO_COMMENTS.docx`: updated response language for protocol preservation, balance-score correction, candidate-pool sensitivity, Figure S3, AI-use disclosure, and the final 8-test verification result.
- `supplementary_material.tex`: added the detailed computational workflow pseudocode and the RAG/LLM scoring-rubric and hallucination-flag tables moved out of the main manuscript.

## Repository files

- Commit `beb19d7e`: implemented descriptor availability masks, removed void fraction/porosity from active numerical ranking, added tests, and updated frontend displays.
- Additional final-pass working-tree updates: README reproducibility notes and code comments documenting masked-distance fallback behavior.
- Final technical-audit working-tree updates: implemented `masked_balance_score` as observed-objective evenness, switched LEA fitness to use it, added focused regression tests for masked distance and balance, and updated clean-clone reproduction commands.
- Commit `f8b52c00`: committed the final technical-audit repository updates.

## Verification

- `PYTHONPATH=backend pytest -q backend/tests/test_missing_data_masks.py` passed; final technical-audit rerun passed with 8 tests.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` passed.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex` passed.
- Final pre-submission rebuild passed after citation/protocol/retrieval/length edits.
- Final polish rebuild passed after Figure 7, abstract, Table 4, Table 5, Table 6, and contribution wording edits.
- Final presentation-cleanup rebuild passed after the Table 3, Table 7, and Table 8 caption/header edits.
- Duplicate manuscript PDF variants and LaTeX build byproducts were removed after successful compilation, leaving `main.tex`/`main.pdf` and `supplementary_material.tex`/`supplementary_material.pdf` as the manuscript outputs.

## Notes

- A full missing-data ablation was not added because the saved repeated-seed metrics do not include top-K identifiers needed to quantify changed recommendation lists, and a full rerun under the revised masking protocol would create a new primary-results protocol.
- Historical numerical results were preserved transparently rather than replaced with unsupported new numbers.
- The saved repeated-seed artifacts support metric-level identity between LEA no diversity and WeightedSum for all 50 query/seed rows, but they do not support top-K ID/order verification.
