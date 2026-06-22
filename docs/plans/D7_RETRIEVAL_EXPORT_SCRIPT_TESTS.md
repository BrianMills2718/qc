# Plan #132: D7 Retrieval Export Script Tests

**Status:** In Progress
**Type:** testing
**Priority:** High
**Blocked By:** Existing D7 retrieval export script
**Blocks:** Confidence in canonical CLI wrappers and Make D7 retrieval export workflows

---

## Gap

**Current:** `qc_clean.core.d7_retrieval.export_d7_retrieval_baseline` has core
tests, and `qc_cli.py run-d7-retrieval` now has forwarding tests. The script
boundary `scripts/run_d7_retrieval.py` itself has no direct tests for argument
parsing, JSON stdout/output behavior, missing-project error behavior, or
option forwarding into the core exporter.

**Target:** Add direct script-level tests for `scripts/run_d7_retrieval.py`:

- Successful lexical export writes the same JSON to stdout and `--output`.
- Missing projects return a JSON error and exit non-zero.
- Parser options are forwarded to `export_d7_retrieval_baseline` with the
  expected typed values.

**Why:** The D7 retrieval export script is now a shared execution boundary for
Make and the canonical CLI wrapper. Testing only the core function and only the
wrapper leaves the script boundary under-specified.

---

## References Reviewed

- `scripts/run_d7_retrieval.py` - script boundary under test.
- `tests/test_d7_retrieval.py` - core D7 retrieval export behavior.
- `tests/test_qc_cli_d7_retrieval.py` - top-level CLI forwarding.
- `docs/plans/completed/D7_RETRIEVAL_MODE_EXPORT.md` - original export plan.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This is deterministic test coverage for an existing
local script boundary.

---

## Capabilities

Test coverage only; no new runtime capability or cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `run_d7_retrieval_script_tests` | pytest fixtures and script argv | passing/failing pytest assertions | qualitative_coding | maintainers/agents | free |

### Capability Validation

- [ ] Script stdout/output behavior is covered.
- [ ] Missing-project JSON error behavior is covered.
- [ ] Script option forwarding to the core exporter is covered.

---

## Files Affected

- `tests/test_run_d7_retrieval_script.py` (new)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add tests for successful script export with output-file parity.
2. Add tests for missing-project JSON error behavior.
3. Add tests that monkeypatch the core exporter and assert parsed option values
   passed by the script.
4. Run focused tests, focused Ruff, docs checks, and full `make check`.
5. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_run_d7_retrieval_script.py` | `test_run_d7_retrieval_writes_output_and_stdout` | Script writes a D7 retrieval package to stdout and `--output`, without mutating saved state. |
| `tests/test_run_d7_retrieval_script.py` | `test_run_d7_retrieval_missing_project_returns_json_error` | Missing project fails with JSON error and non-zero exit. |
| `tests/test_run_d7_retrieval_script.py` | `test_run_d7_retrieval_forwards_options_to_exporter` | Script parses and forwards retrieval/export options as typed kwargs. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_run_d7_retrieval_script.py tests/test_d7_retrieval.py tests/test_qc_cli_d7_retrieval.py -q` | Script boundary plus core exporter and top-level wrapper. |
| `python -m ruff check tests/test_run_d7_retrieval_script.py` | Focused lint on the new tests. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Direct script tests cover success, JSON error, and option forwarding.
- [ ] No runtime behavior changes are required unless tests expose a bug.
- [ ] D7 claim caveats remain unchanged.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Notes

This plan adds evidence for an existing script boundary only. It does not run
held-out D7 comparisons, add live baselines, or change evidentiary claim status.
