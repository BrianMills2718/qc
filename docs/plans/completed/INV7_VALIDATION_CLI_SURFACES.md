# Plan #149: INV-7 Validation CLI Surfaces

**Status:** Complete
**Type:** implementation
**Priority:** Medium
**Blocked By:** INV-7 package/protocol/preflight validators
**Blocks:** agent-drivable INV-7 package validation workflows

---

## Outcome

The top-level CLI now exposes:
- `qc_cli.py validate-inv7-package <package_file>`
- `qc_cli.py validate-inv7-live-protocol <protocol_file>`
- `qc_cli.py inv7-live-preflight <protocol_file> <package_file>`

Each command delegates directly to its canonical script and preserves
script-owned JSON output and exit-code semantics. This is CLI parity/process
validation only; it is not prompt-injection robustness evidence, model-obedience
evidence, or methodological-validity evidence.

**Verification:** `python -m pytest tests/test_qc_cli_inv7_fixtures.py
tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py
tests/test_inv7_live_preflight.py -q` passed (23 tests), targeted Ruff passed,
and `make docs-check` passed. Final `make check` passed (1084 passed, 1
skipped, 8 deselected; Ruff/docs-check passed). Type checking is not configured
in this repo.

---

## Gap

**Current:** INV-7 prompt-injection package validation, live protocol validation,
and live protocol-result preflight are available through Make targets and
canonical scripts. The top-level `qc_cli.py` already wraps INV-7 fixture
generation, but not the corresponding validation/preflight surfaces.

**Target:** Add top-level CLI wrappers:
- `qc_cli.py validate-inv7-package <package_file>`
- `qc_cli.py validate-inv7-live-protocol <protocol_file>`
- `qc_cli.py inv7-live-preflight <protocol_file> <package_file>`

Each wrapper must delegate directly to its canonical script and preserve
script-owned JSON output and exit-code behavior.

**Why:** INV-7 live/structural fixture workflows are package-based. Agents can
already generate packages through `qc_cli.py`; they should be able to validate
and preflight those packages through the same top-level CLI without remembering
script paths.

---

## References Reviewed

- `scripts/validate_inv7_prompt_injection_package.py` - canonical INV-7 package validator.
- `scripts/validate_inv7_live_protocol.py` - canonical live protocol validator.
- `scripts/preflight_inv7_live_package.py` - canonical protocol/result preflight.
- `qc_cli.py` - existing INV-7 fixture wrapper commands.
- `tests/test_qc_cli_inv7_fixtures.py` - INV-7 CLI forwarding tests.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-7 caveats and claim discipline.

---

## Research Basis For This Slice

No external research is needed. This is a thin CLI wrapper slice over existing
validators.

---

## Capabilities

This plan exposes existing repo-local INV-7 package validation/preflight through
the top-level CLI. It does not create a new validation capability.

---

## Files Affected

- `qc_cli.py` (modify)
- `tests/test_qc_cli_inv7_fixtures.py` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/EVALUATION_HARNESS.md` (modify if surface list changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/INV7_VALIDATION_CLI_SURFACES.md` (create, then move to completed)

---

## Plan

### Steps

1. Add the three top-level subcommands to `qc_cli.py`.
2. Add handler functions that call the canonical scripts with forwarded paths.
3. Add forwarding tests for path/order and exit-code preservation.
4. Update concise docs to list the CLI validation/preflight wrappers and keep
   the caveat that these are process/provenance checks only.
5. Run focused and full deterministic gates.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_inv7_fixtures.py` | `test_qc_cli_validate_inv7_package_forwards_path` | Top-level CLI delegates to the package validator. |
| `tests/test_qc_cli_inv7_fixtures.py` | `test_qc_cli_validate_inv7_live_protocol_forwards_path` | Top-level CLI delegates to the live protocol validator. |
| `tests/test_qc_cli_inv7_fixtures.py` | `test_qc_cli_inv7_live_preflight_forwards_paths` | Top-level CLI delegates protocol/package paths to live preflight in order. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_qc_cli_inv7_fixtures.py` | Existing INV-7 fixture wrapper tests remain compatible. |
| `tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py tests/test_inv7_live_preflight.py` | Canonical validator behavior remains script/core owned. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `qc_cli.py validate-inv7-package <package_file>` is available.
- [x] `qc_cli.py validate-inv7-live-protocol <protocol_file>` is available.
- [x] `qc_cli.py inv7-live-preflight <protocol_file> <package_file>` is available.
- [x] Wrappers delegate to canonical scripts without duplicating validation logic.
- [x] Script-owned JSON output and exit codes are preserved.
- [x] Docs state these are process/provenance checks only, not prompt-injection robustness evidence.

> Process criteria:
- [x] Focused tests pass (`python -m pytest tests/test_qc_cli_inv7_fixtures.py tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py tests/test_inv7_live_preflight.py -q`: 23 passed).
- [x] Full test suite passes (`make check`: 1084 passed, 1 skipped, 8 deselected; Ruff/docs-check passed).
- [x] Type check status is reported (`make check`: type check not yet configured).
- [x] Docs updated.

---

## Open Questions

None for this slice.
