# Plan #122: D8 GT Fidelity Scorecard Preflight Guard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #121 D8 GT-fidelity protocol/result preflight
**Blocks:** Populated expert GT-fidelity evaluation workflow

---

## Gap

**Current:** D8 protocol/result pairs can be checked with
`make d8-gt-fidelity-preflight PROTOCOL=protocol.json
GT_FIDELITY=gt_fidelity.json`, and `make bench GT_FIDELITY=gt_fidelity.json`
can score externally supplied D8 rubric rows. The scorecard path does not yet
enforce the D8 preflight when a protocol is supplied.

**Target:** Add a score-time guard for D8:

- `scripts/bench_phase0.py --d8-gt-fidelity-protocol-file protocol.json`.
- `make bench D8_PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json`.
- `Phase0BenchmarkPackage.d8_gt_fidelity_protocol_file` support.
- Scorecards include `_meta.preflight_reports.d8_gt_fidelity` when the guard
  passes.
- `_meta.input_hashes`, command metadata, and artifact manifests include the
  D8 protocol file hash/path.
- Failed preflight returns machine-readable JSON and blocks scorecard/output
  file/artifact writes.
- Docs updated to clarify this is score-time provenance only, not
  expert-rubric acceptance, methodological-saturation evidence, full
  grounded-theory evidence, or SOTA evidence.

**Why:** Result-file preflight is useful only if the score boundary can enforce
it. This closes the D8 protocol → result → scorecard provenance chain without
claiming populated expert evidence.

---

## References Reviewed

- `scripts/bench_phase0.py` - D4/D6 score-time guard patterns, input hashes,
  command metadata, and artifact manifest plumbing.
- `scripts/run_phase0_benchmark_package.py` - package-manifest path flag
  mapping and Pydantic model.
- `qc_clean/core/d8_gt_fidelity_preflight.py` - D8 protocol/result preflight.
- `tests/test_bench_phase0_script.py` - D4/D6 guard tests and D8 scorecard
  file tests.
- `tests/test_phase0_benchmark_package.py` - package manifest path/hash tests.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This follows the existing D4/D6 guard pattern.

---

## Capabilities

Internal score-boundary guard only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `guard_d8_gt_fidelity_scorecard_preflight` | D8 protocol JSON + D8 result JSON + project state | Phase 0 scorecard or JSON failure | qualitative_coding | agents/operators running benchmark packages | free |

### Capability Validation

- [x] `make bench D8_PROTOCOL=... GT_FIDELITY=...` runs D8 preflight before
  scorecard generation.
- [x] Passing guarded scorecards include
  `_meta.preflight_reports.d8_gt_fidelity`.
- [x] Protocol file SHA-256 is included in `_meta.input_hashes`.
- [x] Command metadata and artifact manifests include the protocol path.
- [x] Mismatched D8 protocol/result inputs return JSON failure and do not write
  `--output` or `--artifact-dir` artifacts.
- [x] Package manifests can pass `d8_gt_fidelity_protocol_file` through to the
  canonical bench path.

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

1. Write TDD tests for D8 score-time guard pass/fail and package-manifest
   propagation.
2. Add D8 protocol CLI flag, loader, preflight call, and report insertion.
3. Add D8 protocol file to input hashes, command metadata, artifact manifests,
   and package runner.
4. Add `D8_PROTOCOL` to `make bench`.
5. Update docs with a score-time-guard-only caveat.
6. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d8_protocol_guard_allows_matching_inputs` | Passing D8 guard scores rows, includes preflight report, hashes protocol/result, and does not mutate state. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d8_protocol_guard_blocks_mismatched_inputs_without_output` | Failing D8 guard returns JSON failure and writes no output/artifacts. |
| `tests/test_phase0_benchmark_package.py` | existing package path/hash test | Package manifests can include `d8_gt_fidelity_protocol_file` and route it to `bench_phase0`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py tests/test_d8_gt_fidelity_preflight.py -q` | D8 guard, package runner, and preflight behavior. |
| `python -m ruff check scripts/bench_phase0.py scripts/run_phase0_benchmark_package.py tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py` | Focused lint on modified guard/package surfaces. |
| `make -n bench ID=project D8_PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] D8 protocol/result preflight can be enforced at `make bench` score time.
- [x] Passing guarded scorecards include a D8 preflight report in `_meta`.
- [x] Failing guarded runs block scorecard/output/artifact writes.
- [x] D8 protocol file hashes/paths are carried through scorecards, manifests,
  and package runner command mapping.
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

- [ ] Which lane follows D8 guard? — Status: DEFERRED | Likely D9 protocol
  package or confidence-calibration protocol package, selected after this guard
  lands.

---

## Outcome

Implemented in `d196f02`
(`[Plan: D8_GT_FIDELITY_SCORECARD_PREFLIGHT_GUARD] Add D8 score-time guard`).
`scripts/bench_phase0.py` now accepts
`--d8-gt-fidelity-protocol-file`; `make bench` exposes it as
`D8_PROTOCOL=...`; and strict Phase 0 package manifests can carry
`d8_gt_fidelity_protocol_file`. Passing guarded runs include
`_meta.preflight_reports.d8_gt_fidelity`, protocol/result input hashes, and
command provenance. Failing preflights emit machine-readable JSON and return
before scorecard, output file, or artifact writes.

Verification evidence:

- TDD red before implementation: focused tests failed on missing
  `d8_gt_fidelity_protocol_file_sha256`, missing
  `--d8-gt-fidelity-protocol-file`, and strict package-manifest rejection of
  `d8_gt_fidelity_protocol_file`.
- `python -m pytest tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py tests/test_d8_gt_fidelity_preflight.py -q`
  - 46 passed.
- `python -m ruff check scripts/bench_phase0.py scripts/run_phase0_benchmark_package.py tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py`
  - all checks passed.
- `make -n bench ID=project D8_PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json`
  - routed to `scripts/bench_phase0.py --d8-gt-fidelity-protocol-file protocol.json --gt-fidelity-file gt_fidelity.json`.
- `make docs-check` - passed.
- `make check` - 987 passed, 1 skipped, 8 deselected; Ruff and docs checks
  passed; type check is not yet configured.

## Notes

This plan creates a score-time guard. It does not collect expert ratings, run
LLM judges, validate rubric labels beyond schema/protocol consistency, prove
methodological saturation, prove full grounded theory, or license a SOTA claim.
