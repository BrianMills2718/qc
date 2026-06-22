# Plan #140: INV-1 Deterministic Fuzzy Grounding

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Higher D1 recovery for near-verbatim LLM quote outputs

---

## Gap

**Current:** INV-1 grounding resolves exact normalized substrings only
(case/whitespace/smart-character tolerant). Paraphrased or slightly elided
quotes are dropped as unanchored even when there is a single obvious source span.

**Target:** Add a conservative deterministic fuzzy fallback in
`qc_clean/core/grounding.py`:

- Exact normalized matching remains first and authoritative.
- Ambiguous exact matches remain ambiguous; fuzzy matching does not override them.
- Fuzzy matching only runs when exact matching finds zero occurrences.
- Fuzzy candidates must exceed a configurable ratio and token-count floor.
- A fuzzy result is anchorable only when exactly one source span qualifies.
- Returned offsets/hash still point to exact original source text.

**Why:** The roadmap lists fuzzy/semantic matcher as remaining INV-1 work. This
slice implements the deterministic fuzzy part without embeddings or unverifiable
semantic anchors.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - INV-1 remaining fuzzy/semantic
  matcher gap.
- `qc_clean/core/grounding.py` - current normalized exact matching and
  verification.
- `tests/test_grounding.py` - existing INV-1 behavior and ambiguity safety
  tests.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a local deterministic
fallback, not an externally benchmarked semantic matcher.

---

## Scope And Non-Goals

This plan is not semantic retrieval, not embedding matching, not a guarantee
that all paraphrases recover, and not a relaxation of INV-1 verification. It
does not anchor short vague phrases and does not resolve ambiguous repeated
phrases.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `resolve_span` fuzzy fallback | quote string + document content | `SpanMatch` with exact original offsets/hash | qualitative_coding | thematic/incremental/GT grounding callers | free |

### Capability Validation

- [ ] Near-verbatim elided quote recovers the exact original source span.
- [ ] Fuzzy fallback does not run when exact matching is ambiguous.
- [ ] Repeated fuzzy candidates return ambiguous rather than guessing.
- [ ] Short vague quotes do not fuzzy-match.
- [ ] Existing exact grounding tests remain unchanged.

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
2. Add TDD tests for unique fuzzy recovery, exact ambiguity safety, repeated
   fuzzy ambiguity, and short-quote rejection.
3. Implement token-window fuzzy fallback using standard-library deterministic
   scoring.
4. Update docs with the new partial INV-1 status and caveats.
5. Run focused tests, focused Ruff, `make docs-check`, and full `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_grounding.py` | `test_fuzzy_match_recovers_near_verbatim_elision` | A long near-verbatim quote with a small omission resolves to exact original offsets/hash. |
| `tests/test_grounding.py` | `test_fuzzy_match_does_not_override_exact_ambiguity` | Exact repeated phrase remains ambiguous. |
| `tests/test_grounding.py` | `test_fuzzy_match_repeated_near_matches_are_ambiguous` | Multiple fuzzy-qualified spans are ambiguous, not guessed. |
| `tests/test_grounding.py` | `test_fuzzy_match_rejects_short_vague_quote` | Short vague snippets do not fuzzy anchor. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_grounding.py -q` | Direct INV-1 grounding behavior. |
| `python -m ruff check qc_clean/core/grounding.py tests/test_grounding.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Fuzzy fallback recovers a single long near-verbatim source span.
- [ ] Exact matching semantics and ambiguity handling remain intact.
- [ ] Fuzzy ambiguity fails loud as ambiguous.
- [ ] Returned fuzzy anchors verify with `verify_anchor`.
- [ ] Docs preserve that this is deterministic fuzzy recovery, not full semantic
  grounding or methodological-validity evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Notes

This is a precision-biased recovery slice. The system should still drop
borderline, short, or repeated near-matches rather than fabricate provenance.
