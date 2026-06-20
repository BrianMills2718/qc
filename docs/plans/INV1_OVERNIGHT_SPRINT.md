# Overnight Sprint — INV-1 Span Anchoring + Harness Phase 0

*Started: 2026-06-20. Owner: autonomous agent. Re-read this file after any compaction.*

## Mission

Make evidentiary grounding (INV-1) real: every `CodeApplication` resolves to a
stable, verifiable source anchor (`doc_id` + `start_char`/`end_char` + `quote_hash`,
speaker best-effort), or is dropped+warned if it cannot be *uniquely* resolved.
Then stand up evaluation-harness Phase 0 so grounding is measurable. This is the
foundation the public-SOTA claim rests on (see `PROJECT_THEORY_AND_GOALS.md`
§13.1 INV-1 and `EVALUATION_HARNESS.md` D1/Phase 0).

## Acceptance criteria (what "done" means)

- A pure, tested span resolver maps a quote to **exact original-document char
  offsets**, robust to smart quotes / whitespace / case, and reports
  **zero / unique / ambiguous** match status.
- All coding paths populate `start_char`/`end_char`/`quote_hash` on applications;
  unresolvable **and ambiguous** quotes are dropped + surfaced in `data_warnings`
  (no fabricated provenance — extends the D1 fix).
- `verify_grounding(state)` recomputes anchors and returns a grounding report
  (rate, unresolvable, ambiguous, hash-mismatch counts).
- `make bench` runs Phase 0 (grounding rate + reliability/stability-if-present +
  cost) on a project and emits a JSON scorecard. Agent-drivable.
- `make check` green after every phase (deterministic tests + ruff + docs). No
  live-LLM calls in the autonomous run (E2E validation is a flagged follow-up
  needing the user's API budget).

## Pre-made decisions (don't stop to ask)

- **Offsets** index into the *original* `Document.content` (not normalized text).
- **Normalization for matching only:** NFKC, smart→straight quotes, collapse
  whitespace, casefold — via a normalized string + index map back to original.
- **`quote_hash`** = `sha256(doc.content[start:end])` (the exact source span), new
  `Optional[str]` field on `CodeApplication` (additive, backward-compatible).
- **Ambiguity rule:** quote matching >1 span (within or across docs) is NOT
  uniquely anchorable → drop + warn (this is the "three people said 'I felt
  ignored'" case). Unique match → anchor. Zero → drop + warn (unresolvable).
- **Speaker:** best-effort from the doc's speaker-turn segmentation; `None` if
  undeterminable. Not a blocker for INV-1 char-anchoring.
- New module `qc_clean/core/grounding.py`. Harness Phase 0 = `scripts/bench_phase0.py`
  + `make bench`, standalone (extend prompt_eval later, not tonight).
- Commit + push after each green phase. Don't batch.

## Phase tracker (update as you go)

| Phase | Scope | Status |
|---|---|---|
| 1 | `grounding.py`: `resolve_span` (offset-mapped, status) + `quote_hash` + unit tests | DONE (10 tests) |
| 2 | Wire anchors into thematic/incremental/legacy/constant-comparison; add `quote_hash` field; drop ambiguous+unresolvable | DONE |
| 3 | `verify_grounding(state)` + report model + tests; CLI/MCP surface | IN PROGRESS |
| 4 | Harness Phase 0: `scripts/bench_phase0.py` + `make bench` + scoring tests | PENDING |
| 5 | Docs: INV-1 status (precise, no overclaim), harness Phase 0 started, roadmap, theory doc, counts | PENDING |

## Notes / findings log

- (append discoveries here as phases run)
