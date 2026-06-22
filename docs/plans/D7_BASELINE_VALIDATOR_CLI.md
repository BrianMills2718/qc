# Plan #144: D7 Baseline Validator CLI

**Status:** Planned
**Type:** implementation
**Priority:** Medium
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** `make validate-d7-baseline-package PACKAGE=...` and
`scripts/validate_d7_baseline_package.py` validate versioned D7 retrieval and
live-baseline prediction packages. The top-level `qc_cli.py` D7 surface has
wrappers for retrieval export, live-baseline export, and comparison, but no
wrapper for the validator.

**Target:** Add `qc_cli.py validate-d7-baseline-package <package_file>` as a
thin wrapper over the canonical script, preserving script-owned JSON output and
exit codes.

**Why:** D7 package validation is now part of the evidence-lane workflow. The
top-level CLI should expose the full D7 package lifecycle consistently without
requiring agents to remember which steps are Make-only/script-only. This is CLI
parity/provenance ergonomics only, not held-out D7 evidence or live-baseline
evidence.

---

## References Reviewed

- `agent-memory recall 'qualitative_coding qc_cli D7 baseline validator CLI wrapper' --project qualitative_coding --limit 5` - 2 broad historical findings; no specific active decision.
- `qc_cli.py` - existing top-level D7 parser and command routing.
- `scripts/validate_d7_baseline_package.py` - canonical validator script to delegate to.
- `tests/test_qc_cli_d7_retrieval.py` - existing top-level D7 wrapper tests.
- `tests/test_qc_cli_d7_live_baseline.py` - existing top-level live-baseline wrapper tests.
- `CLAUDE.md` - command surface and D7 caveats.
- `docs/EVALUATION_HARNESS.md` - D7 package validation surface.
- Coordination claims check: `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active claim files after Plan #143 closeout.

---

## Research Basis For This Slice

No additional research beyond repo-local references. This is a wrapper around an
existing validated script.

---

## Capabilities

No new core capability. This plan adds a top-level CLI alias for an existing
script-owned validator.

---

## Files Affected

- `qc_cli.py` (modify)
- `tests/test_qc_cli_d7_retrieval.py` (modify or create adjacent test)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add the `validate-d7-baseline-package` subparser with one positional
   `package_file` argument.
2. Add a handler that delegates to `scripts.validate_d7_baseline_package.main`.
3. Route the command in `qc_cli.main()`.
4. Add a top-level CLI test proving argument forwarding and exit-code passthrough.
5. Update docs and regenerated `AGENTS.md`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_validate_d7_baseline_package_forwards_path` | Top-level CLI delegates package path to the canonical validator script and returns its exit code. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_d7_baseline_package.py` | Canonical validator behavior remains script-owned. |
| `tests/test_qc_cli_d7_retrieval.py tests/test_qc_cli_d7_live_baseline.py` | Existing D7 top-level wrappers remain unchanged. |
| `make docs-check` | Plan/docs/AGENTS sync must pass. |
| `make check` | Full deterministic gate must pass. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_cli.py validate-d7-baseline-package <package_file>` exists.
- [ ] The command delegates to `scripts.validate_d7_baseline_package.main` with
      the same package path and returns the script exit code.
- [ ] Docs list the CLI alias and keep the package/provenance-only caveat.

> Process criteria:
- [ ] Required CLI wrapper test passes.
- [ ] Related D7 validator tests pass.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Plan is completed, committed, and pushed.

---

## Open Questions

None.

---

## Notes

The canonical behavior remains in `scripts/validate_d7_baseline_package.py`.
`qc_cli.py` should not duplicate validation logic.
