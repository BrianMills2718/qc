# Plan #184: Phase 0 Benchmark Artifact Verifier

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 benchmark artifacts
**Blocks:** Agent-drivable verification of local Phase 0 benchmark artifact packages

---

## Gap

**Current:** `make bench ARTIFACT_DIR=...` / `qc_cli.py bench --artifact-dir`
can write versioned Phase 0 artifact directories containing `scorecard.json`,
`timing_d10.json`, and `manifest.json`. The manifest records scorecard and
timing hashes, input hashes, run-configuration hashes, command provenance,
claim discipline, and prompt-eval-not-run caveats. Unlike the D7 comparison
artifact package, there is no standalone verifier that checks a Phase 0
artifact directory or manifest after the fact.

**Target:** Add a deterministic Phase 0 artifact verifier:

- `scripts/verify_phase0_benchmark_artifact.py <artifact-dir-or-manifest.json>`
  emits a structured JSON verification report and exits `0` only when verified.
- The verifier accepts either a run directory or `manifest.json` path.
- It validates the manifest shape and expected artifact type.
- It checks `scorecard.json` bytes against `manifest.scorecard_sha256`.
- It checks `timing_d10.json` bytes against `manifest.timing_sha256`.
- It checks manifest `input_hashes`, `run_configuration_hashes`, and
  `claim_discipline` against `scorecard.json` `_meta`.
- It checks `timing_d10.json.source_file`, artifact type, and copied D10
  sections against `scorecard.json`.
- It checks `prompt_eval.status == "not_run"` and claim-discipline caveats.
- `make verify-phase0-benchmark-artifact ARTIFACT=...` and
  `qc_cli.py verify-phase0-benchmark-artifact ...` delegate to the verifier.

**Why:** Phase 0 artifact packages are increasingly used as durable local
benchmark/provenance records. A verifier makes their integrity agent-drivable
instead of relying on manual inspection.

**Non-target:** This slice does not run benchmarks, create held-out data, call
`prompt_eval`, verify semantic validity, sign artifacts, provide append-only
storage, or license methodological-validity, superiority, parity, timing, or
SOTA claims.

---

## References Reviewed

- `scripts/bench_phase0.py` - Phase 0 artifact writer and manifest schema.
- `tests/test_bench_phase0_script.py` - existing artifact-package tests.
- `scripts/verify_d7_comparison_artifact.py` - verifier/report pattern.
- `tests/test_d7_comparison_artifact_verifier.py` - verifier behavior tests.
- `Makefile` - verifier target style.
- `qc_cli.py` - top-level wrapper and dispatch pattern.
- `docs/EVALUATION_HARNESS.md` - artifact caveats and output semantics.
- Coordination/memory check: no active claim files under
  `~/.claude/coordination/claims`; `agent-memory recall 'active decisions'
  --project qualitative_coding` returned no conflicting in-flight decision.

---

## Research Basis For This Slice

No external research is needed. This is deterministic local integrity checking
for an existing repo artifact format.

---

## Capabilities

Internal Phase 0 artifact verification only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `verify_phase0_benchmark_artifact` | Phase 0 artifact directory or manifest path | structured verification report | qualitative_coding | agents/operators reviewing benchmark artifacts | free |

### Capability Validation

- [ ] Matching artifact package verifies with `status="verified"`.
- [ ] Manifest path input and run-directory input both work.
- [ ] Scorecard hash mismatch is detected.
- [ ] Timing hash mismatch is detected.
- [ ] Manifest/scorecard metadata mismatch is detected.
- [ ] Missing scorecard or timing files are detected.
- [ ] Prompt-eval and claim-discipline caveat violations are detected.

---

## Files Affected

- `scripts/verify_phase0_benchmark_artifact.py`
- `tests/test_phase0_benchmark_artifact_verifier.py`
- `tests/test_qc_cli_bench.py`
- `Makefile`
- `qc_cli.py`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Write failing verifier tests for accepted artifacts, manifest-path input,
   scorecard hash mismatch, timing hash mismatch, metadata mismatch, missing
   files, and `qc_cli.py` forwarding.
2. Add `scripts/verify_phase0_benchmark_artifact.py` with Pydantic manifest
   reader, structured failures, and a JSON report.
3. Add Make and `qc_cli.py` surfaces.
4. Update docs with verifier-only claim caveats.
5. Regenerate `AGENTS.md`.
6. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
7. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_phase0_benchmark_artifact_verifier.py` | `test_verify_phase0_benchmark_artifact_accepts_matching_package` | Matching manifest, scorecard, and timing files verify. |
| `tests/test_phase0_benchmark_artifact_verifier.py` | `test_verify_phase0_benchmark_artifact_accepts_manifest_path` | Verifier accepts `manifest.json` directly. |
| `tests/test_phase0_benchmark_artifact_verifier.py` | `test_verify_phase0_benchmark_artifact_detects_scorecard_hash_mismatch` | Tampered scorecard fails hash check. |
| `tests/test_phase0_benchmark_artifact_verifier.py` | `test_verify_phase0_benchmark_artifact_detects_timing_hash_mismatch` | Tampered timing file fails hash check. |
| `tests/test_phase0_benchmark_artifact_verifier.py` | `test_verify_phase0_benchmark_artifact_detects_metadata_mismatch` | Manifest metadata copied from scorecard is checked. |
| `tests/test_phase0_benchmark_artifact_verifier.py` | `test_verify_phase0_benchmark_artifact_detects_missing_timing` | Missing timing artifact fails clearly. |
| `tests/test_qc_cli_bench.py` | `test_qc_cli_verify_phase0_benchmark_artifact_forwards_path` | `qc_cli.py` delegates artifact path to canonical verifier. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_phase0_benchmark_artifact_verifier.py tests/test_qc_cli_bench.py -q` | Verifier behavior and CLI wrapper. |
| `python -m ruff check scripts/verify_phase0_benchmark_artifact.py tests/test_phase0_benchmark_artifact_verifier.py tests/test_qc_cli_bench.py qc_cli.py` | Focused lint. |
| `make -n verify-phase0-benchmark-artifact ARTIFACT=benchmark_results/run-dir` | Make target forwards to canonical script. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Matching Phase 0 artifact packages verify with `status="verified"` and
  exit `0`.
- [ ] Invalid artifact packages return structured failures and exit non-zero.
- [ ] Run-directory and manifest-path inputs both work.
- [ ] Scorecard and timing file SHA-256 mismatches are detected.
- [ ] Missing scorecard/timing files are detected.
- [ ] Manifest `input_hashes`, `run_configuration_hashes`, and
  `claim_discipline` must match scorecard `_meta`.
- [ ] Timing artifact must identify `scorecard.json` as source and copy D10
  sections from the scorecard.
- [ ] Manifest `prompt_eval.status` must be `not_run`.
- [ ] Claim caveat must state this is not methodological-validity/SOTA evidence.
- [ ] Make and `qc_cli.py` surfaces delegate to the canonical verifier.
- [ ] Docs state this verifier is local integrity/provenance checking only.

> Process criteria:
- [ ] TDD red state observed before implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] Make dry-run passes.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Plan is moved to completed with verification evidence.
- [ ] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Tampered scorecard accepted | Hash not checked against manifest | Compare exact file bytes to `scorecard_sha256`. |
| Tampered timing accepted | Timing hash not checked | Compare exact file bytes to `timing_sha256`. |
| Manifest metadata drifts | Copied `_meta` fields not checked | Compare `input_hashes`, `run_configuration_hashes`, and `claim_discipline` to scorecard `_meta`. |
| Timing file unrelated to scorecard | D10 sections not checked | Verify source file and copied D10 sections. |
| Caveats omitted | Claims look stronger than evidence | Require prompt_eval-not-run and non-evidentiary caveat text. |
