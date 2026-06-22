# Plan #197: Project Export Publish Preflight Gate

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Export audit manifest workflow and export publish preflight scope lint
**Blocks:** One-command guarded export/handoff workflows

---

## Gap

**Current:** `project export` can write project artifacts, optionally write an
export-audit manifest, optionally verify that manifest, and optionally append
local audit events. Publish/handoff preflight exists as a separate
`export-publish-preflight` script/Make/`qc_cli.py` surface and can optionally
scope-lint Markdown/text artifacts, but `project export` cannot run that final
gate inline.

**Target:** Add explicit opt-in flags to `qc_cli.py project export`:

- `--publish-preflight`
- `--scope-lint`

`--publish-preflight` requires `--audit-manifest`, runs the same
`run_export_publish_preflight` gate after the manifest is written, and fails the
export command when preflight fails. `--scope-lint` requires
`--publish-preflight` and enables the existing Markdown/text scope phrasing gate.

**Why:** A one-command export/handoff workflow should be able to fail before
handoff when the just-written manifest or optional report-boundary checks fail,
without asking an agent to remember a second command.

**Non-target:** This slice does not change default export behavior, make
publish preflight mandatory, change export artifact content, validate
sampling-frame adequacy, sign artifacts, make audit logs append-only, create
external tamper evidence, or produce methodological-validity/SOTA evidence.

---

## References Reviewed

- `qc_clean/core/cli/commands/project.py` - `project export` and export-audit
  manifest/audit-event integration.
- `qc_clean/core/export/publish_preflight.py` - strict publish preflight and
  optional scope lint.
- `scripts/export_publish_preflight.py` - standalone publish-preflight CLI.
- `qc_cli.py` - `project export` parser flags.
- `tests/test_project_commands.py` - existing export command/parser coverage.
- `CLAUDE.md`, `docs/PROJECT_THEORY_AND_GOALS.md`, and `docs/plans/CLAUDE.md`
  - export/audit/scope claim-discipline caveats.
- Memory context:
  `agent-memory recall 'qualitative_coding next roadmap lane held-out live injection evaluation d7 retrieval theoretical sampling active decisions' --project qualitative_coding`
  returned low-relevance historical outcomes only, no active conflicting
  decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned only an
  unrelated `llm_client` claim file.

---

## Research Basis For This Slice

No external research is needed. This is deterministic CLI integration of an
existing repo-local publish/handoff gate.

---

## Capabilities

Internal CLI integration only; no new cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `project export --publish-preflight` | project ID + export args + audit manifest path + boolean flag | export command exit status + local manifest/preflight events | qualitative_coding | agents/operators | free |
| `project export --publish-preflight --scope-lint` | project ID + Markdown/text export + manifest + project state | export command exit status with scope-lint failures surfaced | qualitative_coding | agents/operators | free |

### Capability Validation

- [ ] Existing `project export` behavior is unchanged without new flags.
- [ ] `--publish-preflight` requires `--audit-manifest`.
- [ ] `--scope-lint` requires `--publish-preflight`.
- [ ] A passing inline publish preflight prints a clear success line and exits
  zero.
- [ ] A failing inline publish preflight makes `project export` return nonzero.
- [ ] Optional `--scope-lint` blocks risky Markdown/text handoff artifacts under
  missing or under-specified corpus scope.
- [ ] Audit event logs, when requested, include the inline publish-preflight
  event and SQLite mirrors are refreshed after it.
- [ ] Docs preserve caveats: local integrity/report-discipline only, not
  sampling adequacy, methodological validity, signing, append-only storage,
  external tamper evidence, or SOTA.

---

## Files Expected To Change

- `qc_clean/core/cli/commands/project.py`
- `qc_cli.py`
- `tests/test_project_commands.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`
- `docs/plans/completed/PROJECT_EXPORT_PUBLISH_PREFLIGHT_GATE.md`

---

## Plan

### Steps

1. [ ] Add failing parser tests for `project export --publish-preflight` and
   `--scope-lint`.
2. [ ] Add failing export command tests for dependency validation, passing
   inline preflight, failing scope-lint preflight, and optional audit event
   logging.
3. [ ] Add parser flags in `qc_cli.py`.
4. [ ] Wire `_export_project` and
   `_write_and_optionally_verify_export_manifest` to run
   `run_export_publish_preflight` after manifest writes when explicitly
   requested.
5. [ ] Update docs/CLAUDE/theory/plan caveats and regenerate `AGENTS.md`.
6. [ ] Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
7. [ ] Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_project_commands.py` | `test_export_subparser_publish_preflight_flags` | `project export` parser accepts the new explicit flags. |
| `tests/test_project_commands.py` | `test_project_export_command_rejects_publish_preflight_without_manifest` | Inline preflight cannot run without a manifest path. |
| `tests/test_project_commands.py` | `test_project_export_command_rejects_scope_lint_without_publish_preflight` | Scope lint is only valid as an inline publish-preflight option. |
| `tests/test_project_commands.py` | `test_project_export_command_runs_publish_preflight` | Export writes a manifest, runs preflight, and exits zero when it passes. |
| `tests/test_project_commands.py` | `test_project_export_command_scope_lint_blocks_risky_markdown` | Inline scope lint makes the export command return nonzero for unsafe Markdown handoff text. |
| `tests/test_project_commands.py` | `test_project_export_command_logs_publish_preflight_event` | Audit JSONL/SQLite workflows include the inline publish-preflight event when requested. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_project_commands.py tests/test_export_publish_preflight.py tests/test_export_audit_event_log.py -q` | Project export integration plus existing standalone gate/event behavior. |
| `python -m ruff check qc_clean/core/cli/commands/project.py qc_cli.py tests/test_project_commands.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_cli.py project export` accepts `--publish-preflight` and
  `--scope-lint`.
- [ ] `--publish-preflight` fails loud without `--audit-manifest`.
- [ ] `--scope-lint` fails loud without `--publish-preflight`.
- [ ] Passing inline publish preflight preserves successful export exit code and
  prints a clear success line.
- [ ] Failing inline publish preflight returns nonzero and includes the preflight
  failure reason in stderr.
- [ ] Optional inline `--scope-lint` blocks risky Markdown/text artifacts under
  missing/under-specified scope using existing `scope_lint_*` failure codes.
- [ ] Audit JSONL/SQLite workflows include the inline publish-preflight event
  when audit logging is enabled.
- [ ] Existing export behavior without new flags is unchanged.
- [ ] Documentation preserves caveats: this is opt-in local integrity and
  report-boundary discipline only.

> Process criteria:
- [ ] Plan committed before implementation.
- [ ] Red tests observed before implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff passes.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes, or any failure is documented as unrelated with
  evidence.
- [ ] Implementation and closeout commits are pushed.

---

## Failure Modes And Diagnostics

| Failure Mode | Diagnostic | Response |
|--------------|------------|----------|
| Export defaults accidentally change | Existing export tests fail | Keep both new flags default false and conditional. |
| Scope lint runs without project state | Inline integration test | Use loaded `ProjectState` from `project export`, not manifest-only state. |
| Audit DB misses publish-preflight event | Event-log/DB test | Mirror after all requested audit events are appended. |
| Preflight failure is swallowed | Scope-lint blocking test | Raise from helper so `_export_project` returns nonzero. |
| Docs imply mandatory/default publish policy | Manual caveat review + docs-check | Describe the gate as explicit opt-in only. |

---

## Closeout

Pending implementation.
