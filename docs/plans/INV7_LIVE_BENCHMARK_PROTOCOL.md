# Plan #109: INV-7 Live Benchmark Protocol

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** INV-7 live fixture runner; INV-7 live fixture prompt hashes
**Blocks:** committed/scored live adversarial prompt-injection benchmark protocol

---

## Gap

**Current:** Live INV-7 fixture outputs can include exact fixture prompt hashes
and the versioned result package can validate those hashes. There is still no
pre-run protocol artifact that records the intended fixture set, model, trace
budget, prompt hashes, split, freeze/contamination posture, and success criteria
before a live prompt-injection run is executed or scored.

**Target:** Add a versioned live INV-7 protocol package validator:

- Core: `qc_clean/core/inv7_live_protocol.py`
- Script: `scripts/validate_inv7_live_protocol.py`
- Make target: `make validate-inv7-live-protocol PROTOCOL=protocol.json`
- Protocol package fields:
  - `schema_version=1`, `package_type="inv7_live_protocol"`;
  - `protocol_id`, `dataset_name`, `split`;
  - `fixture_set_id`, `fixture_set_version`, `fixture_prompt_hashes`;
  - `model`, `trace_id`, `max_budget`;
  - `prompt_frozen`, `contamination_checked`, `registered_before_run`;
  - `success_criteria` over metrics such as `attack_success_rate` or
    `failed_fixture_count`;
  - caution text that this is protocol/provenance metadata only.
- Validation rules:
  - non-empty identifiers and fixture set metadata;
  - prompt hashes are lowercase 64-character SHA-256 and fixture IDs non-empty;
  - `max_budget > 0`;
  - at least one success criterion with non-empty metric and pass condition;
  - for `split="held_out"`, require `prompt_frozen`,
    `contamination_checked`, and `registered_before_run`.

**Why:** A live result package with prompt hashes is only half the audit trail.
The protocol says what was supposed to be run and what counts as a pass before
seeing results.

---

## References Reviewed

- `qc_clean/core/adjudication_protocol.py` - pre-registration package pattern.
- `qc_clean/core/inv7_package.py` - live result package metadata.
- `qc_clean/core/inv7_fixtures.py` - live prompt hashes and runner output.
- `scripts/validate_inv7_prompt_injection_package.py` - script output pattern.
- `tests/test_adjudication_protocol.py` - protocol validator test pattern.
- `tests/test_inv7_prompt_injection_package.py` - INV-7 package fixtures.
- `docs/PROJECT_THEORY_AND_GOALS.md` - committed/scored live benchmark gap.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research required. This is deterministic protocol/provenance
infrastructure over existing INV-7 live fixture contracts.

---

## Capabilities

Internal protocol validation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_inv7_live_protocol` | schema_version=1 live protocol JSON | protocol package or validation error | qualitative_coding | agents/operators running live INV-7 canaries | free |

### Capability Validation

- [ ] Valid held-out protocol package validates.
- [ ] Held-out protocols require freeze, contamination check, and registration.
- [ ] Prompt hash maps reject malformed hashes and empty fixture IDs.
- [ ] Success criteria are required and non-empty.
- [ ] CLI/Make target emit machine-readable validation output.

---

## Files Affected

- `qc_clean/core/inv7_live_protocol.py` (create)
- `scripts/validate_inv7_live_protocol.py` (create)
- `tests/test_inv7_live_protocol.py` (create)
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

1. Add TDD tests for valid protocol, held-out requirements, bad hashes, missing
   criteria, and script JSON output.
2. Implement `qc_clean/core/inv7_live_protocol.py`.
3. Add validation script and Make target.
4. Update docs to state this is pre-run protocol metadata only.
5. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_inv7_live_protocol.py` | `test_validate_inv7_live_protocol_accepts_held_out_package` | Valid held-out protocol package validates. |
| `tests/test_inv7_live_protocol.py` | `test_validate_inv7_live_protocol_requires_held_out_freeze_contamination_registration` | Held-out safeguards fail loud. |
| `tests/test_inv7_live_protocol.py` | `test_validate_inv7_live_protocol_rejects_bad_prompt_hashes` | Malformed prompt hashes fail loud. |
| `tests/test_inv7_live_protocol.py` | `test_validate_inv7_live_protocol_requires_success_criteria` | Criteria are required. |
| `tests/test_inv7_live_protocol.py` | `test_validate_inv7_live_protocol_script_outputs_json` | Script emits valid/invalid JSON and exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py` | Live runner/result package contracts remain unchanged. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `validate_inv7_live_protocol_payload` accepts a valid schema_version=1
  held-out protocol.
- [ ] Held-out protocols require `prompt_frozen=true`,
  `contamination_checked=true`, and `registered_before_run=true`.
- [ ] Protocol prompt hashes must be lowercase SHA-256 digests keyed by non-empty
  fixture IDs.
- [ ] Success criteria are required and non-empty.
- [ ] `make validate-inv7-live-protocol PROTOCOL=...` is discoverable and
  dry-runs correctly.
- [ ] Docs state the protocol is pre-run provenance metadata only, not a live
  result or robustness evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should live result packages be preflighted against this protocol? —
  Status: DEFERRED | Why it matters: this slice validates the protocol package.
  A follow-up can compare actual result package model/trace/budget/fixture hashes
  and success criteria against the registered protocol.

---

## Notes

This records intended live benchmark conditions before a run. It does not run a
model, score a result, or prove prompt-injection robustness.
