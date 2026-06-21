# Plan #4: INV-9 First-Class Claim Ledger

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-6 full disconfirmation coverage; INV-10 review beyond code labels; public SOTA claim discipline

*Started: 2026-06-21. Owner: autonomous agent. Re-read after any compaction.*

---

## Gap

**Current:** Substantive analytic assertions live in free-text fields and memos:
code descriptions/reasoning, code applications, perspective summaries,
relationship evidence, synthesis findings, cross-case memo prose, GT
propositions, and negative-case memo content. The state is inspectable, but the
system cannot enumerate every final claim, prove what supports it, attach
contrary evidence, or record whether it was retained, narrowed, or withdrawn.

**Target:** Every substantive assertion is represented as a typed
`AnalyticClaim` object in `ProjectState.claims`, with source stage, claim kind,
claim text, scope, supporting anchors, contrary anchors, adjudication status,
revision history, and links to the originating object. Existing prose outputs
may remain for readability, but no substantive stage may produce only prose
without either emitting claim objects or recording an explicit no-claims event.

**Why:** This closes INV-9 and creates the object substrate required for INV-6
and INV-10. Disconfirmation cannot cover "all final claims" until claims are
first-class objects; human review cannot adjudicate synthesis, relationships, or
negative cases while those assertions are only embedded in prose.

---

## References Reviewed

- `agent-memory recall 'active decisions claim ledger INV-9 qualitative coding' --project qualitative_coding` — 2 old completed outcomes; no active decision.
- `docs/PROJECT_THEORY_AND_GOALS.md:239-323` — honest state, INV-6, INV-9, INV-10, roadmap priority.
- `docs/EVALUATION_HARNESS.md:1-170` — claim discipline and future validity/evaluation requirements.
- `docs/plans/TEMPLATE.md` — required plan structure.
- `docs/plans/CLAUDE.md` — active plan index; currently no active plan and "Next up: the claim ledger (INV-9)."
- `docs/plans/completed/INV8_SEGMENT_UNIVERSE.md` — prior overnight-plan style and status tracking.
- `docs/plans/completed/IRR_APPLICATION_LEVEL.md` — prior completed plan scope and explicit thematic-only boundary.
- `qc_clean/schemas/domain.py` — `ProjectState`, `Code`, `CodeApplication`, `AnalysisMemo`, perspectives, synthesis, GT result models.
- `qc_clean/schemas/analysis_schemas.py` — LLM-facing output schemas that will be adapted into claims.
- `qc_clean/schemas/adapters.py` — conversion layer from LLM output schemas to domain objects.
- `qc_clean/core/pipeline/stages/thematic_coding.py` — thematic and exhaustive code/application outputs.
- `qc_clean/core/pipeline/stages/perspective.py` — participant perspective claims.
- `qc_clean/core/pipeline/stages/relationship.py` — entity relationship and causal/conceptual claims.
- `qc_clean/core/pipeline/stages/synthesis.py` — key findings, patterns, recommendations, confidence claims.
- `qc_clean/core/pipeline/stages/cross_interview.py` — deterministic cross-case claims.
- `qc_clean/core/pipeline/stages/negative_case.py` — current memo-only disconfirmation output.
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py`, `gt_axial_coding.py`, `gt_selective_coding.py`, `gt_theory_integration.py` — GT code, relationship, category, and proposition outputs.
- `qc_clean/core/export/data_exporter.py` — JSON/CSV/Markdown export surfaces.
- `qc_clean/plugins/api/api_server.py`, `qc_mcp_server.py`, `qc_cli.py` — agent/user surfaces that must expose claim summaries.
- `/home/brian/projects/investigations/qualitative_coding/2026-06-21-deep-audit-testing-critique.md` — latest adversarial audit; F5 recommends this plan and F8/F9 constrain overclaiming.

---

## Research Basis For This Slice

No additional external research beyond repo-local references was needed for this
implementation slice. External validity work remains governed by
`docs/EVALUATION_HARNESS.md`; this plan builds the internal claim object layer it
needs.

---

## Capabilities

This plan creates internal callable helpers only. No cross-project boundary or
MCP tool is created in Phase 1. The agent-facing/API surfaces expose summaries of
state already stored in `ProjectState`.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `record_claims_for_stage(state, stage_name, source_objects)` | `ProjectState` + domain objects | mutated `ProjectState.claims` | qualitative_coding | pipeline stages, tests | free |
| `summarize_claim_ledger(state)` | `ProjectState` | plain `dict`/JSON summary | qualitative_coding | CLI/API/MCP/export | free |

### Capability Validation

- [ ] Input/output models live in `qc_clean/schemas/domain.py` or a claim helper module and use Pydantic fields with descriptions.
- [ ] Internal helpers are deterministic and unit-tested.
- [ ] No new MCP/server boundary is required for the first slice.
- [ ] JSON export includes the full ledger automatically via `ProjectState`.

---

## Files Affected

Expected implementation files:

- `qc_clean/schemas/domain.py` — add claim ledger models and `ProjectState.claims`.
- `qc_clean/core/claims.py` — create deterministic claim construction, anchor validation, summary helpers.
- `qc_clean/core/pipeline/stages/thematic_coding.py` — emit code/application claims.
- `qc_clean/core/pipeline/stages/perspective.py` — emit participant, consensus, divergent-view claims.
- `qc_clean/core/pipeline/stages/relationship.py` — emit entity relationship and causal/conceptual claims.
- `qc_clean/core/pipeline/stages/synthesis.py` — emit synthesis finding, pattern, recommendation, confidence claims.
- `qc_clean/core/pipeline/stages/cross_interview.py` — emit cross-case consensus/divergent/co-occurrence claims.
- `qc_clean/core/pipeline/stages/negative_case.py` — emit negative-case claims and attach contrary anchors where resolvable.
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` — emit GT code/application claims.
- `qc_clean/core/pipeline/stages/gt_axial_coding.py` — emit GT relationship claims.
- `qc_clean/core/pipeline/stages/gt_selective_coding.py` — emit core-category claims.
- `qc_clean/core/pipeline/stages/gt_theory_integration.py` — emit theoretical proposition/scope/implication claims.
- `qc_clean/core/export/data_exporter.py` — add CSV/Markdown claim ledger sections.
- `qc_clean/plugins/api/api_server.py` — include claim summary in project/detail responses or add a read-only claims endpoint.
- `qc_mcp_server.py` — add `qc_get_claims` or include claim counts in project show.
- `qc_cli.py` and `qc_clean/core/cli/commands/project.py` — add a read-only `project claims` command or expose claim summary in `project show`.
- `docs/PROJECT_THEORY_AND_GOALS.md` — update INV-9 status only after implementation is verified.
- `docs/plans/CLAUDE.md` and this plan file — track status.

Expected test files:

- `tests/test_claims.py`
- `tests/test_claim_ledger_pipeline.py`
- `tests/test_claim_ledger_exports.py`
- `tests/test_mcp_server.py`
- `tests/test_project_commands.py`
- `tests/test_negative_case_inv6.py`
- GT-specific tests as needed, likely `tests/test_constant_comparison.py` and pipeline-stage tests.

---

## Plan

### Overnight Execution Contract

Execute phases in order without pausing after a green test or completed commit.
Each verified phase gets its own commit. Stop only for an irreversible shared
state action or an architectural decision not pre-made here and not safely
defaultable. If a phase hits three failed attempts without new information, log
the failure in this plan, commit any verified prior work, and move to the next
highest-value independent phase.

### Pre-Made Design Decisions

1. **Additive state model:** add `ProjectState.claims: list[AnalyticClaim]` with
   a default empty list. Existing project JSON remains loadable.
2. **Deterministic first slice:** derive claims from already validated domain
   objects. Do not require new LLM prompt schemas in this plan unless needed for
   a specific claim type.
3. **Typed objects:** use Pydantic models with `Field(description=...)` on every
   new public field.
4. **Claim identity:** stable IDs are system-assigned with a prefix like
   `claim_` or UUID; never ask the LLM to generate IDs.
5. **Claim provenance:** each claim records `source_stage`, `claim_kind`,
   `origin_object_type`, `origin_object_id`, and `created_by`.
6. **Scope:** represent scope explicitly as document IDs, code IDs, segment IDs,
   participant names, or corpus-level scope. Do not infer population-level scope.
7. **Evidence anchors:** supporting and contrary anchors are typed references.
   Prefer `CodeApplication` anchors (`doc_id`, offsets, hash). Free-text claims
   without anchors are allowed only with `support_status="unsupported"` or
   `support_status="needs_anchor"` so the gap is visible.
8. **Adjudication state:** first-slice statuses are
   `pending`, `retained`, `revised`, `withdrawn`, and `needs_review`. LLM-created
   claims default to `pending`.
9. **Revision history:** record lightweight immutable entries with timestamp,
   actor/provenance, action, rationale, and previous/new claim text when changed.
10. **No prose-only bypass:** every substantive stage must call a helper that
    either appends claims or records a no-claims ledger event. This is enforced
    by tests, not by convention.
11. **Negative cases:** first slice stores negative cases as claims and, where a
    quote resolves, as contrary anchors to the challenged claim/code target. Full
    retrieval-first disconfirmation remains a later INV-2/INV-6 plan.
12. **Exports:** JSON gets the full ledger for free through `ProjectState`.
    Markdown and CSV get human-readable summaries. QDPX is unchanged in this
    plan.
13. **Docs discipline:** do not mark INV-6, INV-10, or methodological validity as
    met. If INV-9 is partially implemented, say exactly which claim producers
    are covered.

### Phases

| Phase | Scope | Verification | Commit |
|---|---|---|---|
| 1 | Schema: `AnalyticClaim`, anchor, scope, adjudication/revision models, `ProjectState.claims`, pure summary helper | DONE: `tests/test_claims.py`; JSON round-trip/backward compatibility | `[Plan: INV9] Add claim ledger schema` |
| 2 | Deterministic claim builders for codes, applications, perspectives, relationships, synthesis, cross-case, GT objects, and negative cases | DONE: `tests/test_claims.py` expanded with focused fixtures | `[Plan: INV9] Add claim builders` |
| 3 | Wire default thematic pipeline stages; enforce no prose-only bypass for default path | DONE: `tests/test_claim_ledger_pipeline.py`, targeted stage tests | `[Plan: INV9] Wire default pipeline claims` |
| 4 | Wire GT stages; explicitly reject/flag any GT claim class not yet representable | GT stage tests; no app-level IRR scope expansion | `[Plan: INV9] Wire GT claims` |
| 5 | Surface ledger in CSV/Markdown exports, CLI/API/MCP read paths | export/API/MCP/CLI tests | `[Plan: INV9] Expose claim ledger` |
| 6 | Negative-case linkage: store negative cases as claims and attach contrary anchors/target refs where deterministic | `tests/test_negative_case_inv6.py` updated; no claim over full INV-6 | `[Plan: INV9] Link negative cases to claims` |
| 7 | Docs and governance: update theory ledger, plan status, command docs, audit caveats | `make docs-check`; `make check` | `[Plan: INV9] Document claim ledger` |

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_claims.py` | `test_claim_models_round_trip_with_empty_ledger` | Existing/minimal `ProjectState` serializes and deserializes with `claims=[]`. |
| `tests/test_claims.py` | `test_code_and_application_claims_include_supporting_anchors` | Code/application claims link to code IDs and anchored quote spans. |
| `tests/test_claims.py` | `test_unanchored_claim_is_visible_not_silently_supported` | Claims without evidence anchors are marked `needs_anchor`/`unsupported`. |
| `tests/test_claims.py` | `test_revision_history_records_actor_action_and_text_change` | Review/revision metadata is preserved. |
| `tests/test_claims.py` | `test_claim_summary_counts_by_kind_stage_status` | Agent-facing summary is deterministic. |
| `tests/test_claim_ledger_pipeline.py` | `test_default_pipeline_stages_emit_claims_or_no_claim_events` | Thematic, perspective, relationship, synthesis, cross-case, negative-case outputs cannot remain prose-only. |
| `tests/test_claim_ledger_pipeline.py` | `test_exhaustive_pipeline_application_claims_reference_segments` | INV-8 segment decisions produce claim support over segment anchors. |
| `tests/test_claim_ledger_pipeline.py` | `test_gt_pipeline_emits_gt_claim_kinds` | GT codes, relationships, categories, and propositions are represented. |
| `tests/test_claim_ledger_exports.py` | `test_markdown_export_includes_claim_ledger_summary` | Markdown surfaces claim counts/statuses. |
| `tests/test_claim_ledger_exports.py` | `test_csv_export_writes_claims_file` | CSV export emits `claims.csv`. |
| `tests/test_project_commands.py` | `test_project_claims_command_outputs_summary` | CLI exposes an agent-drivable claim summary. |
| `tests/test_mcp_server.py` | `test_qc_get_claims_returns_claim_summary` | MCP exposes claim summary without raw full state dumping. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_claims.py tests/test_claim_ledger_pipeline.py tests/test_claim_ledger_exports.py -q` | Fast local proof for the new invariant. |
| `python -m pytest tests/test_negative_case_inv6.py tests/test_pipeline_stages.py tests/test_constant_comparison.py -q` | Protect affected stage semantics. |
| `python -m pytest tests/test_project_commands.py tests/test_mcp_server.py tests/test_qdpx_export.py -q` | Protect user/agent/export surfaces. |
| `make check` | Required repo gate: deterministic tests, lint, docs checks, plan sync. |

Live LLM E2E is not required for Phase 1 because the slice is deterministic and
derives claims from validated outputs. Run `make test-e2e` only after stage
wiring if a deterministic stage test cannot cover an integration boundary.

---

## Acceptance Criteria

Feature-level criteria:

- [x] `ProjectState.claims` exists, is backward-compatible, and survives JSON round-trip.
- [x] Every claim records source stage, kind, text, scope, provenance, support status, and origin object linkage.
- [x] Evidence anchors can represent supporting and contrary spans with `doc_id`, offsets, quote hash, and optional segment/application refs.
- [ ] Code, application, perspective, relationship, synthesis, cross-case, negative-case, and GT outputs are represented as claims or explicit no-claim events.
- [x] Claims without anchors are visible as unsupported/needs-anchor; they are never silently treated as grounded.
- [ ] Negative cases are first-class claims and can link to the claim/code target they challenge.
- [ ] CLI/API/MCP/export surfaces expose claim counts by kind, stage, and adjudication/support status.
- [ ] Markdown and CSV exports include the claim ledger summary/details.
- [ ] Docs update INV-9 status precisely, without marking INV-6, INV-10, INV-2, or methodological validity as met.

Process criteria:

- [x] New targeted tests pass after each phase.
- [ ] `make check` passes before final completion.
- [ ] Plan tracker is updated as phases complete.
- [ ] Each verified phase is committed separately with `[Plan: INV9]`.
- [ ] Pre-existing `.claude/hook_log.jsonl` dirt is not staged or committed.

---

## Open Questions

- [ ] Should exhaustive thematic coding become default before public evaluation? — Status: DEFERRED | Why it matters: affects claim denominator semantics, but not required for first-class claim storage.
- [ ] Should human review mutate claims directly in this plan? — Status: DEFERRED | Why it matters: full claim adjudication is INV-10. This plan stores adjudication fields and read surfaces but does not need a full claim-review UI to close the first INV-9 slice.
- [ ] Should prompt schemas emit claims directly later? — Status: DEFERRED | Why it matters: direct LLM claim emission may improve completeness, but deterministic extraction from existing domain objects is the safer first slice.

---

## Notes

This plan intentionally closes the object-layer gap first. It does not claim
retrieval-first disconfirmation, expert validity, bias evaluation, or human
adjudication beyond code labels. Those become tractable only after the ledger
exists.

Phase 1 complete 2026-06-21: added the claim ledger schema,
`ProjectState.claims`, and a deterministic `summarize_claim_ledger()` helper.
Verification: `tests/test_claims.py` (5 passed),
`tests/test_domain_model.py tests/test_claims.py` (29 passed), and `make check`
(586 passed, 1 skipped, 8 deselected; Ruff/docs green).

Phase 2 complete 2026-06-21: added deterministic claim builders for code,
application, perspective, relationship, synthesis, cross-case, GT category,
GT proposition, and negative-case objects. Verification: `tests/test_claims.py`
(10 passed), focused affected set (75 passed), and `make check` (591 passed,
1 skipped, 8 deselected; Ruff/docs green).

Phase 3 complete 2026-06-21: wired claim recording into the default/thematic
pipeline stages (`thematic_coding`, `perspective`, `relationship`, `synthesis`,
`cross_interview`, `negative_case_analysis`) using replace-by-stage semantics so
reruns do not duplicate a stage's claims. Verification: `tests/test_claim_ledger_pipeline.py`
(6 passed), focused affected set (57 passed), and `make check` (597 passed,
1 skipped, 8 deselected; Ruff/docs green).
