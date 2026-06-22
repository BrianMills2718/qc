# Plan #92: INV-3 Adjudication Response Validator

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #91 adjudication sample export
**Blocks:** Safe label import from adjudication packets; D3/D7 gold conversion workflows

---

## Gap

**Current:** `make adjudication-sample` can export schema_version=1 unlabeled
review packets for human/expert adjudicators. There is no deterministic
validator for completed packets. That means malformed, incomplete, or ambiguous
responses could be mistaken for valid labels before any future D3/D7 gold
conversion or scorecard use.

**Target:** Add a strict response validator for completed adjudication sample
packets:

- Core validation in `qc_clean/core/adjudication_sample.py`.
- Script: `scripts/validate_adjudication_responses.py sample.json`.
- Make: `make validate-adjudication-responses PACKAGE=sample.json`.

The validator should accept response data either in an item-level `response`
object or in a filled `response_template` object, because exported packets
already include `response_template`.

**Why:** INV-3 requires human/expert adjudication as a separate validity step.
Before labels can safely feed gold packages, the repo needs fail-loud checks
that responses are complete and shaped correctly. This still does not make the
responses gold or evidence.

---

## References Reviewed

- `docs/plans/completed/INV3_ADJUDICATION_SAMPLE_EXPORT.md` - exported packet
  shape and deferred label import question.
- `qc_clean/core/adjudication_sample.py` - schema_version=1 sample package and
  response template fields.
- `scripts/validate_d3_gold_set.py`, `scripts/validate_d7_gold_set.py`, and
  `scripts/validate_inv7_prompt_injection_package.py` - existing validator
  script pattern.
- `Makefile` - package validator target pattern.
- `docs/PROJECT_THEORY_AND_GOALS.md` / `docs/EVALUATION_HARNESS.md` -
  claim-discipline caveats around expert evidence.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research is needed. This is schema/protocol validation over the
local sample package format.

---

## Capabilities

| Capability | Input | Output | Consumer |
|------------|-------|--------|----------|
| `validate_adjudication_response_payload` | raw sample/response package JSON | validation report model | validator script, future label importer |
| `load_adjudication_response_package` | JSON path | validation report model | Make/script surface |

---

## Files Affected

- `qc_clean/core/adjudication_sample.py` (modify)
- `scripts/validate_adjudication_responses.py` (create)
- `Makefile` (modify)
- `tests/test_adjudication_sample.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV3_ADJUDICATION_RESPONSE_VALIDATOR.md` (create, then move to completed)

---

## Plan

### Decisions

- Validity labels are restricted to `valid`, `invalid`, or `unclear`.
- Every item must have a response object with non-empty `validity` and
  `adjudicator_id`.
- `invalid` and `unclear` responses must include a non-empty rationale.
- Unknown validity labels, missing responses, and duplicate item IDs are
  validation errors.
- Validator returns a report with status `complete` or `invalid`, counts by
  validity, errors, and a caveat that validation is not expert evidence.
- This plan does not import responses into `ProjectState`, create D3/D7 gold
  packages, or score system correctness.

### Steps

1. Add response/report models and validation functions to
   `qc_clean/core/adjudication_sample.py`.
2. Add tests for complete packets, invalid packets, duplicate item IDs, and
   script output.
3. Add `scripts/validate_adjudication_responses.py`.
4. Add `make validate-adjudication-responses PACKAGE=...`.
5. Update docs conservatively: response validation exists, but labels are still
   not gold/evidence until a future importer/protocol does that work.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_adjudication_sample.py` | `test_validate_complete_adjudication_responses` | Complete filled responses validate and summarize counts. |
| `tests/test_adjudication_sample.py` | `test_validate_adjudication_responses_reports_errors` | Missing/invalid responses fail loudly with item-level errors. |
| `tests/test_adjudication_sample.py` | `test_validate_adjudication_responses_rejects_duplicate_item_ids` | Duplicate item IDs are validation errors. |
| `tests/test_adjudication_sample.py` | `test_validate_adjudication_responses_script` | Script emits JSON report and nonzero exit for invalid packages. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_adjudication_sample.py -q` | Sample package + response validator behavior. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Completed sample packets can be validated without mutating project state.
- [ ] Missing/blank responses, bad labels, missing required rationales, and
  duplicate item IDs produce item-level errors.
- [ ] Validator script emits compact JSON and exits nonzero on invalid packets.
- [ ] Make target exposes response validation for agents.
- [ ] Docs state response validation is a protocol check, not expert evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should valid responses with `corrected_value` be normalized into typed
  review decisions? - Status: DEFERRED | Why it matters: that belongs to a
  future import/apply workflow, not response validation.
- [ ] Should validated responses be convertible to D3/D7 gold packages? -
  Status: DEFERRED | Why it matters: gold conversion must preserve metric-
  specific semantics and not treat arbitrary responses as scorecard truth.

---

## Notes

This plan validates response completeness and shape only. A valid response file
is not a populated benchmark result, not a gold set, and not evidence that the
system is correct.
