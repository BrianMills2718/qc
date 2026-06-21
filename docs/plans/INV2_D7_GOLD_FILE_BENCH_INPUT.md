# Plan #12: INV-2 D7 Gold File Bench Input

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** held-out D7 evaluation; prompt_eval-backed benchmark suite

---

## Gap

**Current:** `phase0_scorecard` can compute D7 disconfirmation recall/precision
when `ProjectState.config.extra["disconfirmation_gold"]` contains adjudicated
contrary-evidence anchors. The only current input path is embedding those gold
records in saved project state metadata.

**Target:** Add an agent-drivable external gold-file input to
`scripts/bench_phase0.py` and `make bench`, so D7 gold annotations can live in a
separate frozen JSON artifact. The script should load the gold file into an
in-memory state copy before scoring and must not mutate the persisted project.

**Why:** Held-out gold annotations should be versioned and hashed as benchmark
artifacts, not mixed into ordinary project state. This is the smallest wiring
step toward real D7 benchmark runs without building the full `prompt_eval`
suite yet.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md:57` - D7 score definition and current scorecard substrate.
- `docs/EVALUATION_HARNESS.md:90-97` - frozen/hashing and scorecard output requirements.
- `docs/PROJECT_THEORY_AND_GOALS.md:255` - INV-2 remains partial until held-out D7 runs with CIs/baselines.
- `qc_clean/core/bench.py` - D7 scorecard reads `ProjectState.config.extra["disconfirmation_gold"]`.
- `scripts/bench_phase0.py` - current agent-drivable scorecard CLI.
- `Makefile` - current `bench` target.
- `tests/test_bench_phase0.py` - D7 scoring unit tests.
- Memory context: `agent-memory recall 'active decisions D7 gold file bench_phase0 qualitative_coding INV-2 evaluation harness' --project qualitative_coding` — no active blocking decision surfaced.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is CLI/Make
wiring for an already-defined D7 score contract.

---

## Capabilities

This plan modifies a repo-local CLI script and Make target only; it does not
create a cross-project callable capability.

---

## Files Affected

- `scripts/bench_phase0.py` (modify)
- `Makefile` (modify)
- `tests/test_bench_phase0_script.py` (create)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify if status wording needs precision)
- `CLAUDE.md` (modify if command docs change)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV2_D7_GOLD_FILE_BENCH_INPUT.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `--gold-file <path>` to `scripts/bench_phase0.py`.
2. Accept the same gold shapes the scorecard supports: a list of gold anchors or
   a dict containing `contrary_evidence`.
3. Apply gold only to an in-memory `ProjectState` copy before calling
   `phase0_scorecard`; never write it back through `ProjectStore`.
4. Add `GOLD=` support to `make bench` that forwards `--gold-file`.
5. Add script tests for scored D7 output from a gold file and fail-loud invalid
   gold input.
6. Update docs conservatively: external gold-file wiring exists; no held-out D7
   benchmark has run.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_d7_from_gold_file_without_mutating_state` | External gold file produces D7 scores and does not persist into project state. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_invalid_gold_file_fails_loud` | Malformed gold JSON returns non-zero with a clear error. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Core D7 scoring contract unchanged. |
| `make docs-check` | Make/doc surfaces remain synchronized. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] `python scripts/bench_phase0.py <project_id> --gold-file gold.json` feeds D7 gold into the scorecard.
- [ ] `make bench ID=<project_id> GOLD=gold.json` forwards the gold file.
- [ ] The saved project JSON is not mutated by scoring with an external gold file.
- [ ] Invalid gold file shape fails loudly with a non-zero exit and clear JSON error.
- [ ] Docs state this is gold-file wiring only; no D7 benchmark result is claimed.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should gold files include dataset/prompt/model hashes now? — Status: DEFERRED | Why it matters: full Phase 1/2 scorecards need hashes, but this slice only passes gold anchors into the existing exact D7 metric.
- [ ] Should `--gold-file` become a future `qc bench` option? — Status: DEFERRED | Why it matters: yes for the target harness, but the current repo surface is `make bench`/`bench_phase0.py`.

---

## Notes

This plan keeps the scorecard deterministic and LLM-free. It intentionally does
not create synthetic gold data or claim any disconfirmation score until a real
gold file is supplied.
