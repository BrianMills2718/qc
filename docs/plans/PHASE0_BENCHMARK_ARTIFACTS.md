# Plan #30: Phase 0 Benchmark Artifacts

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 input hashes; QC bench CLI
**Blocks:** prompt_eval-backed benchmark suite; public benchmark evidence packages

---

## Gap

**Current:** `qc_cli.py bench <project_id>` and `make bench ID=<project_id>`
emit a deterministic Phase 0 scorecard and can write a single JSON file through
`--output`, but there is no versioned `benchmark_results/` artifact package.
The evaluation-harness doc says future benchmark output should be versioned and
include dataset/input hashes, prompt/model hashes, per-dimension scores, CIs,
baseline deltas, and a generated scorecard. Phase 0 now has enough provenance to
write the first non-claiming artifact package, but it only emits ad hoc JSON.

**Target:** Add a thin Phase 0 artifact writer behind
`scripts/bench_phase0.py --artifact-dir <dir>`, `qc_cli.py bench --artifact-dir
<dir>`, and `make bench ARTIFACT_DIR=<dir>`. The writer should create a
versioned run directory containing `scorecard.json` and `manifest.json`.

**Why:** This is the smallest bridge from the deterministic local scorecard to
durable benchmark evidence packages. It preserves the boundary that
`prompt_eval` owns statistical comparisons, bootstrap intervals, and full
experiment tracking; this slice only packages current Phase 0 output with hashes
and claim-discipline metadata.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - target output shape and prompt_eval boundary.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline and current Phase 0
  state ledger.
- `docs/plans/completed/PHASE0_INPUT_HASHES.md` - input hash substrate.
- `docs/plans/completed/QC_BENCH_CLI.md` - canonical CLI wrapper.
- `scripts/bench_phase0.py` - current scorecard CLI and input hashing.
- `qc_cli.py` - bench command forwarding.
- `Makefile` - `bench` target.
- `~/projects/prompt_eval/README.md` and public API - confirms
  `prompt_eval` owns experiment semantics/statistics, and precomputed variant
  comparison exists for later full-suite work.
- Memory context:
  `agent-memory recall 'active decisions qualitative_coding evaluation harness prompt_eval benchmark artifacts' --project qualitative_coding`
  returned historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No external research is needed. This is repo-local artifact packaging around an
already implemented deterministic scorecard. The `prompt_eval` repository was
reviewed locally to keep the boundary clear: no bootstrap, Welch, paired-input,
or evaluator work belongs in this Phase 0 package writer.

---

## Capabilities

This plan creates a repo-local benchmark artifact capability:

| Capability | Input | Output | Owner |
|------------|-------|--------|-------|
| `write_phase0_benchmark_artifact` | Phase 0 scorecard, project metadata, CLI provenance, artifact root | Versioned run directory with `scorecard.json` and `manifest.json` | qualitative_coding |

This is not a cross-project boundary and does not become a `prompt_eval`
experiment runner.

---

## Files Affected

- `scripts/bench_phase0.py` (modify)
- `qc_cli.py` (modify)
- `Makefile` (modify)
- `.gitignore` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `tests/test_qc_cli_bench.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify after closeout)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/PHASE0_BENCHMARK_ARTIFACTS.md` (create, then move to completed)

---

## Plan

### Artifact Contract

When `--artifact-dir ROOT` is supplied, create:

```text
ROOT/
  <utc-timestamp>-<project-id-slug>-phase0/
    scorecard.json
    manifest.json
```

`manifest.json` must include:

- `schema_version: 1`
- `artifact_type: qualitative_coding.phase0_scorecard`
- UTC `generated_at`
- `project_id`, `project_name`, and `phase`
- relative `scorecard_file`
- SHA-256 of the exact `scorecard.json` bytes
- copied `_meta.input_hashes`
- copied claim-discipline note from `_meta.claims`
- `prompt_eval` status object that says statistical evaluation was not run and
  belongs to the future prompt_eval-backed suite
- CLI provenance for supplied files and trace selectors

### Steps

1. Add `--artifact-dir` to `scripts/bench_phase0.py`.
2. Implement `write_phase0_benchmark_artifact(...)` and small helpers for slug,
   UTC timestamp, manifest construction, and byte hashing.
3. Fail loudly if the selected versioned run directory already exists.
4. Forward `--artifact-dir` through `qc_cli.py bench`.
5. Forward `ARTIFACT_DIR=` through `make bench`.
6. Add `benchmark_results/` to `.gitignore` because generated benchmark
   packages can contain sensitive project metadata and are runtime artifacts.
7. Update docs to say Phase 0 can now write a versioned artifact package, while
   full `prompt_eval` statistics and public SOTA evidence remain future work.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_writes_versioned_artifact_package` | `--artifact-dir` creates one run directory with `scorecard.json` and `manifest.json`; manifest hash matches scorecard bytes. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_artifact_manifest_records_external_inputs` | Manifest copies input hashes and CLI provenance for supplied benchmark files. |
| `tests/test_qc_cli_bench.py` | `test_qc_cli_bench_forwards_artifact_dir` | `qc_cli.py bench --artifact-dir` forwards to the script and writes the package. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0_script.py` | Protect scorecard CLI behavior and file inputs. |
| `tests/test_qc_cli_bench.py` | Protect top-level CLI wrapper behavior. |
| `make docs-check` | Verify doc links, plan status, and AGENTS sync. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] `scripts/bench_phase0.py --artifact-dir <dir>` writes a versioned run
  directory with `scorecard.json` and `manifest.json`.
- [ ] The manifest records schema version, artifact type, generation timestamp,
  project identity, phase, scorecard SHA-256, input hashes, claim-discipline
  note, prompt_eval not-run status, and CLI provenance.
- [ ] The artifact writer fails loudly rather than overwriting an existing run
  directory.
- [ ] `qc_cli.py bench --artifact-dir <dir>` forwards the artifact directory.
- [ ] `make bench ARTIFACT_DIR=<dir>` forwards the artifact directory.
- [ ] Generated `benchmark_results/` artifacts are gitignored.
- [ ] Docs describe this as Phase 0 artifact packaging, not full prompt_eval
  benchmark evidence.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should Phase 0 artifact directories be git-tracked for public benchmark
  releases? - Status: DEFERRED | Why it matters: local generated artifacts may
  include project metadata; for now `benchmark_results/` is ignored, and public
  release packaging should be a separate explicit plan.
- [ ] Should this first package produce a `prompt_eval.PrecomputedOutput`
  bundle? - Status: DEFERRED | Why it matters: full precomputed comparison is a
  later prompt_eval suite concern; this slice should only preserve current
  scorecard evidence.

---

## Notes

Do not add bootstrap intervals, Welch tests, live baselines, or held-out gold
logic here. Those belong to the future `prompt_eval` integration. This plan
creates a durable Phase 0 package only.
