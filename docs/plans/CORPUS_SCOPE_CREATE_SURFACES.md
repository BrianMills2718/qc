# Plan #76: Corpus Scope Create Surfaces

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #16 corpus scope contract; Plan #19 CLI/API scope surfaces
**Blocks:** lower-friction scope discipline for new projects

---

## Gap

**Current:** `project scope` and `/projects/{id}/scope` can read/update
`ProjectState.corpus_scope` after a project exists, but project creation does
not accept scope fields. Operators must remember to run a second command before
claim-bearing exports avoid missing-scope warnings.

**Target:** Add optional corpus-scope fields to CLI `project create` and MCP
`qc_create_project`. When any scope field is supplied, the new project is saved
with `ProjectState.corpus_scope`; when none are supplied, creation behavior is
unchanged. The API has no project-create endpoint, so its existing scope update
endpoint remains the API route.

**Why:** Capturing scope at project creation reduces silent missing-boundary
states. It remains report discipline only; a recorded scope does not validate
sampling adequacy.

---

## References Reviewed

- `docs/plans/completed/CORPUS_SCOPE_CONTRACT.md` - deferred create-scope
  question.
- `docs/plans/completed/CORPUS_SCOPE_CLI_API.md` - existing scope read/update
  surfaces and deferred project-create question.
- `qc_cli.py` - CLI parser for `project create` and `project scope`.
- `qc_clean/core/cli/commands/project.py` - project creation and scope update
  command handlers.
- `qc_mcp_server.py` - MCP `qc_create_project` tool.
- `tests/test_project_commands.py` - CLI parser and command tests.
- `tests/test_mcp_server.py` - MCP project creation tests.
- Memory context: `agent-memory recall 'corpus scope create surfaces' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic surface-completion slice for an existing state contract.

---

## Capabilities

This plan modifies repo-local CLI/MCP surfaces only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_cli.py` (modify)
- `qc_clean/core/cli/commands/project.py` (modify)
- `qc_mcp_server.py` (modify)
- `tests/test_project_commands.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CORPUS_SCOPE_CREATE_SURFACES.md` (create, then move to completed)

---

## Plan

### Steps

1. Add the same scope flags accepted by `project scope` to `project create`.
2. Build a `CorpusScope` during create only when at least one scope field is
   supplied.
3. Extend MCP `qc_create_project` with optional scope parameters and include
   scope metadata in the returned payload.
4. Add parser/handler/MCP tests for populated scope and preserve existing
   no-scope behavior.
5. Update docs to describe create-time scope capture without claiming sampling
   adequacy.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_project_commands.py` | `test_create_subparser_accepts_scope_fields` | CLI `project create` parses optional scope flags. |
| `tests/test_project_commands.py` | `test_project_create_command_saves_scope_when_supplied` | CLI creation persists `ProjectState.corpus_scope` when scope fields are supplied. |
| `tests/test_mcp_server.py` | `test_create_project_with_scope` | MCP creation persists and returns corpus-scope metadata. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_project_commands.py::TestProjectScopeCommand` | Existing post-create scope update remains intact. |
| `tests/test_mcp_server.py::TestMCPServer::test_create_project` | Existing MCP create behavior remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] CLI `project create` accepts optional `--phenomenon`, `--population`,
  `--sampling-frame`, repeated `--include`, repeated `--exclude`, and `--notes`.
- [ ] CLI creation persists `corpus_scope` only when at least one scope field is
  supplied.
- [ ] MCP `qc_create_project` accepts equivalent optional scope parameters,
  persists `corpus_scope`, and returns scope metadata.
- [ ] Existing no-scope creation behavior remains compatible.
- [ ] Docs state create-time scope is report discipline, not sampling-frame
  validation.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [x] Should this add an API project-create endpoint? — Status: RESOLVED |
  Answer: No. The API currently has scope read/update endpoints but no
  project-create route; adding one would be a separate API design slice.

---

## Notes

Do not copy project scope into each claim in this slice. That deferred question
has staleness implications if the project scope changes later.
