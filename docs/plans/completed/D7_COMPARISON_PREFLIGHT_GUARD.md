# Plan #112: D7 Comparison Preflight Guard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** D7 retrieval comparison protocol preflight
**Blocks:** safer held-out D7 retrieval comparison scoring

---

## Outcome

Implemented optional score-time protocol guarding for D7 retrieval comparisons.
`scripts/compare_d7_retrieval.py --protocol-package ...` now runs the D7
comparison preflight before scoring; failed preflight blocks scoring and output
file writes, while passing guarded comparisons include `preflight_report` in
stdout and output JSON. `make compare-d7-retrieval ... PROTOCOL=...` forwards
the guard path. Verification: focused guard/D7 tests passed (`16 passed`),
focused Ruff passed, `make docs-check` passed, guarded Make dry-run forwarded
`--protocol-package`, and full `make check` passed (`942 passed, 1 skipped, 8
deselected`; Ruff/docs clean; type check not configured).

## Gap

**Current:** `make d7-comparison-preflight` can validate that a D7 comparison
protocol, versioned D7 gold package, and retrieval prediction packages match
before scoring. `make compare-d7-retrieval` still scores without an optional
preflight guard, so an operator can accidentally bypass the protocol check.

**Target:** Add a score-time guard to the comparison runner:

- `scripts/compare_d7_retrieval.py --protocol-package protocol.json`
- `make compare-d7-retrieval ... PROTOCOL=protocol.json`
- When supplied, the runner loads the protocol, D7 gold, and prediction
  packages, runs the same D7 comparison preflight, and blocks scoring/output if
  preflight fails.
- Passing guarded comparisons include the preflight report in stdout and any
  output JSON report.
- Existing unguarded comparison behavior remains compatible.

**Why:** Separate preflight is useful, but the safer default for an agent-driven
workflow is to let the scoring command itself enforce the registered protocol
when a protocol path is supplied. This mirrors the adjudication import preflight
guard and reduces the chance of scoring mismatched D7 inputs.

---

## References Reviewed

- `scripts/compare_d7_retrieval.py` - current D7 comparison runner.
- `scripts/preflight_d7_comparison.py` - standalone D7 preflight CLI.
- `qc_clean/core/d7_comparison_preflight.py` - reusable preflight function.
- `scripts/import_adjudication_responses.py` - existing optional preflight guard
  pattern.
- `Makefile` - existing `compare-d7-retrieval` and preflight targets.
- `tests/test_d7_comparison_preflight.py` - D7 protocol/preflight fixtures.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is deterministic CLI
guard wiring over existing preflight contracts.

---

## Capabilities

Internal CLI guard only; no new cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `compare_d7_retrieval_guarded` | project ID + D7 gold + prediction packages + optional protocol | comparison report with optional preflight report | qualitative_coding | agents/operators running D7 comparisons | free |

### Capability Validation

- [x] Unguarded comparison behavior remains compatible.
- [x] Guarded comparison runs preflight before scoring.
- [x] Failed preflight blocks scoring and writes no output report.
- [x] Passing guarded comparison includes `preflight_report`.
- [x] Make target forwards `PROTOCOL=` to the script.

---

## Files Affected

- `scripts/compare_d7_retrieval.py` (modify)
- `tests/test_d7_comparison_guard.py` (create)
- `Makefile` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add TDD tests for passing guarded comparison, failed preflight blocking
   output, unguarded compatibility, and Make target dry-run.
2. Add `--protocol-package` to `scripts/compare_d7_retrieval.py`.
3. Reuse `preflight_d7_comparison_payloads` and file-hash mapping before
   scoring.
4. Include `preflight_report` in successful guarded comparison output.
5. Update `Makefile` and docs with the guard caveat.
6. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_guard_includes_preflight_report` | Passing guarded comparison scores and includes `preflight_report`. |
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_guard_blocks_failed_preflight_and_writes_no_output` | Failed preflight exits non-zero and does not write report output. |
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_without_protocol_remains_compatible` | Existing unguarded comparison still works. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_d7_retrieval.py tests/test_d7_comparison_preflight.py` | Core comparison/preflight behavior remains stable. |
| `make -n compare-d7-retrieval ... PROTOCOL=...` | Make target forwards protocol guard. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `scripts/compare_d7_retrieval.py --protocol-package ...` runs D7 preflight
  before scoring.
- [x] Failed preflight blocks scoring and output file writes.
- [x] Passing guarded comparison includes `preflight_report`.
- [x] Unguarded comparison remains backward-compatible.
- [x] `make compare-d7-retrieval ... PROTOCOL=...` forwards the guard path.
- [x] Docs state this is provenance/process enforcement only, not held-out D7
  evidence, live-baseline evidence, or superiority evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should guarded comparison become mandatory for held-out splits? — Status:
  DEFERRED | Why it matters: this plan preserves compatibility while adding the
  guard. A future policy slice can require protocols for held-out scoring once
  operators have migrated.

---

## Notes

This guard prevents accidental mismatch at the score boundary. It does not
create held-out gold, run live baselines, adjudicate labels, or license
validity/SOTA/superiority claims.
