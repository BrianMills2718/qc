# Plan #142: INV-7 Prompt Override Surface Registry

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** Prompt override rendering already requires explicit required data,
optional data, and metadata placeholder declarations at each call site. The
supported override surfaces are documented in prose, but the source has no
central registry or deterministic check that future `PipelineContext.prompt_overrides`
keys are declared before use.

**Target:** Supported prompt override surfaces are declared in one registry with
their protected data and metadata exposure policy. Current stage implementations
read that registry, and an agent-drivable lint command fails if source code uses
an override key missing from the registry or leaves a registered surface unused.

**Why:** INV-7 remains partial because future metadata-exposure surfaces can
miss the explicit declaration discipline. A registry plus source check converts
that governance rule from documentation into a deterministic gate without
claiming prompt-injection robustness or model obedience.

---

## References Reviewed

- `agent-memory recall 'qualitative_coding INV-7 prompt override custom prompt governance' --project qualitative_coding --limit 5` - 2 broad historical findings; no specific reusable decision for this slice.
- `CLAUDE.md:38` - INV-7 partial status and remaining custom-prompt governance gap.
- `CLAUDE.md:359` - current prompt override surfaces and declared placeholder roles.
- `docs/PROJECT_THEORY_AND_GOALS.md:451` - INV-7 remaining gaps and claim discipline.
- `docs/PROJECT_THEORY_AND_GOALS.md:560` - roadmap entry for broader custom-prompt threat-model tightening.
- `docs/EVALUATION_HARNESS.md:60` - live INV-7 canary/scorecard caveat.
- `qc_clean/core/prompting.py` - current `render_prompt_override` declaration enforcement.
- `qc_clean/core/pipeline/stages/thematic_coding.py` - current `thematic_coding` override call site.
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` - current `gt_constant_comparison` override call site.
- `tests/test_prompt_boundaries_inv7.py` - current prompt-boundary and override guard regressions.
- Coordination claims check: `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active claim files.

---

## Research Basis For This Slice

No additional research beyond repo-local references. This is deterministic
governance hardening of an already-designed INV-7 surface, not an
externally-informed algorithm or benchmark claim.

---

## Capabilities

This plan creates an internal validation script and Make target. It does not
create a cross-project callable capability or contract.

---

## Files Affected

- `qc_clean/core/prompt_override_registry.py` (create)
- `qc_clean/core/pipeline/stages/thematic_coding.py` (modify)
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` (modify)
- `scripts/check_prompt_override_registry.py` (create)
- `tests/test_prompt_override_registry.py` (create)
- `Makefile` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add a typed prompt override surface registry describing stage name, required
   protected data placeholders, optional protected data placeholders, and
   metadata placeholders.
2. Wire `thematic_coding` and `gt_constant_comparison` to call
   `render_prompt_override` from the registry rather than duplicating placeholder
   sets inline.
3. Add a source checker that scans Python source for `prompt_overrides["..."]`
   and compares observed keys to the registry.
4. Add `make lint-prompt-overrides` as the agent-drivable check.
5. Add tests covering the registry contents, source checker pass/fail behavior,
   and JSON CLI report.
6. Update docs and generated `AGENTS.md` without claiming INV-7 is solved.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_prompt_override_registry.py` | `test_registry_declares_current_prompt_override_surfaces` | Registry records the two supported surfaces and their placeholder roles. |
| `tests/test_prompt_override_registry.py` | `test_check_prompt_override_registry_passes_current_source` | Current source uses only registered prompt override keys and all registry entries are used. |
| `tests/test_prompt_override_registry.py` | `test_check_prompt_override_registry_fails_for_unregistered_surface` | A source fixture with an undeclared override key fails loudly. |
| `tests/test_prompt_override_registry.py` | `test_check_prompt_override_registry_cli_outputs_json` | The script emits a machine-readable pass/fail report and exit status. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_prompt_boundaries_inv7.py` | Existing INV-7 override and prompt-boundary behavior must remain unchanged. |
| `make lint-prompt-overrides` | New deterministic governance gate must pass. |
| `make docs-check` | Plan/docs/AGENTS sync must pass. |
| `make check` | Full deterministic gate must pass. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Current supported surfaces are centrally declared with required protected
      data, optional protected data, and metadata placeholders.
- [ ] Current override call sites consume the registry and preserve existing
      fail-loud placeholder enforcement.
- [ ] `make lint-prompt-overrides` exits non-zero and reports JSON when source
      uses a prompt override key absent from the registry.
- [ ] Docs state this is custom-prompt governance only, not proof of
      prompt-injection robustness or model obedience.

> Process criteria:
- [ ] Required new tests pass.
- [ ] `tests/test_prompt_boundaries_inv7.py` passes.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Plan is completed, committed, and pushed.

---

## Open Questions

None for this slice. Committed live adversarial INV-7 benchmarking remains a
separate higher-cost evidence lane because it requires an explicit model,
budget, frozen protocol, and scored result package.

---

## Notes

The registry does not and cannot prove that arbitrary operator-authored custom
instructions around protected data blocks are safe. It only makes the supported
override surfaces and exposed placeholders explicit and mechanically checkable.
