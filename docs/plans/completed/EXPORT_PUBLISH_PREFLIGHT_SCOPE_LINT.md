# Plan #196: Export Publish Preflight Scope Lint

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Existing export publish preflight and corpus scope phrasing lint
**Blocks:** Safer publish/handoff gates for claim-bearing text artifacts

---

## Gap

**Current:** `make export-publish-preflight` / `qc_cli.py
export-publish-preflight` verify a local export-audit manifest, artifact hashes,
and optional current project-state hash. Separately, `make
lint-scope-phrasing` / `qc_cli.py lint-scope-phrasing` can scan arbitrary text
for risky population-generalizing phrasing under missing or under-specified
corpus scope.

**Target:** Add an explicit opt-in scope-language gate to export publish
preflight:

- `scripts/export_publish_preflight.py --scope-lint`
- `make export-publish-preflight ... SCOPE_LINT=1`
- `qc_cli.py export-publish-preflight ... --scope-lint`

When enabled, the gate reads textual export artifacts from a valid manifest and
applies the existing deterministic `lint_scope_phrasing` policy against the
loaded `ProjectState`.

**Why:** Publish/handoff preflight is the last local deterministic gate before
exported text leaves the system. It should be able to block broad population
language when the project has no defensible recorded corpus boundary, while
preserving the existing manifest-integrity default for workflows that do not opt
in.

**Non-target:** This slice does not change the scope-lint pattern set, validate
sampling-frame adequacy, prove claim correctness, prove methodological validity,
sign artifacts, make audit logs append-only, create external tamper evidence, or
produce SOTA evidence.

---

## Outcome

Plan commit: `0c7eb5e4`
Implementation commit: `3833e141`

Export publish preflight now has an explicit opt-in scope-language gate:

- `scripts/export_publish_preflight.py --scope-lint`
- `make export-publish-preflight ... SCOPE_LINT=1`
- `qc_cli.py export-publish-preflight ... --scope-lint`

When enabled, preflight requires a loaded `ProjectState`, verifies the export
audit manifest, reads Markdown/text artifacts from verified manifests, and runs
the existing deterministic `lint_scope_phrasing` policy against those artifacts.
Warnings become stable `scope_lint_*` preflight failures. The default behavior
is unchanged when `scope_lint=False`.

The report now includes `scope_lint_status` and `scope_lint_reports` fields.
These fields are local report-boundary discipline only; they are not
sampling-frame adequacy evidence, methodological-validity evidence, audit
signing, external tamper evidence, or SOTA evidence.

Verification:

- TDD red state observed: five expected failures before implementation
  (`scope_lint` argument missing, script flag rejected, and `qc_cli.py` flag
  rejected).
- Focused tests:
  `python -m pytest tests/test_export_publish_preflight.py tests/test_scope_phrasing_lint.py tests/test_qc_cli_export_audit_surfaces.py -q`
  -> `21 passed`.
- Focused Ruff:
  `python -m ruff check qc_clean/core/export/publish_preflight.py scripts/export_publish_preflight.py qc_cli.py tests/test_export_publish_preflight.py tests/test_qc_cli_export_audit_surfaces.py`
  -> passed.
- `make docs-check` -> passed.
- `git diff --check` -> passed.
- `make check` -> `1250 passed, 1 skipped, 8 deselected`; Ruff and docs gates
  passed; type check is still not configured.

---

## References Reviewed

- `qc_clean/core/export/publish_preflight.py` - current manifest preflight gate.
- `scripts/export_publish_preflight.py` - script CLI and audit-event hook.
- `qc_clean/core/scope_lint.py` - deterministic scope-phrasing lint policy.
- `qc_clean/core/export/audit_manifest.py` - manifest model, artifact resolver,
  and verification failure schema.
- `tests/test_export_publish_preflight.py` - current preflight behavior.
- `tests/test_scope_phrasing_lint.py` - current scope-lint behavior.
- `tests/test_qc_cli_export_audit_surfaces.py` - canonical `qc_cli.py` wrapper
  forwarding behavior.
- `CLAUDE.md`, `docs/PROJECT_THEORY_AND_GOALS.md`, and `docs/plans/CLAUDE.md`
  - claim-discipline caveats for corpus scope and audit surfaces.
- Memory context:
  `agent-memory recall 'qualitative_coding export publish preflight scope lint corpus scope active decisions' --project qualitative_coding`
  returned low-relevance historical outcomes only, no active conflicting
  decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned only an
  unrelated `llm_client` claim file.

---

## Research Basis For This Slice

No external research is needed. This is deterministic integration of two
repo-local gates that already have documented claim-discipline limits.

---

## Capabilities

Internal CLI/Make/script integration only; no new cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `export_publish_preflight scope_lint` | manifest path + base dir + project state + opt-in flag | publish preflight report with optional scope-lint reports/failures | qualitative_coding | agents/operators | free |
| `qc_cli.py export-publish-preflight --scope-lint` | canonical preflight args + boolean flag | canonical preflight JSON | qualitative_coding | agents/operators | free |

### Capability Validation

- [x] Default preflight behavior is unchanged when `scope_lint=False`.
- [x] `scope_lint=True` fails loud if no `ProjectState` is supplied.
- [x] Markdown/text artifacts in the manifest are linted when the flag is set.
- [x] Scope-lint warnings become preflight failures with stable failure codes.
- [x] Non-text export artifacts are not ad hoc parsed by this gate.
- [x] Script, Make, and `qc_cli.py` surfaces can opt into the same gate.
- [x] Docs state this is report-boundary discipline only, not sampling-frame
  adequacy, methodological-validity, audit-signing, or SOTA evidence.

---

## Files Expected To Change

- `qc_clean/core/export/publish_preflight.py`
- `scripts/export_publish_preflight.py`
- `qc_cli.py`
- `Makefile`
- `tests/test_export_publish_preflight.py`
- `tests/test_qc_cli_export_audit_surfaces.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`
- `docs/plans/completed/EXPORT_PUBLISH_PREFLIGHT_SCOPE_LINT.md`

---

## Plan

### Steps

1. [x] Add failing tests for the core preflight gate: missing state, warning
   failure on risky Markdown under missing scope, pass with complete scope, and
   script flag exit behavior.
2. [x] Add a `qc_cli.py` wrapper-forwarding test for `--scope-lint`.
3. [x] Extend `run_export_publish_preflight` with an opt-in `scope_lint` flag,
   structured scope-lint fields, and preflight failures derived from existing
   `ScopePhrasingWarning` objects.
4. [x] Add `--scope-lint` to the script, Make target, and `qc_cli.py` wrapper.
5. [x] Update docs/CLAUDE/theory/plan caveats and regenerate `AGENTS.md`.
6. [x] Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
7. [x] Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_export_publish_preflight.py` | `test_export_publish_preflight_scope_lint_requires_state` | Opt-in scope lint fails loudly without project state. |
| `tests/test_export_publish_preflight.py` | `test_export_publish_preflight_scope_lint_fails_risky_markdown_without_scope` | Risky broad language in a Markdown artifact becomes a preflight failure when scope is missing. |
| `tests/test_export_publish_preflight.py` | `test_export_publish_preflight_scope_lint_passes_with_complete_scope` | Complete recorded scope suppresses missing/under-specified scope warnings and preserves pass status. |
| `tests/test_export_publish_preflight.py` | `test_export_publish_preflight_script_scope_lint_exit_code` | Script `--scope-lint` emits JSON and exits nonzero on scope-lint failures. |
| `tests/test_qc_cli_export_audit_surfaces.py` | existing parameterized wrapper case | `qc_cli.py export-publish-preflight --scope-lint` forwards the flag to the canonical script. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_export_publish_preflight.py tests/test_scope_phrasing_lint.py tests/test_qc_cli_export_audit_surfaces.py -q` | Core gate, existing lint behavior, and wrapper parity. |
| `python -m ruff check qc_clean/core/export/publish_preflight.py scripts/export_publish_preflight.py qc_cli.py tests/test_export_publish_preflight.py tests/test_qc_cli_export_audit_surfaces.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] With `scope_lint=False`, existing publish preflight JSON remains compatible
  and does not require project state.
- [x] With `scope_lint=True` and no project state, preflight returns `status:
  fail` with failure code `scope_lint_requires_project_state`.
- [x] With `scope_lint=True`, a manifest for Markdown/text artifacts and a
  missing/empty/under-specified `corpus_scope` blocks risky
  population-generalizing language with stable `scope_lint_*` failure codes.
- [x] With `scope_lint=True` and complete recorded scope, the same text passes
  the deterministic missing-scope lint.
- [x] Script, Make, and `qc_cli.py` surfaces all expose the same opt-in gate.
- [x] Documentation preserves caveats: the gate is report-boundary discipline
  only, not sampling-frame adequacy evidence, methodological-validity evidence,
  audit signing, external tamper evidence, or SOTA evidence.

> Process criteria:
- [x] Plan committed before implementation.
- [x] Red tests observed before implementation.
- [x] Focused tests pass.
- [x] Focused Ruff passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes, or any failure is documented as unrelated with
  evidence.
- [x] Implementation and closeout commits are pushed.

---

## Failure Modes And Diagnostics

| Failure Mode | Diagnostic | Response |
|--------------|------------|----------|
| Existing preflight callers unexpectedly need state | Run current preflight tests without `--scope-lint` | Keep `scope_lint` default false and state requirement conditional only. |
| Scope lint reads binary/non-text artifacts | Check manifest format/suffix filtering tests | Restrict to Markdown/text suffixes and documented text export formats. |
| Duplicate manifest failures obscure scope failures | Inspect report failure list | Preserve verifier failures and append scope-lint failures with `scope_lint_*` codes. |
| `qc_cli.py` diverges from script contract | Wrapper forwarding test | Delegate exact argv to `scripts.export_publish_preflight.main`. |
| Docs imply validity/SOTA/audit guarantees | `make docs-check` plus manual caveat review | Reword docs to local report-discipline and local-integrity language only. |

---

## Closeout

Plan closed after implementation verification.
