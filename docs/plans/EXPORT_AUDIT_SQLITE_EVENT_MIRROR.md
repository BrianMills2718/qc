# Plan #161: Export Audit SQLite Event Mirror

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Export audit event log
**Blocks:** future DB-backed audit workflow integration; future signed/external audit anchoring

---

## Gap

**Current:** Export audit events can be appended to a local hash-linked JSONL log
and verified with `make verify-export-audit-log`. The roadmap still lists
optional DB-backed audit events as a remaining audit-substrate slice.

**Target:** Add an opt-in local SQLite mirror for existing export audit JSONL
events:

- A script/Make target imports a verified JSONL event log into a SQLite table.
- A verifier script/Make target checks the SQLite table's event payload hashes,
  previous-event links, duplicate event hashes, and row ordering.
- Import fails loud when the source JSONL log does not verify.
- Default export behavior remains unchanged.

**Why:** SQLite makes local audit events queryable and easier for agents to
inspect across handoff workflows without claiming signed, immutable, external,
or append-only storage semantics.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 item 11 - optional DB-backed audit
  events remain.
- `qc_clean/core/export/audit_event_log.py` - current event model, append, and
  JSONL verification.
- `scripts/verify_export_audit_event_log.py` - current verifier script shape.
- `tests/test_export_audit_event_log.py` - current event-log tests.
- `Makefile` - current audit targets.
- Memory context:
  `agent-memory recall 'audit substrate DB-backed audit events qualitative_coding' --project qualitative_coding`
  - 2 low-relevance historical findings, no active conflicting decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this adds project-local CLI/Make audit tooling and does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/export/audit_event_log.py` - add SQLite mirror and verification
  helpers.
- `scripts/mirror_export_audit_event_log_db.py` - import verified JSONL events
  into SQLite.
- `scripts/verify_export_audit_event_db.py` - verify the SQLite mirror.
- `tests/test_export_audit_event_db.py` - regressions for import/verify/failure
  behavior.
- `Makefile` - add `mirror-export-audit-db` and `verify-export-audit-db`.
- `CLAUDE.md` - update audit-substrate current-state wording.
- `docs/PROJECT_THEORY_AND_GOALS.md` - update audit roadmap/status wording.
- `AGENTS.md` - regenerated after `CLAUDE.md` changes.

---

## Plan

### Steps

1. Add tests for mirroring a verified JSONL event log into SQLite and verifying
   the resulting DB.
2. Add tests proving invalid JSONL logs fail before DB writes.
3. Add tests proving SQLite tampering is detected by the DB verifier.
4. Implement SQLite schema creation, import, and verification helpers in the
   existing audit event-log module.
5. Add script and Make targets.
6. Update docs and run focused/full gates.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_export_audit_event_db.py` | `test_export_audit_event_log_can_be_mirrored_to_sqlite` | Verified JSONL events import into SQLite and DB verification passes |
| `tests/test_export_audit_event_db.py` | `test_export_audit_event_db_mirror_rejects_invalid_source_log` | Invalid JSONL source logs fail loud before DB writes |
| `tests/test_export_audit_event_db.py` | `test_export_audit_event_db_verifier_detects_tampered_payload` | DB verifier detects modified stored event payloads |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_export_audit_event_log.py tests/test_export_audit_event_db.py -q` | Audit event log behavior remains compatible |
| `make docs-check` | AGENTS sync and plan docs remain valid |
| `make check` | Full deterministic gate remains green |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] Verified JSONL export audit events can be mirrored into SQLite.
- [ ] SQLite verification checks event shape, self-hashes, previous-event links,
  duplicate event hashes, and row ordering.
- [ ] Invalid source JSONL logs fail before SQLite import mutates the DB.
- [ ] Make targets expose the mirror and verifier workflows.
- [ ] Docs preserve the local-only caveat and do not call this a full
  tamper-evident audit log.

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

This slice intentionally mirrors existing JSONL events rather than making the
database the default export-audit sink. Default export behavior and MCP
confinement remain unchanged.
