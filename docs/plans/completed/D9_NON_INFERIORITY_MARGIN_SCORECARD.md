# Plan #59: D9 Non-Inferiority Margin Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D9 blind preference parity assessment

---

## Outcome

D9 interpretive-preference scorecards now always include
`non_inferiority_assessment`. When D9 preference packages include protocol
metadata with `non_inferiority_margin` and
`registered_before_evaluation=true`, the scorecard reports a
system-minus-human preference-rate point estimate, CI, required lower bound,
and `meets_non_inferiority`. Missing protocol metadata reports
`not_available`, and unregistered protocol metadata reports `not_registered`
without licensing non-inferiority. Object-shaped D9 files are preserved in
memory so protocol metadata reaches the scorecard without mutating saved project
state.

## Verification

- Focused tests: `python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py -q`
  (`80 passed`)
- Focused lint: `python -m ruff check qc_clean/core/bench.py scripts/bench_phase0.py tests/test_bench_phase0.py tests/test_bench_phase0_script.py`
  (`All checks passed!`)
- Docs/link/plan checks:
  - `python scripts/check_markdown_links.py`
  - `python scripts/sync_plan_status.py --check`
- Full gate: `make check` (`771 passed, 1 skipped, 8 deselected`; ruff and
  docs-check passed)
- Type check: not configured by the repo (`make check` reports this explicitly)

## Gap

**Current:** D9 interpretive-preference scoring reports forced-choice system wins,
human wins, ties, non-tie system preference rate, Wilson interval, and evaluator
summaries. The evaluation harness says D9 parity requires a pre-registered
non-inferiority margin, but Phase 0 has no way to record that margin or compute
a margin-gated assessment.

**Target:** Add optional protocol metadata to D9 preference packages and compute
`interpretive_preference_d9.non_inferiority_assessment` only when a package
supplies an explicit `non_inferiority_margin` and `registered_before_evaluation`
flag. The assessment will transform the system-preference Wilson interval into
a system-minus-human preference-difference interval and report whether the lower
bound is above `-margin`. If protocol metadata is absent or not pre-registered,
the section remains non-licensing metadata.

**Why:** D9 is a parity claim, not a superiority claim. Making the margin
machine-readable prevents agents from eyeballing preference rates and calling
them parity evidence.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D9 parity and non-inferiority gate.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline and D9 caveats.
- `qc_clean/core/bench.py` - D9 preference scorecard and Wilson intervals.
- `scripts/bench_phase0.py` - external D9 preference file loading.
- `tests/test_bench_phase0.py` and `tests/test_bench_phase0_script.py` -
  current D9 scorecard/file coverage.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with provider errors; circuit breaker applies. No
  active local coordination claims were present.

---

## Research Basis For This Slice

No external research required. This implements the repo-local harness rule in
`docs/EVALUATION_HARNESS.md`: non-inferiority requires a pre-registered margin
and a confidence interval for system-minus-human above `-δ`.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D9 non-inferiority assessment | D9 preference outcomes + protocol margin metadata | `interpretive_preference_d9.non_inferiority_assessment` | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [x] D9 packages may carry protocol metadata without breaking existing outcome-list loading.
- [x] Missing protocol metadata reports `not_available`, not pass/fail.
- [x] Unregistered protocol metadata reports a non-licensing status.
- [x] Registered protocol metadata computes system-minus-human point estimate and CI.
- [x] The assessment only passes when the lower CI bound is above `-margin`.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify, preserve D9 package metadata)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add an `InterpretivePreferenceProtocol` model with
   `non_inferiority_margin`, `registered_before_evaluation`, optional
   `protocol_id`, and notes.
2. Preserve object-shaped D9 preference packages from `load_interpretive_preference_file`
   so protocol metadata can reach the scorecard.
3. Add `_interpretive_preference_protocol` and
   `_interpretive_preference_non_inferiority_assessment`.
4. Add focused tests for absent protocol, unregistered protocol, and registered
   passing/failing margin cases.
5. Update docs to say Phase 0 can compute a margin-gated D9 assessment when
   protocol metadata is supplied, but still cannot claim blind expert parity
   without populated held-out expert data.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D9 absent protocol | Assessment is `not_available`. |
| `tests/test_bench_phase0.py` | D9 unregistered protocol | Assessment refuses licensing despite computing metadata. |
| `tests/test_bench_phase0.py` | D9 registered margin passes/fails | CI lower-bound rule controls `meets_non_inferiority`. |
| `tests/test_bench_phase0_script.py` | D9 object package no mutation | External object package preserves protocol metadata and does not mutate saved state. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| Existing D9 preference scorecard tests | Current counts/rates/grouping must not regress. |
| Existing D9 external file tests | List and object input compatibility must remain. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `interpretive_preference_d9.non_inferiority_assessment` is always present.
- [x] Without protocol metadata, the assessment is explicitly `not_available`.
- [x] With `registered_before_evaluation=false`, the assessment does not license
  non-inferiority.
- [x] With registered protocol metadata, the assessment reports margin, point
  estimate, CI, and pass/fail.
- [x] Docs preserve the caveat that this is still not blind expert-parity
  evidence without populated held-out expert outcomes.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should the full prompt_eval-backed D9 suite use one global margin or
  criterion-specific margins? - Status: DEFERRED | Why it matters: the public
  benchmark protocol may need per-criterion margins; this slice supports one
  package-level margin only.
