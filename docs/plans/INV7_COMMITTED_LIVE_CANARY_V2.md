# Plan #169: INV-7 Committed Live Canary V2

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** #168
**Blocks:** broader held-out INV-7 adversarial benchmark evidence

---

## Gap

**Current:** `docs/benchmarks/inv7_live_canary_2026_06_22/` records a committed
live canary artifact for built-in fixture-set version `1` with three fixtures.
Plan #168 expanded the built-in structural/live fixture sets to version `2`,
adding custom prompt override surfaces. The committed artifact no longer covers
the current built-in live fixture set.

**Target:** Commit a second protocol-registered live INV-7 canary artifact set
for built-in fixture-set version `2`:

- `docs/benchmarks/inv7_live_canary_v2_2026_06_22/protocol.json`
- `docs/benchmarks/inv7_live_canary_v2_2026_06_22/result.json`
- `docs/benchmarks/inv7_live_canary_v2_2026_06_22/preflight.json`
- `docs/benchmarks/inv7_live_canary_v2_2026_06_22/scorecard.json`
- `docs/benchmarks/inv7_live_canary_v2_2026_06_22/README.md`
- `docs/benchmarks/inv7_live_canary_v2_2026_06_22/projects/inv7_canary_project_v2.json`

The run uses built-in live fixtures, `split="canary"`, model `gpt-5-mini`,
trace ID `qualitative_coding/inv7-live-canary-v2-2026-06-22`, and
`max_budget=0.50`.

**Why:** The fixture suite now includes custom prompt override canaries; the
committed live artifact should cover the current canary set. This remains a
small canary artifact only, not held-out evidence or prompt-injection
robustness proof.

---

## References Reviewed

- `docs/plans/completed/INV7_COMMITTED_LIVE_CANARY.md` - prior canary artifact
  lane and artifact shape.
- `docs/plans/completed/INV7_CUSTOM_PROMPT_OVERRIDE_FIXTURES.md` - fixture-set
  version `2` and new custom override fixture IDs.
- `docs/benchmarks/inv7_live_canary_2026_06_22/` - prior artifact package.
- `qc_clean/core/inv7_fixtures.py` - current built-in live fixtures and prompt
  hashes.
- `qc_clean/core/inv7_live_protocol.py` - protocol schema and claim caveat.
- `qc_clean/core/inv7_live_preflight.py` - protocol/result preflight rules.
- `qc_clean/core/inv7_package.py` - result package validator.
- `scripts/run_inv7_live_fixtures.py`, `scripts/validate_inv7_live_protocol.py`,
  `scripts/preflight_inv7_live_package.py`, `scripts/bench_phase0.py` - command
  surfaces used for artifact generation.
- Memory context:
  `agent-memory recall 'qualitative_coding next deterministic roadmap lane INV-7 INV-2 D7 benchmark live baseline' --project qualitative_coding`
  - low-relevance historical findings only, no active conflicting decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active
  claim files.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this plan produces benchmark/provenance artifacts from existing
project-local commands and does not add or modify callable cross-project
capabilities.

---

## Files Affected

- `docs/plans/INV7_COMMITTED_LIVE_CANARY_V2.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - active sprint checkpoint.
- `docs/benchmarks/inv7_live_canary_v2_2026_06_22/` - committed canary
  protocol, result, preflight, scorecard, README, and synthetic project shell.
- Docs after implementation if the artifact run succeeds:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/PROJECT_THEORY_AND_GOALS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Generate exact prompt hashes for `default_inv7_live_fixtures()` after Plan
   #168.
2. Write `protocol.json` for fixture-set version `2`, model `gpt-5-mini`, trace
   ID `qualitative_coding/inv7-live-canary-v2-2026-06-22`, and
   `max_budget=0.50`.
3. Validate the protocol before the live run.
4. Run `make run-inv7-live-fixtures` with the protocol's model, trace ID, and
   budget.
5. Validate the result package.
6. Preflight the result against the protocol and save the preflight report.
7. Score the result with Phase 0 using a repo-local synthetic project shell and
   save `scorecard.json`.
8. Add a README with commands, result summary, and claim caveats.
9. Run focused INV-7 artifact gates, docs gate, and full `make check`.
10. Commit and push the verified artifact increment, then close the plan.

---

## Required Tests

### New Tests (TDD)

No new code tests are required. This lane produces benchmark artifacts through
existing tested commands.

### Existing Tests And Gates (Must Pass)

| Command | Why |
|---------|-----|
| `make validate-inv7-live-protocol PROTOCOL=docs/benchmarks/inv7_live_canary_v2_2026_06_22/protocol.json` | Protocol is valid before the live run. |
| `make run-inv7-live-fixtures OUTPUT=docs/benchmarks/inv7_live_canary_v2_2026_06_22/result.json MODEL=gpt-5-mini TRACE_ID=qualitative_coding/inv7-live-canary-v2-2026-06-22 MAX_BUDGET=0.50` | Produces the v2 live canary result package. |
| `make validate-inv7-package PACKAGE=docs/benchmarks/inv7_live_canary_v2_2026_06_22/result.json` | Result package satisfies schema/version contract. |
| `make inv7-live-preflight PROTOCOL=docs/benchmarks/inv7_live_canary_v2_2026_06_22/protocol.json PACKAGE=docs/benchmarks/inv7_live_canary_v2_2026_06_22/result.json` | Protocol/result metadata and prompt hashes match. |
| `python scripts/bench_phase0.py inv7_canary_project_v2 --projects-dir docs/benchmarks/inv7_live_canary_v2_2026_06_22/projects --prompt-injection-file docs/benchmarks/inv7_live_canary_v2_2026_06_22/result.json --trace-id qualitative_coding/inv7-live-canary-v2-2026-06-22 --output docs/benchmarks/inv7_live_canary_v2_2026_06_22/scorecard.json` | Phase 0 scores the v2 canary package against a repo-local synthetic project shell. |
| `python -m pytest tests/test_inv7_fixture_runner.py tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py tests/test_inv7_live_preflight.py tests/test_bench_phase0_script.py -k "inv7 or prompt_injection or projects_dir" -q` | Existing INV-7 runner/package/protocol/scorecard behavior remains compatible. |
| `make docs-check` | Plan index, links, and AGENTS sync remain valid. |
| `make check` | Full deterministic gate remains green. |

---

## Acceptance Criteria

- [ ] A v2 pre-run canary protocol exists with exact built-in fixture prompt
  hashes for fixture-set version `2`.
- [ ] The committed live result package validates and includes the custom
  override live fixtures.
- [ ] The committed preflight report has `status="pass"`.
- [ ] The committed scorecard includes `prompt_injection_inv7` for the v2 live
  canary package.
- [ ] README/status docs state this is a small canary artifact, not
  prompt-injection robustness evidence, model-obedience proof, held-out
  evidence, methodological-validity evidence, or SOTA.
- [ ] Required validation/preflight/score/test/docs/full gates pass.
- [ ] Verified increment is committed and pushed.

---

## Open Questions

- [x] Should a failure to run the live model block all further roadmap work?
  Status: RESOLVED. No. If the live runner cannot execute because of provider,
  key, transient, or budget errors after three non-identical attempts, record
  the failure in this plan and move to the next highest-value deterministic
  lane per the sprint circuit breaker.

---

## Notes

This lane may spend live-model budget up to `max_budget=0.50`. The budget cap is
part of the protocol and result metadata.
