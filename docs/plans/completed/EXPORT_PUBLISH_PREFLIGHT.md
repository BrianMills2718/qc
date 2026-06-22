# Plan #98: Export Publish Preflight

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Export audit manifest generation and verification
**Blocks:** explicit publish/handoff policy gate; future signed/append-only audit log

---

## Outcome

Implemented a strict local export publish/handoff preflight:

- `qc_clean/core/export/publish_preflight.py` exposes
  `run_export_publish_preflight`.
- `scripts/export_publish_preflight.py` emits JSON and exits nonzero on missing
  manifests, invalid manifests, or failed manifest/artifact/project-state
  verification.
- `make export-publish-preflight MANIFEST=... [BASE_DIR=...] [ID=...]` provides
  the agent-drivable gate.
- `CLAUDE.md`, generated `AGENTS.md`, and
  `docs/PROJECT_THEORY_AND_GOALS.md` document the command as local
  integrity/provenance metadata, not signing, append-only logging,
  methodological validity evidence, or a full tamper-evident audit substrate.

Implementation commit: `d135d35`

## Verification

- TDD red: initial `python -m pytest tests/test_export_publish_preflight.py -q`
  failed with `ModuleNotFoundError: No module named
  'qc_clean.core.export.publish_preflight'`.
- Focused behavior: `python -m pytest tests/test_export_publish_preflight.py -q`
  -> 5 passed.
- Focused lint: `python -m ruff check
  qc_clean/core/export/publish_preflight.py
  scripts/export_publish_preflight.py tests/test_export_publish_preflight.py`
  -> all checks passed.
- Command discoverability: `make help` lists `export-publish-preflight`.
- Documentation governance: `make docs-check` passed.
- Full gate: `make check` -> 873 passed, 1 skipped, 8 deselected; Ruff and
  docs-check passed; type check remains not configured.
- Commit `d135d35` was pushed to `main`.

---

## Gap

**Current:** Export manifests can be written and verified through Make/scripts,
CLI export flags, and MCP export flags. There is still no single strict
preflight command that says "this export package is ready for handoff only if
the export-audit manifest verifies." Agents must know which verifier output
counts as a pass.

**Target:** Add an explicit publish preflight:

- Core: `qc_clean/core/export/publish_preflight.py`
- Script: `scripts/export_publish_preflight.py --manifest manifest.json [--base-dir exports] [--project-id <id>]`
- Make: `make export-publish-preflight MANIFEST=manifest.json [BASE_DIR=exports] [ID=<project_id>]`

The preflight should require a valid export-audit manifest, emit a JSON report,
and exit nonzero on missing/invalid manifests or failed artifact/project-state
verification.

**Why:** This creates an explicit policy gate for handoff/publish workflows
without changing default export behavior or claiming a signed/append-only audit
substrate.

---

## References Reviewed

- `qc_clean/core/export/audit_manifest.py` - manifest verification report.
- `scripts/verify_export_audit_manifest.py` - current verifier CLI behavior.
- `docs/PROJECT_THEORY_AND_GOALS.md` - audit-substrate caveat and roadmap.
- `docs/plans/completed/EXPORT_AUDIT_HASH_MANIFEST.md`
- `docs/plans/completed/EXPORT_AUDIT_MANIFEST_VERIFICATION.md`
- `docs/plans/completed/EXPORT_AUDIT_CLI_INTEGRATION.md`
- `docs/plans/completed/MCP_EXPORT_AUDIT_INTEGRATION.md`
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research is needed. This is a deterministic preflight policy wrapper
around existing local hash verification.

---

## Capabilities

| Capability | Input | Output | Consumer |
|------------|-------|--------|----------|
| `run_export_publish_preflight` | manifest path, optional base dir/current state | publish preflight report | script, Make target, future publish workflows |

---

## Files Affected

- `qc_clean/core/export/publish_preflight.py` (create)
- `scripts/export_publish_preflight.py` (create)
- `Makefile` (modify)
- `tests/test_export_publish_preflight.py` (create)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/EXPORT_PUBLISH_PREFLIGHT.md` (create, then move to completed)

---

## Plan

### Decisions

- Preflight status values: `pass` and `fail`.
- Preflight requires a manifest path; it does not infer or create manifests.
- Preflight delegates all hash checking to
  `verify_export_audit_manifest_payload`.
- Preflight passes only when manifest verification status is `verified`.
- Project-state hash checking runs only when `--project-id` is supplied.
- The report includes a caveat: this is a local handoff integrity preflight, not
  signing, append-only logging, or methodological validity evidence.
- This plan does not make preflight mandatory for all exports.

### Steps

1. Add preflight report model and core function.
2. Add tests for pass, invalid artifact, missing manifest, optional
   project-state checking, and script exit codes.
3. Add script and Make target.
4. Update docs conservatively.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_export_publish_preflight.py` | `test_export_publish_preflight_passes_with_verified_manifest` | Valid manifest/files produce preflight pass. |
| `tests/test_export_publish_preflight.py` | `test_export_publish_preflight_fails_when_artifact_changes` | Mutated artifact produces preflight fail with verifier failures. |
| `tests/test_export_publish_preflight.py` | `test_export_publish_preflight_fails_missing_manifest` | Missing manifest path fails loud in report/script. |
| `tests/test_export_publish_preflight.py` | `test_export_publish_preflight_checks_project_state_when_supplied` | Project-state mismatch fails when state is supplied. |
| `tests/test_export_publish_preflight.py` | `test_export_publish_preflight_script_exit_codes` | Script exits 0 on pass and 1 on fail. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_export_publish_preflight.py -q` | New preflight behavior. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Preflight requires an existing manifest and fails if missing.
- [x] Preflight passes only when export-audit manifest verification is
  `verified`.
- [x] Preflight propagates structured verifier failures.
- [x] Optional project-state hash checking is supported.
- [x] Script and Make target are agent-drivable and emit JSON.
- [x] Docs state this is an explicit local publish/handoff integrity gate, not a
  default export behavior and not a full tamper-evident audit substrate.

> Process criteria:
- [x] Required focused tests pass.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should preflight become mandatory for public release packaging? - Status:
  DEFERRED | Why it matters: this slice provides the gate; release policy should
  be a separate decision.

---

## Notes

This is a policy wrapper around local hash verification. It can prevent
accidental handoff with stale/mutated artifacts, but it still does not prove a
manifest is canonical without a future signed or append-only audit store.
