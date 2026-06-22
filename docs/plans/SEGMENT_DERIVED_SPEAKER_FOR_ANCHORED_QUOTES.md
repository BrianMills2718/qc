# Plan #81: Segment-Derived Speaker For Anchored Quotes

**Status:** Implemented
**Type:** implementation
**Priority:** High
**Blocked By:** INV-1 span anchoring; INV-8 segment universe
**Blocks:** stronger quote provenance and reduced speaker-attribution caveats

---

## Gap

**Current:** Exhaustive thematic coding and GT constant comparison set
`CodeApplication.speaker` from the segment being coded. The default
example-quote anchoring path resolves quote spans to document offsets, but does
not derive the speaker from the segment universe even when the resolved span is
contained in a speaker-labeled segment.

**Target:** Let `resolve_and_anchor` optionally accept the segment universe and
copy the containing segment's speaker onto the anchored `CodeApplication`.
Wire this through thematic and incremental example-quote paths.

**Why:** The theory doc still names `speaker` as a residual INV-1 weakness.
Char offsets are already the source of truth; speaker attribution should be
derived from the same anchored segment registry when available rather than left
blank.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-1 speaker caveat.
- `qc_clean/core/grounding.py` - `resolve_and_anchor`.
- `qc_clean/core/segmentation.py` - char-anchored `Segment.speaker` registry.
- `qc_clean/core/pipeline/stages/thematic_coding.py` - default and exhaustive
  thematic application creation.
- `qc_clean/core/pipeline/stages/incremental_coding.py` - incremental
  quote-anchoring paths.
- `tests/test_grounding.py` - quote anchoring unit tests.
- Memory context: `agent-memory recall 'segment-derived speaker anchored quotes' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No external research is needed. This is deterministic provenance propagation
from existing segment metadata.

---

## Capabilities

This plan modifies repo-local grounding behavior. It does not create a new
shared capability.

---

## Files Affected

- `qc_clean/core/grounding.py` (modify)
- `qc_clean/core/pipeline/stages/thematic_coding.py` (modify)
- `qc_clean/core/pipeline/stages/incremental_coding.py` (modify)
- `tests/test_grounding.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/SEGMENT_DERIVED_SPEAKER_FOR_ANCHORED_QUOTES.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a private grounding helper that finds a segment containing a resolved
   quote span for the same document.
2. Add optional `segments` input to `resolve_and_anchor`.
3. When a containing segment has a non-empty speaker, set
   `CodeApplication.speaker`.
4. Pass `state.segments` from thematic and incremental quote-anchoring paths.
5. Add unit tests for speaker derivation, absent segments, and non-containing
   spans.
6. Update docs to narrow the INV-1 speaker caveat without claiming perfect
   speaker attribution.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_grounding.py` | `test_resolve_and_anchor_derives_speaker_from_containing_segment` | Anchored quote receives speaker from containing segment. |
| `tests/test_grounding.py` | `test_resolve_and_anchor_leaves_speaker_empty_without_containing_segment` | No false speaker attribution when segment does not contain the span. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_grounding.py` | Existing span anchoring semantics remain intact. |
| `tests/test_project_commands.py` / incremental tests | Thematic and incremental callers remain compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `resolve_and_anchor(..., segments=...)` sets `speaker` only when a
  containing same-document segment has a speaker.
- [x] No segment match leaves `speaker` unset.
- [x] Existing callers without `segments` remain compatible.
- [x] Thematic and incremental example-quote paths pass the current segment
  universe.
- [x] Docs state speaker attribution is improved but still best-effort when
  speakers are undetected or no segment contains the span.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status is reported
- [x] Docs updated

## Verification

- `python -m pytest tests/test_grounding.py -q` — 15 passed.
- `python -m pytest tests/test_grounding.py tests/test_incremental.py tests/test_incremental_staleness_inv11.py -q` — 37 passed.
- `make check` — 801 passed, 1 skipped, 8 deselected; lint/docs passed; type check not yet configured.

---

## Open Questions

- [x] Should speaker derivation use overlap instead of containment? — Status:
  RESOLVED | Answer: No. Use containment to avoid assigning a speaker when a
  quote spans speaker-turn boundaries.

---

## Notes

Do not make speaker part of anchor verification. The verifiable evidence anchor
remains doc ID, char offsets, and span hash.
