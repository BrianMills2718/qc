# Plan #110: INV-7 Live Protocol Result Preflight

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** INV-7 live benchmark protocol; INV-7 prompt-injection package
**Blocks:** safer live INV-7 benchmark package scoring

---

## Gap

**Current:** The repo can validate a pre-run INV-7 live protocol and validate a
live result package with prompt hashes. There is no single gate that checks a
concrete live result package matches the registered protocol before the package
is supplied to `make bench PROMPT_INJECTION=...`.

**Target:** Add a protocol-to-result preflight:

- Core: `qc_clean/core/inv7_live_preflight.py`
- Script: `scripts/preflight_inv7_live_package.py`
- Make target: `make inv7-live-preflight PROTOCOL=protocol.json PACKAGE=inv7.json`
- Checks:
  - protocol validation passes;
  - result package validation passes;
  - result package mode is `live_model`;
  - split, fixture set ID/version, model, trace ID, prompt freeze flag, and
    contamination flag match;
  - result package `max_budget` does not exceed the protocol budget;
  - result package fixture prompt hashes exactly match the protocol hashes.
- Output is a machine-readable pass/fail report with the caveat that preflight
  is process/provenance metadata only.

**Why:** Protocol validation alone and result validation alone do not prove that
the result package was produced under the intended protocol. This closes the
deterministic handoff gap before scoring live INV-7 results.

---

## References Reviewed

- `qc_clean/core/inv7_live_protocol.py` - pre-run protocol package validator.
- `qc_clean/core/inv7_package.py` - result package validator.
- `scripts/validate_inv7_live_protocol.py` - protocol script output.
- `scripts/validate_inv7_prompt_injection_package.py` - result package script.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-7 committed/scored live benchmark gap.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research required. This is deterministic cross-package preflight
over existing protocol/result contracts.

---

## Capabilities

Internal preflight capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `preflight_inv7_live_package` | live protocol package + live result package | preflight report | qualitative_coding | agents/operators scoring live INV-7 packages | free |

### Capability Validation

- [ ] Matching protocol/result packages pass.
- [ ] Result validation failures block preflight.
- [ ] Metadata mismatches fail loud.
- [ ] Prompt hash mismatches fail loud.
- [ ] CLI/Make target emit machine-readable pass/fail output.

---

## Files Affected

- `qc_clean/core/inv7_live_preflight.py` (create)
- `scripts/preflight_inv7_live_package.py` (create)
- `tests/test_inv7_live_preflight.py` (create)
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

1. Add TDD tests for pass, protocol/package validation failure, metadata
   mismatch, prompt hash mismatch, and script JSON output.
2. Implement `qc_clean/core/inv7_live_preflight.py`.
3. Add script and Make target.
4. Update docs to state this is provenance/process metadata only.
5. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_inv7_live_preflight.py` | `test_inv7_live_preflight_accepts_matching_protocol_and_package` | Matching protocol/result package passes. |
| `tests/test_inv7_live_preflight.py` | `test_inv7_live_preflight_rejects_metadata_mismatch` | Model/fixture metadata mismatches fail. |
| `tests/test_inv7_live_preflight.py` | `test_inv7_live_preflight_rejects_prompt_hash_mismatch` | Prompt hash mismatch fails. |
| `tests/test_inv7_live_preflight.py` | `test_inv7_live_preflight_rejects_non_live_result_package` | Non-live result package fails. |
| `tests/test_inv7_live_preflight.py` | `test_inv7_live_preflight_script_outputs_json` | CLI emits valid/invalid JSON with exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_inv7_live_protocol.py tests/test_inv7_prompt_injection_package.py` | Upstream package contracts remain unchanged. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Matching protocol/live result package passes preflight.
- [ ] Protocol/result schema failures block preflight.
- [ ] Split, fixture set, model, trace ID, freeze, contamination, and budget
  mismatches fail loud.
- [ ] Prompt hash mismatch fails loud.
- [ ] `make inv7-live-preflight PROTOCOL=... PACKAGE=...` is discoverable and
  dry-runs correctly.
- [ ] Docs state this is process/provenance metadata only, not prompt-injection
  robustness evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should preflight evaluate success criteria automatically? — Status:
  DEFERRED | Why it matters: criteria are human-readable today. A follow-up can
  add structured criteria if the live benchmark protocol needs automatic pass/
  fail decisions beyond package matching.

---

## Notes

This preflight proves files line up. It does not run a model, score a benchmark,
or prove prompt-injection robustness.
