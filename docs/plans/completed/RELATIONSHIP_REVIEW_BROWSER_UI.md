# Plan #89: Relationship Review Browser UI

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Relationship review API decisions; MCP relationship review
**Blocks:** INV-10 browser-native relationship adjudication

---

## Outcome

Completed 2026-06-21. The browser review page now has a Relationships mode next
to Codes and Claims. Relationship mode fetches
`/projects/{project_id}/review/relationships`, renders bounded relationship
cards with source/target names, target type, relationship type, strength, and
evidence metadata, and submits approve/reject/modify decisions using each row's
`target_type`.

This closes the browser-native first slice for relationship review. It does not
add negative-case-specific review UX, expert adjudication, or methodological
validity evidence.

Verification: initial TDD run failed as expected because
`id="relationshipModeBtn"` was absent. After implementation, the new static UI
test passed, full review API/UI tests passed (`30 passed`), Ruff passed on
touched files, docs/plan/AGENTS checks passed, and final `make check` passed
(`829 passed, 1 skipped, 8 deselected`; type check not yet configured).

---

## Gap

**Current:** `ReviewManager`, the API, and MCP can list/adjudicate code/entity
relationships. The browser review page still has only Codes and Claims modes,
so a human using `/review/{project_id}` cannot review relationships.

**Target:** Add a Relationships mode to the existing self-contained browser
review page. It should fetch `/projects/{project_id}/review/relationships`,
render bounded relationship cards, and submit approve/reject/modify decisions
using each row's explicit `target_type` (`code_relationship` or
`entity_relationship`) through the existing `/review/decisions` endpoint.

**Why:** INV-10 requires adjudication beyond code labels and claims. The
manager/API/MCP relationship path exists; the browser path remains the next
documented gap. This is still operational adjudication UX, not expert protocol
or methodological validity evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:363` - INV-10 status and remaining browser
  relationship review gap.
- `docs/plans/completed/RELATIONSHIP_REVIEW_API_DECISIONS.md` - API/manager
  relationship-review semantics.
- `docs/plans/completed/MCP_RELATIONSHIP_REVIEW.md` - MCP relationship-review
  listing and decision support.
- `qc_clean/plugins/api/review_ui.py` - current self-contained Codes/Claims UI.
- `qc_clean/plugins/api/api_server.py` - `/review/relationships` and
  `/review/decisions` endpoints.
- `tests/test_review_api.py` - current static review page tests.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This extends the
existing self-contained review UI and does not introduce a new frontend stack.

---

## Capabilities

This plan modifies an existing browser UI. It does not create a cross-project
callable capability.

---

## Files Affected

- `qc_clean/plugins/api/review_ui.py` (modify)
- `tests/test_review_api.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/RELATIONSHIP_REVIEW_BROWSER_UI.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a Relationships button to the existing Codes/Claims mode switch.
2. Extend `loadProject()` routing for `reviewMode === "relationships"` to fetch
   `/projects/{id}/review/relationships`.
3. Add relationship stats and a `renderRelationships()` path.
4. Render relationship cards with target type, source/target names, relationship
   type, strength, evidence count, and compact evidence/condition details.
5. Support approve/reject/modify actions for relationship rows. Modify should
   edit `relationship_type`, `strength`, and evidence fields:
   - code relationships use `evidence`, `conditions`, `consequences`;
   - entity relationships use `supporting_evidence`.
6. Submit relationship decisions through the existing `/review/decisions`
   endpoint using `target_type` from the row.
7. Keep existing Codes and Claims behavior unchanged.
8. Add static page tests proving the Relationships mode, fetch path,
   relationship renderer, and decision target type wiring exist.
9. Update docs conservatively: browser relationship review first slice is
   present; negative-case-specific review and expert protocols remain future
   work.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_review_page_exposes_relationship_review_ui` | Browser page exposes Relationships mode, fetches `/review/relationships`, renders relationship cards, and submits row `target_type`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_review_api.py -q` | Review API/UI behavior remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Browser review page has a visible Relationships mode.
- [x] Relationship mode fetches `/projects/{project_id}/review/relationships`.
- [x] Relationship cards show source/target, relationship type, strength, and
  evidence metadata.
- [x] Relationship approve/reject/modify decisions submit the row's
  `target_type`.
- [x] Existing Codes and Claims behavior is preserved.
- [x] Docs state this narrows INV-10 but does not add negative-case-specific or
  expert review.

> Process criteria:
- [x] Required focused tests pass.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Verification

- Initial TDD run:
  `python -m pytest tests/test_review_api.py::TestReviewUIPage::test_review_page_exposes_relationship_review_ui -q`
  - failed as expected because `id="relationshipModeBtn"` was absent.
- `python -m pytest tests/test_review_api.py::TestReviewUIPage::test_review_page_exposes_relationship_review_ui -q`
  - passed.
- `python -m pytest tests/test_review_api.py -q` - passed (`30 passed`).
- `python -m ruff check qc_clean/plugins/api/review_ui.py tests/test_review_api.py`
  - passed.
- `python scripts/check_markdown_links.py && python scripts/sync_plan_status.py --check && python scripts/meta/check_agents_sync.py --check`
  - passed.
- `make check` - passed (`829 passed, 1 skipped, 8 deselected`); Ruff and docs
  gates passed; type check is not yet configured.

---

## Open Questions

- [ ] Should relationship cards support bulk filters by relationship family or
  source stage? - Status: DEFERRED | Why it matters: useful for large projects,
  but not required for first browser-native relationship review.
- [ ] Should negative cases get their own browser mode? - Status: DEFERRED |
  Why it matters: negative cases are currently claim rows, but a specialized
  view could expose candidate/disconfirmation context better.

---

## Notes

This keeps the self-contained HTML/JS review page pattern. No new frontend
framework or server is introduced.
