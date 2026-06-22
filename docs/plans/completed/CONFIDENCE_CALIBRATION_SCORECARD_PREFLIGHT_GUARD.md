# Plan #128: Confidence Calibration Scorecard Preflight Guard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #127 Confidence calibration protocol result preflight
**Blocks:** Populated held-out confidence-calibration benchmark

---

## Gap

**Current:** Confidence-calibration protocol/result pairs can be checked with
`make confidence-calibration-preflight PROTOCOL=protocol.json
CALIBRATION=calibration.json`, and `make bench CALIBRATION=calibration.json`
can score externally supplied confidence/correctness rows. The scorecard path
does not yet enforce that preflight when a protocol is supplied.

**Target:** Add a score-time guard for confidence calibration:

- `scripts/bench_phase0.py --confidence-calibration-protocol-file protocol.json`.
- `make bench CONFIDENCE_PROTOCOL=protocol.json CALIBRATION=calibration.json`.
- `Phase0BenchmarkPackage.confidence_calibration_protocol_file` support.
- Scorecards include `_meta.preflight_reports.confidence_calibration` when the
  guard passes.
- `_meta.input_hashes`, command metadata, and artifact manifests include the
  calibration protocol file hash/path.
- Failed preflight returns machine-readable JSON and blocks scorecard/output
  file/artifact writes.
- Docs updated to clarify this is score-time provenance only, not calibration
  proof, held-out correctness evidence, methodological-validity evidence, or
  SOTA evidence.

**Why:** Standalone preflight is useful, but the score boundary must be able to
require it so result files cannot drift from registered protocols before being
reported. This follows the D4/D6/D8/D9 guard pattern and keeps calibration
claims disciplined until populated held-out labels exist.

---

## References Reviewed

- `scripts/bench_phase0.py` - D4/D6/D8/D9 score-time guard patterns, input
  hashes, command metadata, and artifact manifest plumbing.
- `scripts/run_phase0_benchmark_package.py` - package-manifest path flag
  mapping and Pydantic model.
- `qc_clean/core/confidence_calibration_preflight.py` - protocol/result
  preflight added in Plan #127.
- `qc_clean/core/confidence_calibration_protocol.py` - protocol package
  validator and field semantics.
- `qc_clean/core/bench.py` - `ConfidenceCalibrationEvaluation` and scorecard
  row validation semantics.
- `tests/test_bench_phase0_script.py` - D4/D6/D8/D9 guard tests and existing
  calibration scorecard file tests.
- `tests/test_phase0_benchmark_package.py` - package manifest path/hash tests.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.
- Coordination claims: no active claim files were present under
  `~/.claude/coordination/claims/` earlier in this long-running sprint; no new
  conflicting local changes are present at plan start.

---

## Research Basis For This Slice

No new external research. This is deterministic score-boundary provenance
plumbing for already implemented confidence-calibration protocol/result
preflight and local scorecard metrics.

---

## Capabilities

Internal score-boundary guard only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `guard_confidence_calibration_scorecard_preflight` | Confidence-calibration protocol JSON + calibration result JSON + project state | Phase 0 scorecard or JSON failure | qualitative_coding | agents/operators running benchmark packages | free |

### Capability Validation

- [x] `make bench CONFIDENCE_PROTOCOL=... CALIBRATION=...` runs
  confidence-calibration preflight before scorecard generation.
- [x] Passing guarded scorecards include
  `_meta.preflight_reports.confidence_calibration`.
- [x] Protocol file SHA-256 is included in `_meta.input_hashes`.
- [x] Command metadata and artifact manifests include the protocol path.
- [x] Mismatched protocol/result inputs return JSON failure and do not write
  `--output` or `--artifact-dir` artifacts.
- [x] Package manifests can pass `confidence_calibration_protocol_file` through
  to the canonical bench path.

---

## Files Affected

- `scripts/bench_phase0.py` (modify)
- `scripts/run_phase0_benchmark_package.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `tests/test_phase0_benchmark_package.py` (modify)
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

1. Write TDD tests for confidence-calibration score-time guard pass/fail and
   package-manifest propagation.
2. Add the calibration protocol CLI flag, loader, preflight call, and report
   insertion.
3. Add calibration protocol file to input hashes, command metadata, artifact
   manifests, and package runner.
4. Add `CONFIDENCE_PROTOCOL` to `make bench`.
5. Update docs with a score-time-guard-only caveat.
6. Run focused tests, focused Ruff, Make dry-run, docs checks, and full
   `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_confidence_calibration_protocol_guard_allows_matching_inputs` | Passing guard scores rows, includes preflight report, hashes protocol/result, and does not mutate state. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_confidence_calibration_protocol_guard_blocks_mismatched_inputs_without_output` | Failing guard returns JSON failure and writes no output/artifacts. |
| `tests/test_phase0_benchmark_package.py` | existing package path/hash test | Package manifests can include `confidence_calibration_protocol_file` and route it to `bench_phase0`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py tests/test_confidence_calibration_preflight.py -q` | Calibration guard, package runner, and preflight behavior. |
| `python -m ruff check scripts/bench_phase0.py scripts/run_phase0_benchmark_package.py tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py` | Focused lint on modified guard/package surfaces. |
| `make -n bench ID=project CONFIDENCE_PROTOCOL=protocol.json CALIBRATION=calibration.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Confidence-calibration protocol/result preflight can be enforced at
  `make bench` score time.
- [x] Passing guarded scorecards include a confidence-calibration preflight
  report in `_meta`.
- [x] Failing guarded runs block scorecard/output/artifact writes.
- [x] Confidence-calibration protocol file hashes/paths are carried through
  scorecards, manifests, and package runner command mapping.
- [x] Docs state the guard is process/provenance only.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] What Make variable should expose the protocol file?
  — Status: DECIDED | Use `CONFIDENCE_PROTOCOL` to avoid confusion with the
  existing `CALIBRATION` result-file variable while staying concise in
  `make bench`.

---

## Outcome

Implemented in `a84ea44`
(`[Plan: CONFIDENCE_CALIBRATION_SCORECARD_PREFLIGHT_GUARD] Add score-time guard`),
with documentation status follow-ups in `fdcf80c` and `ce136a8`.
`scripts/bench_phase0.py` now accepts
`--confidence-calibration-protocol-file`; `make bench` exposes it as
`CONFIDENCE_PROTOCOL=...`; and strict Phase 0 package manifests can carry
`confidence_calibration_protocol_file`. Passing guarded runs include
`_meta.preflight_reports.confidence_calibration`, protocol/result input hashes,
command provenance, and artifact-manifest provenance. Failing preflights emit
machine-readable JSON and return before scorecard, output file, or artifact
writes.

Verification evidence:

- TDD red before implementation: focused tests failed on unrecognized
  `--confidence-calibration-protocol-file` and strict package-manifest
  rejection of `confidence_calibration_protocol_file` (4 failed, 45 passed).
- `python -m pytest tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py tests/test_confidence_calibration_preflight.py -q`
  passed: 49 passed.
- `python -m ruff check scripts/bench_phase0.py scripts/run_phase0_benchmark_package.py tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py`
  passed.
- `make -n bench ID=project CONFIDENCE_PROTOCOL=protocol.json CALIBRATION=calibration.json`
  routed to `scripts/bench_phase0.py --confidence-calibration-protocol-file protocol.json --confidence-calibration-file calibration.json`.
- `make docs-check` passed.
- `make check` passed: 1014 passed, 1 skipped, 8 deselected; Ruff passed;
  docs-check passed.
- Type check is not configured in this repo.
- Implementation and documentation commits were pushed to `origin/main`.

---

## Notes

This plan creates a score-time guard. It does not create calibration items,
collect correctness labels, validate label correctness beyond schema/protocol
consistency, prove confidence calibration, prove methodological validity, or
license a SOTA claim.
