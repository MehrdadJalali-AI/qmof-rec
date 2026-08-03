# QMOF-Rec Final Submission Checklist

## Submission Files

- Main manuscript: `manuscript/main_submission_final_v2.pdf`
- Supplementary material: `manuscript/supplementary_material_submission_final_v2.pdf`
- Catalog coverage data: `catalog_coverage.csv`
- Query-block diversity data: `lea_vs_weightedsum_query_block_diversity.csv`
- Revision changelog: `REVISION_CHANGELOG.md`

## Abstract And Keywords

- Abstract word count: 249 words.
- Final keywords: QMOF; metal--organic frameworks; materials recommendation; multi-objective optimization; Lotus Effect Algorithm; graph neural networks; materials informatics
- Keyword count: 7.

## Supplementary Tables

- Catalog coverage is reported in Supplementary Table S6.
- Query-block LEA--WeightedSum hybrid material diversity differences are reported in Supplementary Table S7.

## Catalog Coverage Values

Catalog coverage is defined as the union of unique recommended QMOF records across five query scenarios and ten seeds, divided by the full catalog size of 20,372 records. This is distinct from Unique@K.

| Method | Unique recommended QMOF records | Catalog coverage |
| --- | ---: | ---: |
| WeightedSum | 16 | 0.000785 |
| LEA baseline | 32 | 0.001571 |
| MMR | 34 | 0.001669 |
| ParetoCrowding | 50 | 0.002454 |
| SemanticOnly | 163 | 0.008001 |
| Random | 236 | 0.011585 |

## Query-Blocked Diversity Summary

LEA--WeightedSum hybrid material diversity differences across the five query blocks:

| Query scenario | Difference |
| --- | ---: |
| CO2 adsorption | 0.0125 |
| Photocatalysis | 0.0000 |
| Lightweight storage | 0.0028 |
| Balanced discovery | 0.0029 |
| Insulating frameworks | 0.0001 |

Summary statistics: mean 0.0037; median 0.0028; SD 0.0051; min 0.0000; max 0.0125.

## Table 4 Formatting

- Rel@5 tied best values are bold for WeightedSum, LEA, TOPSIS, and MMR; ParetoCrowding is underlined as second-best.
- NDCG@5 tied best values are bold for WeightedSum, LEA, TOPSIS, and MMR; ParetoCrowding is underlined as second-best.
- Diversity best value is bold for ParetoCrowding; MMR is underlined as second-best.
- Hypervolume proxy best value is bold for MMR; LEA is underlined as second-best.
- Runtime best value is bold for SemanticOnly; WeightedSum and Random are both underlined as tied second-best.

## Compile And Visual QA

- Main manuscript compiled successfully to 38 pages.
- Supplementary material compiled successfully to 13 pages.
- Cross-references compile without undefined-reference or rerun warnings.
- Rendered QA pages checked: main abstract/keywords, Table 4, Table 7, statistical analysis, conclusion pages, and supplementary S6/S7 pages.
- Remaining LaTeX messages are minor typography warnings from dense tables/long inline paths; no broken references or page-breaking failures were found.

## Ready Files

- `manuscript/main_submission_final_v2.pdf`
- `manuscript/supplementary_material_submission_final_v2.pdf`
- `catalog_coverage.csv`
- `lea_vs_weightedsum_query_block_diversity.csv`
- `FINAL_SUBMISSION_CHECKLIST.md`
- `REVISION_CHANGELOG.md`
