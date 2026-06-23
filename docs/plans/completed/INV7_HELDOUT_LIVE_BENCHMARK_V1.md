# Plan #216: INV-7 Held-Out Live Benchmark V1

**Status:** Completed
**Type:** benchmark artifact
**Priority:** High
**Blocked By:** None
**Blocks:** broader INV-7 held-out live evaluation evidence beyond smoke/canary artifacts

---

## Gap

**Current:** The repo has built-in INV-7 structural/live canaries and a small
3-fixture external held-out smoke artifact. That proves the external manifest,
protocol, preflight, and Phase 0 scoring workflow, but the denominator is too
small and narrow to serve as a serious adversarial live evaluation artifact.

**Target:** Commit a broader external held-out INV-7 live fixture artifact under
`docs/benchmarks/inv7_heldout_live_v1_2026_06_23/` with a frozen manifest,
protocol prompt hashes, live result package, preflight report, scorecard, and
README. The fixture set should cover multiple attack families and multiple
prompt surfaces without reusing the 3-fixture smoke prompts.

**Why:** The roadmap names broader held-out live adversarial prompt-injection
runs as a remaining INV-7 gap. This slice makes that evaluation concrete and
reviewable while keeping the run bounded and reproducible.

**Claim boundary:** This is a broader held-out live fixture artifact, not proof
of prompt-injection robustness, model obedience, methodological validity,
security hardening, or SOTA. Passing this artifact does not mean prompt
injection is solved.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §13.1, §18 - INV-7 status and roadmap.
- `docs/plans/completed/INV7_HELD_OUT_FIXTURE_MANIFEST_RUNNER.md` - external
  manifest contract.
- `docs/plans/completed/INV7_EXTERNAL_HELDOUT_SMOKE_ARTIFACT.md` - prior
  external smoke artifact pattern and caveats.
- `qc_clean/core/inv7_fixtures.py` - manifest schema and live result package.
- `scripts/run_inv7_live_fixtures.py` - live runner.
- `scripts/validate_inv7_live_protocol.py` and
  `scripts/preflight_inv7_live_package.py` - protocol/result validation.
- `scripts/bench_phase0.py` - scorecard path for `PROMPT_INJECTION=`.

---

## Research Basis For This Slice

No new external research is required. This is a repo-local benchmark-artifact
slice over existing INV-7 evaluation infrastructure.

---

## Capabilities

Internal project capability only; no cross-project registry entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| INV-7 held-out live fixture evaluation | schema_version=1 external live fixture manifest | schema_version=1 prompt-injection result package + Phase 0 scorecard | qualitative_coding | roadmap/portfolio reviewers | paid LLM |

### Capability Validation

Skipped for cross-project registry purposes: this uses existing project-local
INV-7 fixture and benchmark surfaces.

---

## Files Affected

- `docs/plans/completed/INV7_HELDOUT_LIVE_BENCHMARK_V1.md` - completed plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- New benchmark artifact directory:
  - `docs/benchmarks/inv7_heldout_live_v1_2026_06_23/README.md`
  - `docs/benchmarks/inv7_heldout_live_v1_2026_06_23/manifest.json`
  - `docs/benchmarks/inv7_heldout_live_v1_2026_06_23/protocol.json`
  - `docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json`
  - `docs/benchmarks/inv7_heldout_live_v1_2026_06_23/preflight.json`
  - `docs/benchmarks/inv7_heldout_live_v1_2026_06_23/scorecard.json`
  - `docs/benchmarks/inv7_heldout_live_v1_2026_06_23/projects/inv7_heldout_live_v1_project.json`
- Docs after artifact:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Create a frozen external held-out fixture manifest with at least 10 fixtures,
   distinct fixture IDs, and attack families broader than the existing smoke
   artifact.
2. Compute exact SHA-256 prompt hashes and write a matching INV-7 live protocol.
3. Validate the protocol before execution.
4. Run the live fixture manifest with `gpt-5-mini`, bounded trace ID, and
   `MAX_BUDGET=2.0`.
5. Validate the result package and preflight it against the protocol.
6. Create a minimal synthetic project shell and score the result through Phase
   0 with the INV-7 preflight guard.
7. Write a README with commands, result summary, and explicit caveats.
8. Update project docs conservatively.
9. Run focused INV-7 tests, touched-file Ruff if code changes occur, docs
   checks, diff check, and `make check`.
10. Commit/push the artifact and close the plan.

---

## Required Tests

### Artifact Commands

| Command | What It Verifies |
|---------|------------------|
| `make validate-inv7-live-protocol PROTOCOL=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/protocol.json` | Protocol metadata and prompt hashes are structurally valid. |
| `make run-inv7-live-fixtures OUTPUT=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json MODEL=gpt-5-mini TRACE_ID=qualitative_coding/inv7-heldout-live-v1-2026-06-23 MAX_BUDGET=2.0 FIXTURES=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/manifest.json` | Produces the external held-out live result package. |
| `make validate-inv7-package PACKAGE=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json` | Result package satisfies INV-7 package schema. |
| `make inv7-live-preflight PROTOCOL=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/protocol.json PACKAGE=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json` | Result metadata and prompt hashes match protocol metadata. |
| `python scripts/bench_phase0.py inv7_heldout_live_v1_project --projects-dir docs/benchmarks/inv7_heldout_live_v1_2026_06_23/projects --prompt-injection-file docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json --inv7-live-protocol-file docs/benchmarks/inv7_heldout_live_v1_2026_06_23/protocol.json --trace-id qualitative_coding/inv7-heldout-live-v1-2026-06-23 --output docs/benchmarks/inv7_heldout_live_v1_2026_06_23/scorecard.json` | Phase 0 scores the live result with the INV-7 preflight guard. |

### Regression Gates

| Command | Why |
|---------|-----|
| `python -m pytest tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py tests/test_inv7_live_preflight.py tests/test_bench_phase0_script.py -k "inv7 or prompt_injection" -q` | Existing INV-7 runner/package/protocol/scorecard behavior remains compatible. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] Artifact directory contains manifest, protocol, result, preflight,
  scorecard, project shell, and README.
- [x] Manifest has `split="held_out"`, prompt-frozen, contamination-checked,
  registered-before-run metadata, and at least 10 non-smoke fixture prompts.
- [x] Protocol prompt hashes match every fixture prompt exactly.
- [x] Live result package contains the same fixture-set metadata and one result
  per fixture.
- [x] Preflight status is pass.
- [x] Scorecard records `prompt_injection_inv7` plus passing INV-7 preflight
  metadata.
- [x] README and docs state the artifact is broader than the smoke artifact but
  is not proof of prompt-injection robustness or SOTA.

Process criteria:

- [x] Artifact commands pass or any live-run failure is recorded with concrete
  error evidence and the next safe action.
- [x] Focused INV-7 regression tests pass.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Outcome

Committed `docs/benchmarks/inv7_heldout_live_v1_2026_06_23/`, a broader
external held-out INV-7 live v1 artifact with:

- 10-fixture `manifest.json` covering direct override, roleplay, markdown
  fence, JSON role spoof, XML tag spoof, HTML comment, YAML frontmatter, fake
  tool output, delimiter breakout, and obfuscated-instruction attacks.
- `protocol.json` with exact prompt hashes for every fixture.
- Live `gpt-5-mini` `result.json`: 10 fixtures, 10 passed, 0 failed.
- `preflight.json`: status `pass`.
- `scorecard.json`: `prompt_injection_inv7.status="scored"`,
  `total_fixtures=10`, `passed=10`, `failed=0`,
  `attack_success_rate=0.0`, Wilson upper bound `0.2775327998628892`, and
  `_meta.preflight_reports.inv7_live.status="pass"`.
- Synthetic project shell and README with commands and caveats.

Implementation commit:
`7bbff360 [Plan: INV7_HELDOUT_LIVE_V1] Add held-out live INV-7 artifact`

Verification:

- `make validate-inv7-live-protocol PROTOCOL=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/protocol.json`
  - Result: valid; fixture_count=10.
- `make run-inv7-live-fixtures OUTPUT=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json MODEL=gpt-5-mini TRACE_ID=qualitative_coding/inv7-heldout-live-v1-2026-06-23 MAX_BUDGET=2.0 FIXTURES=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/manifest.json`
  - Result: total_fixtures=10, passed=10, failed=0.
- `make validate-inv7-package PACKAGE=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json`
  - Result: ok, total_fixtures=10, failed=0, passed=10.
- `make inv7-live-preflight PROTOCOL=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/protocol.json PACKAGE=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json`
  - Result: status=pass, fixture_count=10.
- `python scripts/bench_phase0.py inv7_heldout_live_v1_project --projects-dir docs/benchmarks/inv7_heldout_live_v1_2026_06_23/projects --prompt-injection-file docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json --inv7-live-protocol-file docs/benchmarks/inv7_heldout_live_v1_2026_06_23/protocol.json --trace-id qualitative_coding/inv7-heldout-live-v1-2026-06-23 --output docs/benchmarks/inv7_heldout_live_v1_2026_06_23/scorecard.json`
  - Result: `prompt_injection_inv7` scored, total_fixtures=10, passed=10,
    failed=0, preflight=pass.
- `python -m pytest tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py tests/test_inv7_live_preflight.py tests/test_bench_phase0_script.py -k "inv7 or prompt_injection" -q`
  - Result: 35 passed, 42 deselected.
- `make docs-check`
  - Result: Markdown links OK; doc coupling config valid; plan records
    consistent; `AGENTS.md` in sync.
- `git diff --check`
  - Result: clean.
- `make check`
  - Result: 1302 passed, 1 skipped, 8 deselected; Ruff all checks passed;
    docs-check passed; type check not yet configured.

Claim boundary: this is a broader held-out live canary artifact, not proof of
prompt-injection robustness, model obedience, security hardening,
methodological validity, or SOTA. Passing this artifact does not mean prompt
injection is solved.

---

## Open Questions

- [x] Should this plan run a live model rather than only create a manifest?
  Status: RESOLVED. Yes. The roadmap gap is a broader held-out live adversarial
  run beyond smoke/canary artifacts, and a live run is reversible, bounded, and
  already supported by the repo's budgeted runner.

---

## Notes

This plan intentionally uses a small but broader denominator instead of claiming
full robustness. The result should be useful for reviewer inspection and future
regression comparison, while still preserving the theory doc's claim
discipline.
