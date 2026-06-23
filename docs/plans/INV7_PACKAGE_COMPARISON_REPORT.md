# Plan #218: INV-7 Package Comparison Report

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** INV-7 result packages are versioned and individually validatable.
Phase 0 can score one supplied package at a time, and committed artifacts record
bounded canary/held-out live runs. There is no deterministic report that compares
multiple INV-7 packages side by side for package metadata, fixture overlap,
attack-success rates, failed fixture IDs, surfaces, or attack classes.

**Target:** Add an agent-drivable comparison surface that accepts two or more
schema_version=1 INV-7 prompt-injection packages and writes a JSON report with
per-package metrics, pairwise fixture-overlap/missing-fixture diagnostics, and
by-surface/by-attack summaries. Expose it through a script, Make target, and
`qc_cli.py` wrapper.

**Why:** The roadmap calls for broader held-out live INV-7 evaluation and
model/provider comparisons before any prompt-injection robustness claim. A
deterministic comparison report is the next infrastructure layer: it lets agents
compare frozen package outputs without manual spreadsheets, while preserving the
current caveat that such reports are measurement/provenance artifacts, not proof
of robustness, model obedience, methodological validity, or SOTA.

---

## References Reviewed

- `qc_clean/core/inv7_package.py` - schema_version=1 INV-7 result package model,
  loader, and validation invariants.
- `qc_clean/core/bench.py:2310` - current Phase 0 INV-7 scorecard metrics and
  grouping semantics.
- `scripts/validate_inv7_prompt_injection_package.py` - existing validator script
  style for machine-readable output and failure behavior.
- `scripts/preflight_inv7_live_package.py` - existing INV-7 script pattern for
  JSON reports and non-robustness cautions.
- `qc_cli.py` - current INV-7 parser and handler surfaces.
- `Makefile` - current INV-7 Make targets and help conventions.
- `tests/test_inv7_prompt_injection_package.py` and
  `tests/test_inv7_live_preflight.py` - existing INV-7 package/preflight tests.
- `docs/PROJECT_THEORY_AND_GOALS.md` and `CLAUDE.md` - roadmap and claim
  discipline for INV-7.
- Memory context:
  `agent-memory recall 'active decisions' --project qualitative_coding` - no
  active in-flight decision blocking this slice.
- Coordination context:
  `python scripts/meta/check_coordination_claims.py --check --project qualitative_coding --scope roadmap-continuation`
  - no active claims.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
local reporting/provenance slice over existing benchmark package contracts.

---

## Capabilities

This plan adds an internal project CLI/script reporting surface only. It does
not create a cross-project callable boundary or shared tool-registry capability.

---

## Files Affected

- `qc_clean/core/inv7_package_comparison.py` (create)
- `scripts/compare_inv7_packages.py` (create)
- `qc_cli.py` (modify)
- `Makefile` (modify)
- `tests/test_inv7_package_comparison.py` (create)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate from `CLAUDE.md`)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/plans/CLAUDE.md` (update)
- `docs/plans/ACTIVE_SPRINT.md` (update)

---

## Plan

### Steps

1. Add a small core comparison module that loads two or more validated INV-7
   packages and computes deterministic summaries.
2. Add a script wrapper that accepts repeated package paths and optional output,
   emits JSON, and fails loudly on invalid/missing inputs.
3. Add Make and `qc_cli.py` surfaces that delegate to the script.
4. Add focused tests for happy path, insufficient package rejection, fixture
   overlap/missing diagnostics, script output, and CLI delegation.
5. Update docs to describe the comparison surface and its limits.
6. Run focused tests, docs checks, diff checks, and the full check gate.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_inv7_package_comparison.py` | `test_compare_inv7_packages_reports_package_metrics_and_overlap` | Two valid packages produce per-package metrics and fixture overlap/missing diagnostics. |
| `tests/test_inv7_package_comparison.py` | `test_compare_inv7_packages_requires_at_least_two_packages` | Core comparison rejects under-specified comparisons loudly. |
| `tests/test_inv7_package_comparison.py` | `test_compare_inv7_packages_script_writes_json` | Script emits/writes a valid machine-readable report. |
| `tests/test_inv7_package_comparison.py` | `test_qc_cli_compare_inv7_packages_delegates_to_script` | `qc_cli.py compare-inv7-packages` exposes the canonical script surface. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_inv7_prompt_injection_package.py` | Existing package validation and scorecard loader behavior must remain unchanged. |
| `tests/test_inv7_live_preflight.py` | Existing INV-7 protocol/result preflight must remain unchanged. |
| `make docs-check` | Plan/docs governance must remain synchronized. |
| `make check` | Full deterministic gate must remain green. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] A core comparison function loads and validates at least two INV-7 packages.
- [ ] The report includes per-package total/passed/failed/pass-rate/attack-rate,
  failed fixture IDs, mode, split, fixture-set metadata, model, and trace ID.
- [ ] The report includes pairwise fixture overlap, only-in-left, only-in-right,
  and changed attack outcome fixture IDs.
- [ ] The report includes by-surface and by-attack-type summaries per package.
- [ ] Script, Make, and `qc_cli.py` surfaces are agent-drivable and fail loudly
  on fewer than two packages.
- [ ] Report caveats explicitly say the comparison is not prompt-injection
  robustness proof, model-obedience proof, methodological-validity evidence, or
  SOTA evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Plan, implementation, and closeout are committed and pushed.

---

## Open Questions

- [x] Should this run additional live models? - Status: RESOLVED. No. This
  slice is deterministic comparison infrastructure over existing packages. New
  live model/provider runs should use this surface later with separately
  registered protocols and budgets.

---

## Notes

The report must not rank models as better/worse beyond observed fixture outcomes.
It can report exact deltas and changed fixture IDs, but any interpretation must
remain bounded to the compared package files.
