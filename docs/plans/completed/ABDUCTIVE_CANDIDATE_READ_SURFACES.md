# Plan #229: Abductive Candidate Read Surfaces

## Outcome

Completed 2026-06-25. Added bounded read surfaces for provisional abductive
candidate explanations through `qc_cli.py project abductive`,
`/projects/{project_id}/abductive-explanations`, project summary counts, and
Markdown report output. Rows expose source pattern IDs, mechanism summaries,
rival explanations, observable implications, evidence gaps, provisional
confidence, and candidate status. Documentation now states these are inspection
surfaces for provisional hypotheses only, not causal proof, process-tracing
results, methodological-validity evidence, or SOTA evidence.

Verification:

- `python -m pytest tests/test_project_commands.py tests/test_review_api.py tests/test_claim_ledger_exports.py -q` — 149 passed.
- `python -m ruff check qc_cli.py qc_clean/core/cli/commands/project.py qc_clean/plugins/api/api_server.py qc_clean/core/export/data_exporter.py qc_clean/core/abductive.py tests/test_project_commands.py tests/test_review_api.py tests/test_claim_ledger_exports.py` — passed.
- `make docs-check` — passed.
- `git diff --check` — passed.
- `make check` — 1340 passed, 1 skipped, 8 deselected; Ruff/docs passed; type check not configured.

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #228
**Blocks:** Candidate explanation review workflow, process-tracing/workbench handoff bundle

---

## Gap

**Current:** `ProjectState.abductive_explanations` can persist provisional
candidate explanations from `project run --abductive`, but operators can only
inspect them through raw JSON exports.

**Target:** Add bounded read surfaces matching existing claim/pattern
conventions: `qc_cli.py project abductive`, API
`/projects/{project_id}/abductive-explanations`, and a Markdown report section.
Rows must show source pattern IDs, mechanism summary, rivals, observable
implications, evidence gaps, confidence, and status with explicit provisional
caveats.

**Why:** Candidate explanations are only useful if a human or agent can inspect
them before review, process tracing, or workbench handoff. Read surfaces should
come before review semantics.

---

## References Reviewed

- `docs/plans/completed/ABDUCTIVE_CANDIDATE_EXPLANATION_SUBSTRATE.md` - source
  model/stage plan and caveats.
- `qc_clean/schemas/domain.py` - `AbductiveCandidateExplanation` and
  `ProjectState.abductive_explanations`.
- `qc_clean/core/cli/commands/project.py` - `project claims` / `project patterns`
  read-surface conventions.
- `qc_cli.py` - project subparser wiring.
- `qc_clean/plugins/api/api_server.py` - `/projects/{project_id}/claims` and
  `/projects/{project_id}/patterns` endpoint conventions.
- `qc_clean/core/export/data_exporter.py` - Markdown report sections.
- `tests/test_project_commands.py`, `tests/test_review_api.py`, and
  `tests/test_claim_ledger_exports.py` - matching CLI/API/export tests.

---

## Research Basis For This Slice

No external research is needed. This is a local read-surface slice over the
typed candidate objects created in Plan #228.

---

## Capabilities

Skipped: this exposes local read surfaces only. A future cross-project
workbench/process-tracing handoff plan should formalize the boundary contract.

---

## Files Affected

- `qc_clean/core/abductive.py` - compact row/summary helpers.
- `qc_clean/core/cli/commands/project.py` - CLI read handler and project summary
  count.
- `qc_cli.py` - `project abductive` parser.
- `qc_clean/plugins/api/api_server.py` - bounded candidate endpoint and route
  registry.
- `qc_clean/core/export/data_exporter.py` - Markdown candidate section.
- `tests/test_project_commands.py` - CLI/route tests.
- `tests/test_review_api.py` - API endpoint tests.
- `tests/test_claim_ledger_exports.py` - Markdown export tests.
- `CLAUDE.md` / `AGENTS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - command and
  state/read-surface guidance.
- `docs/plans/ACTIVE_SPRINT.md` and `docs/plans/CLAUDE.md` - plan tracking.

---

## Plan

### Steps

1. Add shared candidate row/summary helpers.
2. Add `project abductive <project_id> --limit --offset` CLI output.
3. Add `/projects/{project_id}/abductive-explanations` API endpoint with
   bounded `limit`/`offset`, total/returned metadata, and caveat.
4. Add Markdown `Abductive Candidate Explanations` section when candidates
   exist.
5. Update docs and regenerate `AGENTS.md`.
6. Add focused tests and run full gates.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_project_commands.py` | `test_project_abductive_command_shows_candidate_explanations` | CLI lists bounded candidates with source pattern/status/mechanism and caveat. |
| `tests/test_review_api.py` | `test_project_abductive_endpoint_returns_bounded_rows` | API returns bounded candidate rows and pagination metadata. |
| `tests/test_claim_ledger_exports.py` | `test_export_markdown_includes_abductive_candidates` | Markdown report includes provisional candidate section and caveat. |
| `tests/test_project_commands.py` | `test_api_routes_include_project_abductive_endpoint` | Endpoint registry advertises the new path. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_project_commands.py tests/test_review_api.py tests/test_claim_ledger_exports.py -q` | CLI/API/export surfaces touched by this slice. |
| `python -m ruff check qc_cli.py qc_clean/core/cli/commands/project.py qc_clean/plugins/api/api_server.py qc_clean/core/export/data_exporter.py qc_clean/core/abductive.py tests/test_project_commands.py tests/test_review_api.py tests/test_claim_ledger_exports.py` | Touched-file lint. |
| `make docs-check` | Plan/docs/generated mirror checks. |
| `git diff --check` | Whitespace hygiene. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `qc_cli.py project abductive <project_id>` lists provisional candidate
  explanations with bounded pagination.
- [x] `/projects/{project_id}/abductive-explanations` returns bounded candidate
  rows and pagination metadata.
- [x] Markdown export includes candidate explanations when present and omits the
  section when absent.
- [x] Rows expose source pattern IDs, mechanism summary, rivals, observable
  implications, evidence gaps, confidence, and status.
- [x] Every surface preserves caveats that candidates are provisional
  hypotheses, not causal proof or process-tracing results.

> Process criteria:
- [x] Required focused tests pass.
- [x] Ruff passes for touched files.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should these rows be review targets now? Status: DEFERRED. Read surfaces
  come first; review actions need a separate status/decision policy.
- [ ] Should these rows export to CSV/QDPX? Status: DEFERRED. Start with CLI,
  API, and Markdown; future workbench handoff should define the interchange
  contract.

---

## Notes

This slice exposes provisional candidates for inspection only. It does not
change generation, claim-ledger promotion, disconfirmation targeting, or
process-tracing handoff semantics.
