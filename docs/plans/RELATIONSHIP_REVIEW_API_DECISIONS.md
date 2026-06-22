# Plan #87: Relationship Review API Decisions

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** INV-10 claim review first slices
**Blocks:** INV-10 relationship review UX; MCP relationship review; expert adjudication protocol

---

## Gap

**Current:** `ReviewManager` and the review API can list/adjudicate codes, code
applications, codebooks, and claims. Persisted code/entity relationships are
visible in graph/export surfaces, but they are not review targets. A human or
agent cannot approve, reject, or modify a relationship through the shared review
decision path.

**Target:** Make persisted relationships reviewable through `ReviewManager` and
the API:

- Add `ReviewSummary.relationships_count`.
- Add `ReviewManager.get_pending_relationships()`.
- Support explicit decision target types `code_relationship` and
  `entity_relationship`.
- Add `/projects/{project_id}/review/relationships` returning bounded
  relationship review rows with source/target names and evidence counts.
- Extend `/review/decisions` responses with `relationships_count`.

**Why:** INV-10 says adjudication must reach relationships, not only code labels
or claims. This closes the agent/API first slice while avoiding ambiguous generic
relationship IDs. Browser tabs, MCP tools, and expert protocols remain separate
follow-ups.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:363` - INV-10 still lists
  relationship/negative-case review UX as a remaining gap.
- `docs/PROJECT_THEORY_AND_GOALS.md:451-455` - roadmap puts ledger review and
  relationship review ahead of feature work.
- `qc_clean/core/pipeline/review.py` - existing review manager and decision
  handlers for code/application/codebook/claim targets.
- `qc_clean/plugins/api/api_server.py` - existing `/review/codes`,
  `/review/claims`, and `/review/decisions` endpoints.
- `qc_clean/schemas/domain.py` - `CodeRelationship`,
  `DomainEntityRelationship`, `HumanReviewDecision`, and `ReviewSummary`.
- `tests/test_review.py` - core review-manager regression tests.
- `tests/test_review_api.py` - review API endpoint and decision tests.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic review-routing slice for an already-documented INV-10 gap.

---

## Capabilities

This plan modifies an internal project API and review manager. It does not
create a cross-project callable boundary.

---

## Files Affected

- `qc_clean/schemas/domain.py` (modify)
- `qc_clean/core/pipeline/review.py` (modify)
- `qc_clean/plugins/api/api_server.py` (modify)
- `tests/test_review.py` (modify)
- `tests/test_review_api.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/RELATIONSHIP_REVIEW_API_DECISIONS.md` (create, then move to completed)

---

## Plan

### Steps

1. Extend `ReviewSummary` with `relationships_count`.
2. Add `ReviewManager.get_pending_relationships()` returning deterministic
   normalized rows for both code and entity relationships.
3. Add decision handling for:
   - `target_type="code_relationship"` over `state.code_relationships`;
   - `target_type="entity_relationship"` over `state.entity_relationships`.
4. For relationship decisions:
   - `approve` stores the decision only; no schema field is mutated because
     relationship objects do not yet have adjudication/provenance fields.
   - `reject` removes the target relationship from the relevant list.
   - `modify` updates existing relationship fields from `new_value`.
   - unsupported actions fail loudly.
   - missing IDs fail loudly.
5. Add `/projects/{project_id}/review/relationships` with bounded rows and
   summary metadata.
6. Add `relationships_count` to review-decision responses.
7. Update docs conservatively: this is API/manager relationship review, not
   browser-native relationship review, MCP relationship review, or expert
   adjudication.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review.py` | `test_relationship_review_summary_and_pending_rows` | Review summary counts code/entity relationships and pending rows include explicit target types. |
| `tests/test_review.py` | `test_code_relationship_review_reject_modify_and_missing_id` | Code relationship decisions reject, modify, and fail loud on missing IDs. |
| `tests/test_review.py` | `test_entity_relationship_review_reject_modify_and_unsupported_action` | Entity relationship decisions reject, modify, and fail loud on unsupported actions. |
| `tests/test_review_api.py` | `test_returns_relationships_for_review` | API lists bounded relationship review targets with names/evidence counts. |
| `tests/test_review_api.py` | `test_relationship_decision_persists` | `/review/decisions` persists relationship decisions and updates relationship lists. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_review.py tests/test_review_api.py -q` | Core manager/API review behavior remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Review summaries include total persisted relationships.
- [ ] Relationship review rows distinguish `code_relationship` from
  `entity_relationship`.
- [ ] API clients can list relationship review targets through
  `/projects/{project_id}/review/relationships`.
- [ ] API/manager decisions can approve, reject, and modify code relationships.
- [ ] API/manager decisions can approve, reject, and modify entity relationships.
- [ ] Missing relationship IDs and unsupported relationship actions fail loudly.
- [ ] Docs state this narrows INV-10 but does not add browser/MCP/expert review
  coverage.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should relationship objects gain their own adjudication/provenance fields?
  - Status: DEFERRED | Why it matters: useful long-term, but this slice avoids
  schema churn and records decisions in the existing review-decision ledger.
- [ ] Should browser review get a Relationships tab immediately?
  - Status: DEFERRED | Why it matters: valuable for humans, but API/manager
  review closes the first agent-drivable slice.
- [ ] Should MCP expose `qc_review_relationships`?
  - Status: DEFERRED | Why it matters: useful for agent clients, but API review
  is already agent-drivable and keeps this slice bounded.

---

## Notes

Negative-case review remains partially available through claim review because
negative cases are emitted as `ClaimKind.NEGATIVE_CASE` claim objects. A
separate negative-case-specific UX/protocol is still future work.
