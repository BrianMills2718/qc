# Plan #125: D9 Interpretive Preference Scorecard Preflight Guard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #124 D9 interpretive-preference protocol/result preflight
**Blocks:** Populated blind expert D9 preference workflow

---

## Gap

**Current:** D9 protocol/result pairs can be checked with
`make d9-interpretive-preference-preflight PROTOCOL=protocol.json
PREFERENCE=preference.json`, and `make bench PREFERENCE=preference.json` can
score externally supplied D9 forced-choice rows. The scorecard path does not
yet enforce the D9 preflight when a protocol is supplied.

**Target:** Add a score-time guard for D9:

- `scripts/bench_phase0.py --d9-interpretive-preference-protocol-file protocol.json`.
- `make bench D9_PROTOCOL=protocol.json PREFERENCE=preference.json`.
- `Phase0BenchmarkPackage.d9_interpretive_preference_protocol_file` support.
- Scorecards include `_meta.preflight_reports.d9_interpretive_preference` when
  the guard passes.
- `_meta.input_hashes`, command metadata, and artifact manifests include the
  D9 protocol file hash/path.
- Failed preflight returns machine-readable JSON and blocks scorecard/output
  file/artifact writes.
- When `D9_PROTOCOL=...` is supplied, the validated protocol is the
  authoritative in-memory source for D9 non-inferiority margin metadata in the
  scorecard; no saved project state is mutated.
- Docs updated to clarify this is score-time provenance only, not blind
  expert-parity evidence, interpretive-depth evidence,
  methodological-validity evidence, or SOTA evidence.

**Why:** Result-file preflight is useful only if the score boundary can enforce
it. D9 also differs from D4/D8 because the scorecard can assess
non-inferiority only when protocol margin metadata is available; the guarded
protocol should provide that metadata for the run instead of requiring
duplicated metadata inside the result file.

---

## References Reviewed

- `scripts/bench_phase0.py` - D4/D6/D8 score-time guard patterns, input hashes,
  command metadata, and artifact manifest plumbing.
- `scripts/run_phase0_benchmark_package.py` - package-manifest path flag
  mapping and Pydantic model.
- `qc_clean/core/d9_interpretive_preference_preflight.py` - D9 protocol/result
  preflight.
- `qc_clean/core/bench.py` - D9 scorecard protocol metadata loader and
  non-inferiority assessment.
- `tests/test_bench_phase0_script.py` - D4/D6/D8 guard tests and D9 scorecard
  file tests.
- `tests/test_phase0_benchmark_package.py` - package manifest path/hash tests.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.
- Coordination claims: no active claim files found under
  `~/.claude/coordination/claims/` before this plan.

---

## Research Basis For This Slice

No new external research. This follows the existing D4/D6/D8 score-time guard
pattern and the evaluation harness rule that D9 parity is non-inferiority
against a pre-registered margin.

---

## Capabilities

Internal score-boundary guard only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `guard_d9_interpretive_preference_scorecard_preflight` | D9 protocol JSON + D9 preference JSON + project state | Phase 0 scorecard or JSON failure | qualitative_coding | agents/operators running benchmark packages | free |

### Capability Validation

- [ ] `make bench D9_PROTOCOL=... PREFERENCE=...` runs D9 preflight before
  scorecard generation.
- [ ] Passing guarded scorecards include
  `_meta.preflight_reports.d9_interpretive_preference`.
- [ ] Passing guarded scorecards use the supplied protocol metadata for D9
  non-inferiority assessment.
- [ ] Protocol file SHA-256 is included in `_meta.input_hashes`.
- [ ] Command metadata and artifact manifests include the protocol path.
- [ ] Mismatched D9 protocol/result inputs return JSON failure and do not write
  `--output` or `--artifact-dir` artifacts.
- [ ] Package manifests can pass
  `d9_interpretive_preference_protocol_file` through to the canonical bench
  path.

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

1. Write TDD tests for D9 score-time guard pass/fail, protocol metadata
   injection into the D9 scorecard, and package-manifest propagation.
2. Add D9 protocol CLI flag, loader, preflight call, and report insertion.
3. Add D9 protocol file to input hashes, command metadata, artifact manifests,
   and package runner.
4. Add `D9_PROTOCOL` to `make bench`.
5. Update docs with a score-time-guard-only caveat.
6. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d9_protocol_guard_allows_matching_inputs` | Passing D9 guard scores rows, includes preflight report, hashes protocol/result, uses protocol margin metadata, and does not mutate state. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d9_protocol_guard_blocks_mismatched_inputs_without_output` | Failing D9 guard returns JSON failure and writes no output/artifacts. |
| `tests/test_phase0_benchmark_package.py` | existing package path/hash test | Package manifests can include `d9_interpretive_preference_protocol_file` and route it to `bench_phase0`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py tests/test_d9_interpretive_preference_preflight.py -q` | D9 guard, package runner, and preflight behavior. |
| `python -m ruff check scripts/bench_phase0.py scripts/run_phase0_benchmark_package.py tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py` | Focused lint on modified guard/package surfaces. |
| `make -n bench ID=project D9_PROTOCOL=protocol.json PREFERENCE=preference.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] D9 protocol/result preflight can be enforced at `make bench` score time.
- [ ] Passing guarded scorecards include a D9 preflight report in `_meta`.
- [ ] Passing guarded scorecards use the supplied protocol margin metadata for
  D9 non-inferiority assessment without mutating saved project state.
- [ ] Failing guarded runs block scorecard/output/artifact writes.
- [ ] D9 protocol file hashes/paths are carried through scorecards, manifests,
  and package runner command mapping.
- [ ] Docs state the guard is process/provenance only.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [x] Should the score-time guard inject protocol metadata into D9
  non-inferiority assessment when result files omit embedded protocol metadata?
  — Status: DECIDED | Yes. When `D9_PROTOCOL=...` is supplied, use the
  validated protocol file as the authoritative in-memory source for
  `protocol_id`, `non_inferiority_margin`, and
  `registered_before_evaluation`.

---

## Notes

This plan creates a score-time guard. It does not create preference cases,
blind evaluators, collect expert ratings, validate preference labels beyond
schema/protocol consistency, prove interpretive-depth parity, prove
methodological validity, or license a SOTA claim.
