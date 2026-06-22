# Plan #111: D7 Retrieval Comparison Protocol Preflight

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** D7 gold-set scaffold; D7 retrieval-mode export/comparison
**Blocks:** safer held-out D7 retrieval/live-baseline comparison runs

---

## Outcome

Implemented D7 retrieval comparison protocol validation and preflight. D7
retrieval prediction packages now carry project/corpus/state/trace/budget
provenance; `make validate-d7-comparison-protocol PROTOCOL=...` validates
registered comparison metadata; and `make d7-comparison-preflight PROTOCOL=...
GOLD=... PREDICTIONS="..."` cross-checks versioned D7 gold and retrieval
prediction packages before scoring. Verification: focused D7 tests passed
(`22 passed`), focused Ruff passed, `make docs-check` passed, both new Make
targets dry-ran to the expected scripts, and full `make check` passed (`939
passed, 1 skipped, 8 deselected`; Ruff/docs clean; type check not configured).

## Gap

**Current:** `make compare-d7-retrieval` can score arbitrary retrieval
prediction packages against arbitrary D7 gold. Prediction packages include
retrieval configuration, but they do not yet record project/corpus/state hashes,
trace ID, or budget provenance. There is also no pre-registered comparison
protocol or preflight that proves the gold package and prediction packages match
the intended held-out comparison before scoring.

**Target:** Add a deterministic D7 comparison protocol and preflight:

- Extend D7 retrieval prediction package metadata with `project_id`,
  `project_state_sha256`, `corpus_sha256`, `trace_id`, and `max_budget`.
- Core protocol validator:
  `qc_clean/core/d7_comparison_protocol.py`.
- Core preflight:
  `qc_clean/core/d7_comparison_preflight.py`.
- Scripts:
  `scripts/validate_d7_comparison_protocol.py` and
  `scripts/preflight_d7_comparison.py`.
- Make targets:
  `make validate-d7-comparison-protocol PROTOCOL=protocol.json` and
  `make d7-comparison-preflight PROTOCOL=protocol.json GOLD=gold.json PREDICTIONS="a.json b.json"`.
- Preflight checks:
  - protocol validation passes;
  - gold is a versioned schema_version=1 D7 package, not raw/list gold;
  - gold set ID, dataset, split, corpus hash, optional project-state hash,
    prompt-freeze flag, and contamination flag match the protocol;
  - each retrieval prediction package validates and carries provenance;
  - prediction project/corpus/state hashes match the protocol/gold;
  - expected baseline names are present exactly once;
  - expected retrieval mode, candidates per claim, max targets, embedding model,
    embedding dimensions, trace ID, and max budget match;
  - optional expected prediction-file SHA-256 locks match actual file hashes.
- Output is a machine-readable pass/fail report with the caveat that preflight
  is process/provenance metadata only.

**Why:** D7 is the highest-ranked remaining evaluation lane. Exact-span
comparison output is only meaningful if the gold, state, split, retrieval
configuration, and prediction files are bound to the registered protocol. This
closes the deterministic handoff gap before held-out D7 comparison scoring
without claiming that any populated held-out result exists.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - roadmap ranks D7 held-out evaluation and
  live baselines as a next high-value lane.
- `docs/EVALUATION_HARNESS.md` - D7 scoring substrate, baseline comparison, and
  held-out/live-baseline gaps.
- `qc_clean/core/d7_retrieval.py` - retrieval prediction package and comparison
  report contracts.
- `qc_clean/core/d7_gold.py` - versioned D7 gold-set package validator.
- `scripts/run_d7_retrieval.py` - retrieval package export surface.
- `scripts/compare_d7_retrieval.py` - comparison scoring surface.
- `tests/test_d7_retrieval.py` - existing retrieval export/comparison coverage.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is deterministic
protocol/provenance hardening over existing D7 contracts.

---

## Capabilities

Internal preflight capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_d7_comparison_protocol` | D7 comparison protocol package | protocol validation report | qualitative_coding | agents/operators preparing D7 comparisons | free |
| `preflight_d7_comparison` | D7 comparison protocol + versioned D7 gold + retrieval prediction packages | preflight report | qualitative_coding | agents/operators running held-out D7 comparisons | free |

### Capability Validation

- [x] Protocol validator accepts a valid held-out comparison protocol.
- [x] Protocol validator rejects invalid held-out flags, duplicate expected
  baseline names, malformed hashes, and incomplete embedding expectations.
- [x] Retrieval export packages include project/corpus/state/trace/budget
  provenance.
- [x] Matching protocol/gold/predictions pass preflight.
- [x] Gold provenance mismatches fail loud.
- [x] Prediction provenance/config/file-hash mismatches fail loud.
- [x] CLI/Make targets emit machine-readable pass/fail output.

---

## Files Affected

- `qc_clean/core/d7_retrieval.py` (modify)
- `qc_clean/core/d7_comparison_protocol.py` (create)
- `qc_clean/core/d7_comparison_preflight.py` (create)
- `scripts/validate_d7_comparison_protocol.py` (create)
- `scripts/preflight_d7_comparison.py` (create)
- `tests/test_d7_retrieval.py` (modify)
- `tests/test_d7_comparison_protocol.py` (create)
- `tests/test_d7_comparison_preflight.py` (create)
- `Makefile` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add TDD tests for D7 retrieval export provenance, protocol validation, and
   protocol/gold/prediction preflight.
2. Extend D7 retrieval export metadata with project/corpus/state/trace/budget
   provenance.
3. Implement the protocol validator and validation script.
4. Implement the preflight core, script, and Make targets.
5. Update docs to state this is protocol/provenance metadata only, not held-out
   D7 evidence or live-baseline evidence.
6. Run focused tests, focused Ruff, docs checks, Make dry-runs, and full
   `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_retrieval.py` | `test_export_records_project_hash_trace_and_budget_provenance` | Retrieval prediction package records provenance needed for protocol matching. |
| `tests/test_d7_comparison_protocol.py` | `test_validate_d7_comparison_protocol_accepts_held_out_package` | Valid held-out comparison protocol passes. |
| `tests/test_d7_comparison_protocol.py` | `test_validate_d7_comparison_protocol_rejects_invalid_held_out_flags` | Held-out protocols require freeze, contamination check, and registration. |
| `tests/test_d7_comparison_protocol.py` | `test_validate_d7_comparison_protocol_rejects_duplicate_expected_baselines` | Expected baseline names must be unique. |
| `tests/test_d7_comparison_protocol.py` | `test_validate_d7_comparison_protocol_rejects_incomplete_embedding_expectation` | Embedding-hybrid expectations must name an embedding model. |
| `tests/test_d7_comparison_preflight.py` | `test_d7_comparison_preflight_accepts_matching_protocol_gold_and_predictions` | Matching protocol/gold/predictions pass. |
| `tests/test_d7_comparison_preflight.py` | `test_d7_comparison_preflight_rejects_gold_mismatch` | Gold provenance mismatch fails. |
| `tests/test_d7_comparison_preflight.py` | `test_d7_comparison_preflight_rejects_prediction_config_mismatch` | Retrieval config mismatch fails. |
| `tests/test_d7_comparison_preflight.py` | `test_d7_comparison_preflight_rejects_prediction_file_hash_mismatch` | Optional prediction-file hash lock fails loud. |
| `tests/test_d7_comparison_preflight.py` | `test_d7_comparison_preflight_script_outputs_json` | CLI emits valid/invalid JSON with exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_d7_retrieval.py tests/test_d7_gold_set.py` | Upstream D7 gold and retrieval contracts remain compatible. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Retrieval prediction packages carry project/corpus/state/trace/budget
  provenance.
- [x] Valid D7 comparison protocols validate.
- [x] Invalid held-out protocol metadata fails loud.
- [x] Protocol/gold mismatch fails loud.
- [x] Protocol/prediction provenance and retrieval-config mismatches fail loud.
- [x] Optional prediction file SHA-256 locks fail loud on mismatch.
- [x] `make validate-d7-comparison-protocol PROTOCOL=...` is discoverable and
  dry-runs correctly.
- [x] `make d7-comparison-preflight PROTOCOL=... GOLD=... PREDICTIONS="..."`
  is discoverable and dry-runs correctly.
- [x] Docs state this is process/provenance metadata only, not held-out D7
  validity evidence, live-baseline evidence, or superiority evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should preflight invoke `compare-d7-retrieval` automatically after
  passing? — Status: DEFERRED | Why it matters: this plan is a pre-scoring
  provenance gate. Automatic score execution can be a later wrapper once the
  protocol is stable.
- [x] Should protocols require prediction-file SHA-256 locks before prediction
  files exist? — Status: DEFERRED | Why it matters: pre-run protocols cannot
  know output hashes. This slice supports optional post-run file locks and
  requires metadata/config matching in all cases.

---

## Notes

This preflight proves that files and run metadata line up. It does not create a
held-out D7 result, run a live baseline, adjudicate gold labels, or license
methodological-validity/SOTA/superiority claims.
