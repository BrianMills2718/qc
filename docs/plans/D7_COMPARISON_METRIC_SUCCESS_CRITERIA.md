# Plan #172: D7 Comparison Metric Success Criteria

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** D7 comparison protocol/preflight guard
**Blocks:** Held-out D7 retrieval/live-baseline comparisons with pre-registered
machine-checkable pass/fail criteria

---

## Gap

**Current:** D7 comparison protocol packages validate gold/prediction
provenance, held-out gates, expected retrieval/live-baseline configuration, and
human-readable `success_criteria`. The scoring CLI can enforce preflight before
comparison output, and D7 scorecards now include exact metrics plus diagnostic
span-overlap metadata. However, D7 comparison success criteria remain free text,
so an agent cannot deterministically tell whether a guarded comparison met its
pre-registered metric thresholds.

**Target:** Extend the D7 comparison protocol with optional structured metric
criteria and evaluate those criteria at the guarded comparison boundary:

- Protocol packages accept `metric_criteria`, a list of per-baseline metric
  threshold criteria with explicit operators, thresholds, and rationale.
- Protocol validation rejects duplicate criterion IDs, unknown baselines,
  unsupported metrics, out-of-range thresholds, empty rationale, and malformed
  criteria.
- `scripts/validate_d7_comparison_protocol.py` reports
  `metric_criteria_count`.
- `scripts/compare_d7_retrieval.py --protocol-package ...` includes a
  machine-readable metric-criteria result section after a passing preflight.
- Missing metrics fail criteria explicitly instead of silently passing.
- Existing D7 exact-score, span-overlap, baseline, and preflight semantics stay
  unchanged when no structured criteria are supplied.

**Why:** The roadmap calls for semantic/embedding D7 evaluation-policy
scaffolding before treating any held-out comparison as evidence. This slice
turns pre-registered D7 success criteria from prose into deterministic
accounting while preserving the caveat that protocol/scoring infrastructure is
not held-out D7 evidence by itself.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-2/INV-6 still lack validated
  embedding/adversarial retrieval policy and held-out D7 evidence.
- `docs/EVALUATION_HARNESS.md` - D7 can score supplied gold/baselines, but
  populated held-out comparisons remain future evidence.
- `qc_clean/core/d7_comparison_protocol.py` - current protocol contract and
  human-readable criteria.
- `qc_clean/core/d7_comparison_preflight.py` - score-time provenance guard.
- `scripts/compare_d7_retrieval.py` - guarded comparison CLI boundary.
- `qc_clean/core/d4_codebook_quality_protocol.py` and
  `qc_clean/core/d9_interpretive_preference_protocol.py` - structured
  success-criteria patterns.
- Coordination/memory check: no active claim files; `agent-memory recall`
  returned only low-relevance historical completed-task entries.

---

## Research Basis For This Slice

No new external research. This implements the deterministic protocol/accounting
layer already implied by the D7 evaluation roadmap.

---

## Capabilities

Internal D7 protocol/accounting capability only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_d7_comparison_protocol` | schema_version=1 D7 comparison protocol JSON | validated protocol object / JSON validity report | qualitative_coding | agents/operators preparing D7 comparisons | free |
| `evaluate_d7_comparison_metric_criteria` | D7 comparison protocol + comparison report | criteria result JSON | qualitative_coding | guarded comparison CLI, agents reviewing D7 reports | free |

### Capability Validation

- [ ] Valid protocols with structured metric criteria are accepted.
- [ ] Criteria can target exact D7 metrics and span-overlap diagnostics for
  expected baselines.
- [ ] Criteria cannot reference unknown baselines or unsupported/missing
  metrics.
- [ ] Operators and thresholds are validated deterministically.
- [ ] Guarded comparison output includes criteria result status when criteria
  are present.
- [ ] Unguarded or no-criteria comparison output remains compatible.

---

## Proposed Protocol Shape

Add an optional top-level field:

- `metric_criteria`: list of structured criteria, default `[]`

Each criterion:

- `criterion_id`: stable unique ID
- `baseline_name`: expected baseline being evaluated
- `metric`: one of exact-score `recall`, `precision`, `f1`, or diagnostic
  span-overlap metrics `mean_best_gold_iou`, `mean_best_predicted_iou`,
  `mean_best_gold_modified_hausdorff_distance`,
  `mean_best_predicted_modified_hausdorff_distance`
- `operator`: one of `>=`, `>`, `<=`, `<`, `==`
- `threshold`: float threshold
- `rationale`: human-readable pre-registration rationale

Deferred by design:

- Generating gold labels.
- Choosing validated default embedding/reviewer policy.
- Claiming superiority, methodological validity, or SOTA.
- Requiring structured criteria for old protocol artifacts; this remains
  backward-compatible and optional in schema version 1.

---

## Files Affected

- `qc_clean/core/d7_comparison_protocol.py`
- `scripts/validate_d7_comparison_protocol.py`
- `scripts/compare_d7_retrieval.py`
- `tests/test_d7_comparison_protocol.py`
- `tests/test_d7_comparison_guard.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Write failing tests for protocol metric-criteria validation and guarded
   comparison output.
2. Add D7 metric-criterion models, validation, and evaluation helpers.
3. Add validator CLI count output and guarded comparison report integration.
4. Update docs with the criteria/accounting caveat.
5. Run focused tests, focused Ruff, docs checks, and full `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_comparison_protocol.py` | `test_validate_d7_comparison_protocol_accepts_metric_criteria` | Valid structured criteria are accepted and validator CLI reports the count. |
| `tests/test_d7_comparison_protocol.py` | `test_validate_d7_comparison_protocol_rejects_unknown_metric_criterion_baseline` | Criteria must target expected baselines. |
| `tests/test_d7_comparison_protocol.py` | `test_validate_d7_comparison_protocol_rejects_duplicate_metric_criteria` | Criterion IDs are unique. |
| `tests/test_d7_comparison_protocol.py` | `test_validate_d7_comparison_protocol_rejects_invalid_metric_threshold` | Threshold/operator validation fails loud. |
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_guard_includes_metric_criteria_results` | Guarded comparison output includes pass/fail criteria accounting. |
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_guard_reports_missing_metric_criteria` | Missing metrics produce explicit failed criteria rows. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d7_comparison_protocol.py tests/test_d7_comparison_guard.py -q` | New protocol/guard behavior. |
| `python -m ruff check qc_clean/core/d7_comparison_protocol.py scripts/validate_d7_comparison_protocol.py scripts/compare_d7_retrieval.py tests/test_d7_comparison_protocol.py tests/test_d7_comparison_guard.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] D7 comparison protocol JSON can include structured metric criteria while
  existing no-criteria protocols remain valid.
- [ ] Protocol validation rejects duplicate criterion IDs, unknown baselines,
  invalid operators, out-of-range exact/span-IoU thresholds, and empty rationale.
- [ ] Guarded D7 comparison reports include a criteria evaluation section when
  the supplied protocol has `metric_criteria`.
- [ ] Criteria results include overall status, per-criterion pass/fail/missing
  status, observed values when available, and the pre-registered threshold.
- [ ] Missing metrics fail explicitly.
- [ ] Exact D7 TP/FP/FN, baseline deltas, span-overlap diagnostics, and preflight
  pass/fail behavior remain unchanged except for the additive criteria section.
- [ ] Docs state structured criteria are protocol/accounting only, not held-out
  D7 evidence, superiority evidence, methodological-validity evidence, or SOTA.

> Process criteria:
- [ ] TDD red state observed for at least one new protocol/guard test before
  implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Plan is moved to completed with verification evidence.
- [ ] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Existing protocol fixtures fail validation | Optional field default or validator is not backward-compatible | Restore default `metric_criteria=[]` and avoid requiring it for schema v1. |
| Criteria pass when a metric is absent | Missing metric lookup incorrectly treated as zero or falsey success | Emit `status="missing"` for that row and make overall status fail. |
| Criteria change D7 exact scores | Integration touched scoring instead of post-score accounting | Keep evaluation helper read-only over the comparison report. |
| Span-overlap criteria are misleading | Criteria target diagnostic metrics without caveat | Keep metric names explicit and docs label them diagnostic-only. |
| Full gate fails outside touched files | Inspect failing output; fix only related regressions, otherwise record as pre-existing if proven unrelated. |
