# Plan #70: D10 Timing Artifact

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** D10 wall-clock runtime; Phase 0 benchmark artifacts
**Blocks:** public benchmark timing package review

---

## Gap

**Current:** Phase 0 benchmark packages contain `scorecard.json` and
`manifest.json`. D10 timing data is inside the scorecard as `cost_latency_d10`
and `wall_clock_d10`, but there is no dedicated timing artifact or manifest hash
for timing review.

**Target:** When `--artifact-dir` is supplied, the package also writes
`timing_d10.json`, containing the D10 cost/latency and wall-clock sections plus
an explicit caveat. `manifest.json` records `timing_file` and
`timing_sha256`.

**Why:** The roadmap still calls out versioned benchmark timing artifacts as
missing. A dedicated D10 timing file makes timing evidence reviewable without
claiming public benchmark performance, baseline superiority, or SOTA.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D10 status and remaining timing-artifact work.
- `docs/PROJECT_THEORY_AND_GOALS.md` - D10 caveats and roadmap.
- `docs/plans/completed/D10_WALL_CLOCK_RUNTIME.md` - prior D10 timing slice.
- `docs/plans/completed/PHASE0_BENCHMARK_ARTIFACTS.md` - current package
  contract and artifact boundaries.
- `scripts/bench_phase0.py` - artifact writer and manifest builder.
- `tests/test_bench_phase0_script.py` - artifact package and D10 script tests.
- Memory context: unavailable. Prior repeated
  `agent-memory recall ... --project qualitative_coding` calls in this sprint
  failed with OpenRouter 402/403 provider errors; circuit breaker is active.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a repo-local artifact
packaging extension around already computed D10 scorecard sections.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D10 timing artifact | Phase 0 scorecard with `cost_latency_d10` and `wall_clock_d10` | `timing_d10.json` plus manifest hash | qualitative_coding | artifact reviewers, agents, CI | free |

### Capability Validation

- [x] D10 timing artifact has a stable schema/version/caveat.
- [x] Manifest records the timing file and hash.
- [x] No new cross-project callable boundary is introduced.

---

## Files Affected

- `scripts/bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/D10_TIMING_ARTIFACT.md` (create, then move to completed at closeout)

---

## Plan

### Steps

1. Add a `phase0_timing_artifact(...)` helper that extracts D10 scorecard
   sections into a dedicated artifact payload.
2. Have `write_phase0_benchmark_artifact(...)` write `timing_d10.json`.
3. Add `timing_file` and `timing_sha256` to the manifest.
4. Update artifact tests to assert file content and manifest hash.
5. Update docs without claiming public benchmark timing evidence.
6. Run focused artifact tests, plan sync, docs checks, and full `make check`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_writes_versioned_artifact_package` | Artifact package includes `timing_d10.json` with manifest hash. |
| `tests/test_bench_phase0_script.py` | `test_phase0_artifact_writer_fails_when_run_dir_exists` | Direct writer path still works when timing sections are absent. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0_script.py -k "artifact or d10" -q` | Focused artifact and D10 behavior. |
| `python scripts/sync_plan_status.py --check` | Plan registry consistency. |
| `python scripts/check_markdown_links.py` | Docs link integrity. |
| `make check` | Full deterministic project gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `--artifact-dir` packages include `timing_d10.json`.
- [x] `timing_d10.json` includes `cost_latency_d10`, `wall_clock_d10`,
  `artifact_type`, `schema_version`, and a claim-discipline caveat.
- [x] `manifest.json` records `timing_file` and `timing_sha256`.
- [x] The direct artifact writer remains fail-loud on existing run directory.
- [x] Docs preserve the claim boundary: this is timing artifact packaging, not
  public benchmark or baseline evidence.

> Process criteria:
- [x] Focused tests pass.
- [x] Plan sync passes.
- [x] Markdown link check passes.
- [x] Full `make check` passes, or any non-codebase failure is recorded.
- [ ] Verified implementation is committed and pushed.

---

## Open Questions

- [ ] Should future public timing artifacts include hardware/runtime environment
  metadata? - Status: DEFERRED | Why it matters: public benchmark timing needs
  machine and environment context, but this slice only packages currently
  available D10 scorecard data.

---

## Notes

- This is an additive package artifact; `scorecard.json` remains canonical.
- Missing D10 sections should be represented explicitly as `not_available`
  rather than inferred or estimated.
