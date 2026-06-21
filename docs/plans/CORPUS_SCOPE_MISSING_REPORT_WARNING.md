# Plan #20: Missing Corpus Scope Report Warning

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #16 corpus scope contract; Plan #19 CLI/API scope surfaces
**Blocks:** broader scope-aware claim/report phrasing checks

---

## Gap

**Current:** Markdown export shows a `Corpus Scope` section when
`ProjectState.corpus_scope` is present. If a report contains claim-ledger rows
but no scope is recorded, the report proceeds directly to analytic content. A
reader can still overgeneralize corpus-level claims because the absence of a
scope boundary is silent.

**Target:** When Markdown export contains claims and `state.corpus_scope` is
missing, render a `## Corpus Scope` section before analytic claims that states
no scope is recorded and that claims must be read as bounded to the loaded
documents. Do not show this warning for empty/minimal reports with no claims.

**Why:** This is a small scope-aware report phrasing guard. It does not validate
the sampling frame; it prevents a silent missing-boundary report.

---

## References Reviewed

- `docs/plans/completed/CORPUS_SCOPE_CONTRACT.md` - initial state/export contract.
- `docs/plans/completed/CORPUS_SCOPE_CLI_API.md` - scope read/update surfaces.
- `qc_clean/core/export/data_exporter.py` - Markdown export surface.
- `tests/test_claim_ledger_exports.py` - claim-ledger and corpus-scope export tests.
- `docs/PROJECT_THEORY_AND_GOALS.md:331` - remaining scope-aware report phrasing checks.

---

## Research Basis For This Slice

No external research is needed. This is a deterministic report-safety guard for
an already-defined project invariant.

---

## Capabilities

This plan modifies a repo-local export surface only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/export/data_exporter.py` (modify)
- `tests/test_claim_ledger_exports.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/CORPUS_SCOPE_MISSING_REPORT_WARNING.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a Markdown export branch for `state.claims and not state.corpus_scope`.
2. Render the branch as `## Corpus Scope` before executive summary/claim ledger.
3. Keep existing populated-scope rendering unchanged.
4. Add tests for claims-without-scope warning and minimal no-claims no-scope omission.
5. Update docs conservatively.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_claim_ledger_exports.py` | `test_markdown_export_warns_when_claims_have_no_corpus_scope` | Claim-bearing Markdown reports surface a missing-scope warning. |
| `tests/test_claim_ledger_exports.py` | `test_markdown_export_omits_missing_scope_warning_without_claims` | Minimal reports without claims do not gain a noisy warning. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_claim_ledger_exports.py` | Protect claim ledger and populated scope rendering. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Markdown reports with claims and no `corpus_scope` include a `## Corpus Scope` warning.
- [ ] Populated `corpus_scope` rendering remains unchanged.
- [ ] Markdown reports without claims and without `corpus_scope` omit the warning.
- [ ] Docs state this is a report-safety warning only, not sampling-frame validation.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should JSON/CSV exports also surface missing scope warnings? — Status: DEFERRED | Why it matters: Markdown is the human report surface; machine-readable warning propagation can follow separately.

---

## Notes

This intentionally changes the earlier "omit when absent" behavior only for
reports that already contain analytic claims. Empty/minimal exports stay quiet.
