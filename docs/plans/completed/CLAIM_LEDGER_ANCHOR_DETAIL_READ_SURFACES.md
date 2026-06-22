# Plan #200: Claim Ledger Anchor Detail Read Surfaces

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Negative Case Review Anchor Details
**Blocks:** INV-9/INV-10 agent-drivable claim evidence inspection

---

## Outcome

Completed 2026-06-22. General claim-ledger read surfaces now expose bounded
anchor details without requiring review mode:

- API `/projects/{project_id}/claims` rows include supporting/contrary anchor
  counts plus bounded detail payloads.
- MCP `qc_get_claims(project_id)` rows include the same bounded detail payloads.
- CLI `project claims --show-anchors` prints bounded supporting/contrary anchor
  details; default `project claims` output remains compact.

This is evidence visibility only. It does not validate claim truth, add expert
adjudication, create held-out D7 evidence, prove disconfirmation validity, or
support SOTA claims.

## Verification

- TDD red state observed:
  `python -m pytest tests/test_review_api.py tests/test_mcp_server.py tests/test_project_commands.py -q`
  failed on missing API/MCP anchor details and missing `--show-anchors`.
- Focused tests passed:
  `python -m pytest tests/test_review_api.py tests/test_mcp_server.py tests/test_project_commands.py -q`
  (`188 passed`).
- Focused Ruff passed:
  `python -m ruff check qc_clean/plugins/api/api_server.py qc_mcp_server.py qc_clean/core/cli/commands/project.py qc_cli.py tests/test_review_api.py tests/test_mcp_server.py tests/test_project_commands.py`.
- Docs gate passed: `make docs-check`.
- Full gate passed: `make check` (`1265 passed, 1 skipped, 8 deselected`;
  Ruff and docs checks passed; type check remains not configured).
- Implementation commit pushed:
  `d6be36c6 [Plan: CLAIM_ANCHORS] Expose claim read anchor details`.

---

## Gap

**Current:** API/MCP/browser review rows now expose bounded supporting and
contrary anchor details, but the general claim-ledger read surfaces still expose
mostly counts:

- API `/projects/{project_id}/claims` omits anchor counts/details.
- MCP `qc_get_claims(project_id)` includes anchor counts but omits details.
- CLI `project claims` prints compact claim text only.

An agent inspecting the ledger outside review mode cannot see the exact
evidence document, offsets, hash, and quote text attached to a claim.

**Target:** Extend the bounded `format_claim_anchor_details()` helper to the
general claim-ledger read surfaces:

- API `/projects/{project_id}/claims` includes bounded supporting/contrary
  anchor counts and detail payloads for each returned claim row.
- MCP `qc_get_claims(project_id)` includes the same detail payloads.
- CLI `project claims --show-anchors` prints bounded supporting/contrary anchor
  details while preserving the existing compact default.

**Why:** Claim-ledger inspection should be agent-drivable without requiring the
review workflow. This improves evidence visibility only; it does not validate
claim truth, add expert review, or create held-out D7 evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:502-510` - INV-2/INV-6/INV-9 claim and
  disconfirmation caveats.
- `docs/plans/completed/NEGATIVE_CASE_REVIEW_ANCHOR_DETAILS.md` - shared
  anchor-detail helper and review-row precedent.
- `qc_clean/core/claims.py:477-503` - `format_claim_anchor_details()`.
- `qc_clean/plugins/api/api_server.py:737-769` - API claim-ledger rows.
- `qc_mcp_server.py:323-354` - MCP `qc_get_claims` row shape.
- `qc_clean/core/cli/commands/project.py:656-692` - CLI claim summary output.
- `qc_cli.py:1216-1218` - `project claims` parser.
- `tests/test_review_api.py:184-191`, `tests/test_mcp_server.py:354-359`,
  and `tests/test_project_commands.py:1687-1694,1800-1827` - existing claim
  read-surface tests.
- Memory context:
  `agent-memory recall 'qualitative_coding active decisions next deterministic roadmap lane INV10 D7 adjudication review anchor details' --project qualitative_coding`
  — old completed outcomes only; no active decision.
- Coordination context: `~/.claude/coordination/claims/` contains only an
  unrelated `llm_client` write claim.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is deterministic
payload/display parity over existing persisted claim anchors.

---

## Capabilities

This plan modifies project-local CLI/API/MCP read surfaces only. It does not
create a cross-project boundary, registry entry, or new evaluation capability.

---

## Files Affected

- `qc_clean/plugins/api/api_server.py` (modify)
- `qc_mcp_server.py` (modify)
- `qc_clean/core/cli/commands/project.py` (modify)
- `qc_cli.py` (modify)
- `tests/test_review_api.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `tests/test_project_commands.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add TDD tests for API and MCP claim-ledger rows including bounded anchor
   details.
2. Add parser/output tests for `project claims --show-anchors`.
3. Reuse `format_claim_anchor_details()` in API/MCP read rows and CLI output.
4. Update docs to distinguish evidence visibility from validity evidence.
5. Run focused tests, Ruff, docs checks, and `make check`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_get_project_claims_includes_anchor_details` | API claim-ledger rows include bounded supporting/contrary anchor detail payloads. |
| `tests/test_mcp_server.py` | `test_get_claims` | MCP claim-ledger rows include the same bounded anchor detail payloads. |
| `tests/test_project_commands.py` | `test_claims_subparser_accepts_show_anchors` | CLI parser accepts `project claims --show-anchors`. |
| `tests/test_project_commands.py` | `test_project_claims_command_outputs_anchor_details_when_requested` | CLI prints bounded anchor details only when requested. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_review_api.py tests/test_mcp_server.py tests/test_project_commands.py -q` | Protect API/MCP/CLI project surfaces. |
| `python -m ruff check qc_clean/plugins/api/api_server.py qc_mcp_server.py qc_clean/core/cli/commands/project.py qc_cli.py tests/test_review_api.py tests/test_mcp_server.py tests/test_project_commands.py` | Focused lint for modified files. |
| `make docs-check` | Plan/docs sync and generated-agent governance. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] API `/projects/{project_id}/claims` rows include supporting/contrary
  anchor counts and bounded detail payloads.
- [x] MCP `qc_get_claims` rows include the same bounded detail payloads.
- [x] CLI `project claims` default output remains compact.
- [x] CLI `project claims --show-anchors` prints bounded supporting/contrary
  anchor details with doc ID, offsets, hash, optional application ID, and quote
  text.
- [x] Docs state this is evidence visibility, not claim-validity evidence,
  expert adjudication, D7 evidence, or SOTA.

Process criteria:

- [x] Required focused tests pass.
- [x] Focused Ruff passes.
- [x] `make docs-check` passes.
- [x] `make check` passes or any failure is documented with evidence.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should claim rows eventually return full source context around anchors?
  — Status: DEFERRED | Why it matters: source-window context is useful but can
  bloat payloads and belongs in a separate explicit context-window design.

---

## Notes

Used the existing bounded helper. No unbounded claim, document, or
retrieved-candidate dumps were added to any read surface.
