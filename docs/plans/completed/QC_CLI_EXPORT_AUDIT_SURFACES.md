# Plan #194: QC CLI Export Audit Surfaces

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Existing export-audit scripts and Make targets
**Blocks:** Top-level CLI parity for export manifest and local audit workflows

---

## Outcome

Implementation commit: `b22540f2`

`qc_cli.py` now exposes six top-level export-audit wrappers:

- `export-audit-manifest <project_id> --format <format> --artifact <path>... --output <manifest>`
- `verify-export-audit-manifest <manifest>`
- `export-publish-preflight --manifest <manifest>`
- `verify-export-audit-log <log>`
- `mirror-export-audit-db <log> --db <sqlite>`
- `verify-export-audit-db <sqlite>`

Each wrapper delegates directly to the matching canonical script `main()` and
forwards positional paths, repeated artifacts, and optional audit/project flags
without reimplementing manifest, event-log, or SQLite verification logic.
Documentation identifies these as local integrity/provenance surfaces only,
not signing, append-only storage, external tamper evidence, methodological
validity, or SOTA support.

Verification:

- TDD red state observed: the new wrapper test failed six cases with
  invalid-command parser errors before implementation.
- Focused tests:
  `python -m pytest tests/test_qc_cli_export_audit_surfaces.py tests/test_export_audit_manifest.py tests/test_export_audit_event_log.py tests/test_export_audit_event_db.py -q`
  -> `23 passed`.
- Focused Ruff:
  `python -m ruff check qc_cli.py tests/test_qc_cli_export_audit_surfaces.py`
  -> passed.
- `make docs-check` -> passed.
- `git diff --check` -> passed.
- `make check` -> `1243 passed, 1 skipped, 8 deselected`; Ruff and docs gates
  passed; type check is still not configured.

---

## Gap

**Current:** Export audit workflows are agent-drivable through Make targets and
scripts:

- `make export-audit-manifest`
- `make verify-export-audit-manifest`
- `make export-publish-preflight`
- `make verify-export-audit-log`
- `make mirror-export-audit-db`
- `make verify-export-audit-db`

`qc_cli.py project export` can write audit artifacts during export, but the
standalone local verification/manifold workflows are not exposed as top-level
`qc_cli.py` commands.

**Target:** Add six thin `qc_cli.py` wrappers:

- `export-audit-manifest <project_id> --format <format> --artifact <path>... --output <manifest>`
- `verify-export-audit-manifest <manifest>`
- `export-publish-preflight --manifest <manifest>`
- `verify-export-audit-log <log>`
- `mirror-export-audit-db <log> --db <sqlite>`
- `verify-export-audit-db <sqlite>`

Each wrapper must delegate to the matching canonical script `main()` with exact
argv forwarding.

**Why:** Export integrity/provenance checks should be runnable from the
canonical CLI without requiring operators or agents to remember script paths.
This closes a parity gap in the already-built export-audit substrate.

**Non-target:** This slice does not change export manifest schema, event-log
schema, SQLite mirror schema, verification semantics, append-only guarantees,
signing/external storage, `project export`, Make targets, or default export
policy. It does not make the audit substrate tamper-evident beyond existing
local hash verification and event-log checks.

---

## References Reviewed

- `scripts/write_export_audit_manifest.py` - manifest writer CLI contract.
- `scripts/verify_export_audit_manifest.py` - manifest verifier CLI contract.
- `scripts/export_publish_preflight.py` - publish/handoff preflight CLI
  contract.
- `scripts/verify_export_audit_event_log.py` - JSONL event-log verifier CLI
  contract.
- `scripts/mirror_export_audit_event_log_db.py` - SQLite mirror CLI contract.
- `scripts/verify_export_audit_event_db.py` - SQLite mirror verifier CLI
  contract.
- `Makefile` export-audit targets.
- `qc_cli.py` existing top-level wrapper style.
- `tests/test_export_audit_manifest.py`, `tests/test_export_audit_event_log.py`,
  and `tests/test_export_audit_event_db.py` - canonical behavior.
- `docs/PROJECT_THEORY_AND_GOALS.md` and `CLAUDE.md` - export-audit caveats.
- Memory context:
  `agent-memory recall 'qualitative_coding active decisions next roadmap lane D3 D7 qc_cli evaluation harness INV-2 INV-7 INV-11' --project qualitative_coding`
  returned low-relevance historical outcomes only, no active conflicting
  decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned only an
  unrelated `llm_client` claim file.

---

## Research Basis For This Slice

No external research is needed. This is deterministic CLI parity for existing
repo-local scripts.

---

## Capabilities

Internal CLI delegation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli.py export-audit-manifest` | project ID + export artifact paths/options | canonical manifest JSON | qualitative_coding | agents/operators | free |
| `qc_cli.py verify-export-audit-manifest` | manifest path + optional state/audit options | canonical verification JSON | qualitative_coding | agents/operators | free |
| `qc_cli.py export-publish-preflight` | manifest path + optional state/audit options | canonical preflight JSON | qualitative_coding | agents/operators | free |
| `qc_cli.py verify-export-audit-log` | event-log path | canonical event-log verification JSON | qualitative_coding | agents/operators | free |
| `qc_cli.py mirror-export-audit-db` | event-log path + SQLite path | canonical mirror JSON | qualitative_coding | agents/operators | free |
| `qc_cli.py verify-export-audit-db` | SQLite path | canonical DB verification JSON | qualitative_coding | agents/operators | free |

### Capability Validation

- [x] Each command parses through `qc_cli.py`.
- [x] Each handler delegates to the matching script `main()`.
- [x] Repeated `--artifact` paths are forwarded in order.
- [x] Optional path flags are forwarded only when supplied.
- [x] Docs state these are local provenance/integrity surfaces only, not a full
  tamper-evident audit log.

---

## Files Affected

- `qc_cli.py`
- `tests/test_qc_cli_export_audit_surfaces.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. [x] Add failing wrapper tests that monkeypatch each canonical script `main()` and
   assert exact argv forwarding.
2. [x] Add parser, dispatch, and handler entries in `qc_cli.py`.
3. [x] Update docs/CLAUDE with the top-level CLI surfaces and local-only caveats.
4. [x] Regenerate `AGENTS.md`.
5. [x] Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
6. [x] Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_export_audit_surfaces.py` | `test_qc_cli_export_audit_surface_forwards_args` | All six wrappers delegate exact argv to canonical scripts. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_export_audit_surfaces.py tests/test_export_audit_manifest.py tests/test_export_audit_event_log.py tests/test_export_audit_event_db.py -q` | CLI wrappers plus canonical export-audit behavior. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_export_audit_surfaces.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] All six `qc_cli.py` commands parse successfully.
- [x] Each handler calls the matching canonical script `main()`.
- [x] Supplied arguments are forwarded exactly in canonical script form.
- [x] Repeated artifact paths preserve order.
- [x] Existing Make/script behavior is unchanged.
- [x] Docs/CLAUDE mention the top-level CLI aliases without implying full
  tamper-evident storage, signing, append-only guarantees, methodological
  validity, or SOTA.

> Process criteria:
- [x] TDD red state observed before implementation.
- [x] Focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Plan is moved to completed with verification evidence.
- [x] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| CLI command unrecognized | Parser entry missing | Add subparser. |
| Parser accepts but does nothing | Dispatch branch missing | Add main dispatch branch. |
| Artifact order changes | Handler sorts or reshapes repeated artifact paths | Forward `args.artifact` in parsed order. |
| Optional audit DB without log behavior changes | Wrapper validates differently from script | Delegate exact argv; let canonical script own validation. |
| Export-audit logic duplicated in `qc_cli.py` | Wrapper reimplements script work | Keep handlers as argv delegation only. |
| Docs overclaim | Local hash/event-log checks sound like tamper-evident storage | Keep caveats: local provenance/integrity only, not signing, append-only, external storage, or SOTA evidence. |
