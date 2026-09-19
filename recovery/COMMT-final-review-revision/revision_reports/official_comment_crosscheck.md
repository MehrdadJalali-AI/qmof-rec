# Official reviewer-comment cross-check — COMMT-D-26-00255

Source: `ReviewComments/COMMT-D-26-00255-reviews.pdf`. Page locations refer to the
clean recovered manuscript unless identified as supplementary pages.

| Reviewer comment | Final manuscript evidence | Final experiment/artifact | Response paragraph | Status |
|---|---|---|---|---|
| R1.1 Clarify novelty | System-level incomplete-metadata screening formulation and four contributions, Section 1, p. 1; scoped conclusion, Section 23, p. 29 | Reproduction and component audits | Reviewer 1, Comment 1 | RESOLVED |
| R1.2 Demonstrate LEA and stronger optimizer comparison | Corrected Table 4, p. 22; Discussion, p. 28 | `additional_methods.csv`; DE diagnostics; matched MMR top-5 validation | Reviewer 1, Comment 2 | RESOLVED |
| R1.3 Practical usefulness / external validation | Descriptor-level screening, Section 19, p. 27; limitations, Section 21, p. 29 | `screening.csv`; Supplementary Table S5 | Reviewer 1, Comment 3 | RESOLVED WITH EXPLICIT VALIDATION LIMITATION |
| R1.4 Distinguish graph proxies from atomistic structure | Sections 8–9, p. 17; Table 6, p. 24; Figure 1, p. 9 | Executable proxy formulas and repository implementation audit | Reviewer 1, Comment 4 | RESOLVED |
| R1.5 Clarify LLM/RAG role | Auxiliary explanation audit, Section 18 and Table 9, p. 27 | Deterministic template routine and direct-assignment audit | Reviewer 1, Comment 5 | RESOLVED |
| R1.6 Add modern AI/optimization baselines | DE comparator in Table 4; learned-representation limitation in Sections 20–21 | `additional_methods.csv`; `de_diagnostics.csv` | Reviewer 1, Comment 6 | EXPLAINED: stronger optimizer added; trained GNN/transformer comparison remains unavailable and is not fabricated |
| R1.7 Component ablations | Section 16 and Table 7, p. 25; coefficient sensitivity, Section 17 | `ablations.csv`; `sensitivity.csv` | Reviewer 1, Comment 7 | RESOLVED |
| R1.8 Refine discovery terminology | Candidate-screening title, abstract, Sections 1 and 23; balanced-screening labels | Terminology audit in `final_consistency_audit_v2.md` | Reviewer 1, Comment 8 | RESOLVED |
| R1.9 Runtime and scalability | Figure 4, p. 23; Section 19, p. 27 | `runtime_scaling.csv`; 50-case exact MMR top-5 validation | Reviewer 1, Comment 9 | RESOLVED |
| R1.10 Organization and contribution statements | One-paragraph abstract and four-item contribution list, pp. 1–2 | Source/PDF structure audit | Reviewer 1, Comment 10 | RESOLVED |
| R3.1 Remove LEA core-novelty overclaim | Section 1, p. 1; Conclusion, p. 29 | Reproduced method ordering | Reviewer 3, Response issue 1 | RESOLVED |
| R3.2 Define aligned Rel@K/NDCG and rel_r | Section 13.2, p. 20 explicitly defines `rel_r = R(m_(r),q)` and aligned IDCG | `metrics_per_query_seed.csv`; runner metric implementation | Reviewer 3, Response issue 2 | RESOLVED |
| R3.3 Correct diversity ordering | Table 4, p. 22; Supplementary Table S1 | `aggregate_extended.csv`; `per_scenario_extended.csv` | Reviewer 3, Response issue 3 | RESOLVED |
| R3.4 Correct identical original ablations | Gamma-only history separated from true no-diversity, Table 7, p. 25 | `ablations.csv` | Reviewer 3, Response issue 4 | RESOLVED |
| R3.5 Show per-scenario concentration | Section 17, p. 25; Supplementary Table S1 | `per_scenario_extended.csv` | Reviewer 3, Response issue 5 | RESOLVED |
| R3.6 Reassess middle-ground/runtime interpretation | Table 4 and Figure 4; Discussion explicitly withdraws runtime rationale | `validation.csv`; `runtime_scaling.csv` | Reviewer 3, Response issue 6 | RESOLVED WITH CORRECTION: matched top-5 MMR is faster than LEA |
| R3.7 Gamma sensitivity | Table 8 and Figure 5, p. 26; Supplementary Table S2 | `sensitivity.csv`, 1,750 runs | Reviewer 3, Response issue 7 | RESOLVED |
| R3.8 Redundancy-penalty sensitivity | Joint gamma/lambda Figure 5; Supplementary Table S2 | `sensitivity.csv`, 35 settings × 50 pools | Reviewer 3, Response issue 8 | RESOLVED |
| R3.9 Remove Table 4/Table 7 duplication | Table 4 contains principal methods; Table 7 contains component diagnostics with LEA reference only | Table-generation audit | Reviewer 3, Response issue 9 | RESOLVED |

All ten Reviewer 1 comments and every substantive element of Reviewer 3’s complete
technical comment are answered. The lack of a trained learned-representation comparator
and independent experimental validation is stated as a limitation rather than falsely
reported as completed evidence.
