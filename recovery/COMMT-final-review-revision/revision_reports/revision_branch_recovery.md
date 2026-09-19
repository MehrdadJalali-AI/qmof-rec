# Reviewer-revision branch recovery — COMMT-D-26-00255

Audit date: 19 September 2026 (Europe/Berlin)

## Recovery conclusion

The active reviewer-driven manuscript sources are the correct later revision. They are
paired with executable repository commit `39973ed4f38cc2b22ea0180f0023c751e7de14d4`
and the machine-readable results under `artifacts/reviewer_revision/`. The active
sources satisfy all fourteen recovery signatures: the candidate-screening title,
system-level novelty, one-paragraph abstract, four contributions, aligned relevance
definition, corrected aggregate values, true no-diversity ablation, 1,750-run joint
sensitivity grid, complete scenario results, matched top-five MMR timing, proxy-S/A
framing, auxiliary explanation audit, and the complete Reviewer 1/Reviewer 3 response.

The zero-diversity protocol is an earlier lineage and must not be used for the final
reviewer revision. It was introduced at commit
`79f860d5f665aa9451a7f36602f17dca2e5c806d` (`Add final mask-aware rerun package`,
3 August 2026 09:38:01 +0200) under `artifacts/final_masked_protocol/`.

## Correct latest sources

| Component | Source | Timestamp / commit | SHA-256 |
|---|---|---|---|
| Executable revision | `/Users/mehrdadjalali/Documents/GitHub/qmof-rec` | commit `39973ed4`, 19 September 2026 11:06:46 +0200 | Git object `39973ed4f38cc2b22ea0180f0023c751e7de14d4` |
| Main manuscript | `manuscript/main.tex` | 19 September 2026 10:49:38 +0200 | `42a57cf464769d049167b133ac11f6c96d96d5de8f0f6a0fd306bd95989fd682` |
| Supplement | `manuscript/supplementary_material.tex` | 19 September 2026 10:49:38 +0200 | `e02b3ceca28ca3919393cd821680367fc01853d6bdec6b7668e8a97c1e6306ea` |
| Reviewer response | `manuscript/response_to_reviewers_final.tex` | 19 September 2026 10:54:23 +0200 | `87523a09fac1f7c71a2faa73a74d4c510b2ce0084bac742d63e6d44f09a39b86` |
| Reviewer artifacts | `artifacts/reviewer_revision/` | generated 19 September 2026 | frozen hashes recorded in `artifacts/presubmission_v2/frozen_result_hashes.json` |

The recoverable intermediate snapshot at `artifacts/presubmission_v2/before/` already
contains the correct reviewer experiments and four-item framing. The active sources are
newer because they also contain the final terminology, bibliography, configuration,
availability, and reviewer-location corrections.

## Accidentally reverted / obsolete sources

| Source | Status | Evidence |
|---|---|---|
| Commit `79f860d5`, `artifacts/final_masked_protocol/` | Exact obsolete zero-diversity protocol | LEA diversity `0.0000`; MMR diversity `0.0400`; MMR runtime `1708.1197 ms`; MMR Rel@5 `0.8400`; MMR NDCG@5 `0.9871` |
| `artifacts/reviewer_revision/source_snapshots/main.tex` | Obsolete pre-reviewer-text snapshot dated 7 August 2026 | LEA-as-core-novelty statement, six contributions, graph-named current-result framing, full-list MMR presented as slowest, and perfect groundedness claim |
| `manuscript/main_submission_final_v2.pdf` and `main_submission_final_v3.pdf` | Historical PDFs, not recovery sources | contain the LEA core-novelty statement, GraphSAGE/GAT rows, and perfect-groundedness framing |

The source snapshot above already used the later hybrid representation, so it is not the
same numerical protocol as commit `79f860d5`; both are obsolete for different reasons.
The final recovery must use neither as its textual or numerical base.

## Major numerical differences

| Quantity | Obsolete mask-aware protocol (`79f860d5`) | Correct reviewer revision (`39973ed4` + active sources) |
|---|---:|---:|
| WeightedSum Rel@5 / diversity / NDCG@5 | 0.8479 / 0.0000 / 1.0000 | 0.8479 / 0.0187 / 1.0000 |
| LEA Rel@5 / diversity / runtime | 0.8479 / 0.0000 / 93.68 ms | 0.8479 / 0.0224 / 87.26 ms |
| MMR Rel@5 / diversity / NDCG@5 / runtime | 0.8400 / 0.0400 / 0.9871 / 1708.12 ms | 0.8479 / 0.0241 / 1.0000 / 12.70 ms for matched top-5 |
| ParetoCrowding diversity | 0.0000 | 0.0263 |
| DE portfolio | absent | Rel@5 0.8479; diversity 0.0242; 69.39 ms |
| True no-diversity LEA | not separated from gamma-only history | gamma=0 and lambda=0; diversity 0.0187 |
| Joint coefficient sweep | absent | 35 settings × 50 pools = 1,750 runs |

## Repository-state audit

- `git log --all`, `git reflog --all`, `git stash list`, and `git worktree list` were checked.
- No stash contains a later manuscript revision.
- The authoritative repository had one worktree and no hidden later branch.
- Commit `39973ed4` is the latest executable/reproducibility commit; `origin/main` remains at `10082124`.
- The manuscript workspace is not a Git repository, so exact active-source hashes and
  timestamps are the authoritative identity for its current reviewer-driven text.

## Recovery decision

Create `revision/COMMT-final-recovery` from `39973ed4`, preserve the active manuscript,
supplement, and response as a tracked recovery snapshot, retain the reviewer-revision
scripts/configuration/artifacts, and compile new filenames only from those active sources.
