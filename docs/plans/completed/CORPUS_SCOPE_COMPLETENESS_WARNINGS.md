# Plan #77: Corpus Scope Completeness Warnings

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #16 corpus scope contract; Plan #72 corpus scope machine-readable warnings; Plan #76 corpus scope create surfaces
**Blocks:** broader scope-aware claim/report phrasing checks

---

## Gap

**Current:** Claim-bearing JSON/CSV/Markdown exports warn when
`ProjectState.corpus_scope` is missing. If a scope object exists but is empty, or
records a population without a sampling frame, JSON/CSV exports treat the scope
as sufficient and emit no machine-readable warning.

**Target:** Extend export warnings from "missing scope object" to "scope object
exists but is incomplete for the claim-boundary role." Warnings remain
non-blocking report discipline and must not claim sampling adequacy.

**Why:** Plan #76 made create-time scope easier, but it also makes it easier to
persist a partial scope. Claim-bearing exports should surface that partial
boundary explicitly rather than letting a blank or under-specified scope look
like a defensible population boundary.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - roadmap item #8 and claim-discipline
  caveats for corpus scope.
- `qc_clean/core/export/data_exporter.py` - JSON/CSV/Markdown export warning
  paths.
- `tests/test_claim_ledger_exports.py` - existing export warning coverage.
- Memory context: `agent-memory recall 'corpus scope completeness warnings' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No external research is needed. This is deterministic warning propagation for an
existing scope contract. It does not evaluate sample quality.

---

## Capabilities

This plan modifies repo-local export warning behavior only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/export/data_exporter.py` (modify)
- `tests/test_claim_ledger_exports.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CORPUS_SCOPE_COMPLETENESS_WARNINGS.md` (create, then move to completed)

---

## Plan

### Steps

1. Replace the single missing-scope warning helper with a list-producing export
   warning helper.
2. Preserve existing `missing_corpus_scope` behavior when claim-bearing exports
   have no `corpus_scope`.
3. Add `empty_corpus_scope` for claim-bearing exports whose scope object exists
   but has no phenomenon, population, sampling frame, inclusion/exclusion
   criteria, or notes.
4. Add `missing_sampling_frame` when a claim-bearing export records a population
   but no sampling frame.
5. Surface the same warnings in JSON `export_warnings`, CSV
   `export_warnings.csv`, and Markdown corpus-scope text.
6. Update docs to state incomplete scope warnings are report-boundary discipline,
   not sampling adequacy validation.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_claim_ledger_exports.py` | `test_json_export_warns_when_corpus_scope_is_empty` | JSON exports warn when scope exists but has no details. |
| `tests/test_claim_ledger_exports.py` | `test_csv_export_writes_all_scope_warnings` | CSV warnings can include multiple scope warning rows. |
| `tests/test_claim_ledger_exports.py` | `test_markdown_export_warns_when_population_has_no_sampling_frame` | Markdown warns when a population is stated without sampling frame. |
| `tests/test_claim_ledger_exports.py` | `test_json_export_omits_scope_warnings_when_scope_is_complete` | Complete scope does not produce scope warnings. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_claim_ledger_exports.py` | Existing missing-scope and scoped Markdown behavior remain compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Missing-scope warnings remain unchanged for claim-bearing exports with no
  `corpus_scope`.
- [x] Claim-bearing exports with an empty `CorpusScope()` emit
  `empty_corpus_scope` warnings in JSON/CSV/Markdown.
- [x] Claim-bearing exports with `population` but no `sampling_frame` emit
  `missing_sampling_frame` warnings in JSON/CSV/Markdown.
- [x] Complete scope records do not emit scope warnings.
- [x] Warning messages state the boundary limitation without claiming sample
  validity or invalidity.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status is reported
- [x] Docs updated

## Verification

- `python -m pytest tests/test_claim_ledger_exports.py -q` — 13 passed.
- `make check` — 791 passed, 1 skipped, 8 deselected; lint/docs passed; type check not yet configured.

## Outcome

Claim-bearing JSON, CSV, and Markdown exports now warn when a corpus scope
record exists but is empty, and when a population is recorded without a sampling
frame. The existing missing-scope warning remains unchanged. Complete scope
records do not emit scope warnings. These warnings are report-boundary metadata,
not sampling-adequacy validation.

---

## Open Questions

- [x] Should incomplete scope warnings block export? — Status: RESOLVED |
  Answer: No. Export warnings are report discipline; blocking would be a
  separate policy/strict-mode decision.

---

## Notes

Do not implement sampling-frame adequacy evaluation in this slice. This only
detects missing boundary metadata.
