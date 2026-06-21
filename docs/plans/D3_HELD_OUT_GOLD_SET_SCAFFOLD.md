# Plan #37: D3 Held-Out Gold-Set Scaffold

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Held-out D3 application-validity evaluation; expert-parity D3 claims

---

## Gap

**Current:** D3 exact application-validity scoring accepts raw application gold
lists or simple objects, but there is no versioned package contract for held-out
D3 gold with corpus hashes, prompt-freeze status, contamination checks, and
human adjudication metadata.

**Target:** Add a schema_version=1 D3 application gold-set package contract,
loader/validator, validation script, make target, and bench-loader support.

**Why:** A public or held-out D3 result needs provenance and adjudication
metadata. Raw JSON anchors are adequate for local tests, but not for claim
discipline or future benchmark artifacts.

---

## References Reviewed

- `qc_clean/core/d3_gold.py` - current raw D3 application gold anchor contract.
- `qc_clean/core/d7_gold.py` - versioned D7 gold-set package pattern.
- `scripts/validate_d7_gold_set.py` - validator script pattern.
- `tests/test_d7_gold_set.py` - validation behavior expected for held-out gold.
- `scripts/bench_phase0.py` - D3 gold file loader.
- `Makefile` - validation target pattern.
- Memory context: `agent-memory recall 'active decisions qualitative_coding D3 gold set package validation adjudication application validity' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a package-contract
scaffold, not a populated gold dataset.

---

## Capabilities

Internal project capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_d3_gold_set_payload(payload)` | JSON object | `D3GoldSetPackage` | qualitative_coding | `scripts/validate_d3_gold_set.py`, `scripts/bench_phase0.py` | free |

### Capability Validation

- [ ] Versioned package validates prompt freeze, contamination check, coder count,
  corpus hash, and exact-key uniqueness.
- [ ] Bench loader accepts schema_version=1 D3 packages as `--d3-gold-file`.
- [ ] Validation script emits machine-readable JSON.

---

## Files Affected

- `qc_clean/core/d3_gold.py` (modify)
- `scripts/validate_d3_gold_set.py` (create)
- `Makefile` (modify)
- `tests/test_d3_gold_set.py` (create)
- `tests/test_bench_phase0_script.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add `D3AdjudicationMetadata` and `D3GoldSetPackage` models to
   `qc_clean/core/d3_gold.py`.
2. Add `load_d3_gold_set()`, `validate_d3_gold_set_payload()`, and package-aware
   support in `application_gold_payload_for_scorecard()`.
3. Add `scripts/validate_d3_gold_set.py` and `make validate-d3-gold GOLD=...`.
4. Add tests mirroring D7 package validation and bench loader acceptance.
5. Update docs conservatively: a package validator exists; no human-populated
   held-out D3 package has been built or scored.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d3_gold_set.py` | `test_validate_d3_gold_set_accepts_held_out_package` | Valid schema_version=1 held-out D3 package loads. |
| `tests/test_d3_gold_set.py` | `test_validate_d3_gold_set_rejects_duplicate_anchor_keys` | Duplicate code/doc/span application keys fail loudly. |
| `tests/test_d3_gold_set.py` | `test_validate_d3_gold_set_requires_held_out_freeze_and_adjudication` | Held-out package requires prompt freeze, contamination check, and at least two coders. |
| `tests/test_d3_gold_set.py` | `test_validate_d3_gold_set_script_outputs_json` | Script emits valid/invalid machine-readable JSON. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_d3_from_versioned_gold_package` | `--d3-gold-file` accepts schema_version=1 packages. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Raw D3 gold scoring remains unchanged. |
| `tests/test_d7_gold_set.py` | D7 package behavior remains unchanged. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] D3 package schema enforces held-out provenance and adjudication invariants.
- [ ] `make validate-d3-gold GOLD=...` validates packages with JSON output.
- [ ] `make bench ID=<project> D3_GOLD=package.json` accepts versioned D3 gold
  packages without mutating project state.
- [ ] Docs say this is a scaffold only; no held-out D3 result exists.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should D3 packages include human-human agreement metrics now? — Status:
  DEFERRED | Why it matters: the field exists as optional metadata, but computing
  κ/α/AC1 belongs to the future full D3 evaluation lane.

---

## Notes

This is a provenance scaffold for future held-out D3. It does not populate a
gold set or make any validity claim.
