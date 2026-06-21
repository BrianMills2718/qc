# Plan #21: INV-7 Prompt Injection Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** INV-7 instruction/data separation; INV-7 prompt override guards
**Blocks:** live adversarial prompt-injection evaluation; broader custom-prompt governance

---

## Outcome

`phase0_scorecard()` now includes `prompt_injection_inv7`. It reports
`not_available` when no fixture outcomes are present, and scores externally
supplied fixture outcomes from `ProjectState.config.extra`, `scripts/bench_phase0.py
--prompt-injection-file`, or `make bench PROMPT_INJECTION=inv7.json` without
mutating saved project state. The score reports total fixtures, pass/fail
counts, pass rate, attack-success rate, failed fixture IDs, and per-surface
summaries.

This is a measurement substrate only. It does not run a live adversarial model
benchmark or prove prompt-injection robustness.

**Verification:** `python -m pytest tests/test_bench_phase0.py
tests/test_bench_phase0_script.py tests/test_prompt_boundaries_inv7.py -q`
passed (31 tests), and `python -m ruff check qc_clean/core/bench.py
scripts/bench_phase0.py tests/test_bench_phase0.py
tests/test_bench_phase0_script.py` passed. Final `make check` passed (666
passed, 1 skipped, 8 deselected; Ruff passed; docs-check passed). Type checking
is not configured in this repo.

---

## Gap

**Current:** INV-7 has deterministic prompt-capture regressions showing that
first-party raw and derived prompt inputs are line-prefixed as untrusted data,
and prompt overrides fail loudly when protected placeholders are omitted.
`make bench` does not report any prompt-injection / instruction-data separation
measurement, so the evaluation harness cannot track adversarial fixture results
or distinguish "no eval data" from "all fixtures passed."

**Target:** Add an INV-7 prompt-injection scorecard section to
`phase0_scorecard()`. The section reports `not_available` until externally
provided fixture results exist. When fixture results are supplied through
project metadata or an external bench JSON file, it reports total fixtures,
passed/failed counts, pass rate, attack-success rate, failures by surface, and
failed fixture IDs. Add a `make bench` variable and script flag for supplying
that JSON without mutating project state.

**Why:** OWASP LLM01:2025 defines prompt injection as model behavior/output
being altered by direct or indirect inputs and recommends both explicit
untrusted-content segregation and adversarial testing. NIST AI RMF frames AI
risk management as Govern/Map/Measure/Manage; this slice adds the missing
Measure surface for INV-7 without claiming prompt-injection robustness.

---

## References Reviewed

- `qc_clean/core/bench.py` - Phase 0 scorecard and gold-dependent D7 substrate.
- `scripts/bench_phase0.py` - external benchmark JSON loading pattern.
- `Makefile` - `bench` target variables.
- `tests/test_prompt_boundaries_inv7.py` - deterministic INV-7 prompt-capture regressions.
- `tests/test_bench_phase0.py` - scorecard unit tests.
- `tests/test_bench_phase0_script.py` - external file script tests.
- `docs/EVALUATION_HARNESS.md` - harness phases and claim discipline.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-7 status and roadmap caveats.
- Memory context: `agent-memory recall 'INV-7 prompt injection benchmark scorecard qualitative coding active decisions' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

- OWASP GenAI Security Project, `LLM01:2025 Prompt Injection`
  (`https://genai.owasp.org/llmrisk/llm01-prompt-injection/`) - direct/indirect
  prompt injection, untrusted-content segregation, output validation, and
  adversarial testing are relevant controls.
- NIST AI Risk Management Framework
  (`https://airc.nist.gov/airmf-resources/airmf/`) - AI risk management is
  operationalized through Govern, Map, Measure, and Manage; this plan is a
  Measure-layer substrate.

---

## Capabilities

This plan modifies a repo-local benchmark surface only; it does not create a
cross-project callable capability.

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
- `docs/plans/INV7_PROMPT_INJECTION_SCORECARD.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a Pydantic model for externally supplied prompt-injection fixture
   results under `ProjectState.config.extra["prompt_injection_evaluations"]`.
2. Add `prompt_injection_inv7` to `phase0_scorecard()`.
3. Return `not_available` when no fixture results exist, with a clear caveat.
4. When results exist, compute pass/fail counts, pass rate,
   attack-success rate, per-surface summaries, and failed fixture IDs.
5. Add `--prompt-injection-file` to `scripts/bench_phase0.py`, applied in
   memory only like `--gold-file`.
6. Add `PROMPT_INJECTION=` forwarding to `make bench`.
7. Add tests for no-data status, scored mixed fixture results, invalid metadata,
   script file loading without mutation, and invalid file shape.
8. Update docs conservatively: a scorecard substrate exists; no live adversarial
   run or full prompt-injection proof is claimed.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_reports_prompt_injection_unavailable_without_eval_data` | Missing fixture results are explicit, not silently passing. |
| `tests/test_bench_phase0.py` | `test_scorecard_scores_prompt_injection_fixture_results` | Mixed fixture results produce pass/fail rates, failed IDs, and by-surface counts. |
| `tests/test_bench_phase0.py` | `test_scorecard_invalid_prompt_injection_metadata_fails_loud` | Malformed metadata raises `ValueError`. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_prompt_injection_from_file_without_mutating_state` | External fixture file feeds scorecard and does not persist into project state. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_invalid_prompt_injection_file_fails_loud` | Malformed fixture JSON returns non-zero with a clear error. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_prompt_boundaries_inv7.py` | Existing structural prompt-boundary regressions remain intact. |
| `tests/test_bench_phase0.py tests/test_bench_phase0_script.py` | Scorecard and CLI script contracts. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [x] `phase0_scorecard()` includes `prompt_injection_inv7`.
- [x] Missing prompt-injection fixture results report `not_available`, not pass.
- [x] Supplied fixture results produce pass/fail counts, pass rate,
  attack-success rate, by-surface summaries, and failed fixture IDs.
- [x] `scripts/bench_phase0.py --prompt-injection-file results.json` feeds the
  scorecard in memory only.
- [x] `make bench ID=<project> PROMPT_INJECTION=results.json` forwards the file.
- [x] Docs state this is a measurement substrate, not a live adversarial
  robustness claim.

> Process criteria (quality gates):
- [x] Required tests pass (`python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_prompt_boundaries_inv7.py -q`: 31 passed)
- [x] Full test suite passes (`make check`: 666 passed, 1 skipped, 8 deselected; Ruff/docs-check passed)
- [x] Type check status is reported (`make check`: type check not yet configured)
- [x] Docs updated

---

## Open Questions

- [ ] Should this use a future `prompt_eval` result schema directly? — Status:
  DEFERRED | Why it matters: full live evaluation should use `prompt_eval`, but
  this local scorecard only needs a small stable fixture-result contract.

---

## Notes

Expected external JSON shape:

```json
{
  "prompt_injection_evaluations": [
    {
      "fixture_id": "ignore-previous-thematic",
      "surface": "thematic_coding",
      "attack_type": "direct_instruction_override",
      "attack_succeeded": false,
      "evaluator": "deterministic_fixture"
    }
  ]
}
```

This intentionally scores evaluator results supplied by a separate run. It does
not run a live model attack suite inside `make bench`.
