# Plan #174: D3 Baseline Span-Overlap Diagnostics

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** D3 application-validity scorecard and D3 baseline comparison
substrate
**Blocks:** Better D3 baseline error analysis for future held-out adjudication
and baseline comparison packages

---

## Gap

**Current:** The D3 system scorecard reports exact code/source-anchor metrics plus
local same-code/document character-span overlap diagnostics, including IoU and
Modified Hausdorff distance. D3 baseline rows under
`application_validity_d3.baselines` report exact TP/FP/FN, recall/precision/F1,
system-minus-baseline deltas, and optional delta bootstrap intervals, but they
do not include the same local span-overlap diagnostics. D7 baselines already
have this diagnostic parity.

**Target:** Add `application_validity_d3.baselines.<name>.span_overlap` for each
scored D3 baseline. The diagnostic should reuse the D3 same-code/document
character-span logic, count unscored segment-only/missing-offset records, and
leave exact D3 baseline metrics/deltas unchanged.

**Why:** Exact-anchor baseline failures are too coarse for D3 error analysis. A
near-boundary baseline prediction should remain an exact false positive/false
negative, but the scorecard should also show that it overlapped the correct
same-code/document span. This improves local debugging without claiming
semantic application validity, held-out evidence, expert parity, superiority, or
SOTA.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D3 system scoring includes span alignment, but
  D3 baseline substrate text is exact-key only.
- `docs/PROJECT_THEORY_AND_GOALS.md` - D3 baseline comparison remains a local
  substrate; actual/live held-out baseline runs remain future work.
- `docs/plans/completed/D3_SPAN_OVERLAP_IOU_SCORECARD.md` and
  `docs/plans/completed/D3_MODIFIED_HAUSDORFF_SCORECARD.md` - existing D3
  system overlap diagnostics.
- `docs/plans/completed/D3_BASELINE_COMPARISON_SCORECARD.md` - existing D3
  baseline exact-score substrate.
- `docs/plans/completed/D7_BASELINE_SPAN_OVERLAP_DIAGNOSTICS.md` - analogous D7
  baseline diagnostic pattern.
- `qc_clean/core/bench.py` - D3 baseline scoring and existing D3/D7 span helpers.
- Coordination/memory check: no active claim files; `agent-memory recall
  'active decisions' --project qualitative_coding` returned only low-relevance
  completed-task summaries.

---

## Research Basis For This Slice

No new external research. This is a deterministic parity slice that reuses the
local D3 span-overlap diagnostic already implemented for system predictions.

---

## Capabilities

Internal scorecard diagnostic only; no new cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `d3_baseline_span_overlap_diagnostic` | D3 gold anchors + D3 baseline code-application anchors | `application_validity_d3.baselines.<name>.span_overlap` diagnostic metrics | qualitative_coding | `make bench`, `qc_cli.py bench`, benchmark artifacts | free |

### Capability Validation

- [ ] Every scored D3 baseline row includes `span_overlap`.
- [ ] Baseline overlap diagnostics compare only same-code/document character
  spans.
- [ ] Near-boundary baseline predictions report non-zero IoU/Modified Hausdorff
  diagnostics while exact baseline TP/FP/FN remain unchanged.
- [ ] Segment-only or missing-offset baseline/gold anchors are counted as
  unscored instead of guessed.
- [ ] Existing unguarded D3 baseline exact metrics, deltas, and bootstrap CIs
  remain unchanged.

---

## Files Affected

- `qc_clean/core/bench.py`
- `tests/test_bench_phase0.py`
- `tests/test_bench_phase0_script.py`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Add failing tests for D3 baseline near-boundary span overlap and unscored
   record accounting.
2. Refactor D3 span-overlap scoring to accept an explicit prediction set, as
   D7 already does.
3. Convert each D3 baseline's code applications into scoreable comparable spans
   and attach `span_overlap` inside `_score_d3_baselines()`.
4. Preserve exact D3 baseline metrics, system-minus-baseline deltas, and
   bootstrap CI behavior.
5. Update docs with the local-diagnostic caveat.
6. Run focused tests, focused Ruff, docs checks, and full `make check`.
7. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_d3_baseline_span_overlap_scores_near_boundary_match` | A near-boundary D3 baseline prediction remains exact TP/FP/FN unchanged while reporting overlap diagnostics. |
| `tests/test_bench_phase0.py` | `test_scorecard_d3_baseline_span_overlap_counts_unscored_records` | Segment-only/missing-offset baseline/gold records are counted as unscored. |
| `tests/test_bench_phase0_script.py` | existing D3 baseline file test extended | External `D3_BASELINES=` scoring surfaces baseline span-overlap diagnostics without mutating state. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py -k "d3 and (baseline or span_overlap)" -q` | D3 baseline and D3 span-overlap regressions. |
| `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py tests/test_bench_phase0_script.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `application_validity_d3.baselines.<name>.span_overlap` appears for every
  scored D3 baseline.
- [ ] Baseline overlap diagnostics use same-code/document matching.
- [ ] Near-boundary D3 baseline spans report IoU and Modified Hausdorff values
  while exact baseline metrics remain unchanged.
- [ ] Unscored D3 baseline/gold anchors are counted and not inferred.
- [ ] External `D3_BASELINES=` inputs get the same diagnostics as config-backed
  baselines.
- [ ] Docs preserve the caveat that this is local error-analysis metadata only,
  not semantic application validity, held-out D3 evidence, expert parity,
  superiority evidence, or SOTA.

> Process criteria:
- [ ] TDD red state observed before implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Plan is moved to completed with verification evidence.
- [ ] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Exact D3 baseline scores change | Span diagnostics reused predicted keys incorrectly | Keep exact scoring inputs unchanged; add overlap as additive metadata only. |
| Baseline span overlap uses system predictions | Helper still reads from `ProjectState` | Split D3 overlap into state wrapper + explicit prediction helper. |
| Segment-only anchors get guessed spans | Conversion uses `segment_id` to infer offsets | Preserve existing D3 span policy: only char offsets are scoreable. |
| Missing offsets crash instead of counting unscored | Baseline conversion calls exact-key path only | Add a baseline span conversion helper that mirrors system unscored counting. |
| Docs imply improved validity evidence | Language drift in theory/evaluation docs | Explicitly state local diagnostic only; no held-out, expert, superiority, or SOTA claim. |
