# Mission: Report Authoritativeness Continuous Run

## Objective
Complete the current report-baseline and reviewer-report-authoritativeness program so the structured pipeline can be compared fairly against simpler transcript-to-report baselines. The immediate product problem is that reviewer Markdown can present historical memo accumulation as if it were final analysis, causing incompatible prevalence facts inside one report.

## Success Criteria For Full Completion

- [ ] Active plan records the exact completion contract for this run.
- [ ] Baseline substrate remains runnable through `qc_cli.py run-report-baselines` and has focused tests.
- [ ] Side-by-side report comparison is runnable through a canonical CLI and has focused tests.
- [ ] Comparison artifact scores structured report and both baselines on coherence, grounding, disagreement handling, scope discipline, recommendation traceability, reviewer usefulness, and auditability.
- [ ] Reviewer Markdown no longer renders superseded historical `cross_case` memo accumulation as final peer analysis.
- [ ] Audit/history surfaces still preserve full memo history outside reviewer Markdown.
- [ ] Export tests prove both the diagnosed failure mode and the intended reviewer-report behavior.
- [ ] Contradiction/authoritativeness risk is documented honestly: this slice removes stale cross-case memo duplication from reviewer Markdown but does not claim full semantic contradiction detection.
- [ ] Focused pytest targets pass.
- [ ] Ruff passes for touched Python files.
- [ ] Governance/documentation checks pass.
- [ ] `git diff --check` passes.
- [ ] Diff is reviewed after implementation, with risks and remaining gaps recorded.
- [ ] Worktree is left commit-ready, with pre-existing and new changes distinguishable.

## Constraints

- Do not hide unresolved live contradictions by arbitrarily choosing a preferred fact.
- Keep the fix scoped to the diagnosed reviewer Markdown failure unless tests justify broader memo filtering.
- Preserve full memo history in audit/state/CSV exports.
- Do not claim the structured system beats baselines until a scored comparison exists.

## Current Phase

Add the scored side-by-side comparison artifact so baseline runs can be evaluated against the structured reviewer report without relying on chat-only judgment.

## Completed

- Baseline-comparison plan documented in `docs/plans/SOTA_METHODODOLOGY_PIPELINE_REALIGNMENT.md`.
- Transcript-only baseline substrate added for `direct_report` and `qa_report`.
- Both baselines were run on the copied seed artifact and the early comparison was recorded.
- Exact diagnosis recorded in conversation: historical `cross_case` memos accumulate in `state.memos`, Markdown rendered them all, and current observed patterns were rendered beside them.
- Reviewer Markdown now filters only superseded historical `cross_case` memo families, preserves non-cross-case memo repetition, and emits an explicit omission note when cross-case histories are hidden from the reviewer report.
- CSV memo export is covered to preserve historical `cross_case` memos for audit.
- Commit `286fd0db` was pushed to `origin/main` for the baseline substrate and reviewer Markdown authoritativeness fix.
- Report-baseline comparison scoring now has a deterministic package design and canonical CLI surface in progress.
- Export-time prevalence conflict gate is now in progress so reviewer Markdown fails loud if incompatible X/Y document-count facts remain.
- Recommendation traceability/support-status gating is now in progress for reviewer Markdown.
- Markdown reviewer/full profile split is now in progress so the default audit export can coexist with a cleaner reviewer-facing report.

## Progress Log

- 2026-06-26: Continuous run started after interrupted exporter patch. Initial focused review found the current patch red: one characterization test still asserts old behavior, and an `xfail(strict=True)` regression now XPASSes after the helper change.
- 2026-06-26: Reworked the exporter patch to narrowly filter only superseded `cross_case` memo histories in Markdown. Focused verification passed: `pytest tests/test_memos.py::TestMarkdownExportMemos tests/test_memos.py::TestCSVExportMemos -q`; combined baseline/export focused tests passed; Ruff passed for touched Python files.
- 2026-06-26: Regenerated `test_output/plan241_position_claims_replay_2026_06_25/report.md` from the copied seed store. The report now contains one `### Cross-Interview Pattern Analysis` memo and the note `Reviewer report omitted 2 superseded cross-case memo(s)`.
- 2026-06-26: Final review found missing schema descriptions on LLM-facing baseline output models; added `Field(description=...)` metadata. Final verification passed with `make check`: 1391 deterministic tests passed, 1 skipped, 8 live tests deselected; Ruff passed; docs/governance checks passed; type check is not configured.
- 2026-06-26: User correctly challenged the premature stop after the first slice. Continuous run resumed with the next unambiguous missing program piece: a scored comparison package for structured report versus direct-report and QA baselines.
- 2026-06-26: Added deterministic report-baseline comparison scorer, script, and top-level CLI. Focused tests passed for scoring behavior, script output, and CLI forwarding. Copied-seed run wrote ignored local `report_baseline_comparison.json` and ranked structured report above both transcript baselines under the heuristic rubric; this is instrumentation, not adjudicated superiority evidence.
- 2026-06-26: Added shared prevalence-conflict detector and Markdown export gate. Focused tests passed for the original bold/colon prevalence form, consistent repeated counts, and fail-loud export behavior. Copied-seed Markdown export still succeeds under the gate.
- 2026-06-26: Added local recommendation evidence context in Markdown export. Focused tests pass for traced recommendations and untraced recommendations. Copied-seed report now shows recommendation evidence status, trace claim IDs, anchor counts, and supporting themes.
- 2026-06-26: Added Markdown `full`/`reviewer` profile split. Focused tests pass for reviewer profile audit-section omission and project export command profile forwarding. Copied-seed reviewer export keeps the analytic story and recommendation trace lines while omitting audit-heavy sections.
- 2026-06-26: Compared copied-seed reviewer report against transcript baselines. Heuristic scores: reviewer structured report `0.845` at 2705 words, direct baseline `0.446` at 606 words, QA baseline `0.435` at 386 words; no prevalence conflicts detected.
