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

2. **Exhaustive null-coding (NOT this plan — a genuine fork for the user):**
   forcing the LLM to render a decision on *every* segment (incl. "no code
   applies") so we can distinguish "examined-but-irrelevant" from "not
   examined." This ~5–10×'s LLM cost and changes the thematic method's
   character. **Flagged for the user; do not implement without an explicit
   decision.**

This plan delivers #1 and moves INV-8 from UNMET to PARTIAL.

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

**Foundational half complete.** INV-8 UNMET→PARTIAL: char-anchored segment universe + coverage denominator (D2) built and surfaced. 559 tests, all gates green.

## Notes / findings log
- The exhaustive per-segment-coding half (examined-and-judged coverage + application-level agreement unit) is a **cost/method fork (~5-10x LLM cost)** deliberately deferred to a user decision.
- Reused nothing from the GT segmenter (it strips offsets); the new segmenter is offset-preserving and round-trip-verified.
