# Plan #85: Claim Review Browser UI

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Claim review API listing; MCP claim review decisions
**Blocks:** INV-10 browser-native adjudication beyond code labels

---

## Gap

**Current:** Claim review is agent-drivable through `/projects/{id}/review/claims`,
`/projects/{id}/review/decisions`, and MCP tools, but the browser review page at
`/review/{project_id}` still loads only `/review/codes`. Humans using the
browser can review code labels/applications, but not the claim ledger.

**Target:** Extend the existing self-contained review page with a code/claim
mode switch. Claim mode should fetch `/projects/{id}/review/claims`, render
bounded claim review cards, and submit approve/reject/modify decisions with
`target_type="claim"` through the existing generic decision endpoint.

**Why:** INV-10 says adjudication must reach claims, not only code labels.
The API/MCP path exists; the browser path remains a documented gap. A small
tabbed addition closes the first browser-native claim-review slice without
inventing a new frontend stack.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:360-370` - INV-9/10 claim ledger and review status.
- `docs/PROJECT_THEORY_AND_GOALS.md:443-452` - roadmap lists browser-native claim review UI as remaining work.
- `qc_clean/plugins/api/review_ui.py` - existing self-contained code review page.
- `qc_clean/plugins/api/api_server.py` - existing `/review/codes`, `/review/claims`, and `/review/decisions` endpoints.
- `tests/test_review_api.py` - current API and review page tests.
- `qc_clean/core/pipeline/review.py` - shared claim decision application behavior.
- Memory context: not retried because `agent-memory recall` has repeatedly failed with provider 402/403 in this long-running session; circuit breaker remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
browser surface for an existing claim-review API.

---

## Capabilities

This plan modifies an existing browser UI and does not create a cross-project
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
- `docs/plans/CLAIM_REVIEW_BROWSER_UI.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a compact mode switch to the review page action bar for Codes and Claims.
2. Refactor load/render logic so code mode keeps current behavior and claim mode
   fetches `/projects/{id}/review/claims`.
3. Render claim cards with claim text, kind, source stage, support/adjudication
   statuses, scope hints, anchor counts, and approve/reject/modify actions.
4. Submit claim decisions through the existing `/review/decisions` endpoint with
   `target_type="claim"` and `target_id=<claim_id>`.
5. Keep existing code/application review behavior unchanged.
6. Add static HTML tests that prove the page exposes the claim mode, claim API
   fetch, claim decision target type, and claim-card renderer.
7. Update docs conservatively: this is a browser-native claim-review first
   slice, not expert adjudication or full INV-10.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_review_page_exposes_claim_review_ui` | Browser page includes claim mode, `/review/claims` fetch path, and claim decision target type. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_review_api.py -q` | Review page/API behavior remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Review page has a visible code/claim mode switch.
- [x] Claim mode fetches `/projects/{id}/review/claims`.
- [x] Claim cards show claim text and review-relevant metadata.
- [x] Claim approve/reject/modify decisions submit `target_type="claim"`.
- [x] Existing code and application review behavior is preserved.
- [x] Docs state this narrows INV-10 but does not create expert adjudication.

> Process criteria:
- [x] Required focused tests pass.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Verification

- Initial TDD run: `python -m pytest tests/test_review_api.py::TestReviewUIPage::test_review_page_exposes_claim_review_ui -q` failed because `id="claimModeBtn"` was absent.
- `python -m pytest tests/test_review_api.py::TestReviewUIPage::test_review_page_exposes_claim_review_ui -q` - passed.
- `python -m pytest tests/test_review_api.py -q` - `26 passed`.
- `python -m ruff check qc_clean/plugins/api/review_ui.py tests/test_review_api.py` - passed.
- `python scripts/check_markdown_links.py && python scripts/sync_plan_status.py --check && python scripts/meta/check_agents_sync.py --check` - passed.
- `make check` - `813 passed, 1 skipped, 8 deselected`; Ruff and docs checks passed; type check is not yet configured.

---

## Open Questions

- [ ] Should relationship and negative-case review get separate browser tabs? - Status: DEFERRED | Why it matters: INV-10 also names those surfaces, but claim review is the highest-value shared object layer.
- [ ] Should browser claim review support bulk filtering by source stage/support status? - Status: DEFERRED | Why it matters: useful for large ledgers, but not required for the first browser-native claim-review slice.

---

## Notes

This plan does not add expert sampling, blinding, or methodological validity
evidence. It makes the existing claim-review workflow browser-native.
