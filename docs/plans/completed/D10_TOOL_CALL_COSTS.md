# Plan #75: D10 Tool-Call Costs

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #27 D10 cost latency scorecard
**Blocks:** fuller D10 local cost accounting

---

## Outcome

D10 `cost_latency_d10` now preserves existing LLM-only fields and adds optional
observed `tool_calls` accounting when matching real `tool_calls` rows exist.
The scorecard reports tool call counts, success/error counts, tool cost,
duration summaries, and tool/operation/task breakdowns, plus explicit
`combined_observed_*` totals. Missing or unmatched tool-call rows are reported
as `not_available` without suppressing scored LLM rows. This is local
observability accounting only; it is not public benchmark timing evidence.

**Verification:** `python -m pytest tests/test_bench_phase0.py
tests/test_bench_phase0_script.py::test_bench_phase0_includes_d10_from_observability_db
-q` passed (61 tests); `python -m ruff check qc_clean/core/bench.py
tests/test_bench_phase0.py` passed; final `make check` passed (783 passed, 1
skipped, 8 deselected; Ruff/docs-check passed). Type checking is not configured
in this repo.

---

## Gap

**Current:** D10 `cost_latency_d10` reports real LLM costs and observed LLM-call
latency from `llm_calls` rows. It intentionally deferred `tool_calls` costs and
durations even though the shared observability DB now has a concrete
`tool_calls` schema.

**Target:** When matching `tool_calls` rows exist, include a `tool_calls`
subsection in D10 with call counts, success/error counts, total tool cost,
summed/mean/max tool duration, and tool/operation/task breakdowns. Preserve the
existing LLM-only fields and add combined observed cost/duration fields that
include tools when the subsection is scored.

**Why:** D10 should account for real non-LLM tool spend/latency once the schema
exists. This remains local observability accounting, not public benchmark timing
or baseline evidence.

---

## References Reviewed

- `docs/plans/completed/D10_COST_LATENCY_SCORECARD.md` - deferred tool-call cost
  question.
- `qc_clean/core/bench.py` - D10 scorecard and observability DB query code.
- `tests/test_bench_phase0.py` - D10 scorecard tests and SQLite fixtures.
- Local `~/projects/data/llm_observability.db` schema inspection - confirmed
  `tool_calls` columns: `project`, `trace_id`, `timestamp`, `tool_name`,
  `operation`, `status`, `duration_ms`, `task`, `cost`, error fields.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - D10
  claim-discipline language.
- Memory context: `agent-memory recall 'D10 tool call costs' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No additional research beyond repo-local references and direct local DB schema
inspection was needed.

---

## Capabilities

This plan modifies a repo-local scorecard surface only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/D10_TOOL_CALL_COSTS.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a `_fetch_d10_tool_rows` query for the existing `tool_calls` schema,
   using the same project/trace selector as LLM rows.
2. Add a `_summarize_d10_tool_calls` helper that returns scored/not-available
   metadata without failing when `tool_calls` is absent or has no matches.
3. Preserve existing LLM-only D10 fields and add `tool_calls`,
   `combined_observed_cost_usd`, `combined_observed_duration_s`, and per-document
   combined cost/duration fields.
4. Add focused SQLite tests for matched tool calls and absent `tool_calls`
   table behavior.
5. Update docs to describe D10 as LLM plus optional observed tool-call accounting
   without turning it into public timing evidence.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_d10_cost_latency_includes_matching_tool_calls` | Matching `tool_calls` rows are summarized and included in combined observed totals. |
| `tests/test_bench_phase0.py` | `test_d10_cost_latency_marks_tool_calls_unavailable_when_table_missing` | Existing LLM D10 scoring still works when `tool_calls` is absent. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py::test_d10_cost_latency_scores_matching_project_trace_rows` | Protect existing LLM-only D10 semantics. |
| `tests/test_bench_phase0_script.py::test_bench_phase0_includes_d10_from_observability_db` | Protect CLI D10 output. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] D10 retains existing LLM-only fields and values.
- [x] Matching `tool_calls` rows produce a scored `tool_calls` subsection.
- [x] Missing or unmatched `tool_calls` data is reported as `not_available`
  without suppressing scored LLM rows.
- [x] Combined observed cost/duration fields include tool totals only when tool
  calls are scored.
- [x] Docs state tool-call D10 is local observability accounting, not public
  benchmark timing evidence.

> Process criteria:
- [x] Required tests pass (`python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py::test_bench_phase0_includes_d10_from_observability_db -q`: 61 passed)
- [x] Full test suite passes (`make check`: 783 passed, 1 skipped, 8 deselected; Ruff/docs-check passed)
- [x] Type check status is reported (`make check`: type check not yet configured)
- [x] Docs updated

---

## Open Questions

- [x] Should D10 overwrite `total_cost_usd` to include tools? — Status: RESOLVED
  | Answer: No. Keep existing LLM-only fields stable and add explicit combined
  observed totals.

---

## Notes

The local DB schema inspection was observational only; no production/shared data
was modified.
