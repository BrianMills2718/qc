# Plan #163: MCP Export Audit SQLite Mirror

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Export audit SQLite workflow integration
**Blocks:** future signed/external audit anchoring

---

## Gap

**Current:** Local scripts, Make targets, and `project export` can mirror JSONL
audit events into SQLite with explicit `--audit-db` / `AUDIT_DB`. MCP JSON and
Markdown export tools can write confined manifests and JSONL event logs, but
cannot write a confined SQLite event mirror.

**Target:** Add optional MCP SQLite event mirrors:

- `qc_export_json(..., audit_event_db=True)`
- `qc_export_markdown(..., audit_event_db=True)`

The DB path is derived from the confined export artifact name under
`EXPORTS_DIR` (for example `export.audit_events.sqlite`). `audit_event_db=True`
requires `audit_event_log=True`, which already requires `audit_manifest=True`.
Default MCP export payloads remain unchanged.

**Why:** MCP clients should have the same local/queryable audit event mirror as
CLI/script clients, while preserving MCP path confinement and explicit opt-in
semantics.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 item 11 - current audit-substrate
  status and caveats.
- `qc_mcp_server.py` - confined export, manifest, and event-log sidecar helpers.
- `qc_clean/core/export/audit_event_log.py` - SQLite mirror and verifier helpers.
- `tests/test_mcp_server.py` - current MCP export audit sidecar tests.
- `docs/plans/completed/EXPORT_AUDIT_SQLITE_WORKFLOW_INTEGRATION.md` - local
  CLI/script DB mirror integration and remaining MCP caveat.
- Memory context:
  `agent-memory recall 'MCP export audit SQLite mirror confined output qualitative_coding' --project qualitative_coding`
  - 2 low-relevance historical findings, no active conflicting decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this extends project-local MCP export tool parameters and does not
create a cross-project callable capability.

---

## Files Affected

- `qc_mcp_server.py` - add confined SQLite sidecar helper and
  `audit_event_db` tool parameter.
- `tests/test_mcp_server.py` - add MCP SQLite mirror and dependency-guard
  regressions.
- `CLAUDE.md`, `AGENTS.md`, and `docs/PROJECT_THEORY_AND_GOALS.md` - status
  wording.

---

## Plan

### Steps

1. Add tests proving MCP JSON/Markdown export writes a confined SQLite mirror
   when `audit_event_db=True` is supplied with `audit_event_log=True`.
2. Add tests proving `audit_event_db=True` fails without `audit_event_log=True`.
3. Implement confined DB sidecar naming from the already-confined export path.
4. Mirror the JSONL event log after event appends.
5. Update docs and run focused/full gates.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_mcp_server.py` | `test_export_json_with_audit_event_db` | MCP JSON export writes a confined SQLite mirror and verifies it |
| `tests/test_mcp_server.py` | `test_export_audit_event_db_requires_event_log` | `audit_event_db=True` requires `audit_event_log=True` |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_mcp_server.py -q` | MCP export behavior remains compatible |
| `make docs-check` | AGENTS sync and plan docs remain valid |
| `make check` | Full deterministic gate remains green |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] MCP JSON export can write a confined SQLite audit event mirror.
- [ ] MCP Markdown export uses the same confined naming helper.
- [ ] `audit_event_db=True` fails loud unless `audit_event_log=True`.
- [ ] Default MCP export payloads remain unchanged when audit DB flags are
  absent.
- [ ] Docs preserve the local mirror caveat and do not call this append-only or
  tamper-evident storage.

Process criteria:

- [ ] Required focused tests pass.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Open Questions

- [ ] None.

---

## Notes

This plan does not make audit logging or DB mirrors default. It only adds an
explicit MCP opt-in that mirrors the confined JSONL event log.
