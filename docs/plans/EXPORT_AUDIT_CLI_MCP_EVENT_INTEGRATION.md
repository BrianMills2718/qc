# Plan #100: Export Audit CLI/MCP Event Integration

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Export audit event log
**Blocks:** stricter release packaging policy; future signed/external audit anchoring

---

## Gap

**Current:** Local audit scripts can append hash-linked event-log records for
manifest write, manifest verification, and publish preflight operations.
`qc_cli.py project export --audit-manifest ... --verify-audit-manifest` and MCP
JSON/Markdown export tools can write and verify manifest sidecars, but those
export workflows cannot yet append event-log records.

**Target:** Add opt-in event-log writing to export-audit workflows:

- CLI: `qc_cli.py project export ... --audit-manifest manifest.json
  [--verify-audit-manifest] --audit-log export_audit_events.jsonl`
- MCP: `qc_export_json(..., audit_manifest=True, audit_event_log=True)` and
  `qc_export_markdown(..., audit_manifest=True, audit_event_log=True)` write a
  confined event-log sidecar under `EXPORTS_DIR`.

Default behavior must remain unchanged. CLI keeps trusted local path freedom;
MCP continues to sandbox all generated paths under `EXPORTS_DIR`.

**Why:** This makes the event-log substrate usable from the main export
workflows agents already call, without forcing event logs on all exports or
claiming signed/immutable audit semantics.

---

## References Reviewed

- `qc_clean/core/export/audit_event_log.py` - append/verify event-log contract.
- `qc_clean/core/cli/commands/project.py` - CLI export implementation and
  manifest write/verify helper.
- `qc_cli.py` - project export parser flags.
- `qc_mcp_server.py` - MCP export confinement and optional manifest sidecar
  helper.
- `tests/test_project_commands.py` - CLI export/audit-manifest regression
  tests.
- `tests/test_mcp_server.py` - MCP export/audit-manifest regression tests.
- `docs/plans/completed/EXPORT_AUDIT_EVENT_LOG.md`
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research is needed. This is integration work over a repo-local
event-log contract.

---

## Capabilities

| Capability | Input | Output | Consumer |
|------------|-------|--------|----------|
| CLI export event logging | export args with `--audit-manifest` and `--audit-log` | export artifacts, manifest, optional event log | local operators, agents |
| MCP export event logging | MCP export args with `audit_manifest=True`, `audit_event_log=True` | confined export payload with event-log path | agent workflows |

---

## Files Affected

- `qc_cli.py` (modify)
- `qc_clean/core/cli/commands/project.py` (modify)
- `qc_mcp_server.py` (modify)
- `tests/test_project_commands.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/EXPORT_AUDIT_CLI_MCP_EVENT_INTEGRATION.md` (create, then move
  to completed)

---

## Plan

### Decisions

- CLI `--audit-log` requires `--audit-manifest`; otherwise export fails before
  writing artifacts, matching the existing `--verify-audit-manifest` dependency
  rule.
- CLI writes `manifest_written` after manifest write and `manifest_verified`
  after immediate verification when `--verify-audit-manifest` is supplied.
- MCP exposes a boolean `audit_event_log`; callers cannot supply an arbitrary
  event-log path.
- MCP `audit_event_log=True` requires `audit_manifest=True`; otherwise the tool
  returns an error payload.
- MCP event logs are confined to `EXPORTS_DIR` and named from the export stem
  (for example `report.audit_events.jsonl`).
- No default export behavior changes; event logs remain opt-in.
- This slice does not make event logs signed, externally anchored, immutable,
  or mandatory for public release.

### Steps

1. Add parser flag and CLI helper plumbing.
2. Add MCP parameter, confined event-log path helper, and optional event
   appends in `_with_optional_export_audit`.
3. Add tests for CLI parser, CLI event appends, CLI dependency failure, MCP
   confined event path, and MCP dependency failure.
4. Update docs conservatively.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_project_commands.py` | `test_project_export_command_writes_audit_event_log` | CLI export appends manifest write/verify events when `--audit-log` is supplied. |
| `tests/test_project_commands.py` | `test_project_export_command_rejects_audit_log_without_manifest` | CLI refuses audit-log path without audit manifest. |
| `tests/test_project_commands.py` | `test_export_subparser_audit_log_flag` | CLI parser exposes `--audit-log`. |
| `tests/test_mcp_server.py` | `test_export_json_with_audit_event_log` | MCP JSON export writes confined event-log sidecar when requested. |
| `tests/test_mcp_server.py` | `test_export_audit_event_log_requires_audit_manifest` | MCP rejects event log without manifest. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_project_commands.py tests/test_mcp_server.py tests/test_export_audit_event_log.py -q` | CLI/MCP/event-log integration. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] CLI `project export` supports `--audit-log` when `--audit-manifest` is
  supplied.
- [ ] CLI export appends `manifest_written` and, when requested,
  `manifest_verified` events.
- [ ] CLI rejects `--audit-log` without `--audit-manifest`.
- [ ] MCP JSON/Markdown export tools support confined `audit_event_log=True`.
- [ ] MCP rejects `audit_event_log=True` without `audit_manifest=True`.
- [ ] Default CLI/MCP export behavior and existing audit-manifest outputs remain
  compatible.
- [ ] Docs state event logs remain opt-in local provenance metadata, not signed
  or immutable audit evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should event logs become mandatory for public release packaging? - Status:
  DEFERRED | Why it matters: this slice adds opt-in workflow coverage; release
  policy belongs in a separate signed/anchored audit plan.

---

## Notes

The MCP surface intentionally takes a boolean rather than a caller-supplied
path. That preserves the existing arbitrary-write defense for agent-driven
exports.
