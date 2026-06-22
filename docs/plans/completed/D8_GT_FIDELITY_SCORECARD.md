# Plan #52: D8 GT Fidelity Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D8 grounded-theory fidelity measurement substrate

---

## Outcome

Implemented the deterministic Phase 0 `gt_fidelity_d8` scorecard for externally
supplied GT-fidelity rubric outcomes. The bench surface now accepts
`GT_FIDELITY=gt_fidelity.json` / `--gt-fidelity-file`, hashes the D8 file in
`_meta.input_hashes`, records it in artifact command provenance, and keeps the
file input in memory without mutating saved project state. The scorecard
reports total evaluations, metric summaries, overall mean, evaluator-type
summaries, and scope summaries. Docs state that this is not full GT,
methodological saturation, expert-rubric acceptance, or SOTA evidence.

## Verification

- `python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py -q` - 71 passed.
- `python -m ruff check qc_clean/core/bench.py scripts/bench_phase0.py qc_cli.py tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py` - passed.
- `python scripts/check_markdown_links.py` - passed.
- `python scripts/sync_plan_status.py --check` - passed.
- `make check` - 752 passed, 1 skipped, 8 deselected; Ruff and docs checks passed; type check not yet configured.

---

## Gap

**Current:** The evaluation harness defines D8 GT fidelity as expert-rubric
acceptance over constant comparison, category development, memo quality, and
saturation justification, but Phase 0 has no D8 scorecard section and no
agent-drivable way to feed external GT-fidelity rubric outcomes into
`make bench`.

**Target:** Add a deterministic `gt_fidelity_d8` scorecard that accepts
externally supplied rubric outcomes from
`ProjectState.config.extra["gt_fidelity_evaluations"]` or
`GT_FIDELITY=` / `--gt-fidelity-file`. The scorecard will summarize
0-1 rubric scores for constant comparison, category development, memo quality,
saturation justification, and overall mean, grouped by evaluator type and
rubric scope.

**Why:** This creates the local D8 measurement substrate while preserving the
hard claim discipline: GT fidelity, methodological saturation, and "full
grounded theory" are not established until expert rubric outcomes and a
pre-registered benchmark protocol are populated.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D8 expert-rubric definition and Phase 2 target.
- `docs/PROJECT_THEORY_AND_GOALS.md` - GT-inspired caveat, INV-4 status, and
  no-full-GT claim discipline.
- `qc_clean/core/bench.py` - external D4/D6/D9 scorecard patterns.
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
adds deterministic accounting over externally supplied GT-fidelity rubric
outcomes; future rubric design, expert collection, GT protocol validation, and
public benchmark statistics belong in the prompt_eval-backed suite.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D8 GT fidelity scorecard | External GT-fidelity rubric outcomes | Rubric summaries by metric/type/scope | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [x] GT-fidelity outcomes are Pydantic-validated and fail loudly when malformed.
- [x] Rubric metrics are constrained to 0-1.
- [x] Overall mean and metric summaries are computed deterministically.
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
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add `GTFidelityEvaluation` and `gt_fidelity_scorecard` in
   `qc_clean/core/bench.py`.
2. Include `gt_fidelity_d8` in `phase0_scorecard`, returning an explicit
   unavailable state when no external rubric outcomes exist.
3. Add `--gt-fidelity-file` to `scripts/bench_phase0.py` and `qc_cli.py`, and
   `GT_FIDELITY=` to `make bench`.
4. Hash the external D8 file and include it in Phase 0 artifact command
   provenance.
5. Add focused tests for unavailable, scored, invalid metadata, external-file
   loading, hash/provenance, and CLI forwarding.
6. Update docs to mark a D8 Phase 0 substrate as present while preserving the
   no-full-GT/no-methodological-saturation/no-SOTA caveat.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D8 unavailable test | Missing rubric outcomes are explicit non-evidence. |
| `tests/test_bench_phase0.py` | D8 scored test | Metric summaries, overall mean, and grouping are correct. |
| `tests/test_bench_phase0.py` | D8 invalid metadata test | Out-of-range rubric values fail loudly. |
| `tests/test_bench_phase0_script.py` | D8 file input test | External D8 JSON is applied in memory without mutating project state. |
| `tests/test_bench_phase0_script.py` | D8 hash/provenance test | External D8 file hash and artifact command provenance are recorded. |
| `tests/test_qc_cli_bench.py` | D8 wrapper forwarding test | `qc_cli bench --gt-fidelity-file` reaches the canonical script. |

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
- [x] Scorecard has `gt_fidelity_d8` with explicit unavailable state when no
  rubric outcomes exist.
- [x] Scored output reports total evaluations, metric summaries, overall mean,
  evaluator-type summaries, and scope summaries.
- [x] External D8 JSON file can be supplied through Make, script, and `qc_cli`
  without mutating saved project state.
- [x] Phase 0 input hashes and artifact command provenance include the D8
  external file.
- [x] Docs preserve the caveat that this is not full GT, methodological
  saturation, expert-rubric acceptance, or SOTA evidence.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] What exact D8 rubric and expert threshold should be pre-registered? —
  Status: DEFERRED | Why it matters: expert-rubric acceptance requires a
  benchmark protocol fixed before the run, likely in the prompt_eval-backed
  suite.
