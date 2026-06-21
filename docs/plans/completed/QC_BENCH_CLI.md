# Plan #29: QC Bench CLI

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 scorecard
**Blocks:** first-class benchmark command; future prompt_eval-backed `qc bench`

---

## Outcome

`qc_cli.py bench <project_id>` now delegates to `scripts.bench_phase0.main()`
and supports the same current Phase 0 flags as `make bench`: `--gold-file`,
`--d7-baselines-file`, `--prompt-injection-file`, `--observability-db`,
`--trace-id`, and `--output`. The wrapper preserves the existing JSON stdout,
output-file writing, externally supplied benchmark-file scoring, D7/D10 metrics,
and `_meta.input_hashes` behavior because it reuses the script implementation
instead of duplicating scorecard logic.

Docs now describe `qc_cli.py bench <project_id>` as the current canonical CLI
surface for the deterministic Phase 0 scorecard while preserving the caveat
that the full `prompt_eval` benchmark suite remains future work.

Verification:
- Focused: `python -m pytest tests/test_qc_cli_bench.py tests/test_bench_phase0_script.py -q` -> 11 passed.
- Focused lint: `python -m ruff check qc_cli.py tests/test_qc_cli_bench.py` -> passed.
- Full gate: `make check` -> 686 passed, 1 skipped, 8 deselected; Ruff passed; docs checks passed; type check not yet configured.

---

## Gap

**Current:** The evaluation harness docs still say there is no `qc bench` CLI
subcommand and that users/agents must use `make bench` or
`scripts/bench_phase0.py`. That works, but it keeps the benchmark surface outside
the main project CLI.

**Target:** Add a top-level `qc_cli.py bench <project_id>` command that delegates
to the existing Phase 0 bench implementation without duplicating scoring logic.
It should support the same current flags: `--gold-file`, `--d7-baselines-file`,
`--prompt-injection-file`, `--observability-db`, `--trace-id`, and `--output`.

**Why:** The target harness surface is `qc bench`; adding a thin Phase 0 route
makes benchmarking agent-drivable through the canonical CLI now and leaves room
for a future prompt_eval-backed implementation behind the same command.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - says no `qc bench` CLI subcommand exists and
  names it as the target surface.
- `qc_cli.py` - main CLI parser and command dispatch.
- `scripts/bench_phase0.py` - existing Phase 0 scorecard implementation.
- `tests/test_bench_phase0_script.py` - current bench script contract tests.
- Memory context: `agent-memory recall 'qc bench cli evaluation harness qualitative_coding active decisions' --project qualitative_coding` - historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is CLI
surface wiring over existing functionality.

---

## Capabilities

This plan modifies the repo-local CLI surface only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_cli.py` (modify)
- `tests/test_qc_cli_bench.py` (create)
- `docs/EVALUATION_HARNESS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify if queue changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/QC_BENCH_CLI.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a top-level `bench` subparser to `qc_cli.py` with the same Phase 0 flags
   as `scripts/bench_phase0.py`.
2. Dispatch `args.command == "bench"` by calling `scripts.bench_phase0.main()`
   with an equivalent argv list.
3. Preserve JSON stdout, non-zero error behavior, external-file handling, output
   file writing, D10 overrides, and input hashes by reusing the script.
4. Add CLI tests that monkeypatch `bench_phase0.ProjectStore` and exercise
   `qc_cli.main()` through `sys.argv`.
5. Update docs to say `qc bench` now exists as a Phase 0 wrapper; full
   prompt_eval-backed benchmark execution remains future work.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_bench.py` | `test_qc_cli_bench_emits_phase0_scorecard` | `qc_cli.py bench <project_id>` emits the Phase 0 JSON scorecard. |
| `tests/test_qc_cli_bench.py` | `test_qc_cli_bench_forwards_files_and_output` | CLI flags forward to `bench_phase0` and `--output` writes the scorecard. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0_script.py` | Underlying bench behavior remains unchanged. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [x] `qc_cli.py bench <project_id>` works.
- [x] Current Phase 0 bench flags are supported.
- [x] The command reuses `scripts.bench_phase0.main` rather than duplicating
  scorecard logic.
- [x] JSON stdout and `--output` behavior match the script path.
- [x] Docs say this is a Phase 0 wrapper, not the full prompt_eval suite.

> Process criteria (quality gates):
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status is reported
- [x] Docs updated

---

## Open Questions

- [ ] Should `qc bench` eventually replace `make bench`? - Status: DEFERRED |
  Why it matters: `make bench` remains the stable Makefile target; `qc bench`
  is the CLI surface future prompt_eval execution can grow behind.

---

## Notes

Keep this slice thin. The future full benchmark runner should not be implemented
inside `qc_cli.py`; it should route to benchmark orchestration code or
`prompt_eval` adapters.
