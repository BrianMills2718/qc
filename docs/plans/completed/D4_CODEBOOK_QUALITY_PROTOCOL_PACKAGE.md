# Plan #117: D4 Codebook Quality Protocol Package

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 D4 scorecard substrate
**Blocks:** Populated D4 blind expert / LLM-judge evaluation workflow

---

## Outcome

Implemented and verified the schema_version=1 D4 codebook-quality protocol
validator, importable validation API, JSON CLI, and Make target. The package
checks held-out gates, codebook/corpus/state hashes, blinding, evaluator plans,
required rubric metrics, and per-metric success criteria while preserving the
claim-discipline caveat that protocol metadata is not blind expert-panel
evidence, codebook-quality evidence, methodological-validity evidence, or SOTA
evidence.

Verification evidence:

- TDD red: `python -m pytest tests/test_d4_codebook_quality_protocol.py -q`
  initially failed with missing `qc_clean.core.d4_codebook_quality_protocol`.
- Focused tests: `python -m pytest tests/test_d4_codebook_quality_protocol.py -q`
  passed (`6 passed`).
- Focused Ruff:
  `python -m ruff check qc_clean/core/d4_codebook_quality_protocol.py scripts/validate_d4_codebook_quality_protocol.py tests/test_d4_codebook_quality_protocol.py`
  passed.
- Make dry-run:
  `make -n validate-d4-codebook-quality-protocol PROTOCOL=protocol.json`
  emitted `python scripts/validate_d4_codebook_quality_protocol.py protocol.json`.
- Docs gate: `make docs-check` passed.
- Full gate: `make check` passed (`966 passed, 1 skipped, 8 deselected`;
  Ruff and docs checks clean; type check not configured).
- Implementation commit pushed: `e24b300`
  `[Plan: D4_CODEBOOK_QUALITY_PROTOCOL_PACKAGE] Add D4 protocol validator`.

---

## Gap

**Current:** Phase 0 can locally score externally supplied D4 codebook-quality
rubric rows through `CODEBOOK_QUALITY=quality.json`, reporting rubric means and
bootstrap intervals. There is no pre-registered protocol package for the D4
evaluation: evaluator plan, blinding, codebook artifact hash, rubric metrics,
target scopes, split/freeze metadata, and success/reporting criteria are not
validated before rows are collected or scored.

**Target:** Add a deterministic D4 codebook-quality protocol validator:

- New `qc_clean/core/d4_codebook_quality_protocol.py`.
- New `scripts/validate_d4_codebook_quality_protocol.py`.
- New `make validate-d4-codebook-quality-protocol PROTOCOL=protocol.json`.
- Tests for valid held-out protocols, held-out gates, rubric/evaluator
  requirements, blinding requirements, malformed hashes, missing criteria, and
  CLI JSON output.
- Docs updated to clarify this is protocol/provenance only, not blind expert
  evidence, codebook-quality evidence, or SOTA evidence.

**Why:** D4 is one of the dimensions where the product can credibly compete, but
only if expert/LLM-judge rubric outcomes are collected under a frozen, blinded,
pre-registered protocol. This slice adds the deterministic protocol gate before
any populated D4 rows are treated as benchmark evidence.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D4 requires LLM-judge rubric plus blind human
  expert panel; current scoring substrate is local accounting only.
- `docs/PROJECT_THEORY_AND_GOALS.md` - D4 populated LLM-judge/blind-expert
  evaluations remain unpopulated evidence.
- `qc_clean/core/bench.py` - `CodebookQualityEvaluation` row schema and D4
  scorecard.
- `qc_clean/core/d6_bias_protocol.py` - recent protocol package validator
  pattern.
- `qc_clean/core/adjudication_protocol.py` - held-out/freeze/registration gate
  pattern.
- `scripts/validate_d6_bias_protocol.py` - machine-readable validator CLI
  pattern.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This implements the protocol/provenance layer already
specified by D4 in the evaluation harness.

---

## Capabilities

Internal protocol validation capability only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_d4_codebook_quality_protocol` | schema_version=1 D4 protocol JSON | validated protocol object / JSON validity report | qualitative_coding | agents/operators preparing D4 evaluations | free |

### Capability Validation

- [x] Valid held-out D4 protocol packages are accepted.
- [x] Held-out protocols require prompt/model freeze, contamination check,
  pre-evaluation registration, project-state hash, and codebook artifact hash.
- [x] Protocols require blind evaluation metadata.
- [x] Protocols require non-empty evaluator plan and at least one evaluator.
- [x] Protocols require the D4 rubric metrics: clarity, specificity,
  usefulness, and grounding.
- [x] Success criteria are required for every configured rubric metric.
- [x] Malformed hashes and duplicate metric/evaluator entries fail loud.
- [x] CLI emits machine-readable JSON for valid and invalid packages.

---

## Proposed Protocol Shape

Top-level fields:

- `schema_version`: literal `1`
- `package_type`: literal
  `qualitative_coding.d4_codebook_quality_protocol`
- `protocol_id`, `project_id`, `dataset_name`
- `split`: `held_out`, `dev`, or `public_comparator`
- `corpus_sha256`
- `project_state_sha256` (required for held-out)
- `codebook_artifact_sha256` (required for held-out)
- `prompt_frozen`
- `contamination_checked`
- `registered_before_evaluation`
- `blinding`: evaluator/source blinding metadata
- `evaluator_plan`: evaluator types/counts/qualification statement
- `rubric_metrics`: must include clarity, specificity, usefulness, grounding
- `target_scopes`: e.g. `codebook`, `individual_code`
- `outcome_file` and optional `outcome_file_sha256`
- `success_criteria`: one or more criteria per rubric metric
- `caution`: protocol-only claim-discipline caveat

Deferred by design:

- Preflighting concrete D4 result files against this protocol.
- Running LLM-judge or human expert panels.
- Claiming expert acceptance, codebook quality, or SOTA performance.

---

## Files Affected

- `qc_clean/core/d4_codebook_quality_protocol.py` (add)
- `scripts/validate_d4_codebook_quality_protocol.py` (add)
- `tests/test_d4_codebook_quality_protocol.py` (add)
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
2. Implement D4 protocol Pydantic models and validation helpers.
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
| `tests/test_d4_codebook_quality_protocol.py` | `test_validate_d4_codebook_quality_protocol_accepts_held_out_package` | Valid held-out protocol shape and caveat. |
| `tests/test_d4_codebook_quality_protocol.py` | `test_validate_d4_codebook_quality_protocol_requires_held_out_gates` | Held-out freeze/contamination/registration/state/codebook gates fail loud. |
| `tests/test_d4_codebook_quality_protocol.py` | `test_validate_d4_codebook_quality_protocol_requires_blinding_and_evaluators` | Blinding/evaluator plan fail loud when absent. |
| `tests/test_d4_codebook_quality_protocol.py` | `test_validate_d4_codebook_quality_protocol_rejects_missing_metrics_and_bad_hashes` | Required metrics and hashes are enforced. |
| `tests/test_d4_codebook_quality_protocol.py` | `test_validate_d4_codebook_quality_protocol_requires_success_criteria_for_each_metric` | Success criteria must cover every D4 metric. |
| `tests/test_d4_codebook_quality_protocol.py` | `test_validate_d4_codebook_quality_protocol_script_outputs_json` | CLI emits machine-readable valid/invalid results. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d4_codebook_quality_protocol.py -q` | New validator behavior. |
| `python -m ruff check qc_clean/core/d4_codebook_quality_protocol.py scripts/validate_d4_codebook_quality_protocol.py tests/test_d4_codebook_quality_protocol.py` | Focused lint on new surfaces. |
| `make -n validate-d4-codebook-quality-protocol PROTOCOL=protocol.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] A schema_version=1 D4 codebook-quality protocol JSON can be validated by
  importable code.
- [x] `make validate-d4-codebook-quality-protocol PROTOCOL=protocol.json` emits
  JSON and returns non-zero on invalid packages.
- [x] Held-out protocols require prompt freeze, contamination check,
  pre-evaluation registration, project-state hash, and codebook artifact hash.
- [x] Blinding and evaluator-plan metadata are required.
- [x] All four D4 rubric metrics are required.
- [x] Success criteria cover every configured metric.
- [x] Docs state protocol validation is process/provenance only.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should D4 protocol/result preflight and score-time guard follow
  immediately? — Status: DEFERRED | This plan validates protocol metadata first;
  concrete-result preflight/guard can follow the D6 pattern in a later slice.

---

## Notes

This plan creates a protocol validator. It does not collect expert ratings, run
LLM judges, validate rubric labels, prove codebook quality, or license a SOTA
claim.
