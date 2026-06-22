# Plan #83: INV-7 Strict Prompt Override Placeholders

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-7 custom-prompt governance; future prompt-injection benchmark protocol

---

## Gap

**Current:** Current prompt override guards require protected root placeholder
names such as `{combined_text}` and `{segment_text}`. Because validation only
checks the root name, an override can still satisfy the guard with transformed
fields such as `{combined_text[0]}` or `{combined_text!r}`, which can drop or
reshape the already-boundaried data block. Unknown metadata-like placeholders
fail during formatting, but the allowed placeholder contract is not explicit.

**Target:** Make prompt overrides use bare, declared placeholders only. Reject
attribute access, item access, conversion flags, format specs, automatic
positional fields, and undeclared placeholders before any LLM call. Keep valid
current overrides working.

**Why:** INV-7 is a validity invariant. A custom prompt template that slices,
repr-converts, or indirectly formats a protected data block can silently turn a
guarded data boundary into a weaker or data-free prompt. Failing loudly is the
right behavior for override syntax that can alter protected untrusted-data
blocks or smuggle unsafe metadata into the prompt surface.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:360` - INV-7 remains partial because broader custom-prompt governance and unsafe metadata remain residual gaps.
- `docs/plans/completed/INV7_PROMPT_OVERRIDE_GUARDS.md` - prior first guard and deferred metadata-placeholder question.
- `docs/plans/completed/INV7_DERIVED_OUTPUT_PROMPT_BOUNDARIES.md` - prior deferred question about stricter override governance.
- `qc_clean/core/prompting.py` - current untrusted-data and prompt override helpers.
- `qc_clean/core/pipeline/pipeline_engine.py` - `PipelineContext.prompt_overrides` contract.
- `qc_clean/core/pipeline/stages/thematic_coding.py` - `thematic_coding` override surface.
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` - `gt_constant_comparison` override surface.
- `tests/test_prompt_boundaries_inv7.py` - existing INV-7 prompt-capture regressions.
- Memory context: not retried in this slice because `agent-memory recall` has hit repeated OpenRouter 402/403 failures in this long-running session; circuit breaker is active and there is no new information that would make another retry useful.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic fail-loud tightening of an already-identified INV-7 override
contract.

---

## Capabilities

This plan modifies internal prompt construction only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/prompting.py` (modify)
- `tests/test_prompt_boundaries_inv7.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV7_STRICT_PROMPT_OVERRIDE_PLACEHOLDERS.md` (create, then move to completed)

---

## Plan

### Steps

1. Tighten `render_prompt_override()` parsing so every placeholder must be a
   bare declared field from the supplied values.
2. Fail loudly for protected-placeholder item access, attribute access,
   conversion flags, format specs, and automatic positional fields.
3. Fail loudly for undeclared placeholders such as metadata placeholders that
   the stage did not explicitly supply.
4. Preserve valid existing thematic and GT override behavior.
5. Add prompt-boundary regressions proving transformed protected placeholders
   and undeclared metadata placeholders fail before any LLM call.
6. Update docs conservatively: this narrows INV-7 custom-prompt governance but
   does not prove model obedience or solve prompt injection.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_prompt_boundaries_inv7.py` | `test_thematic_prompt_override_rejects_indexed_combined_text` | `{combined_text[0]}` cannot satisfy the protected placeholder requirement. |
| `tests/test_prompt_boundaries_inv7.py` | `test_thematic_prompt_override_rejects_repr_combined_text` | `{combined_text!r}` cannot transform the protected data block. |
| `tests/test_prompt_boundaries_inv7.py` | `test_thematic_prompt_override_rejects_undeclared_metadata_placeholder` | Metadata-like placeholders are not available unless a stage explicitly supplies them. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_prompt_boundaries_inv7.py -q` | Full INV-7 prompt-boundary regression suite. |
| `make check` | Full deterministic repo gate, lint, and docs checks. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Valid existing prompt overrides still render and receive protected data blocks.
- [x] Protected placeholders must be exact bare placeholders, not indexed, attributed, converted, or format-specified.
- [x] Undeclared metadata-like placeholders fail loudly before any LLM call.
- [x] Error messages name the affected stage and problematic placeholder syntax.
- [x] INV-7 docs remain conservative and do not claim prompt injection is solved.

> Process criteria:
- [x] Required focused tests pass.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Verification

- `python -m pytest tests/test_prompt_boundaries_inv7.py -k "indexed_combined_text or repr_combined_text or undeclared_metadata_placeholder" -q` - first failed against the old parser (`2 failed, 1 passed`), then passed after implementation (`3 passed, 14 deselected`).
- `python -m pytest tests/test_prompt_boundaries_inv7.py -q` - `17 passed`.
- `python -m ruff check qc_clean/core/prompting.py tests/test_prompt_boundaries_inv7.py` - passed.
- `python scripts/meta/check_agents_sync.py --check` - passed.
- `python scripts/sync_plan_status.py --check && python scripts/check_markdown_links.py` - passed.
- `make check` - `807 passed, 1 skipped, 8 deselected`; Ruff and docs checks passed; type check is not yet configured.

---

## Open Questions

- [ ] Should future override-capable stages declare placeholder contracts in a central registry? - Status: DEFERRED | Why it matters: there are still only two override-capable stages today, so centralizing now would add structure without a second consumer.
- [ ] Should custom prompt overrides require a full threat-model document before being enabled for new stages? - Status: DEFERRED | Why it matters: this slice tightens syntax only; it does not govern arbitrary operator-authored instructions around the protected block.

---

## Notes

This is a structural guard. It does not prove that a model obeys the
untrusted-data boundary, and it does not replace live adversarial prompt
injection evaluation.
