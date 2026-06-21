# Plan #38: Gold-Set Provenance in Scorecards

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Benchmark artifact review; held-out D3/D7 evaluation reporting

---

## Gap

**Current:** Versioned D3 and D7 gold-set packages can be validated and fed into
`make bench`, but the D3/D7 scorecard sections mainly report exact-anchor scores.
Package provenance such as gold-set ID, dataset, split, corpus hash,
prompt-freeze status, contamination check, coder count, and human-human
agreement metadata is not surfaced next to the score.

**Target:** When `ProjectState.config.extra["application_gold"]` or
`ProjectState.config.extra["disconfirmation_gold"]` contains a
`schema_version=1` package, include compact gold-set provenance in the
corresponding D3/D7 scorecard section. Raw-list and simple-object gold inputs
remain supported and continue reporting no package provenance.

**Why:** A public or held-out benchmark artifact must show what gold set was
used and whether its provenance conditions were satisfied. Hiding that metadata
inside the input file makes review harder and weakens artifact auditability.

---

## References Reviewed

- `qc_clean/core/bench.py` - current D3/D7 exact-anchor scorecard sections.
- `qc_clean/core/d3_gold.py` - D3 package contract.
- `qc_clean/core/d7_gold.py` - D7 package contract.
- `scripts/bench_phase0.py` - external gold loader and artifact writer.
- `tests/test_bench_phase0_script.py` - external gold/package regressions.
- `docs/EVALUATION_HARNESS.md` - claim-discipline and artifact status.
- Memory context: `agent-memory recall 'active decisions qualitative_coding evaluation harness D3 D7 bootstrap intervals agreement gold set next roadmap' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional external research. This is deterministic provenance surfacing over
already-validated package metadata.

---

## Capabilities

Internal project capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `phase0_scorecard(state)` gold provenance | `ProjectState.config.extra` D3/D7 package dicts | compact JSON provenance object | qualitative_coding | bench CLI, artifact packages, reviewers | free |

### Capability Validation

- [ ] Versioned D3 packages add `gold_provenance` to
  `application_validity_d3`.
- [ ] Versioned D7 packages add `gold_provenance` to `disconfirmation_d7`.
- [ ] Raw/list gold inputs still score without package provenance.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `tests/test_bench_phase0.py` (modify if useful for direct scorecard coverage)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add helper(s) in `qc_clean/core/bench.py` to extract compact provenance from
   schema_version=1 D3/D7 package dictionaries.
2. Add provenance to scored D3/D7 sections only when package metadata is present.
3. Add tests for D3 package provenance, D7 package provenance, and raw-input
   behavior.
4. Update docs conservatively: benchmark artifacts can now report package
   provenance; no held-out package has been populated or scored.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_d3_from_versioned_gold_package` | D3 package score includes provenance metadata. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_d7_from_versioned_gold_package` | D7 package score includes provenance metadata. |
| `tests/test_bench_phase0.py` | direct raw gold test | Raw/simple D3 or D7 gold does not invent package provenance. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0_script.py` | External file loading/artifact behavior remains stable. |
| `tests/test_d3_gold_set.py` / `tests/test_d7_gold_set.py` | Package validation behavior remains stable. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] D3 scorecard sections fed by schema_version=1 packages include compact
  gold provenance.
- [ ] D7 scorecard sections fed by schema_version=1 packages include compact
  gold provenance.
- [ ] Raw gold inputs remain accepted and do not claim package provenance.
- [ ] Docs explain this as artifact provenance only, not validity evidence.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should benchmark manifest duplicate per-section gold provenance? — Status:
  DEFERRED | Why it matters: the scorecard already lives inside the artifact
  package, and manifest schema changes should be a separate artifact-versioning
  decision.

---

## Notes

This plan surfaces provenance for review. It does not create a gold set, run a
held-out benchmark, compute human-human agreement, or license D3/D7 validity
claims.
