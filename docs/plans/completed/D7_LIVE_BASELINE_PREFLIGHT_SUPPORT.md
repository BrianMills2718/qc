# Plan #135: D7 Live Baseline Preflight Support

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #134 live D7 baseline package shape
**Blocks:** Guarded D7 comparisons that include opt-in live baseline packages

---

## Gap

**Current:** `make compare-d7-retrieval ... PROTOCOL=...` can enforce a
registered D7 comparison protocol before scoring retrieval prediction packages.
Plan #134 added opt-in live candidate-selection baseline packages, but the
preflight still validates only `D7RetrievalBaselinePackage`, so live packages
can be scored only through unguarded `BASELINES=` / comparison paths.

**Target:** Extend the D7 comparison protocol/preflight guard so it can validate
both existing retrieval packages and new live candidate-selection baseline
packages.

**Why:** The D7 roadmap needs held-out D7 comparisons with live baselines. A
live-baseline package generator is less useful if guarded comparisons cannot
pre-register and enforce its model, trace, budget, retrieval config, and file
hash metadata.

---

## References Reviewed

- `qc_clean/core/d7_comparison_protocol.py` - expected prediction metadata.
- `qc_clean/core/d7_comparison_preflight.py` - current retrieval-only
  prediction validation and metadata checks.
- `qc_clean/core/d7_live_baseline.py` - live package metadata shape.
- `scripts/compare_d7_retrieval.py` - guarded comparison script boundary.
- `tests/test_d7_comparison_preflight.py` and
  `tests/test_d7_comparison_guard.py` - existing guard coverage.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Scope And Non-Goals

This plan only updates protocol/preflight validation for live baseline
packages. It does not run a live baseline, populate held-out D7 gold, or claim
methodological validity/superiority.

Existing retrieval protocol JSON must remain valid without adding new fields.
The new live fields are opt-in for expected live baseline packages.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `d7_comparison_preflight_live_baseline` | D7 comparison protocol + D7 gold + retrieval/live prediction packages | pass/fail preflight report | qualitative_coding | `compare-d7-retrieval` guarded comparisons | free |

### Capability Validation

- [x] Existing retrieval protocol packages remain valid with no schema changes
  required.
- [x] Protocol expectations can declare `baseline_mode="live_candidate_selector"`
  and `model=<model>`.
- [x] Preflight accepts a matching live candidate-selection package.
- [x] Preflight rejects live package model/metadata mismatches.
- [x] Guarded comparison script can include a live package and a passing
  preflight report.

---

## Files Affected

- `qc_clean/core/d7_comparison_protocol.py` (modify)
- `qc_clean/core/d7_comparison_preflight.py` (modify)
- `tests/test_d7_comparison_preflight.py` (modify)
- `tests/test_d7_comparison_guard.py` (modify)
- `docs/EVALUATION_HARNESS.md` and `CLAUDE.md` (docs/update)
- `AGENTS.md` (regenerate)
- `docs/plans/CLAUDE.md` and `docs/plans/ACTIVE_SPRINT.md` (plan tracking)

---

## Plan

### Steps

1. Commit this plan and mark it active.
2. Add TDD tests for live package protocol acceptance, live model mismatch
   rejection, and guarded comparison script output with a live package.
3. Extend `D7ExpectedRetrievalPrediction` with backward-compatible
   `baseline_mode` and `model` fields.
4. Normalize retrieval and live prediction package metadata inside preflight so
   shared checks apply consistently.
5. Update docs to state D7 comparison preflight can now guard live baseline
   packages, while preserving evidence caveats.
6. Run focused tests, focused Ruff, `make docs-check`, and full `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_comparison_preflight.py` | `test_d7_comparison_preflight_accepts_live_candidate_baseline_package` | A protocol with `baseline_mode="live_candidate_selector"` accepts a matching live package. |
| `tests/test_d7_comparison_preflight.py` | `test_d7_comparison_preflight_rejects_live_model_mismatch` | Live package model drift fails preflight. |
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_guard_accepts_live_baseline_package` | Script-level guarded comparison can score a live package and include a passing preflight report. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d7_comparison_preflight.py tests/test_d7_comparison_guard.py -q` | D7 comparison preflight/guard behavior. |
| `python -m pytest tests/test_d7_live_baseline.py tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py -q` | Live baseline package producer remains compatible. |
| `python -m ruff check qc_clean/core/d7_comparison_protocol.py qc_clean/core/d7_comparison_preflight.py tests/test_d7_comparison_preflight.py tests/test_d7_comparison_guard.py` | Focused lint on changed files. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Retrieval comparison protocols without `baseline_mode` still validate and
  behave as retrieval expectations.
- [x] Live baseline expectations can specify `baseline_mode`,
  `retrieval_mode`, `candidates_per_claim`, `max_targets`, `model`,
  `trace_id`, `max_budget`, and optional file hash.
- [x] Preflight accepts matching live baseline packages and rejects mismatched
  live model metadata.
- [x] Guarded comparison script can include a live baseline prediction package.
- [x] Docs preserve that this is guard/provenance infrastructure, not a
  committed held-out D7 result or superiority claim.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Outcome

Implemented and pushed as `1ab03b5`
(`[Plan: D7_LIVE_BASELINE_PREFLIGHT_SUPPORT] Guard live D7 baselines`).

Verification evidence:

- TDD red:
  `python -m pytest tests/test_d7_comparison_preflight.py tests/test_d7_comparison_guard.py -q`
  initially failed because live baseline packages were rejected as invalid D7
  retrieval prediction packages and the guarded script blocked before writing
  output (`3 failed, 8 passed`).
- Focused preflight/guard tests:
  `python -m pytest tests/test_d7_comparison_preflight.py tests/test_d7_comparison_guard.py -q`
  passed (`11 passed`).
- Live baseline producer tests:
  `python -m pytest tests/test_d7_live_baseline.py tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py -q`
  passed (`6 passed`).
- Combined focused tests:
  `python -m pytest tests/test_d7_comparison_preflight.py tests/test_d7_comparison_guard.py tests/test_d7_live_baseline.py tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py -q`
  passed (`17 passed`).
- Focused Ruff:
  `python -m ruff check qc_clean/core/d7_comparison_protocol.py qc_clean/core/d7_comparison_preflight.py tests/test_d7_comparison_preflight.py tests/test_d7_comparison_guard.py`
  passed.
- Docs gate: `make docs-check` passed.
- Full gate: `make check` passed (`1032 passed, 1 skipped, 8 deselected`);
  Ruff and docs checks passed inside the gate.
- Type check remains not configured in this repo, as reported by `make check`.

---

## Notes

This plan makes live baseline outputs usable in registered D7 comparison
preflight, but still does not produce a populated benchmark.
