# Plan #166: INV-11 Thematic Recode Higher-Order Refresh

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** INV-11 hard invalidation; INV-11 add-docs recode hook
**Blocks:** fuller corpus-mutation auto-recompute design

---

## Gap

**Current:** `project recode` and `project add-docs --recode` incrementally code
new documents, then rerun cross-interview and negative-case stages. They
hard-invalidate higher-order outputs that are not recomputed:
`perspective_analysis`, code/entity relationships, `synthesis`, GT core
categories, and the theoretical model. This is safe, but INV-11 remains partial
because omitted higher-order outputs require a full pipeline rerun to refresh.

**Target:** Add an explicit thematic-only higher-order refresh option:

- `project recode <project_id> --refresh-higher-order`
- `project add-docs <project_id> ... --recode --refresh-higher-order`

For default/thematic projects, the refresh path must:

1. run incremental coding on uncoded documents;
2. invalidate stale higher-order outputs before any intermediate save can
   publish them as current;
3. reconstruct Phase 1 code-hierarchy JSON from the current codebook;
4. rerun Perspective -> Relationship -> Synthesis;
5. rerun Cross-Interview -> Negative Case as today.

Default recode behavior must stay unchanged: no refresh flag means the current
hard-invalidation + cross-interview + negative-case pipeline remains the
contract.

Grounded-theory higher-order refresh is deliberately out of scope for this
slice. `--refresh-higher-order` must fail loudly on GT projects rather than
pretending GT axial/selective/theory context can be reconstructed by the
thematic path.

**Why:** This is the smallest safe auto-refresh step for INV-11. The thematic
higher-order stages already derive their inputs from state plus Phase 1/2/3
JSON; Phase 2 and Phase 3 are freshly produced by the refresh run, while Phase
1 can be reconstructed deterministically from the updated codebook. This
narrows the stale-output gap without fabricating a full GT recomputation design.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §7, §13.1, §18 - incremental recode and
  INV-11 caveats.
- `docs/plans/completed/INV11_INCREMENTAL_HARD_INVALIDATION.md` - current
  hard-invalidation contract and deferred auto-recompute question.
- `docs/plans/completed/INV11_ADD_DOCS_RECODE_HOOK.md` - explicit mutation +
  recode hook contract.
- `qc_clean/core/pipeline/pipeline_factory.py` - current incremental pipeline.
- `qc_clean/core/pipeline/stages/incremental_coding.py` - incremental coding
  and stale-output invalidation.
- `qc_clean/core/pipeline/stages/perspective.py`,
  `relationship.py`, `synthesis.py` - thematic higher-order stage context
  requirements.
- `qc_clean/schemas/adapters.py` and `qc_clean/schemas/analysis_schemas.py` -
  codebook/code-hierarchy schemas.
- `qc_clean/core/cli/commands/project.py` and `qc_cli.py` - recode/add-docs
  CLI surfaces.
- `tests/test_incremental_staleness_inv11.py`, `tests/test_incremental.py`,
  `tests/test_project_commands.py`, `tests/test_pipeline_stages.py`,
  `tests/test_adapters.py` - affected behavior and regression suites.
- Memory context:
  `agent-memory recall 'qualitative_coding INV-11 refresh higher-order recode auto recompute thematic pipeline' --project qualitative_coding`
  - low-relevance historical findings only, no active conflicting decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active
  claim files.

---

## Research Basis For This Slice

No external research is required. This is a repo-local recomputation pipeline
slice over existing stage contracts.

---

## Capabilities

Internal pipeline/CLI capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `thematic_recode_higher_order_refresh` | ProjectState with uncoded docs + existing codebook, PipelineContext | refreshed ProjectState or fail-loud error | qualitative_coding | CLI recode/add-docs operators | LLM |

---

## Files Affected

- `docs/plans/INV11_THEMATIC_RECODE_HIGHER_ORDER_REFRESH.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `qc_clean/schemas/adapters.py` - add `codebook_to_code_hierarchy()`.
- `qc_clean/core/pipeline/stages/incremental_coding.py` - let refresh mode
  suppress the invalidation warning while still invalidating stale objects.
- `qc_clean/core/pipeline/pipeline_factory.py` - add opt-in refresh pipeline
  shape and fail-loud GT guard.
- `qc_clean/core/cli/commands/project.py` - parse and forward refresh flag,
  fail loudly for GT projects.
- `qc_cli.py` - add CLI flags for `recode` and `add-docs --recode`.
- Tests:
  - `tests/test_adapters.py`
  - `tests/test_incremental_staleness_inv11.py`
  - `tests/test_project_commands.py`
  - `tests/test_pipeline_factory.py` if a dedicated file is clearer, otherwise
    an existing pipeline/factory test file.
- Docs after implementation:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/PROJECT_THEORY_AND_GOALS.md`

---

## Implementation Plan

1. Add `codebook_to_code_hierarchy(codebook: Codebook) -> CodeHierarchy`.
   Preserve code IDs/names/descriptions/definitions/parents/levels/example
   quotes/mention counts/confidence/reasoning; compute `total_codes` from the
   code list and `analysis_confidence` as the mean code confidence, defaulting
   to `0.0` for an empty codebook.
2. Add a lightweight pipeline stage, e.g. `RebuildThematicPhase1ContextStage`,
   that sets `ctx.phase1_json` from `codebook_to_code_hierarchy(state.codebook)`.
3. Extend `IncrementalCodingStage` with a constructor flag that keeps stale
   higher-order invalidation enabled but can suppress the "rerun full pipeline"
   data warning when the refresh pipeline will immediately recompute thematic
   outputs.
4. Extend `create_incremental_pipeline(..., refresh_higher_order=False)`.
   Default remains the existing three-stage incremental pipeline. When refresh
   is true and methodology is default/thematic, build:
   `IncrementalCodingStage(emit_invalidation_warning=False)` ->
   `RebuildThematicPhase1ContextStage()` -> `PerspectiveStage()` ->
   `RelationshipStage()` -> `SynthesisStage()` -> `CrossInterviewStage()` ->
   `NegativeCaseStage()`.
5. Fail loudly if `refresh_higher_order=True` is requested for grounded theory.
6. Add `--refresh-higher-order` to `project recode` and to `project add-docs`
   as an option that only has effect with `--recode`.
7. Update `_recode_project()` to forward the flag and print that thematic
   higher-order refresh is enabled.
8. Update docs to say this is an opt-in thematic refresh slice only; INV-11 is
   still partial because default recode still invalidates and GT higher-order
   recompute remains future work.

---

## Acceptance Criteria

| Check | Pass condition |
|-------|----------------|
| Default compatibility | `create_incremental_pipeline()` without refresh still returns incremental coding -> cross-interview -> negative-case, and default recode still emits invalidation warnings when stale outputs exist. |
| Thematic refresh pipeline | `create_incremental_pipeline(methodology="thematic_analysis", refresh_higher_order=True)` includes incremental coding, rebuilt thematic Phase 1 context, perspective, relationship, synthesis, cross-interview, and negative-case in that order. |
| Safe invalidation | Refresh mode invalidates stale higher-order objects before recompute, but does not leave the old "rerun full pipeline" warning after a successful refresh. |
| Context reconstruction | The rebuilt Phase 1 JSON validates as `CodeHierarchy` and represents the current codebook. |
| CLI | `project recode --refresh-higher-order` and `project add-docs --recode --refresh-higher-order` parse and forward the flag. |
| GT guard | `--refresh-higher-order` on a grounded-theory project exits non-zero with a clear unsupported-methodology message before any LLM call. |
| Claim discipline | Docs state this is opt-in thematic higher-order refresh only, not full INV-11 completion, not GT refresh, not methodological validity evidence, and not SOTA. |

---

## Verification

| Command | Expected |
|---------|----------|
| `python -m pytest tests/test_adapters.py -k "codebook_to_code_hierarchy" -q` | Adapter tests pass |
| `python -m pytest tests/test_incremental_staleness_inv11.py tests/test_project_commands.py -k "refresh_higher_order or stale_higher_order" -q` | INV-11/CLI focused tests pass |
| `python -m pytest tests/test_incremental.py tests/test_pipeline_stages.py tests/test_project_commands.py -q` | Incremental/pipeline command regressions pass |
| `python -m ruff check qc_clean/schemas/adapters.py qc_clean/core/pipeline/stages/incremental_coding.py qc_clean/core/pipeline/pipeline_factory.py qc_clean/core/cli/commands/project.py qc_cli.py tests/test_adapters.py tests/test_incremental_staleness_inv11.py tests/test_project_commands.py` | Touched Python lint passes |
| `make docs-check` | Plan index, links, coupling, and AGENTS sync pass |
| `git diff --check` | No whitespace errors |
| `make check` | Full deterministic gate passes |

---

## Failure Modes

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Refresh pipeline cannot satisfy a stage's context requirement | Rebuilt context stage did not populate the same `ctx.phase1_json` contract as thematic coding | Fix context stage or adapter; do not weaken `ctx.require()` fail-loud behavior |
| Refresh pipeline saves stale outputs after incremental coding | Invalidation happened after the first save callback or was disabled entirely | Ensure incremental stage still invalidates stale outputs before returning even in refresh mode |
| GT refresh request runs thematic stages | Methodology guard missing or wrong | Add fail-loud guard in factory and CLI before pipeline execution |
| Docs imply full INV-11 is met | Overclaim | Revise docs to "opt-in thematic slice"; keep default/GT caveats |
| Full suite exposes unrelated failure | Inspect; fix only if causally related, otherwise record and continue per sprint rules |

---

## Claim Discipline

This plan may say thematic projects can opt into higher-order recomputation
after incremental recode. It must not say INV-11 is fully met, because default
recode still uses hard invalidation and grounded-theory higher-order refresh is
not implemented. It must not claim methodological validity or SOTA evidence.
