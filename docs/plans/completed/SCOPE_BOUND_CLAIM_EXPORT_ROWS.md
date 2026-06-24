# Plan #86: Scope-Bound Claim Export Rows

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Corpus scope completeness warnings
**Blocks:** broader scope-aware claim/report phrasing checks

---

## Outcome

Completed 2026-06-21. CSV `claims.csv` rows now include `claim_scope` and
`corpus_scope_boundary` columns. Markdown claim ledger tables now include
`Scope` and `Corpus boundary` columns. Missing or empty corpus scope is phrased
as loaded-document-corpus-only context, and population-without-sampling-frame
rows are explicitly marked as unvalidated population boundaries. The underlying
`AnalyticClaim.claim_text` is not rewritten.

This narrows the scope-aware export-phrasing gap. It does not validate sampling
adequacy, source support, disconfirmation survival, or human/expert
adjudication.

Verification: initial TDD run failed on the expected missing columns/Markdown
header (`4 failed, 14 passed`). After implementation, focused export tests
passed (`18 passed`), Ruff passed on touched code/tests, docs/plan/AGENTS checks
passed, and final `make check` passed (`818 passed, 1 skipped, 8 deselected`;
type check not yet configured).

---

## Gap

**Current:** Claim-bearing exports show a report-level `Corpus Scope` section or
warning, and JSON/CSV emit warning metadata when scope is absent or incomplete.
Individual claim rows still omit a compact claim-scope summary and corpus-boundary
phrase. A copied Markdown claim table row or `claims.csv` row can therefore lose
the "loaded documents only" / sampling-frame caveat that makes the claim safe to
read.

**Target:** Add deterministic per-claim export context without changing the
underlying `AnalyticClaim.claim_text`: CSV `claims.csv` rows should include
`claim_scope` and `corpus_scope_boundary` columns, and Markdown claim tables
should include compact `Scope` and `Corpus boundary` columns. Missing or
under-specified corpus scope must phrase the boundary as loaded-document-corpus
only and must not imply population validity.

**Why:** This closes a concrete scope-aware phrasing gap while preserving the
existing claim ledger as the source of truth. It improves report discipline but
does not validate sampling-frame adequacy.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:94` - `corpus_scope` is a report boundary,
  not sampling-frame validation.
- `docs/PROJECT_THEORY_AND_GOALS.md:384` - claim discipline allows binding
  claims to `CorpusScope` or to loaded transcripts only, not unsupported
  population generalization.
- `docs/PROJECT_THEORY_AND_GOALS.md:455` - roadmap leaves broader scope-aware
  claim/report phrasing checks as remaining work.
- `qc_clean/core/export/data_exporter.py` - current JSON/CSV/Markdown export and
  scope warning behavior.
- `qc_clean/core/claims.py` - existing private claim-scope formatter used for
  disconfirmation prompts.
- `qc_clean/schemas/domain.py` - `CorpusScope`, `ClaimScope`, `AnalyticClaim`,
  and `ProjectState` schemas.
- `tests/test_claim_ledger_exports.py` - current claim ledger export and corpus
  scope warning coverage.
- `docs/plans/completed/CORPUS_SCOPE_CONTRACT.md` - initial scope state/export
  contract.
- `docs/plans/completed/CORPUS_SCOPE_COMPLETENESS_WARNINGS.md` - current
  completeness-warning behavior this plan must preserve.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic export/wording guard for an already-documented claim-discipline
gap.

---

## Capabilities

This plan modifies internal export formatting only. It does not create a
cross-project callable capability or boundary.

---

## Files Affected

- `qc_clean/core/claims.py` (modify)
- `qc_clean/core/export/data_exporter.py` (modify)
- `tests/test_claim_ledger_exports.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/SCOPE_BOUND_CLAIM_EXPORT_ROWS.md` (create, then move to completed)

---

## Plan

### Steps

1. Promote the existing compact claim-scope formatter in `qc_clean/core/claims.py`
   to a public helper while keeping existing disconfirmation prompt behavior.
2. Add exporter helpers for:
   - compact claim scope from `AnalyticClaim.scope`;
   - compact corpus-boundary phrase from `ProjectState.corpus_scope`;
   - Markdown table-cell escaping.
3. Add `claim_scope` and `corpus_scope_boundary` columns to `claims.csv`.
4. Add `Scope` and `Corpus boundary` columns to the Markdown claim ledger table.
5. Preserve existing report-level warnings and warning metadata unchanged.
6. Update docs conservatively: per-row export context narrows scope-aware report
   phrasing, but it is still not sampling adequacy evidence.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_claim_ledger_exports.py` | `test_csv_claim_rows_include_scope_and_loaded_document_boundary` | `claims.csv` has `claim_scope` and `corpus_scope_boundary` columns, and missing corpus scope is phrased as loaded-document-only. |
| `tests/test_claim_ledger_exports.py` | `test_csv_claim_rows_include_recorded_scope_boundary` | Complete `CorpusScope` is summarized in per-claim CSV context without removing warning behavior for other cases. |
| `tests/test_claim_ledger_exports.py` | `test_markdown_claim_rows_include_scope_and_boundary_columns` | Markdown claim table rows include compact claim scope and corpus-boundary columns. |
| `tests/test_claim_ledger_exports.py` | `test_markdown_claim_rows_do_not_rewrite_claim_text` | Export context is additional metadata; the original claim text remains unchanged. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_claim_ledger_exports.py -q` | Claim export and warning behavior remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] CSV claim rows include deterministic `claim_scope` and
  `corpus_scope_boundary` columns.
- [x] Markdown claim rows include deterministic `Scope` and `Corpus boundary`
  columns.
- [x] Missing/empty corpus scope row context binds claims to loaded documents
  only.
- [x] Population without sampling frame remains explicitly unvalidated in row
  context.
- [x] Original `claim_text` values are not rewritten or decorated.
- [x] Existing `export_warnings` behavior is preserved.
- [x] Docs state this is scope-aware export context, not sampling-frame
  validation.

> Process criteria:
- [x] Required focused tests pass.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Verification

- Initial TDD run: `python -m pytest tests/test_claim_ledger_exports.py -q` -
  failed as expected with missing `claim_scope` / `corpus_scope_boundary` CSV
  fields and missing Markdown table columns (`4 failed, 14 passed`).
- `python -m pytest tests/test_claim_ledger_exports.py -q` - passed
  (`18 passed`).
- `python -m ruff check qc_clean/core/claims.py qc_clean/core/export/data_exporter.py tests/test_claim_ledger_exports.py`
  - passed.
- `python scripts/check_markdown_links.py && python scripts/sync_plan_status.py --check && python scripts/meta/check_agents_sync.py --check`
  - passed.
- `make check` - passed (`818 passed, 1 skipped, 8 deselected`); Ruff and docs
  gates passed; type check is not yet configured.

---

## Open Questions

- [ ] Should JSON exports duplicate a computed `corpus_scope_boundary` on every
  claim object? - Status: DEFERRED | Why it matters: JSON already includes
  structured `claims[*].scope`, project-level `corpus_scope`, and
  `export_warnings`; duplicating derived row context could introduce staleness.
- [ ] Should future LLM claim builders include `CorpusScope` in claim generation
  prompts? - Status: DEFERRED | Why it matters: potentially useful, but this
  slice only hardens deterministic exports and avoids prompt-surface expansion.

---

## Notes

This plan deliberately keeps `AnalyticClaim.claim_text` untouched. The scope
phrasing belongs in export metadata so review, disconfirmation, and adjudication
continue to operate over the original claim object.
