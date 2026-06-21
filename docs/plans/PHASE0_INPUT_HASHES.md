# Plan #28: Phase 0 Input Hashes

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 scorecard
**Blocks:** versioned benchmark result artifacts; held-out benchmark provenance

---

## Gap

**Current:** `make bench` can score Phase 0 metrics and accept external D7 gold,
D7 baselines, prompt-injection fixture outcomes, observability DB paths, and
project-run timing metadata. The scorecard does not report deterministic hashes
for the project state, corpus, or supplied benchmark files, so a saved scorecard
cannot prove exactly what inputs it scored.

**Target:** Add a `_meta.input_hashes` section to `scripts/bench_phase0.py`
output. It should include SHA-256 hashes for the loaded project state and corpus
plus any supplied `GOLD=`, `BASELINES=`, `PROMPT_INJECTION=`, and `OBS_DB=`
files. Missing optional files should be represented as `null`; unreadable files
should still fail through the existing load paths. Hashes are evidence metadata
only and do not change scoring.

**Why:** The evaluation harness requires frozen/hashed datasets, prompts, models,
and artifacts before any public claim. This slice supplies the deterministic
input-hash substrate for the existing Phase 0 scorecard without building the
full `prompt_eval` suite.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - requires frozen/hashed prompts/models/datasets
  and versioned benchmark results with hashes.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline requires artifact
  evidence before SOTA or parity claims.
- `docs/plans/completed/INV2_D7_GOLD_FILE_BENCH_INPUT.md` - deferred dataset
  and file hashes for future benchmark artifacts.
- `docs/plans/completed/D7_BASELINE_COMPARISON.md` - added external baseline
  input that should be hashable.
- `scripts/bench_phase0.py` - current CLI and external file loaders.
- `tests/test_bench_phase0_script.py` - current external-file bench tests.
- Memory context: `agent-memory recall 'benchmark input hashes qualitative_coding phase0 scorecard gold file hashes active decisions' --project qualitative_coding` - historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is
deterministic artifact hashing.

---

## Capabilities

This plan modifies a repo-local benchmark/report surface only; it does not
create a cross-project callable capability.

---

## Files Affected

- `scripts/bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify if operational summary changes)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify if queue changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/PHASE0_INPUT_HASHES.md` (create, then move to completed)

---

## Plan

### Steps

1. Add deterministic helper functions in `scripts/bench_phase0.py`:
   `sha256_file(path)`, `sha256_jsonable(value)`, and `input_hashes(...)`.
2. Hash the saved project state immediately after load, before applying external
   in-memory gold/baseline/prompt-injection data.
3. Hash the corpus separately from the full state using document IDs, names,
   content, and metadata in corpus order.
4. Hash supplied external files by bytes: `gold_file_sha256`,
   `d7_baselines_file_sha256`, `prompt_injection_file_sha256`, and
   `observability_db_sha256`.
5. Add the hashes under `card["_meta"]["input_hashes"]` without changing the
   score sections.
6. Update docs conservatively: hashes improve reproducibility but do not create a
   held-out benchmark or validate claims.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_includes_input_hashes_without_external_files` | Project-state and corpus hashes are present; optional file hashes are null. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_hashes_external_input_files` | Gold, baseline, prompt-injection, and observability DB file hashes match SHA-256 bytes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0_script.py` | Protect bench CLI contract. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Bench output includes `_meta.input_hashes`.
- [ ] Project-state and corpus hashes are deterministic SHA-256 hashes.
- [ ] Supplied external benchmark files are hashed by file bytes.
- [ ] Missing optional files are represented as `null`, not omitted.
- [ ] Hash metadata does not mutate project state or alter score calculations.
- [ ] Docs state hashes are provenance metadata, not benchmark validity evidence.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should prompt hashes be included now? - Status: DEFERRED | Why it matters:
  Phase 0 does not run prompts. The full `prompt_eval` suite should hash frozen
  prompt templates and model IDs when it executes live benchmark runs.

---

## Notes

Use canonical JSON (`sort_keys=True`, compact separators) for state/corpus
hashes. Use raw file bytes for file hashes so the hash matches what a reviewer
would compute from the artifact.
