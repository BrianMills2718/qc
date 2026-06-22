# Plan #104: Adjudication Protocol Sample Preflight

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Adjudication protocol package; INV-3 adjudication sample export
**Blocks:** safer human/expert labeling handoff; held-out adjudication run discipline

---

## Gap

**Current:** The repo can validate a pre-label adjudication protocol package and
can export an unlabeled adjudication sample package. These two artifacts are
validated independently. There is no agent-drivable preflight that proves a
specific sample package is the one governed by a specific protocol before humans
label it.

**Target:** Add a protocol-to-sample preflight:

- Core: `qc_clean/core/adjudication_preflight.py`
- Script: `scripts/preflight_adjudication_protocol_sample.py`
- Make target: `make adjudication-protocol-preflight PROTOCOL=protocol.json
  SAMPLE=sample.json`
- Checks:
  - protocol and sample packages both validate;
  - `project_id` and `corpus_sha256` match;
  - `project_state_sha256` matches when the protocol records one;
  - `sample_package_sha256` matches the concrete sample file when supplied;
  - every protocol `sampling_plan.target_item_types` has returned sample items;
  - returned sample count is at least `planned_sample_size`.
- Output is a machine-readable report with pass/fail status, counts, hashes, and
  the same caveat that preflight is process metadata, not validity evidence.

**Why:** INV-3 evidence depends on labels being collected under a declared
protocol over a declared sample. This closes a process gap between protocol
validation and response import without requiring human labels.

---

## References Reviewed

- `qc_clean/core/adjudication_protocol.py` - protocol package schema and held-out
  invariants.
- `qc_clean/core/adjudication_sample.py` - sample package schema, target types,
  item counts, and corpus/project hashes.
- `scripts/validate_adjudication_protocol.py` - validator script pattern.
- `scripts/validate_adjudication_responses.py` - machine-readable report pattern.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - current
  INV-3 claim-discipline language.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references. This is deterministic local
preflight over two existing package contracts.

---

## Capabilities

Internal preflight capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `preflight_adjudication_protocol_sample` | protocol file + sample file | preflight report | qualitative_coding | agents, future labeling workflows | free |

### Capability Validation

- [ ] Protocol and sample payloads validate before cross-checks.
- [ ] Hash/project mismatches fail loudly.
- [ ] Required target-type coverage and planned sample size are tested.
- [ ] CLI emits machine-readable JSON.

---

## Files Affected

- `qc_clean/core/adjudication_preflight.py` (create)
- `scripts/preflight_adjudication_protocol_sample.py` (create)
- `tests/test_adjudication_preflight.py` (create)
- `Makefile` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify after closeout)

---

## Plan

### Steps

1. Write TDD tests for pass, project/hash mismatch, sample file hash mismatch,
   missing target type, undersized sample, and script JSON output.
2. Implement `qc_clean/core/adjudication_preflight.py` with report models and
   cross-check helpers.
3. Add script and Make target.
4. Update docs to state this is a handoff/process preflight, not evidence.
5. Run focused tests, focused Ruff, docs checks, and full `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_adjudication_preflight.py` | `test_preflight_accepts_matching_protocol_and_sample` | Matching protocol/sample passes with counts and hashes. |
| `tests/test_adjudication_preflight.py` | `test_preflight_rejects_project_or_corpus_mismatch` | Mismatched project/corpus fails loudly. |
| `tests/test_adjudication_preflight.py` | `test_preflight_rejects_sample_file_hash_mismatch` | Protocol sample hash must match the concrete file when supplied. |
| `tests/test_adjudication_preflight.py` | `test_preflight_rejects_missing_required_target_type` | Required target types must have returned items. |
| `tests/test_adjudication_preflight.py` | `test_preflight_rejects_undersized_sample` | Sample returned count must meet planned sample size. |
| `tests/test_adjudication_preflight.py` | `test_preflight_script_outputs_json` | CLI emits valid/invalid machine-readable JSON with exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_adjudication_protocol.py tests/test_adjudication_sample.py` | Source package contracts stay unchanged. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Matching protocol/sample package pair passes preflight.
- [ ] Project, corpus, project-state, and optional sample-file hash mismatches
  fail loudly.
- [ ] Missing required target types fail loudly.
- [ ] Sample count below planned sample size fails loudly.
- [ ] `make adjudication-protocol-preflight PROTOCOL=... SAMPLE=...` is
  discoverable.
- [ ] Docs state preflight is process/provenance metadata only, not labels or
  evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should preflight require exact target-type counts by type, not just total
  planned sample size? — Status: DEFERRED | Why it matters: the current protocol
  package records one total sample size; per-type quotas need an explicit schema
  extension.

---

## Notes

This preflight is meant to run before the sample leaves the repo for human
labeling. It prevents common artifact-mismatch errors, but it still does not
create labels or evaluate correctness.
