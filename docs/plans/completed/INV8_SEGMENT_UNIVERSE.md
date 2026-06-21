# Plan — INV-8 Segment Universe (foundational half)

*Started: 2026-06-20. Owner: autonomous agent. Re-read after any compaction.*

## Gap (from PROJECT_THEORY_AND_GOALS.md §13.1 INV-8)

The system has **no defensible denominator**. Coverage, application-level
agreement, consensus, prevalence, and "absence of evidence" all need a stable
set of examined textual units. Today the thematic path's applications come from
LLM example quotes (no universe), so any rate over them measures generation
salience, not corpus reality.

## Scope decision (important — read before extending)

INV-8 has two halves:

1. **Foundational (THIS plan, safe to do autonomously):** build a stable
   **segment registry** (every document split into identified units with char
   spans + speaker), store it in `ProjectState`, map code applications to
   segments, and report **coverage = segments-with-anchored-evidence / total
   segments**. No change to LLM cost or to how coding works; it adds an honest
   denominator. Deterministic.

2. **Exhaustive per-segment coding (APPROVED 2026-06-20 — Phases 5–7).**
   A decision on *every* segment (incl. "no code applies"). **Cost correction:**
   NOT one call per segment — the model codes the whole segmented document in
   ONE batched structured call that returns a per-segment decision array. Real
   delta vs today ≈ more output tokens, not 5–10×. Bonus: applications anchor
   directly to segment offsets (no fuzzy matching), strengthening INV-1. Wired
   as opt-in `ctx.exhaustive_coding` (default off → no behavior change).

Phases 1–4 delivered #1 (PARTIAL). Phases 5–7 deliver #2 → INV-8 MET (in
exhaustive mode).

## Pre-made decisions

- New module `qc_clean/core/segmentation.py` with a `Segment` Pydantic model
  (`id, doc_id, index, start_char, end_char, speaker, text`) and
  `segment_corpus(documents) -> list[Segment]`. Reuse the GT speaker-turn /
  paragraph logic from `gt_constant_comparison` but return **char-anchored**
  segments (offsets into the original doc).
- `ProjectState.segments: list[Segment]` (additive, backward-compatible).
- Coverage computed by char-span overlap between `CodeApplication`
  (start_char/end_char, INV-1) and segments — no new LLM calls. Applications
  without offsets (unanchored) don't count toward covered segments.
- Coverage surfaced in `verify_grounding`/`phase0_scorecard`/`make bench` and a
  `segment_id` is **not** forced onto applications (computed on demand) to keep
  the change additive.
- Commit + push per green phase.

## Acceptance criteria

- `segment_corpus` produces non-overlapping, char-anchored, uniquely-identified
  segments covering each document; round-trip `doc.content[seg.start:seg.end]`
  equals `seg.text`. Tested on speaker-turn and paragraph inputs.
- `ProjectState.segments` populated by ingest (or a populate step); coverage
  metric = covered/total with a defined denominator.
- `make bench` / grounding report include `coverage` with the segment count.
- `make check` green after each phase. No live-LLM calls in the autonomous run.

## Phase tracker

| Phase | Scope | Status |
|---|---|---|
| 1 | `segmentation.py`: `Segment` + `segment_corpus` (char-anchored) + tests | DONE (6 tests) |
| 2 | `ProjectState.segments`; populate in ingest; coverage helper (app↔segment overlap) + tests | DONE |
| 3 | Surface coverage in scorecard/MCP + tests | DONE |
| 4 | Docs: INV-8 UNMET→PARTIAL, roadmap, counts | DONE |
| 5 | Exhaustive coding: `Segment.decision`, `ExhaustiveCodingResponse`, `ctx.exhaustive_coding` branch + tests | DONE (3 tests) |
| 6 | `compute_coverage` examined/coded rates; surface in bench; CLI opt-in + tests | DONE |
| 7 | Docs: INV-8 → MET (exhaustive mode); roadmap; counts | DONE |

**COMPLETE (all 7 phases).** INV-8 MET in exhaustive mode (`project run --exhaustive`): char-anchored segment universe, examined-and-judged coverage, segment-anchored applications. PARTIAL by default (traversal coverage). Follow-up status: `project irr --application-level` shipped in `IRR_APPLICATION_LEVEL.md` and reports positive segment x code agreement plus segment-decision agreement over `coded` / `no_code` / `not_examined`; remaining decision is whether exhaustive becomes default after live validation.

## Notes / findings log
- The exhaustive per-segment-coding half SHIPPED (Phases 5-7, `project run --exhaustive`). The earlier '~5-10x cost / deferred' worry was wrong: it is ONE batched call (more output tokens, not more calls). User approved it 2026-06-20.
- Reused nothing from the GT segmenter (it strips offsets); the new segmenter is offset-preserving and round-trip-verified.
