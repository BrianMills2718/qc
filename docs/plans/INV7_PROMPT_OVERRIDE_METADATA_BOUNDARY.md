# Plan #158: INV-7 Prompt Override Metadata Boundary

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** Prompt override surfaces distinguish protected data placeholders
from metadata placeholders. Data placeholders are now checked for untrusted-data
block structure, but metadata placeholder values are not checked for prompt-line
injection risk or scalar shape. A user-controlled document name exposed as
metadata could contain a newline and become an unprefixed prompt line if a
custom template renders it.

**Target:** Declared metadata placeholder values must be scalar, and string
metadata must be single-line (no CR/LF). Invalid metadata fails before
rendering.

**Why:** This continues INV-7 custom-prompt hardening while preserving the
data/metadata distinction. Metadata can be unwrapped, so it must not carry
multi-line prompt content or structured untrusted payloads.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 item 6 - INV-7 remaining custom-prompt
  threat-model tightening.
- `qc_clean/core/prompting.py` - prompt override renderer and data-placeholder
  validation.
- `qc_clean/core/prompt_override_registry.py` - metadata-placeholder
  declarations (`num_interviews`, `doc_name`, `seg_idx`, `total_segments`).
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` - exposes
  `doc_name` metadata from source documents to GT custom prompts.
- `tests/test_prompt_boundaries_inv7.py` - prompt override boundary tests.
- Memory context:
  `agent-memory recall 'INV-7 prompt override metadata placeholder newline validation qualitative_coding' --project qualitative_coding`
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

- `qc_clean/core/prompting.py` - validate metadata-placeholder values before
  rendering prompt overrides.
- `tests/test_prompt_boundaries_inv7.py` - add regression tests for multi-line
  and structured metadata values.
- `CLAUDE.md` - update INV-7 current-state wording after implementation.
- `docs/PROJECT_THEORY_AND_GOALS.md` - update INV-7 roadmap/status wording.
- `AGENTS.md` - regenerated after `CLAUDE.md` changes.

---

## Plan

### Steps

1. Add failing tests for multi-line string metadata and structured metadata
   values supplied to `render_prompt_override()`.
2. Add a stage-level regression for a custom GT prompt with a malicious document
   name exposed as `doc_name` metadata.
3. Implement metadata validation in `render_prompt_override()`.
4. Update docs without claiming prompt-injection robustness.
5. Run focused tests, docs checks, and `make check`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_prompt_boundaries_inv7.py` | `test_prompt_override_rejects_multiline_metadata_value` | Metadata strings cannot add prompt lines |
| `tests/test_prompt_boundaries_inv7.py` | `test_prompt_override_rejects_structured_metadata_value` | Metadata placeholders cannot carry structured payloads |
| `tests/test_prompt_boundaries_inv7.py` | `test_gt_prompt_override_rejects_multiline_doc_name_metadata` | Stage wiring fails before LLM call when source doc name metadata is unsafe |

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

- [ ] Metadata placeholder values must be scalar (`str`, `int`, `float`, `bool`,
  or `None`).
- [ ] String metadata values with CR/LF are rejected before rendering.
- [ ] Current valid metadata placeholders still render.
- [ ] Unsafe GT `doc_name` metadata fails before an LLM call under prompt
  override mode.
- [ ] Docs describe this as structural boundary hardening, not solved
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

This guards custom prompt renderer metadata, not default prompt behavior or
model obedience.
