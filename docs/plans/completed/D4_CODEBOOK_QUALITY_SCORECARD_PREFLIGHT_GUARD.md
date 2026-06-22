# Plan #119: D4 Codebook Quality Scorecard Preflight Guard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #118 D4 codebook quality protocol result preflight
**Blocks:** Guarded D4 benchmark scoring and populated D4 blind expert /
LLM-judge evaluation workflow

---

## Outcome

Implemented and verified optional D4 score-time preflight enforcement.
`bench_phase0` now accepts `--d4-codebook-quality-protocol-file`, `make bench`
forwards `D4_PROTOCOL=...`, and Phase 0 benchmark package manifests accept
`d4_codebook_quality_protocol_file`. When a protocol is supplied, bench runs
D4 protocol/result preflight before scorecard generation and before
output/artifact writes. Failed preflight returns a JSON error with the
preflight report and writes no scorecard/artifact files. Passing guarded
scorecards include `_meta.preflight_reports.d4_codebook_quality`, and input
hashes/command provenance include the D4 protocol file.

Verification evidence:

- TDD red: targeted bench/package tests initially failed because
  `--d4-codebook-quality-protocol-file`,
  `d4_codebook_quality_protocol_file`, and the protocol hash key were not
  supported.
- Focused tests: `python -m pytest tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py -q`
  passed (`38 passed`).
- Focused Ruff:
  `python -m ruff check scripts/bench_phase0.py scripts/run_phase0_benchmark_package.py tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py`
  passed.
- Make dry-run:
  `make -n bench ID=project D4_PROTOCOL=protocol.json CODEBOOK_QUALITY=quality.json`
  forwarded `--d4-codebook-quality-protocol-file`.
- Docs gate: `make docs-check` passed.
- Full gate: `make check` passed (`973 passed, 1 skipped, 8 deselected`;
  Ruff and docs checks clean; type check not configured).
- Implementation commit pushed: `8c2ea30`
  `[Plan: D4_CODEBOOK_QUALITY_SCORECARD_PREFLIGHT_GUARD] Add D4 score guard`.

---

## Gap

**Current:** `make d4-codebook-quality-preflight` can check a D4 rubric result
file against a registered protocol, and `make bench CODEBOOK_QUALITY=...` can
score that same result file. The guard is not integrated into scorecard
generation: an operator can supply a protocol/result pair that fails preflight
and still produce a D4 scorecard if they run bench without a guard.

**Target:** Add optional score-time D4 preflight enforcement:

- `scripts/bench_phase0.py --d4-codebook-quality-protocol-file protocol.json`
- `make bench ... D4_PROTOCOL=protocol.json CODEBOOK_QUALITY=quality.json`
- When a D4 protocol is supplied, bench loads the protocol and D4 quality
  result file, runs `preflight_d4_codebook_quality_payloads`, and blocks
  scoring/output/artifact writes if preflight fails.
- Passing guarded scorecards include
  `_meta.preflight_reports.d4_codebook_quality`.
- Phase 0 input hashes and command provenance include the D4 protocol file.
- Package manifests can include `d4_codebook_quality_protocol_file`.
- Docs state the guard enforces protocol/result provenance only, not codebook
  quality evidence.

**Why:** Standalone preflight is useful, but score-time enforcement is the point
where provenance mistakes should fail loud. This prevents protocol-mismatched
D4 files from producing an apparently valid codebook-quality scorecard.

---

## References Reviewed

- `qc_clean/core/d4_codebook_quality_preflight.py` - D4 protocol/result
  preflight.
- `scripts/preflight_d4_codebook_quality_protocol.py` - standalone preflight
  CLI.
- `scripts/bench_phase0.py` - Phase 0 external-file loading, input hashes,
  command provenance, output/artifact write order.
- `scripts/run_phase0_benchmark_package.py` - Phase 0 package manifest routing.
- `docs/plans/completed/D6_BIAS_SCORECARD_PREFLIGHT_GUARD.md` - analogous
  guard plan and acceptance criteria.
- `tests/test_bench_phase0_script.py` and `tests/test_phase0_benchmark_package.py`
  - Phase 0 external-file non-mutation and package routing patterns.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This is guard integration for the D4 protocol and
preflight infrastructure already implemented.

---

## Capabilities

Internal guarded-scoring capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `bench_phase0_d4_protocol_guard` | D4 protocol + D4 result file | scorecard or JSON error | qualitative_coding | agents/operators scoring D4 inputs | free |

### Capability Validation

- [x] Passing protocol/result preflight lets `bench_phase0` score D4 rows.
- [x] Passing guarded scorecards include
  `_meta.preflight_reports.d4_codebook_quality`.
- [x] Failing protocol/result preflight returns non-zero JSON error and writes
  no scorecard/output/artifact files.
- [x] Input hashes, command provenance, and package manifests include the D4
  protocol file.
- [x] `make bench D4_PROTOCOL=...` forwards the guard flag.

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

1. Write TDD tests for passing guarded bench, failing guarded bench with no
   output write, package manifest forwarding, and Make dry-run forwarding.
2. Add `--d4-codebook-quality-protocol-file` to `bench_phase0`.
3. Run D4 preflight after D4 quality result file loading but before scorecard
   generation/output/artifact writes.
4. Include successful preflight report in
   `_meta.preflight_reports.d4_codebook_quality`.
5. Add input hash, command provenance, package manifest, Make, and docs wiring.
6. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New / Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d4_protocol_guard_allows_matching_inputs` | Passing guard scores D4 and includes preflight report. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d4_protocol_guard_blocks_mismatched_inputs_without_output` | Failed guard exits non-zero and writes no output. |
| `tests/test_phase0_benchmark_package.py` | existing package routing test update | Package manifest can forward `d4_codebook_quality_protocol_file`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py -q` | Phase 0 guard and package behavior. |
| `python -m ruff check scripts/bench_phase0.py scripts/run_phase0_benchmark_package.py tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py` | Focused lint on touched files. |
| `make -n bench ID=project D4_PROTOCOL=protocol.json CODEBOOK_QUALITY=quality.json` | Make target forwards the new protocol guard. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `bench_phase0` accepts `--d4-codebook-quality-protocol-file`.
- [x] `make bench` accepts `D4_PROTOCOL=...`.
- [x] Phase 0 package manifests accept `d4_codebook_quality_protocol_file`.
- [x] Passing guarded D4 scorecards include
  `_meta.preflight_reports.d4_codebook_quality`.
- [x] Failed D4 preflight blocks scoring and output/artifact writes.
- [x] Protocol file hash and command provenance are recorded.
- [x] Docs state this is a provenance guard only, not codebook-quality evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should `D4_PROTOCOL` become required whenever D4 external files are
  supplied? — Status: DEFERRED | This slice makes the guard opt-in so existing
  Phase 0 local accounting remains compatible. A later policy plan can decide
  whether populated benchmark packages must require it.

---

## Notes

This is a score-time provenance guard. It does not create result rows, run LLM
judges, collect expert ratings, validate rubric correctness, prove codebook
quality, or license a SOTA claim.
