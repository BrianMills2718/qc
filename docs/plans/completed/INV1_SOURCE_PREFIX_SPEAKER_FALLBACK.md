# Plan #141: INV-1 Source-Prefix Speaker Fallback

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Narrower INV-1 speaker-attribution caveat

---

## Outcome

Implemented in `0939f03` (`[Plan: INV1_SOURCE_PREFIX_SPEAKER_FALLBACK] Add speaker prefix fallback`).
`resolve_and_anchor()` now prefers a containing segment speaker when available,
then falls back to an explicit same-line `Speaker:` source prefix before the
anchored span. It does not infer speakers from ordinary prose or previous lines,
and speaker remains outside hash-based anchor verification.

This narrows the speaker-attribution caveat for common transcript-prefix cases.
It is not diarization, not speaker verification, and not methodological-validity
evidence.

Verification:

- TDD red captured: explicit same-line `Alex:` prefix produced `speaker=None`
  before implementation.
- `python -m pytest tests/test_grounding.py -q` passed (`22 passed`).
- `python -m ruff check qc_clean/core/grounding.py tests/test_grounding.py`
  passed.
- `make docs-check` passed.
- `make check` passed (`1058 passed, 1 skipped, 8 deselected`); type check is
  not yet configured in this repo.

---

## Gap

**Current:** `resolve_and_anchor(..., segments=...)` can copy the speaker from a
containing segment. When no segment universe is supplied, or the containing
segment has no speaker, anchored example quotes keep `speaker=None` even when the
source line has an explicit speaker prefix like `Alex:`.

**Target:** Add a cautious source-prefix speaker fallback:

- Containing segment speaker remains authoritative.
- If no segment speaker is available, inspect only the anchored span's source
  line.
- Return a speaker only when the text before the span on that same line is an
  explicit compact speaker label ending in `:`.
- Do not make speaker part of anchor verification.
- Do not infer speaker from previous paragraphs, doc names, or vague proximity.

**Why:** The roadmap still names speaker attribution as an INV-1 residual
weakness. This slice improves common transcript-prefix cases without weakening
the source-span anchor.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §13.1/§18 - INV-1 speaker caveat.
- `qc_clean/core/grounding.py` - current segment-derived speaker helper.
- `qc_clean/core/segmentation.py` - speaker-turn detection and segment speaker
  registry.
- `tests/test_grounding.py` - existing speaker attribution behavior.
- `docs/plans/completed/SEGMENT_DERIVED_SPEAKER_FOR_ANCHORED_QUOTES.md` -
  prior containment-based speaker decision.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Scope And Non-Goals

This is not diarization, not speaker detection across unlabeled prose, not
speaker verification, and not part of hash-based anchor verification. It only
fills `CodeApplication.speaker` for explicit same-line source prefixes.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| source-prefix speaker fallback | anchored span + source document content | optional speaker string | qualitative_coding | `resolve_and_anchor` callers | free |

### Capability Validation

- [x] Segment speaker remains authoritative when present.
- [x] Same-line `Speaker:` prefix fills speaker when no segment speaker exists.
- [x] Non-prefix prose before a quote does not fill speaker.
- [x] Existing grounding/speaker tests remain unchanged.

---

## Files Affected

- `qc_clean/core/grounding.py` (modify)
- `tests/test_grounding.py` (modify)
- `CLAUDE.md` and `AGENTS.md` (docs/update)
- `docs/PROJECT_THEORY_AND_GOALS.md` (docs/update)
- `docs/plans/CLAUDE.md` and `docs/plans/ACTIVE_SPRINT.md` (plan tracking)

---

## Plan

### Steps

1. Commit this plan and mark it active.
2. Add TDD tests for same-line prefix fallback, segment precedence, and prose
   non-prefix rejection.
3. Implement a helper in `grounding.py` and use it inside `resolve_and_anchor`.
4. Update docs to narrow, not remove, the speaker caveat.
5. Run focused tests, focused Ruff, `make docs-check`, and full `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_grounding.py` | `test_resolve_and_anchor_derives_speaker_from_source_prefix_without_segments` | Same-line `Speaker:` label fills speaker without segment input. |
| `tests/test_grounding.py` | `test_resolve_and_anchor_prefers_containing_segment_speaker_over_prefix` | Segment speaker remains authoritative. |
| `tests/test_grounding.py` | `test_resolve_and_anchor_does_not_infer_speaker_from_plain_prefix_text` | Plain prose before a quote does not create speaker attribution. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_grounding.py -q` | Direct INV-1 grounding/speaker behavior. |
| `python -m ruff check qc_clean/core/grounding.py tests/test_grounding.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Source-prefix fallback fills speakers only for explicit same-line labels.
- [x] Segment-derived speaker remains authoritative.
- [x] No speaker is inferred from ordinary prose.
- [x] Docs preserve that speaker attribution remains best-effort and is not part
  of anchor verification.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Notes

This deliberately avoids previous-line speaker inference. That can be useful in
some transcripts but is too easy to over-attribute without a speaker-turn
registry.
