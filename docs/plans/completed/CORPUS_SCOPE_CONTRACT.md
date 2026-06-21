# Plan #16: Corpus Scope Contract

**Outcome:** Complete. Added optional `ProjectState.corpus_scope` with typed
`CorpusScope` fields for phenomenon, population, sampling frame,
inclusion/exclusion criteria, and notes. Markdown export now renders a `Corpus
Scope` section before analytic claims when the field is present. Documentation
now describes this as report-boundary context, not sampling-frame validation.

**Verification:** `python -m pytest
tests/test_domain_model.py::TestCorpusScope::test_project_state_corpus_scope_round_trips
tests/test_claim_ledger_exports.py::test_markdown_export_includes_corpus_scope
tests/test_claim_ledger_exports.py::test_markdown_export_includes_claim_ledger_summary`
and `python -m ruff check qc_clean/schemas/domain.py
qc_clean/core/export/data_exporter.py tests/test_domain_model.py
tests/test_claim_ledger_exports.py` passed. Final full gate: `make check`
passed with 650 tests passed, 1 skipped, 8 deselected; Ruff and docs gates
passed; type check is not yet configured.

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** claim discipline; public report safety; future sampling-frame evaluation

---

## Gap

**Current:** `AnalyticClaim.scope` can mark claims as corpus-level, document-level,
or code-level, but `ProjectState` has no project-level corpus boundary object
describing the phenomenon, population/sampling frame, inclusion/exclusion
criteria, or scope notes. The theory doc warns not to generalize beyond the
corpus, but exports cannot show the intended boundary.

**Target:** Add a typed `CorpusScope` model to `ProjectState` and surface it in
Markdown export. Preserve backwards compatibility by making it optional. This
is a report-safety and claim-discipline contract, not a validity proof.

**Why:** A claim ledger can still overgeneralize if the project lacks an explicit
scope boundary. Public-facing reports need a visible place to say what the
claims are and are not about.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:284` - claim discipline forbids generalizing to a population without a sampling frame.
- `docs/PROJECT_THEORY_AND_GOALS.md:300` - corpus boundary is currently unstated.
- `docs/PROJECT_THEORY_AND_GOALS.md:330` - roadmap item: corpus-boundary / scope-condition contract.
- `qc_clean/schemas/domain.py` - `ProjectState`, `ProjectConfig`, and `AnalyticClaim.scope`.
- `qc_clean/core/export/data_exporter.py` - Markdown export surface.
- `tests/test_claim_ledger_exports.py` - current claim ledger export tests.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
schema/export contract for an already-documented claim-discipline gap.

---

## Capabilities

This plan modifies the repo-local state schema and export surface only; it does
not create a cross-project callable capability.

---

## Files Affected

- `qc_clean/schemas/domain.py` (modify)
- `qc_clean/core/export/data_exporter.py` (modify)
- `tests/test_domain_model.py` (modify)
- `tests/test_claim_ledger_exports.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/CORPUS_SCOPE_CONTRACT.md` (create, then move to completed)

---

## Plan

### Steps

1. Add optional `CorpusScope` to `ProjectState`.
2. Include fields for phenomenon, population, sampling frame, inclusion criteria,
   exclusion criteria, and notes.
3. Add persistence/model tests proving the field round-trips and remains
   optional for old states.
4. Add a Markdown export section when `state.corpus_scope` is present.
5. Update docs conservatively: scope can now be recorded/exported; it still does
   not validate sampling, population generalization, or claim correctness.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_domain_model.py` | `test_project_state_corpus_scope_round_trips` | `CorpusScope` persists through JSON state. |
| `tests/test_claim_ledger_exports.py` | `test_markdown_export_includes_corpus_scope` | Reports include the explicit corpus boundary when present. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_domain_model.py` | Schema backwards compatibility. |
| `tests/test_claim_ledger_exports.py` | Claim export surface unchanged except new optional section. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [x] `ProjectState.corpus_scope` is optional and typed.
- [x] Corpus scope round-trips through `ProjectState.model_dump_json()` / validation.
- [x] Markdown export includes corpus scope when present and omits it when absent.
- [x] Docs state this binds report claims to a scope boundary but does not validate the sampling frame.

> Process criteria (quality gates):
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status is reported
- [x] Docs updated

---

## Open Questions

- [ ] Should CLI/API project creation collect scope fields? — Status: DEFERRED | Why it matters: useful, but this slice only adds the state/export contract.
- [ ] Should claim builders copy corpus scope into each corpus-level claim? — Status: DEFERRED | Why it matters: likely future work; duplicating scope into every claim may create staleness if the project scope changes.

---

## Notes

This is not sampling-frame validation. It creates a durable place to record the
scope so agents and reports have less excuse to overgeneralize.
