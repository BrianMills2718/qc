# Plan #26: D7 Baseline Comparison

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 D7 scorecard
**Blocks:** held-out D7 evaluation; public benchmark baseline reporting

---

## Outcome

`make bench` now supports D7 baseline comparison wiring. Baseline predictions
can be supplied through `ProjectState.config.extra["disconfirmation_baselines"]`
or externally with `BASELINES=baselines.json` / `--d7-baselines-file`; external
baseline files are applied in memory and do not mutate saved project state.

When D7 gold and baseline predictions are both present, `disconfirmation_d7`
now includes a `baselines` section keyed by baseline name. Each baseline is
scored with the same exact target-claim/source-anchor matching as the system and
reports TP/FP/FN, recall, precision, F1, recall/precision Wilson intervals,
matched/missed/extra keys, and `system_minus_baseline` point deltas for recall,
precision, and F1. Invalid baseline metadata fails loudly. This is still
baseline scorecard wiring only: no held-out D7 benchmark, live baseline run,
interval-tested baseline delta, or superiority claim exists.

**Verification:** `python -m pytest tests/test_bench_phase0.py
tests/test_bench_phase0_script.py -q` passed (25 tests), and `python -m ruff
check qc_clean/core/bench.py scripts/bench_phase0.py tests/test_bench_phase0.py
tests/test_bench_phase0_script.py` passed. Final closeout gate: `make check`
passed with 678 tests passing, 1 skipped, 8 deselected, Ruff passing, docs
checks passing, and type checking reported as not configured.

---

## Gap

**Current:** `make bench` can score the system's D7 negative-case anchors
against adjudicated contrary-evidence gold. It cannot score baseline systems
against the same gold, so a held-out D7 run still has no agent-drivable
baseline-comparison slot.

**Target:** Add optional D7 baseline prediction input to the Phase 0 scorecard.
The input lives in `ProjectState.config.extra["disconfirmation_baselines"]` or
an external `BASELINES=` / `--d7-baselines-file` JSON file and is applied in
memory only. Each baseline supplies a name and exact contrary-evidence anchors
using the same target-claim/source-anchor key shape as D7 gold. When gold is
available, `disconfirmation_d7` scores each baseline with the same exact
TP/FP/FN, recall, precision, F1, and recall/precision Wilson intervals as the
system, plus point deltas versus the system.

**Why:** D7 superiority requires baselines. This slice does not run a held-out
benchmark or prompt-eval statistics, but it creates the deterministic input and
reporting slot needed for future held-out D7 runs.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D7 requires disconfirmation recall/precision
  versus human gold and the roadmap still lists baselines as missing.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-2/INV-6 remain partial without held-
  out D7 gold-set evaluation with baselines.
- `docs/plans/completed/D7_WILSON_INTERVALS.md` - F1/bootstrap intervals were
  intentionally deferred to the later `prompt_eval` suite.
- `qc_clean/core/bench.py` - current D7 exact-anchor scorecard and Wilson helper.
- `scripts/bench_phase0.py` - current external gold/prompt-injection/D10 inputs.
- `tests/test_bench_phase0.py` - current D7 scorecard tests.
- `tests/test_bench_phase0_script.py` - current external-file bench tests.
- Memory context: `agent-memory recall 'D7 baseline comparison prompt_eval qualitative_coding disconfirmation benchmark active decisions' --project qualitative_coding` - historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is
deterministic baseline wiring, not a new statistical method.

---

## Capabilities

This plan modifies a repo-local benchmark/report surface only; it does not
create a cross-project callable capability.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `Makefile` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify if queue changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/D7_BASELINE_COMPARISON.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a D7 baseline metadata model with non-empty unique names and a
   `contrary_evidence` anchor list.
2. Reuse the exact D7 anchor key logic so baseline predictions are scored the
   same way as system predictions.
3. Add `baselines` under `disconfirmation_d7` only when gold is available and
   baseline metadata is supplied.
4. For each baseline, report counts, recall, precision, F1, recall/precision
   Wilson intervals, matched/missed/extra keys, and deltas versus system point
   scores.
5. Add `--d7-baselines-file` to `scripts/bench_phase0.py`, applied in memory
   only like `--gold-file`.
6. Add `BASELINES=` forwarding to `make bench`.
7. Update docs conservatively: this is baseline scorecard wiring, not a held-out
   benchmark, not F1/bootstrap statistics, and not D7 validity evidence.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_scores_d7_baselines_against_same_gold` | Baseline predictions are scored against the same gold and include point deltas versus the system. |
| `tests/test_bench_phase0.py` | `test_scorecard_invalid_d7_baseline_metadata_fails_loud` | Malformed or duplicate baseline metadata raises a clear error. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_d7_baselines_from_file_without_mutating_state` | External baseline file feeds the D7 scorecard and does not persist into project state. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_invalid_d7_baselines_file_fails_loud` | Malformed baseline JSON returns non-zero with a clear error. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py tests/test_bench_phase0_script.py` | Protect Phase 0 scorecard and CLI contracts. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [x] `disconfirmation_d7.baselines` appears when D7 gold and baseline
  predictions are supplied.
- [x] Each baseline uses the same exact target-claim/source-anchor scoring as
  the system.
- [x] Baseline output includes TP/FP/FN, recall, precision, F1,
  recall/precision CIs, key lists, and deltas versus system point scores.
- [x] Invalid baseline JSON/metadata fails loudly.
- [x] `make bench ID=<project> BASELINES=baselines.json` forwards the file and
  does not mutate saved project state.
- [x] Docs say baseline wiring is not a held-out benchmark or superiority
  claim.

> Process criteria (quality gates):
- [x] Required tests pass (`python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py -q`: 25 passed)
- [x] Full test suite passes (`make check`: 678 passed, 1 skipped, 8 deselected)
- [x] Type check status is reported (`make check`: type checking not configured)
- [x] Docs updated

---

## Open Questions

- [ ] Should baseline delta CIs be computed here? - Status: DEFERRED | Why it
  matters: superiority needs interval tests, but the prior D7 interval plan
  reserved F1/bootstrap and baseline-delta statistics for the `prompt_eval`
  suite. This slice reports deterministic point deltas only.

---

## Notes

Expected external JSON shape:

```json
{
  "disconfirmation_baselines": [
    {
      "name": "single_prompt_baseline",
      "description": "Optional human-readable baseline description.",
      "contrary_evidence": [
        {
          "target_claim_id": "claim-ai",
          "doc_id": "d1",
          "start_char": 10,
          "end_char": 42,
          "quote_text": "Optional evidence text."
        }
      ]
    }
  ]
}
```
