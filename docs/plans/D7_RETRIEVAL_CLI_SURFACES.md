# Plan #131: D7 Retrieval CLI Surfaces

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Existing D7 retrieval export and comparison scripts
**Blocks:** Canonical CLI execution of D7 retrieval baseline export and guarded comparison

---

## Gap

**Current:** D7 retrieval prediction export and comparison are agent-drivable
through Make/script surfaces:

- `make run-d7-retrieval` / `scripts/run_d7_retrieval.py`
- `make compare-d7-retrieval` / `scripts/compare_d7_retrieval.py`

But `qc_cli.py` has no canonical local CLI commands for these D7 evaluation
surfaces.

**Target:** Add thin canonical CLI wrappers:

- `python qc_cli.py run-d7-retrieval <project_id> ...`
- `python qc_cli.py compare-d7-retrieval <project_id> --gold-file ... --predictions-file ...`

The wrappers should forward current script flags unchanged and leave retrieval
export, preflight, scoring, JSON error behavior, and report writing owned by the
existing scripts.

**Why:** The roadmap's next high-value evaluation lane is held-out D7
evaluation/live-baseline work. Before populated held-out runs, the existing D7
retrieval export/comparison substrate should be reachable from the canonical
local CLI that agents already use for Phase 0 scorecards and packages.

---

## References Reviewed

- `scripts/run_d7_retrieval.py` - D7 retrieval prediction export flags.
- `scripts/compare_d7_retrieval.py` - D7 retrieval comparison/preflight flags.
- `qc_cli.py` - top-level command parser and thin wrapper pattern.
- `CLAUDE.md` and `docs/EVALUATION_HARNESS.md` - D7 comparison surfaces and claim caveats.
- `docs/plans/completed/D7_RETRIEVAL_MODE_EXPORT.md`
- `docs/plans/completed/D7_RETRIEVAL_COMPARISON_REPORT.md`
- `docs/plans/completed/D7_COMPARISON_PREFLIGHT_GUARD.md`
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This is deterministic CLI exposure for existing local
D7 retrieval export and comparison surfaces.

---

## Capabilities

Internal CLI wrapper capability only; no new cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli_run_d7_retrieval` | `qc_cli.py run-d7-retrieval` argv | `scripts/run_d7_retrieval.py` exit code/stdout | qualitative_coding | agents/operators using canonical CLI | free unless embedding mode is requested |
| `qc_cli_compare_d7_retrieval` | `qc_cli.py compare-d7-retrieval` argv | `scripts/compare_d7_retrieval.py` exit code/stdout | qualitative_coding | agents/operators using canonical CLI | free |

### Capability Validation

- [ ] `qc_cli.py run-d7-retrieval` accepts and forwards current retrieval export
  flags.
- [ ] `qc_cli.py compare-d7-retrieval` accepts and forwards current comparison
  flags including repeated `--predictions-file` and optional
  `--protocol-package`.
- [ ] Existing script-level D7 retrieval/comparison behavior continues to pass.

---

## Files Affected

- `qc_cli.py` (modify)
- `tests/test_qc_cli_d7_retrieval.py` (new)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add TDD tests that monkeypatch the two script `main()` functions and assert
   exact `qc_cli.py` forwarding.
2. Add `run-d7-retrieval` and `compare-d7-retrieval` parsers and handlers in
   `qc_cli.py`.
3. Update docs to list the canonical D7 retrieval CLI commands.
4. Run focused CLI tests, focused Ruff, docs checks, and full `make check`.
5. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_run_d7_retrieval_forwards_flags` | Retrieval export flags reach `scripts.run_d7_retrieval.main` unchanged. |
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_compare_d7_retrieval_forwards_flags` | D7 comparison flags, including repeated predictions, reach `scripts.compare_d7_retrieval.main` unchanged. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_d7_retrieval.py tests/test_d7_retrieval.py tests/test_d7_comparison_report.py tests/test_d7_comparison_guard.py -q` | Top-level wrappers plus underlying D7 retrieval/comparison behavior. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_d7_retrieval.py` | Focused lint on modified CLI surfaces. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_cli.py run-d7-retrieval <project_id>` exists and forwards supported
  script flags.
- [ ] `qc_cli.py compare-d7-retrieval <project_id>` exists and forwards
  supported script flags.
- [ ] The wrappers do not duplicate retrieval export, preflight, scoring, or
  JSON error logic from the scripts.
- [ ] Docs list these commands and preserve D7 claim caveats.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Notes

This plan only exposes existing D7 retrieval evaluation substrate through the
canonical local CLI. It does not run held-out D7 comparisons, add live
baselines, or change evidentiary claim status.
