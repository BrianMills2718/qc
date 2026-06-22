# Plan #137: Theoretical Sampling Protocol Preflight

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** #136
**Blocks:** Future theoretical-sampling result packages and score-time GT-fidelity provenance

---

## Gap

**Current:** INV-4 can validate pre-run theoretical-sampling protocol metadata,
and `suggest_next_documents()` can produce local diagnostic-driven suggestions
over already-loaded uncoded documents. There is no machine-readable preflight
that checks a registered protocol against a concrete candidate pool or selected
sampling-result package before operators treat the protocol as executed.

**Target:** Add a schema_version=1 theoretical-sampling preflight surface:

- `make theoretical-sampling-preflight PROTOCOL=protocol.json CANDIDATES=candidates.json [RESULTS=results.json]`
- `scripts/preflight_theoretical_sampling_protocol.py protocol.json --candidates-file candidates.json [--results-file results.json]`

**Why:** The roadmap explicitly lists "protocol preflight against concrete
candidate pools/results" as the next INV-4 gap after protocol validation. This
adds provenance and drift checks without claiming sampling adequacy or
methodological saturation.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - INV-4 roadmap now calls out
  protocol preflight against concrete candidate pools/results.
- `docs/EVALUATION_HARNESS.md` §2/§6 - protocol/result preflight pattern used
  across D4/D6/D8/D9/confidence.
- `qc_clean/core/theoretical_sampling_protocol.py` - existing protocol package
  contract.
- `qc_clean/core/pipeline/theoretical_sampling.py` - current loaded-document
  suggestion heuristic.
- `qc_clean/schemas/domain.py` - `SamplingSuggestion` domain shape.
- `qc_clean/core/d8_gt_fidelity_preflight.py` and
  `qc_clean/core/d6_bias_preflight.py` - local preflight report patterns.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Scope And Non-Goals

This plan validates package consistency only. It is not a sampling-frame
adequacy evaluation, not a recruitment/data-collection workflow, not saturation
evidence, not GT-fidelity evidence, and not a SOTA claim.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `preflight_theoretical_sampling_protocol` | protocol JSON + candidate package JSON + optional result package JSON | schema_version=1 preflight report | qualitative_coding | agents/operators planning INV-4 sampling runs | free |

### Capability Validation

- [ ] Candidate packages validate and are cross-checked against protocol ID,
  project ID, corpus hash, optional state hash, source policy, collection mode,
  candidate count, and target gap coverage.
- [ ] Optional result packages validate and selected candidate IDs are checked
  against the candidate pool and protocol target gaps.
- [ ] Script emits a machine-readable pass/fail report and exits nonzero on
  failed preflight.
- [ ] Make target exposes the preflight.

---

## Files Affected

- `qc_clean/core/theoretical_sampling_preflight.py` (new)
- `scripts/preflight_theoretical_sampling_protocol.py` (new)
- `tests/test_theoretical_sampling_preflight.py` (new)
- `Makefile` (modify)
- `CLAUDE.md` and `AGENTS.md` (docs/update)
- `docs/PROJECT_THEORY_AND_GOALS.md` and `docs/EVALUATION_HARNESS.md`
  (docs/update)
- `docs/plans/CLAUDE.md` and `docs/plans/ACTIVE_SPRINT.md` (plan tracking)

---

## Plan

### Steps

1. Commit this plan and mark it active.
2. Add TDD tests for candidate-only pass, protocol/candidate drift, missing
   target gap coverage, result selected-ID drift, and script JSON output.
3. Implement Pydantic candidate/result package models plus a preflight report.
4. Add script and Make target.
5. Update docs with the new preflight surface and caveats.
6. Run focused tests, focused Ruff, `make docs-check`, and full `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_theoretical_sampling_preflight.py` | `test_theoretical_sampling_preflight_passes_for_matching_candidates` | Matching protocol/candidate package passes and reports target-gap coverage. |
| `tests/test_theoretical_sampling_preflight.py` | `test_theoretical_sampling_preflight_rejects_protocol_candidate_drift` | Mismatched protocol/project/hash/source policy fails loudly. |
| `tests/test_theoretical_sampling_preflight.py` | `test_theoretical_sampling_preflight_rejects_missing_target_gap_coverage` | Candidate pool must cover every protocol target gap code. |
| `tests/test_theoretical_sampling_preflight.py` | `test_theoretical_sampling_preflight_rejects_unknown_selected_candidate` | Result packages cannot select candidate IDs absent from the candidate pool. |
| `tests/test_theoretical_sampling_preflight.py` | `test_preflight_theoretical_sampling_script_outputs_json` | Script emits pass/fail JSON with proper exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_theoretical_sampling_preflight.py tests/test_theoretical_sampling_protocol.py tests/test_category_saturation_inv4.py -q` | New preflight plus existing INV-4 protocol/diagnostic behavior. |
| `python -m ruff check qc_clean/core/theoretical_sampling_preflight.py scripts/preflight_theoretical_sampling_protocol.py tests/test_theoretical_sampling_preflight.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Candidate packages are validated as schema_version=1 packages.
- [ ] Result packages are validated as schema_version=1 packages when supplied.
- [ ] Preflight enforces protocol/candidate/result ID and hash consistency.
- [ ] Preflight enforces source-policy and collection-mode consistency.
- [ ] Preflight enforces target-gap coverage and selected-candidate provenance.
- [ ] Docs preserve that this is provenance/preflight infrastructure, not
  sampling adequacy or saturation evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Notes

This is the second protocol-surface slice for INV-4. It makes future sampling
runs auditable without pretending that candidate selection, new data collection,
or methodological saturation has happened.
