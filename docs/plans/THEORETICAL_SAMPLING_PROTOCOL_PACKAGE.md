# Plan #136: Theoretical Sampling Protocol Package

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Existing INV-4 category adequacy diagnostic and sampling suggestions
**Blocks:** Pre-registered theoretical-sampling runs and future sampling preflight/results

---

## Gap

**Current:** INV-4 has diagnostic-only category adequacy and local
`suggest_next_documents()` guidance over already-loaded uncoded documents. The
repo still has no machine-readable theoretical-sampling protocol artifact for
pre-registering gap targets, candidate-source policy, thresholds, collection
rules, and stopping criteria before additional data collection/selection.

**Target:** Add a schema_version=1 theoretical-sampling protocol package
validator plus Make/script surfaces:

- `make validate-theoretical-sampling-protocol PROTOCOL=protocol.json`
- `scripts/validate_theoretical_sampling_protocol.py protocol.json`

**Why:** The roadmap calls out a full theoretical sampling protocol as a
remaining INV-4 gap. This slice creates the protocol contract only; it does not
collect data, select participants, or prove saturation.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - theoretical sampling remains unmet.
- `qc_clean/core/pipeline/saturation.py` - category adequacy thresholds.
- `qc_clean/core/pipeline/theoretical_sampling.py` - current loaded-document
  suggestion heuristic.
- `tests/test_category_saturation_inv4.py` and `tests/test_cross_interview.py`
  - existing INV-4 coverage.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Scope And Non-Goals

This plan validates protocol metadata only. It is not a sampling-frame
adequacy evaluation, not a data-collection workflow, not a theoretical
saturation result, and not full grounded-theory evidence.

Future lanes can preflight a protocol against a concrete project state,
candidate pool, or completed sampling result package.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_theoretical_sampling_protocol` | schema_version=1 protocol JSON | validated protocol or JSON error | qualitative_coding | agents/operators planning INV-4 sampling runs | free |

### Capability Validation

- [ ] Valid protocol packages load and preserve configured thresholds, target
  gaps, candidate-source policy, collection rules, stopping rule, and success
  criteria.
- [ ] Invalid protocols fail loudly on missing target gaps, invalid hashes,
  duplicate target gap codes, absent stopping rule, or absent success criteria.
- [ ] Script emits validated JSON on success and JSON errors on failure.
- [ ] Make target exposes the validator.

---

## Files Affected

- `qc_clean/core/theoretical_sampling_protocol.py` (new)
- `scripts/validate_theoretical_sampling_protocol.py` (new)
- `tests/test_theoretical_sampling_protocol.py` (new)
- `Makefile` (modify)
- `CLAUDE.md` and `AGENTS.md` (docs/update)
- `docs/PROJECT_THEORY_AND_GOALS.md` and/or `docs/EVALUATION_HARNESS.md`
  (docs/update)
- `docs/plans/CLAUDE.md` and `docs/plans/ACTIVE_SPRINT.md` (plan tracking)

---

## Plan

### Steps

1. Commit this plan and mark it active.
2. Add TDD tests for valid protocol loading, invalid invariants, and script
   success/failure behavior.
3. Implement Pydantic protocol models and loader/validator helpers.
4. Add script and Make target.
5. Update docs with the new protocol surface and caveats.
6. Run focused tests, focused Ruff, `make docs-check`, and full `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_theoretical_sampling_protocol.py` | `test_valid_theoretical_sampling_protocol_loads` | Valid schema_version=1 protocol validates and preserves metadata. |
| `tests/test_theoretical_sampling_protocol.py` | `test_theoretical_sampling_protocol_rejects_missing_target_gaps` | Missing target gap codes fail loudly. |
| `tests/test_theoretical_sampling_protocol.py` | `test_theoretical_sampling_protocol_rejects_duplicate_target_gap_codes` | Duplicate target gap codes fail loudly. |
| `tests/test_theoretical_sampling_protocol.py` | `test_validate_theoretical_sampling_protocol_script_outputs_json` | Script emits validated JSON and JSON errors with proper exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_theoretical_sampling_protocol.py tests/test_category_saturation_inv4.py -q` | New protocol plus existing INV-4 diagnostic behavior. |
| `python -m ruff check qc_clean/core/theoretical_sampling_protocol.py scripts/validate_theoretical_sampling_protocol.py tests/test_theoretical_sampling_protocol.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_clean.core.theoretical_sampling_protocol` validates
  schema_version=1 protocol packages.
- [ ] `make validate-theoretical-sampling-protocol` exists and delegates to the
  script.
- [ ] The validator enforces meaningful target gaps, source policy, thresholds,
  collection rules, stopping rule, success criteria, project/corpus hashes, and
  claim-discipline caveat.
- [ ] Docs preserve that this is protocol infrastructure, not evidence of
  theoretical sampling, sampling adequacy, or GT saturation.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Notes

This is the first slice of the theoretical-sampling protocol gap. It makes the
future work agent-drivable without pretending that a populated sampling cycle
has happened.
