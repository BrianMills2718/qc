# Plan #199: Negative Case Review Anchor Details

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Negative Case Review Surfaces
**Blocks:** INV-10 negative-case-specific adjudication workflow

---

## Gap

**Current:** Negative-case-specific API, MCP, and browser review surfaces list
`AnalyticClaim` rows with challenged claim IDs in `scope.claim_ids` and anchor
counts, but they do not show the contrary anchor document, offsets, hash, or
quote text. A reviewer can see that a negative case has an anchor, but not the
anchored evidence needed to judge it without leaving the review surface.

**Target:** Add bounded anchor-detail payloads to the shared claim-review rows
used by API/MCP/browser review surfaces. Negative-case rows should expose
contrary anchor details directly, and generic claim rows may expose supporting
anchor details through the same bounded helper. Browser review cards should
render those details compactly.

**Why:** INV-10 review is not useful if the review surface hides the evidence
being adjudicated. This slice improves review ergonomics and agent-drivability
without claiming expert adjudication, disconfirmation validity, or held-out D7
evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:502-507` - INV-2/INV-6/INV-7/INV-10
  claim discipline and remaining gaps.
- `docs/plans/completed/NEGATIVE_CASE_REVIEW_SURFACES.md` - prior deferred
  question about showing retrieved candidate details.
- `qc_clean/core/pipeline/stages/negative_case.py` - `NegativeCase.candidate_id`
  and contrary-anchor construction path.
- `qc_clean/core/claims.py:370-407` and `qc_clean/core/claims.py:781-804` -
  negative-case claims and contrary-anchor resolution.
- `qc_clean/plugins/api/api_server.py:206-225` - API/browser review row shape.
- `qc_mcp_server.py:355-374` - MCP review row shape.
- `qc_clean/plugins/api/review_ui.py:430-456` - browser claim-card rendering.
- `tests/test_review_api.py:309-347` and `tests/test_mcp_server.py:663-710`
  - current negative-case review tests.
- Memory context:
  `agent-memory recall 'qualitative_coding active decisions remaining roadmap D7 INV7 theoretical sampling' --project qualitative_coding`
  — old completed outcomes only; no active decision.
- Coordination context: `~/.claude/coordination/claims/` contains only an
  unrelated `llm_client` write claim.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a deterministic
review-surface payload improvement over existing claim-anchor models.

---

## Capabilities

This plan modifies project-local API/MCP/browser review payloads only. It does
not create a cross-project callable boundary, registry entry, or new evaluation
capability.

---

## Files Affected

- `qc_clean/plugins/api/api_server.py` (modify)
- `qc_clean/core/claims.py` (modify)
- `qc_mcp_server.py` (modify)
- `qc_clean/plugins/api/review_ui.py` (modify)
- `tests/test_review_api.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add TDD coverage proving negative-case API and MCP rows include bounded
   contrary-anchor details.
2. Add a static browser test proving the review UI renders anchor detail rows.
3. Implement a small bounded anchor-detail formatter in the existing API and
   MCP row helpers.
4. Render supporting/contrary anchor details in browser claim cards without
   changing decision semantics.
5. Update docs conservatively and regenerate `AGENTS.md`.
6. Run focused tests, Ruff, docs checks, and `make check`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_returns_negative_cases_for_review` | Negative-case API rows include contrary-anchor details with doc/offset/hash/quote payloads, not only counts. |
| `tests/test_mcp_server.py` | `test_review_negative_cases` | MCP negative-case rows include the same bounded contrary-anchor details. |
| `tests/test_review_api.py` | `test_review_page_exposes_anchor_detail_rendering` | Browser review page includes the static rendering path for anchor details. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_review_api.py tests/test_mcp_server.py -q` | Protect API/MCP/browser review surfaces. |
| `python -m ruff check qc_clean/plugins/api/api_server.py qc_mcp_server.py qc_clean/plugins/api/review_ui.py tests/test_review_api.py tests/test_mcp_server.py` | Focused lint for modified files. |
| `make docs-check` | Plan/docs sync and generated-agent governance. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] API claim-review rows expose bounded `supporting_anchor_details` and
  `contrary_anchor_details`.
- [ ] MCP claim-review rows expose the same bounded anchor-detail fields.
- [ ] Negative-case review rows include contrary anchor doc IDs, offsets,
  quote hashes, quote text, and optional code-application IDs when present.
- [ ] Browser review cards render anchor details compactly when present.
- [ ] Existing review-decision semantics still submit `target_type="claim"`;
  this slice does not propagate negative-case decisions to challenged claims.
- [ ] Docs state this improves evidence visibility only; it does not add expert
  adjudication, candidate-score adjudication, held-out D7 evidence, or
  disconfirmation validity.

Process criteria:

- [ ] Required focused tests pass.
- [ ] Focused Ruff passes.
- [ ] `make docs-check` passes.
- [ ] `make check` passes or any failure is documented with evidence.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should negative-case decisions automatically mutate challenged target
  claims? — Status: DEFERRED | Why it matters: that is an adjudication policy
  decision and should not be hidden inside a display-payload slice.
- [ ] Should retrieved candidate scores and retrieval rationale be persisted for
  review? — Status: DEFERRED | Why it matters: current persisted claims retain
  anchors, not full candidate objects; candidate-score persistence is a larger
  data-model change.

---

## Notes

Anchor details must be bounded and compact. The review surface should help a
reviewer inspect the exact evidence but must not become a raw full-state dump.
