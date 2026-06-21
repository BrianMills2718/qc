# Plan #13: INV-7 Prompt Override Guards

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-7 custom-prompt hardening; live adversarial injection evaluation

---

## Outcome

Completed 2026-06-21. `qc_clean/core/prompting.py` now provides
`render_prompt_override()`, which parses override templates and fails loudly if
required protected data placeholders are absent. `thematic_coding` requires
`{combined_text}` and `gt_constant_comparison` requires `{segment_text}` before
formatting; malformed/unknown placeholders become stage-specific `ValueError`s.
Existing valid overrides still receive already-boundaried untrusted data blocks.

This narrows one INV-7 custom-prompt failure mode, but it does not prove model
obedience, govern all possible future override surfaces, sanitize unsafe
metadata, or replace live adversarial injection evaluation. INV-7 remains
PARTIAL.

Verification: `python -m pytest tests/test_prompt_boundaries_inv7.py -q` passed
(`14 passed`) and Ruff passed on touched files before the implementation commit.
Final plan completion was verified with `make check`.

---

## Gap

**Current:** Raw and derived prompt data are rendered as untrusted `DATA>` blocks
on first-party prompt paths. Current custom override surfaces
(`thematic_coding`, `gt_constant_comparison`) receive already-boundaried
`{combined_text}` / `{segment_text}` values when the template includes those
placeholders, but an override can omit the protected placeholder entirely and
still run.

**Target:** Add a shared prompt override renderer that requires configured
protected placeholders to be present before formatting. Wire the current override
surfaces through it so an override that drops the protected data block fails
loudly.

**Why:** INV-7 is a validity invariant. A custom template that omits the
boundaried transcript segment silently turns a coding stage into an analysis of
instructions without data. Failing loudly is safer than producing plausible but
data-free output.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:260` - INV-7 remains partial because fully custom prompt overrides can misuse protected blocks.
- `CLAUDE.md` - current INV-7 status and fail-loud principle.
- `qc_clean/core/prompting.py` - current untrusted data block helpers.
- `qc_clean/core/pipeline/stages/thematic_coding.py` - `thematic_coding` prompt override path.
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` - `gt_constant_comparison` prompt override path.
- `tests/test_prompt_boundaries_inv7.py` - current prompt boundary regressions.
- Memory context: `agent-memory recall 'active decisions prompt overrides instruction data separation INV-7 qualitative_coding' --project qualitative_coding` — no active blocking decision surfaced.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
fail-loud guard around existing prompt-boundary mechanics.

---

## Capabilities

This plan modifies internal prompt construction only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/prompting.py` (modify)
- `qc_clean/core/pipeline/stages/thematic_coding.py` (modify)
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` (modify)
- `tests/test_prompt_boundaries_inv7.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV7_PROMPT_OVERRIDE_GUARDS.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `render_prompt_override()` to `qc_clean/core/prompting.py`.
2. Parse template fields with `string.Formatter` and fail loudly if required
   protected placeholders are absent.
3. Preserve normal `.format()` behavior for valid overrides and turn malformed
   templates into clear `ValueError`s naming the stage.
4. Wire `thematic_coding` to require `combined_text`.
5. Wire `gt_constant_comparison` to require `segment_text`.
6. Add tests for valid overrides still receiving boundaried data and invalid
   overrides failing before any LLM call.
7. Update docs conservatively: current override surfaces now guard required
   protected placeholders, but INV-7 remains partial until broader custom prompt
   governance and live adversarial injection evaluation land.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_prompt_boundaries_inv7.py` | `test_thematic_prompt_override_missing_combined_text_fails_loud` | A thematic override cannot omit the protected corpus block. |
| `tests/test_prompt_boundaries_inv7.py` | `test_gt_prompt_override_missing_segment_text_fails_loud` | A GT override cannot omit the protected segment block. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_prompt_boundaries_inv7.py` | Existing valid override and data-boundary contracts. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Missing protected override placeholders fail loudly with a stage-specific `ValueError`.
- [ ] Valid thematic overrides still receive `combined_text` as an untrusted data block.
- [ ] Valid GT constant-comparison overrides still receive `segment_text` as an untrusted data block.
- [ ] The guard is shared, not duplicated in each stage.
- [ ] Docs state this narrows but does not close INV-7.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should all future override-capable stages declare protected placeholders centrally? — Status: DEFERRED | Why it matters: only two override surfaces exist today; central policy becomes useful when more are added.
- [ ] Should metadata placeholders also be escaped or line-prefixed? — Status: DEFERRED | Why it matters: unsafe metadata remains an INV-7 residual gap beyond this placeholder guard.

---

## Notes

This plan does not prove model obedience. It only prevents a deterministic
operator error: custom prompt templates that accidentally drop the boundaried
data they are supposed to analyze.
