# Plan #189: QC CLI Adjudication Import Surface

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Adjudication response import script
**Blocks:** Top-level CLI parity for guarded D3/D7 adjudication gold import

---

## Gap

**Current:** `scripts/import_adjudication_responses.py` and
`make import-adjudication-responses` can convert completed adjudication response
packages into D3/D7 gold package inputs, optionally enforcing protocol/sample
response preflight before writing outputs. `qc_cli.py` now wraps the surrounding
adjudication validation/preflight surfaces and the strict Phase 0 adjudication
package writer, but it does not expose the import step itself as a top-level
command.

**Target:** Add `qc_cli.py import-adjudication-responses` as a thin delegating
wrapper over `scripts/import_adjudication_responses.py`.

**Why:** The agent-drivable adjudication path should be continuous through the
canonical top-level CLI: validate protocol, preflight sample, validate
responses, preflight responses, import valid responses into versioned D3/D7
gold package inputs, then assemble/run a strict Phase 0 package.

**Non-target:** This slice does not change import semantics, package schemas,
preflight behavior, Make targets, scorecard scoring, or evidence claims. It only
adds a top-level CLI alias that forwards arguments to the existing script.

---

## References Reviewed

- `scripts/import_adjudication_responses.py` - canonical import script.
- `Makefile` - existing `import-adjudication-responses` target.
- `qc_cli.py` - parser/dispatch/handler patterns.
- `tests/test_adjudication_import.py` - script-level import behavior.
- `tests/test_qc_cli_adjudication_surfaces.py` - adjacent wrapper tests.
- `docs/plans/completed/ADJUDICATION_IMPORT_PREFLIGHT_GUARD.md` - import-time
  preflight guard behavior and caveats.
- `docs/EVALUATION_HARNESS.md` - adjudication workflow and claim discipline.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-3 state and no-evidence caveats.

---

## Research Basis For This Slice

No external research is needed. This is deterministic CLI parity for an
existing repo-local script.

---

## Capabilities

Internal CLI delegation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli.py import-adjudication-responses` | CLI args matching canonical import script | canonical import report | qualitative_coding | agents/operators creating D3/D7 adjudication gold inputs | free |

### Capability Validation

- [ ] Parser accepts `import-adjudication-responses`.
- [ ] Required `package`, `--gold-set-id`, `--dataset-name`, `--coder-count`,
  `--adjudicator`, and `--protocol` are forwarded.
- [ ] Optional `--output-d3`, `--output-d7`, `--split`,
  `--protocol-package`, `--sample-package`, `--prompt-frozen`,
  `--contamination-checked`, and `--notes` are forwarded only when supplied.
- [ ] The wrapper delegates to `scripts.import_adjudication_responses.main`
  without duplicating validation, preflight, or import logic.
- [ ] Docs state this is CLI parity/provenance only, not expert labels,
  correctness estimates, validity evidence, or benchmark results.

---

## Files Affected

- `qc_cli.py`
- `tests/test_qc_cli_adjudication_surfaces.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Add a failing CLI wrapper test that monkeypatches
   `import_adjudication_responses.main` and verifies forwarded argv for required,
   optional, and boolean arguments.
2. Add parser, dispatch, and handler entries in `qc_cli.py`.
3. Update docs/CLAUDE with the top-level CLI surface and caveats.
4. Regenerate `AGENTS.md`.
5. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
6. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_adjudication_surfaces.py` | `test_qc_cli_import_adjudication_responses_forwards_args` | Top-level CLI delegates supplied import args to the canonical script. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_adjudication_surfaces.py tests/test_adjudication_import.py -q` | CLI wrapper and canonical import behavior. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_adjudication_surfaces.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_cli.py import-adjudication-responses ...` parses successfully.
- [ ] The handler calls `scripts.import_adjudication_responses.main()`.
- [ ] Supplied arguments are forwarded exactly in canonical script form.
- [ ] Omitted optional arguments are not forwarded.
- [ ] Existing Make/script behavior is unchanged.
- [ ] Docs/CLAUDE mention the top-level CLI alias without implying expert
  labels, correctness estimates, validity evidence, or benchmark results.

> Process criteria:
- [ ] TDD red state observed before implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Plan is moved to completed with verification evidence.
- [ ] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| CLI command unrecognized | Parser entry missing | Add subparser. |
| Parser accepts but does nothing | Dispatch branch missing | Add main dispatch branch. |
| Validation duplicated in `qc_cli.py` | Wrapper reimplements script import/preflight logic | Keep handler as argv delegation only. |
| Optional args forwarded as `None` strings | Handler blindly forwards all fields | Forward optional flags only when non-null. |
| Boolean flags lost | Handler fails to append flag-only args | Append `--prompt-frozen` / `--contamination-checked` when true. |
| Docs overclaim | CLI alias sounds like expert-label evidence | Keep caveats: import/package creation only, not populated adjudication evidence. |
