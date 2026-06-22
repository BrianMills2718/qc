# Plan #71: D10 Runtime Environment Metadata

**Outcome:** Complete. `timing_d10.json` now includes a non-sensitive
`runtime_environment` block with Python implementation/version, OS
system/release, machine architecture, and logical CPU count. Tests assert the
required metadata and that sensitive top-level keys such as hostnames,
usernames, paths, environment variables, and serial identifiers are absent.
Verified with focused artifact/D10 tests, docs checks, and full `make check` on
2026-06-21 (`776 passed, 1 skipped, 8 deselected`; Ruff/docs checks passed;
type check remains not configured).

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** D10 timing artifact
**Blocks:** public benchmark timing package review

---

## Gap

**Current:** `timing_d10.json` packages local D10 cost/latency and wall-clock
sections, but it does not record the runtime environment. Docs correctly say
public benchmark timing still requires environment context.

**Target:** Add a non-sensitive `runtime_environment` block to
`timing_d10.json` with Python implementation/version, OS family/release,
machine architecture, and CPU count. Do not include hostnames, usernames,
absolute paths, environment variables, or hardware serial identifiers.

**Why:** Runtime timing is not interpretable without machine/runtime context.
This still does not create public benchmark evidence, but it makes local timing
artifacts less ambiguous and prepares the package shape for future benchmark
review.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D10 caveat says public timing evidence needs
  environment metadata.
- `docs/PROJECT_THEORY_AND_GOALS.md` - roadmap still requires public benchmark
  timing evidence with environment/baseline context.
- `docs/plans/completed/D10_TIMING_ARTIFACT.md` - timing artifact scope and
  deferred environment metadata question.
- `scripts/bench_phase0.py` - `phase0_timing_artifact` implementation.
- `tests/test_bench_phase0_script.py` - artifact package tests.
- Memory context: unavailable. Prior repeated
  `agent-memory recall ... --project qualitative_coding` calls in this sprint
  failed with OpenRouter 402/403 provider errors; circuit breaker is active.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a repo-local metadata
addition using Python standard-library runtime information.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D10 runtime environment metadata | local runtime | `timing_d10.json.runtime_environment` | qualitative_coding | artifact reviewers, agents, CI | free |

### Capability Validation

- [x] Runtime metadata excludes hostnames, usernames, absolute paths, env vars,
  and serial identifiers.
- [x] Artifact tests assert required metadata keys exist.
- [x] No new cross-project callable boundary is introduced.

---

## Files Affected

- `scripts/bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/D10_RUNTIME_ENVIRONMENT_METADATA.md` (create, then move to completed at closeout)

---

## Plan

### Steps

1. Add a `_runtime_environment_metadata()` helper in `scripts/bench_phase0.py`.
2. Add `runtime_environment` to `phase0_timing_artifact(...)`.
3. Test required keys and explicitly assert sensitive keys are absent.
4. Update docs to say local D10 timing artifacts include runtime environment
   metadata while public benchmark evidence still requires frozen datasets and
   comparator/baseline runs.
5. Run focused artifact tests, plan sync, docs checks, and full `make check`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_writes_versioned_artifact_package` | `timing_d10.json` includes runtime environment metadata and excludes sensitive keys. |

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
- [x] `timing_d10.json` includes `runtime_environment`.
- [x] Runtime metadata includes Python implementation/version, OS
  family/release, machine architecture, and CPU count.
- [x] Runtime metadata excludes hostnames, usernames, absolute paths,
  environment variables, and serial identifiers.
- [x] Manifest timing hash still covers the updated timing artifact.
- [x] Docs preserve the claim boundary: this is local runtime context, not
  public benchmark timing evidence.

> Process criteria:
- [x] Focused tests pass.
- [x] Plan sync passes.
- [x] Markdown link check passes.
- [x] Full `make check` passes, or any non-codebase failure is recorded.
- [x] Verified implementation is committed and pushed.

---

## Open Questions

- [ ] Should future public timing artifacts require benchmark harness container
  image digests and CPU governor/power-mode metadata? - Status: DEFERRED | Why
  it matters: public timing evidence needs stronger reproducibility controls
  than local runtime metadata.

---

## Notes

- Do not record `platform.node()`, usernames, home paths, or full environment.
- This metadata should be review context only; it must not affect scoring.
