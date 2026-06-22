# Plan #126: Confidence Calibration Protocol Package

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Confidence calibration scorecard, Wilson intervals, and bootstrap intervals
**Blocks:** Confidence-calibration protocol/result preflight, score-time guard, populated held-out calibration benchmark

---

## Gap

**Current:** `make bench CALIBRATION=calibration.json` can score externally
supplied confidence/correctness rows, including accuracy Wilson intervals,
Brier score, expected calibration error, bin summaries, per-surface summaries,
and deterministic local Brier/ECE bootstrap intervals. There is no standalone
pre-evaluation protocol package for confidence-calibration benchmark metadata.

**Target:** Add a versioned confidence-calibration protocol package:

- `qc_clean/core/confidence_calibration_protocol.py`.
- `scripts/validate_confidence_calibration_protocol.py protocol.json`.
- `make validate-confidence-calibration-protocol PROTOCOL=protocol.json`.
- Tests covering valid held-out protocols, held-out gates, hash validation,
  label-source/evaluator plan requirements, target surfaces, planned item
  count, confidence source, configured outcome metrics, and success criteria.
- Docs updated to clarify this is protocol/provenance only, not calibration
  proof, held-out correctness evidence, methodological-validity evidence, or
  SOTA evidence.

**Why:** Calibration scoring already exists, but the benchmark still lacks a
pre-registered protocol describing the frozen prediction/confidence artifact,
correctness-label source, target surfaces, outcome metrics, and success
criteria before labels are collected or scored. This creates the first link in
the confidence-calibration protocol -> result -> scorecard provenance chain.

---

## References Reviewed

- `qc_clean/core/bench.py` - `ConfidenceCalibrationEvaluation`,
  `confidence_calibration_scorecard`, accuracy intervals, Brier score, ECE,
  bin summaries, and bootstrap interval semantics.
- `scripts/bench_phase0.py` - external calibration file loader and Phase 0
  input-hash/provenance plumbing.
- `qc_clean/core/d9_interpretive_preference_protocol.py` - recent protocol
  package validator pattern.
- `scripts/validate_d9_interpretive_preference_protocol.py` - CLI validator
  pattern.
- `tests/test_d9_interpretive_preference_protocol.py` - protocol package
  regression shape.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` -
  calibration claim discipline and remaining-evidence caveats.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.
- Coordination claims: no active claim files found under
  `~/.claude/coordination/claims/` before this plan.

---

## Research Basis For This Slice

No new external research. This slice only validates pre-evaluation protocol
metadata for the already implemented local calibration metrics. A populated
held-out calibration benchmark remains future work.

---

## Capabilities

Internal protocol validation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_confidence_calibration_protocol` | Confidence-calibration protocol JSON | Validated protocol object or machine-readable JSON error | qualitative_coding | agents/operators preparing calibration evaluations | free |

### Capability Validation

- [ ] Valid schema_version=1 held-out confidence-calibration protocols pass
  validation.
- [ ] Held-out protocols require prompt/model freeze, contamination check,
  pre-evaluation registration, project-state hash, and prediction/confidence
  artifact hash.
- [ ] Corpus/project/prediction/outcome hashes are valid SHA-256 values.
- [ ] Label-source plan, target surfaces, confidence source, planned item
  count, and configured outcome metrics are non-empty.
- [ ] Success criteria cover configured calibration outcome metrics.
- [ ] CLI emits machine-readable JSON for valid and invalid protocols.
- [ ] Make target routes to the CLI.

---

## Files Affected

- `qc_clean/core/confidence_calibration_protocol.py` (add)
- `scripts/validate_confidence_calibration_protocol.py` (add)
- `tests/test_confidence_calibration_protocol.py` (add)
- `Makefile` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Write failing protocol-validator tests and Make dry-run expectation.
2. Implement Pydantic protocol models, loader, payload validator, and claim
   caution.
3. Add the CLI validator and Make target.
4. Update docs with protocol-only caveats and future preflight/guard direction.
5. Run focused tests, focused Ruff, Make dry-run, docs checks, and full
   `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_confidence_calibration_protocol.py` | `test_validate_confidence_calibration_protocol_accepts_held_out_package` | Valid held-out calibration protocol metadata validates and preserves target surfaces/outcome metrics. |
| `tests/test_confidence_calibration_protocol.py` | `test_validate_confidence_calibration_protocol_requires_held_out_gates` | Held-out gates fail loud when freeze/contamination/registration/hashes are missing. |
| `tests/test_confidence_calibration_protocol.py` | `test_validate_confidence_calibration_protocol_requires_label_plan_and_case_design` | Empty label-source plan, target surfaces, confidence source, planned item count, and outcome metrics fail. |
| `tests/test_confidence_calibration_protocol.py` | `test_validate_confidence_calibration_protocol_rejects_bad_hashes` | Malformed hash locks fail. |
| `tests/test_confidence_calibration_protocol.py` | `test_validate_confidence_calibration_protocol_requires_success_criteria_for_each_metric` | Success criteria must cover configured calibration outcome metrics. |
| `tests/test_confidence_calibration_protocol.py` | `test_validate_confidence_calibration_protocol_script_outputs_json` | CLI emits valid/invalid JSON and exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_confidence_calibration_protocol.py -q` | New calibration protocol contract. |
| `python -m ruff check qc_clean/core/confidence_calibration_protocol.py scripts/validate_confidence_calibration_protocol.py tests/test_confidence_calibration_protocol.py` | Focused lint on new surfaces. |
| `make -n validate-confidence-calibration-protocol PROTOCOL=protocol.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Confidence-calibration protocols can be validated before correctness
  labels are collected or scored.
- [ ] Held-out protocols enforce freeze/contamination/registration gates and
  required hashes.
- [ ] Protocols carry label-source, confidence-source, target-surface, planned
  item-count, and outcome-metric metadata as pre-evaluation process data.
- [ ] CLI and Make target emit machine-readable success/failure.
- [ ] Docs state the validator is process/provenance only.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should confidence-calibration protocol/result preflight require exact
  target-surface equality or allow result subsets? — Status: DEFERRED |
  Decide in the result-preflight lane after this protocol validator exists.
- [ ] Should score-time guard configuration include protocol-governed bootstrap
  settings or keep bootstrap settings in Phase 0 config only? — Status:
  DEFERRED | Decide in the score-time guard lane if the protocol/result
  preflight needs to govern uncertainty settings.

---

## Notes

This plan validates protocol metadata only. It does not create calibration
items, collect correctness labels, validate label correctness, prove confidence
calibration, prove methodological validity, or license a SOTA claim.
