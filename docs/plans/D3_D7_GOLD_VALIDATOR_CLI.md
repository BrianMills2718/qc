# Plan #146: D3/D7 Gold Validator CLI Surfaces

**Status:** In Progress
**Type:** implementation
**Priority:** Medium
**Blocked By:** D3/D7 held-out gold-set scaffolds
**Blocks:** easier held-out package validation in agent-driven workflows

---

## Gap

**Current:** Versioned D3 and D7 gold-set packages can be validated through
`make validate-d3-gold`, `make validate-d7-gold`, and their canonical scripts.
The top-level `qc_cli.py` already wraps related evaluation-harness commands
(`bench`, `bench-package`, D7 retrieval export/comparison, D7 baseline package
validation), but not the D3/D7 gold-set validators themselves.

**Target:** Add top-level `qc_cli.py validate-d3-gold <gold_set>` and
`qc_cli.py validate-d7-gold <gold_set>` commands that delegate directly to
`scripts.validate_d3_gold_set.main()` and `scripts.validate_d7_gold_set.main()`.
The wrappers must preserve script-owned JSON output and exit-code semantics.

**Why:** Future held-out D3/D7 evidence depends on versioned package validation.
CLI parity gives agents and operators one canonical entrypoint without
duplicating validation logic or claiming that any held-out labels/results exist.

---

## References Reviewed

- `scripts/validate_d3_gold_set.py` - canonical D3 package validator.
- `scripts/validate_d7_gold_set.py` - canonical D7 package validator.
- `Makefile` - existing `validate-d3-gold` and `validate-d7-gold` targets.
- `qc_cli.py` - current evaluation-harness wrapper patterns.
- `tests/test_qc_cli_d7_retrieval.py` - CLI forwarding test style.
- `docs/PROJECT_THEORY_AND_GOALS.md` - evaluation harness and INV-3 caveats.

---

## Research Basis For This Slice

No external research is needed. This is a repo-local CLI parity slice over
existing package validators.

---

## Capabilities

This plan exposes existing repo-local D3/D7 gold-set validation through the
top-level CLI. It does not create a new scoring or validation capability.

---

## Files Affected

- `qc_cli.py` (modify)
- `tests/test_qc_cli_d7_retrieval.py` or a focused CLI test file (modify/create)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify if state ledger command list changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/D3_D7_GOLD_VALIDATOR_CLI.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `validate-d3-gold` and `validate-d7-gold` top-level subcommands to
   `qc_cli.py`.
2. Add small handler functions that call the canonical validator script `main`
   functions with the supplied package path.
3. Add tests that monkeypatch script `main` and prove path forwarding plus
   exit-code preservation.
4. Update concise docs to list the new CLI commands and preserve the caveat
   that package validation is not validity evidence.
5. Run focused CLI tests and full deterministic gates.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_validate_d3_gold_forwards_path` | Top-level CLI forwards the package path to the D3 validator and returns its exit code. |
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_validate_d7_gold_forwards_path` | Top-level CLI forwards the package path to the D7 validator and returns its exit code. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_d3_gold_set.py tests/test_d7_gold_set.py` | Canonical validator behavior remains owned by scripts/core validators. |
| `tests/test_qc_cli_d7_retrieval.py` | Related top-level CLI wrappers remain compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] `qc_cli.py validate-d3-gold <gold_set>` is available.
- [ ] `qc_cli.py validate-d7-gold <gold_set>` is available.
- [ ] Both wrappers delegate to canonical validator scripts without duplicating validation logic.
- [ ] Both wrappers preserve script-owned JSON output and exit codes.
- [ ] Docs describe these as package/provenance validation only, not held-out evidence.

> Process criteria (quality gates):
- [ ] Required focused tests pass.
- [ ] Full test suite passes (`make check`).
- [ ] Type check status is reported.
- [ ] Docs updated.

---

## Open Questions

None for this slice.

---

## Notes

This does not create D3/D7 gold labels, run held-out benchmarks, or license
validity/superiority claims.
