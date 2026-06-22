# Plan #51: D9 Interpretive Preference Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D9 interpretive-depth measurement substrate

---

## Outcome

Implemented the deterministic Phase 0 `interpretive_preference_d9` scorecard
for externally supplied forced-choice preference outcomes. The bench surface now
accepts `PREFERENCE=preference.json` / `--interpretive-preference-file`, hashes
the D9 file in `_meta.input_hashes`, records it in artifact command provenance,
and keeps the file input in memory without mutating saved project state. The
scorecard reports system wins, human wins, ties, tie rate, non-tie system
preference rate, a Wilson interval, and evaluator/criterion summaries. Docs
state that this is not blind expert-parity or SOTA evidence.

## Verification

- `python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py -q` - 66 passed.
- `python -m ruff check qc_clean/core/bench.py scripts/bench_phase0.py qc_cli.py tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py` - passed.
- `python scripts/check_markdown_links.py` - passed.
- `python scripts/sync_plan_status.py --check` - passed.
- `make check` - 747 passed, 1 skipped, 8 deselected; Ruff and docs checks passed; type check not yet configured.

---

## Gap

**Current:** The evaluation harness defines D9 interpretive depth as a blind
forced-choice expert preference task, but Phase 0 has no D9 scorecard section
and no agent-drivable way to feed external preference outcomes into `make bench`.

**Target:** Add a deterministic `interpretive_preference_d9` scorecard that
accepts externally supplied forced-choice outcomes from
`ProjectState.config.extra["interpretive_preference_evaluations"]` or
`PREFERENCE=` / `--interpretive-preference-file`. The scorecard will report
system wins, human wins, ties, tie rate, system preference rate among non-ties,
and a Wilson interval for the system preference rate.

**Why:** This creates the local D9 measurement substrate while preserving the
hard claim discipline: parity is not established until blind expert preference
outcomes are populated under a pre-registered benchmark protocol.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D9 forced-choice preference definition and
  parity caveat.
- `docs/PROJECT_THEORY_AND_GOALS.md` - "hard wall" and no-parity/no-SOTA claim
  discipline.
- `qc_clean/core/bench.py` - external scorecard patterns and Wilson interval
  helper.
- `scripts/bench_phase0.py`, `qc_cli.py`, `Makefile` - external file input,
  hashing, provenance, and wrapper surfaces.
- `tests/test_bench_phase0.py`, `tests/test_bench_phase0_script.py`,
  `tests/test_qc_cli_bench.py` - scorecard and bench wrapper coverage.
- Memory context: unavailable. The last three `agent-memory recall` attempts in
  this session failed with the same OpenRouter 402/403 embedding-provider
  errors, so the circuit breaker applies; no local coordination claims were
  present.

---

## Research Basis For This Slice

No additional external research beyond repo-local references. This slice only
adds deterministic accounting over externally supplied forced-choice outcomes;
future preference-case generation, blinding, expert collection,
non-inferiority margins, and public benchmark statistics belong in the
prompt_eval-backed suite.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D9 interpretive preference scorecard | Forced-choice preference outcomes | Preference counts/rates/CI | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [x] Preference outcomes are Pydantic-validated and fail loudly when malformed.
- [x] Allowed preferences are exactly `system`, `human`, and `tie`.
- [x] System preference rate and Wilson interval are computed over non-tie cases.
- [x] External files are hashed in `_meta.input_hashes` and recorded in artifact command provenance.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `qc_cli.py` (modify)
- `Makefile` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `tests/test_qc_cli_bench.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add `InterpretivePreferenceEvaluation` and
   `interpretive_preference_scorecard` in `qc_clean/core/bench.py`.
2. Include `interpretive_preference_d9` in `phase0_scorecard`, returning an
   explicit unavailable state when no external preference outcomes exist.
3. Add `--interpretive-preference-file` to `scripts/bench_phase0.py` and
   `qc_cli.py`, and `PREFERENCE=` to `make bench`.
4. Hash the external D9 file and include it in Phase 0 artifact command
   provenance.
5. Add focused tests for unavailable, scored, invalid metadata, external-file
   loading, hash/provenance, and CLI forwarding.
6. Update docs to mark a D9 Phase 0 substrate as present while preserving the
   no-blind-expert-parity/no-SOTA caveat.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D9 unavailable test | Missing preference outcomes are explicit non-evidence. |
| `tests/test_bench_phase0.py` | D9 scored test | Counts, tie rate, system preference rate, and Wilson CI are correct. |
| `tests/test_bench_phase0.py` | D9 invalid metadata test | Invalid preference values fail loudly. |
| `tests/test_bench_phase0_script.py` | D9 file input test | External D9 JSON is applied in memory without mutating project state. |
| `tests/test_bench_phase0_script.py` | D9 hash/provenance test | External D9 file hash and artifact command provenance are recorded. |
| `tests/test_qc_cli_bench.py` | D9 wrapper forwarding test | `qc_cli bench --interpretive-preference-file` reaches the canonical script. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Main Phase 0 scorecard shape. |
| `tests/test_bench_phase0_script.py` | Bench script external-input and artifact behavior. |
| `tests/test_qc_cli_bench.py` | Top-level wrapper behavior. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Scorecard has `interpretive_preference_d9` with explicit unavailable state
  when no forced-choice outcomes exist.
- [x] Scored output reports total cases, system wins, human wins, ties, tie
  rate, system preference rate among non-ties, and Wilson interval.
- [x] External D9 JSON file can be supplied through Make, script, and `qc_cli`
  without mutating saved project state.
- [x] Phase 0 input hashes and artifact command provenance include the D9
  external file.
- [x] Docs preserve the caveat that this is not blind expert-parity or SOTA
  evidence.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] How should the D9 non-inferiority margin be pre-registered? — Status:
  DEFERRED | Why it matters: parity claims require a margin fixed before the
  benchmark run, likely in the prompt_eval-backed suite.
