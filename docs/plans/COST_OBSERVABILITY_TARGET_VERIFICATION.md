# Plan #155: Cost Observability Target Verification

**Status:** Planned
**Type:** implementation
**Priority:** Medium
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** The maintenance backlog asks to verify `make cost`; if
`llm_client cost` is unavailable or unstable, the repo should replace the
fallback with an explicit repo-local helper like `make errors`.

**Target:** The cost and error observability Make targets are verified in the
current environment. If they work, close the maintenance item without changing
the working interface. If they fail, replace the failing behavior with an
agent-drivable repo-local helper.

**Why:** The repo's operating model requires observability before speculation.
Agents need reliable `make cost` / `make errors` targets for LLM spend and
failure diagnosis.

---

## References Reviewed

- `CLAUDE.md` - maintenance follow-up requiring `make cost` verification.
- `Makefile` - `cost` and `errors` targets.
- `scripts/recent_errors.py` - repo-local error breakdown helper used by
  `make errors`.
- Memory context:
  `agent-memory recall 'cost observability make cost qualitative_coding' --project qualitative_coding`
  - 2 low-relevance historical findings, no active conflicting decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this plan verifies existing Make targets and does not create a new
callable capability unless verification fails.

---

## Files Affected

- `Makefile` - modify only if `make cost` is unavailable or unstable.
- `scripts/recent_errors.py` - modify only if `make errors` verification
  exposes a local helper issue.
- `CLAUDE.md` - remove the completed maintenance follow-up after verification.
- `AGENTS.md` - regenerated after `CLAUDE.md` changes.

---

## Plan

### Steps

1. Run `make cost` and inspect whether it reports real `llm_client`
   observability output or falls back to "not available."
2. Run `make errors` and inspect whether the repo-local helper returns a clear
   error summary.
3. If either target fails ambiguously, implement the smallest repo-local fix.
4. If both targets work, remove the completed maintenance follow-up.
5. Run docs and full deterministic gates.

---

## Required Tests

### New Tests (TDD)

No new tests are required if both Make targets work as existing agent-drivable
commands.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `make cost` | Verifies LLM spend observability target works |
| `make errors` | Verifies failure diagnosis target works |
| `make docs-check` | AGENTS sync and plan docs remain valid |
| `make check` | Full deterministic gate remains green |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] `make cost` exits 0 and reports real cost output, not only the fallback.
- [ ] `make errors` exits 0 with a clear recent-error summary.
- [ ] The maintenance follow-up is removed only after verification.
- [ ] No working observability target is replaced unnecessarily.

Process criteria:

- [ ] Required commands pass.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Open Questions

- [ ] None.

---

## Notes

This is a verification lane. It should be code-free unless an observability
target is actually unavailable or ambiguous.
