# Session Handoff

## Project

`qualitative_coding` is the qualitative evidence engine for a future mixed-methods workbench. It ingests qualitative documents, produces coded evidence, claims, observed patterns, provisional abductive explanations, negative cases, review packets, benchmark/protocol artifacts, and exports. The repo must preserve claim discipline: software surfaces are not methodological validity, causal proof, process-tracing results, or SOTA evidence.

## What Was Done

- `35b0498f` / `1e748735`: created and completed Plan #231, adding [docs/LONG_TERM_EXECUTION_PLAN.md](../docs/LONG_TERM_EXECUTION_PLAN.md) as the design-plan-aligned execution spine. It names the frame, authority order, modality split, next slices, dependency subplans, concern cadence, and stop conditions.
- `e7665731` / `dd725c48`: created and completed Plan #232, adding first-class abductive candidate review. `ReviewManager`, `/projects/{project_id}/review/abductive-candidates`, shared review decision POST handling, CLI JSON-file review, summary counts, tests, and reviewer-demo snapshots now support `target_type="abductive_candidate"`.
- `b67e517b` / `dc103db4`: created and completed Plan #233, adding a strict schema_version=1 QC-to-process-tracing handoff package. It exports scope, document hashes, observed patterns, abductive candidates, analytic claims, anchors, provenance, and caveats, while rejecting process-tracing inference fields.

## Start With Audit

The next agent should begin adversarially. Do not assume the recent work is correct because tests passed.

Audit questions:

- Does [docs/LONG_TERM_EXECUTION_PLAN.md](../docs/LONG_TERM_EXECUTION_PLAN.md) actually follow the design-plan skill, or does it over-prescribe exploratory work?
- Does `target_type="abductive_candidate"` preserve the correct semantics? Approve means `needs_evidence_review`, not causal promotion.
- Does [qc_clean/core/process_tracing_handoff.py](../qc_clean/core/process_tracing_handoff.py) leak process-tracing inference concepts or omit critical QC provenance?
- Are docs overstating the new package as a bridge rather than a QC-side fixture for consumer review?
- Are `CLAUDE.md`, `AGENTS.md`, `docs/PROJECT_THEORY_AND_GOALS.md`, `docs/CONCERNS.md`, and `docs/plans/ACTIVE_SPRINT.md` internally consistent?
- Are Make, script, and `qc_cli.py` wrappers aligned on `PROJECTS_DIR` / `--projects-dir` behavior?

## Active Source And Generated Files

| Path | Status | Notes |
|---|---|---|
| `docs/LONG_TERM_EXECUTION_PLAN.md` | tracked source | Current long-running execution spine. |
| `qc_clean/core/process_tracing_handoff.py` | tracked source | New strict package schema/export/validation core. |
| `qc_clean/core/pipeline/review.py` | tracked source | New abductive-candidate review target semantics. |
| `scripts/export_process_tracing_handoff.py` | tracked source | Script wrapper used by Make and qc_cli. |
| `scripts/validate_process_tracing_handoff.py` | tracked source | Script validator wrapper used by Make and qc_cli. |
| `test_output/reviewer_demo/handoff/process_tracing_handoff.json` | generated, untracked | Deterministic fixture; regenerate with `make reviewer-demo OUTPUT=test_output/reviewer_demo`. |
| `test_output/reviewer_demo/api_snapshots/review_abductive_candidates_snapshot.json` | generated, untracked | Demo snapshot for candidate review list. |

No important `/tmp` files need backup. The only useful generated artifacts are reproducible under `test_output/reviewer_demo`.

## Build And Verification

Recent verified commands:

```bash
make check
```

Last result: `1353 passed, 1 skipped, 8 deselected`; Ruff and docs checks passed; type check is not configured.

```bash
make reviewer-demo OUTPUT=test_output/reviewer_demo
make validate-process-tracing-handoff PACKAGE=test_output/reviewer_demo/handoff/process_tracing_handoff.json
QC_PROJECTS_DIR=test_output/reviewer_demo/projects python qc_cli.py export-process-tracing-handoff reviewer-demo --output test_output/reviewer_demo/handoff/qc_cli_handoff.json
python qc_cli.py validate-process-tracing-handoff test_output/reviewer_demo/handoff/qc_cli_handoff.json
```

All passed in the previous session.

## Pending Work

### P1: Adversarial Audit

Review commits `35b0498f..dc103db4`. Prioritize bugs, claim overreach, contract drift, doc inconsistency, missing tests, and hidden generated-output assumptions. If changes are needed, create a plan first, make the smallest fix, run focused tests, then `make check`, commit, and push.

### P2: Process-Tracing Consumer Review

The QC-side package is ready for consumer review, not consumer acceptance. Give the process-tracing agent this task:

> Review `/home/brian/projects/qualitative_coding/test_output/reviewer_demo/handoff/process_tracing_handoff.json` and `/home/brian/projects/qualitative_coding/qc_clean/core/process_tracing_handoff.py`. Advise whether the package can map into process_tracing’s future adapter surface without importing internal `pt.schemas` or adding likelihood/posterior/comparative-support fields to QC. Return concrete schema changes or confirm the contract is acceptable as a QC-side fixture.

If the fixture is missing or stale:

```bash
cd /home/brian/projects/qualitative_coding
make reviewer-demo OUTPUT=test_output/reviewer_demo
```

### P3: Choose Next Slice

After audit and consumer review, choose the next slice from [docs/LONG_TERM_EXECUTION_PLAN.md](../docs/LONG_TERM_EXECUTION_PLAN.md). Current likely options:

- process-tracing consumer contract adjustments;
- browser-native abductive candidate review, but only after UI planning;
- sanitized/adjudicated corpus seed for real review evidence;
- populated D3/D7/D8/D9 evaluation lanes.

## Uncertainties

### U1: Consumer Fit

The process-tracing repo owns causal/process-tracing semantics. The QC package validates locally, but it has not been consumed or reviewed by the process-tracing agent. This blocks treating the seam as stable.

### U2: Research-Design Fields

The package intentionally omits process-tracing `research_question`, `focal_window`, `outcome`, source classes, and pre-specified tests. That may be correct because those are PT/source-packet concerns, but consumer review should decide whether QC should export optional hints or stay narrower.

## Do Not Edit Directly

- `AGENTS.md` is generated from `CLAUDE.md`; update `CLAUDE.md`, then run `python scripts/meta/render_agents_md.py`.
- Generated `test_output/reviewer_demo/*` files are not source. Regenerate them instead of hand-editing.
- Do not add PT likelihood vectors, Bayesian updates, `final_posterior`, or `comparative_support` to QC handoff packages.

## Quick Sanity Checks

```bash
git status --short --branch
make check
make reviewer-demo OUTPUT=test_output/reviewer_demo
make validate-process-tracing-handoff PACKAGE=test_output/reviewer_demo/handoff/process_tracing_handoff.json
```
