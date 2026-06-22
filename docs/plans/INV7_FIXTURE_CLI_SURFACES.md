# Plan #133: INV-7 Fixture CLI Surfaces

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Existing structural and live INV-7 fixture scripts
**Blocks:** Canonical CLI execution of prompt-injection fixture package generation

---

## Gap

**Current:** INV-7 structural and live prompt-injection fixture packages can be
generated through Make/script surfaces:

- `make run-inv7-fixtures` / `scripts/run_inv7_fixtures.py`
- `make run-inv7-live-fixtures` / `scripts/run_inv7_live_fixtures.py`

But `qc_cli.py` has no canonical local CLI commands for those fixture runners.

**Target:** Add thin canonical CLI wrappers:

- `python qc_cli.py run-inv7-fixtures --output inv7.json`
- `python qc_cli.py run-inv7-live-fixtures --output inv7_live.json --model ...`

The wrappers should forward current script flags unchanged and leave fixture
generation, live model calls, JSON summaries, and output writing owned by the
existing scripts.

**Why:** The roadmap's next INV-7 lane is live prompt-injection evaluation. The
existing structural/live fixture package generators should be reachable from
the same canonical local CLI used for Phase 0 scorecards and D7 retrieval work.

---

## References Reviewed

- `scripts/run_inv7_fixtures.py` - structural fixture runner script.
- `scripts/run_inv7_live_fixtures.py` - opt-in live fixture runner script.
- `tests/test_inv7_fixture_runner.py` - core and script fixture tests.
- `qc_cli.py` - current thin-wrapper command patterns.
- `docs/EVALUATION_HARNESS.md` and `CLAUDE.md` - INV-7 fixture caveats.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This is deterministic CLI exposure for existing
structural/live INV-7 fixture runners.

---

## Capabilities

Internal CLI wrapper capability only; no new cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli_run_inv7_fixtures` | `qc_cli.py run-inv7-fixtures` argv | `scripts/run_inv7_fixtures.py` exit code/stdout | qualitative_coding | agents/operators using canonical CLI | free |
| `qc_cli_run_inv7_live_fixtures` | `qc_cli.py run-inv7-live-fixtures` argv | `scripts/run_inv7_live_fixtures.py` exit code/stdout | qualitative_coding | agents/operators using canonical CLI | paid LLM |

### Capability Validation

- [ ] `qc_cli.py run-inv7-fixtures` accepts and forwards `--output`.
- [ ] `qc_cli.py run-inv7-live-fixtures` accepts and forwards `--output`,
  `--model`, `--trace-id`, and `--max-budget`.
- [ ] Existing INV-7 fixture runner tests continue to pass.

---

## Files Affected

- `qc_cli.py` (modify)
- `tests/test_qc_cli_inv7_fixtures.py` (new)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add TDD tests that monkeypatch the two script `main()` functions and assert
   exact `qc_cli.py` forwarding.
2. Add `run-inv7-fixtures` and `run-inv7-live-fixtures` parsers and handlers in
   `qc_cli.py`.
3. Update docs to list the canonical INV-7 fixture CLI commands and preserve
   live-evaluation caveats.
4. Run focused CLI/fixture tests, focused Ruff, docs checks, and full
   `make check`.
5. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_inv7_fixtures.py` | `test_qc_cli_run_inv7_fixtures_forwards_output` | Structural fixture output path reaches `scripts.run_inv7_fixtures.main`. |
| `tests/test_qc_cli_inv7_fixtures.py` | `test_qc_cli_run_inv7_live_fixtures_forwards_flags` | Live fixture output/model/trace/budget flags reach `scripts.run_inv7_live_fixtures.main`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_inv7_fixtures.py tests/test_inv7_fixture_runner.py -q` | Top-level wrappers plus existing fixture runner behavior. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_inv7_fixtures.py` | Focused lint on modified CLI surfaces. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_cli.py run-inv7-fixtures --output ...` exists and delegates to the
  structural fixture script.
- [ ] `qc_cli.py run-inv7-live-fixtures --output ...` exists and delegates to
  the live fixture script without duplicating live-call behavior.
- [ ] Docs list these commands and preserve the caveat that fixtures are not
  prompt-injection robustness proof.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Notes

This plan only exposes existing INV-7 fixture runners through the canonical
local CLI. It does not run a live adversarial benchmark or change prompt-
injection claim status.
