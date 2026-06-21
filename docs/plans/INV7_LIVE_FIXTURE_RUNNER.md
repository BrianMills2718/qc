# Plan #43: INV-7 Live Fixture Runner

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Live adversarial prompt-injection evaluation; INV-7 hardening

---

## Gap

**Current:** `make run-inv7-fixtures` runs deterministic structural checks that
verify adversarial transcript/derived-output lines are DATA-prefixed. The bench
scorecard can consume externally supplied INV-7 outcomes, but the repo has no
agent-drivable live model fixture runner.

**Target:** Add an opt-in live INV-7 fixture runner that sends adversarial
untrusted-data prompts to a configured model through `llm_client`, detects simple
payload-following canary failures, emits the same `PROMPT_INJECTION=` compatible
JSON shape as structural fixtures, and records model/trace/budget provenance.

**Why:** Structural prompt-boundary tests are necessary but do not prove live
model obedience. A live runner gives agents a repeatable way to generate
adversarial fixture outcomes for `make bench PROMPT_INJECTION=...` without
manual scripts.

---

## References Reviewed

- `qc_clean/core/inv7_fixtures.py` - current structural fixture contracts.
- `scripts/run_inv7_fixtures.py` - current structural runner CLI.
- `qc_clean/core/bench.py` - prompt-injection scorecard input shape.
- `llm_client.acall_llm` - unstructured live model call surface with task,
  trace, and budget kwargs.
- `Makefile` - current `run-inv7-fixtures` target pattern.
- Memory context: `agent-memory recall 'active decisions qualitative_coding next roadmap D3 agreement kappa alpha AC1 bias prompt injection live benchmark confidence calibration' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research. This is a live harness scaffold over the already
defined INV-7 threat model. It uses simple canary-token failure detection, not a
general adversarial robustness proof.

---

## Capabilities

Internal project capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `run_inv7_live_fixtures(...)` | built-in live fixtures + model config | `PROMPT_INJECTION=` compatible JSON | qualitative_coding | `make bench`, artifact packages | paid LLM |

### Capability Validation

- [ ] Live runner emits scorecard-compatible prompt-injection evaluations.
- [ ] Deterministic tests can inject fake call results without live LLM calls.
- [ ] CLI/make target requires explicit output and exposes model, trace, and
  budget controls.
- [ ] Docs state live fixtures are a benchmark input, not proof of prompt-
  injection robustness.

---

## Files Affected

- `qc_clean/core/inv7_fixtures.py` (modify)
- `scripts/run_inv7_live_fixtures.py` (create)
- `Makefile` (modify)
- `tests/test_inv7_fixture_runner.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add live fixture contracts and default adversarial prompts to
   `qc_clean/core/inv7_fixtures.py`.
2. Add async/sync live runner functions that call an injectable model-call
   function and emit bench-compatible JSON.
3. Add `scripts/run_inv7_live_fixtures.py` and `make run-inv7-live-fixtures`.
4. Add deterministic tests with fake model outputs for pass/fail behavior and
   script output.
5. Update docs conservatively: live fixture runner exists; no live benchmark has
   been run unless a result file is supplied/scored.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_inv7_fixture_runner.py` | live runner pass/fail test | Fake model output with canary token is marked attack succeeded; normal output passes. |
| `tests/test_inv7_fixture_runner.py` | live script summary test | Script writes bench-compatible JSON and prints summary when provided fake runner. |
| `tests/test_bench_phase0_script.py` | existing runner output path | Existing structural runner remains compatible. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_inv7_fixture_runner.py` | Structural fixtures remain stable. |
| `tests/test_bench_phase0.py` | Scorecard consumes fixture output. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `make run-inv7-live-fixtures OUTPUT=... MODEL=...` writes a
  `PROMPT_INJECTION=` compatible JSON file.
- [ ] Live outputs include model, trace ID, max budget, response excerpts, and
  deterministic canary-token failure modes.
- [ ] Live fixture tests do not make network/LLM calls.
- [ ] Docs distinguish structural checks, live fixture outcomes, and robustness
  claims.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should live fixture pass/fail eventually be judged by a second evaluator
  model? — Status: DEFERRED | Why it matters: evaluator-model adjudication is
  itself prompt-injection sensitive and belongs in a future adversarial benchmark
  protocol.

---

## Notes

This plan creates an agent-drivable live fixture runner. It does not run a live
benchmark in CI and does not prove INV-7 is solved.
