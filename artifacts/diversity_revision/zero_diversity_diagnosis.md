# Zero-Diversity Diagnosis

The zero masked-diversity result in `artifacts/final_masked_protocol` is a representation limitation caused by binned objective scores, not by identical raw materials and not by a pairwise-distance implementation bug.

`property_scorer.score_band_gap` maps every observed band gap in the interval 1.0--3.5 eV to the same score of 1.0. `property_scorer.score_density` maps every density in 1.0--2.0 g/cm3 to the same score of 0.7. When no measured stability field is present, `hybrid_ranker._compute_stability_score` uses the density score as the stability proxy. The deterministic semantic proxy is also tied within several high-ranked query/application buckets.

For the CO2 Table 3 candidates, the raw density and band-gap values differ, but all five transform to the same active objective vector:

- qmof-c8f0292: raw density=1.602088418, raw band gap=3.494605, active vector=0.7166666666666667|1.0|0.7|0.7, final utility=0.8596077576279639
- qmof-b0a3596: raw density=1.704727415, raw band gap=3.49187, active vector=0.7166666666666667|1.0|0.7|0.7, final utility=0.8596077576279639
- qmof-c631f72: raw density=1.65313731, raw band gap=3.280036, active vector=0.7166666666666667|1.0|0.7|0.7, final utility=0.8596077576279639
- qmof-b2fddf8: raw density=1.64642024, raw band gap=2.966635, active vector=0.7166666666666667|1.0|0.7|0.7, final utility=0.8596077576279639
- qmof-26c54ef: raw density=1.504454446, raw band gap=2.825171, active vector=0.7166666666666667|1.0|0.7|0.7, final utility=0.8596077576279639

Because intra-list diversity in the previous final-masked protocol was computed over this transformed active objective vector, every pair among these tied candidates has zero distance. Pairwise distance uses full-precision arithmetic and the no-overlap fallback is not triggered for these rows; their masks are identical (`1|1|1|1`). The collapse occurs before the distance calculation, at the property-score discretization/clipping step.

The scientifically appropriate correction is to keep mask-aware relevance on the application-oriented score vector, but measure list diversity over a richer, full-precision material representation that includes continuous physical descriptors and query-independent formula/graph-derived features.
