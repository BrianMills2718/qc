# Plan #57: D3 Baseline Comparison Scorecard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Held-out D3 baseline comparison packages

---

## Gap

**Current:** D3 application-validity scoring can compare the system to supplied
adjudicated application gold and can surface human-ceiling metadata, but it
cannot score externally supplied baseline predictions against the same D3 gold.
D7 already has this comparison path for disconfirmation baselines.

**Target:** Add D3 exact-anchor baseline comparison using the existing
scorecard primitives. `make bench ID=<project> D3_BASELINES=baselines.json` /
`scripts/bench_phase0.py --d3-baselines-file baselines.json` will load
baseline prediction records into `ProjectState.config.extra["application_baselines"]`
in memory only. `application_validity_d3.baselines` will report baseline
TP/FP/FN, recall, precision, F1, Wilson intervals, F1 bootstrap intervals, and
system-minus-baseline deltas with local paired exact-key bootstrap intervals.

**Why:** Public D3 claims require comparison to named baselines on the same
held-out gold. This slice adds the repeatable comparison substrate without
creating or implying populated held-out data.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D3 metrics, D7 baseline comparison precedent,
  and claim discipline.
- `docs/PROJECT_THEORY_AND_GOALS.md` - state ledger and roadmap caveats.
- `qc_clean/core/bench.py` - D3 exact scoring, D7 baseline scorer, bootstrap
  interval helpers.
- `scripts/bench_phase0.py` - external file loading, input hashes, provenance.
- `scripts/run_phase0_benchmark_package.py` - Phase 0 package path forwarding.
- `tests/test_bench_phase0.py` and `tests/test_bench_phase0_script.py` - D7
  baseline and external-file coverage.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with provider errors; circuit breaker applies. No
  active local coordination claims were present.

---

## Research Basis For This Slice

No external research needed. This is a deterministic scorer extension that
reuses the existing exact-anchor baseline comparison substrate already built for
D7.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D3 baseline comparison scorecard | `application_baselines` records with D3 exact anchor predictions | `application_validity_d3.baselines` metrics and deltas | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [ ] D3 baseline metadata is validated and duplicate names fail loudly.
- [ ] Baseline predictions score against the same D3 gold key universe as the system.
- [ ] Baseline deltas include paired exact-key bootstrap intervals when enabled.
- [ ] External `--d3-baselines-file` input is applied in memory without mutating saved project state.
- [ ] Phase 0 package manifests can forward `d3_baselines_file`.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `scripts/run_phase0_benchmark_package.py` (modify)
- `Makefile` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `tests/test_phase0_benchmark_package.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add an `ApplicationBaselinePrediction` model using D3
   `ApplicationGoldAnchor` records and the extra key `application_baselines`.
2. Extend `application_validity_d3_scorecard` to score D3 baselines with the
   existing exact-anchor score and paired delta bootstrap helpers.
3. Add `--d3-baselines-file`, `D3_BASELINES=`, input-hash, command-provenance,
   and package-manifest forwarding support.
4. Add focused tests for state metadata, external file loading/no-mutation,
   duplicate baseline failure, bootstrap disabling, and package forwarding.
5. Update docs to describe the new D3 baseline substrate without claiming
   held-out or expert-parity evidence.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D3 baselines score against same gold | Baseline metrics, matched/missed/extra keys, deltas, and delta CI shape. |
| `tests/test_bench_phase0.py` | D3 baseline bootstrap disabled | Disabling exact bootstrap removes baseline F1 and delta CIs. |
| `tests/test_bench_phase0.py` | invalid D3 baseline metadata fails | Duplicate baseline names fail loudly. |
| `tests/test_bench_phase0_script.py` | D3 baselines file no mutation | External file scores and saved project state remains unchanged. |
| `tests/test_bench_phase0_script.py` | invalid D3 baselines file fails | Bad payload exits with JSON error. |
| `tests/test_phase0_benchmark_package.py` | package forwards D3 baselines file | Manifest path resolves and reaches canonical bench flags. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` D3/D7 exact-score tests | Existing scorecard sections must not regress. |
| `tests/test_bench_phase0_script.py` input hash/artifact tests | Provenance stays complete. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `application_validity_d3.baselines` appears when D3 gold and D3 baseline
  predictions are supplied.
- [ ] Baseline records use stable names and duplicate names fail loudly.
- [ ] System-minus-baseline deltas are reported for recall, precision, and F1.
- [ ] Delta CIs are omitted when `phase0_exact_bootstrap.enabled=false`.
- [ ] `make bench D3_BASELINES=...`, `--d3-baselines-file`, and
  `d3_baselines_file` package manifests are supported.
- [ ] Input hashes and artifact command provenance include the D3 baselines file.
- [ ] Docs preserve the caveat that this is a substrate, not populated held-out
  benchmark evidence.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should a future D3 baseline export runner generate `application_baselines`
  from generic-prompt or commercial-tool outputs? - Status: DEFERRED | Why it
  matters: public comparisons need real baseline runs, but this slice only adds
  the scorer and file/package interface.
