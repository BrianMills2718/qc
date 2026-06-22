# Plan #176: D3 Baseline Comparison Preflight

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** D3 baseline comparison protocol validator
**Blocks:** D3 score-time preflight guard for `make bench D3_PROTOCOL=...`

---

## Gap

**Current:** D3 now has versioned gold-set packages, versioned baseline
prediction packages, and a pre-run comparison protocol validator. It still lacks
the deterministic preflight that cross-checks a concrete D3 gold package and
concrete D3 baseline packages against that protocol before scoring.

**Target:** Add D3 comparison preflight:

- New core module `qc_clean/core/d3_comparison_preflight.py`.
- New script `scripts/preflight_d3_comparison.py`.
- New Make target
  `d3-comparison-preflight PROTOCOL=protocol.json GOLD=d3_gold.json PREDICTIONS="a.json b.json"`.
- Preflight validates protocol, gold, and baseline packages using existing
  validators.
- Preflight checks gold metadata against protocol: gold set, dataset, split,
  corpus hash, project-state hash, prompt freeze, and contamination check.
- Preflight checks expected baseline names, duplicate/unexpected/missing
  baselines, package project/baseline mode/model metadata, expected application
  counts per baseline, and optional prediction-file SHA-256 locks.
- Output is a schema_version=1 pass/fail JSON report with explicit error rows.

**Non-target:** This slice does not add `make bench D3_PROTOCOL=...`,
`qc_cli.py bench` forwarding, artifact metadata, or metric-criteria evaluation
against scorecard output.

**Why:** D3 held-out baseline comparisons should not be scored against a
protocol that only validates in isolation. This slice creates the package-level
cross-check needed before a later score-time guard can safely block scoring on
protocol drift.

---

## References Reviewed

- `qc_clean/core/d3_comparison_protocol.py` - D3 comparison protocol contract.
- `qc_clean/core/d3_gold.py` - D3 gold-set package contract.
- `qc_clean/core/d3_baseline_package.py` - D3 baseline prediction package
  contract.
- `qc_clean/core/d7_comparison_preflight.py` and
  `scripts/preflight_d7_comparison.py` - analogous D7 preflight pattern.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - D3
  comparison protocol exists but preflight/score-time guards remain future work.

---

## Research Basis For This Slice

No new external research. This is deterministic package/protocol cross-checking
based on existing local package contracts.

---

## Capabilities

Internal preflight capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `preflight_d3_comparison` | D3 comparison protocol + D3 gold package + D3 baseline package files | schema_version=1 pass/fail preflight report | qualitative_coding | agents/operators preparing D3 comparisons | free |

### Capability Validation

- [ ] Matching protocol/gold/baseline packages produce a passing report.
- [ ] Gold metadata mismatches produce explicit errors.
- [ ] Missing, unexpected, or duplicate baseline names produce explicit errors.
- [ ] Baseline mode/model/application-count mismatches produce explicit errors.
- [ ] Optional prediction-file SHA-256 locks are enforced.
- [ ] Script emits machine-readable JSON and exits 0/1.

---

## Files Affected

- `qc_clean/core/d3_comparison_preflight.py` (new)
- `scripts/preflight_d3_comparison.py` (new)
- `tests/test_d3_comparison_preflight.py` (new)
- `Makefile`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Write failing tests for matching preflight, gold mismatch, baseline mismatch,
   hash mismatch, and script JSON output.
2. Implement D3 preflight core with Pydantic report/error models.
3. Add the canonical preflight script.
4. Add the Make target.
5. Update docs with preflight availability and score-time guard deferral.
6. Run focused tests, focused Ruff, Make dry-run, docs checks, and full
   `make check`.
7. Commit/push implementation, then close this plan.

---

## Required Tests

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d3_comparison_preflight.py tests/test_d3_comparison_protocol.py tests/test_d3_baseline_package.py -q` | New preflight plus adjacent D3 package/protocol behavior. |
| `python -m ruff check qc_clean/core/d3_comparison_preflight.py scripts/preflight_d3_comparison.py tests/test_d3_comparison_preflight.py` | Focused lint. |
| `make -n d3-comparison-preflight PROTOCOL=protocol.json GOLD=d3_gold.json PREDICTIONS="a.json b.json"` | Make target forwards to canonical script. |
| `make docs-check` | Plan/docs governance. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `preflight_d3_comparison_payloads()` returns pass/fail reports.
- [ ] `scripts/preflight_d3_comparison.py` accepts protocol, gold, and one or
  more prediction files and emits JSON.
- [ ] `make d3-comparison-preflight ...` is available.
- [ ] Preflight validates protocol/gold/baseline package shapes before
  cross-checking metadata.
- [ ] Preflight enforces expected baseline names and optional file hashes.
- [ ] Docs state this is protocol/provenance only and not score-time
  enforcement, held-out D3 evidence, expert parity, superiority, or SOTA.

> Process criteria:
- [ ] TDD red state observed before implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] Make dry-run confirms target wiring.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Plan is moved to completed with verification evidence.
- [ ] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Preflight accepts legacy/raw baseline inputs | It bypassed versioned package validation | Require schema_version=1 D3 baseline packages for preflight. |
| File hash locks cannot be matched to baseline names | A package can contain multiple baselines | Map every baseline row in a supplied package to that file's SHA-256. |
| Application count check uses package total only | Package metadata total can cover multiple baselines | Compare expected `application_count` to the concrete baseline row length. |
| Score-time guard accidentally added | Scope creep into `bench_phase0.py` | Keep `D3_PROTOCOL` / score-time enforcement for a separate plan. |
