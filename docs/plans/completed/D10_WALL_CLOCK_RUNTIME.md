# Plan #27: D10 Wall-Clock Runtime

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** D10 cost latency scorecard
**Blocks:** full benchmark cost/latency reporting

---

## Outcome

`project run` now records last-run wall-clock metadata in
`ProjectState.config.extra["run_timing"]`. The record includes schema version,
started/completed timestamps, monotonic duration seconds, final run status,
trace ID, model, exhaustive-coding flag, resume point, document count, and phase
result count. Completed, paused-for-review, and failed runs record timing before
the project state is saved.

`make bench` now emits `wall_clock_d10` next to `cost_latency_d10`. Missing
timing reports `not_available`; invalid timing metadata fails loudly; durations
are never estimated from stage timestamps or summed LLM-call latency. This is
last-local-run timing metadata, not a versioned public benchmark artifact or
baseline comparison.

**Verification:** `python -m pytest tests/test_bench_phase0.py
tests/test_bench_phase0_script.py tests/test_project_commands.py -q` passed (52
tests), and `python -m ruff check qc_clean/core/bench.py
scripts/bench_phase0.py qc_clean/core/cli/commands/project.py
tests/test_bench_phase0.py tests/test_bench_phase0_script.py
tests/test_project_commands.py` passed. Final closeout gate: `make check`
passed with 682 tests passing, 1 skipped, 8 deselected, Ruff passing, docs
checks passing, and type checking reported as not configured.

---

## Gap

**Current:** `make bench` reports D10 cost/latency from `llm_client`
observability rows. That latency is summed observed LLM-call latency, not the
full pipeline wall-clock runtime. The evaluation harness and theory roadmap
still list full wall-clock run timing as missing.

**Target:** Record a last-run wall-clock timing record around `project run` and
surface it in `make bench` as `wall_clock_d10`. Store the record in
`ProjectState.config.extra["run_timing"]` so it round-trips through the existing
project JSON without a schema migration. The record includes started/completed
timestamps, duration seconds, final run status, trace ID, model, exhaustive flag,
resume point, document count, and phase-result count. Failed runs are recorded
before saving failed state.

**Why:** D10 should distinguish end-to-end runtime from summed LLM-call latency.
This is still local run metadata, not a baseline or public benchmark result.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D10 currently notes summed LLM latency is not
  full pipeline wall-clock time, and Phase 0 remaining work lists full wall-clock
  run timing.
- `docs/PROJECT_THEORY_AND_GOALS.md` - measured ledger says no full wall-clock
  timing has been run.
- `docs/plans/completed/D10_COST_LATENCY_SCORECARD.md` - D10 cost/latency slice
  explicitly deferred pipeline wall-clock timing.
- `qc_clean/core/cli/commands/project.py` - `project run` owns end-to-end
  pipeline invocation and trace ID creation.
- `qc_clean/core/pipeline/pipeline_engine.py` - per-stage timestamps already
  exist; run-level timing is missing.
- `qc_clean/core/bench.py` - D10 cost/latency scorecard and Phase 0 output shape.
- `scripts/bench_phase0.py` - bench CLI injects D10 sections.
- Memory context: `agent-memory recall 'active decisions next evaluation harness qualitative_coding wall clock prompt_eval injection gold set' --project qualitative_coding` - historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is local
instrumentation and scorecard wiring.

---

## Capabilities

This plan modifies a repo-local CLI and benchmark/report surface only; it does
not create a cross-project callable capability.

---

## Files Affected

- `qc_clean/core/cli/commands/project.py` (modify)
- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_project_commands.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify if queue changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/D10_WALL_CLOCK_RUNTIME.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a small helper in `project.py` that writes
   `state.config.extra["run_timing"]`.
2. Wrap `_run_project` around `datetime.now().isoformat()` plus
   `time.perf_counter()` so duration is monotonic.
3. Record timing for completed, paused-for-review, and failed runs before
   `store.save(state)`.
4. Add `d10_wall_clock_scorecard(state)` in `bench.py` that returns
   `not_available` when timing is absent and `scored` when present.
5. Add `wall_clock_d10` to `scripts/bench_phase0.py` output next to
   `cost_latency_d10`.
6. Update docs to say Phase 0 now has last-run wall-clock timing metadata, but
   not public benchmark timing or baseline runtime comparison.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_d10_wall_clock_unavailable_without_run_timing` | Missing run timing is explicit and not estimated. |
| `tests/test_bench_phase0.py` | `test_d10_wall_clock_scores_run_timing_metadata` | Valid timing metadata is surfaced with duration, status, trace ID, model, and document count. |
| `tests/test_project_commands.py` | `test_run_project_records_wall_clock_timing` | `project run` records last-run timing on successful/paused pipeline invocation. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py tests/test_project_commands.py` | Scorecard and project-run contracts. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [x] `project run` records `ProjectState.config.extra["run_timing"]`.
- [x] Failed runs record timing before failed state is saved.
- [x] `make bench` emits `wall_clock_d10`.
- [x] Missing timing reports `not_available`, never estimated from stage
  timestamps.
- [x] `wall_clock_d10` clearly distinguishes end-to-end wall-clock runtime from
  summed LLM-call latency.
- [x] Docs state this is last-run metadata, not a benchmark/baseline result.

> Process criteria (quality gates):
- [x] Required tests pass (`python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_project_commands.py -q`: 52 passed)
- [x] Full test suite passes (`make check`: 682 passed, 1 skipped, 8 deselected)
- [x] Type check status is reported (`make check`: type checking not configured)
- [x] Docs updated

---

## Open Questions

- [ ] Should run history be append-only? - Status: DEFERRED | Why it matters:
  public benchmark artifacts need versioned histories, but this slice records
  the last local run only. A future `benchmark_results/` output should preserve
  immutable run records with dataset/prompt/model hashes.

---

## Notes

`wall_clock_d10.duration_s` must be measured with a monotonic timer. The
timestamp strings are for operator inspection; they are not used to compute
duration.
