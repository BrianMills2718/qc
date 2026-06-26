# Plan #240: Claim/Position Methodology Alignment

**Status:** Planned
**Type:** design
**Priority:** High
**Blocked By:** None
**Blocks:** further default-path qualitative-polish claims, claim/graph UX hardening that treats theme structure as sufficient

---

## Gap

**Current:** The repo now has a more truthful default-path graph and a
first-class claim ledger, but the default analytic UX and extraction logic
still center themes/codes more strongly than claims, positions, framings,
contestation, attribution, and evaluation. Broad nodes such as
`NATURE_OF_INFORMATION_THREATS` can organize subject matter while still hiding
the more methodologically important question of what participants are asserting
about that subject matter.

**Target:** Document the methodology gap explicitly, define the repo's intended
analytic ontology for codes versus claims/positions, and specify the next
implementation/evaluation boundary for claim/position-aware analysis on the
default path.

**Why:** Without this alignment slice, the repo risks continuing to optimize
theme extraction, graph density, and review/export polish while under-serving a
core qualitative need: surfacing bounded interpretive positions rather than
only topical categories.

---

## References Reviewed

- `docs/METHODOLOGY.md` - current methodology framing and failure modes.
- `docs/PROJECT_THEORY_AND_GOALS.md` - canonical theory, honest-state ledger,
  and claim-discipline framing.
- `docs/plans/SANITIZED_CORPUS_ADJUDICATION_SEED.md` - fresh local seed packet
  that exposed the concern during user review.
- `docs/plans/THEMATIC_GRAPH_RELATIONSHIP_HARDENING.md` - recent graph
  remediation and its limits.
- `qc_clean/schemas/domain.py` - current first-class claim and relationship
  contracts.
- `qc_clean/core/pipeline/stages/thematic_coding.py` - default code/theme
  producer.
- `qc_clean/core/pipeline/stages/cross_interview.py` - higher-order observed
  pattern / claim producer.
- `qc_clean/plugins/api/api_server.py` and `qc_clean/plugins/api/review_ui.py`
  - current claim review surfaces versus graph surfaces.
- User review on 2026-06-25 - explicit critique that broad themes like
  `Nature of Information Threats` are less useful than position-bearing claims
  such as whether threats are real, exaggerated, externally driven, or locally
  contested.

---

## Research Basis For This Slice

No external literature review is required to establish the existence of this
gap. The distinction between topical themes and bounded claims/positions is
stable qualitative-methodology knowledge and is already compatible with the
repo's claim-ledger architecture.

A later follow-on may still review specific literature or benchmark systems for
implementation choices, but this slice should not delay basic documentation and
problem framing behind unnecessary “research later” ambiguity.

---

## Operational Validation

**Classification:** default_path_visible_surface
**Surface IDs:** `review.claims_mode`, `graph.code_relationships_tab`, `export.markdown_report`
**Real-Run Requirement:** deferred
**Deferred Reason:** This slice is design/governance first. Real-run validation
belongs to the implementation slice that changes default-path extraction,
review, or visualization behavior.

---

## Files Affected

- `docs/plans/CLAIM_POSITION_METHODOLOGY_ALIGNMENT.md` (create)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/LONG_TERM_EXECUTION_PLAN.md` (modify)
- `docs/METHODOLOGY.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)

---

## Plan

### Steps

1. Document the current methodology gap precisely: theme/topic extraction is
   stronger than stance/claim extraction on the default path.
2. Define the intended analytic ontology for:
   - codes/themes
   - claims/positions
   - relationships among codes
   - relationships among claims and between claims and speakers/groups/docs
3. Specify what should remain descriptive versus what should become first-class
   interpretive structure in the default path.
4. Write acceptance criteria for the next implementation slice so it is judged
   by methodological usefulness, not only graph density or schema completion.
5. Queue the follow-on implementation slice only after the ontology and
   evaluation boundary are concrete enough to avoid another “looks complete,
   not methodologically credible” loop.

---

## Required Tests

### New Tests (TDD)

No code tests in this design slice.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `./.venv/bin/python scripts/sync_plan_status.py --check --validate-active` | Planning state must stay coherent. |
| `./.venv/bin/python scripts/check_surface_operational_readiness.py` | New active plan must declare operational-validation posture correctly. |
| `./.venv/bin/python scripts/check_markdown_links.py` | New doc references must remain valid. |
| `git diff --check` | Patch hygiene. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Canonical docs explicitly state that broad themes are not sufficient
  substitutes for claim/position structure.
- [ ] The repo's intended ontology for codes versus claims/positions is written
  clearly enough to guide follow-on implementation.
- [ ] The next implementation slice is framed as a methodology-alignment task,
  not just a graph/prompt polish task.

> Process criteria:
- [ ] Active-plan docs are updated coherently.
- [ ] Governance checks pass.

---

## Notes

This slice should stay disciplined. The purpose is to align methodology,
ontology, and roadmap priorities before more implementation proceeds. It should
not drift into half-implemented claim-graph features or ad hoc prompt edits.
