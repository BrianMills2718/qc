# Plan #187: QC CLI Phase 0 Adjudication Package Writer

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 adjudication package writer script
**Blocks:** Top-level CLI parity for strict Phase 0 adjudication package assembly

---

## Gap

**Current:** `scripts/write_phase0_adjudication_package.py` and
`make write-phase0-adjudication-package` can write strict Phase 0 manifests
from validated imported D3/D7 adjudication gold package inputs. `qc_cli.py`
has `bench-package`, D7 package writer/runner wrappers, and validation wrappers,
but no top-level wrapper for the Phase 0 adjudication package writer.

**Target:** Add `qc_cli.py write-phase0-adjudication-package` as a thin
delegating wrapper over `scripts/write_phase0_adjudication_package.py`.

**Why:** Agents and humans should be able to use the canonical top-level CLI for
the same package assembly surface exposed through Make and script entrypoints.
This keeps Phase 0 package workflows consistent with D7 package workflows.

**Non-target:** This slice does not change manifest schema, adjudication import,
gold package validation, preflight behavior, package runner behavior, Make
targets, or benchmark evidence. It only adds a top-level CLI alias.

---

## References Reviewed

- `scripts/write_phase0_adjudication_package.py` - canonical writer script.
- `Makefile` - existing `write-phase0-adjudication-package` target.
- `qc_cli.py` - parser/dispatch/handler patterns.
- `tests/test_phase0_adjudication_package.py` - script-level behavior.
- `tests/test_qc_cli_bench.py` and D7 CLI tests - wrapper-forwarding pattern.
- `docs/EVALUATION_HARNESS.md` - package writer caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-3 and Phase 0 claim discipline.

---

## Research Basis For This Slice

No external research is needed. This is deterministic CLI parity for an existing
repo-local script.

---

## Capabilities

Internal CLI delegation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli.py write-phase0-adjudication-package` | CLI args matching canonical writer | canonical writer report | qualitative_coding | agents/operators assembling Phase 0 manifests | free |

### Capability Validation

- [ ] Parser accepts `write-phase0-adjudication-package`.
- [ ] Required `project_id` and `--output` are forwarded.
- [ ] Optional `--d3-gold-file`, `--d7-gold-file` / `--gold-file`,
  `--scorecard-output`, `--artifact-dir`, `--observability-db`, and
  `--trace-id` are forwarded only when supplied.
- [ ] The wrapper delegates to `scripts.write_phase0_adjudication_package.main`
  without duplicating validation logic.
- [ ] Docs state this is CLI parity/provenance only, not adjudication evidence.

---

## Files Affected

- `qc_cli.py`
- `tests/test_qc_cli_bench.py`
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
   `write_phase0_adjudication_package.main` and verifies forwarded argv.
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
| `tests/test_qc_cli_bench.py` | `test_qc_cli_write_phase0_adjudication_package_forwards_args` | Top-level CLI delegates all supplied args to canonical writer. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_bench.py tests/test_phase0_adjudication_package.py -q` | CLI wrapper and canonical writer behavior. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_bench.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_cli.py write-phase0-adjudication-package ...` parses successfully.
- [ ] The handler calls `scripts.write_phase0_adjudication_package.main()`.
- [ ] Supplied arguments are forwarded exactly in canonical script form.
- [ ] Omitted optional arguments are not forwarded.
- [ ] Existing Make/script behavior is unchanged.
- [ ] Docs/CLAUDE mention the top-level CLI alias without implying labels or
  validity evidence exist.

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
| Validation duplicated in `qc_cli.py` | Wrapper reimplements script logic | Keep handler as argv delegation only. |
| Optional args forwarded as `None` strings | Handler blindly forwards all fields | Forward optional flags only when non-null. |
| Docs overclaim | CLI alias sounds like expert-label evidence | Keep caveats: package assembly only, not populated adjudication evidence. |
