# Plan #97: MCP Export Audit Integration

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #94 export audit hash manifest; Plan #95 manifest verification; Plan #96 CLI integration
**Blocks:** agent-facing export integrity handoffs

---

## Gap

**Current:** `qc_export_markdown` and `qc_export_json` are the agent-facing MCP
export tools. They can write the export artifact into the confined MCP exports
directory, but they cannot write or verify an export-audit sidecar. Agents using
MCP must remember to call separate scripts outside the tool surface.

**Target:** Add optional MCP export audit sidecars:

- `qc_export_markdown(project_id, output_file=None, audit_manifest=False, verify_audit_manifest=False)`
- `qc_export_json(project_id, output_file=None, audit_manifest=False, verify_audit_manifest=False)`

Default return payloads must remain unchanged when `audit_manifest=False`. When
enabled, the manifest path is also confined to `EXPORTS_DIR`. Immediate
verification is optional and fails loud via an error payload.

**Why:** MCP is the agent-facing workflow. Export integrity metadata should be
available there without weakening the existing export sandbox or changing
default tool contracts.

---

## References Reviewed

- `qc_mcp_server.py` - `qc_export_markdown`, `qc_export_json`, and
  `_confine_export_path`.
- `tests/test_mcp_server.py` - existing MCP export tests and export confinement
  tests.
- `qc_clean/core/export/audit_manifest.py` - manifest build/write/verify
  functions.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research is needed. This is deterministic integration of existing
manifest functionality into the existing sandboxed MCP export tools.

---

## Capabilities

This plan wires existing export-audit capabilities into MCP export tools; it
does not create a new boundary.

---

## Files Affected

- `qc_mcp_server.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/MCP_EXPORT_AUDIT_INTEGRATION.md` (create, then move to completed)

---

## Plan

### Decisions

- Default `qc_export_markdown(project_id, output_file)` and
  `qc_export_json(project_id, output_file)` return payloads stay unchanged.
- `verify_audit_manifest=True` requires `audit_manifest=True`.
- Manifest filenames are derived from the confined export path:
  `<export_stem>.manifest.json`, also inside `EXPORTS_DIR`.
- The returned payload includes `audit_manifest` when written and
  `audit_verification` when immediate verification is requested.
- This plan does not add MCP CSV/QDPX export tools.
- This plan does not add signing or append-only storage.

### Steps

1. Add a small shared MCP helper that writes and optionally verifies an export
   audit manifest for one exported artifact.
2. Extend `qc_export_markdown` and `qc_export_json` signatures with optional
   `audit_manifest` and `verify_audit_manifest` booleans.
3. Preserve default response payloads when `audit_manifest=False`.
4. Add tests for default compatibility, manifest sidecar creation, verification
   success, verify-without-manifest error, and confinement of manifest paths.
5. Update docs conservatively.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_mcp_server.py` | `test_export_markdown_with_audit_manifest` | Markdown MCP export can write a confined manifest sidecar. |
| `tests/test_mcp_server.py` | `test_export_json_with_audit_manifest_verification` | JSON MCP export can write and immediately verify a sidecar. |
| `tests/test_mcp_server.py` | `test_export_verify_requires_audit_manifest` | Verify flag without manifest flag returns an error payload. |
| `tests/test_mcp_export_confinement.py` | `test_confine_export_manifest_stays_in_exports_dir` | Derived manifest names stay inside `EXPORTS_DIR`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_mcp_server.py tests/test_mcp_export_confinement.py -q` | MCP export behavior and confinement. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Default MCP export responses remain unchanged when audit flags are absent.
- [ ] Markdown and JSON MCP exports can write confined manifest sidecars.
- [ ] Immediate verification reports success/failure when requested.
- [ ] Verify without manifest returns an error payload.
- [ ] Manifest paths cannot escape `EXPORTS_DIR`.
- [ ] Docs state MCP integration is optional integrity/provenance metadata, not
  a full tamper-evident audit log.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should MCP grow CSV/QDPX export tools? - Status: DEFERRED | Why it
  matters: this plan only hardens existing MCP export surfaces.

---

## Notes

Preserve the MCP export sandbox. No user-supplied manifest path should be able
to write outside `EXPORTS_DIR`.
