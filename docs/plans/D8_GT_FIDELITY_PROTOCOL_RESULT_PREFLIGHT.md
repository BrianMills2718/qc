# Plan #121: D8 GT Fidelity Protocol Result Preflight

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #120 D8 GT-fidelity protocol package
**Blocks:** D8 GT-fidelity score-time preflight guard; populated expert
GT-fidelity evaluation workflow

---

## Gap

**Current:** `make validate-d8-gt-fidelity-protocol PROTOCOL=protocol.json`
validates pre-evaluation D8 protocol metadata. `make bench
GT_FIDELITY=gt_fidelity.json` scores externally supplied D8 rubric outcomes.
There is no deterministic preflight that checks a concrete D8 result file
against the registered protocol before scorecard ingestion.

**Target:** Add a deterministic D8 protocol/result preflight:

- New `qc_clean/core/d8_gt_fidelity_preflight.py`.
- New `scripts/preflight_d8_gt_fidelity_protocol.py`.
- New `make d8-gt-fidelity-preflight PROTOCOL=protocol.json
  GT_FIDELITY=gt_fidelity.json`.
- Tests for passing preflight, missing result file, protocol/result hash-lock
  mismatch, evaluator drift, target-scope drift, artifact ID requirements, and
  CLI JSON pass/fail output.
- Docs updated to clarify this is protocol/provenance only, not expert-rubric
  acceptance, methodological-saturation evidence, full grounded-theory
  evidence, or SOTA evidence.

**Why:** Protocol validation alone can still let the wrong rows be scored.
Before D8 outcomes can support any benchmark process, agents need an
agent-drivable check that the collected rubric rows match the registered
protocol.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D8 requires expert rubric acceptance only
  after populated outcomes under a protocol.
- `docs/PROJECT_THEORY_AND_GOALS.md` - populated D8 expert GT-fidelity
  evidence remains future work.
- `qc_clean/core/d8_gt_fidelity_protocol.py` - D8 protocol package validator.
- `qc_clean/core/bench.py` - `GTFidelityEvaluation` row schema and D8
  scorecard.
- `qc_clean/core/d4_codebook_quality_preflight.py` - closest rubric-result
  preflight pattern.
- `qc_clean/core/d6_bias_preflight.py` - result presence/hash-lock preflight
  pattern.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This is the concrete result-file preflight already
implied by the D8 protocol and the D4/D6 preflight pattern.

---

## Capabilities

Internal protocol/result preflight capability only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `preflight_d8_gt_fidelity_protocol` | schema_version=1 D8 protocol JSON + D8 result JSON | schema_version=1 pass/fail preflight report | qualitative_coding | agents/operators preparing D8 evaluations | free |

### Capability Validation

- [ ] Valid protocol/result pairs produce `status="pass"`.
- [ ] Missing D8 result files fail loud.
- [ ] Invalid protocol packages fail loud inside the report.
- [ ] Invalid D8 result row payloads fail loud inside the report.
- [ ] Protocol `outcome_file_sha256` is checked against the actual result file
  hash when set.
- [ ] Result evaluator types match the protocol evaluator plan.
- [ ] Unique result evaluators meet or exceed the protocol planned evaluator
  count.
- [ ] Result scopes match protocol target scopes.
- [ ] Non-`grounded_theory_pipeline` result scopes require `artifact_id`.
- [ ] CLI emits machine-readable JSON and exits non-zero on failure.

---

## Proposed Report Shape

Top-level fields:

- `schema_version`: literal `1`
- `package_type`: literal `d8_gt_fidelity_protocol_result_preflight`
- `status`: `pass` or `fail`
- `protocol_id`, `project_id`, `split`
- `rubric_metrics`
- `target_scopes`
- `result_row_count`
- `evaluator_count`
- `evaluator_types`
- `artifact_count`
- `errors`: list of `{field, message}`
- `caution`: preflight-only claim-discipline caveat

Deferred by design:

- Enforcing this preflight inside `make bench`.
- Running expert panels or LLM judges.
- Claiming expert-rubric acceptance, methodological saturation, full grounded
  theory, or SOTA performance.

---

## Files Affected

- `qc_clean/core/d8_gt_fidelity_preflight.py` (add)
- `scripts/preflight_d8_gt_fidelity_protocol.py` (add)
- `tests/test_d8_gt_fidelity_preflight.py` (add)
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

1. Write TDD tests for pass/fail preflight behavior and CLI JSON.
2. Implement D8 preflight Pydantic report models and cross-check helpers.
3. Add preflight script and Make target.
4. Update docs with a preflight-only caveat.
5. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d8_gt_fidelity_preflight.py` | `test_preflight_d8_gt_fidelity_accepts_matching_protocol_and_rows` | Valid protocol/result pair passes with counts and caveat. |
| `tests/test_d8_gt_fidelity_preflight.py` | `test_preflight_d8_gt_fidelity_requires_result_file` | Missing result file fails loud. |
| `tests/test_d8_gt_fidelity_preflight.py` | `test_preflight_d8_gt_fidelity_rejects_hash_lock_mismatch` | Protocol outcome hash lock is enforced. |
| `tests/test_d8_gt_fidelity_preflight.py` | `test_preflight_d8_gt_fidelity_rejects_evaluator_and_scope_drift` | Evaluator types/count and target scopes match the protocol. |
| `tests/test_d8_gt_fidelity_preflight.py` | `test_preflight_d8_gt_fidelity_requires_artifact_ids_for_targeted_scopes` | Category/memo/model rows require artifact IDs. |
| `tests/test_d8_gt_fidelity_preflight.py` | `test_preflight_d8_gt_fidelity_script_outputs_json` | CLI emits machine-readable valid/invalid reports. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d8_gt_fidelity_protocol.py tests/test_d8_gt_fidelity_preflight.py -q` | D8 protocol + preflight behavior. |
| `python -m ruff check qc_clean/core/d8_gt_fidelity_protocol.py qc_clean/core/d8_gt_fidelity_preflight.py scripts/validate_d8_gt_fidelity_protocol.py scripts/preflight_d8_gt_fidelity_protocol.py tests/test_d8_gt_fidelity_protocol.py tests/test_d8_gt_fidelity_preflight.py` | Focused lint on D8 surfaces. |
| `make -n d8-gt-fidelity-preflight PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] A schema_version=1 D8 GT-fidelity protocol/result preflight report can be
  produced by importable code.
- [ ] `make d8-gt-fidelity-preflight PROTOCOL=protocol.json
  GT_FIDELITY=gt_fidelity.json` emits JSON and returns non-zero on failed
  preflight.
- [ ] Result files must exist and contain valid D8 rubric rows.
- [ ] Protocol hash locks, evaluator plan, target scopes, and targeted-scope
  artifact IDs are enforced.
- [ ] Docs state D8 preflight is process/provenance only.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should the D8 score-time guard follow immediately? — Status: DEFERRED |
  This plan adds standalone protocol/result preflight first. The score-time
  guard can follow the D4/D6 guard pattern in the next slice.

---

## Notes

This plan creates a result-file preflight. It does not collect expert ratings,
run LLM judges, validate rubric labels beyond schema/protocol consistency,
prove methodological saturation, prove full grounded theory, or license a SOTA
claim.
