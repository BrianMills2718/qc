# Plan #48: D6 Counterfactual Bias Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D6 bias measurement substrate; future prompt_eval-backed counterfactual suite

---

## Outcome

Phase 0 scorecards now include `bias_counterfactual_d6`, which scores
externally supplied counterfactual identity-swap outcomes from
`ProjectState.config.extra["bias_counterfactual_evaluations"]`,
`make bench BIAS_COUNTERFACTUAL=bias.json`, `scripts/bench_phase0.py
--bias-counterfactual-file`, or `qc_cli.py bench --bias-counterfactual-file`.
The scorecard reports invariant-case code-change rate, mean code-set Jaccard
distance, changed case IDs, and by-attribute summaries; external D6 files are
hashed in `_meta.input_hashes` and recorded in Phase 0 artifact command
provenance. The docs explicitly keep this as a local measurement substrate only,
not a populated bias audit, causal proof, or bias-free claim.

**Verification:**
- `python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py -q` - 56 passed.
- `python -m ruff check qc_clean/core/bench.py scripts/bench_phase0.py qc_cli.py tests/test_bench_phase0.py tests/test_bench_phase0_script.py tests/test_qc_cli_bench.py` - passed.
- `python scripts/check_markdown_links.py` - passed.
- `make check` - 737 passed, 1 skipped, 8 deselected; Ruff and docs checks passed; type check not yet configured.

## Gap

**Current:** The evaluation harness names D6 bias as stratified error plus
counterfactual identity-cue masking/swapping, but Phase 0 has no D6 scorecard
section or agent-drivable way to feed externally generated counterfactual
outcomes into `make bench`.

**Target:** Add a deterministic D6 scorecard section that scores externally
supplied counterfactual identity-swap outcomes from
`ProjectState.config.extra["bias_counterfactual_evaluations"]` or a
`BIAS_COUNTERFACTUAL=` / `--bias-counterfactual-file` JSON file. The scorecard
will report invariant-case code-change rate, mean code-set Jaccard distance,
changed case IDs, and attribute-group summaries.

**Why:** This creates the missing local measurement substrate for INV-5/D6
without pretending the repo has run a bias audit, has causal bias proof, or is
bias-free.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D6 bias requirement and Phase 0 harness scope.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-5 and claim-discipline caveats.
- `qc_clean/core/bench.py` - Phase 0 scorecard and external-evaluation patterns.
- `scripts/bench_phase0.py` - external file loading, input hashes, artifact
  provenance.
- `qc_cli.py` and `Makefile` - bench wrapper surfaces.
- `tests/test_bench_phase0.py`, `tests/test_bench_phase0_script.py`,
  `tests/test_qc_cli_bench.py` - scorecard, script, and wrapper tests.
- Memory context: `agent-memory recall 'active decisions qualitative_coding evaluation harness D3 D5 D6 D7 benchmark next lane' --project qualitative_coding` failed before planning because the embedding provider returned OpenRouter 402/403 errors; no local coordination claims were present.

---

## Research Basis For This Slice

No additional external research beyond repo-local references. This slice only
adds deterministic accounting over externally supplied counterfactual outcomes;
the future prompt_eval-backed D6 suite will own frozen case generation,
statistical comparisons, and public benchmark evidence.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D6 counterfactual bias scorecard | Counterfactual case outcomes | Code-change diagnostics | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [x] Counterfactual outcomes are Pydantic-validated and fail loudly when malformed.
- [x] Invariant cases report code-change rate and mean Jaccard distance.
- [x] Attribute buckets report changed-case diagnostics without causal claims.
- [x] External files are hashed in `_meta.input_hashes` and recorded in artifact command provenance.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `qc_cli.py` (modify)
- `Makefile` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `tests/test_qc_cli_bench.py` (modify if wrapper coverage needs updating)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add `BiasCounterfactualEvaluation` and a D6 scorecard function in
   `qc_clean/core/bench.py`.
2. Include the D6 scorecard in `phase0_scorecard`, returning `not_available`
   when no external outcomes exist.
3. Add `--bias-counterfactual-file` to `scripts/bench_phase0.py`, `qc_cli.py`,
   and `BIAS_COUNTERFACTUAL=` to `make bench`.
4. Hash the external D6 file and include it in Phase 0 artifact command
   provenance.
5. Add focused tests for unavailable, scored, invalid metadata, external-file
   loading, hash/provenance, and CLI forwarding where needed.
6. Update docs to mark a D6 Phase 0 substrate as present while preserving the
   no-bias-audit/no-causal-proof caveat.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D6 unavailable test | Missing counterfactual outcomes are explicit non-evidence. |
| `tests/test_bench_phase0.py` | D6 scored test | Code-change rate, Jaccard distance, changed IDs, and attribute buckets are correct. |
| `tests/test_bench_phase0.py` | D6 invalid metadata test | Malformed metadata fails loudly. |
| `tests/test_bench_phase0_script.py` | D6 file input test | External D6 JSON is applied in memory without mutating project state. |
| `tests/test_bench_phase0_script.py` | D6 hash/provenance test | External D6 file hash and artifact command provenance are recorded. |
| `tests/test_qc_cli_bench.py` | D6 wrapper forwarding test | `qc_cli bench --bias-counterfactual-file` reaches the canonical script. |

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
- [x] Scorecard has `bias_counterfactual_d6` with explicit unavailable state when no data exists.
- [x] Scored output reports total cases, invariant cases, changed invariant cases, code-change rate, mean Jaccard distance, changed case IDs, and by-attribute summaries.
- [x] External D6 JSON file can be supplied through Make, script, and `qc_cli` without mutating saved project state.
- [x] Phase 0 input hashes and artifact command provenance include the D6 external file.
- [x] Docs preserve the caveat that this is not a populated bias audit or causal proof.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should the future D6 suite generate identity swaps inside QC or in
  `prompt_eval`? — Status: DEFERRED | Why it matters: frozen case generation,
  model comparison, and statistical testing should probably live in
  `prompt_eval`, not this local scorecard.
