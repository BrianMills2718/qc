# Plan #95: Export Audit Manifest Verification

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #94 export audit hash manifest
**Blocks:** useful export integrity preflight; future signed/append-only audit log

---

## Gap

**Current:** `make export-audit-manifest` writes a schema_version=1 hash
manifest for existing export artifacts. There is no deterministic verifier that
can later check whether the manifest still matches artifact bytes, sizes, its
own self-hash, or the current stored project state.

**Target:** Add manifest verification:

- Core: extend `qc_clean/core/export/audit_manifest.py` with verification
  report models and functions.
- Script: `scripts/verify_export_audit_manifest.py manifest.json --base-dir exports [--project-id <id>]`.
- Make: `make verify-export-audit-manifest MANIFEST=manifest.json [BASE_DIR=exports] [ID=<project_id>]`.

The verifier should emit JSON and exit nonzero when integrity checks fail.

**Why:** A hash manifest is only useful if agents can check it after handoff.
This remains local integrity/provenance metadata. It is not signing,
append-only logging, or a complete tamper-evident audit substrate.

---

## References Reviewed

- `docs/plans/completed/EXPORT_AUDIT_HASH_MANIFEST.md` - manifest fields,
  caveats, and deferred verification need.
- `qc_clean/core/export/audit_manifest.py` - manifest models and hash helpers.
- `scripts/write_export_audit_manifest.py` - project-store/script pattern.
- `tests/test_export_audit_manifest.py` - current manifest generation coverage.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research is needed. This is deterministic verification of hashes and
file metadata already recorded by Plan #94.

---

## Capabilities

| Capability | Input | Output | Consumer |
|------------|-------|--------|----------|
| `verify_export_audit_manifest_payload` | manifest JSON payload, optional base dir/state | verification report model | script, future handoff checks |
| `load_export_audit_manifest` | manifest JSON path | manifest model | verifier script |

---

## Files Affected

- `qc_clean/core/export/audit_manifest.py` (modify)
- `scripts/verify_export_audit_manifest.py` (create)
- `Makefile` (modify)
- `tests/test_export_audit_manifest.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/EXPORT_AUDIT_MANIFEST_VERIFICATION.md` (create, then move to completed)

---

## Plan

### Decisions

- Verification report status values are `verified` and `invalid`.
- Always verify manifest self-hash by recomputing the manifest hash with
  `manifest_sha256` blanked.
- Always verify artifact existence, byte size, and SHA-256. Artifact paths are
  resolved relative to `base_dir` when supplied; otherwise relative to the
  manifest file directory in the script.
- Verify `project_state_sha256` only when a `ProjectState` is supplied via
  `--project-id`; otherwise report that project-state verification was not run.
- Each failure is a structured item with code, path/field, expected, actual, and
  message.
- This plan does not sign manifests, append them to an immutable log, or make
  exporters write manifests automatically.

### Steps

1. Add verification report/failure models and verifier functions.
2. Add tests for successful verification, artifact hash mismatch, manifest
   self-hash mismatch, missing artifact, optional project-state mismatch, and
   script exit/output behavior.
3. Add `scripts/verify_export_audit_manifest.py`.
4. Add `make verify-export-audit-manifest`.
5. Update docs to say manifests can be verified, but full tamper-evident audit
   remains future work.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_export_audit_manifest.py` | `test_verify_export_audit_manifest_accepts_matching_files` | Matching manifest/files verifies with no failures. |
| `tests/test_export_audit_manifest.py` | `test_verify_export_audit_manifest_detects_artifact_hash_mismatch` | Mutated artifact produces hash/size failure. |
| `tests/test_export_audit_manifest.py` | `test_verify_export_audit_manifest_detects_manifest_hash_mismatch` | Tampered manifest metadata fails self-hash check. |
| `tests/test_export_audit_manifest.py` | `test_verify_export_audit_manifest_detects_project_state_mismatch` | Optional project-state check fails when current state hash differs. |
| `tests/test_export_audit_manifest.py` | `test_verify_export_audit_manifest_script` | Script emits JSON and exits nonzero on invalid manifest/files. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_export_audit_manifest.py -q` | Manifest generation and verification behavior. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Matching manifest/files verify with status `verified`.
- [ ] Manifest self-hash mismatch is detected.
- [ ] Missing or changed artifact files are detected with structured failures.
- [ ] Optional project-state hash mismatch is detected when `--project-id` is
  supplied.
- [ ] Script and Make target are agent-drivable and produce JSON.
- [ ] Docs state verification is local integrity checking, not signing or a
  complete tamper-evident audit substrate.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should verification be a mandatory preflight before publishing exports? -
  Status: DEFERRED | Why it matters: policy gating belongs after manifest
  generation and verification are both stable.

---

## Notes

Verification can detect changed files relative to a manifest. It cannot prove
the manifest itself is the canonical one unless a future signed or append-only
system protects the manifest.
