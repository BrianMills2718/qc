# Plan #130: QC Bench Package CLI

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Completed Phase 0 benchmark package runner
**Blocks:** Canonical CLI execution of strict Phase 0 benchmark manifests

---

## Gap

**Current:** Phase 0 benchmark packages can be run through
`scripts/run_phase0_benchmark_package.py <package.json>` and
`make bench-package PACKAGE=<package.json>`, but `qc_cli.py` has no top-level
command for the same manifest-driven path.

**Target:** Add a thin canonical CLI wrapper:

- `python qc_cli.py bench-package <package_file>`
- The command calls `scripts.run_phase0_benchmark_package.main([package_file])`
  without reimplementing package validation or scoring.
- Existing package-runner JSON error behavior remains owned by the script.
- Docs identify the command as a package orchestration/provenance surface, not
  populated held-out evidence.

**Why:** The repo treats `qc_cli.py` as the canonical local CLI. A strict Phase 0
manifest is now the cleanest agent-drivable benchmark handoff object, so it
should be runnable from that same CLI surface rather than only through Make or a
script path.

---

## References Reviewed

- `qc_cli.py` - top-level command parser and bench command handler.
- `scripts/run_phase0_benchmark_package.py` - strict package manifest runner.
- `tests/test_phase0_benchmark_package.py` - package-runner behavior.
- `tests/test_qc_cli_bench.py` - existing top-level bench CLI tests.
- `docs/EVALUATION_HARNESS.md` - Phase 0 package-runner documentation.
- `docs/plans/completed/PHASE0_BENCHMARK_PACKAGE_RUNNER.md` - original package-runner plan.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This is deterministic CLI exposure for an already
implemented local package-runner surface.

---

## Capabilities

Internal CLI wrapper only; no new cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli_bench_package` | `qc_cli.py bench-package <package_file>` argv | `run_phase0_benchmark_package.py` exit code/stdout | qualitative_coding | agents/operators using canonical CLI | free |

### Capability Validation

- [ ] `qc_cli.py bench-package <package_file>` is accepted by argparse.
- [ ] The handler forwards the manifest path unchanged to
  `run_phase0_benchmark_package.main`.
- [ ] Existing `qc_cli.py bench` behavior continues to pass.
- [ ] Existing package-runner tests continue to pass.

---

## Files Affected

- `qc_cli.py` (modify)
- `tests/test_qc_cli_bench.py` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add a TDD test that monkeypatches
   `scripts.run_phase0_benchmark_package.main`, invokes
   `qc_cli.py bench-package package.json`, and asserts exact forwarding.
2. Add the `bench-package` parser and handler in `qc_cli.py`.
3. Update docs to list the canonical package CLI command.
4. Run focused CLI/package tests, focused Ruff, docs checks, and full
   `make check`.
5. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_bench.py` | `test_qc_cli_bench_package_forwards_manifest_path` | The top-level CLI forwards one package manifest path to the canonical package runner. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_bench.py tests/test_phase0_benchmark_package.py -q` | Top-level CLI wrapper plus underlying package runner. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_bench.py` | Focused lint on modified CLI surfaces. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_cli.py bench-package <package_file>` exists.
- [ ] The command delegates to `scripts.run_phase0_benchmark_package.main`
  without duplicating package validation/scoring logic.
- [ ] Docs list the canonical CLI package surface.
- [ ] Existing package-runner behavior does not regress.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Notes

This plan only exposes existing strict Phase 0 package execution through
`qc_cli.py`. It does not create package contents, run held-out benchmarks, or
change evidentiary claim status.
