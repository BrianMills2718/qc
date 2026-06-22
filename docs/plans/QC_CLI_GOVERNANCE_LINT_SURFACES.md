# Plan #195: QC CLI Governance Lint Surfaces

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Existing scope-phrasing and prompt-override lint scripts
**Blocks:** Top-level CLI parity for local governance lint checks

---

## Gap

**Current:** Two governance checks are agent-drivable through Make/script
surfaces:

- `make lint-scope-phrasing`
- `make lint-prompt-overrides`

`qc_cli.py` exposes the broader project and evaluation workflows, but it does
not expose these lint checks as top-level commands.

**Target:** Add two thin `qc_cli.py` wrappers:

- `lint-scope-phrasing <project_id> (--input-file <path> | --text <text>) [--projects-dir <dir>]`
- `lint-prompt-overrides [--root <path>]`

Each wrapper must delegate to the matching canonical script `main()` with exact
argv forwarding.

**Why:** Scope-language and prompt-override governance checks should be
available from the canonical CLI for agent workflows, not only through Make or
direct script paths.

**Non-target:** This slice does not change scope-lint rules, prompt-override
registry rules, Make targets, prompt rendering, corpus-scope semantics,
prompt-injection scoring, or model behavior. It does not validate sampling
frames, prove prompt-injection robustness, prove model obedience, or create
methodological-validity/SOTA evidence.

---

## References Reviewed

- `scripts/lint_scope_phrasing.py` - scope phrasing lint CLI contract.
- `scripts/check_prompt_override_registry.py` - prompt override registry lint
  CLI contract.
- `Makefile` governance lint targets.
- `qc_cli.py` existing top-level wrapper style.
- `tests/test_scope_phrasing_lint.py` and `tests/test_prompt_override_registry.py`
  - canonical behavior.
- `CLAUDE.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - governance-lint caveats.
- Memory context:
  `agent-memory recall 'qualitative_coding lint-scope-phrasing lint-prompt-overrides qc_cli active decisions' --project qualitative_coding`
  returned low-relevance historical outcomes only, no active conflicting
  decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned only an
  unrelated `llm_client` claim file.

---

## Research Basis For This Slice

No external research is needed. This is deterministic CLI parity for existing
repo-local lint scripts.

---

## Capabilities

Internal CLI delegation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli.py lint-scope-phrasing` | project ID + input file or inline text + optional project store | canonical JSON lint report | qualitative_coding | agents/operators | free |
| `qc_cli.py lint-prompt-overrides` | optional Python source root | canonical JSON registry report | qualitative_coding | agents/operators | free |

### Capability Validation

- [ ] Each command parses through `qc_cli.py`.
- [ ] Each handler delegates to the matching script `main()`.
- [ ] Mutually exclusive scope-lint inputs stay enforced by `argparse`.
- [ ] Optional path flags are forwarded only when supplied.
- [ ] Docs state these are governance lint surfaces only, not validity,
  sampling-frame, prompt-injection robustness, or model-obedience evidence.

---

## Files Affected

- `qc_cli.py`
- `tests/test_qc_cli_governance_lint_surfaces.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Add failing wrapper tests that monkeypatch each canonical script `main()` and
   assert exact argv forwarding.
2. Add parser, dispatch, and handler entries in `qc_cli.py`.
3. Update docs/CLAUDE with the top-level CLI surfaces and caveats.
4. Regenerate `AGENTS.md`.
5. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
6. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_governance_lint_surfaces.py` | `test_qc_cli_governance_lint_surface_forwards_args` | Both wrappers delegate exact argv to canonical scripts. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_governance_lint_surfaces.py tests/test_scope_phrasing_lint.py tests/test_prompt_override_registry.py -q` | CLI wrappers plus canonical lint behavior. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_governance_lint_surfaces.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Both `qc_cli.py` commands parse successfully.
- [ ] Each handler calls the matching canonical script `main()`.
- [ ] Supplied arguments are forwarded exactly in canonical script form.
- [ ] Existing Make/script behavior is unchanged.
- [ ] Docs/CLAUDE mention the top-level CLI aliases without implying sampling
  adequacy, prompt-injection robustness, model obedience, methodological
  validity, or SOTA.

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
| CLI command unrecognized | Parser entry missing | Add subparser. |
| Parser accepts but does nothing | Dispatch branch missing | Add main dispatch branch. |
| Scope-lint input mode drifts | Wrapper changes mutually exclusive input semantics | Mirror script inputs and delegate exact argv. |
| Optional root/projects-dir flags are forwarded as `None` | Handler always emits optional flags | Forward optional flags only when supplied. |
| Lint logic duplicated in `qc_cli.py` | Wrapper reimplements script work | Keep handlers as argv delegation only. |
| Docs overclaim | Lint checks sound like validity or robustness evidence | Keep caveats: governance lint only, not sampling adequacy, model obedience, or SOTA evidence. |
