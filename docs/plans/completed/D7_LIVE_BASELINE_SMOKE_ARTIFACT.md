# Plan #217: D7 Live Baseline Smoke Artifact

**Status:** Completed
**Type:** benchmark artifact
**Priority:** High
**Blocked By:** None
**Blocks:** live D7 candidate-selection baseline comparison smoke evidence

---

## Gap

**Current:** D7 retrieval smoke evidence exists, and the repo can export live
D7 candidate-selection baseline packages with explicit `PROJECTS_DIR` support.
However, there is no committed artifact that runs the opt-in live D7 baseline
through validation, D7 comparison preflight, comparison scoring, artifact
verification, and strict package replay.

**Target:** Commit a small synthetic D7 live-baseline smoke artifact under
`docs/benchmarks/d7_live_baseline_smoke_2026_06_23/` that proves the live
candidate-selection baseline can be exported from a repo-local project store,
validated, preflighted against synthetic D7 gold, compared, artifact-verified,
and replayed through `compare-d7-package`.

**Why:** The roadmap names held-out D7 evaluation with live baselines as a
remaining gap. Real held-out D7 evidence needs expert/adjudicated labels, but a
synthetic smoke artifact can still verify the live-baseline plumbing end to end
without mutating the default project store.

**Claim boundary:** This is workflow/provenance smoke evidence only. It is not
held-out D7 evidence, live-baseline quality evidence, semantic disconfirmation
validity, superiority evidence, methodological-validity evidence, or SOTA
evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §13.1, §18 - INV-2/D7 status and roadmap.
- `docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/` - deterministic
  retrieval smoke artifact pattern.
- `docs/plans/completed/D7_LIVE_BASELINE_PROJECTS_DIR_PARITY.md` - explicit
  project-store live baseline export support.
- `docs/plans/completed/D7_COMPARISON_PACKAGE_PROJECTS_DIR_SUPPORT.md` - strict
  package replay with package-local project stores.
- `qc_clean/core/d7_live_baseline.py` - live candidate-selection exporter.
- `scripts/run_d7_live_baseline.py`, `scripts/compare_d7_retrieval.py`,
  `scripts/write_d7_comparison_package.py`, and
  `scripts/run_d7_comparison_package.py` - artifact command surfaces.

---

## Research Basis For This Slice

No additional external research. This is repo-local smoke evidence for the
existing D7 live-baseline orchestration chain.

---

## Capabilities

Internal project capability only; no cross-project registry entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D7 live-baseline smoke comparison | synthetic ProjectState + versioned D7 gold | live baseline package + D7 comparison report/artifact | qualitative_coding | roadmap/portfolio reviewers | paid LLM |

### Capability Validation

Skipped for cross-project registry purposes: this uses existing project-local
D7 benchmark surfaces.

---

## Files Affected

- `docs/plans/completed/D7_LIVE_BASELINE_SMOKE_ARTIFACT.md` - completed plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- New benchmark artifact directory:
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/README.md`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/projects/d7_live_baseline_smoke_project.json`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/preflight.json`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/report.json`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/package.json`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/package_report.json`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/package_replay_report.json`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/artifact/...`
  - `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/verification.json`
- Docs after artifact:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Create a small synthetic repo-local ProjectState with one claim target and
   one contrary candidate span.
2. Create a versioned synthetic D7 gold package matching that contrary span.
3. Run `make run-d7-live-baseline` with explicit `PROJECTS_DIR`, bounded
   `TRACE_ID`, `MAX_BUDGET=1.0`, and `CANDIDATES=1`.
4. Validate the live baseline package.
5. Create a D7 comparison protocol whose expected prediction hash matches the
   live baseline package.
6. Run D7 comparison preflight, direct comparison with artifact output, artifact
   verification, strict comparison package writer, and strict package replay.
7. Write README and update docs with caveats.
8. Run focused D7 live/comparison tests, docs-check, diff-check, and
   `make check`.
9. Commit/push artifact and close the plan.

---

## Required Tests

### Artifact Commands

| Command | What It Verifies |
|---------|------------------|
| `make run-d7-live-baseline ID=d7_live_baseline_smoke_project PROJECTS_DIR=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/projects OUTPUT=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json MODEL=gpt-5-mini TRACE_ID=qualitative_coding/d7-live-baseline-smoke-2026-06-23 MAX_BUDGET=1.0 CANDIDATES=1` | Live candidate-selection package exports from repo-local project store. |
| `make validate-d7-baseline-package PACKAGE=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json` | Live baseline package is schema-valid. |
| `make validate-d7-gold GOLD=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json` | Synthetic D7 gold package is schema-valid. |
| `make validate-d7-comparison-protocol PROTOCOL=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json` | Protocol metadata and expected prediction hash are valid. |
| `make d7-comparison-preflight PROTOCOL=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json GOLD=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json PREDICTIONS=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json` | Protocol/gold/live-baseline package preflight passes. |
| `make compare-d7-retrieval ID=d7_live_baseline_smoke_project PROJECTS_DIR=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/projects GOLD=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json PREDICTIONS=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json PROTOCOL=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json OUTPUT=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/report.json ARTIFACT_DIR=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/artifact` | Direct comparison writes report and artifact. |
| `make verify-d7-comparison-artifact ARTIFACT=<created manifest>` | Artifact manifest verifies against copied report. |
| `make write-d7-comparison-package ID=d7_live_baseline_smoke_project PROJECTS_DIR=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/projects GOLD=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json PREDICTIONS=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json OUTPUT=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/package.json PROTOCOL=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json COMPARISON_OUTPUT=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/package_replay_report.json` | Strict package manifest records project store and inputs. |
| `make compare-d7-package PACKAGE=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/package.json` | Strict package replay succeeds. |

### Regression Gates

| Command | Why |
|---------|-----|
| `python -m pytest tests/test_d7_live_baseline.py tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py tests/test_d7_comparison_guard.py tests/test_d7_comparison_package_runner.py tests/test_d7_comparison_package_writer.py -q` | Focused live-baseline and comparison/package regressions. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] Artifact directory contains project shell, gold, live baseline package,
  protocol, preflight, comparison report, package manifest, package replay
  report, artifact manifest/report, verification output, and README.
- [x] Live baseline package validates and contains one selected candidate for
  the synthetic claim.
- [x] D7 comparison preflight passes against the live baseline package.
- [x] Direct comparison report includes the live baseline row and records
  input-hash/command provenance.
- [x] Artifact verifier reports `status="verified"`.
- [x] Strict comparison package replay succeeds from the package manifest with
  package-local `projects_dir`.
- [x] README/docs state this is live-baseline workflow smoke evidence only, not
  held-out D7 validity, live-baseline quality, or SOTA evidence.

Process criteria:

- [x] Artifact commands pass or any live-run failure is recorded with concrete
  error evidence and the next safe action.
- [x] Focused D7 regression tests pass.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Outcome

Committed `docs/benchmarks/d7_live_baseline_smoke_2026_06_23/`, a synthetic D7
live-baseline smoke artifact that runs the opt-in live candidate selector
through validation, D7 comparison preflight, direct comparison, artifact
verification, strict package writing, and strict package replay from a
package-local `projects_dir`.

Result summary:

- Live baseline package: one target claim, one retrieved candidate, one live
  selected candidate.
- Baseline row: `live_candidate_selector_gpt_5_mini_lexical_bm25_top1`.
- Direct comparison and package replay both report baseline
  recall/precision/F1 = 1.0 / 1.0 / 1.0 on the synthetic exact anchor.
- Direct comparison preflight: pass.
- Metric criteria: 2 passed, 0 failed.
- Artifact verification: verified.

Implementation commit:
`b1f78dad [Plan: D7_LIVE_SMOKE] Add D7 live baseline smoke artifact`

Verification:

- `make run-d7-live-baseline ID=d7_live_baseline_smoke_project PROJECTS_DIR=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/projects OUTPUT=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json MODEL=gpt-5-mini TRACE_ID=qualitative_coding/d7-live-baseline-smoke-2026-06-23 MAX_BUDGET=1.0 CANDIDATES=1`
  - Result: selected_candidate_count=1.
- `make validate-d7-baseline-package PACKAGE=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json`
  - Result: status=pass, selected_candidate_count=1.
- `make validate-d7-gold GOLD=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json`
  - Result: valid, contrary_evidence_count=1.
- `make validate-d7-comparison-protocol PROTOCOL=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json`
  - Result: status=valid, expected_prediction_count=1,
    metric_criteria_count=2.
- `python scripts/preflight_d7_comparison.py docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json`
  - Result: status=pass.
- `make compare-d7-retrieval ID=d7_live_baseline_smoke_project PROJECTS_DIR=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/projects GOLD=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json PREDICTIONS=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json PROTOCOL=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json OUTPUT=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/report.json ARTIFACT_DIR=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/artifact`
  - Result: report written, preflight=pass, baseline recall/precision/F1=1.0.
- `python scripts/verify_d7_comparison_artifact.py docs/benchmarks/d7_live_baseline_smoke_2026_06_23/artifact/20260623T220928828002Z-d7_live_baseline_smoke_project-d7-comparison/manifest.json`
  - Result: status=verified.
- `python scripts/write_d7_comparison_package.py d7_live_baseline_smoke_project --projects-dir docs/benchmarks/d7_live_baseline_smoke_2026_06_23/projects --output docs/benchmarks/d7_live_baseline_smoke_2026_06_23/package.json --gold-file docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json --predictions-file docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json --protocol-package docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json --comparison-output package_replay_report.json`
  - Result: status=complete, package `projects_dir="projects"`.
- `python scripts/run_d7_comparison_package.py docs/benchmarks/d7_live_baseline_smoke_2026_06_23/package.json`
  - Result: package replay report written, preflight=pass, baseline
    recall/precision/F1=1.0.
- `python -m pytest tests/test_d7_live_baseline.py tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py tests/test_d7_comparison_guard.py tests/test_d7_comparison_package_runner.py tests/test_d7_comparison_package_writer.py -q`
  - Result: 28 passed.
- `make docs-check`
  - Result: Markdown links OK; doc coupling config valid; plan records
    consistent; `AGENTS.md` in sync.
- `git diff --check`
  - Result: clean.
- `make check`
  - Result: 1302 passed, 1 skipped, 8 deselected; Ruff all checks passed;
    docs-check passed; type check not yet configured.

Claim boundary: this is workflow/provenance smoke evidence only. It is not
held-out D7 evidence, live-baseline quality evidence, semantic disconfirmation
validity, superiority evidence, methodological-validity evidence, or SOTA
evidence.

---

## Open Questions

- [x] Should this use synthetic gold rather than wait for expert labels?
  Status: RESOLVED. Yes for this slice. The objective is smoke coverage for the
  live-baseline artifact chain; expert/adjudicated held-out D7 evidence remains
  a separate roadmap item.

---

## Notes

This plan should avoid claiming the live selector is good. It only proves the
repo can run, package, validate, compare, verify, and replay live D7 baseline
outputs from repo-local artifacts.
