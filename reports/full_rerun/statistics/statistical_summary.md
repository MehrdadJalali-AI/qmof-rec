# Statistical Tests

Input: `reports/full_rerun/ablation/ablation_metrics.csv`

Metric: `mean_relevance`

| test                 | comparison                                               | metric         |   n_pairs |   statistic |     p_value |   mean_first |   mean_second |   paired_cohens_d | status   | reason   |
|:---------------------|:---------------------------------------------------------|:---------------|----------:|------------:|------------:|-------------:|--------------:|------------------:|:---------|:---------|
| wilcoxon_signed_rank | LEA baseline vs WeightedSum                              | mean_relevance |        50 |       0     | 3.4983e-07  |     0.693936 |      0.696091 |         -0.777704 | executed |          |
| wilcoxon_signed_rank | LEA baseline vs MMR                                      | mean_relevance |        50 |     138     | 1.73945e-07 |     0.693936 |      0.688482 |          0.957356 | executed |          |
| wilcoxon_signed_rank | LEA baseline vs RandomRepeated                           | mean_relevance |        50 |      11     | 9.76996e-14 |     0.693936 |      0.682672 |          1.41203  | executed |          |
| wilcoxon_signed_rank | LEA baseline vs SemanticOnly                             | mean_relevance |        50 |       7     | 3.37508e-14 |     0.693936 |      0.681782 |          1.44667  | executed |          |
| friedman             | SemanticOnly;WeightedSum;MMR;RandomRepeated;LEA baseline | mean_relevance |        50 |     173.626 | 1.7424e-36  |   nan        |    nan        |        nan        | executed |          |
