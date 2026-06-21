# Plan #31: D7 Held-Out Gold-Set Scaffold

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** D7 gold-file bench input; Phase 0 benchmark artifacts
**Blocks:** held-out D7 prompt_eval runs; live baseline comparison; D7 public benchmark evidence

---

## Gap

**Current:** `make bench` / `qc_cli.py bench` can score D7 when a JSON file
contains a raw `contrary_evidence` anchor list, but there is no versioned
gold-set package contract for held-out adjudicated evidence. That leaves future
D7 runs without a deterministic way to verify dataset identity, adjudication
metadata, contamination/freeze status, or duplicate anchor keys before scoring.

**Target:** Add a D7 gold-set scaffold: typed package models, a loader/validator,
an agent-drivable validation script, and docs. The package should wrap the
existing `contrary_evidence` anchors with schema version, split, corpus hash,
adjudication protocol, prompt-freeze/contamination flags, and provenance.

**Why:** D7 cannot become evidence until humans produce held-out contrary
evidence and the system records the human ceiling and dataset provenance. This
slice does not create that human gold data. It creates the contract and validator
so future prompt_eval D7 runs can fail loudly before scoring malformed or
non-held-out packages.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D7 definition, held-out gold requirement, and
  prompt_eval boundary.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-2 state ledger and claim discipline.
- `docs/plans/completed/INV2_D7_GOLD_FILE_BENCH_INPUT.md` - external gold-file
  wiring.
- `docs/plans/completed/D7_BASELINE_COMPARISON.md` - baseline comparison needs
  held-out D7 evaluation later.
- `docs/plans/completed/PHASE0_BENCHMARK_ARTIFACTS.md` - benchmark artifact
  provenance substrate.
- `qc_clean/core/bench.py` - current `DisconfirmationGoldAnchor` model and exact
  key matching.
- `scripts/bench_phase0.py` - current gold file loader.
- Memory context:
  `agent-memory recall 'active decisions qualitative_coding D7 held-out gold set disconfirmation benchmark prompt_eval' --project qualitative_coding`
  returned historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research is needed. The evaluation-harness doc already specifies
the expert-consensus-panel requirement and the held-out/prompt-frozen standard.
This plan translates that local design into a machine-checkable package shape.

---

## Capabilities

| Capability | Input | Output | Owner |
|------------|-------|--------|-------|
| `validate_d7_gold_set` | JSON D7 gold-set package | Typed package or clear validation errors | qualitative_coding |

This is a repo-local validator and package contract, not a prompt_eval
experiment runner.

---

## Package Contract

Version 1 gold-set package:

```json
{
  "schema_version": 1,
  "gold_set_id": "d7-heldout-v1",
  "dataset_name": "Held-out interview contrary evidence v1",
  "split": "held_out",
  "corpus_sha256": "<64 hex chars>",
  "project_state_sha256": "<64 hex chars or null>",
  "prompt_frozen": true,
  "contamination_checked": true,
  "adjudication": {
    "coder_count": 2,
    "adjudicator": "redacted-or-name",
    "protocol": "Independent coding followed by adjudication.",
    "human_human_agreement": null,
    "notes": ""
  },
  "contrary_evidence": [
    {
      "target_claim_id": "claim-ai",
      "doc_id": "doc-1",
      "start_char": 100,
      "end_char": 142,
      "quote_text": "..."
    }
  ]
}
```

Validation rules:

- `schema_version` must be `1`.
- `gold_set_id`, `dataset_name`, `split`, and `corpus_sha256` must be present.
- `split` is one of `held_out`, `dev`, or `public_comparator`.
- `corpus_sha256` and optional `project_state_sha256` must be 64-character hex
  SHA-256 strings.
- `contrary_evidence` must be non-empty.
- Each anchor uses the existing D7 exact key contract: target claim, document,
  and either span offsets or segment ID.
- Duplicate exact anchor keys fail loudly.
- `held_out` packages require `prompt_frozen=true`,
  `contamination_checked=true`, and `adjudication.coder_count >= 2`.

---

## Files Affected

- `qc_clean/core/d7_gold.py` (create)
- `qc_clean/core/bench.py` (modify only if needed to reuse shared anchor/package loader)
- `scripts/validate_d7_gold_set.py` (create)
- `scripts/bench_phase0.py` (modify if package loader should replace ad hoc shape check)
- `Makefile` (modify)
- `tests/test_d7_gold_set.py` (create)
- `tests/test_bench_phase0_script.py` (modify if package compatibility is routed through bench)
- `docs/EVALUATION_HARNESS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify after closeout)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/D7_HELD_OUT_GOLD_SET_SCAFFOLD.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `qc_clean/core/d7_gold.py` with Pydantic models for the gold anchor,
   adjudication metadata, and versioned gold-set package.
2. Add `load_d7_gold_set(path)` and `validate_d7_gold_set_payload(payload)` that
   return typed packages or raise clear `ValueError`s.
3. Add duplicate exact-key validation using the same target-claim/source-anchor
   key semantics as the D7 scorecard.
4. Add `scripts/validate_d7_gold_set.py <gold_set.json>` that emits compact JSON:
   `{"valid": true, ...}` or `{"valid": false, "error": "..."}` with exit code
   `0` or `1`.
5. Add `make validate-d7-gold GOLD=<path>` as the agent-facing shortcut.
6. Update `scripts/bench_phase0.py --gold-file` to accept the versioned package
   without mutating project state, while preserving raw list/object compatibility.
7. Update docs conservatively: this is a gold-set scaffold only; no held-out D7
   benchmark has been run.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_gold_set.py` | `test_validate_d7_gold_set_accepts_held_out_package` | Valid held-out package loads and exposes anchors. |
| `tests/test_d7_gold_set.py` | `test_validate_d7_gold_set_rejects_duplicate_anchor_keys` | Duplicate exact D7 keys fail loudly. |
| `tests/test_d7_gold_set.py` | `test_validate_d7_gold_set_requires_held_out_freeze_and_adjudication` | Held-out packages require prompt freeze, contamination check, and at least two coders. |
| `tests/test_d7_gold_set.py` | `test_validate_d7_gold_set_script_outputs_json` | Script returns JSON success/failure and correct exit codes. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_d7_from_versioned_gold_package` | Existing `--gold-file` path accepts the package and feeds D7 scoring. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Core D7 scorecard contract remains unchanged. |
| `tests/test_bench_phase0_script.py` | Existing raw gold-file compatibility remains intact. |
| `make docs-check` | Verify docs, plan status, and AGENTS sync. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] A versioned D7 gold-set package schema exists.
- [ ] Valid held-out packages require freeze/contamination/adjudication metadata.
- [ ] Duplicate D7 anchor keys fail loudly.
- [ ] A CLI script validates packages and emits machine-readable JSON.
- [ ] `make validate-d7-gold GOLD=<path>` runs the validator.
- [ ] `bench_phase0 --gold-file` accepts a versioned package while preserving raw
  anchor-list compatibility.
- [ ] Docs state no held-out D7 benchmark, live baseline run, or superiority
  evidence has been produced.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should the first real held-out package include human-human κ/α/AC1 fields?
  - Status: DEFERRED | Why it matters: D7 recall/precision can run with contrary
  evidence anchors alone, but public claim evidence needs human-ceiling metadata.
  This scaffold includes optional `human_human_agreement` as a future slot.
- [ ] Should gold packages include encrypted/redacted source excerpts?
  - Status: DEFERRED | Why it matters: quote text helps inspection but can leak
  participant data. This scaffold permits `quote_text` but does not require it.

---

## Notes

Do not create synthetic gold data and do not report D7 validity. The deliverable
is the package contract and validator only.
