# Plan #159: INV-9 Code-Scoped Higher-Order Claim Anchors

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** None

---

## Outcome

Code-scoped higher-order claims now inherit exact existing `CodeApplication`
anchors when their `ClaimScope` names matching code IDs or application IDs.
This covers participant perspectives, code relationships, synthesis
recommendations, and GT categories. Duplicate anchors are removed, and
corpus-level/no-code-scope claims remain visibly `needs_anchor`.

This is structural traceability only: anchors show the source spans backing the
referenced code scope, not semantic proof or methodological validation of the
higher-order prose.

Implementation commit: `8dd2aae`

## Verification

- `python -m pytest tests/test_claims.py -q` -> 13 passed.
- `python -m pytest tests/test_bench_phase0.py -k claim_anchor_coverage -q` ->
  2 passed, 67 deselected.
- `make docs-check` passed.
- `make check` -> 1109 passed, 1 skipped, 8 deselected; Ruff and docs-check
  passed; type check remains not configured.
- Commit `8dd2aae` was pushed to `main`.

---

## Gap

**Current:** Code and code-application claims carry supporting source anchors,
and cross-case code-presence claims inherit code-application anchors. Several
higher-order claims that explicitly scope themselves to code IDs still emit as
`needs_anchor` even when those code IDs have anchored applications.

**Target:** Higher-order claims with explicit `scope.code_ids` inherit existing
code-application anchors for those codes. Corpus-level claims with no scoped
code evidence remain visibly unanchored.

**Why:** This narrows INV-9's "stronger source anchoring for higher-order
claims" gap without pretending that an anchor proves the full interpretation.
It makes report/evaluation surfaces more honest: code-scoped synthesis,
perspective, relationship, and GT-category claims can cite the underlying
anchored evidence they depend on.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 item 4 - remaining INV-9 work:
  stronger source anchoring for higher-order claims.
- `qc_clean/core/claims.py` - claim builders and anchor helpers.
- `tests/test_claims.py` - current claim-builder expectations.
- `docs/PROJECT_THEORY_AND_GOALS.md` §14 - claim discipline; anchors are
  structural support, not claim truth.
- Memory context:
  `agent-memory recall 'higher order claim anchors code scoped claims qualitative_coding' --project qualitative_coding`
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

- `qc_clean/core/claims.py` - propagate anchors from scoped code IDs.
- `tests/test_claims.py` - add regressions for code-scoped higher-order claim
  anchors and preserve unanchored corpus-level behavior.
- `CLAUDE.md` - update INV-9 current-state wording after implementation.
- `docs/PROJECT_THEORY_AND_GOALS.md` - update INV-9 roadmap/status wording.
- `AGENTS.md` - regenerated after `CLAUDE.md` changes.

---

## Plan

### Steps

1. Add tests proving code-scoped perspective/synthesis/relationship/GT-category
   claims inherit anchors from code applications.
2. Add or preserve tests proving corpus-level higher-order claims without code
   scope remain `needs_anchor`.
3. Implement a shared scope-anchor helper with de-duplication.
4. Thread those anchors into higher-order claim builders that already declare
   `scope.code_ids`.
5. Update docs and run focused/full gates.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_claims.py` | `test_code_scoped_higher_order_claims_inherit_code_application_anchors` | Perspective, code-relationship, synthesis recommendation, and GT-category code-scoped claims inherit anchors |
| `tests/test_claims.py` | existing unanchored higher-order test | Corpus-level/no-code-scope claims remain `needs_anchor` |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_claims.py -q` | Claim-ledger construction remains correct |
| `python -m pytest tests/test_bench_phase0.py -k claim_anchor_coverage -q` | Anchor coverage accounting remains correct |
| `make docs-check` | AGENTS sync and plan docs remain valid |
| `make check` | Full deterministic gate remains green |

---

## Acceptance Criteria

Feature-level criteria:

- [x] Code-scoped higher-order claims inherit unique supporting anchors from
  matching code applications.
- [x] Corpus-level higher-order claims with no code scope remain unanchored and
  `needs_anchor`.
- [x] Claim anchor propagation does not mark unsupported/no-anchor code scopes
  as supported.
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

This is not semantic source matching for arbitrary prose. It only reuses exact
anchors already attached to code applications referenced by claim scope.
