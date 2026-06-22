# Plan #160: INV-9 Relationship Evidence Anchors

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** None

---

## Outcome

Relationship claims now resolve direct relationship evidence strings into exact
supporting anchors when the evidence uniquely grounds to the loaded corpus.
This covers `DomainEntityRelationship.supporting_evidence` and
`CodeRelationship.evidence`. Code relationship claims still prefer scoped
code-application anchors and skip duplicate evidence-only anchors for the same
source span. Ambiguous or unresolvable evidence is not guessed, so otherwise
unanchored relationship claims remain `needs_anchor`.

This is structural traceability only: the anchors identify source spans attached
to relationship evidence, not semantic proof or methodological validation of
the higher-order relationship claim.

Implementation commit: `7a5eb55`

## Verification

- TDD red: initial `python -m pytest tests/test_claims.py -q` failed on
  `test_relationship_evidence_strings_resolve_to_claim_anchors` because entity
  relationship evidence was not yet anchored.
- `python -m pytest tests/test_claims.py -q` -> 15 passed.
- `python -m pytest tests/test_claim_ledger_pipeline.py -q` -> 8 passed.
- `python -m pytest tests/test_bench_phase0.py -k claim_anchor_coverage -q` ->
  2 passed, 67 deselected.
- `make docs-check` passed.
- `git diff --check` passed.
- `make check` -> 1111 passed, 1 skipped, 8 deselected; Ruff and docs-check
  passed; type check remains not configured.
- Commit `7a5eb55` was pushed to `main`.

---

## Gap

**Current:** Relationship claims can inherit code-application anchors when their
code scope names anchored codes, but relationship objects also carry direct
evidence strings (`CodeRelationship.evidence` and
`DomainEntityRelationship.supporting_evidence`). Those evidence strings are not
resolved into claim anchors, so entity relationships and relationship-specific
quotes can remain visibly unanchored even when they quote the loaded corpus.

**Target:** Relationship claim builders resolve direct evidence strings to exact
source spans using the existing conservative grounding path. Unique resolved
evidence anchors become `supporting_anchors`; ambiguous or unresolvable evidence
does not get guessed and leaves the claim `needs_anchor` unless another scoped
anchor exists.

**Why:** This narrows INV-9's remaining higher-order anchoring gap with a
deterministic, auditable slice. Relationship claims should cite exact source
spans when the relationship object already contains quote-like evidence, without
claiming that the quote proves the full interpretation.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 item 4 - remaining INV-9 work:
  semantic/source anchoring for higher-order claims.
- `qc_clean/core/claims.py` - relationship claim builders, scoped anchor helper,
  and negative-case quote grounding helper.
- `qc_clean/schemas/domain.py` - `CodeRelationship.evidence` and
  `DomainEntityRelationship.supporting_evidence`.
- `qc_clean/schemas/adapters.py` - axial/entity relationship adapters preserve
  evidence strings into domain objects.
- `tests/test_claims.py` - current claim-builder expectations.
- Memory context:
  `agent-memory recall 'relationship evidence anchors claim ledger qualitative_coding exact quote anchoring' --project qualitative_coding`
  - 2 low-relevance historical findings, no active conflicting decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this modifies internal claim construction and does not create a new
cross-project capability.

---

## Files Affected

- `qc_clean/core/claims.py` - resolve direct relationship evidence strings into
  supporting claim anchors and de-duplicate with scoped code anchors.
- `tests/test_claims.py` - add regressions for entity and code relationship
  evidence anchors plus ambiguous/unresolvable evidence behavior.
- `CLAUDE.md` - update INV-9 current-state wording after implementation.
- `docs/PROJECT_THEORY_AND_GOALS.md` - update INV-9 roadmap/status wording.
- `AGENTS.md` - regenerated after `CLAUDE.md` changes.

---

## Plan

### Steps

1. Add tests proving entity relationship evidence resolves into supporting
   claim anchors when the quote uniquely matches the corpus.
2. Add tests proving code relationship direct evidence is de-duplicated with
   existing code-scope anchors when both point to the same application span.
3. Add tests proving ambiguous/unresolvable evidence is not guessed and does
   not mark an otherwise unanchored relationship as supported.
4. Implement a shared evidence-anchor helper using existing exact grounding.
5. Thread direct evidence anchors into relationship claim construction and keep
   scope-code anchor behavior intact.
6. Update status docs and run focused/full gates.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_claims.py` | `test_relationship_evidence_strings_resolve_to_claim_anchors` | Entity and code relationship evidence strings become exact supporting anchors |
| `tests/test_claims.py` | `test_relationship_evidence_anchors_are_not_guessed_when_ambiguous_or_missing` | Ambiguous/unresolvable relationship evidence remains unanchored |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_claims.py -q` | Claim-ledger construction remains correct |
| `python -m pytest tests/test_claim_ledger_pipeline.py -q` | Pipeline claim emission remains compatible |
| `python -m pytest tests/test_bench_phase0.py -k claim_anchor_coverage -q` | Anchor coverage accounting remains correct |
| `make docs-check` | AGENTS sync and plan docs remain valid |
| `make check` | Full deterministic gate remains green |

---

## Acceptance Criteria

Feature-level criteria:

- [x] Direct relationship evidence strings with one unique corpus match create
  supporting anchors.
- [x] Relationship evidence anchors are de-duplicated with scoped
  code-application anchors.
- [x] Ambiguous or unresolvable relationship evidence is not guessed.
- [x] Unsupported/no-anchor relationship claims remain `needs_anchor`.
- [x] Docs frame this as structural support/traceability, not claim truth or
  methodological validation.

Process criteria:

- [x] Required focused tests pass.
- [x] `make docs-check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Open Questions

- [ ] None.

---

## Notes

This is not semantic anchoring for arbitrary relationship prose. It only
resolves quote-like relationship evidence strings through the same conservative
exact grounding path already used for negative-case evidence.
