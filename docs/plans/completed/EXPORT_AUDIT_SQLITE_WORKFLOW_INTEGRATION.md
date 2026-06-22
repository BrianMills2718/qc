# Plan #162: Export Audit SQLite Workflow Integration

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Export audit SQLite event mirror
**Blocks:** future signed/external audit anchoring

---

## Outcome

Local export-audit workflows can now update the optional SQLite event mirror as
part of the same operation that appends JSONL audit events:

- `scripts/write_export_audit_manifest.py --audit-log ... --audit-db ...`
- `scripts/verify_export_audit_manifest.py --audit-log ... --audit-db ...`
- `scripts/export_publish_preflight.py --audit-log ... --audit-db ...`
- `make export-audit-manifest ... AUDIT_LOG=... AUDIT_DB=...`
- `make verify-export-audit-manifest ... AUDIT_LOG=... AUDIT_DB=...`
- `make export-publish-preflight ... AUDIT_LOG=... AUDIT_DB=...`
- `qc_cli.py project export ... --audit-manifest ... --audit-log ... --audit-db ...`

`--audit-db` / `AUDIT_DB` requires the JSONL event log, so SQLite remains a
mirror rather than a standalone source of truth. Default export behavior remains
unchanged when the audit DB flag is absent. MCP SQLite mirror integration remains
future work because it needs a separate confined output naming policy.

This is local provenance/queryability infrastructure only: it is not signing,
immutable storage, external timestamping, append-only infrastructure,
methodological validity evidence, or a full tamper-evident audit log.

Implementation commit: `93ca01d`

## Verification

- TDD red: focused tests initially failed for missing `--audit-db` script/parser
  support and missing `project export` DB mirror behavior.
- `python -m pytest tests/test_export_audit_event_log.py tests/test_export_audit_event_db.py tests/test_project_commands.py -q`
  -> 60 passed.
- `python -m ruff check qc_clean/core/cli/commands/project.py qc_cli.py
  scripts/write_export_audit_manifest.py scripts/verify_export_audit_manifest.py
  scripts/export_publish_preflight.py tests/test_export_audit_event_log.py
  tests/test_project_commands.py` -> all checks passed.
- `make docs-check` passed.
- `git diff --check` passed.
- `make help` lists `AUDIT_DB` on existing audit targets.
- `make check` -> 1118 passed, 1 skipped, 8 deselected; Ruff and docs-check
  passed; type check remains not configured.
- Commit `93ca01d` was pushed to `main`.

---

## Gap

**Current:** `make mirror-export-audit-db` can mirror a verified JSONL audit event
log into SQLite after the fact. Existing export-audit workflows can append JSONL
events, but they cannot opt into updating the SQLite mirror as part of the same
workflow.

**Target:** Add optional SQLite mirror integration to the existing CLI/script
audit workflows:

- `scripts/write_export_audit_manifest.py --audit-log events.jsonl --audit-db events.sqlite`
- `scripts/verify_export_audit_manifest.py --audit-log events.jsonl --audit-db events.sqlite`
- `scripts/export_publish_preflight.py --audit-log events.jsonl --audit-db events.sqlite`
- `make export-audit-manifest ... AUDIT_LOG=... AUDIT_DB=...`
- `make verify-export-audit-manifest ... AUDIT_LOG=... AUDIT_DB=...`
- `make export-publish-preflight ... AUDIT_LOG=... AUDIT_DB=...`
- `qc_cli.py project export ... --audit-manifest ... --audit-log events.jsonl --audit-db events.sqlite`

`--audit-db` / `AUDIT_DB` must require the JSONL event log. Default export
behavior remains unchanged, and the database remains a mirror rather than the
source of truth.

**Why:** Agents already call the export-audit workflows. Mirroring SQLite during
those workflows makes DB-backed local audit inspection available without a
manual follow-up step and without making DB logging default.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 item 11 - current audit-substrate
  status and caveats.
- `qc_clean/core/export/audit_event_log.py` - SQLite mirror and verifier helpers.
- `scripts/write_export_audit_manifest.py` - manifest write audit event path.
- `scripts/verify_export_audit_manifest.py` - manifest verification audit event
  path.
- `scripts/export_publish_preflight.py` - publish preflight audit event path.
- `qc_clean/core/cli/commands/project.py` - `project export` manifest/log
  integration.
- `qc_cli.py` - top-level export parser flags.
- `tests/test_export_audit_event_log.py`,
  `tests/test_export_audit_event_db.py`, and `tests/test_project_commands.py`
  - current audit workflow coverage.
- Memory context:
  `agent-memory recall 'export audit SQLite integration audit db CLI scripts qualitative_coding' --project qualitative_coding`
  - 2 low-relevance historical findings, no active conflicting decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this adds project-local CLI/Make audit workflow integration and does
not create a cross-project callable capability.

---

## Files Affected

- `qc_clean/core/cli/commands/project.py` - add optional audit DB mirror after
  export-audit event appends.
- `qc_cli.py` - add `--audit-db` parser flag.
- `scripts/write_export_audit_manifest.py` - accept and apply `--audit-db`.
- `scripts/verify_export_audit_manifest.py` - accept and apply `--audit-db`.
- `scripts/export_publish_preflight.py` - accept and apply `--audit-db`.
- `Makefile` - pass `AUDIT_DB` through existing audit targets.
- `tests/test_export_audit_event_log.py` - extend script workflow coverage.
- `tests/test_project_commands.py` - add CLI parser/command coverage.
- `CLAUDE.md`, `AGENTS.md`, and `docs/PROJECT_THEORY_AND_GOALS.md` - status
  wording.

---

## Plan

### Steps

1. Add tests proving audit scripts update SQLite when both `--audit-log` and
   `--audit-db` are supplied.
2. Add tests proving scripts reject `--audit-db` without `--audit-log`.
3. Add CLI parser and `project export` tests for `--audit-db` and the same
   dependency guard.
4. Implement a small helper that mirrors the JSONL log to SQLite after audit
   event appends.
5. Wire scripts, CLI, and Make targets.
6. Update docs and run focused/full gates.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_export_audit_event_log.py` | extend `test_export_audit_scripts_write_opt_in_events` | Existing scripts update SQLite mirror when `--audit-db` is supplied |
| `tests/test_export_audit_event_log.py` | `test_export_audit_scripts_reject_audit_db_without_log` | Scripts fail loud when `--audit-db` is supplied without `--audit-log` |
| `tests/test_project_commands.py` | `test_project_export_command_writes_audit_event_db` | `project export` writes and verifies SQLite mirror when audit manifest/log/db are supplied |
| `tests/test_project_commands.py` | `test_project_export_command_rejects_audit_db_without_log` | `project export --audit-db` requires `--audit-log` |
| `tests/test_project_commands.py` | `test_export_subparser_audit_db_flag` | Parser accepts the new flag |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_export_audit_event_log.py tests/test_export_audit_event_db.py tests/test_project_commands.py -q` | Audit and project export surfaces remain compatible |
| `make docs-check` | AGENTS sync and plan docs remain valid |
| `make check` | Full deterministic gate remains green |

---

## Acceptance Criteria

Feature-level criteria:

- [x] Audit scripts mirror JSONL events into SQLite when `--audit-log` and
  `--audit-db` are supplied.
- [x] `project export` mirrors JSONL events into SQLite when `--audit-manifest`,
  `--audit-log`, and `--audit-db` are supplied.
- [x] `--audit-db` / `AUDIT_DB` fails loud without `--audit-log` / `AUDIT_LOG`.
- [x] Existing defaults remain unchanged when audit DB flags are absent.
- [x] Docs preserve the local mirror caveat and do not call this append-only or
  tamper-evident storage.

Process criteria:

- [x] Required focused tests pass.
- [x] `make docs-check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Open Questions

- [ ] None.

---

## Notes

MCP export DB integration remains a separate slice because MCP path confinement
needs its own confined output naming policy. This plan covers local CLI and
script workflows only.
