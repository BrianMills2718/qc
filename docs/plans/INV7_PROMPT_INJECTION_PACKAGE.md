# Plan #84: INV-7 Prompt-Injection Package

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** INV-7 fixture runner scaffold; INV-7 live fixture runner
**Blocks:** committed live adversarial prompt-injection benchmark protocol

---

## Gap

**Current:** `make run-inv7-fixtures` and `make run-inv7-live-fixtures` emit
scorecard-compatible JSON with `prompt_injection_evaluations`, and `make bench
PROMPT_INJECTION=...` can score that list. The result file has no validated
package-level protocol contract: no required package ID, split, fixture-set ID,
fixture-set version, prompt-freeze flag, contamination-check flag, or validator
target. That makes it too easy to treat an ad hoc canary run like a committed
benchmark.

**Target:** Add a schema_version=1 INV-7 prompt-injection package contract and
validator. The existing structural and live runners should emit the package
metadata while preserving the existing `prompt_injection_evaluations` list for
Phase 0 scoring. `make bench PROMPT_INJECTION=...` should accept the versioned
package by extracting the same list. `make validate-inv7-package PACKAGE=...`
should validate package invariants and emit a compact JSON summary.

**Why:** INV-7 needs a committed live adversarial benchmark protocol before any
prompt-injection robustness claim is credible. A versioned package does not
create robustness evidence by itself, but it gives agents a fail-loud protocol
boundary for future live runs and prevents unstructured canary files from being
mistaken for stronger evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:360` and §18 item 6 - INV-7 remains partial; committed/scored live adversarial benchmark protocol is still missing.
- `docs/EVALUATION_HARNESS.md:60` - current INV-7 fixture scorecard caveats.
- `qc_clean/core/inv7_fixtures.py` - existing structural and live fixture runners.
- `scripts/run_inv7_fixtures.py` and `scripts/run_inv7_live_fixtures.py` - current runner CLIs.
- `scripts/bench_phase0.py` - current `PROMPT_INJECTION=` loader.
- `qc_clean/core/d3_gold.py`, `qc_clean/core/d7_gold.py`, `scripts/validate_d3_gold_set.py`, and `scripts/validate_d7_gold_set.py` - versioned package and validator patterns.
- `tests/test_inv7_fixture_runner.py` and `tests/test_bench_phase0_script.py` - current INV-7 runner and scorecard coverage.
- Memory context: not retried because `agent-memory recall` has repeatedly failed with provider 402/403 in this long-running session; circuit breaker remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
package/protocol scaffold around existing INV-7 fixture outputs, not an external
benchmark study.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_inv7_prompt_injection_package` | schema_version=1 INV-7 package JSON | typed package or JSON validation error | qualitative_coding | agents, Phase 0 benchmark workflows | free |

### Capability Validation

- [ ] Input/output schemas defined with Pydantic models and field descriptions.
- [ ] Agent-facing CLI and Makefile target exist.
- [ ] Phase 0 `PROMPT_INJECTION=` accepts validated package files without mutating project state.

---

## Files Affected

- `qc_clean/core/inv7_package.py` (create)
- `qc_clean/core/inv7_fixtures.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `scripts/validate_inv7_prompt_injection_package.py` (create)
- `Makefile` (modify)
- `tests/test_inv7_prompt_injection_package.py` (create)
- `tests/test_inv7_fixture_runner.py` (modify)
- `tests/test_bench_phase0_script.py` (modify if package loader coverage is best placed there)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV7_PROMPT_INJECTION_PACKAGE.md` (create, then move to completed)

---

## Plan

### Steps

1. Add Pydantic package models for INV-7 fixture outcomes and a
   schema_version=1 prompt-injection package.
2. Enforce package-level invariants: non-empty package and fixture-set IDs,
   supported split, at least one evaluation, unique fixture IDs, and live-model
   fields (`model`, `trace_id`, `max_budget`) when `mode="live_model"`.
3. Add loader/helpers that validate versioned packages and return the existing
   `prompt_injection_evaluations` list for Phase 0 scoring.
4. Add a validation script and `make validate-inv7-package PACKAGE=...`.
5. Update structural and live fixture runners to emit package metadata while
   preserving existing scorecard-compatible fields.
6. Add tests for valid package validation, invalid package failures, duplicate
   fixture IDs, runner package metadata, and Phase 0 package-file scoring.
7. Update docs conservatively: the package is protocol/provenance structure,
   not prompt-injection robustness evidence.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_inv7_prompt_injection_package.py` | `test_valid_live_inv7_package_validates` | A schema_version=1 live package with required protocol metadata validates. |
| `tests/test_inv7_prompt_injection_package.py` | `test_live_inv7_package_requires_model_metadata` | Live packages fail loudly without model/trace/budget metadata. |
| `tests/test_inv7_prompt_injection_package.py` | `test_inv7_package_rejects_duplicate_fixture_ids` | Duplicate fixture IDs cannot be packaged. |
| `tests/test_inv7_prompt_injection_package.py` | `test_validate_inv7_package_script_emits_summary` | Agent-facing validator emits compact JSON success metadata. |
| `tests/test_bench_phase0_script.py` | package loader test | `PROMPT_INJECTION=` accepts schema_version=1 packages without mutating state. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py -q` | INV-7 runner/package behavior. |
| `python -m pytest tests/test_bench_phase0_script.py -k "prompt_injection" -q` | Phase 0 external-file behavior remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Versioned INV-7 prompt-injection package model exists.
- [x] Structural and live INV-7 fixture runners emit package metadata.
- [x] Invalid live package metadata fails loudly.
- [x] Duplicate fixture IDs fail loudly.
- [x] `make validate-inv7-package PACKAGE=...` validates packages.
- [x] `make bench PROMPT_INJECTION=...` accepts the versioned package shape.
- [x] Docs state the package is protocol/provenance only, not robustness evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Verification

- Initial TDD run: `python -m pytest tests/test_inv7_prompt_injection_package.py tests/test_inv7_fixture_runner.py -q` failed during collection with `ModuleNotFoundError: No module named 'qc_clean.core.inv7_package'`.
- `python -m pytest tests/test_inv7_prompt_injection_package.py tests/test_inv7_fixture_runner.py -q` - `10 passed`.
- `python -m pytest tests/test_bench_phase0_script.py -k "prompt_injection" -q` - `2 passed, 26 deselected`.
- `python -m pytest tests/test_inv7_prompt_injection_package.py tests/test_inv7_fixture_runner.py tests/test_bench_phase0_script.py -k "prompt_injection or inv7" -q` - `13 passed, 25 deselected`.
- `python -m ruff check qc_clean/core/inv7_package.py qc_clean/core/inv7_fixtures.py scripts/bench_phase0.py scripts/validate_inv7_prompt_injection_package.py tests/test_inv7_prompt_injection_package.py tests/test_inv7_fixture_runner.py tests/test_bench_phase0_script.py` - passed.
- `python scripts/check_markdown_links.py && python scripts/sync_plan_status.py --check && python scripts/meta/check_agents_sync.py --check` - passed.
- `make -n validate-inv7-package PACKAGE=inv7.json` - resolved to `python scripts/validate_inv7_prompt_injection_package.py inv7.json`.
- `make check` - `812 passed, 1 skipped, 8 deselected`; Ruff and docs checks passed; type check is not yet configured.

---

## Open Questions

- [ ] What fixture set should become the first committed live adversarial benchmark? - Status: DEFERRED | Why it matters: this package scaffold can validate a run, but selecting and scoring the committed benchmark is a separate evaluation decision.
- [ ] Should held-out INV-7 packages require second-model adjudication of responses in addition to canary matching? - Status: DEFERRED | Why it matters: canary matching is cheap and deterministic, but it can miss semantic obedience failures.

---

## Notes

This plan must not upgrade INV-7 from PARTIAL. It creates a protocol container
and validator for future live runs; it does not run or score a committed live
benchmark.
