# Implementation Plans

Track all implementation work here.

## Active Plans

| # | Name | Priority | Status | Plan doc |
|---|------|----------|--------|----------|

## Completed Plans

| Name | Outcome | Record |
|------|---------|--------|
| INV-1 span anchoring + harness Phase 0 | INV-1 mostly met; `make bench` Phase 0 stood up | `completed/INV1_OVERNIGHT_SPRINT.md` |
| INV-8 segment universe + exhaustive coding | INV-8 met in exhaustive mode (`--exhaustive`); coverage denominator | `completed/INV8_SEGMENT_UNIVERSE.md` |
| Application-level IRR | `project irr --application-level` reports positive segment x code agreement plus segment-decision agreement | `completed/IRR_APPLICATION_LEVEL.md` |
| INV-9 first-class claim ledger | INV-9 object layer mostly met; claims emitted/read across stages and surfaces | `completed/INV9_CLAIM_LEDGER.md` |
| INV-6 ledger-wide disconfirmation and claim review | INV-6/INV-10 first slice: negative-case targets claim ledger IDs; claim review decisions supported | `completed/INV6_LEDGER_DISCONFIRMATION.md` |
| INV-7 instruction/data separation | INV-7 first slice: raw transcript/segment prompt data is line-prefixed as untrusted; prompt-injection regressions added | `completed/INV7_INSTRUCTION_DATA_SEPARATION.md` |
| INV-2 retrieval-first disconfirmation | INV-2 first slice: negative-case analysis retrieves anchored candidate passages before LLM interpretation | `completed/INV2_RETRIEVAL_FIRST_DISCONFIRMATION.md` |
| INV-2 adversarial disconfirmation model routing | INV-2 follow-up: configurable disconfirmation model override and adversarial evidence-bound prompt stance | `completed/INV2_ADVERSARIAL_DISCONFIRMATION_MODEL.md` |
| INV-7 derived-output prompt boundaries | INV-7 follow-up: downstream LLM/codebook artifacts are also line-prefixed as untrusted data | `completed/INV7_DERIVED_OUTPUT_PROMPT_BOUNDARIES.md` |
| INV-2 D7 disconfirmation scorecard | Evaluation-harness follow-up: `make bench` reports exact-anchor D7 recall/precision/F1 when adjudicated contrary-evidence gold is supplied | `completed/INV2_D7_DISCONFIRMATION_SCORECARD.md` |
| INV-2 BM25 disconfirmation retrieval | INV-2 follow-up: disconfirmation candidate retrieval uses configurable BM25-style lexical scoring plus contrary-cue boosts | `completed/INV2_BM25_DISCONFIRMATION_RETRIEVAL.md` |
| INV-2 D7 gold file bench input | Evaluation-harness follow-up: `make bench ID=<project> GOLD=gold.json` feeds external D7 gold without mutating project state | `completed/INV2_D7_GOLD_FILE_BENCH_INPUT.md` |
| INV-7 prompt override guards | INV-7 follow-up: current prompt override surfaces fail loudly if required protected data placeholders are omitted | `completed/INV7_PROMPT_OVERRIDE_GUARDS.md` |
| INV-7 strict prompt override placeholders | INV-7 follow-up: current prompt override surfaces require bare declared placeholders and reject transformed protected data or undeclared metadata placeholders before LLM calls | `completed/INV7_STRICT_PROMPT_OVERRIDE_PLACEHOLDERS.md` |
| INV-7 prompt-injection package | INV-7 follow-up: structural and live fixture outputs now have a schema_version=1 package contract, validator, and Phase 0 loader support without claiming robustness evidence | `completed/INV7_PROMPT_INJECTION_PACKAGE.md` |
| INV-4 category saturation diagnostic | INV-4 first slice: `make bench` reports diagnostic-only category property/dimension/support adequacy separately from codebook stability | `completed/INV4_CATEGORY_SATURATION_DIAGNOSTIC.md` |
| INV-4 diagnostic-driven theoretical sampling | INV-4 follow-up: sampling suggestions use category adequacy gaps before falling back to low application coverage | `completed/INV4_DIAGNOSTIC_THEORETICAL_SAMPLING.md` |
| Corpus scope contract | Report-boundary first slice: optional `ProjectState.corpus_scope` records scope and Markdown export surfaces it before claims | `completed/CORPUS_SCOPE_CONTRACT.md` |
| INV-2 query-expansion disconfirmation retrieval | INV-2 follow-up: BM25-style retrieval can use weighted deterministic query-expansion terms while preserving exact candidate anchors | `completed/INV2_QUERY_EXPANSION_DISCONFIRMATION_RETRIEVAL.md` |
| INV-2 embedding-hybrid disconfirmation retrieval | INV-2 follow-up: opt-in embedding-hybrid retrieval can add embedding cosine similarity while preserving the lexical default and exact anchors | `completed/INV2_EMBEDDING_HYBRID_DISCONFIRMATION_RETRIEVAL.md` |
| D7 Wilson intervals | Evaluation-harness follow-up: gold-dependent D7 recall/precision now include 95% Wilson intervals in `make bench` | `completed/D7_WILSON_INTERVALS.md` |
| Corpus scope CLI/API surfaces | Scope contract follow-up: `project scope` and `/projects/{id}/scope` read/update `ProjectState.corpus_scope` | `completed/CORPUS_SCOPE_CLI_API.md` |
| Missing corpus scope report warning | Scope/report follow-up: Markdown claim reports without corpus scope now warn not to generalize beyond loaded documents | `completed/CORPUS_SCOPE_MISSING_REPORT_WARNING.md` |
| Corpus scope machine-readable warnings | Scope/report follow-up: JSON/CSV claim exports without corpus scope now carry missing-scope warning metadata | `completed/CORPUS_SCOPE_MACHINE_READABLE_WARNINGS.md` |
| Corpus scope create surfaces | Scope contract follow-up: CLI/MCP project creation can persist corpus scope when supplied while no-scope creation remains compatible | `completed/CORPUS_SCOPE_CREATE_SURFACES.md` |
| Corpus scope completeness warnings | Scope/report follow-up: claim-bearing exports warn on empty scope records and population-without-sampling-frame metadata | `completed/CORPUS_SCOPE_COMPLETENESS_WARNINGS.md` |
| Scope-bound claim export rows | Scope/report follow-up: CSV/Markdown claim rows carry per-row claim scope and corpus boundary context without rewriting claim text | `completed/SCOPE_BOUND_CLAIM_EXPORT_ROWS.md` |
| Claim review API listing | INV-10 follow-up: `/projects/{id}/review/claims` exposes bounded claim review targets and claim decisions are covered through the review API | `completed/CLAIM_REVIEW_API_LISTING.md` |
| Claim review browser UI | INV-10 follow-up: browser review page now has a Claims mode that lists claim cards and submits claim approve/reject/modify decisions | `completed/CLAIM_REVIEW_BROWSER_UI.md` |
| Relationship review API decisions | INV-10 follow-up: `/projects/{id}/review/relationships` and ReviewManager support code/entity relationship review decisions | `completed/RELATIONSHIP_REVIEW_API_DECISIONS.md` |
| MCP claim review decisions | INV-10 follow-up: `qc_review_decisions` applies generic review decisions including claim targets with preserved rationale | `completed/MCP_CLAIM_REVIEW_DECISIONS.md` |
| MCP claim review listing | INV-10 follow-up: `qc_review_claims` exposes bounded claim review targets for agent-driven review workflows | `completed/MCP_CLAIM_REVIEW_LISTING.md` |
| MCP relationship review | INV-10 follow-up: `qc_review_relationships` exposes bounded code/entity relationship review targets for agent-driven review workflows | `completed/MCP_RELATIONSHIP_REVIEW.md` |
| Relationship review browser UI | INV-10 follow-up: browser review page now has a Relationships mode for code/entity relationship decisions | `completed/RELATIONSHIP_REVIEW_BROWSER_UI.md` |
| Negative case review surfaces | INV-10 follow-up: API/MCP/browser surfaces expose bounded negative-case claim rows while decisions keep `target_type="claim"` | `completed/NEGATIVE_CASE_REVIEW_SURFACES.md` |
| INV-7 prompt injection scorecard | Evaluation-harness follow-up: `make bench` can score externally supplied prompt-injection fixture outcomes without mutating project state | `completed/INV7_PROMPT_INJECTION_SCORECARD.md` |
| INV-11 incremental hard invalidation | Incremental recode now clears stale higher-order outputs, stale phase results, and stale claim rows it cannot recompute | `completed/INV11_INCREMENTAL_HARD_INVALIDATION.md` |
| INV-11 review decisions inactive on invalidation | Review decisions targeting claims removed by incremental invalidation are retained as inactive audit history | `completed/INV11_REVIEW_DECISION_INACTIVE_ON_INVALIDATION.md` |
| INV-11 narrow surface warnings | INV-11 follow-up: MCP codebook and graph code/entity data responses now surface `data_warnings` when present | `completed/INV11_NARROW_SURFACE_WARNINGS.md` |
| Review summary active inactive counts | Review summaries and CLI now distinguish active decisions from historical inactive decisions | `completed/REVIEW_SUMMARY_ACTIVE_INACTIVE_COUNTS.md` |
| D10 cost latency scorecard | Evaluation-harness follow-up: `make bench` now reports D10 cost/latency from real llm_client observability rows | `completed/D10_COST_LATENCY_SCORECARD.md` |
| D10 tool-call costs | Evaluation-harness follow-up: D10 cost/latency now includes optional observed tool-call accounting and combined local totals without changing LLM-only fields | `completed/D10_TOOL_CALL_COSTS.md` |
| Segment-derived speaker for anchored quotes | INV-1 follow-up: example-quote anchors now copy speaker from containing same-document segments when available | `completed/SEGMENT_DERIVED_SPEAKER_FOR_ANCHORED_QUOTES.md` |
| D7 baseline comparison | Evaluation-harness follow-up: `make bench` can score externally supplied D7 baseline predictions against the same gold as the system | `completed/D7_BASELINE_COMPARISON.md` |
| D10 wall-clock runtime | Evaluation-harness follow-up: `project run` records last-run wall-clock metadata and `make bench` reports `wall_clock_d10` | `completed/D10_WALL_CLOCK_RUNTIME.md` |
| D10 timing artifact | Evaluation-harness follow-up: Phase 0 artifact packages now include a hash-recorded `timing_d10.json` file without claiming public benchmark timing evidence | `completed/D10_TIMING_ARTIFACT.md` |
| D10 runtime environment metadata | Evaluation-harness follow-up: D10 timing artifacts include non-sensitive runtime environment metadata without claiming public benchmark timing evidence | `completed/D10_RUNTIME_ENVIRONMENT_METADATA.md` |
| Phase 0 input hashes | Evaluation-harness follow-up: `make bench` reports SHA-256 hashes for loaded state, corpus, and supplied benchmark files | `completed/PHASE0_INPUT_HASHES.md` |
| QC bench CLI | Evaluation-harness follow-up: `qc_cli.py bench` wraps the deterministic Phase 0 scorecard with the same current flags as `make bench` | `completed/QC_BENCH_CLI.md` |
| Phase 0 benchmark artifacts | Evaluation-harness follow-up: Phase 0 bench writes versioned `benchmark_results/` packages with scorecard and manifest provenance | `completed/PHASE0_BENCHMARK_ARTIFACTS.md` |
| Phase 0 run configuration hashes | Evaluation-harness follow-up: Phase 0 scorecards and artifact manifests hash persisted methodology/model/config metadata while marking prompt hashes as not-run | `completed/PHASE0_RUN_CONFIGURATION_HASHES.md` |
| D7 held-out gold-set scaffold | Evaluation-harness follow-up: versioned D7 gold-set packages can be validated and used as `--gold-file` inputs without claiming held-out results | `completed/D7_HELD_OUT_GOLD_SET_SCAFFOLD.md` |
| INV-7 fixture runner scaffold | Evaluation-harness follow-up: `make run-inv7-fixtures` writes deterministic structural prompt-boundary fixture outcomes for `PROMPT_INJECTION=` | `completed/INV7_FIXTURE_RUNNER_SCAFFOLD.md` |
| D7 retrieval-mode export | Evaluation-harness follow-up: `make run-d7-retrieval` exports retrieval candidates as D7 baseline-compatible predictions for `make bench BASELINES=...` | `completed/D7_RETRIEVAL_MODE_EXPORT.md` |
| D7 retrieval comparison report | Evaluation-harness follow-up: `make compare-d7-retrieval` scores multiple retrieval prediction packages against one D7 gold file with the existing exact-span scorer | `completed/D7_RETRIEVAL_COMPARISON_REPORT.md` |
| D3 application validity scorecard | Evaluation-harness follow-up: `make bench D3_GOLD=...` reports exact code/source-anchor application-validity scores when adjudicated D3 gold is supplied | `completed/D3_APPLICATION_VALIDITY_SCORECARD.md` |
| D3 held-out gold-set scaffold | Evaluation-harness follow-up: versioned D3 gold-set packages can be validated and used as `--d3-gold-file` inputs without claiming held-out results | `completed/D3_HELD_OUT_GOLD_SET_SCAFFOLD.md` |
| Gold-set provenance in scorecards | Evaluation-harness follow-up: versioned D3/D7 package metadata is surfaced as compact `gold_provenance` in Phase 0 scorecard sections | `completed/GOLD_SET_PROVENANCE_SCORECARD.md` |
| Exact-score F1 bootstrap intervals | Evaluation-harness follow-up: D3/D7 exact-anchor scorecards now report configurable local F1 bootstrap intervals while baseline deltas remain point estimates | `completed/EXACT_SCORE_F1_BOOTSTRAP_INTERVALS.md` |
| D7 baseline delta bootstrap intervals | Evaluation-harness follow-up: D7 baseline comparisons now report configurable local paired bootstrap intervals for system-minus-baseline recall/precision/F1 deltas | `completed/D7_BASELINE_DELTA_BOOTSTRAP_INTERVALS.md` |
| D3 span-overlap IoU scorecard | Evaluation-harness follow-up: D3 scorecards now report local same-code/doc char-span IoU overlap diagnostics beside exact-anchor scores | `completed/D3_SPAN_OVERLAP_IOU_SCORECARD.md` |
| D3 Modified Hausdorff scorecard | Evaluation-harness follow-up: D3 span-overlap diagnostics now report local discrete Modified Hausdorff distances beside IoU | `completed/D3_MODIFIED_HAUSDORFF_SCORECARD.md` |
| INV-7 live fixture runner | Evaluation-harness follow-up: `make run-inv7-live-fixtures` writes opt-in live model canary fixture outcomes for `PROMPT_INJECTION=` without claiming prompt-injection robustness | `completed/INV7_LIVE_FIXTURE_RUNNER.md` |
| Human-ceiling comparison scorecard | Evaluation-harness follow-up: D3/D7 scorecards compare exact recall/precision/F1 to supplied human-human package metrics when available without claiming expert parity | `completed/HUMAN_CEILING_COMPARISON_SCORECARD.md` |
| D5 Gwet AC1 reliability scorecard | Evaluation-harness follow-up: `project irr`, Markdown export, and `make bench` surface Gwet's AC1 for LLM-pass consistency without claiming human IRR | `completed/D5_GWET_AC1_RELIABILITY_SCORECARD.md` |
| D5 reliability prevalence tables | Evaluation-harness follow-up: `make bench` surfaces rating prevalence tables beside D5 κ/AC1 reliability metrics | `completed/D5_RELIABILITY_PREVALENCE_TABLES.md` |
| D5 reliability bootstrap intervals | Evaluation-harness follow-up: `make bench` surfaces deterministic local row-bootstrap intervals for D5 LLM-pass percent agreement and AC1 without claiming human IRR | `completed/D5_RELIABILITY_BOOTSTRAP_INTERVALS.md` |
| D6 counterfactual bias scorecard | Evaluation-harness follow-up: `make bench BIAS_COUNTERFACTUAL=...` scores externally supplied identity-swap outcomes without claiming a populated bias audit | `completed/D6_COUNTERFACTUAL_BIAS_SCORECARD.md` |
| Human agreement metadata scorecard | Evaluation-harness follow-up: D3/D7 human-ceiling sections now surface supplied human-human κ/α/AC1 metadata without claiming system agreement-vs-gold | `completed/HUMAN_AGREEMENT_METADATA_SCORECARD.md` |
| D4 codebook quality scorecard | Evaluation-harness follow-up: `make bench CODEBOOK_QUALITY=...` scores externally supplied rubric outcomes without claiming blind expert-panel evidence | `completed/D4_CODEBOOK_QUALITY_SCORECARD.md` |
| D9 interpretive preference scorecard | Evaluation-harness follow-up: `make bench PREFERENCE=...` scores externally supplied forced-choice preference outcomes without claiming blind expert-parity evidence | `completed/D9_INTERPRETIVE_PREFERENCE_SCORECARD.md` |
| D8 GT fidelity scorecard | Evaluation-harness follow-up: `make bench GT_FIDELITY=...` scores externally supplied GT-fidelity rubric outcomes without claiming full GT or methodological saturation | `completed/D8_GT_FIDELITY_SCORECARD.md` |
| Confidence calibration scorecard | Evaluation-harness follow-up: `make bench CALIBRATION=...` scores externally supplied confidence/correctness records without claiming calibrated confidence | `completed/CONFIDENCE_CALIBRATION_SCORECARD.md` |
| D3 system-gold agreement scorecard | Evaluation-harness follow-up: D3 scorecards report exact-key binary system-vs-gold agreement metrics without claiming full D3 validity or expert parity | `completed/D3_SYSTEM_GOLD_AGREEMENT_SCORECARD.md` |
| D7 system-gold agreement scorecard | Evaluation-harness follow-up: D7 scorecards report exact-key binary system-vs-gold agreement metrics without claiming semantic disconfirmation validity or held-out evidence | `completed/D7_SYSTEM_GOLD_AGREEMENT_SCORECARD.md` |
| Phase 0 benchmark package runner | Evaluation-harness follow-up: `make bench-package PACKAGE=...` runs canonical Phase 0 scoring from a strict versioned manifest without claiming held-out evidence | `completed/PHASE0_BENCHMARK_PACKAGE_RUNNER.md` |
| D3 baseline comparison scorecard | Evaluation-harness follow-up: D3 scorecards report exact-key baseline comparisons and system-minus-baseline deltas when supplied without claiming held-out evidence | `completed/D3_BASELINE_COMPARISON_SCORECARD.md` |
| Exact-key Krippendorff alpha scorecard | Evaluation-harness follow-up: D3/D7 exact-key system-gold agreement now reports Krippendorff's α metadata without claiming full semantic/multi-label α | `completed/EXACT_KEY_KRIPPENDORFF_ALPHA_SCORECARD.md` |
| D9 non-inferiority margin scorecard | Evaluation-harness follow-up: D9 preference packages can report a pre-registered non-inferiority margin assessment without claiming blind expert parity | `completed/D9_NON_INFERIORITY_MARGIN_SCORECARD.md` |
| Confidence calibration Wilson intervals | Evaluation-harness follow-up: confidence-calibration scorecards report Wilson accuracy intervals overall, by bin, and by surface without claiming calibration proof | `completed/CONFIDENCE_CALIBRATION_WILSON_INTERVALS.md` |
| D6 counterfactual change-rate Wilson intervals | Evaluation-harness follow-up: D6 counterfactual-bias scorecards report Wilson intervals for code-change rates overall and by attribute without claiming a populated bias audit | `completed/D6_COUNTERFACTUAL_CHANGE_RATE_WILSON_INTERVALS.md` |
| D6 counterfactual Jaccard bootstrap intervals | Evaluation-harness follow-up: D6 counterfactual-bias scorecards report deterministic local bootstrap intervals for mean Jaccard distance without claiming a populated bias audit | `completed/D6_COUNTERFACTUAL_JACCARD_BOOTSTRAP_INTERVALS.md` |
| D4 codebook-quality bootstrap intervals | Evaluation-harness follow-up: D4 codebook-quality scorecards report deterministic local bootstrap intervals for rubric means without claiming blind expert-panel evidence | `completed/D4_CODEBOOK_QUALITY_BOOTSTRAP_INTERVALS.md` |
| D8 GT-fidelity bootstrap intervals | Evaluation-harness follow-up: D8 GT-fidelity scorecards report deterministic local bootstrap intervals for rubric means without claiming expert-rubric acceptance or full GT evidence | `completed/D8_GT_FIDELITY_BOOTSTRAP_INTERVALS.md` |
| D9 tie-rate Wilson intervals | Evaluation-harness follow-up: D9 interpretive-preference scorecards report Wilson intervals for tie rates without claiming blind expert parity | `completed/D9_TIE_RATE_WILSON_INTERVALS.md` |
| INV-7 prompt-injection Wilson intervals | Evaluation-harness follow-up: INV-7 prompt-injection fixture scorecards report Wilson intervals for pass and attack-success rates without claiming prompt-injection robustness | `completed/INV7_PROMPT_INJECTION_WILSON_INTERVALS.md` |
| INV-7 attack-type scorecard | Evaluation-harness follow-up: INV-7 prompt-injection fixture scorecards report by-attack-type pass and attack-success summaries without claiming prompt-injection robustness | `completed/INV7_ATTACK_TYPE_SCORECARD.md` |
| D1/D2 structural rate Wilson intervals | Evaluation-harness follow-up: Phase 0 grounding, coverage, and examined rates report Wilson intervals without claiming validity evidence | `completed/D1_D2_STRUCTURAL_RATE_WILSON_INTERVALS.md` |
| D2 coded segment rate | Evaluation-harness follow-up: Phase 0 D2 coverage reports coded-segment rate and Wilson intervals over examined decisions only | `completed/D2_CODED_SEGMENT_RATE.md` |
| Confidence calibration bootstrap intervals | Evaluation-harness follow-up: confidence-calibration scorecards report deterministic local bootstrap intervals for Brier score and ECE without claiming calibrated confidence | `completed/CONFIDENCE_CALIBRATION_BOOTSTRAP_INTERVALS.md` |
| INV-3 adjudication sample export | INV-3 first slice: `make adjudication-sample` exports unlabeled schema_version=1 sample packets for human/expert review inputs without claiming labels or validity evidence | `completed/INV3_ADJUDICATION_SAMPLE_EXPORT.md` |
| INV-3 adjudication response validator | INV-3 follow-up: `make validate-adjudication-responses` validates completed sample response shape/completeness without importing labels or claiming validity evidence | `completed/INV3_ADJUDICATION_RESPONSE_VALIDATOR.md` |

## Status Key

| Status | Meaning |
|--------|---------|
| Planned | Ready to implement |
| In Progress | Being worked on |
| Blocked | Waiting on dependency |
| Complete | Implemented and verified |

## Creating a New Plan

1. Copy `TEMPLATE.md` to a descriptive `NAME.md` (e.g. `INV9_CLAIM_LEDGER.md`)
2. Fill in gap, steps, required tests
3. Add a row to the **Active Plans** table above
4. Commit with a `[Plan: NAME]` prefix

## Trivial Changes

Not everything needs a plan. Use `[Trivial]` for:
- Less than 20 lines changed
- No changes to `src/` (production code)
- No new files created

```bash
git commit -m "[Trivial] Fix typo in README"
```

## Completing Plans

1. Move the plan doc to `completed/NAME.md` (add a one-paragraph outcome + verification evidence at the top)
2. Remove its row from **Active Plans** and add one to **Completed Plans** pointing at `completed/NAME.md`
3. `python scripts/sync_plan_status.py --check` (run by `make docs-check`) verifies every Completed row resolves and every record file is listed
