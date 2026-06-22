# Plan #96: Export Audit CLI Integration

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #94 export audit hash manifest; Plan #95 manifest verification
**Blocks:** lower-friction export integrity handoffs; future strict publish preflight

---

## Gap

**Current:** Agents can create and verify export-audit manifests through separate
Make/script targets after running `qc_cli.py project export`. The project export
command itself does not offer an opt-in sidecar manifest path, so agents must
remember a second command and manually pass the artifact list.

**Target:** Add optional CLI integration to `qc_cli.py project export`:

- `--audit-manifest manifest.json`: after a successful export, write an export
  hash manifest for the produced artifact path(s).
- `--verify-audit-manifest`: immediately verify the manifest against those
  artifact bytes and the current project state; exit nonzero if verification
  fails.

Default export behavior must remain unchanged when these flags are absent.

**Why:** This makes export integrity recording agent-drivable from the export
workflow itself without making manifests mandatory or claiming a full
tamper-evident audit log.

---

## References Reviewed

- `qc_cli.py` - `project export` parser flags.
- `qc_clean/core/cli/commands/project.py` - `_export_project` command handler.
- `qc_clean/core/export/audit_manifest.py` - manifest build/write/verify
  functions.
- `tests/test_project_commands.py` - project export command tests.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research is needed. This is deterministic CLI integration for
already-built manifest generation and verification.

---

## Capabilities

This plan wires existing export-audit capabilities into the project export CLI;
it does not create a new cross-project capability.

---

## Files Affected

- `qc_cli.py` (modify)
- `qc_clean/core/cli/commands/project.py` (modify)
- `tests/test_project_commands.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/EXPORT_AUDIT_CLI_INTEGRATION.md` (create, then move to completed)

---

## Plan

### Decisions

- `--audit-manifest` is optional; no default sidecar is written.
- `--verify-audit-manifest` requires `--audit-manifest`, because there is
  nothing to verify otherwise.
- For CSV exports, all returned CSV paths are included in the manifest.
- For JSON/Markdown/QDPX exports, the single returned file path is included.
- Manifest base directory is the parent of the manifest file by default, so
  artifact paths are relative when the manifest sits beside the artifacts.
- Verification uses the current in-memory `ProjectState` loaded for export.
- This plan does not add signing, append-only storage, or mandatory publish
  gates.

### Steps

1. Add parser flags to `qc_cli.py project export`.
2. Refactor `_export_project` to track produced artifact paths for each format.
3. If `--audit-manifest` is supplied, build/write the manifest.
4. If `--verify-audit-manifest` is supplied, verify immediately and fail loud on
   invalid verification.
5. Add command-handler tests for JSON and CSV manifest creation, default
   unchanged behavior, and verify-without-manifest failure.
6. Update docs conservatively.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_project_commands.py` | `test_project_export_command_writes_audit_manifest_for_json` | JSON export can write a manifest sidecar with the exported file. |
| `tests/test_project_commands.py` | `test_project_export_command_writes_audit_manifest_for_csv` | CSV export manifest includes all CSV artifact paths. |
| `tests/test_project_commands.py` | `test_project_export_command_rejects_verify_without_manifest` | Verification flag without manifest path fails loud. |
| `tests/test_project_commands.py` | `test_project_export_command_verifies_audit_manifest` | Export can write and immediately verify a manifest. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_project_commands.py -q` | CLI export command behavior remains compatible. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Default `project export` behavior remains unchanged without audit flags.
- [ ] JSON/Markdown/QDPX exports can write a one-artifact manifest.
- [ ] CSV exports can write a manifest containing every returned CSV artifact.
- [ ] `--verify-audit-manifest` verifies immediately and fails loud on invalid
  verification.
- [ ] `--verify-audit-manifest` without `--audit-manifest` exits nonzero.
- [ ] Docs state CLI integration is optional integrity/provenance metadata, not
  a full tamper-evident audit log.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should exports eventually write manifests by default? - Status: DEFERRED |
  Why it matters: default sidecars change user-visible output contracts and
  should wait for a publish/export policy decision.

---

## Notes

This is convenience integration for existing manifest functionality. It does not
make export artifacts tamper-evident unless a future signed or append-only store
protects the manifest itself.
