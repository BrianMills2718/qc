# Plan #115: D6 Bias Protocol Result Preflight

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #114 D6 bias protocol package
**Blocks:** Guarded D6 benchmark scoring and populated INV-5 bias-audit workflow

---

## Gap

**Current:** D6 bias-audit protocols can be validated with
`make validate-d6-bias-protocol`, and Phase 0 can score externally supplied
counterfactual (`BIAS_COUNTERFACTUAL=...`) and stratified
(`BIAS_STRATIFIED=...`) rows. There is still no preflight that binds a validated
D6 protocol to concrete result files before scoring. A user can accidentally
score rows from the wrong case set, wrong attribute strategy, wrong surface, or
wrong file hash.

**Target:** Add a deterministic D6 protocol/result preflight:

- New `qc_clean/core/d6_bias_preflight.py`.
- New `scripts/preflight_d6_bias_protocol.py`.
- New `make d6-bias-preflight PROTOCOL=protocol.json
  [STRATIFIED=bias_stratified.json] [COUNTERFACTUAL=bias_counterfactual.json]`.
- The preflight validates the D6 protocol, validates supplied result rows using
  the same D6 row schemas as Phase 0, requires result files for configured
  dimensions, rejects unexpected result files for unconfigured dimensions,
  checks protocol file-hash locks when present, checks stratified attributes and
  surfaces against the registered strategy, and reports machine-readable
  pass/fail status with errors.
- Docs updated to clarify this is package-matching provenance only, not a
  populated bias audit, causal proof, or bias-free evidence.

**Why:** Protocol validation alone records intent; result preflight checks that
the concrete files about to be scored still match that intent. This narrows the
most likely D6 provenance failure without claiming that labels are correct or
that the system is unbiased.

---

## References Reviewed

- `qc_clean/core/d6_bias_protocol.py` - D6 protocol package contract.
- `qc_clean/core/bench.py` - D6 counterfactual and stratified row schemas and
  scorecard loaders.
- `qc_clean/core/inv7_live_preflight.py` - protocol/result preflight report
  pattern.
- `qc_clean/core/d7_comparison_preflight.py` - protocol/gold/prediction
  preflight checks and file-hash lock pattern.
- `scripts/preflight_inv7_live_package.py` and `scripts/preflight_d7_comparison.py`
  - machine-readable preflight CLI pattern.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This is a deterministic provenance/preflight layer
for the D6 protocol and scorecard substrates already implemented.

---

## Capabilities

Internal preflight capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `preflight_d6_bias_payloads` | D6 protocol JSON + optional stratified/counterfactual result JSON | D6 preflight report | qualitative_coding | agents/operators preparing D6 scorecard inputs | free |

### Capability Validation

- [ ] Valid protocol + matching result files returns `status="pass"`.
- [ ] Missing required result files fail for configured dimensions.
- [ ] Unexpected result files fail for unconfigured dimensions.
- [ ] Result-file SHA-256 locks fail on mismatch when protocol hashes are set.
- [ ] Stratified rows reject unexpected/missing attributes and surfaces against
  the protocol strategy.
- [ ] Counterfactual rows validate shape and reject unexpected attributes.
- [ ] CLI emits machine-readable JSON and returns non-zero on failed preflight.

---

## Files Affected

- `qc_clean/core/d6_bias_preflight.py` (add)
- `scripts/preflight_d6_bias_protocol.py` (add)
- `tests/test_d6_bias_preflight.py` (add)
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

1. Write TDD tests for passing preflight, missing required result files,
   unexpected result files, hash mismatches, attribute/surface mismatches, and
   CLI JSON output.
2. Implement `D6BiasPreflightReport` and `preflight_d6_bias_payloads`.
3. Add the preflight script and Make target.
4. Update docs with a provenance-only caveat.
5. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d6_bias_preflight.py` | `test_preflight_d6_bias_passes_matching_protocol_and_results` | Matching protocol/results pass. |
| `tests/test_d6_bias_preflight.py` | `test_preflight_d6_bias_fails_missing_required_results` | Configured dimensions require files. |
| `tests/test_d6_bias_preflight.py` | `test_preflight_d6_bias_fails_unexpected_result_file` | Unconfigured dimensions reject extra files. |
| `tests/test_d6_bias_preflight.py` | `test_preflight_d6_bias_fails_hash_and_attribute_mismatches` | Hash locks and stratified attributes/surfaces are enforced. |
| `tests/test_d6_bias_preflight.py` | `test_preflight_d6_bias_script_outputs_json` | CLI emits valid/invalid JSON reports and exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d6_bias_preflight.py -q` | New preflight behavior. |
| `python -m ruff check qc_clean/core/d6_bias_preflight.py scripts/preflight_d6_bias_protocol.py tests/test_d6_bias_preflight.py` | Focused lint on new surfaces. |
| `make -n d6-bias-preflight PROTOCOL=protocol.json STRATIFIED=bias_stratified.json COUNTERFACTUAL=bias_counterfactual.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Importable preflight returns a schema_version=1 report with pass/fail
  status, protocol metadata, row counts, and errors.
- [ ] CLI/Make preflight returns exit code 0 only when status is `pass`.
- [ ] Configured D6 dimensions require matching result files.
- [ ] Result files for unconfigured D6 dimensions fail loud.
- [ ] Optional protocol file-hash locks are enforced.
- [ ] Stratified rows are checked against registered attributes and surfaces.
- [ ] Counterfactual rows are validated and checked against registered
  attributes.
- [ ] Docs state this is provenance/preflight only, not bias evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should `make bench` grow an optional `D6_PROTOCOL=...` guard after this
  preflight exists? — Status: DEFERRED | This plan creates the standalone
  preflight first. Score-time guard integration is the likely next slice.

---

## Notes

This is a protocol/result matching gate. It does not create result rows, run
models, validate label correctness, prove causation, or show that the system is
unbiased.
