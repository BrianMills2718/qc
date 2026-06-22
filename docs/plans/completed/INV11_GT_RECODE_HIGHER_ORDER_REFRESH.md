# Plan #167: INV-11 GT Recode Higher-Order Refresh

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #166
**Blocks:** fuller default corpus-mutation auto-refresh policy

---

## Outcome

Grounded-theory projects can now opt into higher-order refresh after
incremental recode:

- `project recode <project_id> --refresh-higher-order`
- `project add-docs <project_id> ... --recode --refresh-higher-order`

The GT refresh path now:

1. runs incremental coding on uncoded documents;
2. invalidates stale higher-order outputs before the first post-incremental
   save can preserve stale objects as current;
3. reconstructs `ctx.gt_open_codes` and `ctx.gt_open_codes_text` from the
   current codebook via `codebook_to_open_codes()`;
4. reruns Axial -> Selective -> Theory Integration;
5. reruns Cross-Interview -> Negative Case.

Default recode remains unchanged: without `--refresh-higher-order`, it uses
hard invalidation plus Cross-Interview and Negative Case. The existing
default/thematic refresh path remains unchanged.

Implementation commit: `ccd7051`
(`Add GT recode higher-order refresh`).

Verification:

- Initial focused tests failed before implementation because
  `RebuildGTOpenCodesContextStage` did not exist.
- `python -m pytest tests/test_adapters.py -k "CodebookToOpenCodes or CodebookToCodeHierarchy" tests/test_incremental.py -k "gt_open_codes_context or gt_refresh_pipeline or thematic_refresh_pipeline or creates_default_pipeline" tests/test_project_commands.py -k "refresh_higher_order" -q`
  -> 3 passed, 89 deselected.
- `python -m pytest tests/test_adapters.py tests/test_incremental.py tests/test_pipeline_stages.py tests/test_project_commands.py -q`
  -> 116 passed.
- Targeted Ruff passed for touched Python files.
- `make docs-check` -> passed.
- `git diff --check` -> passed.
- `make check` -> 1133 passed, 1 skipped, 8 deselected; Ruff and docs gates
  passed.

INV-11 remains partial. Refresh is still opt-in, default recode still uses hard
invalidation, and no full automatic corpus-mutation policy exists. This is not
grounded-theory methodological-validity evidence, saturation evidence, full-GT
evidence, or a SOTA claim.

---

## Gap

**Current:** `project recode --refresh-higher-order` and
`project add-docs --recode --refresh-higher-order` can refresh thematic
higher-order outputs after incremental coding, but grounded-theory projects fail
loudly because the prior slice did not rebuild the GT open-code context required
by axial, selective, and theory-integration stages.

**Target:** Grounded-theory projects can opt into `--refresh-higher-order`.
After incremental coding, the refresh pipeline must rebuild GT open-code context
from the current codebook, rerun Axial -> Selective -> Theory Integration, and
then rerun Cross-Interview -> Negative Case. The default non-refresh path must
remain unchanged and continue hard-invalidating stale outputs it cannot refresh.

**Why:** INV-11 requires stale higher-order outputs to be invalidated or
recomputed after corpus mutation. Thematic opt-in refresh exists; GT opt-in
refresh is the next scoped recompute path because the stage dependencies are
already explicit (`gt_open_codes_text` -> `gt_axial_text` -> `gt_core_text`).

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §7, §13.1, §18 - current INV-11 status and
  claim-discipline boundaries.
- `docs/plans/completed/INV11_THEMATIC_RECODE_HIGHER_ORDER_REFRESH.md` - prior
  thematic refresh slice and explicit GT deferral.
- `qc_clean/core/pipeline/pipeline_factory.py` - current incremental pipeline
  shape and GT guard.
- `qc_clean/core/pipeline/stages/incremental_coding.py` - incremental coding,
  hard invalidation, and thematic Phase 1 context rebuild stage.
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` - open-code context
  formatter consumed by downstream GT stages.
- `qc_clean/core/pipeline/stages/gt_axial_coding.py` - requires
  `ctx.gt_open_codes_text`, emits `ctx.gt_axial_text`.
- `qc_clean/core/pipeline/stages/gt_selective_coding.py` - requires
  `ctx.gt_open_codes_text` and `ctx.gt_axial_text`, emits `ctx.gt_core_text`.
- `qc_clean/core/pipeline/stages/gt_theory_integration.py` - requires
  `ctx.gt_open_codes_text`, `ctx.gt_axial_text`, and `ctx.gt_core_text`.
- `qc_clean/schemas/adapters.py` and `qc_clean/schemas/gt_schemas.py` -
  existing `codebook_to_open_codes()` adapter and GT schemas.
- `qc_clean/core/cli/commands/project.py` and `qc_cli.py` - recode/add-docs CLI
  surfaces.
- `tests/test_incremental.py`, `tests/test_project_commands.py`,
  `tests/test_adapters.py` - affected regression tests.
- Memory context:
  `agent-memory recall 'active decisions INV-11 grounded theory refresh qualitative_coding' --project qualitative_coding`
  - low-relevance historical findings only, no active conflicting decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active
  claim files.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a repo-local
pipeline dependency and stale-output recompute slice.

---

## Capabilities

Internal pipeline/CLI capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `gt_recode_higher_order_refresh` | ProjectState with uncoded docs + existing GT codebook, PipelineContext | refreshed ProjectState or fail-loud error | qualitative_coding | CLI recode/add-docs operators | LLM |

### Capability Validation

Skipped: this does not create a cross-project tool, contract, or external
callable capability.

---

## Files Affected

- `docs/plans/completed/INV11_GT_RECODE_HIGHER_ORDER_REFRESH.md` - completed
  plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `qc_clean/schemas/adapters.py` - tighten `codebook_to_open_codes()` if needed
  for GT context fidelity.
- `qc_clean/core/pipeline/stages/incremental_coding.py` - add GT open-code
  context rebuild stage.
- `qc_clean/core/pipeline/pipeline_factory.py` - add GT refresh pipeline shape.
- `qc_clean/core/cli/commands/project.py` - remove GT refresh rejection and
  report refresh scope accurately.
- `qc_cli.py` - update refresh flag help text.
- Tests:
  - `tests/test_incremental.py`
  - `tests/test_project_commands.py`
  - `tests/test_adapters.py`
- Docs after implementation:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/PROJECT_THEORY_AND_GOALS.md`

---

## Plan

### Steps

1. Add/verify a `codebook_to_open_codes()` adapter contract that preserves the
   codebook fields the GT formatter can expose.
2. Add `RebuildGTOpenCodesContextStage` that converts the current codebook into
   GT `OpenCode` rows and populates `ctx.gt_open_codes` plus
   `ctx.gt_open_codes_text`.
3. Extend `create_incremental_pipeline(..., refresh_higher_order=True)` so GT
   projects run:
   `IncrementalCodingStage(emit_invalidation_warning=False)` ->
   `RebuildGTOpenCodesContextStage()` -> `GTAxialCodingStage()` ->
   `GTSelectiveCodingStage()` -> `GTTheoryIntegrationStage()` ->
   `CrossInterviewStage()` -> `NegativeCaseStage()`.
4. Preserve the existing thematic refresh path and the existing default
   hard-invalidation path exactly.
5. Remove the CLI-level GT rejection, forward the refresh flag for all
   methodologies, and make the operator message name the active refresh scope.
6. Update docs and claim-discipline text: INV-11 remains partial because refresh
   is opt-in and no default automatic corpus-mutation policy exists.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_incremental.py` | `test_rebuild_gt_open_codes_context_stage_uses_current_codebook` | GT context rebuild creates `gt_open_codes` and `gt_open_codes_text` from the current codebook. |
| `tests/test_incremental.py` | `test_creates_gt_refresh_pipeline` | GT refresh pipeline has incremental -> rebuild GT context -> axial -> selective -> theory -> cross-interview -> negative-case order. |
| `tests/test_project_commands.py` | `test_recode_refresh_higher_order_allows_grounded_theory` | CLI no longer rejects GT refresh before pipeline creation and forwards the flag. |
| `tests/test_adapters.py` | adapter preservation test if needed | Adapter preserves GT-relevant codebook fields. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_incremental.py tests/test_pipeline_stages.py tests/test_project_commands.py -q` | Pipeline and CLI regression coverage. |
| `python -m pytest tests/test_adapters.py -q` | Schema adapter coverage. |
| targeted Ruff on touched Python files | Style/syntax gate before full check. |
| `make docs-check` | Plan/docs governance and generated AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before implementation closeout. |

---

## Acceptance Criteria

- [x] Default compatibility: `create_incremental_pipeline()` without refresh
  still returns incremental coding -> cross-interview -> negative-case.
- [x] Thematic compatibility: existing default/thematic refresh pipeline order
  is unchanged.
- [x] GT refresh pipeline: grounded-theory refresh runs incremental coding,
  rebuilds GT open-code context, reruns axial/selective/theory integration, then
  reruns cross-interview and negative-case.
- [x] Safe invalidation: refresh mode still invalidates stale higher-order
  objects before recompute and does not leave the old "rerun full pipeline"
  warning after successful refresh.
- [x] CLI: `project recode --refresh-higher-order` and
  `project add-docs --recode --refresh-higher-order` parse and forward the flag
  for GT projects.
- [x] Claim discipline: docs state this is opt-in higher-order refresh, not full
  INV-11 completion, not GT methodological-validity evidence, not saturation
  evidence, and not SOTA.
- [x] Required tests and gates pass.

---

## Open Questions

- [x] Can GT open-code context be reconstructed safely from the codebook?
  Status: RESOLVED. The existing `codebook_to_open_codes()` adapter already
  maps current codebook rows into GT `OpenCode` objects; the refresh stage can
  reuse the same downstream formatter as constant comparison.

---

## Notes

This plan deliberately does not make refresh the default behavior. That policy
choice remains the broader INV-11 follow-up because automatic refresh spends LLM
budget and changes corpus-mutation semantics.
