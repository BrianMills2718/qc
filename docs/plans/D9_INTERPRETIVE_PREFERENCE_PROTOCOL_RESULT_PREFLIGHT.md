# Plan #124: D9 Interpretive Preference Protocol Result Preflight

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #123 D9 interpretive-preference protocol package
**Blocks:** D9 score-time protocol guard, populated blind expert preference workflow

---

## Gap

**Current:** D9 pre-evaluation protocol packages can be validated with
`make validate-d9-interpretive-preference-protocol PROTOCOL=protocol.json`, and
`make bench PREFERENCE=preference.json` can score externally supplied D9
forced-choice outcomes. There is no protocol/result preflight that checks a
concrete preference result file against a registered D9 protocol before scoring.

**Target:** Add a D9 protocol/result preflight:

- `qc_clean/core/d9_interpretive_preference_preflight.py`.
- `scripts/preflight_d9_interpretive_preference_protocol.py protocol.json --preference-file preference.json`.
- `make d9-interpretive-preference-preflight PROTOCOL=protocol.json PREFERENCE=preference.json`.
- Result rows can carry `evaluator_type` and `surface` so preflight can compare
  evaluator types and target surfaces against the protocol.
- Preflight validates the protocol and concrete preference rows, checks optional
  result-file SHA-256 locks, evaluator type/count, target criteria, target
  surfaces, and planned case count.
- Preflight emits a schema_version=1 pass/fail report with claim-discipline
  caveats.
- Docs updated to clarify this is protocol/result provenance only, not blind
  expert-parity evidence, interpretive-depth evidence,
  methodological-validity evidence, or SOTA evidence.

**Why:** D9 now has a standalone protocol validator. The next durability gap is
binding concrete result files to that protocol before those results are scored.
This mirrors the D4/D6/D8 protocol -> result -> scorecard progression.

---

## References Reviewed

- `qc_clean/core/d9_interpretive_preference_protocol.py` - D9 protocol package
  contract.
- `qc_clean/core/bench.py` - D9 result row model and scorecard semantics.
- `qc_clean/core/d8_gt_fidelity_preflight.py` - recent protocol/result
  preflight pattern.
- `tests/test_d8_gt_fidelity_preflight.py` - pass/fail/script regression shape.
- `scripts/preflight_d8_gt_fidelity_protocol.py` - CLI preflight pattern.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - D9
  claim discipline and remaining-evidence caveats.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.
- Coordination claims: no active claim files found under
  `~/.claude/coordination/claims/` before this plan.

---

## Research Basis For This Slice

No new external research. This slice only cross-checks already-defined D9
protocol metadata and existing local D9 scorecard row semantics.

---

## Capabilities

Internal preflight validation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `preflight_d9_interpretive_preference_protocol_results` | D9 protocol JSON + D9 preference JSON | D9 preflight report JSON | qualitative_coding | agents/operators preparing D9 blind preference evaluations | free |

### Capability Validation

- [ ] Valid protocol/result pairs pass.
- [ ] Missing preference result files fail loud.
- [ ] Optional result-file SHA-256 locks are enforced.
- [ ] Evaluator type set, evaluator count, target criteria set, target surface
  set, and planned case count are cross-checked.
- [ ] Preflight report includes schema version, protocol ID, project ID, split,
  target criteria/surfaces, non-inferiority margin, result row count, case
  count, evaluator count/types, status, errors, and caution.
- [ ] CLI emits machine-readable JSON and meaningful exit codes.
- [ ] Make target routes to the CLI.

---

## Files Affected

- `qc_clean/core/bench.py` (modify D9 row model with optional preflight fields)
- `qc_clean/core/d9_interpretive_preference_preflight.py` (add)
- `scripts/preflight_d9_interpretive_preference_protocol.py` (add)
- `tests/test_d9_interpretive_preference_preflight.py` (add)
- `tests/test_bench_phase0.py` (update if row model output expectations require it)
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

1. Write failing D9 preflight tests for pass, missing file, hash mismatch,
   evaluator/criterion/surface drift, planned case count, and CLI output.
2. Add optional `evaluator_type` and `surface` fields to
   `InterpretivePreferenceEvaluation` with defaults preserving existing
   scorecard compatibility.
3. Implement D9 preflight report models and cross-check logic.
4. Add CLI and Make target.
5. Update docs with protocol/result-preflight caveats and future score-time
   guard direction.
6. Run focused tests, focused Ruff, Make dry-run, docs checks, and full
   `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d9_interpretive_preference_preflight.py` | `test_preflight_d9_interpretive_preference_accepts_matching_protocol_and_rows` | Valid protocol/result pair passes and reports counts/metadata. |
| `tests/test_d9_interpretive_preference_preflight.py` | `test_preflight_d9_interpretive_preference_requires_result_file` | Missing result file fails with a machine-readable error. |
| `tests/test_d9_interpretive_preference_preflight.py` | `test_preflight_d9_interpretive_preference_rejects_hash_lock_mismatch` | Outcome SHA-256 lock mismatch fails. |
| `tests/test_d9_interpretive_preference_preflight.py` | `test_preflight_d9_interpretive_preference_rejects_evaluator_criterion_and_surface_drift` | Evaluator type/count, criteria, and surface drift fail. |
| `tests/test_d9_interpretive_preference_preflight.py` | `test_preflight_d9_interpretive_preference_requires_planned_case_count` | Result rows must meet the planned unique case count. |
| `tests/test_d9_interpretive_preference_preflight.py` | `test_preflight_d9_interpretive_preference_script_outputs_json` | CLI emits pass/fail JSON and exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d9_interpretive_preference_protocol.py tests/test_d9_interpretive_preference_preflight.py tests/test_bench_phase0.py::test_scorecard_scores_interpretive_preference_outcomes tests/test_bench_phase0_script.py::test_bench_phase0_scores_interpretive_preference_from_file_without_mutating_state -q` | D9 protocol/preflight and existing D9 scorecard compatibility. |
| `python -m ruff check qc_clean/core/bench.py qc_clean/core/d9_interpretive_preference_preflight.py scripts/preflight_d9_interpretive_preference_protocol.py tests/test_d9_interpretive_preference_preflight.py` | Focused lint on modified/new D9 surfaces. |
| `make -n d9-interpretive-preference-preflight PROTOCOL=protocol.json PREFERENCE=preference.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] D9 protocol/result pairs can be preflighted before scoring.
- [ ] Passing reports include the expected D9 protocol/result metadata.
- [ ] Missing/mismatched preference results fail loud with machine-readable
  errors.
- [ ] D9 result rows can carry evaluator type and surface without breaking
  existing scorecard callers.
- [ ] Docs state the preflight is process/provenance only.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [x] Should D9 protocol/result preflight require exact target surface equality
  or allow result subsets? — Status: DECIDED | Use exact set equality for
  criteria and surfaces, matching D4/D8 strict protocol drift checks.
- [ ] Should the score-time guard inject protocol metadata into D9
  non-inferiority assessment when result files omit embedded protocol metadata?
  — Status: DEFERRED | Decide in the score-time guard lane.

---

## Notes

This plan preflights result-file/protocol consistency. It does not create
preference cases, blind evaluators, collect expert ratings, validate preference
labels beyond schema/protocol consistency, prove interpretive-depth parity,
prove methodological validity, or license a SOTA claim.
