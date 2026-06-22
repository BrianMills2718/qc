# Plan #165: INV-7 Prompt Override Guardrail Wrapper

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** broader INV-7 custom-prompt governance

---

## Outcome

Rendered custom prompt overrides are now bookended by a repo-owned
instruction/data-separation wrapper in `qc_clean/core/prompting.py`.
`render_prompt_override()` still performs the existing placeholder declaration,
bare-placeholder syntax, data-value, and metadata-value validations first. Only
after a template passes validation and formats successfully does the renderer
wrap the operator-authored prompt template with:

- `BEGIN CUSTOM PROMPT OVERRIDE`;
- stage-name metadata for prompt observability;
- a repo-owned reminder that untrusted-data blocks and `DATA>` lines remain
  source data only;
- the rendered operator-authored prompt template;
- `REPOSITORY DATA-BOUNDARY REMINDER` after the operator template; and
- `END CUSTOM PROMPT OVERRIDE`.

The regression suite now proves valid thematic and GT constant-comparison
overrides still receive boundaried data blocks, and a valid operator template
that places contradictory text after `{combined_text}` is still followed by the
repo-owned final boundary reminder.

Implementation commit: `abf8a39`
(`Wrap INV-7 prompt overrides with boundary reminder`).

Verification:

- Initial focused prompt-override test failed before implementation because
  the wrapper constants/behavior did not exist.
- `python -m pytest tests/test_prompt_boundaries_inv7.py -k "prompt_override" -q`
  -> 16 passed, 10 deselected.
- `python -m pytest tests/test_prompt_boundaries_inv7.py tests/test_prompt_override_registry.py -q`
  -> 30 passed.
- `make lint-prompt-overrides` -> passed.
- `python -m ruff check qc_clean/core/prompting.py tests/test_prompt_boundaries_inv7.py`
  -> passed.
- `make docs-check` -> passed.
- `git diff --check` -> passed.
- Direct render sanity check confirmed the repo reminder appears after
  contradictory operator text and the prompt ends with `END CUSTOM PROMPT
  OVERRIDE`.
- `make check` -> 1122 passed, 1 skipped, 8 deselected; Ruff and docs gates
  passed.

This is deterministic custom-prompt governance only. It does not prove model
obedience, prompt-injection robustness, held-out adversarial benchmark
performance, methodological validity, or SOTA.

---

## Gap

**Current:** Custom prompt override surfaces enforce declared placeholders,
bare placeholder syntax, untrusted-data block values for data placeholders, and
single-line scalar metadata. A valid operator-authored template can still place
contradictory instructions before or after `{combined_text}` / `{segment_text}`
and make that operator text the final wording in the prompt.

**Target:** Make every rendered custom prompt override carry a repo-owned
instruction/data-separation wrapper:

- a stable header before the operator-authored template;
- the rendered operator-authored template unchanged inside the wrapper;
- a stable footer/reminder after the operator-authored template, so the final
  prompt text restates that source-data blocks and `DATA>` lines are data only.

This is deterministic custom-prompt governance only. It does not prove model
obedience, prompt-injection robustness, methodological validity, or SOTA.

**Why:** Existing guardrails protect the data values and placeholder exposure
policy, but they do not ensure the repo's instruction/data-separation policy is
present after arbitrary operator-authored override text. A wrapper is a small,
auditable improvement that preserves custom overrides while reducing the chance
that runtime templates omit or bury the boundary instruction.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §13.1 and §18 - INV-7 remaining
  custom-prompt governance caveats and claim discipline.
- `docs/EVALUATION_HARNESS.md` - current INV-7 fixture/package/scorecard
  framing and caveats.
- `qc_clean/core/prompting.py` - current untrusted-data block and prompt
  override renderer.
- `qc_clean/core/prompt_override_registry.py` - supported override surfaces and
  declared data/metadata placeholders.
- `qc_clean/core/pipeline/stages/thematic_coding.py` - thematic override call
  site.
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` - GT constant
  comparison override call site.
- `tests/test_prompt_boundaries_inv7.py` - current INV-7 prompt boundary
  regression suite.
- `tests/test_prompt_override_registry.py` and
  `scripts/check_prompt_override_registry.py` - registry/source governance.
- Memory context:
  `agent-memory recall 'active decisions' --project qualitative_coding`;
  `agent-memory recall 'qualitative_coding remaining roadmap INV-7 custom prompt governance INV-11 recompute' --project qualitative_coding`
  - low-relevance historical findings only, no active conflicting decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active
  claim files.

---

## Research Basis For This Slice

No external research is required. This is a deterministic prompt-construction
and regression-test slice over existing repo-local contracts.

---

## Capabilities

Internal rendering capability only; no cross-project boundary or reusable tool
is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `render_prompt_override` wrapper | stage name, template, declared placeholders, rendered values | wrapped prompt string or `ValueError` | qualitative_coding | custom prompt override call sites | free |

---

## Files Affected

- `docs/plans/INV7_PROMPT_OVERRIDE_GUARDRAIL_WRAPPER.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - active sprint checkpoint.
- `qc_clean/core/prompting.py` - add the repo-owned wrapper around rendered
  custom prompt overrides.
- `tests/test_prompt_boundaries_inv7.py` - update existing override assertions
  and add adversarial trailing-operator-instruction regression coverage.
- `docs/PROJECT_THEORY_AND_GOALS.md`, `docs/EVALUATION_HARNESS.md`, and
  `CLAUDE.md` - status wording after implementation succeeds.

---

## Implementation Plan

1. Add stable custom-override wrapper text in `qc_clean/core/prompting.py`.
2. After existing placeholder/value validation and `template.format(...)`,
   return the wrapped prompt rather than the raw rendered template.
3. Keep the rendered operator-authored template intact inside the wrapper; this
   lane must not rewrite or censor operator instructions.
4. Include the stage name in the wrapper for observability.
5. Put the final boundary reminder after the operator template, and make tests
   assert that contradictory trailing operator text is not the final prompt
   text.
6. Update existing override tests that currently expect the custom template to
   start the prompt.
7. Update status docs without claiming the gap is fully closed.

---

## Acceptance Criteria

| Check | Pass condition |
|-------|----------------|
| Wrapper placement | Rendered custom override prompts start with a repo-owned custom-override boundary header, contain the rendered operator template, and end with the repo-owned data-boundary reminder. |
| Runtime surfaces | Thematic and GT constant-comparison prompt overrides still include the protected untrusted-data blocks and valid metadata values. |
| Adversarial regression | A valid override template with contradictory text after `{combined_text}` is still followed by the repo-owned final boundary reminder. |
| Existing strictness | Missing/unknown/transformed placeholders, unwrapped data values, and unsafe metadata values still fail before any LLM call. |
| Registry governance | `make lint-prompt-overrides` still passes. |
| Claim discipline | Docs say this is custom-prompt governance only, not model-obedience or robustness proof. |

---

## Verification

| Command | Expected |
|---------|----------|
| `python -m pytest tests/test_prompt_boundaries_inv7.py -k "prompt_override" -q` | Focused prompt-override regressions pass |
| `python -m pytest tests/test_prompt_boundaries_inv7.py tests/test_prompt_override_registry.py -q` | INV-7 boundary and registry suites pass |
| `make lint-prompt-overrides` | Source/registry governance check passes |
| `python -m ruff check qc_clean/core/prompting.py tests/test_prompt_boundaries_inv7.py` | Touched Python lint passes |
| `make docs-check` | Plan index, links, coupling, and AGENTS sync pass |
| `git diff --check` | No whitespace errors |
| `make check` | Full deterministic gate passes |

---

## Failure Modes

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Existing tests expect prompt to start with operator template | Tests are asserting the pre-wrapper contract | Update tests to assert operator template is inside the wrapper and untrusted data remains protected |
| Wrapper breaks placeholder validation errors | Wrapper was applied before validation | Keep wrapper after existing validation and formatting |
| Wrapper creates overclaim wording | Docs or wrapper text implies solved injection/model obedience | Revise wording to "instruction/data-separation policy" and "not robustness evidence" |
| Full `make check` fails outside touched prompt override surfaces | Inspect failure; only fix if causally related, otherwise record and choose the next highest-value lane per sprint rules |

---

## Claim Discipline

This plan may say custom prompt overrides are now automatically bookended by a
repo-owned instruction/data-separation reminder. It must not say prompt
injection is solved, model obedience is proven, held-out adversarial evaluation
passed, methodological validity is established, or the system is SOTA.
