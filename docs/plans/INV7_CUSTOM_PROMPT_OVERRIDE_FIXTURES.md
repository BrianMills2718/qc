# Plan #168: INV-7 Custom Prompt Override Fixtures

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** INV-7 fixture runner scaffold; INV-7 live fixture runner; INV-7 prompt override guardrail wrapper
**Blocks:** broader committed INV-7 adversarial benchmark evidence

---

## Gap

**Current:** The built-in INV-7 structural/live fixture sets cover raw
transcript data, derived output, boundary breakout, and incremental codebook
context. They do not exercise the registered custom prompt override surfaces,
even though custom overrides are named as remaining INV-7 risk.

**Target:** Add built-in deterministic structural fixtures and opt-in live
canary fixtures for the current custom override surfaces:

- `thematic_coding` prompt overrides with `{combined_text}`.
- `gt_constant_comparison` prompt overrides with `{segment_text}` and optional
  `{codebook_context}`.

The fixtures must use the actual `render_prompt_override()` wrapper so they
exercise the same repo-owned boundary/reminder text used in production.

**Why:** The repo has strong unit tests for override validation, but the
agent-drivable INV-7 fixture package omits those surfaces. Adding them makes
structural and live canary packages more representative while preserving the
claim boundary: fixture coverage is not proof of model obedience or
prompt-injection robustness.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §13.1 and §18 - INV-7 status and remaining
  custom-prompt/live benchmark gaps.
- `docs/EVALUATION_HARNESS.md` - INV-7 fixture/package scorecard caveats.
- `docs/plans/completed/INV7_FIXTURE_RUNNER_SCAFFOLD.md` - structural fixture
  runner contract.
- `docs/plans/completed/INV7_LIVE_FIXTURE_RUNNER.md` - opt-in live fixture
  runner contract.
- `docs/plans/completed/INV7_PROMPT_OVERRIDE_GUARDRAIL_WRAPPER.md` - custom
  override wrapper behavior and claim limits.
- `qc_clean/core/inv7_fixtures.py` - current structural/live fixture sets.
- `qc_clean/core/prompting.py` - `render_prompt_override()` and boundary wrapper.
- `qc_clean/core/prompt_override_registry.py` - current override surfaces and
  declared placeholders.
- `tests/test_inv7_fixture_runner.py` and `tests/test_prompt_boundaries_inv7.py`
  - current fixture and override coverage.
- Memory context:
  `agent-memory recall 'qualitative_coding next deterministic roadmap lane INV-7 INV-2 D7 benchmark live baseline' --project qualitative_coding`
  - low-relevance historical findings only, no active conflicting decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active
  claim files.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a repo-local fixture
coverage slice over existing INV-7 prompt-override contracts.

---

## Capabilities

Internal fixture-runner capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `run_inv7_structural_fixtures` | built-in fixture definitions | INV-7 package JSON | qualitative_coding | `make bench`, `qc_cli.py bench`, artifact packages | free |
| `run_inv7_live_fixtures_async` | built-in live fixtures + model config | INV-7 package JSON | qualitative_coding | `make bench`, `qc_cli.py bench`, artifact packages | paid LLM |

### Capability Validation

Skipped for cross-project registry purposes: these are existing internal
project capabilities, and this plan only expands their built-in fixture sets.

---

## Files Affected

- `docs/plans/INV7_CUSTOM_PROMPT_OVERRIDE_FIXTURES.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `qc_clean/core/inv7_fixtures.py` - add custom override structural/live
  fixtures.
- `tests/test_inv7_fixture_runner.py` - add fixture coverage tests.
- Docs after implementation:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/PROJECT_THEORY_AND_GOALS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Add helper functions in `qc_clean/core/inv7_fixtures.py` that render
   thematic and GT custom override prompts through `render_prompt_override()`
   using the current registry declarations.
2. Add two structural fixtures:
   - thematic override with malicious `{combined_text}` payload;
   - GT override with malicious `{segment_text}` and optional
     `{codebook_context}` payloads.
3. Add two live canary fixtures using the same custom override wrapper and a
   `VALIDATED` forbidden marker.
4. Add tests that the default structural payload includes the custom override
   surfaces, that those structural fixtures pass, and that the live fixture set
   carries prompt hashes for the new custom override fixtures.
5. Update docs conservatively: the built-in fixture suite now covers custom
   override surfaces, but this remains fixture coverage, not robustness proof.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_inv7_fixture_runner.py` | `test_default_structural_fixtures_include_custom_prompt_overrides` | Built-in structural suite includes thematic and GT custom override surfaces and they pass structural checks. |
| `tests/test_inv7_fixture_runner.py` | `test_default_live_fixtures_include_custom_prompt_overrides` | Built-in live canary suite includes custom override fixtures with stable prompt hashes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_inv7_fixture_runner.py tests/test_prompt_boundaries_inv7.py -q` | INV-7 fixture and override regressions. |
| `make lint-prompt-overrides` | Registry/source governance remains intact. |
| targeted Ruff on touched Python files | Style/syntax gate before full check. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before implementation closeout. |

---

## Acceptance Criteria

- [ ] Structural fixtures include custom prompt override coverage for
  `thematic_coding` and `gt_constant_comparison`.
- [ ] Live fixtures include custom prompt override canaries for those surfaces.
- [ ] The custom override fixtures render through `render_prompt_override()`,
  not hand-built wrapper strings.
- [ ] Existing package schema, scorecard compatibility, and Make/CLI surfaces
  remain unchanged.
- [ ] Docs state this expands fixture coverage only and does not prove
  prompt-injection robustness, model obedience, methodological validity, or
  SOTA.
- [ ] Required tests and gates pass.

---

## Open Questions

- [x] Should this run a live model and commit new live outcomes?
  Status: RESOLVED. No. This slice expands the fixture set deterministically.
  Committed live outcomes require a separate protocol/result artifact lane and
  should not be mixed with fixture-definition changes.

---

## Notes

The live fixtures remain opt-in. They define prompts and expected canary
markers; they do not spend model budget unless an operator runs
`run-inv7-live-fixtures`.
