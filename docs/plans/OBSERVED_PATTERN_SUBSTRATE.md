# Plan #226: Observed Pattern Substrate

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Abductive synthesis stage, QC-to-workbench evidence/pattern bundle, causal hypothesis handoff to process tracing

---

## Gap

**Current:** The repo has several pattern-like outputs: synthesis
`cross_cutting_patterns`, cross-interview consensus/divergence/co-occurrence
dicts, code relationships, entity relationships, and memos. These are useful
but not represented as one first-class, typed, source-scope-aware descriptive
pattern layer. As a result, future abductive/causal theory-building would have
to scrape memos or stage-specific dicts.

**Target:** Add a first-class descriptive `ObservedPattern` domain object and
populate it from deterministic cross-interview analysis. Patterns must be
explicitly descriptive and must carry a causal interpretation status that
defaults to "descriptive_only". The first slice should not generate latent
constructs or causal hypotheses; it should create the substrate those later
stages consume.

**Why:** Abductive analysis needs observed patterns as input. Those patterns
must be typed, inspectable, source-linked where possible, and explicitly
non-causal until a later process tests or upgrades them.

---

## References Reviewed

- `qc_clean/schemas/domain.py` - current `ProjectState`, `CrossInterviewResult`, code/entity relationship, claim, and memo models.
- `qc_clean/core/pipeline/stages/cross_interview.py` - deterministic consensus/divergence/co-occurrence analysis.
- `qc_clean/core/pipeline/stages/relationship.py` - current relationship stage and memo behavior.
- `qc_clean/core/claims.py` - current cross-case/synthesis/relationship claim builders.
- `tests/test_cross_interview.py` - cross-interview expectations.
- `tests/test_claims.py` - cross-interview claim support expectations.
- `docs/PROJECT_THEORY_AND_GOALS.md` - denominator caveat for cross-interview counts.
- `CLAUDE.md` - product philosophy and future workbench alignment.
- Memory context: not needed; current repo docs/code are sufficient for this narrow slice.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This slice is
software substrate work: it makes existing descriptive pattern outputs typed and
agent-drivable without making new methodological claims.

---

## Capabilities

Skipped: this is an internal state/schema slice. A future QC-to-workbench export
capability will consume these patterns and should declare boundary contracts then.

---

## Files Affected

- `qc_clean/schemas/domain.py` (add `ObservedPattern` and related enums/fields)
- `qc_clean/core/pipeline/stages/cross_interview.py` (populate observed patterns)
- `tests/test_cross_interview.py` (focused tests)
- `tests/test_claims.py` or related claim tests if claim/pattern interactions change
- `docs/PROJECT_THEORY_AND_GOALS.md` (document pattern substrate)
- `CLAUDE.md` / `AGENTS.md` if operational guidance changes
- `docs/plans/ACTIVE_SPRINT.md` and `docs/plans/CLAUDE.md` (plan registration)

---

## Plan

### Steps

1. Add typed pattern enums/model:
   - `ObservedPatternKind`: `consensus_code`, `divergent_code`,
     `code_co_occurrence`.
   - `CausalInterpretationStatus`: `descriptive_only`,
     `candidate_explanation_generated`, `tested_by_process_tracing`,
     `eligible_for_cross_case_model`.
   - `ObservedPattern`: stable ID, source stage, pattern kind, summary,
     code IDs, doc IDs, application IDs, strength/count metadata, support
     anchors, interpretation status, provenance, creation time.
2. Add `observed_patterns: List[ObservedPattern]` to `ProjectState`.
3. Add a deterministic builder in `cross_interview.py` that converts
   `CrossInterviewResult` plus `ProjectState` into observed patterns.
4. Have `CrossInterviewStage.execute()` replace prior cross-interview patterns
   from that stage before adding the new set.
5. Preserve existing memos and claims behavior.
6. Add tests proving consensus, divergence, and co-occurrence patterns are
   created with descriptive-only causal status and source/code/doc references.
7. Update docs with the caveat that this is descriptive pattern accounting, not
   causal proof or abductive synthesis.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_cross_interview.py` | `test_stage_populates_observed_patterns` | Cross-interview execution writes first-class observed patterns. |
| `tests/test_cross_interview.py` | `test_observed_patterns_are_descriptive_only` | Pattern records default to non-causal `descriptive_only` status. |
| `tests/test_cross_interview.py` | `test_co_occurrence_pattern_records_code_and_doc_scope` | Co-occurrence pattern records involved codes and shared documents. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_cross_interview.py -q` | Core pattern extraction and memo behavior. |
| `python -m pytest tests/test_claims.py -q` | Claim builders still work with cross-interview outputs. |
| `python -m pytest tests/test_pipeline_stages.py -q` | Pipeline stages still compose with domain model changes. |
| `make docs-check` | Plan/docs/generated mirror checks. |
| `git diff --check` | Whitespace hygiene. |
| `make check` | Full deterministic suite and docs/lint gates before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `ProjectState` has a typed `observed_patterns` list.
- [ ] Cross-interview stage writes `ObservedPattern` records for consensus,
  divergence, and code co-occurrence where those outputs exist.
- [ ] Pattern records include enough scope to trace back to involved codes and
  documents; application IDs/support anchors are included where available.
- [ ] Pattern records default to `causal_interpretation_status="descriptive_only"`.
- [ ] Existing cross-interview memos and claim ledger behavior are preserved.
- [ ] Documentation states these are descriptive pattern records, not causal
  proof, abductive explanations, methodological-validity evidence, or SOTA.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should synthesis and relationship stages also write `ObservedPattern`
  records in this slice? Status: DEFERRED. Keep Slice 1 deterministic and
  cross-interview-only; extend after the model proves useful.
- [ ] Should patterns become claim-ledger entries? Status: DEFERRED. Existing
  cross-interview claims remain intact; pattern records are a substrate for
  future abductive synthesis, not a replacement for claims.
- [ ] Should observed patterns have a public CLI/API surface immediately?
  Status: DEFERRED. Add after the state model and extraction behavior are
  stable.

---

## Notes

This is the first abductive-substrate slice, not the abductive synthesis stage.
It deliberately stops at descriptive pattern records so later causal/abductive
work has a clean input without implying causal interpretation.

