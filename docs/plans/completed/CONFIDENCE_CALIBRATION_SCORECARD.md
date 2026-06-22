# Plan #53: Confidence Calibration Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Confidence-calibration measurement substrate

---

## Outcome

Implemented the deterministic Phase 0 `confidence_calibration` scorecard for
externally supplied confidence/correctness records. The bench surface now
accepts `CALIBRATION=calibration.json` / `--confidence-calibration-file`,
hashes the calibration file in `_meta.input_hashes`, records it in artifact
command provenance, and keeps the file input in memory without mutating saved
project state. The scorecard reports total records, accuracy, mean confidence,
Brier score, fixed 10-bin expected calibration error, calibration bins, and
per-surface summaries. Docs state that confidence remains uncalibrated until a
populated held-out calibration benchmark exists.

## Verification

- `python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py -q` - 76 passed.
- `python -m ruff check qc_clean/core/bench.py scripts/bench_phase0.py qc_cli.py tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py` - passed.
- `python scripts/check_markdown_links.py` - passed.
- `python scripts/sync_plan_status.py --check` - passed.
- `make check` - 757 passed, 1 skipped, 8 deselected; Ruff and docs checks passed; type check not yet configured.

---

## Gap

**Current:** The theory doc states that `confidence`, `discovery_confidence`,
and `confidence_assessment` are ordinal self-reports, not calibrated
probabilities. The evaluation harness lists confidence calibration as future
work, but Phase 0 has no calibration scorecard section and no agent-drivable
way to feed external confidence/correctness outcomes into `make bench`.

**Target:** Add a deterministic `confidence_calibration` scorecard that accepts
externally supplied records from
`ProjectState.config.extra["confidence_calibration_evaluations"]` or
`CALIBRATION=` / `--confidence-calibration-file`. The scorecard will report
accuracy, mean confidence, Brier score, expected calibration error over fixed
bins, and per-surface summaries.

**Why:** This creates the local calibration measurement substrate while
preserving the hard claim discipline: confidence is not calibrated until frozen
cases with correctness labels are populated and scored under a pre-registered
benchmark protocol.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - confidence is ordinal and uncalibrated.
- `docs/EVALUATION_HARNESS.md` - confidence calibration remains future work.
- `qc_clean/core/bench.py` - external scorecard and numeric-summary patterns.
- `scripts/bench_phase0.py`, `qc_cli.py`, `Makefile` - external file input,
  hashing, provenance, and wrapper surfaces.
- `tests/test_bench_phase0.py`, `tests/test_bench_phase0_script.py`,
  `tests/test_qc_cli_bench.py` - scorecard and bench wrapper coverage.
- Memory context: unavailable. The last three `agent-memory recall` attempts in
  this session failed with the same OpenRouter 402/403 embedding-provider
  errors, so the circuit breaker applies; no local coordination claims were
  present.

---

## Research Basis For This Slice

No additional external research beyond repo-local references. This slice only
adds deterministic accounting over externally supplied confidence/correctness
records. Future extraction of calibration records from held-out tasks, scoring
against gold labels, and statistical comparisons belong in the prompt_eval-backed
suite.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Confidence calibration scorecard | External confidence/correctness records | Accuracy, confidence, Brier, ECE summaries | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [x] Calibration records are Pydantic-validated and fail loudly when malformed.
- [x] Confidence values are constrained to 0-1.
- [x] Brier score and expected calibration error are computed deterministically.
- [x] External files are hashed in `_meta.input_hashes` and recorded in artifact command provenance.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `qc_cli.py` (modify)
- `Makefile` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `tests/test_qc_cli_bench.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add `ConfidenceCalibrationEvaluation` and
   `confidence_calibration_scorecard` in `qc_clean/core/bench.py`.
2. Include `confidence_calibration` in `phase0_scorecard`, returning an
   explicit unavailable state when no external calibration records exist.
3. Add `--confidence-calibration-file` to `scripts/bench_phase0.py` and
   `qc_cli.py`, and `CALIBRATION=` to `make bench`.
4. Hash the external calibration file and include it in Phase 0 artifact command
   provenance.
5. Add focused tests for unavailable, scored, invalid metadata, external-file
   loading, hash/provenance, and CLI forwarding.
6. Update docs to mark a calibration Phase 0 substrate as present while
   preserving the caveat that system confidence is not calibrated.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | Calibration unavailable test | Missing calibration records are explicit non-evidence. |
| `tests/test_bench_phase0.py` | Calibration scored test | Accuracy, mean confidence, Brier, ECE, bins, and per-surface summaries are correct. |
| `tests/test_bench_phase0.py` | Calibration invalid metadata test | Out-of-range confidence fails loudly. |
| `tests/test_bench_phase0_script.py` | Calibration file input test | External calibration JSON is applied in memory without mutating project state. |
| `tests/test_bench_phase0_script.py` | Calibration hash/provenance test | External calibration file hash and artifact command provenance are recorded. |
| `tests/test_qc_cli_bench.py` | Calibration wrapper forwarding test | `qc_cli bench --confidence-calibration-file` reaches the canonical script. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Main Phase 0 scorecard shape. |
| `tests/test_bench_phase0_script.py` | Bench script external-input and artifact behavior. |
| `tests/test_qc_cli_bench.py` | Top-level wrapper behavior. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Scorecard has `confidence_calibration` with explicit unavailable state
  when no calibration records exist.
- [x] Scored output reports total records, accuracy, mean confidence, Brier
  score, expected calibration error, fixed calibration bins, and per-surface
  summaries.
- [x] External calibration JSON file can be supplied through Make, script, and
  `qc_cli` without mutating saved project state.
- [x] Phase 0 input hashes and artifact command provenance include the
  calibration external file.
- [x] Docs preserve the caveat that confidence remains uncalibrated until a
  populated held-out calibration benchmark exists.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Which held-out tasks should supply calibration labels? — Status:
  DEFERRED | Why it matters: public calibration claims need frozen task-specific
  correctness definitions and gold labels, likely in the prompt_eval-backed
  suite.
