# Plan #173: INV-7 Score-Time Preflight Guard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** INV-7 live protocol/preflight package surfaces
**Blocks:** Broader held-out live INV-7 benchmark accounting that can be
populated later without rerouting Phase 0

---

## Gap

**Current:** INV-7 live prompt-injection work has schema_version=1 result
packages, a pre-run live protocol validator, and
`make inv7-live-preflight PROTOCOL=... PACKAGE=...` for protocol/result
cross-checking. Phase 0 can score `PROMPT_INJECTION=inv7.json`, but it does not
have a score-time guard equivalent to D4/D6/D8/D9/confidence: a user can produce
an INV-7 scorecard from a live package without requiring or recording the
registered protocol preflight.

**Target:** Add score-time INV-7 live preflight enforcement:

- `scripts/bench_phase0.py` accepts `--inv7-live-protocol-file`.
- `make bench` accepts `INV7_PROTOCOL=protocol.json`.
- `qc_cli.py bench` forwards `--inv7-live-protocol-file`.
- When a protocol is supplied, Phase 0 preflights that protocol against the
  supplied `--prompt-injection-file` package before scoring.
- Failed preflight blocks scorecard/output/artifact writes with a
  machine-readable error and preflight report.
- Passing preflight is included at `_meta.preflight_reports.inv7_live`.
- `_meta.input_hashes`, artifact manifests, and command provenance include the
  protocol file hash/path.
- Existing unguarded `PROMPT_INJECTION=` scoring remains compatible when no
  protocol is supplied.

**Why:** The roadmap still lacks a broader held-out live adversarial benchmark
result. Before populating one, the bench boundary should enforce that a live
result package actually matches the pre-registered protocol. This slice adds
that deterministic accounting layer without running live models or claiming
prompt-injection robustness.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-7 remains partial; broader held-out
  live adversarial benchmark evidence is still missing.
- `docs/EVALUATION_HARNESS.md` - Phase 0 can score INV-7 fixture outcomes, but
  the full prompt_eval-backed suite and broader live benchmark remain future
  work.
- `qc_clean/core/inv7_live_protocol.py` - protocol package contract.
- `qc_clean/core/inv7_live_preflight.py` - protocol/result preflight logic.
- `qc_clean/core/inv7_package.py` - schema_version=1 INV-7 result packages and
  scorecard payload conversion.
- `scripts/bench_phase0.py` - existing score-time guard patterns for D4/D6/D8/D9
  and confidence calibration.
- `Makefile` and `qc_cli.py` - bench command surfaces.
- Coordination/memory check: no active claim files; `agent-memory recall`
  returned only low-relevance historical completed-task entries.

---

## Research Basis For This Slice

No new external research. This implements the deterministic score-time guard
already implied by the INV-7 protocol/preflight and evaluation-harness patterns.

---

## Capabilities

Internal score-time guard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `bench_inv7_live_preflight_guard` | INV-7 live protocol JSON + INV-7 live result package JSON | Phase 0 scorecard with preflight report or JSON error | qualitative_coding | `make bench`, `qc_cli.py bench`, artifact package writers | free |

### Capability Validation

- [ ] Matching live protocol/result packages score successfully.
- [ ] Passing preflight report is recorded in `_meta.preflight_reports.inv7_live`.
- [ ] Protocol file hash is recorded in `_meta.input_hashes`.
- [ ] Protocol file path is recorded in artifact command provenance.
- [ ] Failed preflight blocks stdout scorecard success, output writes, and
  artifact writes.
- [ ] Existing unguarded prompt-injection scoring remains compatible.

---

## Files Affected

- `scripts/bench_phase0.py`
- `qc_cli.py`
- `Makefile`
- `tests/test_bench_phase0_script.py`
- `tests/test_qc_cli_bench.py`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Write failing tests for matching and mismatched INV-7 score-time preflight,
   plus CLI forwarding if needed.
2. Add `--inv7-live-protocol-file` to `scripts/bench_phase0.py`.
3. Load the raw INV-7 package payload for preflight while preserving the existing
   scorecard conversion path.
4. Attach passing preflight report under `_meta.preflight_reports.inv7_live` and
   add protocol hash/path to input hashes, command provenance, and artifact
   manifests through existing metadata flow.
5. Add `INV7_PROTOCOL` to `make bench` and the matching `qc_cli.py bench` flag.
6. Update docs with the score-time guard caveat.
7. Run focused tests, focused Ruff, docs checks, and full `make check`.
8. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_inv7_live_protocol_guard_allows_matching_package` | Score-time guard passes and records `_meta.preflight_reports.inv7_live` plus protocol input hash. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_inv7_live_protocol_guard_blocks_mismatch_and_writes_no_output` | Failed preflight returns JSON error and does not write output or artifacts. |
| `tests/test_qc_cli_bench.py` | `test_qc_cli_bench_forwards_inv7_live_protocol_file` | Top-level bench CLI forwards the protocol flag to the canonical script. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0_script.py tests/test_inv7_live_preflight.py tests/test_inv7_live_protocol.py tests/test_qc_cli_bench.py -k "inv7 or bench" -q` | New score-time guard plus existing INV-7 protocol/preflight behavior. |
| `python -m ruff check scripts/bench_phase0.py qc_cli.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py` | Focused lint. |
| `make -n bench ID=project PROMPT_INJECTION=inv7.json INV7_PROTOCOL=protocol.json` | Make target forwards the protocol flag. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `scripts/bench_phase0.py` exposes `--inv7-live-protocol-file`.
- [ ] `make bench INV7_PROTOCOL=... PROMPT_INJECTION=...` forwards the protocol
  to the scorecard script.
- [ ] `qc_cli.py bench --inv7-live-protocol-file ... --prompt-injection-file ...`
  forwards the protocol to the scorecard script.
- [ ] Passing INV-7 preflight is recorded under
  `_meta.preflight_reports.inv7_live`.
- [ ] Failed INV-7 preflight blocks scorecard, output, and artifact writes.
- [ ] `_meta.input_hashes` includes `inv7_live_protocol_file_sha256`.
- [ ] Artifact command provenance includes `inv7_live_protocol_file`.
- [ ] Existing unguarded `PROMPT_INJECTION=` scoring remains compatible.
- [ ] Docs state this is protocol/accounting only, not live prompt-injection
  robustness evidence, model-obedience proof, held-out benchmark evidence,
  methodological-validity evidence, or SOTA.

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
| Guard scores legacy raw list inputs | Protocol preflight received converted outcome rows instead of raw package | Preserve raw JSON payload for protocol preflight; only converted rows go to scorecard config. |
| Failed preflight still writes output/artifact | Error handling occurs after output/artifact write | Run preflight before `phase0_scorecard()` and before any output/artifact writes. |
| Existing prompt-injection tests break | Protocol accidentally made mandatory | Keep `--inv7-live-protocol-file` optional and only guard when supplied. |
| Input hashes omit protocol file | `phase0_input_hashes()` signature not updated | Add explicit `inv7_live_protocol_file` parameter and assert in tests. |
| CLI wrapper misses new flag | Top-level `qc_cli.py bench` not updated with script parity | Add parser and forwarding test. |

