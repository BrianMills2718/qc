# Plan #175: D3 Baseline Comparison Protocol

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** D3 gold-set packages, D3 baseline packages, D3 baseline
scorecard diagnostics
**Blocks:** D3 comparison preflight and eventual score-time guard for held-out
baseline comparisons

---

## Outcome

Implemented and pushed in `c46f94e`
(`[Plan: D3_BASELINE_COMPARISON_PROTOCOL] Add D3 comparison protocol
validator`). The repo now has a schema_version=1 D3 baseline comparison
protocol contract, a JSON-emitting validator script, and
`make validate-d3-comparison-protocol PROTOCOL=...`. The protocol can register
expected D3 baselines, held-out freeze/provenance flags, hash locks, success
criteria, and optional exact/span metric criteria. D3 comparison preflight,
score-time enforcement, and criteria evaluation against scorecard output remain
deferred follow-up lanes.

Verification:

- TDD red state observed: `python -m pytest tests/test_d3_comparison_protocol.py -q`
  failed during collection because `qc_clean.core.d3_comparison_protocol` did
  not exist.
- `python -m pytest tests/test_d3_comparison_protocol.py -q` passed: 9 passed.
- `python -m pytest tests/test_d3_comparison_protocol.py tests/test_d3_baseline_package.py tests/test_bench_phase0.py -k "d3" -q`
  passed: 26 passed, 64 deselected.
- `python -m ruff check qc_clean/core/d3_comparison_protocol.py scripts/validate_d3_comparison_protocol.py tests/test_d3_comparison_protocol.py`
  passed.
- `make -n validate-d3-comparison-protocol PROTOCOL=protocol.json` showed
  `python scripts/validate_d3_comparison_protocol.py protocol.json`.
- `make docs-check` passed.
- `git diff --check` passed.
- `make check` passed: 1160 passed, 1 skipped, 8 deselected; Ruff and
  docs-check passed; type check is not configured.

Claim discipline: this is protocol/provenance metadata only. It does not run or
preflight baseline packages, enforce score-time guards, populate held-out D3
evidence, establish expert parity, demonstrate superiority/non-inferiority,
prove methodological validity, or support any SOTA claim.

---

## Gap

**Current:** D3 has versioned gold-set packages, versioned baseline prediction
packages, and local Phase 0 scoring for `D3_GOLD=` + `D3_BASELINES=`, including
exact metrics, local paired deltas, and per-baseline span-overlap diagnostics.
Unlike D7, D3 does not yet have a pre-registered comparison protocol package
that records the intended gold set, split, expected baselines, prompt/model
freeze flags, hash locks, success criteria, or optional machine-checkable metric
criteria before comparison inputs are scored.

**Target:** Add a schema_version=1 D3 baseline comparison protocol validator:

- New core module `qc_clean/core/d3_comparison_protocol.py`.
- New script `scripts/validate_d3_comparison_protocol.py`.
- New Make target `validate-d3-comparison-protocol PROTOCOL=protocol.json`.
- Protocol package type:
  `qualitative_coding.d3_application_baseline_comparison_protocol`.
- Required provenance fields: protocol/project/dataset/split/gold IDs,
  corpus SHA-256, optional project-state SHA-256, prompt-frozen,
  contamination-checked, registered-before-run, expected baseline predictions,
  success criteria, and caution.
- Optional structured metric criteria for exact and local span-overlap metrics,
  validated against expected baseline names and metric-specific threshold
  ranges.

**Non-target:** This slice does not add D3 comparison preflight, `make bench
D3_PROTOCOL=...`, `qc_cli.py bench` forwarding, or metric-criteria evaluation
against scorecard output. Those become concrete follow-up lanes after the
protocol contract is stable.

**Why:** Future held-out D3 baseline comparisons need the same pre-registration
discipline now available for D7 comparisons. The protocol validator is a small
deterministic first step: it constrains what later preflight and score-time
guards will enforce without claiming any held-out result or superiority.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D3 baseline comparisons are a local substrate;
  actual/live held-out baseline runs remain future benchmark work.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-3 remains partial; no expert labels
  or held-out D3 correctness estimate exists.
- `qc_clean/core/d3_gold.py` - versioned D3 gold-set package metadata.
- `qc_clean/core/d3_baseline_package.py` - versioned D3 baseline prediction
  package metadata.
- `qc_clean/core/d7_comparison_protocol.py` and
  `scripts/validate_d7_comparison_protocol.py` - analogous comparison protocol
  pattern, including optional metric criteria.
- Coordination/memory check: no active claim files; `agent-memory recall
  'D3 comparison protocol baseline active decisions' --project qualitative_coding`
  returned only low-relevance historical completed-task summaries.

---

## Research Basis For This Slice

No new external research. This is a deterministic protocol/provenance parity
slice based on existing D3 package shapes and the D7 comparison protocol
pattern.

---

## Capabilities

Protocol validation only; no scorecard or cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_d3_comparison_protocol` | schema_version=1 D3 comparison protocol JSON | valid/invalid JSON report and validated Pydantic object | qualitative_coding | agents/operators preparing D3 baseline comparisons | free |

### Capability Validation

- [x] Valid held-out D3 comparison protocol packages validate through core and
  script surfaces.
- [x] Held-out protocols require prompt/model freeze, contamination check,
  pre-run registration, and project-state hash.
- [x] Expected baseline names are non-empty and unique.
- [x] Optional file hash locks must be SHA-256.
- [x] Optional metric criteria validate duplicate IDs, unknown baseline names,
  supported operators, finite thresholds, metric-specific threshold ranges, and
  non-empty rationale.

---

## Files Affected

- `qc_clean/core/d3_comparison_protocol.py` (new)
- `scripts/validate_d3_comparison_protocol.py` (new)
- `tests/test_d3_comparison_protocol.py` (new)
- `Makefile`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Write failing tests for valid protocol validation, invalid held-out flags,
   duplicate expected baseline names, bad hashes, valid metric criteria, and
   invalid metric criteria.
2. Add `qc_clean/core/d3_comparison_protocol.py` with Pydantic contracts and a
   `load_d3_comparison_protocol()` helper.
3. Add `scripts/validate_d3_comparison_protocol.py` with machine-readable JSON
   success/failure output.
4. Add `make validate-d3-comparison-protocol PROTOCOL=...`.
5. Update docs with explicit caveats and deferred preflight/score-time guard.
6. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
7. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d3_comparison_protocol.py` | `test_validate_d3_comparison_protocol_accepts_held_out_package` | Valid protocol validates through core and script, with expected-baseline count in JSON. |
| `tests/test_d3_comparison_protocol.py` | `test_validate_d3_comparison_protocol_accepts_metric_criteria` | Optional structured metric criteria validate and script reports count. |
| `tests/test_d3_comparison_protocol.py` | invalid cases | Held-out flags, duplicate expected baselines, bad hashes, unknown criterion baselines, duplicate criterion IDs, invalid operators/thresholds/rationale fail loudly. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d3_comparison_protocol.py tests/test_d3_baseline_package.py tests/test_bench_phase0.py -k "d3" -q` | New protocol plus adjacent D3 package/scorecard behavior. |
| `python -m ruff check qc_clean/core/d3_comparison_protocol.py scripts/validate_d3_comparison_protocol.py tests/test_d3_comparison_protocol.py` | Focused lint. |
| `make -n validate-d3-comparison-protocol PROTOCOL=protocol.json` | Make target forwards to the canonical validator script. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `qc_clean/core/d3_comparison_protocol.py` validates schema_version=1 D3
  comparison protocol packages.
- [x] `scripts/validate_d3_comparison_protocol.py` emits JSON `valid` /
  `invalid` reports and exit codes.
- [x] `make validate-d3-comparison-protocol PROTOCOL=...` is available.
- [x] Held-out protocols require freeze/contamination/registration/project-state
  metadata.
- [x] Optional structured metric criteria are supported for exact and local
  span-overlap metrics.
- [x] Docs state this is protocol/provenance metadata only and does not run a
  baseline, compare packages, enforce score-time guards, prove held-out D3
  evidence, expert parity, superiority, methodological validity, or SOTA.

> Process criteria:
- [x] TDD red state observed before implementation.
- [x] Focused tests pass.
- [x] Focused Ruff check passes.
- [x] Make dry-run confirms target wiring.
- [x] `make docs-check` passes.
- [x] `make check` passes.
- [x] Plan is moved to completed with verification evidence.
- [x] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Protocol shape duplicates D7 retrieval-only fields | Copying D7 expected-prediction metadata too literally | Use D3 baseline package concepts: baseline name/mode/model/count/hash; do not require retrieval fields. |
| Validator accepts unregistered held-out protocols | Held-out invariant checks omitted | Require prompt_frozen, contamination_checked, registered_before_run, and project_state_sha256 for held_out. |
| Metric criteria allow nonsensical thresholds | No per-metric threshold validation | Treat recall/precision/F1/IoU as 0..1; Modified Hausdorff thresholds must be non-negative. |
| Script prints traceback instead of JSON | Exceptions not caught at CLI boundary | Catch `ValueError` and emit `{"status": "invalid", "error": ...}` with exit 1. |
| Docs imply evidence exists | Protocol wording drifts into benchmark claims | State explicitly that validation is process/provenance only and preflight/scoring are deferred. |
