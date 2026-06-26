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

> Finished-product criteria (outer gate; no slice may close the whole product
> unless these pass):
- [ ] The default workflow can take a real multi-document corpus from ingest to
  reviewer-ready export through a documented, repeatable command/API path, with
  no manual state surgery and no ignored local-only artifacts required.
- [ ] Every default-path reviewer-facing analytic claim is represented as a
  first-class claim object with explicit scope, source-stage provenance,
  support status, and source-span anchors or a local `needs_anchor`/unsupported
  label at the point where the claim appears.
- [ ] Every default-path code application and quoted evidence item resolves to
  a verifiable source span, or is dropped/flagged with stage-level provenance
  and an auditable remediation path; unanchored quote candidates are not merely
  summarized as acceptable residual noise.
- [ ] Exhaustive segment coverage is available on the default reviewer path, or
  the default path explicitly avoids prevalence/coverage language that depends
  on an exhaustive denominator.
- [ ] Disconfirmation is evaluated against the final claim set with a validated
  retrieval/reviewer policy and held-out D7 evidence; absence of found negative
  cases is not presented as proof until that gate passes.
- [ ] Human/agent review covers code applications, claims, relationships,
  negative cases, recommendations, and provisional abductive candidates through
  an agent-drivable workflow with importable decisions and audit history.
- [ ] Reviewer and audit exports are separate products: reviewer exports are
  coherent, non-duplicative, locally caveated, and publish-preflightable; audit
  exports preserve full memo/history/claim/retrieval/provenance detail.
- [ ] Baseline comparisons against direct transcript-to-report, QA-report, and
  relevant commercial/research baselines are reproducible from versioned
  artifacts, not chat-only observations.
- [ ] The evaluation harness has populated evidence, not only protocol
  substrate, for D1-D10 where claimed; product claims are licensed only for
  dimensions whose confidence intervals clear the registered baseline/human
  ceiling.
- [ ] Expert/adjudicator review packages exist and have completed responses for
  codebook quality, application validity, disconfirmation, interpretive
  preference, bias, sampling-frame adequacy, and GT fidelity where those claims
  are made.
- [ ] Prompt-injection and untrusted-data boundaries are validated on a frozen,
  independently curated live suite across the supported model/provider set; no
  robustness claim is made from structural fixtures alone.
- [ ] Incremental corpus mutation cannot leave stale higher-order outputs in the
  reviewer path; default refresh/invalidation policy is live-validated and
  documented.
- [ ] The product has an operator-ready surface: CLI/API/UI paths are documented,
  smoke-tested on a clean environment, and expose every human-visible operation
  through an agent-drivable interface.
- [ ] Observability and auditability are production-ready: LLM traces, costs,
  artifact hashes, export manifests, event logs, and verification commands are
  generated and checked as part of the normal handoff path.
- [ ] A fresh end-to-end benchmark run on a held-out corpus passes the registered
  product gate, produces reviewer/audit artifacts, runs baseline comparisons,
  imports review/adjudication responses, and leaves a clean committed benchmark
  package.

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

Implementation checkpoint on 2026-06-26 (graph inspectability): the graph UI
now supports edge-level detail inspection, including claim-relationship
rationales. Reviewers can click claim-graph edges to inspect relation type,
source/target IDs, and deterministic rationale, rather than only seeing an
undifferentiated visual edge. Focused graph tests passed.

Critique after the inspectability checkpoint:

- this materially improves reviewer utility because the claim graph is no
  longer only a visual topology; it now exposes why a link exists;
- but the UI still displays raw source/target claim IDs for edge details rather
  than humanized source/target labels, so one further polish step remains if we
  keep investing in this surface;
- the larger remaining gap is still semantic breadth, not basic inspectability.

Implementation checkpoint on 2026-06-26 (humanized claim-edge detail): the
claim-graph API and browser UI now expose human-readable source/target labels
for claim-relationship edges, along with full source/target claim text in the
detail panel. This preserves deterministic graph scope while removing the need
for reviewers to cross-reference opaque claim IDs manually. Focused graph API
tests, Ruff, and copied-replay verification passed.

Replay critique after the humanized-edge checkpoint:

- the copied replay claim graph still yields 22 nodes and 30 edges, so the
  underlying deterministic relation structure is unchanged by this UI/API
  improvement;
- reviewer usability is materially better because edge inspection now shows
  readable claim summaries and full source/target claim text rather than only
  internal IDs;
- the next-week queue for the current claim-graph surface is now effectively
  exhausted: the main remaining gap is semantic breadth/selectivity, not basic
  reviewer readability.

Output-audit checkpoint on 2026-06-26 (report authoritativeness failure): the
copied replay report is now materially richer than before, but the export still
fails a core reviewer contract. A single final report currently contains
multiple competing cross-interview analyses with conflicting prevalence facts
for the same themes/codes (for example, one section reports local
actors/diaspora as `2/3` while a later section reports the same theme as `3/3`;
one section reports nature-of-threats as `1/3` divergent while a later section
reports it as `2/3` consensus). This is not merely interpretive variation; it
is incompatible reported analysis state inside one artifact.

Implications of this audit finding:

- the current default-path problem is no longer only "claims/positions are too
  hidden"; it is also "the final report is not authoritative";
- the traced failure mode is export composition: historical `cross_case` memo
  layers and newer structured cross-interview outputs were rendered side by
  side without a reviewer-report supersession rule;
- recommendation prose currently reads more settled than the local evidence
  status warrants, because the report combines strong executive prose with
  `needs_anchor` material and duplicated analytic layers.

High-confidence remediation path recorded from this audit:

1. Define one canonical final-analysis object for each main report section,
   especially cross-interview analysis.
2. Render only that canonical object in the reviewer report; move draft,
   challenge, and superseded memo layers to appendix/debug/audit exports.
3. Add export-time contradiction checks so a final report fails loudly if the
   same code/theme family appears with incompatible prevalence labels.
4. Integrate negative-case output by revising or qualifying final findings,
   rather than letting it appear as a peer competing truth layer.
5. Split reviewer-facing and audit-facing artifacts more cleanly so the main
   report gives one authoritative answer and the audit export preserves full
   traceability.

Baseline-comparison track opened from the same audit:

- We should not assume the structured pipeline is winning merely because it is
  more elaborate. Add two explicit comparison baselines against the same corpus:
  1. a direct-report baseline where an LLM receives the transcripts plus a fair
     analytic brief and writes a qualitative report;
  2. a QA-report baseline where an LLM receives the transcripts plus a fixed
     question set, answers each question with evidence/uncertainty, and then
     optionally synthesizes those answers into a short report.

Baseline evaluation should compare at least:

- internal consistency;
- evidence grounding / quote traceability;
- handling of participant disagreement and boundary conditions;
- scope discipline and caveating;
- recommendation traceability;
- reviewer usefulness / readability;
- auditability.

Expected use of this baseline track:

- determine whether the current structured pipeline is genuinely outperforming
  simpler transcript-to-report workflows;
- identify whether the main current weakness is extraction quality,
  synthesis/report composition quality, or both;
- provide a fair external comparator before further architecture expansion.

Recommended implementation order for the baseline track:

1. define fair prompt specs for the direct-report and QA-report baselines;
2. define a scoring rubric and artifact schema for side-by-side comparison;
3. run both baselines on the same bounded local seed corpus;
4. compare them directly to the current exported report;
5. use that evidence to prioritize either report-authoritativeness/export fixes
   or deeper extraction/claim-model redesign.

Implementation checkpoint on 2026-06-26 (baseline substrate): the repo now has
a first runnable transcript-to-report baseline export surface. `scripts/run_report_baselines.py`
and `qc_cli.py run-report-baselines <project_id>` can generate a versioned
baseline package in two modes:

- `direct_report`: transcripts plus a fair reviewer-facing analytic brief;
- `qa_report`: transcripts plus a fixed reviewer question set, with synthesized
  report output.

Current command surface:

- `python qc_cli.py run-report-baselines <project_id> --output report_baselines.json`
- optional `--mode direct_report --mode qa_report`
- optional `--projects-dir path`
- optional `--model <model>`
- optional `--max-chars-per-doc N`

Current scope/limitations of this substrate:

- it is transcript-only by design and intentionally does not consume the repo's
  derived codes, claims, or memos;
- it is a generation/provenance surface, not yet a scored benchmark;
- it creates a versioned comparison artifact so the same corpus can be compared
  against the current structured report;
- no baseline run has yet been committed/evaluated on the copied seed in this
  slice, so no comparative conclusion is licensed yet.

Baseline run checkpoint on 2026-06-26 (copied seed): both transcript-only
baselines were executed against the copied Plan 234 seed project and written to
`test_output/plan241_position_claims_replay_2026_06_25/report_baselines.json`.

Early comparison result from that run:

- both baselines produced cleaner, more internally coherent reviewer prose than
  the current structured export because they give one answer rather than
  multiple competing cross-interview sections;
- both baselines preserved key substantive content already visible in the seed
  corpus: local + strategic actors, media-literacy responses, operational harms,
  capacity gaps, and sovereignty/attribution tensions;
- neither baseline matches the structured system's auditability or object-level
  trace substrate (claim ledger, claim relationships, observed patterns,
  reviewer-visible position statements);
- this comparison increases confidence that the current highest-value fix is
  report composition/authoritativeness, not merely extracting more objects.

Continuous-run completion contract opened on 2026-06-26:

This run is complete only when the repo has a verified, reviewed, commit-ready
implementation slice for the baseline + reviewer-report-authoritativeness
program. The concrete success criteria are:

- baseline generation remains runnable through
  `qc_cli.py run-report-baselines` and covered by focused tests;
- side-by-side report comparison remains runnable through
  `qc_cli.py compare-report-baselines` and covered by focused tests;
- comparison artifacts score structured reports and transcript baselines on
  internal consistency, evidence grounding, disagreement handling, scope
  discipline, recommendation traceability, reviewer usefulness, and
  auditability;
- reviewer Markdown no longer renders superseded historical `cross_case` memo
  accumulation as final peer analysis;
- memo history remains available through audit/state/CSV surfaces;
- export tests prove both the diagnosed failure mode and the intended
  reviewer-report contract;
- the plan and progress file record that this slice removes stale cross-case
  memo duplication from reviewer Markdown but does not claim full semantic
  contradiction detection;
- focused pytest targets, Ruff for touched Python files, plan/governance
  checks, Markdown-link checks, surface-readiness checks, and `git diff
  --check` pass;
- the final diff is reviewed and remaining risks are recorded before the
  worktree is declared complete.

Progress file for this continuous run:
`.claude/tasks/report_authoritativeness_continuous_run.md`.

Implementation checkpoint on 2026-06-26 (reviewer Markdown memo
authoritativeness): the Markdown exporter now treats `ProjectState.memos` as
audit history rather than blindly rendering every historical `cross_case` memo
as final peer analysis. For reviewer Markdown only, it keeps the latest
`cross_case` memo per stable title/family, leaves other memo types untouched,
and emits an explicit note when superseded cross-case memos are omitted. CSV
export still preserves full memo history.

Focused regression coverage now proves:

- superseded `cross_case` memo history is omitted from Markdown while current
  structured observed patterns remain visible;
- repeated non-`cross_case` memos with the same title are still rendered, so
  the fix is scoped to the diagnosed failure mode;
- CSV memo export preserves historical `cross_case` memos for audit.

Copied-seed replay verification: regenerating
`test_output/plan241_position_claims_replay_2026_06_25/report.md` from the
local copied project store now yields one `### Cross-Interview Pattern
Analysis` memo and an explicit note that two superseded cross-case memos were
omitted from the reviewer report.

Residual limitation: this checkpoint prevents stale cross-case memo
accumulation from creating incompatible prevalence facts in the reviewer
Markdown. It does not yet implement a general semantic contradiction detector
for all possible prose claims or negative-case critique text.

Implementation checkpoint on 2026-06-26 (report-baseline comparison scoring):
the repo now has a deterministic side-by-side comparison surface for the
structured reviewer report and transcript-only baselines. `scripts/compare_report_baselines.py`
and `qc_cli.py compare-report-baselines <report.md> <report_baselines.json>`
write a versioned comparison package with rubric dimensions for:

- internal consistency;
- evidence grounding;
- disagreement handling;
- scope discipline;
- recommendation traceability;
- reviewer usefulness;
- auditability.

This scorer is intentionally heuristic and transparent. It uses deterministic
signals such as conflicting prevalence-count labels, quote/table/claim-ID
signals, consensus/divergence mentions, scope/caveat markers, and audit-surface
signals. It is a triage readout, not human adjudication, held-out evidence, or
proof that one report is superior.

Copied-seed scoring checkpoint: running
`qc_cli.py compare-report-baselines` over the copied seed structured report and
`report_baselines.json` wrote an ignored local
`test_output/plan241_position_claims_replay_2026_06_25/report_baseline_comparison.json`
artifact. The deterministic readout ranked:

1. `structured_report` (`overall_score=0.957`)
2. `transcript_direct_report` (`overall_score=0.446`)
3. `transcript_qa_report` (`overall_score=0.435`)

Interpretation of that readout:

- after the Markdown memo-authoritativeness fix, the structured report no
  longer shows the earlier stale prevalence-count conflict under the heuristic
  detector;
- the structured report dominates auditability/evidence-signal dimensions
  because it carries claim IDs, tables, observed patterns, and relationship
  surfaces;
- the baselines remain much shorter and cleaner to read, but score weakly on
  auditability and explicit evidence/claim trace signals;
- this still does not license a SOTA or superiority claim because the scorer is
  deterministic instrumentation, not an adjudicated reviewer preference study.

Implementation checkpoint on 2026-06-26 (export-time prevalence conflict gate):
the reviewer Markdown exporter now reuses the same prevalence-conflict detector
as the comparison scorer and fails loudly before writing if the final Markdown
contains incompatible `present/appears in X/Y documents` facts for the same
normalized theme/code label. This is the hard gate counterpart to the
post-export comparison readout.

Focused coverage proves:

- the detector catches the original Markdown form
  `**Theme**: present in 2/3 documents` versus `**Theme**: present in 3/3 documents`;
- consistent repeated prevalence counts do not trip the gate;
- Markdown export raises `ValueError` and writes no file when two live
  cross-case memo families still create a conflicting prevalence fact.

Copied-seed verification: the fixed copied seed report still exports cleanly
under the new gate, confirming the earlier memo-authoritativeness fix resolved
the stale cross-case prevalence conflict for that artifact.

Implementation checkpoint on 2026-06-26 (recommendation traceability and local
support gating): reviewer Markdown recommendations now include local evidence
context instead of standing as unsupported action prose. For each synthesis
recommendation, export looks for the matching `synthesis_recommendation` claim
ledger entry (`recommendation:<index>`) and renders:

- evidence/support status;
- trace claim ID(s);
- supporting and contrary anchor counts;
- supporting themes.

If no matching recommendation claim exists, the report says so locally and
instructs reviewers to treat the recommendation as unverified until claims are
generated. This preserves the distinction between plausible advice and
grounded/traced analytic recommendation.

Copied-seed verification: regenerating the copied seed report now shows every
recommendation with `Evidence status: supported`, a trace claim ID, supporting
anchor counts, and supporting themes. This closes the immediate reviewer-facing
gap where recommendation prose read more settled than the evidence trail.

Implementation checkpoint on 2026-06-26 (Markdown reviewer/full profile split):
Markdown export now has an explicit profile:

- `markdown_profile="full"` / `--markdown-profile full` preserves the existing
  audit-heavy Markdown report and remains the default for backward
  compatibility;
- `markdown_profile="reviewer"` / `--markdown-profile reviewer` renders a
  cleaner reviewer-facing report that omits audit-heavy sections such as full
  key quotes, analytical memo history, claim ledger, claim relationships, and
  observed-pattern tables.

Reviewer profile keeps the latest cross-interview analysis, participant
perspectives, entity relationships, recommendations, and local recommendation
evidence status/trace lines. The full profile remains the audit surface.

Copied-seed verification: exporting the copied seed with
`--markdown-profile reviewer` produced `reviewer_report.md` with corpus scope,
executive summary, codebook, latest cross-interview analysis, participant
perspectives, entity relationships, recommendation evidence status, and
pipeline phases, while omitting `Key Quotes`, `Analytical Memos`, `Claim
Ledger`, and `Observed Patterns`.

Reviewer-profile comparison checkpoint: running
`qc_cli.py compare-report-baselines` on the copied seed `reviewer_report.md`
and the transcript-only baseline package produced an ignored local
`reviewer_report_baseline_comparison.json`. The heuristic readout showed:

- reviewer-profile structured report: `word_count=2705`,
  `overall_score=0.845`, `prevalence_conflict_count=0`;
- direct transcript baseline: `word_count=606`, `overall_score=0.446`;
- QA transcript baseline: `word_count=386`, `overall_score=0.435`.

This is the fairer comparison artifact for reviewer usability than the full
audit Markdown. It shows the structured report can be made substantially less
dense while retaining enough trace/audit signal to beat the simple baselines
under the deterministic rubric. It still does not replace human preference
review or expert adjudication.

Implementation checkpoint on 2026-06-26 (report review packet): the repo now
has a human/agent adjudication packet for report comparison. `scripts/write_report_review_packet.py`
and `qc_cli.py write-report-review-packet <reviewer_report.md>
<report_baselines.json>` write a versioned packet containing:

- the structured reviewer report;
- direct-report and QA-report baseline Markdown;
- fixed rubric questions for internal consistency, evidence grounding,
  disagreement handling, scope discipline, recommendation traceability,
  reviewer usefulness, and auditability;
- response instructions for 1-5 scores, evidence notes, overall ranking, and
  unsupported/contradictory/over-scoped claim flags.

This makes the next evaluation step agent-drivable and reviewable without
pretending the deterministic scorer is the final judge. Copied-seed verification
wrote an ignored local `report_review_packet.json` containing the reviewer
report, both transcript baselines, and all rubric dimensions.

Implementation checkpoint on 2026-06-26 (agent report review response): the repo
now has a structured agent-review response workflow for report review packets.
`scripts/run_report_review.py` and `qc_cli.py run-report-review
<report_review_packet.json>` call `llm_client` with schema-validated output and
write a versioned `qualitative_coding.report_review_response` package.

Copied-seed live review: running `gpt-5-mini` over the copied seed review packet
wrote an ignored local `report_review_response.json`. The agent reviewer ranked:

1. `structured_report`
2. `transcript_qa_report`
3. `transcript_direct_report`

The comparative summary judged the structured reviewer report most useful
because it is anchored with claim IDs and anchor counts, while the QA baseline
is a stronger simple baseline than the direct report due to concrete examples.
Residual concerns recorded by the reviewer:

- dropped/unanchored quotes still reduce confidence that all relevant evidence
  was preserved;
- the three-transcript seed limits generalizability across all artifacts;
- numeric confidences and codebook counts need clearer derivation to avoid
  being misread as precise measures.

Implementation checkpoint on 2026-06-26 (codebook count/confidence caveat):
reviewer and full Markdown exports now state locally in the Codebook section
that mention counts and confidence values are local pipeline signals for the
loaded corpus, not validated prevalence estimates or methodological-certainty
measures. This directly addresses one residual concern from the agent review
without pretending the metrics are more rigorous than they are.

Implementation checkpoint on 2026-06-26 (grounding warning clarity): Markdown
exports now summarize repeated dropped-quote grounding warnings before listing
the raw warnings. The copied-seed reviewer report now states that 13 quote
candidates matched no source document across 2 grounding warning events, while
37 anchored code applications remain available for audit. This does not hide
evidence loss; it makes the warning interpretable and distinguishes dropped
quote candidates from retained anchored evidence.

Implementation checkpoint on 2026-06-26 (review-scope and local-signal
caveats): report review packets now prepend a common review-scope notice to
every artifact, including both transcript-only baselines. Reviewer Markdown now
adds local caveats that attribution statements and external-event references are
participant-reported unless separately verified, cross-interview X/3 and
strength values are loaded-corpus occurrence summaries, and entity relationship
strengths are local analytic confidence signals rather than validated causal
weights. Future default thematic dropped-quote warnings now include `Thematic
coding:` provenance.

Final copied-seed live review on 2026-06-26: after regenerating
`reviewer_report.md`, `report_review_packet.json`, and
`report_review_response.json`, the `gpt-5-mini` reviewer again ranked:

1. `structured_report`
2. `transcript_qa_report`
3. `transcript_direct_report`

The structured report scored 5 overall, with 5/5 internal consistency,
disagreement handling, scope discipline, recommendation traceability, and
reviewer usefulness; evidence grounding and auditability remained 4/5 because
13 quote candidates were not source-anchored. Remaining concerns are now
recorded as real limitations rather than report-composition defects:

- unanchored quote candidates need source-level remediation or re-extraction;
- the three-document local seed is not representative;
- sensitive, classified, or external-reference claims are not independently
  verified inside these artifacts.

Product-gate implementation checkpoint on 2026-06-26 (grounding issue ledger):
default thematic coding now persists dropped quote candidates as first-class
`GroundingIssue` records with stage provenance, code ID, quote text, match
status, occurrence count, and remediation guidance. CSV export writes
`grounding_issues.csv` when issues exist, and Markdown export renders a
`Grounding Issues` table before analytic conclusions. Historical states that
only contain count-based grounding warnings now render an explicit
`Grounding issue ledger unavailable` notice instructing operators to rerun
coding to capture quote-level remediation records. This is the first product
gate slice for the criterion that unanchored evidence cannot remain merely a
counted residual.
