# Plan #203: Claim Ledger API Offset Pagination

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Claim Ledger API Limit Metadata
**Blocks:** INV-9 agent-drivable claim interpretation

---

## Outcome

Completed 2026-06-22. API `/projects/{project_id}/claims` now accepts an
`offset` query parameter, clamps negative offsets to zero, returns applied
`offset` metadata, and slices claim rows with the existing bounded `limit` page
size. Offsets beyond the ledger return an empty page with `returned: 0` and the
unchanged `total_claims` count. This is API pagination/accounting only; it is
not claim truth, expert adjudication, D7 evidence, disconfirmation validity, or
SOTA evidence.

## Verification

- TDD red: `python -m pytest tests/test_review_api.py -q` initially failed on
  missing `offset` metadata for default, positive-offset, and bounded-offset
  tests.
- Focused tests: `python -m pytest tests/test_review_api.py -q` (`42 passed`).
- Focused Ruff:
  `python -m ruff check qc_clean/plugins/api/api_server.py tests/test_review_api.py`.
- Docs gate: `make docs-check`.
- Whitespace gate: `git diff --check`.
- Full gate: `make check` (`1272 passed, 1 skipped, 8 deselected`; Ruff/docs
  passed; type check not configured).
- Implementation commit pushed:
  `e287e289 [Plan: CLAIM_API_OFFSET] Add claim API offset pagination`.

## Gap

**Current:** API `/projects/{project_id}/claims` now exposes a first-window
`limit` and returns `returned`, `total_claims`, and applied `limit` metadata,
but callers still cannot retrieve claim rows beyond the first window. Large
claim ledgers are visibly truncated but not fully traversable through the API.

**Target:** Add an explicit non-negative `offset` query parameter to
`/projects/{project_id}/claims`, return applied `offset` metadata, and slice
claim rows with `state.claims[offset:offset + limit]` after applying the
existing configured per-page limit cap. Negative offsets clamp to zero; offsets
beyond `total_claims` return an empty page with metadata.

**Why:** Agent-driven claim interpretation needs deterministic traversal of the
whole claim ledger, not just visible truncation of the first page. This is API
pagination/accounting only; it does not add claim truth, expert adjudication,
D7 evidence, disconfirmation validity, or SOTA evidence.

---

## References Reviewed

- `docs/plans/completed/CLAIM_LEDGER_API_LIMIT_METADATA.md` - first-window
  limit metadata slice and deferred pagination question.
- `qc_clean/plugins/api/api_server.py:741-780` - current API claim-ledger
  limit and metadata implementation.
- `tests/test_review_api.py:184-245` - current API claim-ledger metadata tests.
- `qc_mcp_server.py:323-363` - MCP claim-ledger limit precedent.
- `qc_clean/core/cli/commands/project.py:661-703` - CLI claim-ledger limit and
  truncation display precedent.
- `docs/PROJECT_THEORY_AND_GOALS.md:510` - INV-9 claim ledger caveats.
- Memory context:
  `agent-memory recall 'qualitative_coding claim ledger API pagination offset limit metadata active decisions' --project qualitative_coding`
  — old completed outcomes only; no active decision.
- Coordination context: `~/.claude/coordination/claims/` contains only
  unrelated `agentic_scaffolding` / `llm_client` write claims.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is deterministic API
pagination over existing persisted claim rows.

---

## Capabilities

This plan modifies one project-local HTTP read endpoint only. It does not
create a cross-project boundary, registry entry, or new evaluation capability.

---

## Files Affected

- `qc_clean/plugins/api/api_server.py` (modify)
- `tests/test_review_api.py` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/CLAIM_LEDGER_API_OFFSET_PAGINATION.md` (create)

---

## Plan

### Steps

1. Add TDD tests proving `limit=1&offset=1` returns the second claim and
   reports `offset: 1`.
2. Add TDD tests proving negative offsets clamp to zero and offsets beyond the
   ledger return an empty page with `returned: 0`.
3. Implement `offset` on the API endpoint without changing existing claim row
   fields.
4. Update docs to describe API pagination as structural traversal/accounting,
   not evidence.
5. Run focused tests, focused Ruff, docs checks, whitespace checks, and the full
   deterministic gate.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_get_project_claims_offset_parameter` | Explicit offset pages to later claims and reports applied offset. |
| `tests/test_review_api.py` | `test_get_project_claims_offset_bounds` | Negative offsets clamp to zero; beyond-end offsets return empty pages. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_review_api.py -q` | Protect API claim/review surfaces. |
| `python -m ruff check qc_clean/plugins/api/api_server.py tests/test_review_api.py` | Focused lint for modified implementation/tests. |
| `make docs-check` | Plan/docs consistency and generated-agent sync. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] API `/projects/{project_id}/claims` accepts `offset`.
- [x] Default API behavior reports `offset: 0`.
- [x] Positive offsets page claim rows after the applied offset.
- [x] Negative offsets clamp to `offset: 0`.
- [x] Offsets beyond `total_claims` return an empty `claims` page with
  `returned: 0`.
- [x] Existing `limit`, `returned`, `total_claims`, and claim row fields remain
  unchanged.

Process criteria:

- [x] Required focused tests pass.
- [x] Focused Ruff passes.
- [x] `make docs-check` passes.
- [x] `make check` passes or any failure is documented with evidence.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should future API responses include cursor URLs or `next_offset`?
  — Status: DEFERRED | Why it matters: convenience helpers are useful, but
  `offset` + `limit` + `total_claims` is enough for deterministic traversal.

---

## Notes

Do not increase the configured per-page limit in this slice. Pagination enables
complete traversal by repeated bounded reads.
