# Plan #204: Claim Ledger CLI/MCP Offset Pagination

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Claim Ledger API Offset Pagination
**Blocks:** INV-9 agent-drivable claim interpretation

---

## Gap

**Current:** API `/projects/{project_id}/claims` supports bounded
`limit`/`offset` traversal with count metadata, but MCP `qc_get_claims` and CLI
`project claims` only expose first-window reads by `limit`. MCP can request a
large limit, and CLI can show a truncation count, but neither surface has an
explicit offset contract for deterministic bounded traversal.

**Target:** Add offset traversal to the non-API general claim-ledger read
surfaces:

- MCP `qc_get_claims(project_id, limit=50, offset=0)` clamps negative
  `limit`/`offset` to zero, slices rows by `offset:offset + limit`, and returns
  top-level `returned`, `total_claims`, `limit`, and `offset`.
- CLI `project claims --offset N` clamps negative offsets to zero and displays
  the requested page while preserving the existing compact default when no
  offset/truncation is involved.

**Why:** Agent-driven and local operator claim inspection should use the same
bounded traversal model across API, MCP, and CLI. This is read-surface
pagination/accounting only; it does not add claim truth, expert adjudication,
D7 evidence, disconfirmation validity, or SOTA evidence.

---

## References Reviewed

- `docs/plans/completed/CLAIM_LEDGER_API_OFFSET_PAGINATION.md` - API offset
  pagination precedent.
- `qc_mcp_server.py:323-363` - current MCP claim-ledger read surface.
- `qc_clean/core/cli/commands/project.py:661-703` - current CLI claim-ledger
  display and truncation behavior.
- `qc_cli.py:1217-1228` - current `project claims` parser options.
- `tests/test_mcp_server.py:340-385` - current MCP claim-ledger tests.
- `tests/test_project_commands.py:1688-1728,1826-1915` - current CLI parser and
  claim display tests.
- `docs/PROJECT_THEORY_AND_GOALS.md:510` - INV-9 claim ledger caveats.
- Memory context:
  `agent-memory recall 'qualitative_coding qc_get_claims project claims offset pagination limit metadata active decisions' --project qualitative_coding`
  — old completed outcomes only; no active decision.
- Coordination context: `~/.claude/coordination/claims/` contains only
  unrelated `agentic_scaffolding` / `llm_client` write claims.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is deterministic
read-surface parity over existing persisted claim rows.

---

## Capabilities

This plan modifies project-local CLI and MCP read surfaces only. It does not
create a cross-project boundary, registry entry, or new evaluation capability.

---

## Files Affected

- `qc_mcp_server.py` (modify)
- `qc_clean/core/cli/commands/project.py` (modify)
- `qc_cli.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `tests/test_project_commands.py` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/CLAIM_LEDGER_CLI_MCP_OFFSET_PAGINATION.md` (create)

---

## Plan

### Steps

1. Add TDD tests for MCP `qc_get_claims(..., limit=1, offset=1)` and negative
   offset behavior, including returned pagination metadata.
2. Add TDD parser and display tests for `project claims --offset`.
3. Implement MCP offset slicing and metadata.
4. Implement CLI parser/display offset support while preserving compact default
   output for non-truncated first pages.
5. Update docs to describe API/MCP/CLI bounded traversal as structural
   accounting, not evidence.
6. Run focused tests, focused Ruff, docs checks, whitespace checks, and the full
   deterministic gate.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_mcp_server.py` | `test_get_claims_limit_offset_metadata` | MCP `qc_get_claims` reports limit/offset/total metadata and pages rows. |
| `tests/test_mcp_server.py` | `test_get_claims_negative_offset` | MCP negative offset clamps to zero. |
| `tests/test_project_commands.py` | `test_claims_subparser_accepts_offset` | CLI parser accepts `project claims --offset`. |
| `tests/test_project_commands.py` | `test_project_claims_command_outputs_offset_page` | CLI displays the requested offset page and page metadata. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_mcp_server.py tests/test_project_commands.py -q` | Protect MCP and CLI project surfaces. |
| `python -m ruff check qc_mcp_server.py qc_clean/core/cli/commands/project.py qc_cli.py tests/test_mcp_server.py tests/test_project_commands.py` | Focused lint for modified files. |
| `make docs-check` | Plan/docs consistency and generated-agent sync. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] MCP `qc_get_claims` accepts `offset`.
- [ ] MCP response reports top-level `returned`, `total_claims`, `limit`, and
  `offset`.
- [ ] MCP positive offsets page claim rows after the applied offset.
- [ ] MCP negative offsets clamp to `offset: 0`.
- [ ] CLI `project claims` accepts `--offset`.
- [ ] CLI positive offsets display the requested claim page with visible page
  metadata.
- [ ] CLI default output without offset/truncation remains compact.
- [ ] Existing scope and anchor detail fields/output remain unchanged.

Process criteria:

- [ ] Required focused tests pass.
- [ ] Focused Ruff passes.
- [ ] `make docs-check` passes.
- [ ] `make check` passes or any failure is documented with evidence.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should review-specific MCP/API claim listing also gain offset traversal?
  — Status: DEFERRED | Why it matters: review-specific surfaces are still
  bounded first-window listings; this slice targets general claim-ledger reads.

---

## Notes

Do not change claim ordering, scope serialization, or anchor-detail formatting.
This is paging and metadata parity only.
