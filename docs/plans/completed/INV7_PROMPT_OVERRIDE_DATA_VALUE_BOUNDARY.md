# Plan #157: INV-7 Prompt Override Data Value Boundary

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** `render_prompt_override()` knows which placeholders are required or
optional protected data, and it requires custom templates to include required
data placeholders as bare fields. It does not independently verify that the
values supplied for those data placeholders are actually untrusted-data blocks.

**Target:** Prompt override rendering fails loudly when a required or optional
data placeholder value is raw/unwrapped text. Metadata placeholders remain
unrestricted scalar values.

**Why:** This tightens INV-7 at the renderer boundary. If a future stage wires a
prompt override with raw transcript, segment, or derived-output text, the shared
renderer should catch it before any LLM call.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 item 6 - INV-7 remaining work includes
  broader custom-prompt threat-model tightening.
- `CLAUDE.md` - current INV-7 status and claim discipline.
- `qc_clean/core/prompting.py` - untrusted data block formatter and prompt
  override renderer.
- `qc_clean/core/prompt_override_registry.py` - required/optional
  data-placeholder declarations.
- `tests/test_prompt_boundaries_inv7.py` - existing INV-7 prompt boundary and
  prompt override tests.
- Memory context:
  `agent-memory recall 'INV-7 prompt override data placeholder value validation qualitative_coding' --project qualitative_coding`
  - 2 low-relevance historical findings, no active conflicting decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this strengthens an existing internal prompt-rendering boundary and
does not create a new cross-project capability.

---

## Files Affected

- `qc_clean/core/prompting.py` - validate data-placeholder values before
  rendering prompt overrides.
- `tests/test_prompt_boundaries_inv7.py` - add regression tests for raw required
  and optional data placeholder values.
- `CLAUDE.md` - update INV-7 current-state wording after implementation.
- `docs/PROJECT_THEORY_AND_GOALS.md` - update INV-7 roadmap/status wording.
- `AGENTS.md` - regenerated after `CLAUDE.md` changes.

---

## Plan

### Steps

1. Add failing tests that pass raw text for required and optional data
   placeholders and expect `render_prompt_override()` to raise before rendering.
2. Implement data-placeholder value validation in `render_prompt_override()`.
3. Ensure existing valid prompt override tests still pass.
4. Update current-state docs without claiming prompt-injection robustness.
5. Run focused tests, docs checks, and `make check`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_prompt_boundaries_inv7.py` | `test_prompt_override_rejects_unwrapped_required_data_value` | Required data placeholders must be untrusted-data blocks |
| `tests/test_prompt_boundaries_inv7.py` | `test_prompt_override_rejects_unwrapped_optional_data_value` | Optional data placeholders, when exposed, must also be untrusted-data blocks |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_prompt_boundaries_inv7.py -q` | INV-7 prompt boundary behavior remains correct |
| `python -m pytest tests/test_prompt_override_registry.py -q` | Registry governance remains correct |
| `make docs-check` | AGENTS sync and plan docs remain valid |
| `make check` | Full deterministic gate remains green |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] Required data-placeholder values must be strings containing untrusted-data
  block structure.
- [ ] Optional data-placeholder values, when provided to the renderer, must meet
  the same boundary check.
- [ ] Metadata placeholders are still allowed to be scalar values such as counts
  or names.
- [ ] Existing stage prompt override behavior remains compatible.
- [ ] Docs describe this as custom-prompt boundary hardening, not solved
  prompt-injection robustness.

Process criteria:

- [ ] Required focused tests pass.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Open Questions

- [ ] None.

---

## Notes

This guard checks renderer inputs, not model obedience. It narrows a future
integration hazard but remains structural prompt-boundary infrastructure only.

## Closeout Notes

Completed 2026-06-22.

Outcome: `render_prompt_override()` now validates values supplied for declared
required and optional data placeholders before rendering. Those values must be
string untrusted-data blocks with the expected boundary markers and `DATA>`
content; raw/unwrapped data values fail loudly before any LLM call. Metadata
placeholders remain scalar values.

Checkpoints:

- Plan checkpoint: `5ba9b0f`
- Implementation checkpoint: `5d3f547`

Verification:

- `python -m pytest tests/test_prompt_boundaries_inv7.py -q` (`22 passed`)
- `python -m pytest tests/test_prompt_override_registry.py -q` (`4 passed`)
- `make docs-check`
- `make check` (`1105 passed, 1 skipped, 8 deselected`)

Caveat: this is renderer-input hardening only. It does not prove model
obedience, prompt-injection robustness, or a committed live adversarial
benchmark result.
