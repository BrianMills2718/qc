# Plan #177: D3 Baseline Comparison Score-Time Guard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** D3 baseline comparison preflight
**Blocks:** Held-out D3 baseline comparisons with enforced pre-registered
protocol matching

---

## Gap

**Current:** D3 now has versioned gold-set packages, versioned baseline
prediction packages, a pre-run comparison protocol validator, and
`make d3-comparison-preflight ...` for standalone package/protocol
cross-checking. Phase 0 can score `D3_GOLD=...` and `D3_BASELINES=...`, but
the scoring boundary does not enforce or record the registered D3 comparison
preflight.

**Target:** Add optional score-time D3 comparison preflight enforcement:

- `scripts/bench_phase0.py` accepts `--d3-comparison-protocol-file`.
- `make bench` accepts `D3_PROTOCOL=protocol.json`.
- `qc_cli.py bench` forwards `--d3-comparison-protocol-file`.
- Phase 0 package manifests accept `d3_comparison_protocol_file` and resolve it
  relative to the manifest path.
- When a D3 protocol is supplied, Phase 0 runs D3 comparison preflight against
  the raw supplied `--d3-gold-file` and `--d3-baselines-file` payloads before
  scoring.
- Failed preflight blocks stdout scorecard success, output writes, and artifact
  writes with a machine-readable error and preflight report.
- Passing preflight is included at `_meta.preflight_reports.d3_comparison`.
- `_meta.input_hashes`, artifact command provenance, and manifests include the
  D3 protocol file hash/path.
- Existing unguarded D3 gold/baseline scoring remains compatible when no
  protocol is supplied.

**Non-target:** This slice does not run or create baselines, evaluate D3
structured metric criteria against scorecard output, collect held-out labels,
add full semantic/multi-label D3 agreement, or license expert-parity,
superiority, methodological-validity, or SOTA claims.

**Why:** A standalone preflight is useful, but the benchmark boundary is where
protocol drift must be caught. This slice closes the D3 package/protocol
enforcement gap while preserving legacy unguarded local accounting.

---

## References Reviewed

- `docs/plans/completed/D3_BASELINE_COMPARISON_PREFLIGHT.md` - standalone D3
  protocol/gold/baseline preflight now exists.
- `qc_clean/core/d3_comparison_preflight.py` - report schema and cross-check
  behavior.
- `scripts/bench_phase0.py` - D4/D6/D8/D9/confidence/INV-7 score-time guard
  patterns, input hashes, artifact command provenance.
- `scripts/run_phase0_benchmark_package.py` - package-manifest path forwarding.
- `qc_cli.py` - top-level bench flag parity.
- `tests/test_bench_phase0_script.py`, `tests/test_qc_cli_bench.py`,
  `tests/test_phase0_benchmark_package.py` - current Phase 0 guard and
  forwarding tests.
- Coordination check: no active claim files under
  `~/.claude/coordination/claims`; `agent-memory recall 'active decisions'
  --project qualitative_coding` returned only low-relevance completed-task
  entries.

---

## Research Basis For This Slice

No new external research. This implements the deterministic score-time guard
already implied by the D3 protocol/preflight and existing Phase 0 guard
patterns.

---

## Design Decisions

- Guard flag names:
  - Make: `D3_PROTOCOL=protocol.json`
  - Script/CLI: `--d3-comparison-protocol-file protocol.json`
  - Package manifest: `d3_comparison_protocol_file`
- Scorecard metadata names:
  - Passing report: `_meta.preflight_reports.d3_comparison`
  - Input hash: `d3_comparison_protocol_file_sha256`
  - Artifact command field: `d3_comparison_protocol_file`
- Guard strictness:
  - If a D3 protocol is supplied without both `--d3-gold-file` and
    `--d3-baselines-file`, the guard fails before scoring.
  - Guarded inputs must be versioned D3 gold and baseline packages because the
    standalone preflight validators require those contracts. Legacy raw D3
    gold/baseline inputs remain supported only in unguarded scoring.
- File hash handling:
  - Pass `prediction_file_sha256_by_baseline` to the preflight by mapping every
    baseline name in the raw D3 baseline package to the supplied baseline file
    SHA-256.

---

## Capabilities

Internal score-time guard capability only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `bench_d3_comparison_preflight_guard` | D3 comparison protocol JSON + versioned D3 gold package JSON + versioned D3 baseline package JSON | Phase 0 scorecard with preflight report or JSON error | qualitative_coding | `make bench`, `qc_cli.py bench`, Phase 0 package runner, artifact package writers | free |

### Capability Validation

- [ ] Matching protocol/gold/baseline packages score successfully.
- [ ] Passing preflight report is recorded in
  `_meta.preflight_reports.d3_comparison`.
- [ ] D3 protocol file hash is recorded in `_meta.input_hashes`.
- [ ] D3 protocol file path is recorded in artifact command provenance.
- [ ] Failed preflight blocks stdout scorecard success, output writes, and
  artifact writes.
- [ ] Phase 0 package manifests forward `d3_comparison_protocol_file`.
- [ ] Existing unguarded D3 scoring remains compatible.

---

## Files Affected

- `scripts/bench_phase0.py`
- `scripts/run_phase0_benchmark_package.py`
- `qc_cli.py`
- `Makefile`
- `tests/test_bench_phase0_script.py`
- `tests/test_qc_cli_bench.py`
- `tests/test_phase0_benchmark_package.py`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Write failing tests for matching D3 score-time guard, mismatched guard
   blocking output/artifacts, package-manifest forwarding, and top-level CLI
   forwarding.
2. Add `--d3-comparison-protocol-file` to `scripts/bench_phase0.py`.
3. Preserve raw D3 gold/baseline payloads for preflight while continuing to use
   the existing scorecard-compatible conversions for scoring.
4. Run D3 comparison preflight before `phase0_scorecard()` and before output or
   artifact writes.
5. Attach passing preflight report under `_meta.preflight_reports.d3_comparison`.
6. Add D3 protocol file hash/path to input hashes, artifact command provenance,
   and Phase 0 package manifest forwarding.
7. Add `D3_PROTOCOL` to `make bench` and the matching `qc_cli.py bench` flag.
8. Update docs with the score-time-guard caveat.
9. Run focused tests, focused Ruff, Make dry-run, docs checks, and full
   `make check`.
10. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d3_comparison_protocol_guard_allows_matching_inputs` | Matching versioned D3 protocol/gold/baseline packages score, record `_meta.preflight_reports.d3_comparison`, hash the protocol file, and do not mutate state. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d3_comparison_protocol_guard_blocks_mismatch_and_writes_no_output` | Failed D3 preflight returns JSON error and writes no output file or artifact directory. |
| `tests/test_phase0_benchmark_package.py` | `test_phase0_benchmark_package_forwards_d3_comparison_protocol` | Package manifest field `d3_comparison_protocol_file` resolves relative paths and forwards the canonical bench flag. |
| `tests/test_qc_cli_bench.py` | `test_qc_cli_bench_forwards_all_phase0_flags` | Top-level bench CLI forwards `--d3-comparison-protocol-file`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py tests/test_phase0_benchmark_package.py tests/test_d3_comparison_preflight.py -k "d3_comparison or d3_baseline or forwards_all_phase0_flags or phase0_benchmark_package" -q` | New score-time guard plus adjacent D3 preflight/package forwarding behavior. |
| `python -m ruff check scripts/bench_phase0.py scripts/run_phase0_benchmark_package.py qc_cli.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py tests/test_phase0_benchmark_package.py` | Focused lint. |
| `make -n bench ID=project D3_GOLD=d3_gold.json D3_BASELINES=d3_baselines.json D3_PROTOCOL=protocol.json` | Make target forwards protocol/gold/baseline inputs. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `scripts/bench_phase0.py` exposes `--d3-comparison-protocol-file`.
- [ ] `make bench D3_PROTOCOL=... D3_GOLD=... D3_BASELINES=...` forwards the
  protocol to the scorecard script.
- [ ] `qc_cli.py bench --d3-comparison-protocol-file ...` forwards the protocol
  to the scorecard script.
- [ ] Phase 0 package manifests accept and forward
  `d3_comparison_protocol_file`.
- [ ] Passing D3 preflight is recorded under
  `_meta.preflight_reports.d3_comparison`.
- [ ] Failed D3 preflight blocks scorecard, output, and artifact writes.
- [ ] `_meta.input_hashes` includes `d3_comparison_protocol_file_sha256`.
- [ ] Artifact command provenance includes `d3_comparison_protocol_file`.
- [ ] Existing unguarded D3 gold/baseline scoring remains compatible.
- [ ] Docs state this is score-time provenance only, not held-out D3 evidence,
  live baseline evidence, expert parity, superiority, methodological-validity
  evidence, or SOTA.

> Process criteria:
- [ ] TDD red state observed before implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] Make dry-run confirms flag forwarding.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Plan is moved to completed with verification evidence.
- [ ] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Guard scores legacy/raw D3 inputs | Preflight received converted scorecard payloads instead of raw versioned packages | Preserve raw JSON payloads for protocol preflight; only converted payloads go to `state.config.extra`. |
| `D3_PROTOCOL` without D3 gold/baselines scores anyway | Preflight not run or missing payloads converted to permissive defaults | Run preflight whenever protocol is supplied and let missing payloads fail before scoring. |
| Failed preflight still writes output/artifact | Error handling occurs after scorecard/output/artifact generation | Run preflight before `phase0_scorecard()` and before any output/artifact writes. |
| Prediction hash lock cannot be checked | File hash was not mapped by baseline name | Map every raw `application_baselines[*].name` in the supplied baseline package to the file SHA-256 before preflight. |
| Input hashes omit protocol file | `phase0_input_hashes()` signature not updated | Add `d3_comparison_protocol_file` and assert the hash in tests. |
| Package manifests cannot use the guard | Manifest schema/path flag map omits `d3_comparison_protocol_file` | Add manifest field and forwarding test. |
| CLI wrapper misses new flag | Top-level `qc_cli.py bench` not updated with script parity | Add parser, forwarding logic, and flag-parity test. |
