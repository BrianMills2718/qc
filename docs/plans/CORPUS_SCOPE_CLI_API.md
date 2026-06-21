# Plan #19: Corpus Scope CLI/API Surfaces

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #16 corpus scope contract
**Blocks:** scope-aware report phrasing checks; sampling-frame evaluation

---

## Gap

**Current:** `ProjectState.corpus_scope` can be stored and appears in Markdown
exports, but there is no agent-drivable CLI or JSON API surface to read or
update it. Agents must mutate project JSON directly to set scope, which violates
the project rule that operations should be invocable through stable interfaces.

**Target:** Add a CLI command and REST endpoints for reading/updating corpus
scope:

- `qc_cli project scope <project_id>` — show current scope.
- `qc_cli project scope <project_id> --phenomenon ... --population ... --sampling-frame ... --include ... --exclude ... --notes ...` — update supplied scope fields.
- `GET /projects/{project_id}/scope` — return current scope plus whether it is set.
- `PUT /projects/{project_id}/scope` — replace/update scope fields from JSON.

**Why:** The scope contract is only useful if agents and humans can set it
without hand-editing project state. This keeps the corpus boundary visible and
maintainable before report/export work.

---

## References Reviewed

- `docs/plans/completed/CORPUS_SCOPE_CONTRACT.md` - completed state/export contract.
- `qc_clean/schemas/domain.py` - `CorpusScope` and `ProjectState.corpus_scope`.
- `qc_cli.py` - project subparser registration.
- `qc_clean/core/cli/commands/project.py` - project command handlers.
- `qc_clean/plugins/api/api_server.py` - existing project/claims endpoints.
- `tests/test_project_commands.py` - CLI parser and command tests.
- `tests/test_review_api.py` - FastAPI TestClient endpoint tests.

---

## Research Basis For This Slice

No external research is needed. This is interface wiring for an already-defined
typed state object.

---

## Capabilities

This plan adds repo-local CLI/API surfaces only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_cli.py` (modify)
- `qc_clean/core/cli/commands/project.py` (modify)
- `qc_clean/plugins/api/api_server.py` (modify)
- `tests/test_project_commands.py` (modify)
- `tests/test_review_api.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/CORPUS_SCOPE_CLI_API.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `project scope` parser in `qc_cli.py`.
2. Add `_show_or_update_scope()` in project command handlers.
3. Preserve existing scope fields when only some CLI flags are supplied.
4. Add `GET /projects/{project_id}/scope` and `PUT /projects/{project_id}/scope`.
5. Ensure `PUT` validates through `CorpusScope` and saves via `ProjectStore`.
6. Update endpoint registry and docs conservatively.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_project_commands.py` | `test_scope_subparser` | CLI parser captures scope flags and repeated include/exclude criteria. |
| `tests/test_project_commands.py` | `test_project_scope_command_updates_and_outputs_scope` | CLI updates persisted `CorpusScope` and prints it. |
| `tests/test_review_api.py` | `test_get_project_scope_returns_current_scope` | API read surface returns current scope fields. |
| `tests/test_review_api.py` | `test_put_project_scope_updates_scope` | API write surface validates/saves scope. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_project_commands.py` | Protect project CLI parser and command behavior. |
| `tests/test_review_api.py` | Protect project API endpoint registration and status. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] CLI can show scope when absent and when present.
- [ ] CLI can set phenomenon, population, sampling frame, inclusion criteria, exclusion criteria, and notes.
- [ ] API `GET /projects/{project_id}/scope` returns a stable JSON shape.
- [ ] API `PUT /projects/{project_id}/scope` validates and persists `CorpusScope`.
- [ ] Docs state these are read/update surfaces only, not sampling-frame validation.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should `project create` accept scope fields? — Status: DEFERRED | Why it matters: useful, but update/read surfaces are the smallest safe slice.
- [ ] Should Markdown export warn when claims exist but scope is absent? — Status: DEFERRED | Why it matters: likely valuable for report discipline, but it changes export semantics and belongs in a scope-aware phrasing plan.

---

## Notes

Do not describe this as validating the sampling frame. It only makes the scope
contract agent-drivable.
