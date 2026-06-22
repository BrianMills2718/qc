# Plan #56: Phase 0 Benchmark Package Runner

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Repeatable benchmark-package execution

---

## Gap

**Current:** Phase 0 scorecards can consume many external benchmark inputs via
individual flags (`D3_GOLD=`, `GOLD=`, `BASELINES=`, `CODEBOOK_QUALITY=`,
`BIAS_COUNTERFACTUAL=`, `GT_FIDELITY=`, `PREFERENCE=`, `CALIBRATION=`,
`PROMPT_INJECTION=`), but there is no single manifest that records one coherent
benchmark package and runs the canonical scorecard from it.

**Target:** Add a versioned Phase 0 benchmark package runner. A JSON manifest
with `schema_version=1`, `project_id`, optional external input paths, optional
`observability_db`, optional `trace_id`, optional `output`, and optional
`artifact_dir` will be validated fail-loudly, paths will resolve relative to the
manifest file, and the runner will invoke `scripts/bench_phase0.py` with the
same canonical flags. Add `make bench-package PACKAGE=package.json`.

**Why:** This is the next step from many local scorecard substrates toward a
repeatable held-out benchmark workflow. It improves provenance and agent
drivability without claiming that any populated held-out benchmark exists.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - Phase 0 scorecard surfaces and remaining
  held-out benchmark work.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline: substrate is not SOTA
  or methodological validity.
- `scripts/bench_phase0.py` - canonical bench CLI and external file flags.
- `Makefile` - agent-facing target pattern.
- `tests/test_bench_phase0_script.py` - external file and artifact behavior.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with OpenRouter embedding-provider errors, so the
  circuit breaker applies; no local coordination claims were present.

---

## Research Basis For This Slice

No additional external research beyond repo-local references. This slice is
orchestration and validation over existing deterministic Phase 0 inputs; it does
not create or evaluate held-out expert data.

---

## Capabilities

Internal runner capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Phase 0 benchmark package runner | Versioned package manifest | Canonical Phase 0 scorecard output | qualitative_coding | agents, CI, benchmark artifacts | free |

### Capability Validation

- [ ] Manifest schema is validated with unknown keys rejected.
- [ ] Input paths resolve relative to the manifest file.
- [ ] Runner invokes `bench_phase0.main` with canonical flags only.
- [ ] Make target is agent-drivable.

---

## Files Affected

- `scripts/run_phase0_benchmark_package.py` (new)
- `Makefile` (modify)
- `tests/test_phase0_benchmark_package.py` (new)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add a Pydantic manifest model with `extra="forbid"` and `schema_version=1`.
2. Resolve relative file/directory paths from the manifest directory and build
   canonical `bench_phase0` argv.
3. Add `scripts/run_phase0_benchmark_package.py` with JSON error output on
   manifest/read/validation failures.
4. Add `make bench-package PACKAGE=package.json`.
5. Add tests for relative-path forwarding, unknown-key failure, and output/artifact
   propagation through the canonical bench script.
6. Update docs to identify the package runner as provenance/orchestration, not
   populated benchmark evidence.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_phase0_benchmark_package.py` | package forwards relative inputs | Manifest paths resolve relative to package and scorecard sections are scored. |
| `tests/test_phase0_benchmark_package.py` | unknown key fails | Manifest `extra="forbid"` fails loudly. |
| `tests/test_phase0_benchmark_package.py` | artifact and output paths forward | Manifest `output` and `artifact_dir` reach canonical bench behavior. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0_script.py` | Canonical bench behavior stays unchanged. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `scripts/run_phase0_benchmark_package.py <package.json>` runs the
  canonical Phase 0 bench path.
- [ ] Manifest paths resolve relative to the manifest file.
- [ ] Unknown manifest fields fail loudly.
- [ ] `make bench-package PACKAGE=package.json` is available.
- [ ] Docs preserve the caveat that a package runner is not populated held-out
  benchmark evidence.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should future package manifests include prompt/model hashes? — Status:
  DEFERRED | Why it matters: full public benchmark artifacts need prompt/model
  hashing, but Phase 0 package execution only orchestrates existing local
  deterministic scorecards.
