# Plan #210: INV-7 External Held-Out Smoke Artifact

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #209
**Blocks:** broader held-out/adversarial INV-7 benchmark execution

---

## Outcome

Committed a protocol-registered external INV-7 held-out smoke artifact at
`docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/`:

- `manifest.json` - external schema_version=1 live fixture manifest.
- `protocol.json` - held-out protocol metadata with exact prompt hashes.
- `result.json` - live `gpt-5-mini` result package produced through
  `FIXTURES=manifest.json`.
- `preflight.json` - protocol/result preflight report with `status="pass"`.
- `scorecard.json` - Phase 0 scorecard with
  `_meta.preflight_reports.inv7_live.status="pass"`.
- `README.md` - command replay instructions, result summary, and claim caveats.
- `projects/inv7_external_heldout_smoke_project.json` - synthetic project shell
  used only for scorecard reproducibility.

The live run produced 3 fixture outcomes, all passing:
`attack_success_rate=0.0`; the Wilson 95% upper bound is approximately
`0.5615` because the denominator is only 3. D10 cost remains `not_available`
because no matching `llm_calls` rows were found for the exact trace selector;
no cost was estimated from runner fallback text.

Implementation commit: `69a32e00`
(`[Plan: INV7_HELDOUT_SMOKE] Add external held-out smoke artifact`).

Verification:

- `make validate-inv7-live-protocol PROTOCOL=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/protocol.json`
  -> valid protocol, 3 fixtures.
- `make run-inv7-live-fixtures OUTPUT=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/result.json MODEL=gpt-5-mini TRACE_ID=qualitative_coding/inv7-external-heldout-smoke-2026-06-23 MAX_BUDGET=0.75 FIXTURES=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/manifest.json`
  -> 3 passed, 0 failed.
- `make validate-inv7-package PACKAGE=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/result.json`
  -> valid package, 3 passed, 0 failed.
- `make inv7-live-preflight PROTOCOL=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/protocol.json PACKAGE=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/result.json`
  -> `status="pass"`.
- `python scripts/bench_phase0.py inv7_external_heldout_smoke_project --projects-dir docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/projects --prompt-injection-file docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/result.json --inv7-live-protocol-file docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/protocol.json --trace-id qualitative_coding/inv7-external-heldout-smoke-2026-06-23 --output docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/scorecard.json`
  -> scorecard written with `total_fixtures=3`, `passed=3`, `failed=0`, and
  INV-7 preflight status `pass`.
- `python -m pytest tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py tests/test_inv7_live_preflight.py tests/test_bench_phase0_script.py -k "inv7 or prompt_injection" -q`
  -> 35 passed, 42 deselected.
- `make docs-check` -> passed.
- `git diff --check` -> passed.
- `make check` -> 1293 passed, 1 skipped, 8 deselected; Ruff and docs gates
  passed.

This is a small external held-out smoke artifact, not a full held-out
adversarial benchmark. It is not prompt-injection robustness evidence,
model-obedience proof, methodological-validity evidence, or a SOTA claim.

---

## Gap

**Current:** Plan #209 made external schema_version=1 INV-7 live fixture
manifests executable through script, Make, and `qc_cli.py`. The repo still has
no committed artifact demonstrating a protocol-registered external manifest
run beyond the built-in canary fixture set.

**Target:** Commit a small protocol-registered external held-out INV-7 smoke
artifact at `docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/`:

- `manifest.json` - external live fixture manifest with `split="held_out"`.
- `protocol.json` - pre-run live protocol with exact manifest prompt hashes.
- `result.json` - live model result package produced via `FIXTURES=manifest.json`.
- `preflight.json` - protocol/result preflight report.
- `scorecard.json` - Phase 0 scorecard over the external result package.
- `README.md` - commands, result summary, and claim caveats.
- `projects/inv7_external_heldout_smoke_project.json` - synthetic project shell
  used only to make Phase 0 scoring reproducible.

The live run uses `gpt-5-mini`, trace ID
`qualitative_coding/inv7-external-heldout-smoke-2026-06-23`, and
`max_budget=0.75`.

**Why:** This proves the new manifest-runner workflow end to end on a fixture
set outside the built-in canary definitions. It is still a small smoke
artifact, not a full held-out adversarial benchmark or robustness proof.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §17 and §18 - INV-7 remaining gap and
  claim limits.
- `docs/EVALUATION_HARNESS.md` - INV-7 protocol/package/scorecard workflow and
  non-evidentiary caveats.
- `docs/plans/completed/INV7_HELD_OUT_FIXTURE_MANIFEST_RUNNER.md` - new
  external manifest runner contract and verification.
- `docs/plans/completed/INV7_COMMITTED_LIVE_CANARY_V2.md` - artifact directory
  shape and command sequence.
- `qc_clean/core/inv7_fixtures.py` - manifest fields and held-out invariants.
- `qc_clean/core/inv7_live_protocol.py` and
  `qc_clean/core/inv7_live_preflight.py` - protocol and preflight requirements.
- `scripts/run_inv7_live_fixtures.py`, `scripts/validate_inv7_live_protocol.py`,
  `scripts/preflight_inv7_live_package.py`, and `scripts/bench_phase0.py` -
  commands used to generate and verify the artifact.
- Memory context:
  `agent-memory recall 'active decisions' --project qualitative_coding` - no
  relevant in-flight decision found.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active
  claim files.

---

## Research Basis For This Slice

No additional external research. This is a repo-local smoke artifact over the
newly landed external fixture-manifest runner.

---

## Capabilities

Skipped: this plan uses existing project-local runner/protocol/scorecard
capabilities and does not add or modify callable capabilities.

---

## Files Affected

- `docs/plans/INV7_EXTERNAL_HELDOUT_SMOKE_ARTIFACT.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/` - manifest,
  protocol, result, preflight, scorecard, README, and project shell artifacts.
- Docs after successful artifact run:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/PROJECT_THEORY_AND_GOALS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Write `manifest.json` with a small external held-out fixture set that does
   not reuse built-in fixture IDs or prompts.
2. Compute exact SHA-256 hashes for all manifest prompts.
3. Write `protocol.json` with `split="held_out"`, matching fixture-set
   metadata, model, trace ID, budget, and success/reporting criteria.
4. Validate the protocol before the live run.
5. Run `make run-inv7-live-fixtures` with `FIXTURES=manifest.json`, model,
   trace ID, and budget.
6. Validate the result package.
7. Preflight result against protocol and save `preflight.json`.
8. Score the result through Phase 0 using a repo-local synthetic project shell.
9. Add README/status docs with caveats.
10. Run required focused gates, docs checks, and `make check`.
11. Commit and push the verified artifact increment, then close the plan.

---

## Required Tests

### New Tests (TDD)

No new code tests are planned unless artifact generation exposes a runner bug.
This lane exercises already tested script/Make/CLI surfaces.

### Existing Tests And Gates (Must Pass)

| Command | Why |
|---------|-----|
| `make validate-inv7-live-protocol PROTOCOL=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/protocol.json` | Protocol is valid before live execution. |
| `make run-inv7-live-fixtures OUTPUT=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/result.json MODEL=gpt-5-mini TRACE_ID=qualitative_coding/inv7-external-heldout-smoke-2026-06-23 MAX_BUDGET=0.75 FIXTURES=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/manifest.json` | Produces the external manifest result package. |
| `make validate-inv7-package PACKAGE=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/result.json` | Result package satisfies schema/version contract. |
| `make inv7-live-preflight PROTOCOL=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/protocol.json PACKAGE=docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/result.json` | Protocol/result metadata and prompt hashes match. |
| `python scripts/bench_phase0.py inv7_external_heldout_smoke_project --projects-dir docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/projects --prompt-injection-file docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/result.json --inv7-live-protocol-file docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/protocol.json --trace-id qualitative_coding/inv7-external-heldout-smoke-2026-06-23 --output docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/scorecard.json` | Phase 0 scores the result and records passing INV-7 preflight metadata. |
| `python -m pytest tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py tests/test_inv7_live_preflight.py tests/test_bench_phase0_script.py -k "inv7 or prompt_injection" -q` | Existing INV-7 runner/package/protocol/scorecard behavior remains compatible. |
| `make docs-check` | Plan/docs governance and AGENTS sync remain valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] External `manifest.json` validates through the runner and contains
  non-built-in fixture IDs/prompts.
- [x] Held-out protocol validates before execution.
- [x] Live result package validates and carries manifest metadata/prompt
  hashes.
- [x] Preflight report has `status="pass"`.
- [x] Scorecard includes `prompt_injection_inv7` for the external manifest
  result and `_meta.preflight_reports.inv7_live.status="pass"`.
- [x] README/status docs state this is a small external held-out smoke
  artifact, not prompt-injection robustness evidence, model-obedience proof,
  methodological-validity evidence, or SOTA evidence.

Process criteria:

- [x] Required validation/preflight/score commands pass.
- [x] Focused INV-7 tests pass.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Open Questions

- [x] Should this artifact be described as full held-out robustness evidence?
  Status: RESOLVED. No. It is a small external held-out smoke artifact only.
- [x] If the live model call fails, should work stop?
  Status: RESOLVED. No. After three non-identical attempts or a clear provider
  outage, record the failure and move to the next deterministic roadmap lane.

---

## Notes

The result may spend live-model budget up to `max_budget=0.75`; this cap is
part of the protocol metadata. Do not estimate costs if observability rows are
not found.
