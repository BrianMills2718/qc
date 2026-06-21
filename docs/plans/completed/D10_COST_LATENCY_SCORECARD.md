# Plan #25: D10 Cost Latency Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 evaluation harness
**Blocks:** public benchmark scorecard cost/latency reporting

---

## Outcome

`make bench` now includes `cost_latency_d10`, computed from real `llm_client`
`llm_calls` rows. Default matching uses the local project trace prefix
`qualitative_coding/project/{state.id}` so local `project run` and recode traces
are included; `TRACE_ID=` / `--trace-id` can force an exact trace. `OBS_DB=` /
`--observability-db` can override the default observability DB path. Missing DBs,
missing schema, or no matching rows report `not_available`; costs are never
estimated from `ProjectState`.

The score reports call counts, errored calls, cost, marginal cost, tokens,
summed/mean/max observed LLM-call latency, per-document cost/latency, model/task
counts, and first/last timestamps. It remains a Phase 0 substrate, not a
baseline or full wall-clock benchmark.

**Verification:** `python -m pytest tests/test_bench_phase0.py
tests/test_bench_phase0_script.py -q` passed (21 tests), and `python -m ruff
check qc_clean/core/bench.py scripts/bench_phase0.py tests/test_bench_phase0.py
tests/test_bench_phase0_script.py` passed. Final closeout gate:
`make check` passed with 674 tests passing, 1 skipped, 8 deselected, Ruff
passing, docs checks passing, and type checking reported as not configured.

---

## Gap

**Current:** `phase0_scorecard()` includes D1/D2/D5 plus optional D7 and INV-7
fixture sections, but `_meta.cost_note` says LLM cost is queried separately.
The evaluation harness explicitly defines D10 cost/latency as a dimension and
requires querying the `llm_client` observability DB for real costs, never
estimates.

**Target:** Add a D10 cost/latency scorecard section to `make bench` using real
`llm_calls` rows from `~/projects/data/llm_observability.db` or a provided
database path. Default matching uses the local CLI trace prefix
`qualitative_coding/project/{state.id}` so normal `project run` and recode
traces are included. Provide an explicit `--trace-id` / `TRACE_ID=` override for
non-default traces. If the DB or rows are unavailable, report `not_available`
rather than estimating.

**Why:** Cost/latency is one of the harness dimensions. It should be part of the
same agent-drivable scorecard instead of a separate ad hoc command.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D10 cost/latency definition and Phase 0 remaining work.
- `docs/PROJECT_THEORY_AND_GOALS.md` - observability rule: query DB for real costs, never estimate.
- `qc_clean/core/bench.py` - current Phase 0 scorecard.
- `scripts/bench_phase0.py` - scorecard CLI.
- `Makefile` - `bench` and `cost` surfaces.
- `scripts/recent_errors.py` and `tests/test_recent_errors.py` - existing observability DB path and SQLite testing pattern.
- `qc_clean/core/cli/commands/project.py` - default project and recode trace IDs.
- Memory context: `agent-memory recall 'active decisions roadmap next qualitative_coding semantic retrieval D7 prompt injection theoretical sampling' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional external research beyond repo-local references was needed. This
implements a documented evaluation-harness dimension using existing
observability infrastructure.

---

## Capabilities

This plan modifies a repo-local benchmark/report surface only; it does not
create a cross-project callable capability.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `Makefile` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/D10_COST_LATENCY_SCORECARD.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `d10_cost_latency_scorecard(state, db_path, trace_id=None,
   project="qualitative_coding")`.
2. Query `llm_calls` only; this slice reports LLM cost/latency, not tool costs.
3. Default trace matching to `trace_id LIKE
   "qualitative_coding/project/{state.id}%"`.
4. If `trace_id` is provided, match that exact trace ID.
5. Return `not_available` for missing DB, missing table/schema, or no matching
   rows; do not estimate from project state.
6. Return real totals when rows exist: call count, errored calls, total/marginal
   cost, prompt/completion/total tokens, summed/mean/max LLM latency, cost per
   document, latency per document, first/last timestamps, task/model counts.
7. Add `--observability-db`, `--trace-id`, `OBS_DB=`, and `TRACE_ID=` bench
   surfaces.
8. Update docs and remove the `_meta.cost_note` wording that says costs are
   queried separately once the section exists.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_d10_cost_latency_unavailable_when_db_missing` | Missing DB reports `not_available`, not an estimate. |
| `tests/test_bench_phase0.py` | `test_d10_cost_latency_scores_matching_project_trace_rows` | Matching trace-prefix rows produce real totals and per-document rates. |
| `tests/test_bench_phase0.py` | `test_d10_cost_latency_uses_explicit_trace_id` | Explicit trace ID overrides default prefix matching. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_includes_d10_from_observability_db` | CLI loads DB path and emits D10 section. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py tests/test_bench_phase0_script.py` | Scorecard and CLI contracts. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [x] Bench output includes `cost_latency_d10`.
- [x] Missing DB or no matching rows reports `not_available` and does not estimate.
- [x] Default matching uses local project trace prefix.
- [x] Explicit trace ID override is supported.
- [x] Reported cost/token/latency values are computed from actual DB rows.
- [x] `make bench` forwards `OBS_DB=` and `TRACE_ID=`.
- [x] Docs state D10 is now a Phase 0 scorecard substrate and still not a
  benchmark/baseline result.

> Process criteria (quality gates):
- [x] Required tests pass (`python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py -q`: 21 passed)
- [x] Full test suite passes (`make check`: 674 passed, 1 skipped, 8 deselected)
- [x] Type check status is reported (`make check`: type checking not configured)
- [x] Docs updated

---

## Open Questions

- [ ] Should tool-call costs be folded into D10 now? — Status: DEFERRED | Why it
  matters: tool costs live in `tool_calls`, but the D10 definition here is LLM
  cost/latency from `llm_calls`. Add tool costs later with a separate schema and
  tests.

---

## Notes

`latency_s` is summed across calls and should be described as summed observed
LLM-call latency, not full wall-clock runtime. Pipeline wall-clock timing can be
added later if the runner logs run start/end.
