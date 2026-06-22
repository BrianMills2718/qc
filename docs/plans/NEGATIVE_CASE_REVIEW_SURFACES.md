# Plan #90: Negative Case Review Surfaces

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Claim review API listing; Relationship review browser UI
**Blocks:** INV-10 negative-case-specific adjudication UX

---

## Gap

**Current:** Negative cases are emitted as `AnalyticClaim` rows with
`claim_kind="negative_case"`, so they are technically reviewable through the
generic claim-review path. They are not exposed as a negative-case-specific
review surface in the API, MCP, or browser UI, which makes disconfirmation
review easy to miss in large mixed claim ledgers.

**Target:** Add negative-case-specific review listing surfaces that filter the
claim ledger to `ClaimKind.NEGATIVE_CASE` while preserving the shared claim
decision semantics:

- API: `/projects/{project_id}/review/negative-cases`
- MCP: `qc_review_negative_cases(project_id, limit=100)`
- Browser: Negative Cases mode in `/review/{project_id}`

Review decisions should still submit `target_type="claim"` because the reviewed
object remains the negative-case claim row.

**Why:** INV-10 names negative cases explicitly. A generic claim table is not a
first-class negative-case review workflow. This slice makes disconfirmation
review visible and agent-drivable without inventing a parallel object model.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:141` - negative case stage writes
  negative-case claim objects with target/candidate anchors where resolvable.
- `docs/PROJECT_THEORY_AND_GOALS.md:363` - INV-10 remaining gap is
  negative-case-specific review UX and expert protocol.
- `qc_clean/core/claims.py` - `claims_for_negative_cases()` creates
  `ClaimKind.NEGATIVE_CASE` rows.
- `qc_clean/schemas/domain.py` - `ClaimKind.NEGATIVE_CASE` and claim review
  models.
- `qc_clean/plugins/api/api_server.py` - existing claim/relationship review API.
- `qc_mcp_server.py` - existing MCP claim/relationship review listing tools.
- `qc_clean/plugins/api/review_ui.py` - existing Codes/Claims/Relationships
  browser review modes.
- `tests/test_review_api.py` and `tests/test_mcp_server.py` - review-surface
  regression tests.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
filtered review surface for an existing claim kind.

---

## Capabilities

This plan modifies project-local API/MCP/UI surfaces only. It does not create a
cross-project callable boundary.

---

## Files Affected

- `qc_clean/plugins/api/api_server.py` (modify)
- `qc_mcp_server.py` (modify)
- `qc_clean/plugins/api/review_ui.py` (modify)
- `tests/test_review_api.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/NEGATIVE_CASE_REVIEW_SURFACES.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a compact claim-review row helper to API code if needed to avoid
   duplicate claim row formatting.
2. Add `/projects/{project_id}/review/negative-cases` that returns only
   `ClaimKind.NEGATIVE_CASE` rows, bounded to 100, with `negative_cases`,
   `returned`, `total_negative_cases`, and review summary metadata.
3. Add `qc_review_negative_cases(project_id, limit=100)` with the same bounded
   filter and shape for MCP clients.
4. Add a Negative Cases browser mode that fetches `/review/negative-cases`,
   renders those rows through the existing claim-card decision path, and submits
   `target_type="claim"`.
5. Update API endpoint inventory/docstrings where applicable.
6. Add API, MCP, and static browser UI tests.
7. Update docs conservatively: negative-case-specific review surface exists, but
   expert adjudication and held-out D7 validity remain absent.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_returns_negative_cases_for_review` | API returns only negative-case claim rows with challenged claim IDs/scope. |
| `tests/test_review_api.py` | `test_review_page_exposes_negative_case_review_ui` | Browser page exposes Negative Cases mode and decision path. |
| `tests/test_mcp_server.py` | `test_review_negative_cases` | MCP lists negative-case review targets. |
| `tests/test_mcp_server.py` | `test_review_negative_cases_limit` | MCP limit behavior matches claim/relationship listing. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_review_api.py tests/test_mcp_server.py -q` | API/MCP/UI review behavior remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] API exposes bounded negative-case review rows.
- [ ] MCP exposes bounded negative-case review rows.
- [ ] Browser review page has a Negative Cases mode.
- [ ] Negative-case decisions still submit `target_type="claim"`.
- [ ] Non-negative-case claims are excluded from negative-case-specific listing.
- [ ] Docs state this narrows INV-10 but does not add expert adjudication or
  held-out D7 validity evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should negative-case review eventually show retrieved candidate details
  beyond the claim anchor counts? - Status: DEFERRED | Why it matters:
  candidate-level adjudication may need a richer object than the claim row.
- [ ] Should negative-case decisions update challenged target claims? - Status:
  DEFERRED | Why it matters: the current slice reviews the negative-case claim
  itself; target-claim propagation is a separate adjudication policy.

---

## Notes

This plan does not claim that negative cases have been found exhaustively or
validated. It only makes existing negative-case claim rows easier to review.
