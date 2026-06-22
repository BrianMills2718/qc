# Plan #99: Export Audit Event Log

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Export audit manifest generation, verification, and publish preflight
**Blocks:** future signed/externally anchored audit log; stricter release packaging policy

---

## Outcome

Implemented an opt-in local hash-linked export audit event log:

- `qc_clean/core/export/audit_event_log.py` provides
  `append_export_audit_event` and `verify_export_audit_event_log`.
- `scripts/verify_export_audit_event_log.py` and
  `make verify-export-audit-log LOG=...` verify event self-hashes and
  previous-event links.
- `scripts/write_export_audit_manifest.py`,
  `scripts/verify_export_audit_manifest.py`, and
  `scripts/export_publish_preflight.py` accept `--audit-log`.
- Make targets for manifest write, manifest verify, and publish preflight pass
  optional `AUDIT_LOG=...`.
- `CLAUDE.md`, generated `AGENTS.md`, and
  `docs/PROJECT_THEORY_AND_GOALS.md` document event logs as local
  integrity/provenance metadata, not signing, immutable storage,
  methodological validity evidence, or a full tamper-evident audit substrate.

Implementation commit: `45ca13c`

## Verification

- TDD red: initial `python -m pytest tests/test_export_audit_event_log.py -q`
  failed with `ModuleNotFoundError: No module named
  'qc_clean.core.export.audit_event_log'`.
- Focused behavior: `python -m pytest tests/test_export_audit_event_log.py -q`
  -> 4 passed.
- Related regressions: `python -m pytest tests/test_export_publish_preflight.py
  tests/test_export_audit_manifest.py -q` -> 14 passed.
- Focused lint: `python -m ruff check
  qc_clean/core/export/audit_event_log.py
  scripts/verify_export_audit_event_log.py
  scripts/write_export_audit_manifest.py
  scripts/verify_export_audit_manifest.py scripts/export_publish_preflight.py
  tests/test_export_audit_event_log.py` -> all checks passed.
- Command discoverability: `make help` lists `verify-export-audit-log` and
  `AUDIT_LOG=...` on the three local audit operations.
- Documentation governance: `make docs-check` passed.
- Full gate: `make check` -> 877 passed, 1 skipped, 8 deselected; Ruff and
  docs-check passed; type check remains not configured.
- Commit `45ca13c` was pushed to `main`.

---

## Gap

**Current:** Export hash manifests can be written, verified, and required by a
publish/handoff preflight. Each command emits a point-in-time JSON report, but
there is no durable local sequence of export-audit events tying manifest writes,
verification attempts, and preflight outcomes together.

**Target:** Add an opt-in local event log for export-audit operations:

- Core: `qc_clean/core/export/audit_event_log.py`
- Script: `scripts/verify_export_audit_event_log.py LOG`
- Make: `make verify-export-audit-log LOG=export_audit_events.jsonl`
- Script integrations:
  - `scripts/write_export_audit_manifest.py --audit-log LOG`
  - `scripts/verify_export_audit_manifest.py --audit-log LOG`
  - `scripts/export_publish_preflight.py --audit-log LOG`

The log should be JSON Lines, hash-linked by event record, and verifiable by a
structured report. It must remain opt-in and must not change default export,
manifest, verifier, or preflight behavior.

**Why:** This creates a durable local provenance trail for export handoff
workflow operations. It narrows the audit-substrate gap while preserving claim
discipline: local hash chaining detects accidental edits and simple tampering
after the fact, but it is still not signing, immutable storage, external
timestamping, or methodological validity evidence.

---

## References Reviewed

- `qc_clean/core/export/audit_manifest.py` - manifest and verification report
  schemas, local hash helpers, and claim caveats.
- `qc_clean/core/export/publish_preflight.py` - strict preflight report and
  caveat language.
- `scripts/write_export_audit_manifest.py` - manifest write CLI integration
  point.
- `scripts/verify_export_audit_manifest.py` - manifest verification CLI
  integration point.
- `scripts/export_publish_preflight.py` - preflight CLI integration point.
- `docs/plans/completed/EXPORT_AUDIT_HASH_MANIFEST.md`
- `docs/plans/completed/EXPORT_AUDIT_MANIFEST_VERIFICATION.md`
- `docs/plans/completed/EXPORT_PUBLISH_PREFLIGHT.md`
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research is needed. This is a deterministic local provenance log
around existing export-audit commands. Signed transparency logs, external
timestamping, and immutable storage are deliberately out of scope.

---

## Capabilities

| Capability | Input | Output | Consumer |
|------------|-------|--------|----------|
| `append_export_audit_event` | log path, event type, status, manifest path, report payload | hash-linked event record | export-audit scripts |
| `verify_export_audit_event_log` | log path | structured verification report | script, Make target, future release gates |

---

## Files Affected

- `qc_clean/core/export/audit_event_log.py` (create)
- `scripts/verify_export_audit_event_log.py` (create)
- `scripts/write_export_audit_manifest.py` (modify)
- `scripts/verify_export_audit_manifest.py` (modify)
- `scripts/export_publish_preflight.py` (modify)
- `Makefile` (modify)
- `tests/test_export_audit_event_log.py` (create)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/EXPORT_AUDIT_EVENT_LOG.md` (create, then move to completed)

---

## Plan

### Decisions

- Event log format is JSON Lines, one event object per line.
- Event schema fields include `schema_version`, `package_type`, `event_type`,
  `event_status`, UTC timestamp, manifest path/hash when available, payload
  SHA-256, previous event hash, current event hash, and caveat.
- Event types are `manifest_written`, `manifest_verified`, and
  `publish_preflight`.
- The event hash is computed from the event with `event_sha256` blanked, using
  deterministic JSON serialization.
- `previous_event_sha256` is the prior valid line's `event_sha256`, or `null`
  for the first event.
- Verification checks JSONL shape, event self-hashes, and previous-hash links.
- `--audit-log` is opt-in. Existing script stdout JSON and exit semantics stay
  unchanged when the flag is absent.
- If `--audit-log` is supplied and the log cannot be appended, the command fails
  loudly rather than silently omitting the requested event.
- This slice does not write audit-log events from `qc_cli.py project export` or
  MCP export tools directly; those remain a follow-up after the local event-log
  contract is proven.

### Steps

1. Add event and verification report models plus append/verify functions.
2. Add TDD tests for hash linking, tamper detection, missing log failure, and
   script opt-in event writing.
3. Add verifier script and Make target.
4. Add `--audit-log` to the three local audit scripts.
5. Update docs conservatively.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_export_audit_event_log.py` | `test_export_audit_event_log_appends_hash_linked_events` | Multiple events are appended as hash-linked JSONL and verify as valid. |
| `tests/test_export_audit_event_log.py` | `test_export_audit_event_log_detects_modified_event` | Editing an existing event causes verification failure. |
| `tests/test_export_audit_event_log.py` | `test_export_audit_event_log_missing_file_fails` | Missing log verification fails loudly in the report/script. |
| `tests/test_export_audit_event_log.py` | `test_export_audit_scripts_write_opt_in_events` | Manifest write, manifest verify, and publish preflight scripts append the expected event types only when `--audit-log` is supplied. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_export_audit_event_log.py -q` | New event-log behavior. |
| `python -m pytest tests/test_export_publish_preflight.py tests/test_export_audit_manifest.py -q` | Existing manifest/preflight behavior remains compatible. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Event log appends schema_version=1 JSONL records with event hashes and
  previous-event links.
- [x] Event-log verifier detects malformed JSON, invalid event shapes,
  self-hash mismatches, and previous-link mismatches.
- [x] Manifest write, manifest verify, and publish preflight scripts support
  optional `--audit-log` without changing default behavior.
- [x] `make verify-export-audit-log LOG=...` is agent-drivable and emits JSON.
- [x] Docs state this is a local provenance/event-history aid, not signing,
  immutable storage, a full tamper-evident audit substrate, or validity
  evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should CLI/MCP export flows write audit events by default when audit
  manifests are requested? - Status: DEFERRED | Why it matters: this first
  slice proves the local event-log contract; default release/package policy is a
  separate decision.

---

## Notes

This is deliberately not called a full tamper-evident audit log. A local
hash-linked JSONL file can detect many accidental or naive modifications, but it
can still be rewritten by anyone with filesystem access unless a future slice
adds signing, external anchoring, or append-only storage.
