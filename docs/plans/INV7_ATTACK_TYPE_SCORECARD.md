# Plan #69: INV-7 Attack-Type Scorecard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-7 adversarial benchmark interpretation; future committed live prompt-injection benchmark protocol

---

## Gap

**Current:** INV-7 prompt-injection fixture records include `attack_type`, and
the structural/live fixture runners populate it. The Phase 0 scorecard reports
overall fixture rates and per-surface rates, but it drops the attack-type
dimension.

**Target:** `prompt_injection_inv7` reports `by_attack_type` summaries with the
same total/pass/fail counts, failed fixture IDs, pass rate, attack-success rate,
and Wilson intervals already used by `by_surface`.

**Why:** Attack class is the unit a reviewer needs to see when a fixture suite
mixes direct overrides, derived-output attacks, boundary breakouts, and other
payload families. Surface-only grouping can hide concentration of failures by
attack class.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - INV-7 scorecard status and claim discipline.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-7 invariant status and roadmap.
- `qc_clean/core/bench.py` - current prompt-injection scorecard and Wilson
  interval implementation.
- `qc_clean/core/inv7_fixtures.py` - structural/live fixture contracts carrying
  `attack_type`.
- `tests/test_bench_phase0.py` - direct INV-7 scorecard coverage.
- `tests/test_bench_phase0_script.py` - external-file INV-7 scorecard coverage.
- Memory context: unavailable. Prior repeated
  `agent-memory recall ... --project qualitative_coding` calls in this sprint
  failed with OpenRouter 402/403 provider errors; circuit breaker is active.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a repo-local
scorecard stratification over an already modeled fixture field.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| INV-7 prompt-injection attack-type scorecard | `ProjectState.config.extra["prompt_injection_evaluations"]` | `prompt_injection_inv7.by_attack_type` rate/interval summaries | qualitative_coding | `make bench`, `qc_cli.py bench`, benchmark artifacts | free |

### Capability Validation

- [x] Input records already use `PromptInjectionEvaluation` with Pydantic field
  descriptions.
- [ ] Scorecard output is covered by focused tests and full docs checks.
- [ ] No new cross-project callable boundary is introduced.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV7_ATTACK_TYPE_SCORECARD.md` (create, then move to completed at closeout)

---

## Plan

### Steps

1. Extract the current surface-grouping logic into a small reusable INV-7
   grouping helper.
2. Keep existing `by_surface` output unchanged.
3. Add `by_attack_type` output using the same counts, rates, failed IDs, and
   Wilson intervals.
4. Add focused direct and script-path tests for the new dimension.
5. Update docs without changing the existing prompt-injection caveats.
6. Run focused tests, plan sync, docs checks, and full `make check`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_scores_prompt_injection_fixture_results` | Direct scorecard output includes correct `by_attack_type` counts/rates/intervals. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_prompt_injection_from_file_without_mutating_state` | External-file path surfaces `by_attack_type` and still avoids persisted state mutation. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0.py -k "prompt_injection" -q` | Focused INV-7 scorecard behavior. |
| `python -m pytest tests/test_bench_phase0_script.py -k "prompt_injection" -q` | External-file INV-7 path. |
| `python scripts/sync_plan_status.py --check` | Plan registry consistency. |
| `python scripts/check_markdown_links.py` | Docs link integrity. |
| `make check` | Full deterministic project gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] INV-7 scored output includes `by_attack_type`.
- [ ] Each attack-type summary includes total, passed, failed, failed fixture
  IDs, pass rate, attack-success rate, and Wilson intervals.
- [ ] Existing overall and `by_surface` fields remain unchanged.
- [ ] External-file scoring path includes the new field without mutating saved
  project state.
- [ ] Docs preserve the claim boundary: this is stratified fixture accounting,
  not proof of prompt-injection robustness.

> Process criteria:
- [ ] Focused tests pass.
- [ ] Plan sync passes.
- [ ] Markdown link check passes.
- [ ] Full `make check` passes, or any non-codebase failure is recorded.
- [ ] Verified implementation is committed and pushed.

---

## Open Questions

- [ ] Should future INV-7 packages require a pre-registered attack taxonomy and
  minimum fixture count per class? - Status: DEFERRED | Why it matters:
  robustness claims need coverage rules, but this slice only reports supplied
  fixture outcomes.

---

## Notes

- The helper should not change current field names or rate semantics.
- No live fixtures are run in this slice.
