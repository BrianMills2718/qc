# Plan #9: INV-7 Derived-Output Prompt Boundaries

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-7 full prompt-injection hardening

---

## Gap

**Current:** Plan #6 wraps raw transcript/document/segment text as untrusted
`DATA>` prompt blocks, but downstream prompts still interpolate earlier LLM
outputs and evolving codebook context directly (`phase1_json`, `phase2_json`,
`phase3_json`, `gt_open_codes_text`, `gt_axial_text`, `gt_core_text`, and
codebook context strings). Those derived artifacts can echo transcript
instructions or contain malicious code descriptions/example quotes.

**Target:** Downstream prompts should wrap LLM-derived analysis artifacts and
codebook context in the same untrusted-data boundary used for raw corpus text.
The model may use these blocks as analytical source data, but must not follow
commands, role labels, or delimiters inside them as instructions.

**Why:** INV-7 is not satisfied if raw transcripts are isolated but transcript
instructions can be echoed into later phase JSON and regain instruction status
in downstream prompts.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:260` - INV-7 remains partial because downstream LLM-derived artifacts are not schema-aware isolated.
- `docs/plans/completed/INV7_INSTRUCTION_DATA_SEPARATION.md` - raw transcript/segment boundary first slice and explicit derived-output follow-up.
- `qc_clean/core/prompting.py` - existing `format_untrusted_data_block` helper.
- `qc_clean/core/pipeline/stages/perspective.py` - consumes `phase1_json`.
- `qc_clean/core/pipeline/stages/relationship.py` - consumes `phase1_json` and `phase2_json`.
- `qc_clean/core/pipeline/stages/synthesis.py` - consumes `phase1_json`, `phase2_json`, and `phase3_json`.
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` - consumes evolving codebook context in default and override prompts.
- `qc_clean/core/pipeline/stages/gt_axial_coding.py` - consumes `gt_open_codes_text`.
- `qc_clean/core/pipeline/stages/gt_selective_coding.py` - consumes `gt_open_codes_text` and `gt_axial_text`.
- `qc_clean/core/pipeline/stages/gt_theory_integration.py` - consumes `gt_open_codes_text`, `gt_axial_text`, and `gt_core_text`.
- `qc_clean/core/pipeline/stages/incremental_coding.py` - consumes existing codebook context containing descriptions/example quotes.
- Coordination context: `~/.claude/coordination/claims/` contained no active claims.
- Memory context: `agent-memory recall 'active decisions derived output prompt boundary phase json prompt injection qualitative_coding INV-7' --project qualitative_coding` — no active blocking decision surfaced; only historical completed outcomes were returned.

---

## Research Basis For This Slice

No additional external research is needed. This is a direct follow-up to the
repo-local INV-7 raw-data boundary mechanism.

---

## Capabilities

Skipped. This modifies internal prompt construction only.

---

## Files Affected

- `qc_clean/core/pipeline/stages/perspective.py` (modify)
- `qc_clean/core/pipeline/stages/relationship.py` (modify)
- `qc_clean/core/pipeline/stages/synthesis.py` (modify)
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` (modify)
- `qc_clean/core/pipeline/stages/gt_axial_coding.py` (modify)
- `qc_clean/core/pipeline/stages/gt_selective_coding.py` (modify)
- `qc_clean/core/pipeline/stages/gt_theory_integration.py` (modify)
- `qc_clean/core/pipeline/stages/incremental_coding.py` (modify)
- `tests/test_prompt_boundaries_inv7.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify at completion)
- `CLAUDE.md` (modify at completion)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV7_DERIVED_OUTPUT_PROMPT_BOUNDARIES.md` (move to completed at finish)

---

## Plan

### Steps

1. Add a tiny local helper pattern in each affected stage using
   `format_untrusted_data_block(label, value)` for upstream LLM/codebook text.
2. Wrap default/thematic derived artifacts in perspective, relationship, and
   synthesis prompts.
3. Wrap GT derived artifacts in constant-comparison codebook context, axial,
   selective, and theory-integration prompts.
4. Wrap incremental recoding's existing-codebook context.
5. Add prompt-capture tests with malicious upstream analysis/codebook text and
   no live LLM calls.
6. Update docs conservatively: INV-7 remains PARTIAL unless live adversarial
   injection evaluation and broader custom-prompt hardening land.
7. Run targeted tests, `make docs-check`, and `make check`; commit and push.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_prompt_boundaries_inv7.py` | `test_perspective_prompt_wraps_malicious_phase1_json_as_untrusted_data` | `phase1_json` appears only as prefixed data lines. |
| `tests/test_prompt_boundaries_inv7.py` | `test_synthesis_prompt_wraps_all_prior_phase_outputs_as_untrusted_data` | Phase 1/2/3 derived outputs are boundary-wrapped. |
| `tests/test_prompt_boundaries_inv7.py` | `test_gt_selective_prompt_wraps_open_and_axial_outputs_as_untrusted_data` | GT open/axial derived outputs are boundary-wrapped. |
| `tests/test_prompt_boundaries_inv7.py` | `test_incremental_prompt_wraps_existing_codebook_context_as_untrusted_data` | Existing codebook context cannot inject instructions. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_prompt_boundaries_inv7.py` | New and existing INV-7 contracts. |
| `python -m pytest tests/test_pipeline_stages.py tests/test_constant_comparison.py tests/test_incremental.py tests/test_memos.py` | Affected prompt-building/stage paths. |
| `make docs-check` | Plan/governance consistency and generated docs sync. |
| `make check` | Full deterministic test, lint, and docs gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Downstream prompts wrap upstream phase JSON/text as untrusted data.
- [ ] GT prompts wrap open/axial/core derived outputs and evolving codebook context as untrusted data.
- [ ] Incremental recoding wraps existing codebook context as untrusted data.
- [ ] Prompt-capture tests prove malicious derived instructions stay prefixed.
- [ ] Docs keep INV-7 conservative and do not claim prompt injection is solved.

> Process criteria:
- [ ] Required targeted tests pass.
- [ ] Full deterministic suite passes through `make check`.
- [ ] Lint passes through `make check`.
- [ ] Docs checks pass.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should prompt overrides that directly reference other metadata fields be
  governed by a stricter template API? — Status: DEFERRED | Why it matters:
  full custom-prompt safety needs an explicit threat model and may require
  rejecting unsafe templates rather than just wrapping default placeholders.

---

## Notes

This extends structural prompt hygiene. It does not replace live prompt-injection
evaluation and does not prove model obedience to the boundary.
