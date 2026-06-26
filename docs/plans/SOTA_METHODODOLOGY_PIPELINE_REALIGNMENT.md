# Plan #241: SOTA Methodology And Pipeline Realignment

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** further default-path polish claims, sanitizer-first sequencing that ignores methodology alignment, major prompt/UX changes without a documented SOTA target

---

## Gap

**Current:** The repo has ambition, claim discipline, a stronger claim ledger,
and a more truthful graph than before, but it still lacks:

- a canonical document describing current state-of-the-art qualitative coding
  methodology and software;
- a clear account of how human labor bottlenecks distort qualitative rigor at
  scale;
- a canonical audit of prompt and dataflow surfaces;
- a sequenced program tying methodology documentation to prompt/code/UX
  improvements and fresh output critique.

**Target:** Establish a documented SOTA methodology frame, document labor
limitations and automation strategy, audit prompts/dataflow/docs/plans/code
against that frame, then implement the highest-value aligned changes and rerun
output critique.

**Why:** Without a shared methodology target and explicit audit trail, the repo
risks continuing to optimize strong local surfaces without converging on a
clearer answer to the harder product question: what would make this system
genuinely state-of-the-art rather than merely feature-rich?

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/METHODOLOGY.md`
- `docs/EVALUATION_HARNESS.md`
- `docs/LONG_TERM_EXECUTION_PLAN.md`
- `docs/plans/CLAIM_POSITION_METHODOLOGY_ALIGNMENT.md`
- `qc_clean/core/pipeline/pipeline_factory.py`
- `qc_clean/core/pipeline/pipeline_engine.py`
- `qc_clean/core/pipeline/stages/thematic_coding.py`
- `qc_clean/core/pipeline/stages/perspective.py`
- `qc_clean/core/pipeline/stages/cross_interview.py`
- `qc_clean/core/pipeline/stages/relationship.py`
- `qc_clean/core/pipeline/stages/negative_case.py`
- `qc_clean/core/claims.py`
- `qc_clean/core/prompt_override_registry.py`
- current local rerun4 packet and graph/review UX findings from 2026-06-25

---

## Research Basis For This Slice

This slice should use both:

- stable inherent qualitative-methodology knowledge for long-settled method
  distinctions;
- current primary sources for time-sensitive “state of the art” landscape
  claims.

The initial source set should include:

- current methodological references for thematic analysis and grounded theory;
- recent LLM/automation papers such as LLMCode and LOGOS;
- current CAQDAS product surfaces such as MAXQDA 26.2 segment-level AI coding.

---

## Operational Validation

**Classification:** default_path_visible_surface
**Surface IDs:** `review.claims_mode`, `graph.code_relationships_tab`, `export.markdown_report`
**Real-Run Requirement:** required

---

## Files Affected

- `docs/QUALITATIVE_CODING_SOTA_AND_AUTOMATION_STRATEGY.md` (create)
- `docs/PIPELINE_PROMPT_DATAFLOW_AUDIT.md` (create)
- `docs/METHODOLOGY.md` (modify if needed)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify if needed)
- `docs/LONG_TERM_EXECUTION_PLAN.md` (modify)
- `docs/plans/SOTA_METHODODOLOGY_PIPELINE_REALIGNMENT.md` (create)
- `docs/plans/CLAIM_POSITION_METHODOLOGY_ALIGNMENT.md` (complete/update)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- prompt/dataflow stage files under `qc_clean/core/pipeline/stages/` (follow-on)
- review/graph/export surfaces as justified by the audit (follow-on)
- tests and docs for any resulting implementation changes

---

## Plan

### Steps

1. Write canonical SOTA methodology documentation for qualitative coding,
   current software/research landscape, labor bottlenecks, and automation
   strategy.
2. Write a canonical prompt/dataflow audit with diagrams showing where codes,
   claims, relationships, and negative cases emerge.
3. Audit docs and plans for ambiguity, inconsistency, or sequencing mistakes
   against the new methodology frame.
4. Audit prompt surfaces and code paths against that frame; record concrete
   improvement opportunities.
5. Implement the highest-value aligned changes first, prioritizing default-path
   qualitative usefulness over surface expansion.
6. Rerun the affected workflow on the local seed, critique the resulting
   output, and record residual concerns plus advised next steps.

---

## Required Tests

### New Tests (TDD)

To be determined by the implementation sub-slice once concrete code changes are
selected.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `./.venv/bin/python scripts/sync_plan_status.py --check --validate-active` | Planning state must stay coherent. |
| `./.venv/bin/python scripts/check_surface_operational_readiness.py` | Active plan posture must remain valid. |
| `./.venv/bin/python scripts/check_markdown_links.py` | Canonical docs and plan references must remain intact. |
| `./.venv/bin/python -m ruff check .` | Lint gate for follow-on code changes. |
| relevant focused pytest targets | Follow-on code changes must add or update coverage. |
| `git diff --check` | Patch hygiene. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Canonical docs clearly describe SOTA qualitative coding methodology and
  the current software/research landscape.
- [ ] Canonical docs clearly describe how human labor bottlenecks hobble
  qualitative rigor and how automation can overcome those constraints.
- [ ] The repo has a prompt/dataflow audit with diagrams that map actual code
  paths to analytic objects.
- [ ] Docs and plans are aligned and unambiguous about the next implementation
  target.
- [ ] At least one high-value methodology-aligned implementation change is made
  and verified on a fresh local rerun.
- [ ] The resulting output is critiqued explicitly rather than merely generated.

> Process criteria:
- [ ] Findings are documented at each major step.
- [ ] Governance checks pass.
- [ ] The final worktree state is committed and pushed.

---

## Notes

This slice is intentionally broader than a prompt-only patch. It should not
skip from “we need SOTA” to ad hoc coding changes without first making the
target methodology, labor model, and dataflow weaknesses explicit.
