# Plan #105: Adjudication Response Preflight

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Adjudication protocol package; Adjudication protocol sample preflight; INV-3 adjudication response validator
**Blocks:** safer D3/D7 gold import; held-out adjudication run discipline

---

## Outcome

Implemented and pushed in commit `15c2785`:

- Added `qc_clean/core/adjudication_response_preflight.py` with a
  machine-readable response preflight report.
- Added `scripts/preflight_adjudication_responses.py` and
  `make adjudication-response-preflight PROTOCOL=... SAMPLE=...
  RESPONSES=...`.
- Added TDD coverage for pass, upstream preflight failure propagation,
  incomplete responses, item-ID mismatch, hash mismatch, required target-type
  completion, and CLI JSON/exit-code behavior.
- Updated claim-discipline docs to state response preflight is
  process/provenance metadata only, not expert evidence or validity evidence.

Verification:

- `python -m pytest tests/test_adjudication_response_preflight.py -q` failed
  before implementation with missing module import, as expected.
- `python -m pytest tests/test_adjudication_response_preflight.py
  tests/test_adjudication_preflight.py tests/test_adjudication_protocol.py
  tests/test_adjudication_sample.py tests/test_adjudication_import.py -q` ->
  28 passed.
- `python -m ruff check qc_clean/core/adjudication_response_preflight.py
  scripts/preflight_adjudication_responses.py
  tests/test_adjudication_response_preflight.py
  qc_clean/core/adjudication_preflight.py qc_clean/core/adjudication_sample.py
  qc_clean/core/adjudication_import.py` -> passed.
- `make docs-check` -> passed.
- `make help | rg "adjudication-response-preflight"` -> target discoverable.
- `make -n adjudication-response-preflight PROTOCOL=protocol.json
  SAMPLE=sample.json RESPONSES=responses.json` -> expected script invocation.
- `make check` -> 908 passed, 1 skipped, 8 deselected; Ruff/docs green; type
  check not yet configured.

---

## Gap

**Current:** The repo can validate a protocol, preflight that protocol against an
unlabeled sample, and validate completed response package shape/completeness.
There is no single pre-import gate that proves a completed response package
matches the governed protocol/sample pair.

**Target:** Add a response preflight:

- Core: `qc_clean/core/adjudication_response_preflight.py`
- Script: `scripts/preflight_adjudication_responses.py`
- Make target: `make adjudication-response-preflight PROTOCOL=protocol.json
  SAMPLE=sample.json RESPONSES=responses.json`
- Checks:
  - protocol/sample preflight passes first;
  - completed response package validation status is `complete`;
  - response package project/corpus/project-state hashes match the sample;
  - response item IDs exactly match the sample item IDs;
  - all protocol-required target item types have completed responses.
- Output is a machine-readable pass/fail report with the same caveat that
  preflight is process metadata, not expert evidence.

**Why:** This is the last deterministic gate before `make
import-adjudication-responses` converts responses into D3/D7 gold package inputs.
It prevents accidentally importing labels from the wrong sample or an incomplete
response file.

---

## References Reviewed

- `qc_clean/core/adjudication_preflight.py` - protocol/sample preflight report
  and hash checks.
- `qc_clean/core/adjudication_protocol.py` - protocol package schema.
- `qc_clean/core/adjudication_sample.py` - sample/response package schema and
  `validate_adjudication_response_payload`.
- `qc_clean/core/adjudication_import.py` - downstream response-to-gold import.
- `scripts/preflight_adjudication_protocol_sample.py` - preflight script output
  pattern.
- `scripts/validate_adjudication_responses.py` - response validation script
  behavior.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - current
  INV-3 claim discipline.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references. This is deterministic local
preflight over existing protocol/sample/response package contracts.

---

## Capabilities

Internal preflight capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `preflight_adjudication_responses` | protocol file + sample file + completed response file | response preflight report | qualitative_coding | agents, `make import-adjudication-responses` operators | free |

### Capability Validation

- [x] Protocol/sample preflight is reused instead of duplicating those checks.
- [x] Response completeness validation is reused.
- [x] Item identity and target-type coverage checks are covered by tests.
- [x] CLI emits machine-readable JSON.

---

## Files Affected

- `qc_clean/core/adjudication_response_preflight.py` (create)
- `scripts/preflight_adjudication_responses.py` (create)
- `tests/test_adjudication_response_preflight.py` (create)
- `Makefile` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify after closeout)

---

## Plan

### Steps

1. Write TDD tests for pass, protocol/sample preflight failure propagation,
   incomplete response validation, item-ID mismatch, hash mismatch, and script
   JSON output.
2. Implement `qc_clean/core/adjudication_response_preflight.py` with report
   models and response cross-check helpers.
3. Add script and Make target.
4. Update docs to state response preflight is a process gate only.
5. Run focused tests, focused Ruff, docs checks, and full `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_adjudication_response_preflight.py` | `test_response_preflight_accepts_matching_protocol_sample_and_responses` | Matching complete responses pass. |
| `tests/test_adjudication_response_preflight.py` | `test_response_preflight_propagates_protocol_sample_failures` | Existing protocol/sample mismatch blocks response preflight. |
| `tests/test_adjudication_response_preflight.py` | `test_response_preflight_rejects_incomplete_responses` | Incomplete completed-response package fails. |
| `tests/test_adjudication_response_preflight.py` | `test_response_preflight_rejects_item_id_mismatch` | Response item IDs must match sample item IDs exactly. |
| `tests/test_adjudication_response_preflight.py` | `test_response_preflight_rejects_response_hash_mismatch` | Response project/corpus hashes must match sample package. |
| `tests/test_adjudication_response_preflight.py` | `test_response_preflight_rejects_missing_required_target_type_responses` | Protocol-required response target types must be complete. |
| `tests/test_adjudication_response_preflight.py` | `test_response_preflight_script_outputs_json` | CLI emits valid/invalid machine-readable JSON with exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_adjudication_preflight.py tests/test_adjudication_protocol.py tests/test_adjudication_sample.py` | Upstream package contracts stay unchanged. |
| `tests/test_adjudication_import.py` | Downstream import remains unchanged. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Matching protocol/sample/response package trio passes preflight.
- [x] Protocol/sample preflight failures block response preflight.
- [x] Incomplete responses fail loudly.
- [x] Response/sample item-ID mismatch fails loudly.
- [x] Response/sample hash mismatch fails loudly.
- [x] `make adjudication-response-preflight PROTOCOL=... SAMPLE=...
  RESPONSES=...` is discoverable.
- [x] Docs state response preflight is process/provenance metadata only, not
  labels or evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should `make import-adjudication-responses` require a successful response
  preflight report in held-out mode? — Status: DEFERRED | Why it matters: this
  slice adds the explicit gate; making import depend on a prior preflight report
  is a stricter workflow-policy change.

---

## Notes

Response preflight should run immediately before response import. It proves the
files line up; it still does not prove the labels are correct.
