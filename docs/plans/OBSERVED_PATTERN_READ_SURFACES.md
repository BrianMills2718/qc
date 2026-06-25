# Plan #227: Observed Pattern Read Surfaces

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** #226
**Blocks:** Abductive synthesis stage, QC-to-workbench evidence/pattern bundle, causal hypothesis handoff to process tracing

---

## Gap

**Current:** `ProjectState.observed_patterns` now stores first-class descriptive
patterns, but operators can only inspect them by opening raw project JSON or
writing custom code. The CLI/API/export surfaces still emphasize claims, review
items, and traditional report sections.

**Target:** Add bounded, agent-drivable observed-pattern read surfaces that
match the existing claim-ledger style: `qc_cli.py project patterns`, an API
endpoint at `/projects/{project_id}/patterns`, and a Markdown report section.
The rows must preserve the descriptive-only caveat and must not imply causal
proof, abductive synthesis, methodological validity, or SOTA evidence.

**Why:** Observed patterns are the next substrate for abductive and
mixed-methods workbench integration. They need a reviewable output surface
before later stages consume or upgrade them.

---

## References Reviewed

- `qc_clean/schemas/domain.py` - `ObservedPattern`, causal-status enum, and
  `ProjectState.observed_patterns`.
- `qc_clean/core/cli/commands/project.py` - existing claim-ledger CLI read
  surface and project command dispatch.
- `qc_cli.py` - project subparser wiring for `project claims`.
- `qc_clean/plugins/api/api_server.py` - existing `/projects/{project_id}/claims`
  endpoint and endpoint registry.
- `qc_clean/core/export/data_exporter.py` - Markdown report structure and claim
  ledger export section.
- `tests/test_project_commands.py` - project CLI/export/API route tests.
- `tests/test_review_api.py` - claim API pagination and row-shape tests.
- `tests/test_claim_ledger_exports.py` - Markdown claim-ledger export tests.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim-discipline and observed-pattern
  substrate caveats.
- `CLAUDE.md` - operational command list and project philosophy.
- Memory context: `agent-memory recall 'observed patterns read surfaces qualitative coding active decisions' --project qualitative_coding` - 2 generic historical findings, no relevant active design decision.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
read-surface and reporting slice over already-created descriptive pattern
records.

---

## Capabilities

Skipped: this adds local CLI/API/report read surfaces but no cross-project
boundary contract. A later QC-to-workbench export plan should define a formal
Pydantic contract for pattern bundles.

---

## Files Affected

- `qc_clean/core/cli/commands/project.py` - add pattern CLI dispatch/output.
- `qc_cli.py` - add `project patterns` parser.
- `qc_clean/plugins/api/api_server.py` - add `/projects/{project_id}/patterns`
  and endpoint registry entry.
- `qc_clean/core/export/data_exporter.py` - add Markdown observed-pattern
  section.
- `tests/test_project_commands.py` - CLI/parser/export route coverage.
- `tests/test_review_api.py` or a focused API test file - pattern endpoint
  coverage.
- `tests/test_claim_ledger_exports.py` or a focused export test file - Markdown
  pattern section coverage.
- `CLAUDE.md` / `AGENTS.md` - command guidance, with generated mirror refresh.
- `docs/PROJECT_THEORY_AND_GOALS.md` - state/read-surface caveat update if
  needed.
- `docs/plans/ACTIVE_SPRINT.md` and `docs/plans/CLAUDE.md` - plan tracking.

---

## Plan

### Steps

1. Add compact observed-pattern row formatting local to the CLI/API/report
   surfaces or a small shared helper if duplication appears.
2. Add `qc_cli.py project patterns <project_id>` with `--limit`, `--offset`,
   and `--show-anchors`.
3. Add CLI handler output that reports total patterns, displayed range, kind,
   causal interpretation status, summary, and compact code/document/application
   scope.
4. Add `/projects/{project_id}/patterns` with bounded `limit`/`offset`, total
   count, returned count, and row payloads suitable for agent inspection.
5. Add a Markdown `Observed Patterns` section capped to a readable default and
   explicitly labeled descriptive-only.
6. Update command documentation and regenerate `AGENTS.md`.
7. Add focused tests, then run full deterministic gates.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_project_commands.py` | `test_project_patterns_command_shows_descriptive_patterns` | CLI lists observed patterns with kind/status/scope and pagination metadata. |
| `tests/test_review_api.py` | `test_project_patterns_endpoint_returns_bounded_rows` | API returns bounded observed-pattern rows with total/returned/limit/offset metadata. |
| `tests/test_claim_ledger_exports.py` | `test_export_markdown_includes_observed_patterns` | Markdown report includes observed patterns and descriptive-only caveat. |
| `tests/test_project_commands.py` | `test_api_routes_include_project_patterns_endpoint` | Endpoint registry advertises `/projects/{project_id}/patterns`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_project_commands.py tests/test_review_api.py tests/test_claim_ledger_exports.py -q` | Covers CLI/API/export surfaces touched by this slice. |
| `python -m ruff check qc_cli.py qc_clean/core/cli/commands/project.py qc_clean/plugins/api/api_server.py qc_clean/core/export/data_exporter.py tests/test_project_commands.py tests/test_review_api.py tests/test_claim_ledger_exports.py` | Fatal lint gate for touched Python files. |
| `make docs-check` | Plan/docs/generated mirror checks. |
| `git diff --check` | Whitespace hygiene. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_cli.py project patterns <project_id>` lists observed patterns with
  bounded pagination and compact scope.
- [ ] `/projects/{project_id}/patterns` returns bounded machine-readable
  pattern rows and pagination metadata.
- [ ] Markdown export includes an observed-pattern section when patterns exist.
- [ ] Read surfaces expose `causal_interpretation_status` and preserve the
  descriptive-only caveat.
- [ ] Empty projects remain quiet/compatible; no report section appears when
  no patterns exist.
- [ ] No surface claims causal proof, abductive synthesis, methodological
  validity, or SOTA evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Ruff passes for touched files.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should observed patterns enter the human review queue in this slice?
  Status: DEFERRED. Read-only inspection is enough for this slice; review
  semantics need a separate target type and decision policy.
- [ ] Should the API include full anchor quote text by default?
  Status: RESOLVED. Include bounded anchor details only when enough fields
  already exist on the pattern. Keep rows compact and aligned with claim
  anchor-detail conventions.
- [ ] Should the formal workbench bundle contract be created now?
  Status: DEFERRED. This plan creates inspectability first; a later boundary
  plan should define the mixed-methods workbench contract.

---

## Notes

This slice makes descriptive pattern records visible. It deliberately does not
change how patterns are generated, reviewed, causally interpreted, or exported
as a cross-project workbench contract.
