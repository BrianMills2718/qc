# Plan #107: Prompt Override Placeholder Policy

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** INV-7 strict prompt override placeholders
**Blocks:** broader custom-prompt governance; future metadata-exposure review

---

## Outcome

Implemented and pushed in commit `759a1b0`:

- Extended `render_prompt_override` with explicit required data, optional data,
  and metadata placeholder declarations.
- Added fail-loud checks for renderer value keys not declared in one of those
  roles.
- Updated thematic coding to declare `{num_interviews}` as metadata.
- Updated GT constant-comparison to declare `{codebook_context}` as optional
  protected data and `{seg_idx}`, `{total_segments}`, `{doc_name}` as metadata.
- Added renderer-level tests for undeclared values, declared metadata, and
  optional data placeholders.
- Updated INV-7 docs to record explicit placeholder exposure policy while
  preserving the prompt-injection caveat.

Verification:

- `python -m pytest tests/test_prompt_boundaries_inv7.py -q` failed before
  implementation on the new policy tests, as expected.
- `python -m pytest tests/test_prompt_boundaries_inv7.py
  tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py
  -q` -> 30 passed.
- `python -m ruff check qc_clean/core/prompting.py
  qc_clean/core/pipeline/stages/thematic_coding.py
  qc_clean/core/pipeline/stages/gt_constant_comparison.py
  tests/test_prompt_boundaries_inv7.py` -> passed.
- `make docs-check` -> passed.
- `make check` -> 914 passed, 1 skipped, 8 deselected; Ruff/docs green; type
  check not yet configured.

---

## Gap

**Current:** Prompt overrides fail loudly for missing protected data
placeholders, unknown template placeholders, item/attribute access, conversions,
and format specs. However, the policy for *which metadata placeholders a stage
may expose* is implicit in each call's `values` dictionary. That leaves a future
footgun: a stage can accidentally pass a new metadata value and make it
available to operator-authored prompt overrides without an explicit exposure
decision.

**Target:** Make metadata exposure explicit at the shared renderer boundary:

- Extend `render_prompt_override(...)` to distinguish:
  - required protected data placeholders;
  - optional protected data placeholders;
  - explicitly declared metadata placeholders.
- Fail loud if the stage passes any value key that is not declared in one of
  those sets.
- Keep existing template checks:
  - required protected data placeholders must be present;
  - unknown template placeholders fail;
  - non-bare placeholders fail.
- Update existing override surfaces:
  - `thematic_coding`: required data `{combined_text}`, metadata
    `{num_interviews}`;
  - `gt_constant_comparison`: required data `{segment_text}`, optional data
    `{codebook_context}`, metadata `{seg_idx, total_segments, doc_name}`.
- Document this as an INV-7 custom-prompt governance slice, not proof of prompt
  injection robustness.

**Why:** This makes future metadata exposure reviewable in code and tests. A
stage cannot quietly add a new `{metadata}` channel just because it passed a new
value into the renderer.

---

## References Reviewed

- `qc_clean/core/prompting.py` - shared override renderer.
- `qc_clean/core/pipeline/stages/thematic_coding.py` - thematic override values.
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` - GT override values.
- `tests/test_prompt_boundaries_inv7.py` - INV-7 prompt-boundary and override
  regressions.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-7 status and remaining metadata
  exposure policy gap.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research required. This is a deterministic policy hardening slice
for existing prompt override contracts.

---

## Capabilities

Internal prompt-rendering governance only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `render_prompt_override_with_declared_placeholders` | template + declared data/metadata placeholders + values | rendered prompt or ValueError | qualitative_coding | prompt override surfaces | free |

### Capability Validation

- [x] Undeclared value keys fail loud before rendering.
- [x] Declared metadata placeholders remain usable.
- [x] Required protected data placeholders are still required.
- [x] Optional data placeholders can be used but are not required.
- [x] Existing thematic and GT override tests still pass.

---

## Files Affected

- `qc_clean/core/prompting.py` (modify)
- `qc_clean/core/pipeline/stages/thematic_coding.py` (modify)
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` (modify)
- `tests/test_prompt_boundaries_inv7.py` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add TDD tests for undeclared renderer values, declared metadata usability,
   optional data placeholder usability, and existing stage compatibility.
2. Extend `render_prompt_override` with explicit optional-data and metadata
   placeholder declarations.
3. Update thematic and GT stage calls to declare their existing placeholders.
4. Update docs to state explicit metadata exposure policy exists while prompt
   injection remains unsolved.
5. Run focused tests, focused Ruff, docs checks, and full `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Changed Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_prompt_boundaries_inv7.py` | `test_prompt_override_rejects_undeclared_renderer_values` | Stage authors cannot pass undeclared metadata/value channels. |
| `tests/test_prompt_boundaries_inv7.py` | `test_prompt_override_allows_declared_metadata_placeholders` | Declared metadata placeholders can be used. |
| `tests/test_prompt_boundaries_inv7.py` | `test_prompt_override_allows_declared_optional_data_placeholders` | Optional protected data placeholders are allowed but not required. |
| `tests/test_prompt_boundaries_inv7.py` | existing thematic/GT override tests | Existing behavior remains compatible with explicit declarations. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_prompt_boundaries_inv7.py` | INV-7 boundary regressions remain green. |
| `tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py` | INV-7 package/fixture surfaces remain unchanged. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Shared renderer rejects value keys not declared as required data,
  optional data, or metadata placeholders.
- [x] Shared renderer still rejects unknown template placeholders.
- [x] Shared renderer still rejects transformed/non-bare placeholders.
- [x] Existing thematic override can use `{combined_text}` and
  `{num_interviews}`.
- [x] Existing GT override can use `{segment_text}`, `{codebook_context}`,
  `{seg_idx}`, `{total_segments}`, and `{doc_name}`.
- [x] Docs state this is metadata-exposure governance, not prompt-injection
  robustness evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should override placeholder declarations become a typed registry per
  stage? — Status: DEFERRED | Why it matters: two surfaces exist today, so
  explicit call-site declarations are enough for this slice. A registry becomes
  useful when more stages expose overrides.

---

## Notes

This narrows operator-authored prompt override governance. It still does not
prove model obedience to the resulting instructions.
