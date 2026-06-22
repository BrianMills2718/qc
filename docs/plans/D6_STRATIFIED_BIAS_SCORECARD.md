# Plan #113: D6 Stratified Bias Scorecard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 evaluation harness
**Blocks:** INV-5 bias-surfacing evidence workflow

---

## Gap

**Current:** Phase 0 can score externally supplied D6 counterfactual
identity-swap outcomes through `BIAS_COUNTERFACTUAL=...`, but INV-5 also
requires stratified error diagnostics where respondent attributes are available
and ethically permissible. There is no `make bench` surface for externally
supplied correctness/error rows grouped by respondent attribute.

**Target:** Add a local D6 stratified-bias scorecard substrate:

- `ProjectState.config.extra["bias_stratified_evaluations"]`
- `make bench ID=<project> BIAS_STRATIFIED=bias_stratified.json`
- `scripts/bench_phase0.py --bias-stratified-file bias_stratified.json`
- Phase 0 scorecard section `bias_stratified_d6`
- Phase 0 input hashes, command provenance, and benchmark package manifest
  support for the new file.
- Score externally supplied rows containing `case_id`, `attribute`, `group`,
  `correct`, optional `surface`, `evaluator`, `error_type`, and `notes`.
- Report total rows, correct/incorrect counts, accuracy/error rates with Wilson
  intervals, per-attribute/per-group summaries, per-surface summaries, and
  per-attribute max error-rate gaps.

**Why:** Systematic LLM coding bias can appear as different error rates across
respondent groups even when aggregate reliability looks good. This adds the
missing local accounting substrate for stratified error parity while preserving
the claim discipline that populated, ethically designed bias audits are still
future work.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D6 target includes counterfactual swaps and
  stratified error parity.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-5 is currently UNMET and warns that
  bias audits are unpopulated.
- `qc_clean/core/bench.py` - current D6 counterfactual scorecard pattern and
  Phase 0 scorecard assembly.
- `scripts/bench_phase0.py` - external file loaders, input hashes, and artifact
  provenance.
- `scripts/run_phase0_benchmark_package.py` - Phase 0 package manifest path
  routing.
- `tests/test_bench_phase0.py` and `tests/test_bench_phase0_script.py` -
  current D6 counterfactual tests and external-file non-mutation pattern.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is local accounting
infrastructure for a bias metric already specified in the evaluation harness.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `bias_stratified_scorecard` | externally supplied stratified correctness rows | D6 stratified scorecard section | qualitative_coding | agents/operators evaluating INV-5 | free |

### Capability Validation

- [ ] Missing stratified rows report `not_available` with no bias-free claim.
- [ ] Valid rows produce overall accuracy/error rates and Wilson intervals.
- [ ] Per-attribute/per-group summaries report group rates and max error-rate gaps.
- [ ] Per-surface summaries report rates.
- [ ] Invalid metadata fails loud.
- [ ] CLI/Make/package inputs load without mutating saved project state.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `scripts/run_phase0_benchmark_package.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `tests/test_phase0_benchmark_package.py` (modify if package manifest hashes need expectation updates)
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

1. Add TDD tests for unavailable, scored, invalid metadata, external file
   loading/non-mutation, and package manifest routing.
2. Add `BiasStratifiedEvaluation` and `bias_stratified_scorecard`.
3. Wire `bias_stratified_d6` into `phase0_scorecard`.
4. Add `--bias-stratified-file`, `BIAS_STRATIFIED=`, input hashes, command
   provenance, and package manifest support.
5. Update docs with the measurement-substrate caveat.
6. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_reports_bias_stratified_unavailable_without_eval_data` | Missing stratified rows do not imply no bias. |
| `tests/test_bench_phase0.py` | `test_scorecard_scores_bias_stratified_outcomes` | Overall/group/surface rates, Wilson intervals, and gaps are computed. |
| `tests/test_bench_phase0.py` | `test_scorecard_invalid_bias_stratified_metadata_fails_loud` | Invalid row/config shape fails loud. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_bias_stratified_from_file_without_mutating_state` | External file loads in memory and input hash is recorded. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_invalid_bias_stratified_file_fails_loud` | Bad external file exits non-zero with JSON error. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_phase0_benchmark_package.py` | Phase 0 scorecard/package surfaces remain consistent. |
| `make -n bench ID=project BIAS_STRATIFIED=bias.json` | Make target forwards the new file. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `phase0_scorecard` includes `bias_stratified_d6`.
- [ ] Missing data returns `not_available` and explicitly refuses bias-free
  inference.
- [ ] Valid rows produce overall, group, attribute-gap, and surface summaries.
- [ ] Wilson intervals are included for accuracy/error rates.
- [ ] `make bench ... BIAS_STRATIFIED=...` and `--bias-stratified-file` load
  external rows without mutating project state.
- [ ] Phase 0 input hashes, command provenance, and package manifest support
  include the new file.
- [ ] Docs state this is local accounting only, not causal proof, bias-free
  evidence, or a populated bias audit.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should this scorecard enforce a minimum group size threshold? — Status:
  DEFERRED | Why it matters: small groups can make disparity estimates unstable.
  This slice reports Wilson intervals and raw counts; policy thresholds should
  be pre-registered in a populated benchmark protocol.

---

## Notes

This is a measurement substrate. It does not generate protected attributes,
decide ethical permissibility, prove causation, or show that the system is
unbiased.
