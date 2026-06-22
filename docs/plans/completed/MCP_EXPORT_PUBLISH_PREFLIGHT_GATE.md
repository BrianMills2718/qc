# Plan #198: MCP Export Publish Preflight Gate

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** MCP export-audit integration and export publish preflight scope lint
**Blocks:** Agent-facing guarded export/handoff workflows

---

## Gap

**Current:** MCP export tools (`qc_export_markdown`, `qc_export_json`) can write
confined export artifacts, optional export-audit manifests, optional manifest
verification reports, optional local audit-event logs, and optional SQLite
event-log mirrors. The standalone script/Make/`qc_cli.py` and `project export`
surfaces can run publish/handoff preflight, including optional Markdown/text
scope lint, but the MCP export tools cannot.

**Target:** Add explicit opt-in MCP parameters:

- `publish_preflight=False`
- `scope_lint=False`

`publish_preflight=True` requires `audit_manifest=True`, runs
`run_export_publish_preflight` after the confined manifest is written, returns a
structured `publish_preflight` report, and returns an error payload if the gate
fails. `scope_lint=True` requires `publish_preflight=True` and enables the same
Markdown/text scope phrasing gate.

**Why:** MCP is the agent-facing workflow. Agents should be able to request a
confined export and the final local publish/handoff gate in one tool call,
without remembering to call a separate script outside MCP.

**Non-target:** This slice does not change default MCP export return payloads,
add CSV/QDPX MCP export tools, make preflight mandatory, validate
sampling-frame adequacy, sign artifacts, make event logs append-only, create
external tamper evidence, or produce methodological-validity/SOTA evidence.

---

## References Reviewed

- `qc_mcp_server.py` - `qc_export_markdown`, `qc_export_json`, export path
  confinement, and `_with_optional_export_audit`.
- `tests/test_mcp_server.py` and `tests/test_mcp_export_confinement.py` -
  existing MCP export behavior and confinement regressions.
- `qc_clean/core/export/publish_preflight.py` - strict publish preflight and
  optional scope lint.
- `qc_clean/core/export/audit_event_log.py` - valid event types and SQLite
  mirroring.
- `docs/plans/completed/MCP_EXPORT_AUDIT_INTEGRATION.md` and
  `docs/plans/completed/MCP_EXPORT_AUDIT_SQLITE_MIRROR.md` - prior MCP export
  audit constraints.
- `CLAUDE.md`, `docs/PROJECT_THEORY_AND_GOALS.md`, and `docs/plans/CLAUDE.md`
  - export/audit/scope claim-discipline caveats.
- Memory context:
  `agent-memory recall 'qualitative_coding export mcp publish preflight audit manifest active decisions' --project qualitative_coding`
  returned low-relevance historical outcomes only, no active conflicting
  decision.

---

## Research Basis For This Slice

No external research is needed. This is deterministic MCP parity for existing
repo-local publish/handoff gates.

---

## Capabilities

Internal MCP tool integration only; no new cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_export_markdown(..., publish_preflight=True)` | project ID + confined output path + audit flags | export payload with manifest and publish-preflight report | qualitative_coding MCP | agents | free |
| `qc_export_markdown(..., scope_lint=True)` | project ID + Markdown export + project state + manifest | export payload or error with scope-lint failures | qualitative_coding MCP | agents | free |
| `qc_export_json(..., publish_preflight=True)` | project ID + confined output path + audit flags | export payload with manifest and publish-preflight report | qualitative_coding MCP | agents | free |

### Capability Validation

- [ ] Default MCP export payloads are unchanged when new flags are absent.
- [ ] `publish_preflight=True` requires `audit_manifest=True`.
- [ ] `scope_lint=True` requires `publish_preflight=True`.
- [ ] Passing MCP publish preflight returns a structured report with status
  `pass`.
- [ ] Failing MCP publish preflight returns an error payload with the structured
  report and stable failure codes.
- [ ] MCP audit event logs include `publish_preflight` when requested, and
  SQLite mirrors are refreshed after that event.
- [ ] MCP export path confinement remains intact for artifacts, manifests,
  event logs, and DB mirrors.
- [ ] Docs preserve caveats: local integrity/report-discipline only, not
  sampling adequacy, methodological validity, signing, append-only storage,
  external tamper evidence, or SOTA.

---

## Files Expected To Change

- `qc_mcp_server.py`
- `tests/test_mcp_server.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`
- `docs/plans/completed/MCP_EXPORT_PUBLISH_PREFLIGHT_GATE.md`

---

## Plan

### Steps

1. [ ] Add failing MCP tests for dependency validation, passing preflight,
   scope-lint blocking behavior, audit-event/DB inclusion, and preserved
   confinement/default payloads.
2. [ ] Extend `_with_optional_export_audit` with opt-in publish preflight and
   scope lint, using `run_export_publish_preflight`.
3. [ ] Add `publish_preflight` / `scope_lint` parameters and docstrings to
   `qc_export_markdown` and `qc_export_json`.
4. [ ] Update docs/CLAUDE/theory/plan caveats and regenerate `AGENTS.md`.
5. [ ] Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
6. [ ] Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_mcp_server.py` | `test_export_publish_preflight_requires_audit_manifest` | MCP publish preflight cannot run without a manifest sidecar. |
| `tests/test_mcp_server.py` | `test_export_scope_lint_requires_publish_preflight` | MCP scope lint is only valid as an explicit publish-preflight option. |
| `tests/test_mcp_server.py` | `test_export_markdown_with_publish_preflight` | Passing Markdown export returns a publish-preflight report. |
| `tests/test_mcp_server.py` | `test_export_markdown_scope_lint_blocks_risky_text` | MCP scope lint returns error payload with `scope_lint_*` failure codes. |
| `tests/test_mcp_server.py` | `test_export_json_publish_preflight_event_log_and_db` | MCP event log/SQLite mirror include `publish_preflight`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_mcp_server.py tests/test_mcp_export_confinement.py tests/test_export_publish_preflight.py -q` | MCP export behavior, confinement, and standalone gate compatibility. |
| `python -m ruff check qc_mcp_server.py tests/test_mcp_server.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_export_markdown` and `qc_export_json` accept `publish_preflight` and
  `scope_lint` booleans.
- [ ] `publish_preflight=True` fails loud in the returned JSON payload unless
  `audit_manifest=True`.
- [ ] `scope_lint=True` fails loud in the returned JSON payload unless
  `publish_preflight=True`.
- [ ] Passing MCP publish preflight returns `publish_preflight.status == "pass"`.
- [ ] Failing MCP publish preflight returns an error payload and preserves the
  structured failure report.
- [ ] Optional scope lint blocks risky Markdown/text handoff artifacts under
  missing/under-specified scope.
- [ ] Audit JSONL/SQLite workflows include the MCP `publish_preflight` event
  when audit logging is enabled.
- [ ] Existing MCP export behavior without new flags is unchanged.
- [ ] Documentation preserves caveats: this is opt-in local integrity and
  report-boundary discipline only.

> Process criteria:
- [ ] Plan committed before implementation.
- [ ] Red tests observed before implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff passes.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes, or any failure is documented as unrelated with
  evidence.
- [ ] Implementation and closeout commits are pushed.

---

## Failure Modes And Diagnostics

| Failure Mode | Diagnostic | Response |
|--------------|------------|----------|
| Default MCP export payload changes | Existing MCP export tests fail | Keep both new flags default false and conditional. |
| Preflight writes outside export sandbox | Confinement tests and path assertions | Reuse confined artifact/manifest paths and existing `EXPORTS_DIR`. |
| Scope lint runs without project state | MCP tests | Use the already loaded `ProjectState`. |
| Audit DB misses publish-preflight event | Event-log/DB test | Mirror after all requested audit events are appended. |
| Docs imply a full audit/security guarantee | Manual caveat review + docs-check | Keep language to local, opt-in integrity/provenance/report discipline. |

---

## Closeout

Pending implementation.
