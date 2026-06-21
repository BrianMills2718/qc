# Plan #22: INV-11 Incremental Hard Invalidation

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** INV-11 warning surfacing
**Blocks:** auto-recompute on corpus mutation

---

## Gap

**Current:** `IncrementalCodingStage` detects populated higher-order outputs
after a recode and appends a `data_warnings` entry, but it deliberately retains
the stale objects. Markdown/API/MCP surfaces warn, yet stale `synthesis`,
`perspective_analysis`, relationships, GT outputs, phase results, and their
claim-ledger rows can still be exported/read as if current if a consumer misses
the warning.

**Target:** When incremental recode processes new documents, hard-invalidate the
outputs the incremental pipeline does not recompute: perspective analysis,
entity/code relationships, synthesis, GT core categories, GT theoretical model,
matching phase results, and stale claim-ledger rows from those source stages.
Keep coding outputs, cross-interview, and negative-case paths intact because the
incremental pipeline updates/reruns those. Emit a clear warning naming the
invalidated outputs and telling the operator to rerun the full pipeline to
regenerate them.

**Why:** INV-11 says stale higher-order outputs must be invalidated or flagged,
never silently retained. The repo already flags; this slice removes the stale
objects themselves so routine exports cannot accidentally launder pre-recode
interpretations.

---

## References Reviewed

- `qc_clean/core/pipeline/stages/incremental_coding.py` - current stale-output warning.
- `tests/test_incremental_staleness_inv11.py` - existing INV-11 detector tests.
- `tests/test_incremental.py` - mocked incremental-stage execution tests.
- `qc_clean/core/claims.py` - claim `source_stage` replacement/removal pattern.
- `qc_clean/core/pipeline/pipeline_factory.py` - incremental pipeline reruns only incremental coding, cross-interview, and negative-case stages.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-11 status and roadmap caveats.
- Memory context: `agent-memory recall 'INV-11 stale output invalidation incremental recode active decisions qualitative_coding' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional external research beyond repo-local references was needed. This
is an implementation of an already-defined project invariant.

---

## Capabilities

This plan modifies repo-local incremental pipeline behavior only; it does not
create a cross-project callable capability.

---

## Files Affected

- `qc_clean/core/pipeline/stages/incremental_coding.py` (modify)
- `tests/test_incremental_staleness_inv11.py` (modify)
- `tests/test_incremental.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV11_INCREMENTAL_HARD_INVALIDATION.md` (create, then move to completed)

---

## Plan

### Steps

1. Define the stale higher-order output fields and stale source stages in one
   local table.
2. Add `invalidate_stale_higher_order_outputs(state) -> list[str]` that:
   clears populated stale outputs, removes stale phase results, and removes
   stale claim-ledger rows for the invalidated source stages.
3. Call invalidation after successful incremental coding and before returning
   state.
4. Update the data warning language from "did not recompute / may be stale" to
   "invalidated / rerun full pipeline to regenerate."
5. Keep cross-interview and negative-case untouched because the incremental
   pipeline reruns them after incremental coding.
6. Add tests for helper-level clearing and stage-level invocation.
7. Update docs from "flagging only" to "hard invalidation first slice"; preserve
   caveats about no auto-recompute.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_incremental_staleness_inv11.py` | `test_invalidate_stale_higher_order_outputs_clears_outputs_phase_results_and_claims` | Invalidation clears stale objects, stale phase results, and stale claims while preserving non-stale claims/results. |
| `tests/test_incremental.py` | `test_incremental_coding_invalidates_stale_higher_order_outputs` | The incremental stage calls invalidation after a successful recode and records an invalidation warning. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_incremental_staleness_inv11.py tests/test_incremental.py` | Direct INV-11 and incremental behavior. |
| `tests/test_claims.py tests/test_claim_ledger_pipeline.py` | Claim ledger stage semantics remain intact. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Incremental recode hard-invalidates stale higher-order outputs it does not recompute.
- [ ] Stale claim-ledger rows from invalidated source stages are removed.
- [ ] Stale phase results from invalidated source stages are removed.
- [ ] Coding outputs, cross-interview, and negative-case paths remain untouched.
- [ ] Data warning says outputs were invalidated and full pipeline rerun is needed.
- [ ] Docs state INV-11 is improved but still partial because auto-recompute is not implemented.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should stale human review decisions targeting removed claims also be
  withdrawn? — Status: DEFERRED | Why it matters: the immediate stale export
  risk is stale claims/objects; review-decision pruning needs a focused contract
  because decisions may be audit history rather than active assertions.

---

## Notes

This intentionally does not auto-rerun perspective/relationship/synthesis/GT
stages. The incremental pipeline lacks their required inter-stage context, so
auto-recompute remains a later architecture change.
