# Plan #65: INV-7 Prompt-Injection Wilson Intervals

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-7 fixture scorecard uncertainty metadata

---

## Outcome

INV-7 prompt-injection fixture scorecards now report Wilson interval metadata
for pass rates and attack-success rates overall and by prompt surface. The
intervals reuse the existing passed/failed and total fixture counts. This
remains local uncertainty metadata for supplied fixture outcomes, not proof of
prompt-injection robustness.

## Verification

- `python -m pytest tests/test_bench_phase0.py -q` - 54 passed
- `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py` - clean
- `python scripts/check_markdown_links.py` - clean
- `python scripts/sync_plan_status.py --check` - clean
- `make check` - 773 passed, 1 skipped, 8 deselected; lint and docs checks clean; type check not configured

## Gap

**Current:** The INV-7 prompt-injection fixture scorecard reports pass/fail
counts, pass rate, attack-success rate, failed fixture IDs, and per-surface
summaries. These rates are point estimates only.

**Target:** Add Wilson intervals for overall and per-surface pass rates and
attack-success rates. Interval counts must reuse the existing passed/failed and
total fixture counts.

**Why:** INV-7 fixture sets are likely sparse, especially live canary sets. Point
rates without uncertainty metadata invite overclaiming prompt-injection
robustness from too few fixtures.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - INV-7 prompt-injection scorecard caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-7 status and prompt-injection claim discipline.
- `qc_clean/core/bench.py` - prompt-injection scorecard and Wilson helper.
- `tests/test_bench_phase0.py` - prompt-injection scorecard coverage.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with OpenRouter 402/403 provider errors; circuit
  breaker applies.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This reuses the existing
Phase 0 Wilson interval convention already used for other binary-rate
scorecards.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| INV-7 fixture rate intervals | prompt-injection fixture outcomes | Wilson intervals for pass and attack-success rates | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [x] Overall INV-7 scorecard includes `pass_rate_ci`.
- [x] Overall INV-7 scorecard includes `attack_success_rate_ci`.
- [x] Per-surface INV-7 summaries include `pass_rate_ci`.
- [x] Per-surface INV-7 summaries include `attack_success_rate_ci`.
- [x] Interval counts match existing passed/failed and total fixture counts.
- [x] Docs preserve the caveat that intervals are local uncertainty metadata, not prompt-injection robustness proof.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add overall `pass_rate_ci` and `attack_success_rate_ci` to `prompt_injection_scorecard`.
2. Add per-surface `pass_rate_ci` and `attack_success_rate_ci` to `_prompt_injection_by_surface`.
3. Update focused INV-7 scorecard tests for overall and per-surface interval metadata.
4. Update evaluation/theory docs and sprint tracker without upgrading INV-7 robustness claims.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | INV-7 prompt-injection scorecard test | Overall and per-surface Wilson interval metadata. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| Existing INV-7 scorecard tests | Existing counts, rates, failed fixture IDs, and fail-loud behavior must not regress. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Overall pass/attack rates have Wilson interval metadata.
- [x] Per-surface pass/attack rates have Wilson interval metadata.
- [x] Existing INV-7 point metrics are unchanged.
- [x] Docs preserve the caveat that this is local metadata only.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should a future committed live INV-7 benchmark use stratified intervals by
  attack type in addition to surface? - Status: DEFERRED | Why it matters:
  public robustness claims need a frozen adversarial protocol; this slice only
  adds local uncertainty metadata for the existing scorecard.
