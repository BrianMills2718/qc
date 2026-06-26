# Plan #241: SOTA Methodology And Pipeline Realignment

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** further default-path polish claims, sanitizer-first sequencing that ignores methodology alignment, major prompt/UX changes without a documented SOTA target

---

## Gap

**Current:** The repo has ambition, claim discipline, a stronger claim ledger,
and a more truthful graph than before, but it still lacks:

- a canonical document describing current state-of-the-art qualitative coding
  methodology and software;
- a clear account of how human labor bottlenecks distort qualitative rigor at
  scale;
- a canonical audit of prompt and dataflow surfaces;
- a sequenced program tying methodology documentation to prompt/code/UX
  improvements and fresh output critique.

**Target:** Establish a documented SOTA methodology frame, document labor
limitations and automation strategy, audit prompts/dataflow/docs/plans/code
against that frame, then implement the highest-value aligned changes and rerun
output critique.

**Why:** Without a shared methodology target and explicit audit trail, the repo
risks continuing to optimize strong local surfaces without converging on a
clearer answer to the harder product question: what would make this system
genuinely state-of-the-art rather than merely feature-rich?

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/METHODOLOGY.md`
- `docs/EVALUATION_HARNESS.md`
- `docs/LONG_TERM_EXECUTION_PLAN.md`
- `docs/plans/CLAIM_POSITION_METHODOLOGY_ALIGNMENT.md`
- `qc_clean/core/pipeline/pipeline_factory.py`
- `qc_clean/core/pipeline/pipeline_engine.py`
- `qc_clean/core/pipeline/stages/thematic_coding.py`
- `qc_clean/core/pipeline/stages/perspective.py`
- `qc_clean/core/pipeline/stages/cross_interview.py`
- `qc_clean/core/pipeline/stages/relationship.py`
- `qc_clean/core/pipeline/stages/negative_case.py`
- `qc_clean/core/claims.py`
- `qc_clean/core/prompt_override_registry.py`
- current local rerun4 packet and graph/review UX findings from 2026-06-25

---

## Research Basis For This Slice

This slice should use both:

- stable inherent qualitative-methodology knowledge for long-settled method
  distinctions;
- current primary sources for time-sensitive “state of the art” landscape
  claims.

The initial source set should include:

- current methodological references for thematic analysis and grounded theory;
- recent LLM/automation papers such as LLMCode and LOGOS;
- current CAQDAS product surfaces such as MAXQDA 26.2 segment-level AI coding.

---

## Operational Validation

**Classification:** default_path_visible_surface
**Surface IDs:** `review.claims_mode`, `graph.code_relationships_tab`, `export.markdown_report`
**Real-Run Requirement:** required

---

## Files Affected

- `docs/QUALITATIVE_CODING_SOTA_AND_AUTOMATION_STRATEGY.md` (create)
- `docs/PIPELINE_PROMPT_DATAFLOW_AUDIT.md` (create)
- `docs/METHODOLOGY.md` (modify if needed)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify if needed)
- `docs/LONG_TERM_EXECUTION_PLAN.md` (modify)
- `docs/plans/SOTA_METHODODOLOGY_PIPELINE_REALIGNMENT.md` (create)
- `docs/plans/CLAIM_POSITION_METHODOLOGY_ALIGNMENT.md` (complete/update)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- prompt/dataflow stage files under `qc_clean/core/pipeline/stages/` (follow-on)
- review/graph/export surfaces as justified by the audit (follow-on)
- tests and docs for any resulting implementation changes

---

## Plan

### Steps

1. Write canonical SOTA methodology documentation for qualitative coding,
   current software/research landscape, labor bottlenecks, and automation
   strategy.
2. Write a canonical prompt/dataflow audit with diagrams showing where codes,
   claims, relationships, and negative cases emerge.
3. Audit docs and plans for ambiguity, inconsistency, or sequencing mistakes
   against the new methodology frame.
4. Audit prompt surfaces and code paths against that frame; record concrete
   improvement opportunities.
5. Implement the highest-value aligned changes first, prioritizing default-path
   qualitative usefulness over surface expansion.
6. Rerun the affected workflow on the local seed, critique the resulting
   output, and record residual concerns plus advised next steps.

---

## Required Tests

### New Tests (TDD)

To be determined by the implementation sub-slice once concrete code changes are
selected.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `./.venv/bin/python scripts/sync_plan_status.py --check --validate-active` | Planning state must stay coherent. |
| `./.venv/bin/python scripts/check_surface_operational_readiness.py` | Active plan posture must remain valid. |
| `./.venv/bin/python scripts/check_markdown_links.py` | Canonical docs and plan references must remain intact. |
| `./.venv/bin/python -m ruff check .` | Lint gate for follow-on code changes. |
| relevant focused pytest targets | Follow-on code changes must add or update coverage. |
| `git diff --check` | Patch hygiene. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Canonical docs clearly describe SOTA qualitative coding methodology and
  the current software/research landscape.
- [ ] Canonical docs clearly describe how human labor bottlenecks hobble
  qualitative rigor and how automation can overcome those constraints.
- [ ] The repo has a prompt/dataflow audit with diagrams that map actual code
  paths to analytic objects.
- [ ] Docs and plans are aligned and unambiguous about the next implementation
  target.
- [ ] At least one high-value methodology-aligned implementation change is made
  and verified on a fresh local rerun.
- [ ] The resulting output is critiqued explicitly rather than merely generated.

> Process criteria:
- [ ] Findings are documented at each major step.
- [ ] Governance checks pass.
- [ ] The final worktree state is committed and pushed.

---

## Notes

This slice is intentionally broader than a prompt-only patch. It should not
skip from “we need SOTA” to ad hoc coding changes without first making the
target methodology, labor model, and dataflow weaknesses explicit.

Implementation checkpoint on 2026-06-25: the first selected low-disruption
change was to make participant-level position statements first-class in the
perspective path. `ParticipantProfile` / `ParticipantPerspective` now carry
`position_statements`, the perspective prompt now asks for stance-bearing
assertions rather than only summaries/themes, adapters preserve them into
domain state, and `claims_for_perspectives()` now emits participant-position
claims into the claim ledger. Focused tests and lint passed. A copied local
project-store replay was started to inspect real output, but did not finish
within the current increment; live output critique remains pending.

Implementation checkpoint on 2026-06-26: the reviewer-visible contract for the
position-bearing perspective work is now more complete. Markdown participant
perspective export and API summary payloads now expose participant
`position_statements` directly, rather than only `perspective_summary`.
Additionally, `cross_interview` now promotes perspective-stage
`consensus_themes` and `divergent_viewpoints` into first-class descriptive
`ObservedPattern` rows (`perspective_consensus`, `perspective_divergence`) plus
supported cross-case claims such as "Participants converge on the position..."
and "Participants diverge on the position...". Focused tests, Ruff, and patch
hygiene passed.

Replay/critique checkpoint on 2026-06-26: the copied replay artifact under
`test_output/plan241_position_claims_replay_2026_06_25/` was deterministically
refreshed by re-running only the local `cross_interview` stage over the copied
project store and regenerating `report.md`. This was not a fresh end-to-end
live LLM rerun, so it should not be framed as full pipeline revalidation.
However, it was sufficient to confirm two concrete product improvements:

- the `## Participant Perspectives` section now shows bounded position
  statements for each participant, not just prose summaries;
- the report now includes explicit `Perspective Consensus` and
  `Perspective Divergence` sections, and the observed-pattern / claim-ledger
  surfaces now carry those position-aware cross-interview rows.

Residual critique after the deterministic replay refresh:

- reviewer usefulness is materially better because positions and cross-speaker
  divergences are now visible without digging through raw JSON;
- but the default path still remains structurally code-first because
  cross-interview perspective outputs still mirror earlier perspective-stage
  abstractions rather than extracting claim-to-claim relations directly;
- a future full live rerun is still warranted before treating this slice as
  fully operational on real output;
- the next structural target should be claim/stance relation modeling
  (speaker-to-claim, claim-to-claim support/tension, or equivalent), not more
  code-co-occurrence polish.

Implementation checkpoint on 2026-06-26 (follow-on): the repo now has a narrow
first-class claim-relationship substrate. Participant-level perspective claims
and participant position claims are linked deterministically through
`elaborates` relationships, and cross-interview perspective-consensus /
perspective-divergence claims now link back to participant perspective claims
through `synthesizes` and `contrasts` relationships. Markdown export now
includes a `## Claim Relationships` section, and the copied replay artifact was
refreshed to confirm that the report shows 33 relationship rows
(`elaborates=12`, `synthesizes=12`, `contrasts=9`).

Critique of this follow-on checkpoint:

- this is a real improvement over a flat claim ledger because reviewers can now
  inspect how higher-order cross-interview claims relate to participant-level
  position claims;
- but the relation layer is still narrow and deterministic, not a rich semantic
  support/contradiction engine;
- cross-interview divergence claims currently relate to all participant
  perspective claims in scope rather than a finer-grained rivalry mapping, so
  the relation layer is useful but still coarse;
- the next unambiguous target remains a richer claim/stance graph or relation
  model, ideally with more selective claim-to-claim links and reviewer-facing
  visualization.

Next-week execution track opened on 2026-06-26:

1. Add read surfaces for the new claim-relationship substrate so reviewers can
   inspect claim links directly through CLI/API, not only Markdown export.
2. Refresh the copied replay artifact and confirm the claim-relationship
   section is reviewer-meaningful rather than only structurally populated.
3. Tighten deterministic relation generation so divergence links are more
   selective than "all in-scope participant claims" where possible.
4. Decide whether the next larger slice should be:
   - reviewer-facing stance/claim graph visualization, or
   - finer claim-to-claim relation modeling first.
5. Preserve honest framing throughout: deterministic claim relationships are a
   useful substrate, not yet a full semantic stance graph.

Implementation checkpoint on 2026-06-26 (read surfaces): the new
claim-relationship substrate is now inspectable through both CLI and API read
surfaces. `qc_cli.py project claim-relationships <project_id>` and
`/projects/{project_id}/claim-relationships` now expose bounded rows plus
relationship-count summaries. Focused tests passed for:

- CLI command rendering;
- API endpoint paging/bounding behavior;
- Markdown export claim-relationship rendering;
- incremental invalidation of stale claim relationships.

Replay critique after this checkpoint:

- the copied replay artifact's `## Claim Relationships` section is genuinely
  useful for auditability because it shows how participant-position claims,
  participant-perspective claims, and cross-interview synthesis/divergence
  claims connect;
- the relation layer is still coarse because divergence links remain
  scope-wide rather than selectively mapped to only the most directly opposed
  participant claims;
- the next higher-value target is therefore not merely "more read surfaces" but
  sharper relation selectivity and, after that, a stance/claim graph view.

Implementation checkpoint on 2026-06-26 (relation selectivity): divergence /
contrast claim relationships are now more selective. Instead of linking each
cross-interview divergence claim to every participant perspective claim in
scope, deterministic alias matching now narrows links using participant names
and role tokens mentioned in the divergence text, with a scope-wide fallback
only when no alias is detectable. On the copied replay artifact this reduced
`contrasts` rows from 9 to 6 and total claim-relationship rows from 33 to 30,
which is a materially better fit to the actual divergence descriptions.

Critique after the selectivity checkpoint:

- this is still not semantic contradiction detection; it is bounded string/role
  alias matching over already-produced divergence text;
- but it is a real improvement in reviewer honesty because the relation table
  no longer implies that every divergence claim equally contrasts with every
  participant perspective in scope;
- the next unambiguous target remains a reviewer-facing stance/claim graph or a
  more selective participant-position linking rule for consensus claims.

Implementation checkpoint on 2026-06-26 (claim graph surface): the repo now has
a reviewer-visible claim graph surface. `/projects/{project_id}/graph/claims`
returns claim nodes plus deterministic `elaborates` / `synthesizes` /
`contrasts` edges, and the browser graph UI now exposes a `Claim Graph` tab
alongside Code Hierarchy, Code Relationships, and Entity Map. Focused graph API
tests passed.

Replay critique after the claim-graph checkpoint:

- the copied replay now yields a nontrivial claim graph with 22 nodes and 30
  edges, which is enough to count as a meaningful reviewer-visible stance-map
  substrate rather than a placeholder surface;
- the graph is still deterministic and partial: it covers perspective-derived
  claims and cross-interview synthesis/divergence links, not the full claim
  ledger;
- this is therefore a real product milestone, but not yet a full semantic
  claims graph.
