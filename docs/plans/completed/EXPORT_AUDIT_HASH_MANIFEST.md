# Plan #94: Export Audit Hash Manifest

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Existing JSON/CSV/Markdown/QDPX export surfaces
**Blocks:** tamper-evident audit substrate first slices; reproducible handoffs

---

## Outcome

Implemented schema_version=1 export-audit hash manifests for existing
JSON/CSV/Markdown/QDPX export artifacts. The manifest records export format,
project ID/name, deterministic project-state SHA-256, per-artifact relative path
when a base directory is supplied, size, artifact SHA-256, artifact count,
manifest SHA-256, and a caveat that this is local integrity/provenance metadata
only. Added:

- `qc_clean/core/export/audit_manifest.py`
- `scripts/write_export_audit_manifest.py`
- `make export-audit-manifest ID=<project_id> FORMAT=markdown ARTIFACTS="report.md" OUTPUT=manifest.json`

Implementation commit: `3a1c230`

## Verification

- TDD red check: `python -m pytest tests/test_export_audit_manifest.py -q`
  initially failed with `ModuleNotFoundError: No module named
  'qc_clean.core.export.audit_manifest'`.
- Focused pass: `python -m pytest tests/test_export_audit_manifest.py -q` →
  `4 passed`.
- Focused lint: `python -m ruff check qc_clean/core/export/audit_manifest.py scripts/write_export_audit_manifest.py tests/test_export_audit_manifest.py` →
  `All checks passed!`
- Make target discovery: `make help` lists `export-audit-manifest`.
- Docs gate: `make docs-check` passed.
- Full gate: `make check` → `854 passed, 1 skipped, 8 deselected`; Ruff and
  docs checks passed.
- Type-check status: `make check` reports `Type check not yet configured`.

---

## Gap

**Current:** `ProjectExporter` can write JSON, CSV, Markdown, and QDPX outputs,
and Phase 0 benchmark packages have manifest hashes. Ordinary project exports
still return file paths only. After a handoff, there is no deterministic
sidecar recording which exported files were produced from which project state
and what their SHA-256 hashes were.

**Target:** Add a standalone export-audit manifest builder that can hash any
already-written export artifacts without changing the existing export output
contracts:

- Core: `qc_clean/core/export/audit_manifest.py`
- Script: `scripts/write_export_audit_manifest.py <project_id> --format markdown --artifact report.md --output manifest.json`
- Make: `make export-audit-manifest ID=<project_id> FORMAT=markdown ARTIFACTS="report.md" OUTPUT=manifest.json`

The manifest should include schema version, package type, export format, project
ID/name, project-state hash, per-artifact relative paths, sizes, SHA-256 hashes,
and a manifest SHA-256 over the content excluding its own hash.

**Why:** This is a small first slice toward tamper-evident auditability. It
gives agents and humans a deterministic integrity record for exported artifacts,
while explicitly not claiming append-only logging, cryptographic signing, or a
complete audit trail.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - limitation and roadmap item for
  tamper-evident audit substrate.
- `qc_clean/core/export/data_exporter.py` - current JSON/CSV/Markdown/QDPX
  export methods and return contracts.
- `qc_clean/core/bench.py` and `scripts/bench_phase0.py` - existing Phase 0
  hashing/manifest patterns.
- `tests/test_qdpx_export.py`, `tests/test_project_commands.py`,
  `tests/test_claim_ledger_exports.py` - export behavior that must not regress.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research is needed. This is deterministic hash/provenance metadata
over local files. It is not a full audit architecture.

---

## Capabilities

| Capability | Input | Output | Consumer |
|------------|-------|--------|----------|
| `build_export_audit_manifest` | `ProjectState`, export format, artifact paths | manifest model | script, future export preflight |
| `write_export_audit_manifest` | manifest model/output path | manifest JSON path | Make/script surface |

---

## Files Affected

- `qc_clean/core/export/audit_manifest.py` (create)
- `scripts/write_export_audit_manifest.py` (create)
- `Makefile` (modify)
- `tests/test_export_audit_manifest.py` (create)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/EXPORT_AUDIT_HASH_MANIFEST.md` (create, then move to completed)

---

## Plan

### Decisions

- This plan does not change the existing `ProjectExporter` methods or CLI export
  return contracts.
- Artifact paths must exist and must be files; missing directories or missing
  files fail loudly with `ValueError`.
- Manifest paths are recorded relative to a caller-supplied base directory when
  possible; otherwise they are recorded as provided/resolved paths.
- Manifest hash is computed from a deterministic JSON payload with
  `manifest_sha256` excluded.
- The script exits nonzero and prints JSON error payloads on missing projects or
  invalid artifact paths.
- This is integrity/provenance metadata only, not signing, append-only storage,
  or tamper-evident logging.

### Steps

1. Add manifest Pydantic models and hash helpers in
   `qc_clean/core/export/audit_manifest.py`.
2. Add focused tests for single-file and multi-file manifests, stable manifest
   hash, missing artifact failure, and script output/exit behavior.
3. Add `scripts/write_export_audit_manifest.py`.
4. Add `make export-audit-manifest`.
5. Update docs to state export audit manifests exist but full tamper-evident
   audit remains future work.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_export_audit_manifest.py` | `test_build_export_audit_manifest_hashes_single_artifact` | Manifest records project hash, artifact size, artifact SHA, and manifest SHA. |
| `tests/test_export_audit_manifest.py` | `test_build_export_audit_manifest_hashes_multiple_csv_artifacts` | Multi-file exports are recorded in deterministic path order. |
| `tests/test_export_audit_manifest.py` | `test_build_export_audit_manifest_rejects_missing_artifact` | Missing artifact path fails loudly. |
| `tests/test_export_audit_manifest.py` | `test_write_export_audit_manifest_script` | Script emits manifest JSON, writes output, and exits nonzero on invalid artifact paths. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_export_audit_manifest.py -q` | New manifest behavior. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Manifest records schema version, package type, export format, project ID,
  project name, project-state SHA-256, artifact count, per-file size/SHA-256,
  caveat, and manifest SHA-256.
- [x] Artifact ordering is deterministic.
- [x] Missing artifact paths fail loudly.
- [x] Script and Make target are agent-drivable and produce JSON.
- [x] Existing export output contracts remain unchanged.
- [x] Docs state this is integrity/provenance metadata, not a full
  tamper-evident audit substrate.

> Process criteria:
- [x] Required focused tests pass.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should exporters write manifests automatically? - Status: DEFERRED | Why
  it matters: automatic sidecars change output contracts and should be a
  separate strict/export-policy decision.
- [x] Should manifests be signed or appended to an immutable log? - Status:
  DEFERRED | Why it matters: that is the real tamper-evident substrate, not this
  first hash-manifest slice.

---

## Notes

Do not call this tamper-evident auditability. A hash manifest helps detect file
changes after export, but it can be replaced unless a future append-only/signed
log makes replacement evident.
