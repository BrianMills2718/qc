# Plan #50: D4 Codebook Quality Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D4 codebook-quality measurement substrate

---

## Outcome

Phase 0 scorecards now include `codebook_quality_d4`, which scores externally
supplied rubric outcomes from
`ProjectState.config.extra["codebook_quality_evaluations"]`,
`make bench CODEBOOK_QUALITY=quality.json`, `scripts/bench_phase0.py
--codebook-quality-file`, or `qc_cli.py bench --codebook-quality-file`. The
scorecard reports evaluator-type counts, per-metric clarity/specificity/
usefulness/grounding summaries, overall mean, and by-evaluator-type summaries.
External D4 files are hashed in `_meta.input_hashes` and recorded in Phase 0
artifact command provenance. The docs keep this as a local measurement substrate
only, not blind expert-panel evidence or codebook-validity proof.

**Verification:**
- `python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py -q` - 61 passed.
- `python -m ruff check qc_clean/core/bench.py scripts/bench_phase0.py qc_cli.py tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py` - passed.
- `python scripts/check_markdown_links.py` - passed.
- `make check` - 742 passed, 1 skipped, 8 deselected; Ruff and docs checks passed; type check not yet configured.

## Gap

**Current:** The evaluation harness defines D4 codebook quality as rubric scores
for clarity, specificity, usefulness, and grounding, but Phase 0 has no D4
scorecard section and no agent-drivable way to feed external rubric outcomes
into `make bench`.

**Target:** Add a deterministic `codebook_quality_d4` scorecard that accepts
externally supplied rubric outcomes from
`ProjectState.config.extra["codebook_quality_evaluations"]` or
`CODEBOOK_QUALITY=` / `--codebook-quality-file`. The scorecard will summarize
0-1 rubric metrics overall and by evaluator type while preserving whether each
score came from an LLM judge, human expert, or another evaluator.

**Why:** This creates the missing local D4 measurement substrate without
running an LLM judge inside Phase 0 and without claiming blind expert quality
evidence has been collected.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D4 rubric definition and Phase 0 gaps.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline around methodological
  validity and expert evidence.
- `qc_clean/core/bench.py` - external-evaluation scorecard patterns.
- `scripts/bench_phase0.py`, `qc_cli.py`, `Makefile` - external file input,
  hashing, provenance, and wrapper surfaces.
- `tests/test_bench_phase0.py`, `tests/test_bench_phase0_script.py`,
  `tests/test_qc_cli_bench.py` - scorecard and bench wrapper coverage.
- Memory context: `agent-memory recall 'qualitative_coding D4 codebook quality rubric scorecard llm_judge expert panel' --project qualitative_coding` failed because the embedding provider returned OpenRouter 402/403 errors; no local coordination claims were present.

---

## Research Basis For This Slice

No additional external research beyond repo-local references. This slice only
adds deterministic accounting over externally supplied rubric outcomes; future
LLM-judge generation, blind expert collection, agreement analysis, and public
benchmark statistics belong in the prompt_eval-backed suite.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D4 codebook quality scorecard | Codebook-quality rubric outcomes | Overall and evaluator-type metric summaries | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [x] Rubric outcomes are Pydantic-validated and fail loudly when malformed.
- [x] Each rubric metric is constrained to the 0-1 range.
- [x] Overall and by-evaluator-type metric summaries are deterministic.
- [x] External files are hashed in `_meta.input_hashes` and recorded in artifact command provenance.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `qc_cli.py` (modify)
- `Makefile` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `tests/test_qc_cli_bench.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add `CodebookQualityEvaluation` and `codebook_quality_scorecard` in
   `qc_clean/core/bench.py`.
2. Include `codebook_quality_d4` in `phase0_scorecard`, returning an explicit
   unavailable state when no external rubric outcomes exist.
3. Add `--codebook-quality-file` to `scripts/bench_phase0.py` and `qc_cli.py`,
   and `CODEBOOK_QUALITY=` to `make bench`.
4. Hash the external D4 file and include it in Phase 0 artifact command
   provenance.
5. Add focused tests for unavailable, scored, invalid metadata, external-file
   loading, hash/provenance, and CLI forwarding.
6. Update docs to mark a D4 Phase 0 substrate as present while preserving the
   no-blind-expert-panel/no-validity-evidence caveat.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D4 unavailable test | Missing rubric outcomes are explicit non-evidence. |
| `tests/test_bench_phase0.py` | D4 scored test | Overall and by-evaluator-type summaries are correct. |
| `tests/test_bench_phase0.py` | D4 invalid metadata test | Malformed or out-of-range rubric metadata fails loudly. |
| `tests/test_bench_phase0_script.py` | D4 file input test | External D4 JSON is applied in memory without mutating project state. |
| `tests/test_bench_phase0_script.py` | D4 hash/provenance test | External D4 file hash and artifact command provenance are recorded. |
| `tests/test_qc_cli_bench.py` | D4 wrapper forwarding test | `qc_cli bench --codebook-quality-file` reaches the canonical script. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Main Phase 0 scorecard shape. |
| `tests/test_bench_phase0_script.py` | Bench script external-input and artifact behavior. |
| `tests/test_qc_cli_bench.py` | Top-level wrapper behavior. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Scorecard has `codebook_quality_d4` with explicit unavailable state when
  no rubric outcomes exist.
- [x] Scored output reports evaluator counts plus clarity, specificity,
  usefulness, grounding, and overall means.
- [x] External D4 JSON file can be supplied through Make, script, and `qc_cli`
  without mutating saved project state.
- [x] Phase 0 input hashes and artifact command provenance include the D4
  external file.
- [x] Docs preserve the caveat that this is not blind expert-panel evidence or
  codebook-validity proof.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should future LLM-judge D4 evaluation live entirely in `prompt_eval`? —
  Status: DEFERRED | Why it matters: prompt/model comparison and expert-panel
  agreement should use frozen cases and shared experiment tracking.
