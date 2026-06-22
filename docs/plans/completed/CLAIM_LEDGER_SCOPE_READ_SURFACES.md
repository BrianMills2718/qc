# Plan #201: Claim Ledger Scope Read Surfaces

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Claim Ledger Anchor Detail Read Surfaces
**Blocks:** INV-9 agent-drivable claim interpretation

---

## Outcome

Completed 2026-06-22. General claim-ledger read surfaces now expose claim
scope without requiring review mode: API `/projects/{project_id}/claims`
includes serialized scope, MCP `qc_get_claims` includes the same scope payload,
and CLI `project claims --show-scope` prints compact scope summaries while the
default CLI output remains compact. This is structural scope visibility only;
it is not claim truth, expert adjudication, D7 evidence, disconfirmation
validity, or SOTA evidence.

## Verification

- TDD red: focused tests initially failed on missing API/MCP `scope` fields and
  missing CLI `--show-scope` parser/output behavior.
- Focused tests:
  `python -m pytest tests/test_review_api.py tests/test_mcp_server.py tests/test_project_commands.py -q`
  (`191 passed`).
- Focused Ruff:
  `python -m ruff check qc_clean/plugins/api/api_server.py qc_mcp_server.py qc_clean/core/cli/commands/project.py qc_cli.py tests/test_review_api.py tests/test_mcp_server.py tests/test_project_commands.py`.
- Docs gate: `make docs-check`.
- Full gate: `make check` (`1268 passed, 1 skipped, 8 deselected`; type check
  not configured).
- Implementation commit pushed:
  `afc6ef39 [Plan: CLAIM_SCOPE] Expose claim read scope details`.

## Gap

**Current:** General claim-ledger read surfaces expose claim IDs, kind, text,
status, origins, and bounded anchor details, but they omit `ClaimScope`:

- API `/projects/{project_id}/claims` rows do not include `scope`.
- MCP `qc_get_claims(project_id)` rows do not include `scope`.
- CLI `project claims` prints compact claim text only.

Review rows already include `scope`, so this is a read-surface parity gap. An
agent inspecting claims outside review mode cannot tell whether a claim is
scoped to codes, documents, participants, relationships, other claims, or the
corpus without loading the full project state.

**Target:** Extend general claim-ledger read surfaces with bounded, explicit
scope context:

- API `/projects/{project_id}/claims` includes `scope` for each returned row.
- MCP `qc_get_claims(project_id)` includes the same `scope` payload.
- CLI `project claims --show-scope` prints a compact
  `format_claim_scope_summary()` line for each displayed claim while preserving
  the existing compact default.

**Why:** A first-class claim ledger is not agent-drivable if claim text is shown
without its scope. This improves structural interpretability only; it does not
validate claim truth or add human/expert adjudication.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:510` - INV-9 claim ledger status and
  caveats.
- `docs/plans/completed/CLAIM_LEDGER_ANCHOR_DETAIL_READ_SURFACES.md` - general
  read-surface precedent for bounded detail fields.
- `qc_clean/core/claims.py:460-477` - `format_claim_scope_summary()`.
- `qc_clean/plugins/api/api_server.py:758-780` - API claim read rows.
- `qc_mcp_server.py:336-360` - MCP claim read rows.
- `qc_clean/core/cli/commands/project.py:656-708` - CLI claim summary and
  anchor-detail output.
- `qc_cli.py:1216-1223` - `project claims` parser.
- `tests/test_review_api.py:184-230`, `tests/test_mcp_server.py:354-392`,
  and `tests/test_project_commands.py:1687-1708,1800-1905` - current claim
  read-surface tests.
- Memory context:
  `agent-memory recall 'qualitative_coding claim ledger read surfaces scope details active decisions' --project qualitative_coding`
  — old completed outcomes only; no active decision.
- Coordination context: `~/.claude/coordination/claims/` contains only an
  unrelated `llm_client` write claim.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is deterministic
payload/display parity over existing persisted claim-scope models.

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

1. Add TDD tests for API and MCP claim-ledger rows including `scope`.
2. Add parser/output tests for `project claims --show-scope`.
3. Reuse `ClaimScope.model_dump(mode="json")` for API/MCP rows and
   `format_claim_scope_summary()` for CLI display.
4. Update docs to distinguish scope visibility from validity/adjudication.
5. Run focused tests, Ruff, docs checks, and `make check`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_get_project_claims_includes_scope` | API claim-ledger rows include serialized `ClaimScope`. |
| `tests/test_mcp_server.py` | `test_get_claims` | MCP claim-ledger rows include serialized `ClaimScope`. |
| `tests/test_project_commands.py` | `test_claims_subparser_accepts_show_scope` | CLI parser accepts `project claims --show-scope`. |
| `tests/test_project_commands.py` | `test_project_claims_command_outputs_scope_when_requested` | CLI prints compact claim scope only when requested. |

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

- [x] API `/projects/{project_id}/claims` rows include serialized `scope`.
- [x] MCP `qc_get_claims` rows include the same serialized `scope`.
- [x] CLI `project claims` default output remains compact.
- [x] CLI `project claims --show-scope` prints compact scope summaries for
  each displayed claim.
- [x] Docs state this is structural scope visibility, not claim-validity
  evidence, human/expert adjudication, D7 evidence, or SOTA.

Process criteria:

- [x] Required focused tests pass.
- [x] Focused Ruff passes.
- [x] `make docs-check` passes.
- [x] `make check` passes or any failure is documented with evidence.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should claim read surfaces support query filters by kind, support status,
  adjudication status, or scope? — Status: DEFERRED | Why it matters: filters
  are useful but should be designed as a separate bounded query surface.

---

## Notes

Used existing `ClaimScope` serialization and `format_claim_scope_summary()`.
Do not expand scope visibility into claim truth assertions. Scope tells users
what a claim purports to cover; it does not prove that coverage is valid.
