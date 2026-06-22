# Plan #127: Confidence Calibration Protocol Result Preflight

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #126 Confidence calibration protocol package
**Blocks:** Confidence-calibration scorecard preflight guard, populated held-out calibration benchmark

---

## Gap

**Current:** `make validate-confidence-calibration-protocol PROTOCOL=...` can
validate pre-evaluation calibration protocol metadata, and `make bench
CALIBRATION=calibration.json` can score externally supplied
confidence/correctness rows. There is no standalone protocol/result preflight
that checks a concrete result file against a registered calibration protocol.

**Target:** Add deterministic confidence-calibration protocol/result preflight:

- `qc_clean/core/confidence_calibration_preflight.py`.
- `scripts/preflight_confidence_calibration_protocol.py protocol.json --calibration-file calibration.json`.
- `make confidence-calibration-preflight PROTOCOL=protocol.json CALIBRATION=calibration.json`.
- Preflight validates the protocol, validates concrete calibration rows using
  `ConfidenceCalibrationEvaluation`, checks optional result-file SHA-256 locks,
  label-source/evaluator consistency, target surfaces, and planned item count.
- Machine-readable schema_version=1 pass/fail report with claim-discipline
  caution.
- Docs updated to clarify this is protocol/result provenance only, not
  calibration proof, held-out correctness evidence, methodological-validity
  evidence, or SOTA evidence.

**Why:** Protocol validation records intended calibration evaluation design.
Result preflight checks that concrete rows still match that registered design
before the scorecard consumes them. This prepares the later score-time guard
without claiming populated held-out calibration evidence.

---

## References Reviewed

- `qc_clean/core/confidence_calibration_protocol.py` - protocol package
  validator and field semantics.
- `qc_clean/core/bench.py` - `ConfidenceCalibrationEvaluation` and scorecard
  row validation semantics.
- `qc_clean/core/d9_interpretive_preference_preflight.py` - recent
  protocol/result preflight pattern.
- `scripts/preflight_d9_interpretive_preference_protocol.py` - machine-readable
  preflight CLI pattern.
- `tests/test_d9_interpretive_preference_preflight.py` - preflight regression
  shape.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` -
  calibration claim discipline and remaining-evidence caveats.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.
- Coordination claims: no active claim files found under
  `~/.claude/coordination/claims/` before this plan.

---

## Research Basis For This Slice

No new external research. This is deterministic provenance/preflight plumbing
for already implemented local confidence-calibration metrics.

---

## Capabilities

Internal preflight capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `preflight_confidence_calibration_payloads` | Confidence-calibration protocol JSON + optional calibration result JSON | Confidence-calibration preflight report | qualitative_coding | agents/operators preparing calibration scorecard inputs | free |

### Capability Validation

- [x] Matching protocol/result payloads produce `status="pass"`.
- [x] Missing result file produces `status="fail"` with a machine-readable
  error.
- [x] Result-file SHA-256 mismatches fail when protocol locks the outcome hash.
- [x] Result rows must match protocol target surfaces and label-source/evaluator
  metadata.
- [x] Result rows must meet or exceed protocol planned item count.
- [x] CLI emits machine-readable JSON and returns non-zero on failed preflight.
- [x] Make target routes to the CLI.

---

## Files Affected

- `qc_clean/core/confidence_calibration_preflight.py` (add)
- `scripts/preflight_confidence_calibration_protocol.py` (add)
- `tests/test_confidence_calibration_preflight.py` (add)
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

1. Write TDD tests for passing preflight, missing result file, hash mismatch,
   target/label-source mismatch, planned item undershoot, and CLI JSON output.
2. Implement preflight report/error models and
   `preflight_confidence_calibration_payloads`.
3. Add the preflight script and Make target.
4. Update docs with protocol/result-preflight-only caveats and future
   score-time guard direction.
5. Run focused tests, focused Ruff, Make dry-run, docs checks, and full
   `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_confidence_calibration_preflight.py` | `test_preflight_confidence_calibration_passes_matching_protocol_and_results` | Matching protocol/results pass and report counts/surfaces/metrics. |
| `tests/test_confidence_calibration_preflight.py` | `test_preflight_confidence_calibration_requires_result_payload` | Protocol preflight requires calibration results. |
| `tests/test_confidence_calibration_preflight.py` | `test_preflight_confidence_calibration_reports_hash_and_surface_mismatches` | Hash locks and target surfaces are enforced. |
| `tests/test_confidence_calibration_preflight.py` | `test_preflight_confidence_calibration_reports_label_source_and_item_count_mismatches` | Label-source/evaluator metadata and planned item count are enforced. |
| `tests/test_confidence_calibration_preflight.py` | `test_preflight_confidence_calibration_script_outputs_json` | CLI emits valid/invalid JSON reports and exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_confidence_calibration_preflight.py tests/test_confidence_calibration_protocol.py -q` | New preflight behavior plus protocol dependency. |
| `python -m ruff check qc_clean/core/confidence_calibration_preflight.py scripts/preflight_confidence_calibration_protocol.py tests/test_confidence_calibration_preflight.py` | Focused lint on new surfaces. |
| `make -n confidence-calibration-preflight PROTOCOL=protocol.json CALIBRATION=calibration.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Importable preflight returns a schema_version=1 report with pass/fail
  status, counts, protocol metadata, errors, and caution.
- [x] CLI/Make preflight returns exit code 0 only when status is `pass`.
- [x] Protocol outcome-file hash locks are enforced when provided.
- [x] Protocol target surfaces and label-source metadata are checked against
  rows.
- [x] Planned item count undershoots fail.
- [x] Docs state this is process/provenance only.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should label-source consistency use result row `evaluator` values?
  — Status: DECIDED | Yes for this slice. `ConfidenceCalibrationEvaluation`
  documents `evaluator` as evaluator or gold source, so protocol
  `label_plan.label_sources` will be compared to result-row `evaluator`
  values until a richer label-source field exists.
- [ ] Should score-time guard inject protocol metadata into calibration
  scorecards? — Status: DEFERRED | Decide in the score-time guard lane after
  standalone preflight exists.

---

## Outcome

Implemented in `f147b2e`:

- Added `qc_clean/core/confidence_calibration_preflight.py` with a
  schema_version=1 pass/fail report, protocol metadata, row counts, evaluator
  counts, machine-readable errors, and claim-discipline caution.
- Added `scripts/preflight_confidence_calibration_protocol.py` and
  `make confidence-calibration-preflight PROTOCOL=... CALIBRATION=...`.
- Added regression coverage for pass, missing result payload, hash mismatch,
  target-surface mismatch, label-source mismatch, planned-item-count
  undershoot, and CLI JSON/exit-code behavior.
- Updated `CLAUDE.md`, generated `AGENTS.md`, `docs/EVALUATION_HARNESS.md`,
  and `docs/PROJECT_THEORY_AND_GOALS.md` to describe this as
  process/provenance metadata only.

Verification:

- TDD red: missing `qc_clean.core.confidence_calibration_preflight` module.
- `python -m pytest tests/test_confidence_calibration_preflight.py tests/test_confidence_calibration_protocol.py -q`
  passed: 11 passed.
- `python -m ruff check qc_clean/core/confidence_calibration_preflight.py scripts/preflight_confidence_calibration_protocol.py tests/test_confidence_calibration_preflight.py`
  passed.
- `make -n confidence-calibration-preflight PROTOCOL=protocol.json CALIBRATION=calibration.json`
  routed to `scripts/preflight_confidence_calibration_protocol.py`.
- `make docs-check` passed.
- `make check` passed: 1012 passed, 1 skipped, 8 deselected; Ruff passed;
  docs-check passed.
- Type check is not configured in this repo.
- Implementation commit `f147b2e` was pushed to `origin/main`.

---

## Notes

This plan creates a protocol/result preflight. It does not create calibration
items, collect correctness labels, validate label correctness beyond
schema/protocol consistency, prove confidence calibration, prove
methodological validity, or license a SOTA claim.
