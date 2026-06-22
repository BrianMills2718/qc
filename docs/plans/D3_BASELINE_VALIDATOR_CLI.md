# Plan #148: D3 Baseline Validator CLI

**Status:** In Progress
**Type:** implementation
**Priority:** Low
**Blocked By:** D3 baseline package validator
**Blocks:** CLI parity for evaluation-harness package validation

---

## Gap

**Current:** Versioned D3 baseline packages validate through
`scripts/validate_d3_baseline_package.py` and
`make validate-d3-baseline-package PACKAGE=...`. The top-level `qc_cli.py`
already wraps D3/D7 gold validation and D7 baseline validation, but not D3
baseline validation.

**Target:** Add `qc_cli.py validate-d3-baseline-package <package_file>` that
delegates directly to `scripts.validate_d3_baseline_package.main()` and
preserves script-owned JSON output and exit-code behavior.

**Why:** This keeps package validation agent-drivable from the same canonical
top-level CLI surface as the related D3/D7 gold and D7 baseline validators.

---

## References Reviewed

- `qc_cli.py` - existing validation wrapper commands.
- `scripts/validate_d3_baseline_package.py` - canonical D3 baseline package validator.
- `tests/test_qc_cli_d7_retrieval.py` - existing forwarding-test style.
- `docs/plans/completed/D3_BASELINE_PACKAGE_VALIDATOR.md` - package validator outcome and caveats.

---

## Research Basis For This Slice

No external research is needed. This is a thin CLI wrapper over an existing
validator.

---

## Capabilities

This plan exposes an existing repo-local validator through the top-level CLI. It
does not create new package validation logic.

---

## Files Affected

- `qc_cli.py` (modify)
- `tests/test_qc_cli_d7_retrieval.py` or focused CLI test file (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/D3_BASELINE_VALIDATOR_CLI.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a top-level `validate-d3-baseline-package` subcommand to `qc_cli.py`.
2. Add a handler that calls `scripts.validate_d3_baseline_package.main()` with
   the supplied path.
3. Add a forwarding test that monkeypatches script `main` and asserts path and
   exit-code preservation.
4. Update concise docs and run deterministic gates.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_validate_d3_baseline_package_forwards_path` | Top-level CLI forwards the package path and returns the script exit code. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_qc_cli_d7_retrieval.py` | Related validation wrappers remain compatible. |
| `tests/test_d3_baseline_package.py` | Canonical validator behavior remains script/core owned. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_cli.py validate-d3-baseline-package <package_file>` is available.
- [ ] The wrapper delegates to `scripts.validate_d3_baseline_package.main()` without duplicating validation logic.
- [ ] Script-owned JSON output and exit codes are preserved.
- [ ] Docs state this is package/provenance validation only, not held-out evidence.

> Process criteria:
- [ ] Focused tests pass.
- [ ] Full test suite passes (`make check`).
- [ ] Type check status is reported.
- [ ] Docs updated.

---

## Open Questions

None for this slice.
