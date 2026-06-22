# Plan #72: Corpus Scope Machine-Readable Warnings

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #16 corpus scope contract; Plan #19 CLI/API scope surfaces; Plan #20 missing corpus scope report warning
**Blocks:** broader scope-aware claim/report phrasing checks

---

## Gap

**Current:** Markdown export warns when a claim-bearing report has no recorded
`ProjectState.corpus_scope`, but JSON export still writes only the raw project
state and CSV export writes no warning artifact. Machine consumers can therefore
miss the same missing-boundary condition that human report readers now see.

**Target:** When exports contain claim-ledger rows and `state.corpus_scope` is
missing, JSON export includes structured `export_warnings` metadata and CSV
export writes `export_warnings.csv`. Minimal exports without claims remain quiet,
and populated `corpus_scope` exports keep their current behavior.

**Why:** This closes the deferred machine-readable warning propagation question
from Plan #20. It is a report-boundary guard only; it does not validate sampling
adequacy or license population generalization.

---

## References Reviewed

- `docs/plans/completed/CORPUS_SCOPE_MISSING_REPORT_WARNING.md` - prior Markdown
  warning slice and deferred JSON/CSV warning question.
- `qc_clean/core/export/data_exporter.py` - JSON, CSV, and Markdown export
  implementation.
- `tests/test_claim_ledger_exports.py` - existing claim-ledger and corpus-scope
  export coverage.
- `tests/test_project_commands.py` - existing exporter contract tests expecting
  minimal CSV exports to write two files.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim-discipline and corpus-boundary
  language.
- Memory context: `agent-memory recall 'corpus scope export warnings' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic export-contract follow-up to an already-defined project invariant.

---

## Capabilities

This plan modifies repo-local export surfaces only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/export/data_exporter.py` (modify)
- `tests/test_claim_ledger_exports.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CORPUS_SCOPE_MACHINE_READABLE_WARNINGS.md` (create, then move to completed)

---

## Plan

### Steps

1. Add one shared helper for the missing corpus-scope export warning so
   Markdown, JSON, and CSV use the same message.
2. Keep raw `ProjectState` JSON unchanged when there is no warning; when a
   warning applies, write the normal project-state payload plus
   `export_warnings`.
3. Keep base CSV exports unchanged when there is no warning; when a warning
   applies, add `export_warnings.csv` to the returned path list.
4. Add tests for JSON warning presence/absence and CSV warning file
   presence/absence.
5. Update theory/roadmap language to say machine-readable exports now carry the
   warning while preserving the caveat that corpus scope is not validity
   evidence.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_claim_ledger_exports.py` | `test_json_export_warns_when_claims_have_no_corpus_scope` | Claim-bearing JSON exports include structured missing-scope warning metadata. |
| `tests/test_claim_ledger_exports.py` | `test_json_export_omits_missing_scope_warning_without_claims` | Minimal JSON exports remain free of noisy warning metadata. |
| `tests/test_claim_ledger_exports.py` | `test_csv_export_writes_scope_warning_file_when_claims_have_no_scope` | Claim-bearing CSV exports include `export_warnings.csv`. |
| `tests/test_claim_ledger_exports.py` | `test_csv_export_omits_scope_warning_file_without_claims` | Minimal CSV exports keep the existing two-file contract. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_claim_ledger_exports.py` | Protect claim ledger, populated scope, Markdown warning behavior. |
| `tests/test_project_commands.py::TestProjectExporter` | Protect existing JSON/CSV export contracts. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [x] JSON exports with claims and no `corpus_scope` include one structured
  `missing_corpus_scope` warning with a claim count and report-boundary message.
- [x] CSV exports with claims and no `corpus_scope` include
  `export_warnings.csv` with the same warning code/message.
- [x] JSON/CSV exports without claims do not gain warning noise or extra CSV
  files.
- [x] Markdown warning text remains present and uses the shared warning message.
- [x] Docs state this is machine-readable report discipline, not sampling-frame
  validation.

> Process criteria (quality gates):
- [x] Required tests pass (`python -m pytest tests/test_claim_ledger_exports.py tests/test_project_commands.py::TestProjectExporter -q`: 18 passed)
- [x] Full test suite passes (`make check`: 780 passed, 1 skipped, 8 deselected; Ruff/docs-check passed)
- [x] Type check status is reported (`make check`: type check not yet configured)
- [x] Docs updated

---

## Open Questions

- [x] Should JSON/CSV exports also surface missing scope warnings? — Status:
  RESOLVED | Answer: Yes, when claims exist and `corpus_scope` is missing; keep
  no-claim/minimal exports quiet.

---

## Notes

This intentionally does not add a warning for every missing `corpus_scope`.
The warning is tied to claim-bearing exports because that is where a missing
scope boundary can invite population-level overgeneralization.
