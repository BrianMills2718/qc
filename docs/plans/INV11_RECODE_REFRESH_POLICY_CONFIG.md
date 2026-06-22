# Plan #192: INV-11 Recode Refresh Policy Config

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** #167
**Blocks:** fuller default corpus-mutation auto-refresh policy

---

## Gap

**Current:** `project recode --refresh-higher-order` and
`project add-docs --recode --refresh-higher-order` can refresh
methodology-specific higher-order outputs after incremental coding. Without the
flag, recode uses hard invalidation. The remaining INV-11 roadmap gap is a
default auto-refresh policy for corpus mutation, but flipping the global
default would silently increase LLM spend and change existing project behavior.

**Target:** Add an explicit project-level recode policy:
`ProjectConfig.auto_refresh_higher_order_on_recode`. When true, `project recode`
and `project add-docs --recode` refresh higher-order outputs by default for
that project. Command-line flags can still force refresh on or off for one run.
Existing projects default to false.

**Why:** INV-11 needs a durable policy path, not only one-off CLI flags. A
project config switch makes the policy agent-drivable and repeatable while
preserving no-surprise behavior for existing projects and avoiding an
unreviewed model-spend default change.

**Non-target:** This slice does not make auto-refresh globally default, does
not change the refresh pipeline stages, does not run LLM calls in tests, does
not eliminate hard invalidation as a supported policy, and does not claim
methodological validity, complete INV-11, or SOTA evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §7, §13.1, §18 - current INV-11 status,
  roadmap gap, and claim-discipline boundaries.
- `CLAUDE.md` - current incremental recode description and next high-value
  lanes.
- `docs/plans/completed/INV11_THEMATIC_RECODE_HIGHER_ORDER_REFRESH.md` - prior
  thematic opt-in refresh slice and default-policy deferral.
- `docs/plans/completed/INV11_GT_RECODE_HIGHER_ORDER_REFRESH.md` - GT opt-in
  refresh slice and explicit default-policy deferral.
- `qc_clean/schemas/domain.py` - `ProjectConfig` persistence contract.
- `qc_clean/core/cli/commands/project.py` - project create, add-docs, and recode
  command behavior.
- `qc_cli.py` - parser surfaces for project create/add-docs/recode.
- `qc_clean/core/pipeline/pipeline_factory.py` - existing refresh pipeline
  contract.
- `tests/test_project_commands.py` and `tests/test_domain_model.py` - affected
  command/config regressions.
- Memory context:
  `agent-memory recall 'qualitative_coding INV-11 default auto refresh policy recode project config' --project qualitative_coding`
  returned low-relevance historical outcomes only, no active conflicting
  decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned only an
  unrelated `llm_client` claim file.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a repo-local policy
and CLI/config persistence slice.

---

## Capabilities

Internal project configuration and CLI policy only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `recode_refresh_policy` | ProjectConfig + CLI flags | effective boolean refresh policy | qualitative_coding | CLI recode/add-docs operators | free |

### Capability Validation

Skipped: this does not create a cross-project tool, contract, or external
callable capability.

---

## Files Affected

- `docs/plans/INV11_RECODE_REFRESH_POLICY_CONFIG.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`
- `qc_clean/schemas/domain.py`
- `qc_clean/core/cli/commands/project.py`
- `qc_cli.py`
- `tests/test_domain_model.py`
- `tests/test_project_commands.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/PROJECT_THEORY_AND_GOALS.md`

---

## Plan

### Steps

1. Add `auto_refresh_higher_order_on_recode: bool = False` to
   `ProjectConfig`, with a description documenting that it controls the default
   recode/add-docs recode policy for higher-order refresh.
2. Add project creation support:
   `project create --auto-refresh-higher-order-on-recode` stores the config
   field as true.
3. Add a small existing-project policy surface, e.g.
   `project recode-policy <project_id>`, that shows the current policy and can
   set it with mutually exclusive enable/disable flags.
4. Add a one-run override flag:
   `--no-refresh-higher-order` for `project recode` and `project add-docs
   --recode`. Keep existing `--refresh-higher-order` as the explicit force-on
   override.
5. Resolve the effective recode policy as:
   `--refresh-higher-order` -> true; `--no-refresh-higher-order` -> false;
   otherwise `ProjectConfig.auto_refresh_higher_order_on_recode`.
6. Preserve the existing refresh pipeline behavior once the effective policy is
   true, including methodology-specific refresh scope messaging.
7. Update docs to describe the project-level policy while preserving claim
   discipline: this narrows INV-11 but does not make INV-11 complete.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_domain_model.py` | `test_project_config_auto_refresh_higher_order_on_recode_defaults_false` | Existing/new project config defaults to no automatic refresh. |
| `tests/test_domain_model.py` | `test_project_config_auto_refresh_higher_order_on_recode_round_trips` | The policy persists through JSON serialization. |
| `tests/test_project_commands.py` | `test_create_project_can_enable_recode_refresh_policy` | Project creation stores the config flag. |
| `tests/test_project_commands.py` | `test_recode_uses_configured_refresh_policy_by_default` | Recode forwards `refresh_higher_order=True` when project config enables it and no override is supplied. |
| `tests/test_project_commands.py` | `test_recode_no_refresh_override_wins_over_config` | `--no-refresh-higher-order` forces hard-invalidation mode even when config enables auto-refresh. |
| `tests/test_project_commands.py` | `test_add_docs_with_recode_forwards_no_refresh_override` | `add-docs --recode --no-refresh-higher-order` passes the override to recode. |
| `tests/test_project_commands.py` | `test_recode_policy_command_updates_config` | The policy command shows/sets the persisted config. |
| `tests/test_project_commands.py` | parser coverage for create/recode/add-docs/policy flags | CLI flags parse into the intended fields. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_domain_model.py tests/test_project_commands.py -q` | Config and CLI behavior. |
| `python -m pytest tests/test_incremental.py tests/test_incremental_staleness_inv11.py -q` | Existing INV-11 invalidation/refresh behavior remains intact. |
| `python -m ruff check qc_clean/schemas/domain.py qc_clean/core/cli/commands/project.py qc_cli.py tests/test_domain_model.py tests/test_project_commands.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `ProjectConfig.auto_refresh_higher_order_on_recode` exists, defaults to
  false, and persists through JSON.
- [ ] New projects can opt into the policy through CLI creation.
- [ ] Existing projects can inspect and update the policy through an
  agent-drivable CLI command.
- [ ] `project recode` and `project add-docs --recode` use the configured
  policy when neither per-run override is supplied.
- [ ] `--refresh-higher-order` forces refresh for one run.
- [ ] `--no-refresh-higher-order` forces hard-invalidation mode for one run.
- [ ] Existing default behavior remains unchanged for projects without the
  config flag.
- [ ] Docs state this is an opt-in project policy, not global auto-refresh and
  not full INV-11 completion.

> Process criteria:
- [ ] TDD red state observed before implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Plan is moved to completed with verification evidence.
- [ ] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Existing projects unexpectedly refresh | Config default or override resolution wrong | Keep config default false and test no-override behavior. |
| Operators cannot disable a configured policy for one run | Missing force-off override | Add mutually exclusive `--no-refresh-higher-order`. |
| Config cannot be changed without manual JSON edits | Missing agent-drivable surface | Add `project recode-policy` show/set command. |
| Add-docs loses override state | `_add_docs` does not forward both override fields | Forward both fields to `_recode_project`. |
| Docs imply INV-11 is complete | Overclaim | Keep language: opt-in project policy only; hard invalidation remains supported. |
