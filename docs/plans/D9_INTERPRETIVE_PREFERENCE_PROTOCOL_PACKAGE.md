# Plan #123: D9 Interpretive Preference Protocol Package

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** D9 interpretive-preference scorecard and non-inferiority margin substrate
**Blocks:** D9 preference result preflight, D9 score-time protocol guard, populated blind expert preference workflow

---

## Gap

**Current:** `make bench PREFERENCE=preference.json` can score externally
supplied D9 forced-choice blind preference outcomes, including tie-rate Wilson
intervals and a non-inferiority assessment when the preference package itself
carries `non_inferiority_margin` and `registered_before_evaluation=true`.
There is no standalone pre-evaluation D9 protocol package validator.

**Target:** Add a versioned D9 interpretive-preference protocol package:

- `qc_clean/core/d9_interpretive_preference_protocol.py`.
- `scripts/validate_d9_interpretive_preference_protocol.py protocol.json`.
- `make validate-d9-interpretive-preference-protocol PROTOCOL=protocol.json`.
- Tests covering valid held-out protocols, held-out gates, hash validation,
  evaluator/blinding requirements, non-inferiority margin bounds, target
  criteria/surfaces, planned case count, and success criteria.
- Docs updated to clarify this is protocol/provenance only, not blind expert
  parity evidence, interpretive-depth evidence, methodological-validity
  evidence, or SOTA evidence.

**Why:** D9 already has a local scorecard and margin assessment, but the
pre-registration metadata still lives inside the result package. A standalone
protocol package is the first step toward a D9 protocol -> result -> scorecard
provenance chain equivalent to D4/D6/D8.

---

## References Reviewed

- `qc_clean/core/bench.py` - D9 `InterpretivePreferenceEvaluation`,
  `InterpretivePreferenceProtocol`, scorecard, tie-rate interval, and
  non-inferiority assessment semantics.
- `scripts/bench_phase0.py` - external D9 preference file loader and Phase 0
  input-hash/provenance plumbing.
- `qc_clean/core/d8_gt_fidelity_protocol.py` - recent standalone protocol
  package validator pattern.
- `scripts/validate_d8_gt_fidelity_protocol.py` - CLI validator pattern.
- `tests/test_d8_gt_fidelity_protocol.py` - protocol package regression shape.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - D9
  claim discipline and remaining-evidence caveats.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.
- Coordination claims: no active claim files found under
  `~/.claude/coordination/claims/` before this plan.

---

## Research Basis For This Slice

No new external research. The statistical semantics are already documented in
the evaluation harness: D9 parity is a non-inferiority/parity claim, not a
superiority claim. This slice only validates pre-evaluation protocol metadata.

---

## Capabilities

Internal protocol validation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_d9_interpretive_preference_protocol` | D9 protocol JSON | Validated D9 protocol object or machine-readable JSON error | qualitative_coding | agents/operators preparing D9 blind preference evaluations | free |

### Capability Validation

- [ ] Valid schema_version=1 held-out D9 protocols pass validation.
- [ ] Held-out protocols require prompt/model freeze, contamination check,
  pre-evaluation registration, blinding, project-state hash, and comparison
  artifact hash.
- [ ] Corpus/project/comparison/outcome hashes are valid SHA-256 values.
- [ ] Evaluator plan, target criteria, target surfaces, planned case count, and
  non-inferiority margin are non-empty/in range.
- [ ] Success criteria cover configured D9 outcome metrics.
- [ ] CLI emits machine-readable JSON for valid and invalid protocols.
- [ ] Make target routes to the CLI.

---

## Files Affected

- `qc_clean/core/d9_interpretive_preference_protocol.py` (add)
- `scripts/validate_d9_interpretive_preference_protocol.py` (add)
- `tests/test_d9_interpretive_preference_protocol.py` (add)
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
| `tests/test_d9_interpretive_preference_protocol.py` | `test_validate_d9_interpretive_preference_protocol_accepts_held_out_package` | Valid held-out D9 protocol metadata validates and preserves margin/criteria/surfaces. |
| `tests/test_d9_interpretive_preference_protocol.py` | `test_validate_d9_interpretive_preference_protocol_requires_held_out_gates` | Held-out gates fail loud when freeze/contamination/registration/blinding/hashes are missing. |
| `tests/test_d9_interpretive_preference_protocol.py` | `test_validate_d9_interpretive_preference_protocol_requires_evaluator_plan_and_case_design` | Empty evaluator plan, criteria, surfaces, planned case count, and bad margin fail. |
| `tests/test_d9_interpretive_preference_protocol.py` | `test_validate_d9_interpretive_preference_protocol_rejects_bad_hashes` | Malformed hash locks fail. |
| `tests/test_d9_interpretive_preference_protocol.py` | `test_validate_d9_interpretive_preference_protocol_requires_success_criteria_for_each_metric` | Success criteria must cover configured D9 outcome metrics. |
| `tests/test_d9_interpretive_preference_protocol.py` | `test_validate_d9_interpretive_preference_protocol_script_outputs_json` | CLI emits valid/invalid JSON and exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d9_interpretive_preference_protocol.py -q` | New D9 protocol contract. |
| `python -m ruff check qc_clean/core/d9_interpretive_preference_protocol.py scripts/validate_d9_interpretive_preference_protocol.py tests/test_d9_interpretive_preference_protocol.py` | Focused lint on new surfaces. |
| `make -n validate-d9-interpretive-preference-protocol PROTOCOL=protocol.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] D9 preference protocols can be validated before preference outcomes are
  collected or scored.
- [ ] Held-out D9 protocols enforce freeze/contamination/registration/blinding
  gates and required hashes.
- [ ] Protocols carry non-inferiority margin metadata as pre-evaluation
  process data.
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

- [ ] Should D9 protocol/result preflight require exact target surface equality
  or allow result subsets? — Status: DEFERRED | Decide in the result-preflight
  lane after this protocol validator exists.
- [ ] Should the score-time guard inject protocol metadata into D9
  non-inferiority assessment when result files omit embedded protocol metadata?
  — Status: DEFERRED | Decide in the score-time guard lane.

---

## Notes

This plan validates protocol metadata only. It does not create preference
cases, blind evaluators, collect expert ratings, validate preference labels,
prove interpretive-depth parity, prove methodological validity, or license a
SOTA claim.
