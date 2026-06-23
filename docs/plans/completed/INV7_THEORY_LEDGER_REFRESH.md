# Plan #219: INV-7 Theory Ledger Refresh

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** `docs/PROJECT_THEORY_AND_GOALS.md` is the canonical strategic
ledger, but its INV-7 status language is stale after the recent held-out live v1
artifact and package-comparison surface. In particular, §17 still says no
broader held-out live adversarial benchmark result exists, and §13.1/§18 omit
the deterministic package-comparison report surface.

**Target:** Refresh the INV-7 strategic ledger so it accurately states:

- committed built-in canaries, external held-out smoke, and the 10-fixture
  external held-out live v1 artifact exist;
- `make compare-inv7-packages` / `qc_cli.py compare-inv7-packages` can compare
  already-produced INV-7 result packages;
- these artifacts and comparison reports remain bounded measurement/provenance
  outputs and do not license robustness, model-obedience, methodological-
  validity, model/provider superiority, or SOTA claims;
- remaining INV-7 work is larger/independently curated suites and
  model/provider comparisons before any robustness claim.

**Why:** Claim discipline depends on the strategic ledger being both current
and conservative. Stale status text causes two opposite failures: undercounting
real evidence surfaces and overclaiming from artifacts whose caveats are not
visible where agents look first.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:507` - INV-7 invariant status paragraph.
- `docs/PROJECT_THEORY_AND_GOALS.md:566` - short limitations list with stale
  "no broader held-out live adversarial benchmark result" phrasing.
- `docs/PROJECT_THEORY_AND_GOALS.md:646` - roadmap INV-7 item missing the
  comparison surface.
- `CLAUDE.md` - operational INV-7 command/capability summary updated by Plan
  #218.
- `docs/EVALUATION_HARNESS.md` - evaluation harness INV-7 surface summary
  updated by Plan #218.
- `docs/plans/completed/INV7_HELDOUT_LIVE_BENCHMARK_V1.md` - committed
  10-fixture held-out live artifact evidence and caveats.
- `docs/plans/completed/INV7_PACKAGE_COMPARISON_REPORT.md` - package-comparison
  surface evidence and caveats.
- Memory context:
  `agent-memory recall 'active decisions' --project qualitative_coding` - no
  active in-flight decision blocking this slice.
- Coordination context:
  `python scripts/meta/check_coordination_claims.py --check --project qualitative_coding --scope roadmap-continuation`
  - no active claims.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
strategic-ledger consistency slice over already committed artifacts.

---

## Capabilities

This is documentation/governance ledger work only. It does not create or modify
callable capabilities.

---

## Files Affected

- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (update)
- `docs/plans/ACTIVE_SPRINT.md` (update)

---

## Plan

### Steps

1. Update the INV-7 invariant/status paragraph to include external fixture
   manifests, the held-out live v1 artifact, and package comparison reports.
2. Replace stale §17 limitation wording with current but conservative phrasing.
3. Update the roadmap INV-7 item with the comparison surface and remaining work.
4. Run doc/plan consistency checks and full deterministic gates.

---

## Required Tests

### New Tests (TDD)

This is a doc-only ledger refresh; no new code tests are required.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `make docs-check` | Validates links, doc coupling, plan status, and AGENTS sync. |
| `git diff --check` | Ensures no whitespace errors. |
| `make check` | Ensures doc changes did not break deterministic project gates. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `docs/PROJECT_THEORY_AND_GOALS.md` no longer says no broader held-out
  live adversarial benchmark result exists.
- [x] INV-7 status names the committed 10-fixture external held-out live v1
  artifact and package-comparison report surface.
- [x] Updated text keeps caveats explicit: measurement/provenance only, not
  robustness, model obedience, methodological validity, superiority, or SOTA.
- [x] Remaining work still includes larger independently curated suites and
  model/provider comparisons before robustness claims.

> Process criteria:
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Plan, implementation, and closeout are committed and pushed.

---

## Outcome

Completed in implementation commit `458fab5f`. The canonical theory ledger now:

- records version `3.3 — 2026-06-23`;
- states that external held-out live fixture manifests can be run under
  protocol/preflight guards;
- states that committed held-out live artifacts exist, including the 10-fixture
  held-out live v1 package;
- states that INV-7 packages can be compared deterministically;
- removes stale wording that said no broader held-out live adversarial result
  exists;
- keeps the remaining-work bar at larger independently curated suites and
  model/provider comparisons before any robustness claim.

This was documentation/governance ledger work only. It added no new benchmark
evidence and did not change runtime behavior.

---

## Verification

- `rg -n "no broader|broader held-out|beyond the built-in canary|larger independently curated|10-fixture held-out|compare-inv7|package-comparison" docs/PROJECT_THEORY_AND_GOALS.md`
  - No stale "no broader held-out" claim remains; current status names the
    10-fixture held-out live v1 artifact and package-comparison surface.
- `make docs-check`
  - Markdown links, doc coupling, plan sync, and AGENTS sync passed.
- `git diff --check`
  - Passed.
- `make check`
  - 1306 passed, 1 skipped, 8 deselected; Ruff passed; docs-check passed; type
    check not yet configured.

---

## Open Questions

- [x] Should this plan add new benchmark evidence? - Status: RESOLVED. No.
  This slice only aligns the strategic ledger with evidence already committed.

---

## Notes

Do not weaken the claim-discipline table or imply that the 10-fixture v1 run is
an independently curated robustness benchmark. It is broader than the built-in
canary, but still bounded.
