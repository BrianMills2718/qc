# Plan #116: D6 Bias Scorecard Preflight Guard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #115 D6 bias protocol result preflight
**Blocks:** Guarded D6 benchmark scoring and populated INV-5 bias-audit workflow

---

## Gap

**Current:** `make d6-bias-preflight` can check D6 stratified/counterfactual
result files against a registered protocol, and `make bench` can score those
same files through `BIAS_STRATIFIED=...` and `BIAS_COUNTERFACTUAL=...`. The
guard is not integrated into scoring: an operator can supply a protocol and
still get a scorecard even when the D6 files do not match the protocol.

**Target:** Add optional score-time D6 preflight enforcement:

- `scripts/bench_phase0.py --d6-bias-protocol-file protocol.json`
- `make bench ... D6_PROTOCOL=protocol.json`
- When a D6 protocol is supplied, bench loads the protocol and the supplied D6
  result files, runs `preflight_d6_bias_payloads`, and blocks scoring/output/
  artifact writes if preflight fails.
- Passing guarded scorecards include `_meta.preflight_reports.d6_bias`.
- Phase 0 input hashes and command provenance include the protocol file.
- Package manifests can include `d6_bias_protocol_file`.
- Docs state the guard enforces protocol/result provenance only, not bias
  evidence.

**Why:** Standalone preflight is useful, but score-time enforcement is the point
where provenance mistakes should fail loud. This prevents protocol-mismatched
D6 files from producing an apparently valid scorecard.

---

## References Reviewed

- `qc_clean/core/d6_bias_preflight.py` - D6 protocol/result preflight.
- `scripts/preflight_d6_bias_protocol.py` - standalone preflight CLI.
- `scripts/bench_phase0.py` - Phase 0 external-file loading, input hashes,
  command provenance, output/artifact write order.
- `scripts/run_phase0_benchmark_package.py` - Phase 0 package manifest routing.
- `tests/test_d7_comparison_guard.py` - score-time preflight guard pattern for
  D7 comparison scoring.
- `tests/test_bench_phase0_script.py` and `tests/test_phase0_benchmark_package.py`
  - Phase 0 external-file non-mutation and package routing patterns.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This is guard integration for the D6 protocol and
preflight infrastructure already implemented.

---

## Capabilities

Internal guarded-scoring capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `bench_phase0_d6_protocol_guard` | D6 protocol + D6 result files | scorecard or JSON error | qualitative_coding | agents/operators scoring D6 inputs | free |

### Capability Validation

- [ ] Passing protocol/result preflight lets `bench_phase0` score D6 rows.
- [ ] Passing guarded scorecards include `_meta.preflight_reports.d6_bias`.
- [ ] Failing protocol/result preflight returns non-zero JSON error and writes
  no scorecard/output/artifact files.
- [ ] Input hashes, command provenance, and package manifests include the D6
  protocol file.
- [ ] `make bench D6_PROTOCOL=...` forwards the guard flag.

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
2. Add `--d6-bias-protocol-file` to `bench_phase0`.
3. Run D6 preflight after D6 external files are loaded but before scorecard
   generation/output/artifact writes.
4. Include successful preflight report in `_meta.preflight_reports.d6_bias`.
5. Add input hash, command provenance, package manifest, Make, and docs wiring.
6. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New / Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d6_protocol_guard_allows_matching_inputs` | Passing guard scores D6 and includes preflight report. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d6_protocol_guard_blocks_mismatched_inputs_without_output` | Failed guard exits non-zero and writes no output. |
| `tests/test_phase0_benchmark_package.py` | existing package routing test update | Package manifest can forward `d6_bias_protocol_file`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py -q` | Phase 0 guard and package behavior. |
| `python -m ruff check scripts/bench_phase0.py scripts/run_phase0_benchmark_package.py tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py` | Focused lint on touched files. |
| `make -n bench ID=project D6_PROTOCOL=protocol.json BIAS_STRATIFIED=bias_stratified.json BIAS_COUNTERFACTUAL=bias_counterfactual.json` | Make target forwards the new protocol guard. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `bench_phase0` accepts `--d6-bias-protocol-file`.
- [ ] `make bench` accepts `D6_PROTOCOL=...`.
- [ ] Phase 0 package manifests accept `d6_bias_protocol_file`.
- [ ] Passing guarded D6 scorecards include `_meta.preflight_reports.d6_bias`.
- [ ] Failed D6 preflight blocks scoring and output/artifact writes.
- [ ] Protocol file hash and command provenance are recorded.
- [ ] Docs state this is a provenance guard only, not bias evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should `D6_PROTOCOL` become required whenever D6 external files are
  supplied? — Status: DEFERRED | This slice makes the guard opt-in so existing
  Phase 0 local accounting remains compatible. A later policy plan can decide
  whether populated benchmark packages must require it.

---

## Notes

This is a score-time provenance guard. It does not create result rows, run
models, validate label correctness, prove causation, or show that the system is
unbiased.
