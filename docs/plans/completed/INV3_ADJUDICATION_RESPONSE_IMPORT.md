# Plan #101: INV-3 Adjudication Response Import

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** INV-3 adjudication sample export; INV-3 adjudication response validator; D3/D7 gold-set package validators
**Blocks:** populated D3/D7 scorecard runs from adjudicated labels; future expert-validity evidence protocols

---

## Outcome

Implemented an explicit response-to-gold import bridge:

- `qc_clean/core/adjudication_import.py` validates completed adjudication
  response packages and converts valid code-application / negative-case
  responses into D3/D7 gold package inputs.
- `scripts/import_adjudication_responses.py` and
  `make import-adjudication-responses` write requested D3/D7 package files.
- Invalid and unclear responses are excluded and counted, not treated as gold.
- Generated packages validate through the existing D3/D7 package validators.
- `CLAUDE.md`, generated `AGENTS.md`, `docs/PROJECT_THEORY_AND_GOALS.md`, and
  `docs/EVALUATION_HARNESS.md` state that generated packages are protocol
  artifacts, not methodological validity evidence by themselves.

Implementation commit: `9c6afea`

## Verification

- TDD red: initial `python -m pytest tests/test_adjudication_import.py -q`
  failed with `ModuleNotFoundError: No module named
  'qc_clean.core.adjudication_import'`.
- Focused behavior: `python -m pytest tests/test_adjudication_import.py
  tests/test_adjudication_sample.py tests/test_d3_gold_set.py
  tests/test_d7_gold_set.py -q` -> 19 passed.
- Focused lint: `python -m ruff check
  qc_clean/core/adjudication_import.py
  scripts/import_adjudication_responses.py tests/test_adjudication_import.py`
  -> all checks passed.
- Command discoverability: `make help` lists `import-adjudication-responses`.
- Documentation governance: `make docs-check` passed.
- Full gate: `make check` -> 886 passed, 1 skipped, 8 deselected; Ruff and
  docs-check passed; type check remains not configured.
- Commit `9c6afea` was pushed to `main`.

---

## Gap

**Current:** The repo can export unlabeled adjudication sample packets and
validate completed response shape/completeness. The response validator
deliberately does not convert responses into gold. D3 and D7 scorecards can
consume gold files, but there is no safe bridge from validated adjudication
responses to D3/D7 gold package files.

**Target:** Add an explicit importer/converter that reads a completed
schema_version=1 adjudication response package and writes versioned D3/D7 gold
packages only when requested:

- Core: `qc_clean/core/adjudication_import.py`
- Script: `scripts/import_adjudication_responses.py PACKAGE
  [--output-d3 d3_gold.json] [--output-d7 d7_gold.json] ...metadata...`
- Make: `make import-adjudication-responses PACKAGE=sample.json
  [D3_OUTPUT=d3_gold.json] [D7_OUTPUT=d7_gold.json] ...`

The importer must validate responses first, include explicit adjudication
metadata in generated packages, and exclude `invalid` / `unclear` responses from
gold anchors. It should fail loudly if a requested output would have no valid
anchors.

**Why:** INV-3 says validity adjudication is separate from consistency. This
bridge makes label import agent-drivable while preventing shape-valid response
files from being silently mistaken for benchmark truth.

---

## References Reviewed

- `qc_clean/core/adjudication_sample.py` - sample package and response
  validation models.
- `scripts/validate_adjudication_responses.py` - existing completed-response
  validator surface.
- `qc_clean/core/d3_gold.py` - D3 gold-set package schema and invariants.
- `qc_clean/core/d7_gold.py` - D7 gold-set package schema and invariants.
- `scripts/validate_d3_gold_set.py` and `scripts/validate_d7_gold_set.py` -
  package validator script patterns.
- `tests/test_adjudication_sample.py` - sample/response fixtures.
- `docs/plans/completed/INV3_ADJUDICATION_SAMPLE_EXPORT.md`
- `docs/plans/completed/INV3_ADJUDICATION_RESPONSE_VALIDATOR.md`
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research is needed. This is a deterministic local conversion
between existing repo package formats. Expert protocol design remains a separate
future lane.

---

## Capabilities

| Capability | Input | Output | Consumer |
|------------|-------|--------|----------|
| `build_adjudication_gold_import` | completed adjudication response package + metadata | D3/D7 gold packages and import report | script, Make, future bench-package workflows |
| `write_adjudication_gold_import` | import result + output paths | JSON gold package files | `make bench`, D3/D7 validators |

---

## Files Affected

- `qc_clean/core/adjudication_import.py` (create)
- `scripts/import_adjudication_responses.py` (create)
- `Makefile` (modify)
- `tests/test_adjudication_import.py` (create)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/EVALUATION_HARNESS.md` (modify if command inventory/status needs it)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV3_ADJUDICATION_RESPONSE_IMPORT.md` (create, then move to
  completed)

---

## Plan

### Decisions

- Import requires the response package to validate as `complete` before any
  gold output is written.
- Only `valid` responses become gold anchors.
- `invalid` and `unclear` responses are counted in the import report but
  excluded from D3/D7 anchors.
- D3 conversion uses `target_type="code_application"` items with source context
  and payload `code_id`.
- D7 conversion uses `target_type="negative_case"` items with source context and
  the first `payload.scope.claim_ids` value as `target_claim_id`.
- Requested D3/D7 output fails loudly if no valid anchor can be created.
- Default split is `dev`; `held_out` is allowed only if the generated D3/D7
  package validators accept the supplied metadata (`prompt_frozen`,
  `contamination_checked`, coder count).
- The importer writes package files, not benchmark results, and does not mutate
  `ProjectState`.
- This slice does not infer expert quality. The metadata must say who/what
  adjudicated the responses.

### Steps

1. Add import metadata/result models and builders in
   `qc_clean/core/adjudication_import.py`.
2. Add tests for D3 and D7 package generation, invalid-response rejection,
   no-anchor failure, and script output.
3. Add script and Make target.
4. Update docs conservatively.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_adjudication_import.py` | `test_imports_valid_responses_to_d3_and_d7_gold_packages` | Valid code-application and negative-case responses become validator-compatible D3/D7 packages. |
| `tests/test_adjudication_import.py` | `test_import_rejects_invalid_response_package` | Incomplete/invalid response packages fail before writing gold. |
| `tests/test_adjudication_import.py` | `test_import_fails_requested_output_with_no_valid_anchors` | Requested D3/D7 output fails loudly when no valid anchors exist. |
| `tests/test_adjudication_import.py` | `test_import_adjudication_responses_script_writes_outputs` | Script writes requested package files and emits a JSON import report. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_adjudication_import.py tests/test_adjudication_sample.py tests/test_d3_gold_set.py tests/test_d7_gold_set.py -q` | Importer plus source/target package compatibility. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Completed response packages are validated before conversion.
- [x] D3 output is a schema_version=1 package accepted by the existing D3
  validator.
- [x] D7 output is a schema_version=1 package accepted by the existing D7
  validator.
- [x] Invalid/unclear responses are excluded and counted, not treated as gold.
- [x] Requested empty outputs fail loudly.
- [x] Script and Make target are agent-drivable.
- [x] Docs state imported gold packages are labels/protocol artifacts, not
  methodological validity evidence unless populated under a documented expert
  protocol and scored.

> Process criteria:
- [x] Required focused tests pass.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should invalid responses generate explicit negative labels for future
  false-positive analysis? - Status: DEFERRED | Why it matters: current D3/D7
  exact-key scorecards consume positive gold anchors, so negative-label
  semantics need a separate metric design.
- [x] Should this importer support D4/D8/D9 package creation too? - Status:
  DEFERRED | Why it matters: this slice only bridges existing sample item types
  to existing D3/D7 gold contracts.

---

## Notes

This is still infrastructure. A generated gold package is only as credible as
the adjudication protocol and labels supplied to it; the command itself does
not create expert evidence.
