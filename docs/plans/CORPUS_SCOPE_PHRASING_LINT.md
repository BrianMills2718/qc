# Plan #93: Corpus Scope Phrasing Lint

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Corpus scope warnings; scope-bound claim export rows
**Blocks:** safer agent/human report drafting; broader scope-aware phrasing checks

---

## Gap

**Current:** Claim-bearing JSON/CSV/Markdown exports warn when corpus scope is
missing or under-specified, and claim export rows carry compact scope/boundary
context. Arbitrary text outside those deterministic export rows - hand-written
summaries, generated memos, copied report excerpts, or future agent-authored
briefs - can still use population-generalizing language without a defensible
`CorpusScope`.

**Target:** Add a deterministic, agent-drivable phrasing lint that scans a text
file/string against a `ProjectState` scope boundary:

- Core: `qc_clean/core/scope_lint.py`
- Script: `scripts/lint_scope_phrasing.py <project_id> --input-file report.md`
- Make: `make lint-scope-phrasing ID=<project_id> INPUT=report.md`

The lint should emit a JSON report and exit nonzero when risky phrases are found
under missing, empty, or population-without-sampling-frame scope conditions.

**Why:** The scope contract is only useful if downstream prose respects it. This
slice gives agents and humans a deterministic guardrail before publishing or
handing off qualitative claims, while still avoiding any claim that the sampling
frame is valid or that the analysis is correct.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline and roadmap item #8.
- `docs/plans/completed/CORPUS_SCOPE_COMPLETENESS_WARNINGS.md` - missing,
  empty, and missing-sampling-frame warning semantics.
- `docs/plans/completed/SCOPE_BOUND_CLAIM_EXPORT_ROWS.md` - per-row scope and
  boundary phrasing.
- `qc_clean/core/export/data_exporter.py` - existing scope warning messages and
  boundary helper behavior.
- `tests/test_claim_ledger_exports.py` - scope warning/export regression
  patterns.
- `qc_clean/core/persistence/project_store.py` - project loading for the script.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research is needed. This is a deterministic wording guard for an
already-documented claim-discipline rule: do not generalize beyond the loaded
documents without a stated and defensible sampling frame.

---

## Capabilities

| Capability | Input | Output | Consumer |
|------------|-------|--------|----------|
| `lint_scope_phrasing` | `ProjectState`, report text, optional source label | lint report model | script, future preflight checks |
| `scope_status_for_lint` | `ProjectState` | missing/empty/missing_sampling_frame/complete status | lint report and future policy checks |

---

## Files Affected

- `qc_clean/core/scope_lint.py` (create)
- `scripts/lint_scope_phrasing.py` (create)
- `Makefile` (modify)
- `tests/test_scope_phrasing_lint.py` (create)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/CORPUS_SCOPE_PHRASING_LINT.md` (create, then move to completed)

---

## Plan

### Decisions

- Linting is advisory and deterministic. It does not mutate project state or
  block exports.
- The lint scans only caller-supplied text. It does not rewrite prose.
- Scope status values:
  - `missing`: no `ProjectState.corpus_scope`
  - `empty`: scope object exists but has no details
  - `missing_sampling_frame`: population is recorded without sampling frame
  - `complete`: at least one defensible boundary path exists for this lint
- Risky phrases are deliberately narrow and explainable: generalization words
  (`generalize`, `representative`), explicit population language, and broad
  quantifier/location patterns such as `all/most/many participants`, `across
  teams`, `among users`, or `in the sector generally`.
- Complete scope suppresses missing/under-specified-scope lint warnings, but
  the report still includes a caveat that `CorpusScope` is not sampling-adequacy
  evidence.
- Script exits `1` when warnings are present, `0` otherwise, and always prints
  JSON.

### Steps

1. Add Pydantic report/warning models and lint functions in
   `qc_clean/core/scope_lint.py`.
2. Add tests for safe loaded-document phrasing, missing-scope risky phrasing,
   empty-scope risky phrasing, population-without-sampling-frame risky phrasing,
   complete-scope suppression, and script exit/output behavior.
3. Add `scripts/lint_scope_phrasing.py`.
4. Add `make lint-scope-phrasing ID=... INPUT=...`.
5. Update docs conservatively: scope phrasing lint is a report-discipline guard,
   not sampling-frame adequacy validation.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_scope_phrasing_lint.py` | `test_scope_lint_allows_loaded_document_phrasing_without_scope` | Explicit loaded-document phrasing does not warn when scope is missing. |
| `tests/test_scope_phrasing_lint.py` | `test_scope_lint_warns_on_generalization_without_scope` | Missing scope plus risky population/generalization text produces warning lines. |
| `tests/test_scope_phrasing_lint.py` | `test_scope_lint_warns_on_empty_scope` | Empty `CorpusScope()` is not treated as a safe boundary. |
| `tests/test_scope_phrasing_lint.py` | `test_scope_lint_warns_when_population_lacks_sampling_frame` | Population without sampling frame warns on broad population phrasing. |
| `tests/test_scope_phrasing_lint.py` | `test_scope_lint_complete_scope_suppresses_under_specified_scope_warnings` | Complete scope does not produce missing-scope warnings for the same text. |
| `tests/test_scope_phrasing_lint.py` | `test_scope_lint_script_outputs_json_and_exit_codes` | Script prints JSON and exits nonzero only when warnings exist. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_scope_phrasing_lint.py -q` | New lint behavior. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Core lint returns a typed JSON-serializable report with status, scope
  status, warning count, line-level warnings, and caveat.
- [ ] Missing scope, empty scope, and population-without-sampling-frame status
  can trigger warnings on risky population/generalization phrases.
- [ ] Loaded-document-only phrasing does not warn.
- [ ] Complete scope suppresses missing/under-specified-scope warnings while
  preserving a non-evidence caveat.
- [ ] Script and Make target are agent-drivable and exit nonzero on warnings.
- [ ] Docs state this is phrasing/report discipline, not sampling adequacy or
  validity evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should this lint eventually run automatically on Markdown exports? -
  Status: DEFERRED | Why it matters: exports already have deterministic scope
  warnings and per-row context; auto-lint can be a future strict/preflight mode.
- [ ] Should phrase patterns become configurable? - Status: DEFERRED | Why it
  matters: configuration is useful, but this first slice should keep the warning
  surface deterministic and testable.

---

## Notes

This lint is intentionally not a semantic claim checker. It catches a bounded
set of unsafe wording patterns when scope metadata is absent or under-specified.
It does not decide whether a complete sampling frame is adequate.
