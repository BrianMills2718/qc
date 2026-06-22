# Plan #129: QC Bench CLI Flag Parity

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 guard/input surfaces already implemented in `scripts/bench_phase0.py`
**Blocks:** Agent-driven benchmark package and scorecard workflows through the canonical CLI

---

## Outcome

Completed in implementation commit `8a658bf`. `qc_cli.py bench` now accepts
and forwards the current Phase 0 external-input and protocol-guard flags from
`scripts/bench_phase0.py`, including D3 baselines, D4/D6/D8/D9 protocol files,
D6 stratified rows, and confidence-calibration protocol files. The change is
CLI parity/provenance only; it adds no new metrics and does not license held-out
benchmark, methodological-validity, or SOTA claims.

Verification:

- TDD red: `python -m pytest tests/test_qc_cli_bench.py -q` failed before the
  implementation with argparse rejecting the missing flags.
- Focused tests: `python -m pytest tests/test_qc_cli_bench.py -q` passed
  (`4 passed`).
- Focused lint: `python -m ruff check qc_cli.py tests/test_qc_cli_bench.py`
  passed.
- Docs: `make docs-check` passed.
- Full gate: `make check` passed (`1015 passed, 1 skipped, 8 deselected`);
  Ruff and docs checks passed inside the gate.
- Type check: not configured.
- Verified implementation was committed and pushed.

---

## Gap

**Current:** `make bench` and `scripts/bench_phase0.py` expose the current Phase
0 external-input and protocol-guard surfaces, including D3 baselines,
D4/D6/D8/D9 protocol guards, D6 stratified rows, and confidence-calibration
protocol guards. `qc_cli.py bench` forwards only a subset of those flags.

**Target:** Make `qc_cli.py bench` a thin parity wrapper over the current
`bench_phase0.py` scorecard surface:

- Add missing parser flags:
  - `--d3-baselines-file`
  - `--d6-bias-protocol-file`
  - `--bias-stratified-file`
  - `--d4-codebook-quality-protocol-file`
  - `--d8-gt-fidelity-protocol-file`
  - `--d9-interpretive-preference-protocol-file`
  - `--confidence-calibration-protocol-file`
- Forward those flags unchanged to `scripts/bench_phase0.py`.
- Add focused tests that capture `bench_phase0.main(argv)` and verify exact
  forwarding without needing fixture-heavy protocol files.
- Update docs to clarify `qc_cli.py bench` mirrors the script/Make Phase 0
  flags.

**Why:** The project treats CLI operations as canonical agent-drivable
surfaces. If `make bench` can enforce protocol guards but `qc_cli.py bench`
cannot request them, agents using the canonical CLI can accidentally run
unguarded scorecards.

---

## References Reviewed

- `qc_cli.py` - bench parser and `handle_bench_command` forwarding.
- `scripts/bench_phase0.py` - canonical Phase 0 flag surface.
- `Makefile` - `make bench` environment-variable mapping.
- `tests/test_qc_cli_bench.py` - existing top-level CLI bench tests.
- `docs/EVALUATION_HARNESS.md` - current Phase 0 surface description.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.
- Coordination claims: no active claim files were present under
  `~/.claude/coordination/claims/` earlier in this long-running sprint; the
  worktree is clean at plan start.

---

## Research Basis For This Slice

No new external research. This is deterministic CLI parity for already
implemented local Phase 0 scorecard surfaces.

---

## Capabilities

Internal CLI wrapper parity only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli_bench_flag_parity` | `qc_cli.py bench` argv | forwarded `bench_phase0.py` argv | qualitative_coding | agents/operators using canonical CLI | free |

### Capability Validation

- [x] `qc_cli.py bench` accepts every current Phase 0 external-input/protocol
  flag listed in this plan.
- [x] `handle_bench_command` forwards those flags unchanged to
  `bench_phase0.main`.
- [x] Existing `qc_cli.py bench` scorecard and artifact tests continue to pass.

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

1. Add a TDD test that monkeypatches `bench_phase0.main`, invokes
   `qc_cli.py bench` with every missing flag, and asserts exact forwarded argv.
2. Add the missing argparse flags and forwarding branches in `qc_cli.py`.
3. Update docs to clarify CLI parity.
4. Run focused tests, focused Ruff, docs checks, and full `make check`.
5. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_bench.py` | `test_qc_cli_bench_forwards_all_phase0_flags` | The top-level CLI accepts and forwards all current Phase 0 file/protocol flags. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_bench.py -q` | Top-level CLI bench behavior. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_bench.py` | Focused lint on modified CLI surfaces. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `qc_cli.py bench` accepts and forwards all current Phase 0 external input
  and protocol guard flags from this plan.
- [x] No existing CLI bench behavior regresses.
- [x] Docs state CLI parity with the canonical Phase 0 script/Make surface.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Notes

This plan only exposes existing deterministic Phase 0 inputs through
`qc_cli.py bench`. It does not add new metrics, run held-out benchmarks, or
change evidentiary claim status.
