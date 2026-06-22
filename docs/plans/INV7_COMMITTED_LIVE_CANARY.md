# Plan #164: INV-7 Committed Live Canary

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** broader prompt-injection benchmark evidence

---

## Gap

**Current:** INV-7 has deterministic structural fixture packages, a live canary
runner, live protocol validation, result-package validation, and
protocol-to-result preflight. The repo still has no committed/scored live
adversarial canary result.

**Target:** Commit a first protocol-registered live INV-7 canary artifact set:

- `docs/benchmarks/inv7_live_canary_2026_06_22/protocol.json`
- `docs/benchmarks/inv7_live_canary_2026_06_22/result.json`
- `docs/benchmarks/inv7_live_canary_2026_06_22/preflight.json`
- `docs/benchmarks/inv7_live_canary_2026_06_22/scorecard.json`
- `docs/benchmarks/inv7_live_canary_2026_06_22/README.md`

The run uses the built-in INV-7 live fixtures, `split="canary"`, model
`gpt-5-mini`, trace ID `qualitative_coding/inv7-live-canary-2026-06-22`, and
`max_budget=0.25`. The scorecard is Phase 0 local accounting only; it is not
held-out evidence and not proof of prompt-injection robustness.

**Why:** This closes the current "no committed/scored live adversarial
benchmark run" gap for the built-in canary path while preserving claim
discipline. It gives reviewers a concrete artifact package to inspect without
pretending the canary is a full benchmark.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §13, §13.1, §18 - INV-7 status, roadmap,
  and claim-discipline caveats.
- `docs/EVALUATION_HARNESS.md` - INV-7 fixture outcome and Phase 0 scorecard
  design.
- `qc_clean/core/inv7_fixtures.py` - built-in live fixture definitions and
  `run_inv7_live_fixtures_async`.
- `qc_clean/core/inv7_live_protocol.py` - live protocol schema and validation.
- `qc_clean/core/inv7_live_preflight.py` - protocol/result preflight rules.
- `qc_clean/core/inv7_package.py` - result package schema validation.
- `scripts/run_inv7_live_fixtures.py` - live runner CLI.
- `scripts/validate_inv7_live_protocol.py` - protocol validator CLI.
- `scripts/preflight_inv7_live_package.py` - live preflight CLI.
- `scripts/validate_inv7_prompt_injection_package.py` - result-package
  validator CLI.
- `scripts/bench_phase0.py` - `PROMPT_INJECTION=` scorecard input path.
- Memory context:
  `agent-memory recall 'active decisions' --project qualitative_coding`;
  `agent-memory recall 'INV-7 live prompt injection benchmark qualitative_coding next lane' --project qualitative_coding`
  - low-relevance historical findings only, no active conflicting decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this plan creates benchmark/provenance artifacts from existing
project-local commands and does not add or modify callable cross-project
capabilities.

---

## Files Affected

- `docs/plans/INV7_COMMITTED_LIVE_CANARY.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - active sprint checkpoint.
- `docs/benchmarks/inv7_live_canary_2026_06_22/` - committed canary protocol,
  result, preflight, scorecard, and README artifacts.
- `docs/PROJECT_THEORY_AND_GOALS.md` - status wording if the artifact run
  succeeds.
- `docs/EVALUATION_HARNESS.md` - status wording if the artifact run succeeds.
- `docs/portfolio/QUALITATIVE_CODING_EVIDENCE_BUNDLE.md` - evidence-map update
  if the artifact run succeeds.
- `CLAUDE.md` / `AGENTS.md` - operational summary update if the artifact run
  succeeds.

---

## Plan

### Steps

1. Add the active plan and sprint checkpoint.
2. Create a protocol package for the built-in live fixture hashes.
3. Validate the protocol package before running live fixtures.
4. Run `make run-inv7-live-fixtures` with the pre-registered model, trace ID,
   and budget.
5. Validate the result package.
6. Preflight the result against the protocol and save the preflight report.
7. Score the result through Phase 0 with `PROMPT_INJECTION=...` and save the
   scorecard.
8. Add a compact README and update status docs without claiming robustness.
9. Run focused gates, docs gate, and full `make check`.
10. Commit and push the verified artifact increment, then close the plan.

---

## Required Tests

### New Tests (TDD)

No new code tests are required because this lane produces benchmark artifacts
through existing tested commands.

### Existing Tests And Gates (Must Pass)

| Command | Why |
|---------|-----|
| `make validate-inv7-live-protocol PROTOCOL=docs/benchmarks/inv7_live_canary_2026_06_22/protocol.json` | Protocol is valid before the live run |
| `make run-inv7-live-fixtures OUTPUT=docs/benchmarks/inv7_live_canary_2026_06_22/result.json MODEL=gpt-5-mini TRACE_ID=qualitative_coding/inv7-live-canary-2026-06-22 MAX_BUDGET=0.25` | Produces the live canary result package |
| `make validate-inv7-package PACKAGE=docs/benchmarks/inv7_live_canary_2026_06_22/result.json` | Result package satisfies schema/version contract |
| `make inv7-live-preflight PROTOCOL=docs/benchmarks/inv7_live_canary_2026_06_22/protocol.json PACKAGE=docs/benchmarks/inv7_live_canary_2026_06_22/result.json` | Protocol/result metadata and prompt hashes match |
| `python scripts/bench_phase0.py __missing_project_for_inv7_canary__ --prompt-injection-file docs/benchmarks/inv7_live_canary_2026_06_22/result.json --output docs/benchmarks/inv7_live_canary_2026_06_22/scorecard.json` | Phase 0 scores the canary package without needing a saved project |
| `python -m pytest tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py tests/test_inv7_live_preflight.py tests/test_bench_phase0_script.py -k "inv7 or prompt_injection" -q` | Existing INV-7 runner/package/protocol/scorecard behavior remains compatible |
| `make docs-check` | Plan index, links, and AGENTS sync remain valid |
| `make check` | Full deterministic gate remains green |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] A pre-run canary protocol exists with exact built-in fixture prompt hashes.
- [ ] The committed live result package validates.
- [ ] The committed preflight report has `status="pass"`.
- [ ] The committed scorecard includes `prompt_injection_inv7` for the live
  canary package.
- [ ] README/status docs state this is a small canary artifact, not prompt-
  injection robustness evidence, model-obedience proof, held-out evidence, or
  methodological validity evidence.

Process criteria:

- [ ] Required validation/preflight/score commands pass.
- [ ] Focused INV-7 tests pass.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Open Questions

- [ ] None.

---

## Notes

Built-in live fixture prompt hashes for this plan:

- `live-boundary-break-direct-override`:
  `6e6de0cfe72449a0ae7171c634185722c8e20d96407b3a24b7ed190d791403c0`
- `live-synthesis-derived-output-override`:
  `545b183cb5ea63978b6235c5c02579e2184d6c62cb06a3ee42682653284741b3`
- `live-thematic-raw-direct-override`:
  `511a1e388d14137f8f857d4ba0a6dd5286bd119bb23575bdb69f6e86b5aaf5d9`
