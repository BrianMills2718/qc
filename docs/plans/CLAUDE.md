# Implementation Plans

Track all implementation work here.

## Active Plans

| # | Name | Priority | Status | Plan doc |
|---|------|----------|--------|----------|
| 173 | INV-7 score-time preflight guard | High | Planned | `INV7_SCORE_TIME_PREFLIGHT_GUARD.md` |

## Completed Plans

| Name | Outcome | Record |
|------|---------|--------|
| D7 comparison metric success criteria | D7 comparison protocols can now carry optional structured per-baseline metric criteria, and guarded retrieval comparison reports include additive pass/fail/missing criteria accounting without changing exact D7 scoring or preflight semantics | `completed/D7_COMPARISON_METRIC_SUCCESS_CRITERIA.md` |
| D7 baseline span-overlap diagnostics | D7 baseline rows and retrieval comparison reports now include diagnostic-only same-target/document span-IoU and Modified Hausdorff metadata without changing exact baseline scores or deltas | `completed/D7_BASELINE_SPAN_OVERLAP_DIAGNOSTICS.md` |
| D7 span-overlap diagnostics | D7 scorecards now include diagnostic-only same-target/document span-IoU and Modified Hausdorff overlap metadata for contrary-evidence anchors without changing exact D7 scores or claims | `completed/D7_SPAN_OVERLAP_DIAGNOSTICS.md` |
| INV-7 committed live canary v2 | A protocol-guarded built-in fixture-set v2 live canary artifact is now committed and scorecarded with five fixtures, including custom prompt override surfaces, while remaining explicitly non-evidentiary for robustness, validity, held-out, model-obedience, or SOTA claims | `completed/INV7_COMMITTED_LIVE_CANARY_V2.md` |
| INV-7 custom prompt override fixtures | Built-in INV-7 structural and opt-in live fixture sets now include custom prompt override canaries for thematic and GT constant-comparison override surfaces rendered through the production override wrapper | `completed/INV7_CUSTOM_PROMPT_OVERRIDE_FIXTURES.md` |
| INV-11 GT recode higher-order refresh | Grounded-theory projects can now opt into `--refresh-higher-order` after incremental recode to rebuild GT open-code context and rerun Axial, Selective, and Theory Integration before Cross-Interview and Negative Case | `completed/INV11_GT_RECODE_HIGHER_ORDER_REFRESH.md` |
| INV-11 thematic recode higher-order refresh | Default/thematic projects can now opt into `--refresh-higher-order` after incremental recode to rebuild Phase 1 context and rerun Perspective, Relationship, and Synthesis before Cross-Interview and Negative Case; GT refresh was deferred to a later slice | `completed/INV11_THEMATIC_RECODE_HIGHER_ORDER_REFRESH.md` |
| INV-7 prompt override guardrail wrapper | Rendered custom prompt overrides are now bookended by a repo-owned instruction/data-separation wrapper with a final data-boundary reminder after operator-authored template text | `completed/INV7_PROMPT_OVERRIDE_GUARDRAIL_WRAPPER.md` |
| INV-7 committed live canary | A protocol-guarded built-in live canary artifact is now committed and scorecarded, while remaining explicitly non-evidentiary for robustness, validity, held-out, model-obedience, or SOTA claims | `completed/INV7_COMMITTED_LIVE_CANARY.md` |
| MCP export audit SQLite mirror | MCP JSON/Markdown exports can now write confined SQLite mirrors for audit event logs when explicitly enabled with `audit_event_db=True` | `completed/MCP_EXPORT_AUDIT_SQLITE_MIRROR.md` |
| Export audit SQLite workflow integration | Local export-audit scripts, Make targets, and `project export` can now update the optional SQLite event mirror whenever JSONL audit logging is explicitly enabled | `completed/EXPORT_AUDIT_SQLITE_WORKFLOW_INTEGRATION.md` |
| Export audit SQLite event mirror | Verified export audit JSONL event logs can now be mirrored into local SQLite and verified there for event shape, hashes, previous links, duplicate hashes, and row ordering | `completed/EXPORT_AUDIT_SQLITE_EVENT_MIRROR.md` |
| INV-9 relationship evidence anchors | Relationship claims now resolve direct evidence strings into exact supporting anchors when uniquely grounded, while ambiguous/unresolvable evidence remains visibly unanchored | `completed/INV9_RELATIONSHIP_EVIDENCE_ANCHORS.md` |
| INV-9 code-scoped higher-order claim anchors | Higher-order claims with explicit code scope now inherit existing exact code-application anchors while corpus-level/no-code-scope claims remain visibly unanchored | `completed/INV9_CODE_SCOPED_HIGHER_ORDER_CLAIM_ANCHORS.md` |
| INV-7 prompt override metadata boundary | Prompt override rendering now rejects structured or multi-line metadata placeholder values before custom prompt rendering | `completed/INV7_PROMPT_OVERRIDE_METADATA_BOUNDARY.md` |
| INV-7 prompt override data value boundary | Prompt override rendering now rejects raw/unwrapped values supplied for declared data placeholders before any LLM call | `completed/INV7_PROMPT_OVERRIDE_DATA_VALUE_BOUNDARY.md` |
| Line ending normalization | Tracked text files are LF-normalized and `.gitattributes` now records an LF text policy; CRLF scans return no tracked text matches | `completed/LINE_ENDING_NORMALIZATION.md` |
| Cost observability target verification | `make cost` returns real llm_client cost/embedding tables and `make errors` returns a clear recent-error summary, so no fallback replacement was needed | `completed/COST_OBSERVABILITY_TARGET_VERIFICATION.md` |
| Ruff F541 expansion | Ruff now gates `F541`, and the existing no-placeholder f-strings were mechanically removed without intended runtime behavior changes | `completed/RUFF_F541_EXPANSION.md` |
| Boundary invalid project ID tests | API/MCP regression tests now prove invalid/traversal-like project IDs return explicit not-found/error responses without aliasing to or deleting existing project files | `completed/BOUNDARY_INVALID_PROJECT_ID_TESTS.md` |
| Explicit export overwrite policy | Project exports now keep default overwrite behavior for compatibility while supporting `--no-overwrite` / `overwrite=False` guards that fail before clobbering existing JSON/CSV/Markdown/QDPX artifacts | `completed/EXPORT_OVERWRITE_POLICY.md` |
| Corpus-scope adequacy scorecard | Phase 0 now reports deterministic corpus-scope status, field completeness, document/claim counts, and status warnings without claiming sampling validity | `completed/CORPUS_SCOPE_ADEQUACY_SCORECARD.md` |
| INV-9 claim-anchor coverage scorecard | Phase 0 now reports deterministic claim-anchor coverage counts/rates/breakdowns for first-class ledger rows without claiming validity or adjudication evidence | `completed/INV9_CLAIM_ANCHOR_COVERAGE_SCORECARD.md` |
| INV-1 span anchoring + harness Phase 0 | INV-1 mostly met; `make bench` Phase 0 stood up | `completed/INV1_OVERNIGHT_SPRINT.md` |
| INV-1 deterministic fuzzy grounding | INV-1 follow-up: normalized exact grounding now has a conservative deterministic fuzzy fallback for long near-verbatim spans while preserving ambiguity drops and hash-verifiable original offsets | `completed/INV1_DETERMINISTIC_FUZZY_GROUNDING.md` |
| INV-1 source-prefix speaker fallback | INV-1 follow-up: anchored quotes now derive speaker from explicit same-line `Speaker:` source prefixes when no containing segment speaker exists, without making speaker part of anchor verification | `completed/INV1_SOURCE_PREFIX_SPEAKER_FALLBACK.md` |
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
| Prompt override placeholder policy | INV-7 follow-up: prompt override renderer values must be declared as required data, optional data, or metadata before exposure to custom prompts | `completed/PROMPT_OVERRIDE_PLACEHOLDER_POLICY.md` |
| INV-7 prompt override surface registry | INV-7 follow-up: supported prompt override surfaces are centrally registered and `make lint-prompt-overrides` checks source uses without claiming prompt-injection robustness | `completed/INV7_PROMPT_OVERRIDE_SURFACE_REGISTRY.md` |
| INV-7 prompt-injection package | INV-7 follow-up: structural and live fixture outputs now have a schema_version=1 package contract, validator, and Phase 0 loader support without claiming robustness evidence | `completed/INV7_PROMPT_INJECTION_PACKAGE.md` |
| INV-4 category saturation diagnostic | INV-4 first slice: `make bench` reports diagnostic-only category property/dimension/support adequacy separately from codebook stability | `completed/INV4_CATEGORY_SATURATION_DIAGNOSTIC.md` |
| INV-4 diagnostic-driven theoretical sampling | INV-4 follow-up: sampling suggestions use category adequacy gaps before falling back to low application coverage | `completed/INV4_DIAGNOSTIC_THEORETICAL_SAMPLING.md` |
| Theoretical sampling protocol package | INV-4 follow-up: `make validate-theoretical-sampling-protocol` validates pre-run theoretical-sampling protocol metadata for target gaps, thresholds, candidate-source policy, collection rules, stopping rule, and success criteria without claiming sampling adequacy | `completed/THEORETICAL_SAMPLING_PROTOCOL_PACKAGE.md` |
| Theoretical sampling protocol preflight | INV-4 follow-up: `make theoretical-sampling-preflight` checks concrete candidate/result packages against registered theoretical-sampling protocol metadata without claiming sampling adequacy or saturation | `completed/THEORETICAL_SAMPLING_PROTOCOL_PREFLIGHT.md` |
| Theoretical sampling candidate export | INV-4 follow-up: `make export-theoretical-sampling-candidates` exports loaded-document candidate packages from diagnostic suggestions for protocol preflight without claiming sampling execution, adequacy, or saturation | `completed/THEORETICAL_SAMPLING_CANDIDATE_EXPORT.md` |
| Theoretical sampling result export | INV-4 follow-up: `make export-theoretical-sampling-results` records explicit selected candidate IDs as result packages for protocol preflight without claiming sampling judgment, adequacy, or saturation | `completed/THEORETICAL_SAMPLING_RESULT_EXPORT.md` |
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
| INV-11 add-docs recode hook | `project add-docs --recode` now explicitly adds documents and invokes the existing incremental recode path without making plain add-docs spend model budget | `completed/INV11_ADD_DOCS_RECODE_HOOK.md` |
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
| QC bench CLI flag parity | Evaluation-harness follow-up: `qc_cli.py bench` mirrors current Phase 0 external-input and protocol-guard flags from `scripts/bench_phase0.py` | `completed/QC_BENCH_CLI_FLAG_PARITY.md` |
| QC bench package CLI | Evaluation-harness follow-up: `qc_cli.py bench-package` runs strict Phase 0 package manifests through the canonical package runner | `completed/QC_BENCH_PACKAGE_CLI.md` |
| Phase 0 benchmark artifacts | Evaluation-harness follow-up: Phase 0 bench writes versioned `benchmark_results/` packages with scorecard and manifest provenance | `completed/PHASE0_BENCHMARK_ARTIFACTS.md` |
| Phase 0 run configuration hashes | Evaluation-harness follow-up: Phase 0 scorecards and artifact manifests hash persisted methodology/model/config metadata while marking prompt hashes as not-run | `completed/PHASE0_RUN_CONFIGURATION_HASHES.md` |
| D7 held-out gold-set scaffold | Evaluation-harness follow-up: versioned D7 gold-set packages can be validated and used as `--gold-file` inputs without claiming held-out results | `completed/D7_HELD_OUT_GOLD_SET_SCAFFOLD.md` |
| D3/D7 gold validator CLI surfaces | `qc_cli.py validate-d3-gold` and `qc_cli.py validate-d7-gold` wrap the canonical gold-set validators without duplicating validation logic or claiming held-out evidence | `completed/D3_D7_GOLD_VALIDATOR_CLI.md` |
| INV-7 fixture runner scaffold | Evaluation-harness follow-up: `make run-inv7-fixtures` writes deterministic structural prompt-boundary fixture outcomes for `PROMPT_INJECTION=` | `completed/INV7_FIXTURE_RUNNER_SCAFFOLD.md` |
| D7 retrieval-mode export | Evaluation-harness follow-up: `make run-d7-retrieval` exports retrieval candidates as D7 baseline-compatible predictions for `make bench BASELINES=...` | `completed/D7_RETRIEVAL_MODE_EXPORT.md` |
| D7 retrieval comparison report | Evaluation-harness follow-up: `make compare-d7-retrieval` scores multiple retrieval prediction packages against one D7 gold file with the existing exact-span scorer | `completed/D7_RETRIEVAL_COMPARISON_REPORT.md` |
| D7 retrieval comparison protocol preflight | Evaluation-harness follow-up: `make validate-d7-comparison-protocol` and `make d7-comparison-preflight` bind D7 retrieval comparison gold/prediction packages to registered protocol metadata before scoring | `completed/D7_RETRIEVAL_COMPARISON_PROTOCOL_PREFLIGHT.md` |
| D7 comparison preflight guard | Evaluation-harness follow-up: `make compare-d7-retrieval ... PROTOCOL=...` runs D7 comparison preflight before scoring and blocks mismatched inputs | `completed/D7_COMPARISON_PREFLIGHT_GUARD.md` |
| D7 retrieval CLI surfaces | Evaluation-harness follow-up: `qc_cli.py run-d7-retrieval` and `qc_cli.py compare-d7-retrieval` expose existing D7 retrieval export/comparison scripts through the canonical CLI | `completed/D7_RETRIEVAL_CLI_SURFACES.md` |
| D7 retrieval export script tests | Testing follow-up: direct script-boundary tests cover `scripts/run_d7_retrieval.py` stdout/output, JSON error, and option forwarding behavior | `completed/D7_RETRIEVAL_EXPORT_SCRIPT_TESTS.md` |
| D7 live candidate baseline export | Evaluation-harness follow-up: `make run-d7-live-baseline` and `qc_cli.py run-d7-live-baseline` export opt-in live candidate-selection D7 baseline packages for `BASELINES=` without claiming held-out evidence | `completed/D7_LIVE_CANDIDATE_BASELINE_EXPORT.md` |
| D7 live baseline preflight support | Evaluation-harness follow-up: D7 comparison protocols and preflights can now guard opt-in live candidate-selection baseline packages via `baseline_mode="live_candidate_selector"` without claiming held-out evidence | `completed/D7_LIVE_BASELINE_PREFLIGHT_SUPPORT.md` |
| D7 baseline package validator | Evaluation-harness follow-up: `make validate-d7-baseline-package` validates versioned retrieval/live-baseline prediction packages and recognized versioned `BASELINES=` files validate before scoring without claiming held-out evidence | `completed/D7_BASELINE_PACKAGE_VALIDATOR.md` |
| D7 baseline validator CLI | Evaluation-harness follow-up: `qc_cli.py validate-d7-baseline-package` wraps the canonical D7 baseline package validator without duplicating validation logic or claiming held-out evidence | `completed/D7_BASELINE_VALIDATOR_CLI.md` |
| INV-7 fixture CLI surfaces | Evaluation-harness follow-up: `qc_cli.py run-inv7-fixtures` and `qc_cli.py run-inv7-live-fixtures` expose existing INV-7 fixture runner scripts through the canonical CLI | `completed/INV7_FIXTURE_CLI_SURFACES.md` |
| D3 application validity scorecard | Evaluation-harness follow-up: `make bench D3_GOLD=...` reports exact code/source-anchor application-validity scores when adjudicated D3 gold is supplied | `completed/D3_APPLICATION_VALIDITY_SCORECARD.md` |
| D3 held-out gold-set scaffold | Evaluation-harness follow-up: versioned D3 gold-set packages can be validated and used as `--d3-gold-file` inputs without claiming held-out results | `completed/D3_HELD_OUT_GOLD_SET_SCAFFOLD.md` |
| Gold-set provenance in scorecards | Evaluation-harness follow-up: versioned D3/D7 package metadata is surfaced as compact `gold_provenance` in Phase 0 scorecard sections | `completed/GOLD_SET_PROVENANCE_SCORECARD.md` |
| Exact-score F1 bootstrap intervals | Evaluation-harness follow-up: D3/D7 exact-anchor scorecards now report configurable local F1 bootstrap intervals while baseline deltas remain point estimates | `completed/EXACT_SCORE_F1_BOOTSTRAP_INTERVALS.md` |
| D7 baseline delta bootstrap intervals | Evaluation-harness follow-up: D7 baseline comparisons now report configurable local paired bootstrap intervals for system-minus-baseline recall/precision/F1 deltas | `completed/D7_BASELINE_DELTA_BOOTSTRAP_INTERVALS.md` |
| D3 span-overlap IoU scorecard | Evaluation-harness follow-up: D3 scorecards now report local same-code/doc char-span IoU overlap diagnostics beside exact-anchor scores | `completed/D3_SPAN_OVERLAP_IOU_SCORECARD.md` |
| D3 Modified Hausdorff scorecard | Evaluation-harness follow-up: D3 span-overlap diagnostics now report local discrete Modified Hausdorff distances beside IoU | `completed/D3_MODIFIED_HAUSDORFF_SCORECARD.md` |
| D3 baseline package validator | Versioned D3 application-baseline packages now validate through `make validate-d3-baseline-package`, and recognized packages validate before `D3_BASELINES=` scoring while legacy inputs remain compatible | `completed/D3_BASELINE_PACKAGE_VALIDATOR.md` |
| D3 baseline validator CLI | `qc_cli.py validate-d3-baseline-package` wraps the canonical D3 baseline package validator without duplicating validation logic or claiming held-out evidence | `completed/D3_BASELINE_VALIDATOR_CLI.md` |
| INV-7 live fixture runner | Evaluation-harness follow-up: `make run-inv7-live-fixtures` writes opt-in live model canary fixture outcomes for `PROMPT_INJECTION=` without claiming prompt-injection robustness | `completed/INV7_LIVE_FIXTURE_RUNNER.md` |
| INV-7 live fixture prompt hashes | INV-7 follow-up: live fixture packages now carry exact prompt SHA-256 hashes for provenance without claiming prompt-injection robustness | `completed/INV7_LIVE_FIXTURE_PROMPT_HASHES.md` |
| INV-7 live benchmark protocol | INV-7 follow-up: `make validate-inv7-live-protocol` validates pre-run live canary protocol metadata before live prompt-injection runs | `completed/INV7_LIVE_BENCHMARK_PROTOCOL.md` |
| INV-7 live protocol result preflight | INV-7 follow-up: `make inv7-live-preflight` checks live result packages against registered live protocols before scoring | `completed/INV7_LIVE_PROTOCOL_RESULT_PREFLIGHT.md` |
| INV-7 validation CLI surfaces | `qc_cli.py validate-inv7-package`, `validate-inv7-live-protocol`, and `inv7-live-preflight` wrap canonical validation/preflight scripts without claiming prompt-injection robustness evidence | `completed/INV7_VALIDATION_CLI_SURFACES.md` |
| Human-ceiling comparison scorecard | Evaluation-harness follow-up: D3/D7 scorecards compare exact recall/precision/F1 to supplied human-human package metrics when available without claiming expert parity | `completed/HUMAN_CEILING_COMPARISON_SCORECARD.md` |
| D5 Gwet AC1 reliability scorecard | Evaluation-harness follow-up: `project irr`, Markdown export, and `make bench` surface Gwet's AC1 for LLM-pass consistency without claiming human IRR | `completed/D5_GWET_AC1_RELIABILITY_SCORECARD.md` |
| D5 reliability prevalence tables | Evaluation-harness follow-up: `make bench` surfaces rating prevalence tables beside D5 κ/AC1 reliability metrics | `completed/D5_RELIABILITY_PREVALENCE_TABLES.md` |
| D5 reliability bootstrap intervals | Evaluation-harness follow-up: `make bench` surfaces deterministic local row-bootstrap intervals for D5 LLM-pass percent agreement and AC1 without claiming human IRR | `completed/D5_RELIABILITY_BOOTSTRAP_INTERVALS.md` |
| D6 counterfactual bias scorecard | Evaluation-harness follow-up: `make bench BIAS_COUNTERFACTUAL=...` scores externally supplied identity-swap outcomes without claiming a populated bias audit | `completed/D6_COUNTERFACTUAL_BIAS_SCORECARD.md` |
| D6 stratified bias scorecard | Evaluation-harness follow-up: `make bench BIAS_STRATIFIED=...` scores externally supplied stratified correctness/error diagnostics without claiming a populated bias audit | `completed/D6_STRATIFIED_BIAS_SCORECARD.md` |
| D6 bias protocol package | Evaluation-harness follow-up: `make validate-d6-bias-protocol` validates pre-run D6 bias-audit protocol metadata without claiming a populated bias audit | `completed/D6_BIAS_PROTOCOL_PACKAGE.md` |
| D6 bias protocol result preflight | Evaluation-harness follow-up: `make d6-bias-preflight` checks D6 result files against a registered protocol before scoring without claiming bias evidence | `completed/D6_BIAS_PROTOCOL_RESULT_PREFLIGHT.md` |
| D6 bias scorecard preflight guard | Evaluation-harness follow-up: `make bench D6_PROTOCOL=...` enforces D6 protocol/result preflight before scorecard/output/artifact writes | `completed/D6_BIAS_SCORECARD_PREFLIGHT_GUARD.md` |
| D4 codebook quality protocol package | Evaluation-harness follow-up: `make validate-d4-codebook-quality-protocol` validates pre-evaluation D4 protocol metadata without claiming blind expert evidence | `completed/D4_CODEBOOK_QUALITY_PROTOCOL_PACKAGE.md` |
| D4 codebook quality protocol result preflight | Evaluation-harness follow-up: `make d4-codebook-quality-preflight` checks D4 result files against a registered protocol without claiming blind expert evidence | `completed/D4_CODEBOOK_QUALITY_PROTOCOL_RESULT_PREFLIGHT.md` |
| D4 codebook quality scorecard preflight guard | Evaluation-harness follow-up: `make bench D4_PROTOCOL=...` enforces D4 protocol/result preflight before scorecard/output/artifact writes | `completed/D4_CODEBOOK_QUALITY_SCORECARD_PREFLIGHT_GUARD.md` |
| Human agreement metadata scorecard | Evaluation-harness follow-up: D3/D7 human-ceiling sections now surface supplied human-human κ/α/AC1 metadata without claiming system agreement-vs-gold | `completed/HUMAN_AGREEMENT_METADATA_SCORECARD.md` |
| D4 codebook quality scorecard | Evaluation-harness follow-up: `make bench CODEBOOK_QUALITY=...` scores externally supplied rubric outcomes without claiming blind expert-panel evidence | `completed/D4_CODEBOOK_QUALITY_SCORECARD.md` |
| D9 interpretive preference scorecard | Evaluation-harness follow-up: `make bench PREFERENCE=...` scores externally supplied forced-choice preference outcomes without claiming blind expert-parity evidence | `completed/D9_INTERPRETIVE_PREFERENCE_SCORECARD.md` |
| D9 interpretive preference protocol package | Evaluation-harness follow-up: `make validate-d9-interpretive-preference-protocol` validates pre-evaluation D9 blind preference protocol metadata without claiming blind expert-parity evidence | `completed/D9_INTERPRETIVE_PREFERENCE_PROTOCOL_PACKAGE.md` |
| D9 interpretive preference protocol result preflight | Evaluation-harness follow-up: `make d9-interpretive-preference-preflight` checks D9 result files against registered protocols without claiming blind expert-parity evidence | `completed/D9_INTERPRETIVE_PREFERENCE_PROTOCOL_RESULT_PREFLIGHT.md` |
| D9 interpretive preference scorecard preflight guard | Evaluation-harness follow-up: `make bench D9_PROTOCOL=...` enforces D9 protocol/result preflight before scorecard/output/artifact writes | `completed/D9_INTERPRETIVE_PREFERENCE_SCORECARD_PREFLIGHT_GUARD.md` |
| D8 GT fidelity scorecard | Evaluation-harness follow-up: `make bench GT_FIDELITY=...` scores externally supplied GT-fidelity rubric outcomes without claiming full GT or methodological saturation | `completed/D8_GT_FIDELITY_SCORECARD.md` |
| D8 GT fidelity protocol package | Evaluation-harness follow-up: `make validate-d8-gt-fidelity-protocol` validates pre-evaluation D8 protocol metadata without claiming expert-rubric evidence | `completed/D8_GT_FIDELITY_PROTOCOL_PACKAGE.md` |
| D8 GT fidelity protocol result preflight | Evaluation-harness follow-up: `make d8-gt-fidelity-preflight` checks D8 result files against registered protocols without claiming expert-rubric evidence | `completed/D8_GT_FIDELITY_PROTOCOL_RESULT_PREFLIGHT.md` |
| D8 GT fidelity scorecard preflight guard | Evaluation-harness follow-up: `make bench D8_PROTOCOL=...` enforces D8 protocol/result preflight before scorecard/output/artifact writes | `completed/D8_GT_FIDELITY_SCORECARD_PREFLIGHT_GUARD.md` |
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
| Confidence calibration protocol package | Evaluation-harness follow-up: `make validate-confidence-calibration-protocol` validates pre-evaluation confidence-calibration protocol metadata without claiming calibration proof | `completed/CONFIDENCE_CALIBRATION_PROTOCOL_PACKAGE.md` |
| Confidence calibration protocol result preflight | Evaluation-harness follow-up: `make confidence-calibration-preflight` checks confidence-calibration result files against registered protocols without claiming calibration proof | `completed/CONFIDENCE_CALIBRATION_PROTOCOL_RESULT_PREFLIGHT.md` |
| Confidence calibration scorecard preflight guard | Evaluation-harness follow-up: `make bench CONFIDENCE_PROTOCOL=...` enforces confidence-calibration protocol/result preflight before scorecard/output/artifact writes | `completed/CONFIDENCE_CALIBRATION_SCORECARD_PREFLIGHT_GUARD.md` |
| INV-7 prompt-injection Wilson intervals | Evaluation-harness follow-up: INV-7 prompt-injection fixture scorecards report Wilson intervals for pass and attack-success rates without claiming prompt-injection robustness | `completed/INV7_PROMPT_INJECTION_WILSON_INTERVALS.md` |
| INV-7 attack-type scorecard | Evaluation-harness follow-up: INV-7 prompt-injection fixture scorecards report by-attack-type pass and attack-success summaries without claiming prompt-injection robustness | `completed/INV7_ATTACK_TYPE_SCORECARD.md` |
| D1/D2 structural rate Wilson intervals | Evaluation-harness follow-up: Phase 0 grounding, coverage, and examined rates report Wilson intervals without claiming validity evidence | `completed/D1_D2_STRUCTURAL_RATE_WILSON_INTERVALS.md` |
| D2 coded segment rate | Evaluation-harness follow-up: Phase 0 D2 coverage reports coded-segment rate and Wilson intervals over examined decisions only | `completed/D2_CODED_SEGMENT_RATE.md` |
| Confidence calibration bootstrap intervals | Evaluation-harness follow-up: confidence-calibration scorecards report deterministic local bootstrap intervals for Brier score and ECE without claiming calibrated confidence | `completed/CONFIDENCE_CALIBRATION_BOOTSTRAP_INTERVALS.md` |
| Adjudication protocol package | INV-3 follow-up: `make validate-adjudication-protocol` validates pre-label adjudication protocol metadata without claiming labels or evidence exist | `completed/ADJUDICATION_PROTOCOL_PACKAGE.md` |
| Adjudication protocol sample preflight | INV-3 follow-up: `make adjudication-protocol-preflight` cross-checks protocol/sample package matching before labeling without claiming labels or evidence exist | `completed/ADJUDICATION_PROTOCOL_SAMPLE_PREFLIGHT.md` |
| Adjudication response preflight | INV-3 follow-up: `make adjudication-response-preflight` checks completed responses against protocol/sample provenance and exact item IDs before import without claiming labels or validity evidence | `completed/ADJUDICATION_RESPONSE_PREFLIGHT.md` |
| Adjudication import preflight guard | INV-3 follow-up: `make import-adjudication-responses ... PREFLIGHT_PROTOCOL=... PREFLIGHT_SAMPLE=...` can run response preflight at the import boundary before writing D3/D7 gold-package inputs | `completed/ADJUDICATION_IMPORT_PREFLIGHT_GUARD.md` |
| INV-3 adjudication sample export | INV-3 first slice: `make adjudication-sample` exports unlabeled schema_version=1 sample packets for human/expert review inputs without claiming labels or validity evidence | `completed/INV3_ADJUDICATION_SAMPLE_EXPORT.md` |
| INV-3 adjudication response validator | INV-3 follow-up: `make validate-adjudication-responses` validates completed sample response shape/completeness without importing labels or claiming validity evidence | `completed/INV3_ADJUDICATION_RESPONSE_VALIDATOR.md` |
| INV-3 adjudication response import | INV-3 follow-up: `make import-adjudication-responses` converts valid completed code-application and negative-case responses into D3/D7 gold package inputs while excluding invalid/unclear labels | `completed/INV3_ADJUDICATION_RESPONSE_IMPORT.md` |
| D3/D7 imported-gold benchmark package | Evaluation-harness/INV-3 follow-up: `make write-phase0-adjudication-package` writes a strict Phase 0 manifest from validated D3/D7 imported gold package inputs without claiming expert evidence | `completed/D3_D7_IMPORTED_GOLD_BENCH_PACKAGE.md` |
| Corpus scope phrasing lint | Scope/report follow-up: `make lint-scope-phrasing` scans arbitrary text for risky population-generalizing phrasing under missing or under-specified corpus scope | `completed/CORPUS_SCOPE_PHRASING_LINT.md` |
| Export audit hash manifest | Audit substrate first slice: `make export-audit-manifest` records project-state and export artifact SHA-256 hashes without claiming a full tamper-evident log | `completed/EXPORT_AUDIT_HASH_MANIFEST.md` |
| Export audit manifest verification | Audit substrate follow-up: `make verify-export-audit-manifest` checks manifest self-hash, artifact hashes, and optional project-state hash without claiming a signed/append-only log | `completed/EXPORT_AUDIT_MANIFEST_VERIFICATION.md` |
| Export audit CLI integration | Audit substrate follow-up: `project export --audit-manifest --verify-audit-manifest` can write and verify optional sidecars without changing default export contracts | `completed/EXPORT_AUDIT_CLI_INTEGRATION.md` |
| MCP export audit integration | Audit substrate follow-up: MCP JSON/Markdown export tools can write and verify optional confined sidecars without changing default return contracts | `completed/MCP_EXPORT_AUDIT_INTEGRATION.md` |
| Export publish preflight | Audit substrate follow-up: `make export-publish-preflight` requires a verified existing export-audit manifest for explicit local publish/handoff preflight without claiming signed/append-only audit | `completed/EXPORT_PUBLISH_PREFLIGHT.md` |
| Export audit event log | Audit substrate follow-up: local audit scripts can append opt-in hash-linked JSONL events and `make verify-export-audit-log` verifies event self-hashes/links without claiming immutable or signed audit | `completed/EXPORT_AUDIT_EVENT_LOG.md` |
| Export audit CLI/MCP event integration | Audit substrate follow-up: CLI/MCP export-audit workflows can append opt-in local event-log records while preserving default behavior and MCP export confinement | `completed/EXPORT_AUDIT_CLI_MCP_EVENT_INTEGRATION.md` |

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
