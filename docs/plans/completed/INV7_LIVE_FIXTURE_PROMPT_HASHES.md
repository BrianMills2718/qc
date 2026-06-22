# Plan #108: INV-7 Live Fixture Prompt Hashes

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** INV-7 live fixture runner; INV-7 prompt-injection package
**Blocks:** auditable committed live adversarial injection benchmark results

---

## Outcome

Implemented and pushed in commit `196103f`:

- `run_inv7_live_fixtures_async(...)` now emits `fixture_prompt_hashes` keyed by
  fixture ID.
- Hashes are SHA-256 over the exact prompt string passed to the live model
  caller.
- `Inv7PromptInjectionPackage` accepts optional `fixture_prompt_hashes`.
- Package validation rejects hash key mismatches and malformed hash values when
  the map is present.
- Legacy packages without `fixture_prompt_hashes` remain valid.
- Docs now describe live prompt hashes as provenance only, not prompt-injection
  robustness evidence.

Verification:

- `python -m pytest tests/test_inv7_fixture_runner.py
  tests/test_inv7_prompt_injection_package.py -q` failed before implementation
  on the new prompt-hash expectations, as expected.
- `python -m pytest tests/test_inv7_fixture_runner.py
  tests/test_inv7_prompt_injection_package.py tests/test_bench_phase0.py
  tests/test_bench_phase0_script.py -q` -> 102 passed.
- `python -m ruff check qc_clean/core/inv7_fixtures.py
  qc_clean/core/inv7_package.py tests/test_inv7_fixture_runner.py
  tests/test_inv7_prompt_injection_package.py` -> passed.
- `make docs-check` -> passed.
- `make check` -> 918 passed, 1 skipped, 8 deselected; Ruff/docs green; type
  check not yet configured.

---

## Gap

**Current:** `make run-inv7-live-fixtures` can run live canary fixtures and the
INV-7 package contract records model, trace ID, budget, fixture set, and outcome
metadata. It does not record stable hashes of the exact live prompts sent to the
model, so a later live result package cannot prove which adversarial prompt set
was run without storing the full prompts in the scorecard input.

**Target:** Add prompt-hash provenance for live INV-7 fixture packages:

- `run_inv7_live_fixtures_async(...)` emits `fixture_prompt_hashes`, mapping
  each fixture ID to the SHA-256 of the exact prompt sent to the model.
- `Inv7PromptInjectionPackage` accepts optional `fixture_prompt_hashes`.
- If `fixture_prompt_hashes` is present, package validation requires:
  - keys exactly match `prompt_injection_evaluations[*].fixture_id`;
  - each value is a lowercase 64-character SHA-256 hex digest.
- Existing packages without hashes remain accepted for backward compatibility.
- Docs state prompt hashes improve benchmark provenance only; they do not prove
  prompt-injection robustness or model obedience.

**Why:** Live prompt-injection results need reproducible prompt identity. Hashing
the exact prompts gives an audit handle without putting adversarial prompts or
potentially sensitive prompt contents into summary reports.

---

## References Reviewed

- `qc_clean/core/inv7_fixtures.py` - live fixture runner payload.
- `qc_clean/core/inv7_package.py` - versioned INV-7 package validation.
- `tests/test_inv7_fixture_runner.py` - live runner tests with fake model.
- `tests/test_inv7_prompt_injection_package.py` - package validation tests.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-7 live benchmark gap.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research required. This is deterministic provenance hardening over
the existing live fixture runner and package contract.

---

## Capabilities

Internal benchmark provenance only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `inv7_live_fixture_prompt_hashes` | live fixture prompts | fixture_id -> sha256(prompt) map | qualitative_coding | package validators, benchmark operators | free |

### Capability Validation

- [x] Live runner output includes a hash for every live fixture prompt.
- [x] Package validator accepts matching prompt hashes.
- [x] Package validator rejects extra/missing prompt hash keys.
- [x] Package validator rejects malformed prompt hashes.
- [x] Backward-compatible packages without prompt hashes still validate.

---

## Files Affected

- `qc_clean/core/inv7_fixtures.py` (modify)
- `qc_clean/core/inv7_package.py` (modify)
- `tests/test_inv7_fixture_runner.py` (modify)
- `tests/test_inv7_prompt_injection_package.py` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add TDD tests for live runner prompt hashes and package validation
   accept/reject cases.
2. Implement prompt hashing in `qc_clean/core/inv7_fixtures.py`.
3. Add optional `fixture_prompt_hashes` validation in
   `qc_clean/core/inv7_package.py`.
4. Update docs to mention live prompt-hash provenance without making robustness
   claims.
5. Run focused tests, focused Ruff, docs checks, and full `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Changed Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_inv7_fixture_runner.py` | `test_run_inv7_live_fixtures_records_prompt_hashes` | Live runner emits SHA-256 prompt hashes for every fixture. |
| `tests/test_inv7_prompt_injection_package.py` | `test_valid_live_inv7_package_validates` | Matching prompt hashes are accepted. |
| `tests/test_inv7_prompt_injection_package.py` | `test_live_inv7_package_rejects_prompt_hash_key_mismatch` | Missing/extra hash keys fail loud. |
| `tests/test_inv7_prompt_injection_package.py` | `test_live_inv7_package_rejects_malformed_prompt_hash` | Non-SHA-256 hash values fail loud. |
| `tests/test_inv7_prompt_injection_package.py` | existing valid package without hashes | Backward compatibility is preserved. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py` | INV-7 runner/package contracts remain green. |
| `tests/test_bench_phase0.py tests/test_bench_phase0_script.py` | Scorecard/package loading remains compatible. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Live runner emits `fixture_prompt_hashes` for every fixture.
- [x] Prompt hashes are SHA-256 over the exact prompt string sent to the model.
- [x] Versioned package validation accepts matching prompt hash maps.
- [x] Versioned package validation rejects hash key mismatches.
- [x] Versioned package validation rejects malformed hash values.
- [x] Existing INV-7 package inputs without prompt hashes remain valid.
- [x] Docs describe prompt hashes as provenance only, not robustness evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should structural fixtures also hash rendered prompts/contexts? — Status:
  DEFERRED | Why it matters: structural fixtures are deterministic and currently
  include direct boundary checks. Live prompt hashes are the higher-value
  provenance gap because model calls are costly and harder to reproduce.

---

## Notes

Prompt hashes identify what was sent. They do not establish that the model
obeyed the boundary instructions, that the fixture suite is exhaustive, or that
INV-7 is solved.
