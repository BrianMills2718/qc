# Plan #74: Phase 0 Run Configuration Hashes

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 input hashes; Phase 0 benchmark artifacts
**Blocks:** future prompt/model-hashed public benchmark artifacts

---

## Gap

**Current:** Phase 0 scorecards and artifact manifests include hashes for the
loaded project state, corpus, supplied benchmark files, scorecard, and timing
artifact. They do not separately summarize/hash the persisted run configuration
that controls methodology/model defaults. Prior plans deferred prompt/model
hashes because Phase 0 is deterministic and does not execute live prompts.

**Target:** Add `_meta.run_configuration_hashes` to Phase 0 scorecards and copy
it into artifact manifests. The payload should hash persisted project
configuration (`methodology`, configured `model_name`, and `config.extra`) and
explicitly mark prompt-template hashes as `not_run` / not applicable for Phase 0.

**Why:** This improves artifact provenance without laundering Phase 0 into a
live benchmark. Public prompt/model hashes still belong to the future
`prompt_eval` suite, but local Phase 0 artifacts should at least make the
configured model/methodology snapshot easy to audit.

---

## References Reviewed

- `docs/plans/completed/PHASE0_INPUT_HASHES.md` - deferred prompt-hash question.
- `docs/plans/completed/PHASE0_BENCHMARK_PACKAGE_RUNNER.md` - deferred
  prompt/model-hash question for package manifests.
- `scripts/bench_phase0.py` - scorecard metadata, artifact writer, manifest,
  and input hash functions.
- `tests/test_bench_phase0_script.py` - input-hash and artifact-manifest tests.
- `docs/EVALUATION_HARNESS.md` - artifact provenance and future prompt/model
  hash target.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim-discipline language for Phase 0
  provenance.
- Memory context: `agent-memory recall 'Phase 0 prompt model hashes' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic provenance enhancement.

---

## Capabilities

This plan modifies repo-local scorecard/artifact metadata only; it does not
create a cross-project callable capability.

---

## Files Affected

- `scripts/bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/PHASE0_RUN_CONFIGURATION_HASHES.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a canonical run-configuration payload for the persisted project
   `ProjectConfig`.
2. Add SHA-256 metadata for that payload under
   `_meta.run_configuration_hashes`, including readable `methodology` and
   `model_name` fields.
3. Add an explicit prompt-hashes status of `not_run`, because Phase 0 does not
   execute prompt templates or live model calls.
4. Copy the run-configuration hash block into artifact manifests, computing it
   from `state` as a fallback when direct writer callers provide a minimal card.
5. Update tests and docs without claiming full prompt/model benchmark
   provenance.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_includes_input_hashes_without_external_files` | Scorecards include deterministic run-configuration hash metadata and prompt hash status. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_writes_versioned_artifact_package` | Artifact manifests copy the same run-configuration hash metadata. |
| `tests/test_bench_phase0_script.py` | `test_phase0_artifact_writer_fails_when_run_dir_exists` | Direct artifact writer fallback still records run-configuration hashes from state. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0_script.py` | Protect CLI/artifact metadata behavior. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Phase 0 scorecards include `_meta.run_configuration_hashes`.
- [ ] Run-configuration hash metadata includes the configured methodology,
  model name, SHA-256 of the canonical config payload, and algorithm.
- [ ] Prompt/template hash metadata is explicit `not_run`, not silently absent
  and not falsely populated.
- [ ] Artifact manifests include the run-configuration hash block.
- [ ] Docs preserve the caveat that full prompt/model hashes remain future
  `prompt_eval` work.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [x] Should Phase 0 hash prompt templates now? — Status: RESOLVED | Answer:
  No. Phase 0 is deterministic and does not execute prompt templates; record
  prompt hashes as `not_run` and leave live prompt/model hashes to the future
  `prompt_eval` suite.

---

## Notes

This is provenance, not evidence. It makes local Phase 0 artifacts easier to
audit but does not support public SOTA, parity, or live-model benchmark claims.
