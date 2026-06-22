# Plan #114: D6 Bias Protocol Package

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #113 D6 stratified bias scorecard
**Blocks:** Populated INV-5 bias-audit workflow

---

## Outcome

Implemented in commit `be827ff` and pushed to `main`. The repo now has a
schema_version=1 D6 bias-audit protocol validator at
`qc_clean/core/d6_bias_protocol.py`, a machine-readable validator CLI at
`scripts/validate_d6_bias_protocol.py`, and the Make target
`make validate-d6-bias-protocol PROTOCOL=protocol.json`. The validator enforces
ethical respondent-attribute policy, frozen case-set metadata, configured D6
dimensions, matching stratified/counterfactual strategies, held-out freeze/
contamination/registration/project-state-hash gates, and dimension-covered
success criteria. Docs frame this as protocol/provenance only, not populated
bias-audit evidence or causal proof.

Verification evidence:
- TDD red slice: `python -m pytest tests/test_d6_bias_protocol.py -q` initially
  failed because `qc_clean.core.d6_bias_protocol` did not exist.
- Focused tests: `python -m pytest tests/test_d6_bias_protocol.py -q` -> `6
  passed`.
- Focused Ruff: `python -m ruff check qc_clean/core/d6_bias_protocol.py
  scripts/validate_d6_bias_protocol.py tests/test_d6_bias_protocol.py` ->
  passed.
- Make dry run: `make -n validate-d6-bias-protocol PROTOCOL=protocol.json`
  routes to `python scripts/validate_d6_bias_protocol.py protocol.json`.
- Docs gate: `make docs-check` passed.
- Full gate: `make check` -> `953 passed, 1 skipped, 8 deselected`; Ruff and
  docs checks passed; type check is still not configured.

---

## Gap

**Current:** Phase 0 can locally score externally supplied D6 counterfactual
identity-swap rows (`BIAS_COUNTERFACTUAL=...`) and stratified correctness/error
rows (`BIAS_STRATIFIED=...`). The repo still has no pre-run D6 protocol package
that records ethical attribute handling, frozen case-set metadata, respondent
attribute strategy, counterfactual strategy, required scorecard inputs, and
pre-registered success/reporting criteria before rows are generated or scored.

**Target:** Add a deterministic D6 protocol validator:

- New `qc_clean/core/d6_bias_protocol.py` with a schema_version=1 package model.
- New `scripts/validate_d6_bias_protocol.py`.
- New `make validate-d6-bias-protocol PROTOCOL=protocol.json`.
- Tests for valid held-out protocols, missing held-out gates, unsupported or
  duplicate dimensions, missing ethical attribute policy, missing success
  criteria, malformed hashes, and CLI JSON output.
- Docs updated to clarify this is protocol/provenance only, not a populated
  bias audit, causal proof, or bias-free evidence.

**Why:** Stratified and counterfactual bias rows are only meaningful when the
case set, respondent attributes, ethical permissibility, prompt/model freeze,
contamination check, and pass/reporting criteria are pre-registered. This slice
adds that gate without inventing labels or claiming bias evidence.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D6 calls for stratified error parity and
  counterfactual masking/swap, but says populated bias audits remain future.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-5 is partial infrastructure only and
  explicitly lacks a populated ethical respondent-attribute protocol.
- `qc_clean/core/adjudication_protocol.py` - pre-label protocol package pattern.
- `qc_clean/core/inv7_live_protocol.py` - pre-run protocol validator pattern.
- `qc_clean/core/d7_comparison_protocol.py` - protocol package with expected
  artifacts and held-out gates.
- `scripts/validate_adjudication_protocol.py` and
  `scripts/validate_inv7_live_protocol.py` - machine-readable validator CLI
  pattern.
- `tests/test_adjudication_protocol.py` and `tests/test_inv7_live_protocol.py`
  - validator regression style.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This implements the protocol/provenance layer already
implied by D6 in the evaluation harness and by the INV-5 claim-discipline gap.

---

## Capabilities

Internal protocol validation capability only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_d6_bias_protocol` | schema_version=1 D6 protocol JSON | validated protocol object / JSON validity report | qualitative_coding | agents/operators preparing D6 audits | free |

### Capability Validation

- [x] Valid held-out D6 protocol packages are accepted.
- [x] Held-out protocols require prompt/model freeze, contamination check,
  pre-run registration, project-state hash, and at least one D6 dimension.
- [x] Protocols require an ethical attribute policy and a non-empty attribute
  strategy before stratified metrics can be configured.
- [x] Counterfactual dimensions require a counterfactual strategy.
- [x] Success criteria must cover every configured D6 dimension.
- [x] Duplicate dimensions and malformed hashes fail loud.
- [x] CLI emits machine-readable JSON for valid and invalid packages.

---

## Proposed Protocol Shape

Top-level fields:

- `schema_version`: literal `1`
- `package_type`: literal
  `qualitative_coding.d6_bias_protocol`
- `protocol_id`, `project_id`, `dataset_name`
- `split`: `held_out`, `dev`, or `public_comparator`
- `corpus_sha256`
- `project_state_sha256` (required for held-out)
- `prompt_frozen`
- `contamination_checked`
- `registered_before_run`
- `dimensions`: one or both of `bias_stratified_d6`,
  `bias_counterfactual_d6`
- `attribute_policy`: ethical and provenance metadata for respondent attributes
- `case_set`: frozen case-set metadata, optional file/hash locks, planned case
  count, and optional minimum group size
- `stratified_strategy`: required when `bias_stratified_d6` is configured
- `counterfactual_strategy`: required when `bias_counterfactual_d6` is configured
- `success_criteria`: one or more criteria per configured dimension
- `caution`: protocol-only claim-discipline caveat

Deferred by design:

- Enforcing group-size thresholds inside `bias_stratified_scorecard`; thresholds
  are protocol metadata until the populated benchmark runner consumes them.
- Generating protected attributes, deciding whether attribute use is ethical, or
  creating counterfactual cases.
- Preflighting concrete D6 result packages against the protocol. That is the
  likely next slice after this validator exists.

---

## Files Affected

- `qc_clean/core/d6_bias_protocol.py` (add)
- `scripts/validate_d6_bias_protocol.py` (add)
- `tests/test_d6_bias_protocol.py` (add)
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
2. Implement `d6_bias_protocol` Pydantic models and validation helpers.
3. Add the validator script and Make target.
4. Update docs with a protocol-only caveat.
5. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d6_bias_protocol.py` | `test_validate_d6_bias_protocol_accepts_held_out_package` | Valid held-out protocol shape and caution. |
| `tests/test_d6_bias_protocol.py` | `test_validate_d6_bias_protocol_requires_held_out_freeze_contamination_registration_and_state_hash` | Held-out gates fail loud. |
| `tests/test_d6_bias_protocol.py` | `test_validate_d6_bias_protocol_rejects_missing_required_strategies` | Stratified/counterfactual dimensions require matching strategies. |
| `tests/test_d6_bias_protocol.py` | `test_validate_d6_bias_protocol_rejects_duplicate_dimensions_and_bad_hashes` | Duplicates and malformed hashes fail loud. |
| `tests/test_d6_bias_protocol.py` | `test_validate_d6_bias_protocol_script_outputs_json` | CLI emits machine-readable valid/invalid results. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d6_bias_protocol.py -q` | New validator behavior. |
| `python -m ruff check qc_clean/core/d6_bias_protocol.py scripts/validate_d6_bias_protocol.py tests/test_d6_bias_protocol.py` | Focused lint on new surfaces. |
| `make -n validate-d6-bias-protocol PROTOCOL=protocol.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] A schema_version=1 D6 protocol JSON can be validated by importable code.
- [x] `make validate-d6-bias-protocol PROTOCOL=protocol.json` emits JSON and
  returns non-zero on invalid packages.
- [x] Held-out protocols require prompt freeze, contamination check,
  pre-run registration, and project-state hash.
- [x] Stratified D6 dimensions require ethical attribute policy and stratified
  strategy metadata.
- [x] Counterfactual D6 dimensions require counterfactual strategy metadata.
- [x] Success criteria are required for every configured dimension.
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

- [x] Should the eventual scorecard enforce protocol thresholds such as
  `minimum_group_size`? — Status: DEFERRED | This plan records thresholds in
  protocol metadata only; enforcement belongs in the later protocol/result
  preflight or benchmark-runner slice.

---

## Notes

This plan creates a protocol validator. It does not generate protected
attributes, decide ethical permissibility, create case sets, run models, score
results, or demonstrate that the system is unbiased.
