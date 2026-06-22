# Plan #202: Claim Ledger API Limit Metadata

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Claim Ledger Scope Read Surfaces
**Blocks:** INV-9 agent-drivable claim interpretation

---

## Outcome

Completed 2026-06-22. API `/projects/{project_id}/claims` now accepts a
`limit` query parameter, clamps it to the configured first-window policy
(`claim_ledger_api_max_rows`, default `100`) and zero for negative inputs, and
returns `returned`, `total_claims`, and applied `limit` metadata. Existing
claim row fields, including serialized scope and bounded anchor details, remain
unchanged. This is read-surface accounting only; it is not claim truth, expert
adjudication, D7 evidence, disconfirmation validity, or SOTA evidence.

## Verification

- TDD red: `python -m pytest tests/test_review_api.py -q` initially failed on
  missing `returned` metadata for the new tests.
- Focused tests: `python -m pytest tests/test_review_api.py -q` (`40 passed`).
- Focused Ruff:
  `python -m ruff check qc_clean/plugins/api/api_server.py tests/test_review_api.py`.
- Docs gate: `make docs-check`.
- Whitespace gate: `git diff --check`.
- Full gate: `make check` (`1270 passed, 1 skipped, 8 deselected`; Ruff/docs
  passed; type check not configured).
- Implementation commit pushed:
  `7d1b2a36 [Plan: CLAIM_API_LIMIT] Expose claim API limit metadata`.

## Gap

**Current:** API `/projects/{project_id}/claims` returns claim-ledger summaries
and the first 100 claim rows via a hard-coded `state.claims[:100]` slice. MCP
and CLI claim-read surfaces accept explicit limits, and review API/MCP surfaces
return `returned`, `total_*`, and `limit` metadata. The general API claim
ledger endpoint does not expose its row cap to callers and does not report
whether the returned rows are complete or truncated.

**Target:** Add an explicit `limit` query parameter to
`/projects/{project_id}/claims`, preserve the existing default/hard maximum of
100 rows, clamp negative limits to zero, and return `returned`,
`total_claims`, and `limit` metadata beside the existing summaries and claim
rows.

**Why:** Agent-driven claim review should not have to infer truncation from an
undocumented slice. This is read-surface accounting only; it does not add claim
truth, adjudication, held-out D7 evidence, semantic disconfirmation validity, or
SOTA evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:105` - claim ledger object contract.
- `docs/PROJECT_THEORY_AND_GOALS.md:644` - INV-9/10 remaining read/review
  gaps.
- `docs/plans/completed/CLAIM_LEDGER_SCOPE_READ_SURFACES.md` - immediately
  preceding API/MCP/CLI claim read-surface parity slice.
- `qc_clean/plugins/api/api_server.py:741-780` - current API claim-ledger
  endpoint with hard-coded `state.claims[:100]`.
- `qc_clean/plugins/api/api_server.py:465-518` - review API count/limit
  metadata precedent.
- `qc_mcp_server.py:323-363` - MCP claim-ledger limit precedent.
- `qc_clean/core/cli/commands/project.py:661-703` - CLI claim-ledger limit
  precedent.
- `tests/test_review_api.py:184-245` - current API claim-ledger tests.
- Memory context:
  `agent-memory recall 'qualitative_coding active decisions claim ledger read surfaces API limit filters scope anchors roadmap' --project qualitative_coding`
  — old completed outcomes only; no active decision.
- Coordination context: `~/.claude/coordination/claims/` contains only an
  unrelated `llm_client` write claim.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is deterministic
read-surface parity over existing persisted claim rows.

---

## Capabilities

This plan modifies one project-local HTTP read endpoint only. It does not
create a cross-project boundary, registry entry, or new evaluation capability.

---

## Files Affected

- `qc_clean/plugins/api/api_server.py` (modify)
- `tests/test_review_api.py` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/CLAIM_LEDGER_API_LIMIT_METADATA.md` (create)

---

## Plan

### Steps

1. Add TDD tests proving API claim-ledger responses include `returned`,
   `total_claims`, and `limit`.
2. Add TDD tests proving `limit=1` truncates rows visibly and negative limits
   return zero rows with `limit: 0`.
3. Implement the endpoint parameter using the existing claim-row payload shape.
4. Run focused tests, focused Ruff, docs checks, whitespace checks, and the full
   deterministic gate.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_get_project_claims_includes_limit_metadata` | Default API response reports returned row count, total claim count, and the default cap. |
| `tests/test_review_api.py` | `test_get_project_claims_limit_parameter` | Explicit small and negative limits produce visible, bounded row windows. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_review_api.py -q` | Protect API claim/review surfaces. |
| `python -m ruff check qc_clean/plugins/api/api_server.py tests/test_review_api.py` | Focused lint for modified implementation/tests. |
| `make docs-check` | Plan/docs consistency. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] API `/projects/{project_id}/claims` accepts `limit`.
- [x] Default API behavior returns at most 100 claim rows and reports
  `limit: 100`.
- [x] Explicit positive limits return at most that many claim rows and report
  the applied limit.
- [x] Negative limits return zero claim rows and report `limit: 0`.
- [x] API response reports `returned` and `total_claims`.
- [x] Existing claim row fields, including scope and anchor details, remain
  unchanged.

Process criteria:

- [x] Required focused tests pass.
- [x] Focused Ruff passes.
- [x] `make docs-check` passes.
- [x] `make check` passes or any failure is documented with evidence.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should the API support offset/cursor pagination for claim rows beyond the
  first 100? — Status: DEFERRED | Why it matters: complete traversal of very
  large ledgers needs a pagination contract, but this slice only makes the
  existing first-window cap explicit.

---

## Notes

Preserve the existing 100-row default and cap to avoid changing API response
size unexpectedly. This plan makes truncation visible; it does not claim full
ledger traversal for large projects.
