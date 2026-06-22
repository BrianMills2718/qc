# Plan #120: D8 GT Fidelity Protocol Package

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 D8 GT-fidelity scorecard substrate
**Blocks:** D8 GT-fidelity protocol/result preflight; populated expert
GT-fidelity evaluation workflow

---

## Gap

**Current:** Phase 0 can locally score externally supplied D8 GT-fidelity rubric
rows through `GT_FIDELITY=gt_fidelity.json`, reporting metric means and
bootstrap intervals. There is no pre-registered protocol package for the D8
evaluation: evaluator plan, GT artifact hash, rubric metrics, target scopes,
split/freeze metadata, and success/reporting criteria are not validated before
rows are collected or scored.

**Target:** Add a deterministic D8 GT-fidelity protocol validator:

- New `qc_clean/core/d8_gt_fidelity_protocol.py`.
- New `scripts/validate_d8_gt_fidelity_protocol.py`.
- New `make validate-d8-gt-fidelity-protocol PROTOCOL=protocol.json`.
- Tests for valid held-out protocols, held-out gates, rubric/evaluator
  requirements, malformed hashes, missing target scopes, missing criteria, and
  CLI JSON output.
- Docs updated to clarify this is protocol/provenance only, not expert-rubric
  acceptance, methodological-saturation evidence, full grounded-theory
  evidence, or SOTA evidence.

**Why:** D8 is the dimension that prevents the system from laundering
"GT-inspired" outputs into grounded-theory claims. A frozen, pre-registered
protocol is the first gate before any expert GT-fidelity rubric rows can be
treated as benchmark evidence.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D8 requires expert rubric acceptance on
  constant comparison, category development, memo quality, and saturation
  justification; current scoring substrate is local accounting only.
- `docs/PROJECT_THEORY_AND_GOALS.md` - populated D8 expert GT-fidelity
  benchmark and full theoretical sampling remain future work.
- `qc_clean/core/bench.py` - `GTFidelityEvaluation` row schema and D8
  scorecard.
- `qc_clean/core/d4_codebook_quality_protocol.py` - recent protocol validator
  pattern for rubric outcomes.
- `qc_clean/core/d6_bias_protocol.py` - protocol package validator pattern for
  held-out/freeze/registration gates.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This implements the protocol/provenance layer already
specified by D8 in the evaluation harness.

---

## Capabilities

Internal protocol validation capability only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_d8_gt_fidelity_protocol` | schema_version=1 D8 protocol JSON | validated protocol object / JSON validity report | qualitative_coding | agents/operators preparing D8 evaluations | free |

### Capability Validation

- [ ] Valid held-out D8 protocol packages are accepted.
- [ ] Held-out protocols require prompt/model freeze, contamination check,
  pre-evaluation registration, project-state hash, and GT artifact hash.
- [ ] Protocols require non-empty evaluator plan and at least one evaluator.
- [ ] Protocols require the D8 rubric metrics: constant comparison, category
  development, memo quality, and saturation justification.
- [ ] Protocols require non-empty target scopes.
- [ ] Success criteria are required for every configured rubric metric.
- [ ] Malformed hashes and duplicate metric/evaluator/scope entries fail loud.
- [ ] CLI emits machine-readable JSON for valid and invalid packages.

---

## Proposed Protocol Shape

Top-level fields:

- `schema_version`: literal `1`
- `package_type`: literal `qualitative_coding.d8_gt_fidelity_protocol`
- `protocol_id`, `project_id`, `dataset_name`
- `split`: `held_out`, `dev`, or `public_comparator`
- `corpus_sha256`
- `project_state_sha256` (required for held-out)
- `gt_artifact_sha256` (required for held-out)
- `prompt_frozen`
- `contamination_checked`
- `registered_before_evaluation`
- `evaluator_plan`: evaluator types/counts/qualification statement
- `rubric_metrics`: must include constant comparison, category development,
  memo quality, and saturation justification
- `target_scopes`: e.g. `grounded_theory_pipeline`, `category`, `memo`,
  `theoretical_model`
- `outcome_file` and optional `outcome_file_sha256`
- `success_criteria`: one or more criteria per rubric metric
- `caution`: protocol-only claim-discipline caveat

Deferred by design:

- Preflighting concrete D8 result files against this protocol.
- Running expert panels or LLM judges.
- Claiming expert-rubric acceptance, methodological saturation, full grounded
  theory, or SOTA performance.

---

## Files Affected

- `qc_clean/core/d8_gt_fidelity_protocol.py` (add)
- `scripts/validate_d8_gt_fidelity_protocol.py` (add)
- `tests/test_d8_gt_fidelity_protocol.py` (add)
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

1. Write TDD tests for valid/invalid protocol payloads and validator CLI JSON.
2. Implement D8 protocol Pydantic models and validation helpers.
3. Add validator script and Make target.
4. Update docs with a protocol-only caveat.
5. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d8_gt_fidelity_protocol.py` | `test_validate_d8_gt_fidelity_protocol_accepts_held_out_package` | Valid held-out protocol shape and caveat. |
| `tests/test_d8_gt_fidelity_protocol.py` | `test_validate_d8_gt_fidelity_protocol_requires_held_out_gates` | Held-out freeze/contamination/registration/state/artifact gates fail loud. |
| `tests/test_d8_gt_fidelity_protocol.py` | `test_validate_d8_gt_fidelity_protocol_requires_evaluator_plan_and_scopes` | Evaluator plan and target scopes fail loud when absent. |
| `tests/test_d8_gt_fidelity_protocol.py` | `test_validate_d8_gt_fidelity_protocol_rejects_missing_metrics_and_bad_hashes` | Required metrics and hashes are enforced. |
| `tests/test_d8_gt_fidelity_protocol.py` | `test_validate_d8_gt_fidelity_protocol_requires_success_criteria_for_each_metric` | Success criteria must cover every D8 metric. |
| `tests/test_d8_gt_fidelity_protocol.py` | `test_validate_d8_gt_fidelity_protocol_script_outputs_json` | CLI emits machine-readable valid/invalid results. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d8_gt_fidelity_protocol.py -q` | New validator behavior. |
| `python -m ruff check qc_clean/core/d8_gt_fidelity_protocol.py scripts/validate_d8_gt_fidelity_protocol.py tests/test_d8_gt_fidelity_protocol.py` | Focused lint on new surfaces. |
| `make -n validate-d8-gt-fidelity-protocol PROTOCOL=protocol.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] A schema_version=1 D8 GT-fidelity protocol JSON can be validated by
  importable code.
- [ ] `make validate-d8-gt-fidelity-protocol PROTOCOL=protocol.json` emits JSON
  and returns non-zero on invalid packages.
- [ ] Held-out protocols require prompt freeze, contamination check,
  pre-evaluation registration, project-state hash, and GT artifact hash.
- [ ] Evaluator-plan metadata and target scopes are required.
- [ ] All four D8 rubric metrics are required.
- [ ] Success criteria cover every configured metric.
- [ ] Docs state protocol validation is process/provenance only.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should D8 protocol/result preflight and score-time guard follow
  immediately? — Status: DEFERRED | This plan validates protocol metadata first;
  concrete-result preflight/guard can follow the D4/D6 patterns in later
  slices.

---

## Notes

This plan creates a protocol validator. It does not collect expert ratings, run
LLM judges, validate rubric labels, prove methodological saturation, prove full
grounded theory, or license a SOTA claim.
