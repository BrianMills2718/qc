# Plan #154: Ruff F541 Expansion

**Status:** Planned
**Type:** implementation
**Priority:** Medium
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** Ruff only gates fatal syntax/name-binding families (`E9`, `F63`,
`F7`, `F82`). The maintenance backlog says to add `F541` and remove f-strings
that do not contain placeholders.

**Target:** `F541` is part of the normal Ruff gate, and the current repository
has zero F541 violations.

**Why:** F541 is a low-risk lint expansion that prevents misleading f-string
syntax from accumulating while avoiding broader import/order cleanup that needs
separate review.

---

## References Reviewed

- `CLAUDE.md` - maintenance follow-up requiring F541 expansion while deferring
  F401/E402.
- `pyproject.toml` - current Ruff selected rule families.
- `qc_clean/core/cli/commands/analyze.py` - current F541 violation in analysis
  submission message.
- `qc_clean/core/export/data_exporter.py` - current F541 violations in Markdown
  export rendering.
- `scripts/optimize_thematic_prompt.py` - current F541 violation in prompt
  optimization reporting.
- `simple_cli_web.py` - current F541 violations in static HTML error returns.
- Memory context:
  `agent-memory recall 'ruff F541 lint expansion qualitative_coding' --project qualitative_coding`
  - 2 low-relevance historical findings, no active conflicting decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this plan changes lint policy and mechanical string prefixes only; it
does not create or modify callable cross-project capabilities.

---

## Files Affected

- `pyproject.toml` - add `F541` to Ruff selected rules.
- `qc_clean/core/cli/commands/analyze.py` - remove one unnecessary f-string
  prefix.
- `qc_clean/core/export/data_exporter.py` - remove three unnecessary f-string
  prefixes.
- `scripts/optimize_thematic_prompt.py` - remove one unnecessary f-string
  prefix.
- `simple_cli_web.py` - remove two unnecessary f-string prefixes.
- `CLAUDE.md` - remove the completed maintenance follow-up.
- `AGENTS.md` - regenerated after `CLAUDE.md` changes.

---

## Plan

### Steps

1. Add `F541` to the Ruff selected rules in `pyproject.toml`.
2. Run Ruff F541 autofix or apply equivalent mechanical edits.
3. Re-run `python -m ruff check . --select F541`.
4. Run focused tests for touched runtime/export surfaces.
5. Remove the completed maintenance follow-up and regenerate `AGENTS.md`.
6. Run `make docs-check` and `make check`.

---

## Required Tests

### New Tests (TDD)

No new tests: this is a lint-policy expansion and mechanical removal of
unnecessary f-string prefixes.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m ruff check . --select F541` | Proves the new lint family is clean |
| `python -m pytest tests/test_project_commands.py -k export -q` | Markdown/export rendering remains covered |
| `python -m pytest tests/test_qdpx_export.py -q` | Export module import/runtime behavior remains covered |
| `make docs-check` | AGENTS sync and plan docs remain valid |
| `make check` | Full deterministic gate remains green with F541 enabled |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] `F541` is selected in `pyproject.toml`.
- [ ] `python -m ruff check . --select F541` reports zero violations.
- [ ] `make lint` includes F541 through the configured rule set.
- [ ] No runtime behavior is intentionally changed.

Process criteria:

- [ ] Required focused tests pass.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Open Questions

- [ ] None.

---

## Notes

Do not add `F401` or `E402` in this slice. They remain deferred because wrapper
and re-export patterns need separate review.

## Closeout Notes

Completed 2026-06-22.

Outcome: Ruff `F541` is now selected in `pyproject.toml`, and all seven
pre-existing no-placeholder f-strings were mechanically rewritten without
intended runtime behavior changes. `F401` and `E402` remain intentionally
deferred for separate wrapper/re-export review.

Checkpoints:

- Plan checkpoint: `b54e167`
- Implementation checkpoint: `bf567d4`

Verification:

- `python -m ruff check . --select F541`
- `python -m pytest tests/test_project_commands.py -k export -q` (`26 passed,
  23 deselected`)
- `python -m pytest tests/test_qdpx_export.py -q` (`14 passed`)
- `make docs-check`
- `make check` (`1103 passed, 1 skipped, 8 deselected`)
