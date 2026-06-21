# Plan #32: INV-7 Fixture Runner Scaffold

## Outcome

Complete on 2026-06-21. Added deterministic structural INV-7 fixture runner
support through `qc_clean/core/inv7_fixtures.py`,
`scripts/run_inv7_fixtures.py`, and `make run-inv7-fixtures OUTPUT=inv7.json`.
The output feeds the existing `PROMPT_INJECTION=` scorecard path and is labeled
as structural prompt-construction evidence, not live model-obedience evidence.

Verification:

- `python -m pytest tests/test_inv7_fixture_runner.py tests/test_bench_phase0_script.py tests/test_prompt_boundaries_inv7.py -q`
  -> `31 passed`
- `make check` -> `699 passed, 1 skipped, 8 deselected`; ruff, docs-check,
  plan status sync, and AGENTS sync passed; type check not yet configured

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** INV-7 prompt boundary tests; INV-7 prompt injection scorecard
**Blocks:** live adversarial prompt-injection benchmark; prompt_eval-backed INV-7 evaluation

---

## Gap

**Current:** INV-7 has deterministic prompt-boundary regression tests and a
Phase 0 scorecard section that can score externally supplied
`prompt_injection_evaluations`, but there is no agent-drivable runner that
produces that result file shape. Operators must manually author
`PROMPT_INJECTION=inv7.json` inputs, which makes the scorecard substrate hard to
use consistently.

**Target:** Add a deterministic INV-7 fixture runner scaffold that emits the
existing `prompt_injection_evaluations` JSON shape for structural boundary
fixtures. The runner should write results usable directly with
`make bench PROMPT_INJECTION=<file>`. It should clearly label its evaluator as a
structural prompt-construction check, not a live model-obedience benchmark.

**Why:** This converts existing INV-7 prompt-capture coverage into a reusable
artifact path and prepares the interface for future live adversarial runs. It
does not prove prompt injection is solved because structural prompt isolation is
not the same as model obedience under attack.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - INV-7 fixture scorecard status and live
  benchmark gap.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-7 claim discipline and remaining
  gaps.
- `docs/plans/completed/INV7_INSTRUCTION_DATA_SEPARATION.md` - raw-data prompt
  boundary slice.
- `docs/plans/completed/INV7_DERIVED_OUTPUT_PROMPT_BOUNDARIES.md` - derived data
  boundary slice.
- `docs/plans/completed/INV7_PROMPT_INJECTION_SCORECARD.md` - existing fixture
  outcome schema and scorecard.
- `tests/test_prompt_boundaries_inv7.py` - current deterministic fixtures.
- `qc_clean/core/bench.py` - `PromptInjectionEvaluation` and scorecard shape.
- Memory context:
  `agent-memory recall 'active decisions qualitative_coding INV-7 prompt injection fixture runner live benchmark' --project qualitative_coding`
  returned historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research is needed. This is a repo-local runner around existing
structural fixture coverage. The live adversarial model benchmark remains a
future plan because it needs model/provider policy, budget controls, and
prompt_eval integration.

---

## Capabilities

| Capability | Input | Output | Owner |
|------------|-------|--------|-------|
| `run_inv7_structural_fixtures` | Built-in fixture definitions | JSON `prompt_injection_evaluations` file | qualitative_coding |

This is not a live LLM benchmark and not a prompt_eval experiment runner.

---

## Result Contract

The runner writes:

```json
{
  "schema_version": 1,
  "evaluator": "structural_boundary",
  "mode": "structural",
  "prompt_injection_evaluations": [
    {
      "fixture_id": "thematic-raw-direct-override",
      "surface": "thematic_coding",
      "attack_type": "direct_instruction_override",
      "attack_succeeded": false,
      "failure_mode": null,
      "evaluator": "structural_boundary",
      "notes": "Prompt kept the adversarial payload on DATA> lines."
    }
  ]
}
```

The existing Phase 0 bench loader already accepts an object with
`prompt_injection_evaluations`, so this output should be directly consumable by
`make bench ID=<project> PROMPT_INJECTION=<output>`.

---

## Files Affected

- `qc_clean/core/inv7_fixtures.py` (create)
- `scripts/run_inv7_fixtures.py` (create)
- `Makefile` (modify)
- `tests/test_inv7_fixture_runner.py` (create)
- `tests/test_bench_phase0_script.py` (modify if needed for runner output compatibility)
- `docs/EVALUATION_HARNESS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify after closeout)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV7_FIXTURE_RUNNER_SCAFFOLD.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `qc_clean/core/inv7_fixtures.py` with typed structural fixture results
   and a small set of built-in fixture checks covering raw transcript, derived
   output, and codebook-context prompt boundaries.
2. Implement structural checks by verifying adversarial payload lines appear
   only as `DATA>` lines in rendered prompt/context text.
3. Add `scripts/run_inv7_fixtures.py --output inv7.json` that writes the result
   contract and exits non-zero only on runner/schema failure, not on attack
   failure. Attack failures are data in the output.
4. Add `make run-inv7-fixtures OUTPUT=inv7.json`.
5. Add tests for JSON output shape, mixed pass/fail accounting, and bench
   compatibility through `PROMPT_INJECTION=`.
6. Update docs to say the runner is structural and deterministic; no live
   adversarial model benchmark has run.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_inv7_fixture_runner.py` | `test_run_inv7_structural_fixtures_returns_scorecard_compatible_payload` | Built-in runner emits `prompt_injection_evaluations` with stable fields. |
| `tests/test_inv7_fixture_runner.py` | `test_run_inv7_fixture_script_writes_json_output` | Script writes JSON output and reports fixture counts. |
| `tests/test_inv7_fixture_runner.py` | `test_structural_fixture_marks_unwrapped_attack_as_success` | Runner can represent a failed boundary as `attack_succeeded=true`. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_inv7_runner_output_file` | Runner output feeds `--prompt-injection-file` and scores through Phase 0. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_prompt_boundaries_inv7.py` | Existing direct prompt-boundary regressions remain intact. |
| `tests/test_bench_phase0_script.py` | Existing externally supplied INV-7 scorecard behavior remains intact. |
| `make docs-check` | Verify docs, plan status, and AGENTS sync. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [x] A deterministic INV-7 fixture runner exists.
- [x] Runner output matches the existing `prompt_injection_evaluations` shape.
- [x] Runner output can be consumed by `bench_phase0 --prompt-injection-file`.
- [x] A Makefile target runs the fixture runner.
- [x] The runner explicitly labels itself `mode=structural` /
  `evaluator=structural_boundary`.
- [x] Docs state this is not a live adversarial model benchmark and does not
  prove prompt-injection robustness.

> Process criteria (quality gates):
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status is reported
- [x] Docs updated

---

## Open Questions

- [ ] What model/provider policy should the future live INV-7 runner use?
  - Status: DEFERRED | Why it matters: live evaluation needs model selection,
  budget controls, observability traces, and possibly cross-model comparison.
- [ ] Should live INV-7 evaluation be owned by prompt_eval directly?
  - Status: DEFERRED | Why it matters: statistical comparison and experiment
  tracking belong in prompt_eval; this slice only emits the current scorecard
  input shape.

---

## Notes

Do not claim prompt injection is solved. Structural boundary checks are necessary
but not sufficient evidence of model obedience under adversarial input.
