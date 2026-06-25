# Plan #238: Thematic Graph Relationship Hardening

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #237
**Blocks:** continuation of default-path graph polish claims, further Plan #234 interpretation beyond the current local seed packet

---

## Gap

**Current:** The default thematic path exposes graph surfaces that are not
operationally credible on a real corpus run. `graph.code_relationships_tab` is
visible by default, but `qc_clean/core/pipeline/stages/relationship.py` does
not populate `state.code_relationships`. The entity map is populated, but the
current prompt/schema balance encourages too many isolated entities and too few
useful links.

**Target:** Make the default thematic graph truthful and useful on the default
path by either producing first-class thematic `code_relationships` or
explicitly disabling unsupported surfaces, and by improving relationship-stage
output density/utility enough that the entity map is not trivially sparse on
the 3-document local seed.

**Why:** The graph UI is a default-path visible analytic surface. Right now it
creates false completion signals: a user can open the graph and infer product
maturity that the default pipeline does not support.

---

## References Reviewed

- `docs/DEFAULT_PATH_OPERATIONAL_CREDIBILITY_POLICY.md` - new policy standard
  and terminology.
- `docs/governance/default_path_surface_contracts.yaml` - explicit registry of
  the current graph surface producer gap.
- `docs/plans/DEFAULT_PATH_OPERATIONAL_CREDIBILITY_POLICY.md` - completed
  policy rollout slice and its known warning-only gap.
- `docs/plans/SANITIZED_CORPUS_ADJUDICATION_SEED.md` - current real-run corpus
  instrument that exposed the graph gap.
- `docs/LONG_TERM_EXECUTION_PLAN.md` - current execution spine and priority
  framing.
- `qc_clean/core/pipeline/stages/relationship.py` - default thematic
  relationship stage.
- `qc_clean/core/pipeline/stages/gt_axial_coding.py` - current GT producer for
  `state.code_relationships`.
- `qc_clean/schemas/analysis_schemas.py` - phase-3 relationship extraction
  schema.
- `qc_clean/schemas/adapters.py` - entity/relationship adapter layer.
- `qc_clean/schemas/domain.py` - `CodeRelationship` and
  `DomainEntityRelationship` contracts.
- `qc_clean/plugins/api/api_server.py` - graph API endpoints currently exposing
  code and entity relationship surfaces.
- `qc_clean/plugins/api/graph_ui.py` - default graph tabs and empty-state
  wording.
- `test_output/plan234_local_africa_seed_2026_06_25/artifacts/report.md` -
  real local seed output context.
- User review on 2026-06-25 - graph inspection found empty code-relationship
  view and sparse entity map on the default thematic path.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

This slice modifies existing default-path graph-producing capability. It does
not add a new external callable boundary.

### Capability Validation

- [x] Default thematic runs produce truthful graph data for visible graph tabs,
  or the UI/API clearly marks unsupported surfaces unavailable.
- [x] Relationship-stage schema/adapter changes preserve typed domain-model
  contracts.
- [x] Real-run graph inspection on the 3-document local seed is part of
  acceptance, not an optional afterthought.

---

## Operational Validation

**Classification:** default_path_visible_surface
**Surface IDs:** `graph.code_relationships_tab`, `graph.entity_map_tab`
**Real-Run Requirement:** required

---

## Files Affected

- `docs/plans/THEMATIC_GRAPH_RELATIONSHIP_HARDENING.md` (create)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/LONG_TERM_EXECUTION_PLAN.md` (modify)
- `docs/governance/default_path_surface_contracts.yaml` (modify)
- `qc_clean/core/pipeline/stages/relationship.py` (modify)
- `qc_clean/schemas/analysis_schemas.py` (modify)
- `qc_clean/schemas/adapters.py` (modify)
- `qc_clean/plugins/api/api_server.py` (modify)
- `qc_clean/plugins/api/graph_ui.py` (modify)
- `tests/` (add focused coverage)

---

## Plan

### Steps

1. Review the thematic relationship stage, graph API/UI, and current domain
   contracts to decide whether thematic code relationships should be produced in
   phase 3 or whether unsupported tabs must be disabled first.
2. Tighten the phase-3 schema/prompt/adapter so the default thematic path emits
   first-class code relationships and more useful entity links on real runs.
3. Update graph API/UI behavior so empty or unsupported surfaces are truthful
   and explicitly explained rather than silently hollow.
4. Run the 3-document local seed again in an isolated store and inspect the
   graph UI/API outputs directly.
5. Update the surface-contract registry from warning-only to present/partial as
   justified by the real-run result.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_relationship_stage.py` | `test_relationship_stage_populates_thematic_code_relationships` | The default thematic relationship stage writes `state.code_relationships` from structured relationship output. |
| `tests/test_relationship_stage.py` | `test_relationship_stage_preserves_entity_relationships` | Entity relationships still persist correctly after the phase-3 schema/adapter change. |
| `tests/test_graph_api.py` | `test_graph_codes_endpoint_returns_relationship_edges_for_thematic_state` | The graph API exposes thematic code-relationship edges when present. |
| `tests/test_graph_api.py` | `test_graph_endpoint_explains_unavailable_relationship_surface_when_missing` | If a visible graph surface is still unsupported or empty, the API/UI surfaces an explicit reason rather than a silent hollow tab. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_project_commands.py` | Project CLI/state interactions must remain stable after graph-producing changes. |
| `tests/test_qc_cli_bench.py` | CLI surface changes must not break benchmark/reporting command contracts. |
| `tests/test_disconfirmation_retrieval_inv2.py` | Recent Plan #234 negative-case fix must remain intact while re-running the seed. |
| `./.venv/bin/python scripts/check_default_path_surface_contracts.py --validate-config` | The surface registry must remain honest after remediation. |
| `./.venv/bin/python scripts/check_surface_operational_readiness.py` | Operational-readiness checks must reflect the new state correctly. |
| `./.venv/bin/python -m ruff check .` | Lint gate. |
| `git diff --check` | Patch hygiene. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Default thematic runs produce non-empty `state.code_relationships`, or
  the graph surface is explicitly disabled/unavailable on that path.
- [x] The entity map is not trivially sparse on the 3-document local seed
  relative to extracted entities, or the remaining limitation is explicitly
  documented in UI/registry wording.
- [x] Graph API/UI wording is truthful about what each graph view is showing and
  what is unavailable.
- [x] The surface-contract registry no longer treats the thematic
  `graph.code_relationships_tab` gap as implicit.

> Process criteria:
- [x] Focused tests pass.
- [x] Relevant docs/plans are updated.
- [x] Real-run inspection is performed on the local seed corpus.
- [x] `git diff --check` passes.

---

## Open Questions

- [ ] Should thematic code relationships be extracted in the same phase-3 LLM
  call as entity relationships, or should they be a dedicated follow-on pass?
  Status: OPEN.
- [ ] What minimum graph-density heuristic is strong enough to justify moving
  `graph.entity_map_tab` from warning-only to fully enforced? Status: OPEN.

---

## Notes

This slice should prefer truthful end-to-end default-path behavior over adding
more graph surface area. If the best immediate fix is to disable or relabel an
unsupported surface before a stronger producer lands, do that first.

Completed on 2026-06-25. Real-run validation used the saved 3-document local
seed from Plan #234 and replayed the patched relationship stage into
`test_output/plan238_graph_hardening_2026_06_25/relationship_stage_replay_state.json`.
That replay produced 6 thematic code relationships, 8 entity relationships, and
15 linked entities, replacing the earlier sparse default-path result of 0 code
relationships, 14 entity relationships, and 59 extracted entities.
