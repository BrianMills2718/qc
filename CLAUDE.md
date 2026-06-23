# Qualitative Coding Analysis System

*Last Updated: 2026-06-22*

> **Canonical status/theory docs (read before describing the system).** This
> file is the **operational** reference (architecture, commands, config). The
> *strategic* layer — honest state ledger, the INV-0..11 architectural
> invariants, the **claim-discipline** table (what you may/may not assert), the
> roadmap, and the prior-art/competitive landscape — lives in
> **`docs/PROJECT_THEORY_AND_GOALS.md`**, and the SOTA-evaluation plan in
> **`docs/EVALUATION_HARNESS.md`**. Where this file and the theory doc disagree
> about *status or claims*, the theory doc wins. Do not assert "validated",
> "full grounded theory", "SOTA", or "inter-rater reliability" without the
> caveats in theory doc §14.

## What This Project Does

LLM-powered qualitative coding analysis for interview transcripts. Accepts .txt, .docx, .pdf, .rtf files. Supports two methodologies:

- **Default/Thematic Analysis** - 7-stage pipeline: Ingest -> Thematic Coding -> Perspective Analysis -> Relationship Mapping -> Synthesis -> Cross-Interview Analysis -> Negative Case Analysis
- **Grounded Theory** - 7-stage pipeline: Ingest -> Constant Comparison Coding -> Axial Coding -> Selective Coding -> Theory Integration -> Cross-Interview Analysis -> Negative Case Analysis

  (Negative Case Analysis runs last and now sees bounded claim-ledger targets by claim ID plus BM25-style lexical/query-expanded retrieval-first source candidates. It has adversarial prompt framing, configurable `disconfirmation_model_name`, and opt-in unvalidated `embedding_hybrid` retrieval, but it is not held-out D7-evaluated and has no validated default embedding/reviewer policy. INV-6 remains PARTIAL and INV-2 is PARTIAL, not full credibility evidence. See `docs/PROJECT_THEORY_AND_GOALS.md`.)

All stages use structured LLM output via Pydantic schemas + JSON mode. State is held in a single `ProjectState` Pydantic model that can be saved/loaded as JSON.

## Current State

The software is **built and software-validated** (deterministic tests + live-LLM E2E; ruff + docs gates green) — "the program does what it's built to do," *not* evidence the analysis is methodologically valid. Implemented:

- Thematic and **GT-inspired** (not "full GT") pipelines; `NegativeCaseStage` runs **last** in both (INV-6), automatic cross-interview analysis for multi-doc corpora.
- GT constant comparison; category-saturation diagnostics, diagnostic-driven sampling suggestions, theoretical-sampling protocol validation/preflight, and candidate/result package export separate from codebook stability (INV-4 partial); incremental re-coding via `project recode` or explicit `project add-docs --recode` (hard-invalidates stale higher-order outputs by default, with per-project `auto_refresh_higher_order_on_recode` and one-run `--refresh-higher-order` / `--no-refresh-higher-order` overrides for thematic Perspective/Relationship/Synthesis and GT Axial/Selective/Theory Integration; INV-11 partial).
- **Span-anchored grounding** (INV-1, mostly met): quotes resolve to char offsets + hash via normalized exact matching plus conservative deterministic fuzzy recovery for long near-verbatim spans, speaker is derived from containing segments or explicit same-line `Speaker:` source prefixes where available, otherwise quotes are dropped + warned; `verify_grounding`/`make bench` measure the rate.
- **Segment universe + coverage** (INV-8): every doc split into char-anchored segments; `project run --exhaustive` codes *every* segment (examined-and-judged coverage, segment-anchored applications), else traversal coverage.
- **D3 application-validity scorecard substrate** (INV-3 partial infrastructure): `make bench D3_GOLD=d3_gold.json` reports exact code/source-anchor metrics, local same-code/document span-IoU plus Modified Hausdorff diagnostics, exact-key agreement metadata, and human-ceiling metadata when package metrics are present; `make bench D3_BASELINES=d3_baselines.json` scores externally supplied application baselines with exact deltas plus per-baseline local span-overlap diagnostics; `make validate-d3-comparison-protocol PROTOCOL=protocol.json` validates pre-run D3 baseline-comparison metadata and optional metric criteria; `make d3-comparison-preflight PROTOCOL=protocol.json GOLD=d3_gold.json PREDICTIONS="baseline.json"` cross-checks a registered protocol, versioned D3 gold package, and versioned D3 baseline packages before scoring; top-level `qc_cli.py validate-d3-comparison-protocol` / `qc_cli.py d3-comparison-preflight` delegate to those same canonical scripts; `make bench D3_PROTOCOL=protocol.json D3_GOLD=d3_gold.json D3_BASELINES=d3_baselines.json` enforces that preflight at score time before output/artifact writes, records `_meta.preflight_reports.d3_comparison`, and reports pre-registered D3 metric-criteria pass/fail/missing status when criteria are present. This is local accounting/error-analysis/protocol/preflight/score-time provenance/metric-criteria infrastructure only, not populated expert evidence, semantic application validity, held-out D3 evidence, expert parity, superiority evidence, or SOTA.
- **First-class claim ledger** (INV-9 object layer): substantive stage outputs become `AnalyticClaim` objects or no-claims events, with source stage, kind, scope, support/adjudication status, anchors where available, code-scoped higher-order claims inheriting existing code-application anchors, relationship evidence strings resolving to exact anchors when uniquely grounded, CLI/API/MCP/export read surfaces with scope and bounded anchor-detail inspection where applicable, API/MCP/CLI claim-ledger traversal with explicit `limit`/`offset` pagination metadata or display, and deterministic `make bench` claim-anchor coverage accounting. This is structural accounting/evidence visibility only, not claim-validity evidence.
- **Retrieval-first/adversarial ledger disconfirmation + review first slices** (INV-2/INV-6/INV-10 partial): negative-case prompts include bounded claim targets by ID and BM25-style lexical/query-expanded source-candidate passages; valid `candidate_id`s attach exact contrary anchors; `disconfirmation_model_name` can route interpretation through a separate model; coverage summaries report challenged/unchallenged targets; `make bench` includes a D7 scorecard substrate with recall/precision Wilson intervals and local same-target/document span-IoU plus Modified Hausdorff diagnostics when adjudicated contrary-evidence gold anchors are supplied via project metadata or `GOLD=gold.json`, plus optional baseline point comparisons via `BASELINES=baselines.json` whose baseline rows carry the same local span-overlap diagnostics; `make run-d7-retrieval` exports baseline-compatible prediction packages with project/corpus/state/trace/budget provenance; `make run-d7-live-baseline` exports opt-in live candidate-selection baseline packages; `make validate-d7-baseline-package` validates versioned retrieval/live-baseline prediction packages, and recognized versioned `BASELINES=` files now validate before scoring; `make validate-d7-comparison-protocol` validates registered comparison metadata plus optional machine-checkable `metric_criteria`, `make d7-comparison-preflight` cross-checks a registered comparison protocol, versioned D7 gold, and retrieval/live-baseline predictions, top-level `qc_cli.py validate-d7-comparison-protocol` / `qc_cli.py d7-comparison-preflight` delegate to those same canonical scripts, `make compare-d7-retrieval PROTOCOL=... ARTIFACT_DIR=...` can enforce that preflight at the scoring boundary, report pre-registered metric-criteria pass/fail/missing status, record `_meta.input_hashes` / `_meta.command` provenance, and optionally write a versioned D7 comparison artifact package with `report.json` and `manifest.json`, `make verify-d7-comparison-artifact ARTIFACT=...` verifies that local artifact manifest against `report.json`, `make write-d7-comparison-package ...` writes a strict manifest after validating gold/prediction packages and optional protocol preflight, and `make compare-d7-package PACKAGE=...` runs the same D7 comparison from that manifest; `ReviewManager`, API/MCP surfaces, and the browser review page support `target_type="claim"` approve/reject/modify decisions with revision history, including negative-case-specific review listing via API/MCP/browser surfaces whose claim rows expose bounded supporting/contrary anchor details; API/MCP review-list JSON surfaces for claims, negative cases, and relationships support bounded `limit`/`offset` traversal; `ReviewManager`, API/MCP surfaces, and the browser review page support `code_relationship` / `entity_relationship` approve/reject/modify decisions. Anchor details and pagination are review context only, not expert adjudication or D7 validity evidence.
- **Corpus-scope contract first slices**: optional `ProjectState.corpus_scope` records phenomenon, population, sampling frame, inclusion/exclusion criteria, and caveats; Markdown export surfaces it before analytic claims, CSV/Markdown claim rows carry compact claim-scope and corpus-boundary context, claim-bearing exports warn when scope is missing or under-specified, `make lint-scope-phrasing` / `qc_cli.py lint-scope-phrasing` check arbitrary text for risky population-generalizing language under missing/under-specified scope, `make export-publish-preflight ... SCOPE_LINT=1` / `qc_cli.py export-publish-preflight ... --scope-lint`, `qc_cli.py project export ... --publish-preflight --scope-lint`, and MCP `qc_export_markdown(..., publish_preflight=True, scope_lint=True)` can block risky Markdown/text handoff artifacts at publish preflight, and `make bench` reports deterministic `corpus_scope_adequacy` status/field completeness; CLI/API scope read/update surfaces are agent-drivable. This is report-boundary context, not sampling-frame validation.
- **Instruction/data separation first slices** (INV-7 partial): raw transcript/document/segment prompt sections and downstream LLM/codebook artifacts are rendered as untrusted `DATA>` lines via `qc_clean/core/prompting.py`; current prompt override surfaces fail loudly if they omit, index, attribute-access, conversion-format, format-specify, replace required protected data placeholders with undeclared metadata placeholders, expose renderer values not declared as required data, optional data, or metadata, supply raw/unwrapped values for declared data placeholders, or supply structured/multi-line values for declared metadata placeholders; rendered custom prompt overrides are bookended by a repo-owned instruction/data-separation wrapper with a final data-boundary reminder after operator-authored template text; `qc_clean/core/prompt_override_registry.py` centrally declares supported override surfaces and `make lint-prompt-overrides` / `qc_cli.py lint-prompt-overrides` check source uses against that registry; deterministic prompt-injection regressions exist; `make bench` can score externally supplied prompt-injection fixture outcomes via `PROMPT_INJECTION=results.json`, including schema_version=1 INV-7 packages from `make run-inv7-fixtures` / `make run-inv7-live-fixtures`, and `make bench INV7_PROTOCOL=protocol.json PROMPT_INJECTION=results.json` can enforce live protocol/result preflight at the score boundary before output/artifact writes; the built-in structural/live fixture sets include custom prompt override surfaces for thematic and GT constant-comparison overrides; live fixture packages include exact prompt SHA-256 hashes when produced by the runner; `make run-inv7-live-fixtures ... FIXTURES=manifest.json` / `qc_cli.py run-inv7-live-fixtures --fixtures manifest.json` can run external schema_version=1 live fixture manifests, including held-out manifests that require prompt-frozen, contamination-checked, and registered-before-run flags; `make validate-inv7-live-protocol` validates pre-run live protocol metadata; `make inv7-live-preflight` checks a live result package against that protocol before scoring; `make validate-inv7-package` validates result package metadata; `docs/benchmarks/inv7_live_canary_2026_06_22/` contains the original 3-fixture committed canary, and `docs/benchmarks/inv7_live_canary_v2_2026_06_22/` contains the current 5-fixture v2 canary including custom override surfaces. Broader held-out/adversarial live result evidence remains.
- D4 codebook-quality protocol/preflight/scorecard substrate: `make validate-d4-codebook-quality-protocol PROTOCOL=protocol.json` validates pre-evaluation D4 rubric protocol metadata; `make d4-codebook-quality-preflight PROTOCOL=protocol.json QUALITY=quality.json` checks concrete D4 result files against that protocol; `make bench D4_PROTOCOL=protocol.json CODEBOOK_QUALITY=quality.json` runs the same guard at score time before output/artifact writes and scores externally supplied rubric outcomes. These are protocol/accounting surfaces only, not blind expert-panel evidence, codebook-quality proof, or SOTA evidence.
- D6 bias protocol/preflight/scorecard substrate: `make validate-d6-bias-protocol PROTOCOL=protocol.json` validates pre-run D6 bias-audit protocol metadata; `make d6-bias-preflight PROTOCOL=protocol.json STRATIFIED=bias_stratified.json COUNTERFACTUAL=bias_counterfactual.json` checks concrete result files against that protocol; `make bench D6_PROTOCOL=protocol.json BIAS_COUNTERFACTUAL=bias.json BIAS_STRATIFIED=bias_stratified.json` runs the same guard at scoring time before output/artifact writes and includes a passing preflight report in scorecard metadata; these are local process/accounting surfaces only, not populated bias-audit evidence, causal proof, or a bias-free claim.
- D8 GT-fidelity protocol/preflight/scorecard substrate: `make validate-d8-gt-fidelity-protocol PROTOCOL=protocol.json` validates pre-evaluation D8 rubric protocol metadata for corpus/state/GT-artifact hashes, evaluator plan, rubric metrics, held-out gates, target scopes, and success criteria; `make d8-gt-fidelity-preflight PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json` checks concrete D8 result files against that protocol; `make bench D8_PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json` runs the same guard at score time before output/artifact writes and scores externally supplied rubric outcomes. These are protocol/accounting surfaces only, not expert-rubric acceptance, methodological-saturation evidence, full grounded-theory evidence, or SOTA evidence.
- D9 interpretive-preference protocol/preflight/scorecard substrate: `make validate-d9-interpretive-preference-protocol PROTOCOL=protocol.json` validates pre-evaluation blind preference protocol metadata for corpus/state/comparison-artifact hashes, blinding, evaluator plan, target criteria/surfaces, held-out gates, non-inferiority margin, and success criteria; `make d9-interpretive-preference-preflight PROTOCOL=protocol.json PREFERENCE=preference.json` checks concrete D9 result files against that protocol; `make bench D9_PROTOCOL=protocol.json PREFERENCE=preference.json` runs the same guard at score time before output/artifact writes and scores externally supplied forced-choice outcomes using the supplied protocol metadata for local non-inferiority assessment. These are protocol/accounting surfaces only, not blind expert-parity evidence, interpretive-depth evidence, methodological-validity evidence, or SOTA evidence.
- Confidence-calibration protocol/preflight/scorecard substrate: `make validate-confidence-calibration-protocol PROTOCOL=protocol.json` validates pre-evaluation calibration protocol metadata for corpus/state/prediction-artifact hashes, label-source plan, target surfaces, confidence source, held-out gates, outcome metrics, and success criteria; `make confidence-calibration-preflight PROTOCOL=protocol.json CALIBRATION=calibration.json` checks concrete calibration result files against that protocol; `make bench CONFIDENCE_PROTOCOL=protocol.json CALIBRATION=calibration.json` runs the same guard at score time before output/artifact writes and scores externally supplied confidence/correctness records. These are protocol/accounting surfaces only, not calibration proof, held-out correctness evidence, methodological-validity evidence, or SOTA evidence.
- Human review (CLI + browser), `project irr` (LLM-pass *codebook-discovery* agreement by default; **application-level** positive segment × code agreement plus segment-decision agreement via `--application-level`, using exhaustive coding), `project stability`.
- D10 cost/latency scorecard substrate: `make bench` queries real `llm_client` observability rows by project trace prefix or `TRACE_ID=...` and reports last-local-`project run` wall-clock metadata when available; missing rows/timing report `not_available`, never estimated.
- Phase 0 provenance/adjudication substrate: `make bench` emits `_meta.input_hashes` for the loaded project state, corpus, and supplied benchmark files; `make bench ARTIFACT_DIR=...` writes local `scorecard.json` / `timing_d10.json` / `manifest.json` artifact packages, and `make verify-phase0-benchmark-artifact ARTIFACT=...` verifies their local hashes and metadata consistency; `make validate-adjudication-protocol PROTOCOL=protocol.json` checks pre-registered protocol metadata; `make adjudication-protocol-preflight PROTOCOL=protocol.json SAMPLE=sample.json` checks that a concrete sample package matches that protocol before labeling; `make adjudication-sample` exports unlabeled schema_version=1 sample packets for human/expert review inputs; `make validate-adjudication-responses PACKAGE=sample.json` validates completed response package shape/completeness; `make adjudication-response-preflight PROTOCOL=protocol.json SAMPLE=sample.json RESPONSES=responses.json` checks completed responses against protocol/sample provenance before import; `make import-adjudication-responses ... PREFLIGHT_PROTOCOL=protocol.json PREFLIGHT_SAMPLE=sample.json` converts valid completed responses into D3/D7 gold package inputs with an optional import-time preflight guard when explicitly requested; `make write-phase0-adjudication-package ...` writes a strict Phase 0 manifest for those versioned package inputs. Hashes, artifact verification, protocol packages, preflight reports, sample packets, response validation, response preflight, guarded import files, and manifest assembly are reproducibility/protocol metadata, not validity evidence by themselves.
- Graph viz, JSON/CSV/Markdown/QDPX export, explicit export overwrite policy (`--no-overwrite` prevents clobbering existing artifacts; default remains overwrite for compatibility), optional CLI/MCP export-audit hash manifests, local verification, strict local publish/handoff preflight (`make export-publish-preflight` / `qc_cli.py export-publish-preflight`, with optional `SCOPE_LINT=1` / `--scope-lint` for Markdown/text scope-phrasing handoff checks), opt-in inline project-export preflight (`qc_cli.py project export ... --audit-manifest ... --publish-preflight [--scope-lint]`), opt-in MCP export preflight (`publish_preflight=True`, optional `scope_lint=True`), opt-in local hash-linked export-audit event logs (`--audit-log`, `audit_event_log=True`, `AUDIT_LOG=...`, `make verify-export-audit-log`, `qc_cli.py verify-export-audit-log`), and optional SQLite mirrors for verified event logs (`--audit-db`, `audit_event_db=True`, `AUDIT_DB=...`, `make mirror-export-audit-db`, `make verify-export-audit-db`, `qc_cli.py mirror-export-audit-db`, `qc_cli.py verify-export-audit-db`), per-stage memos, per-code audit trail; typed `PipelineContext`/results, fail-loud inter-stage checks, `llm_client` observability.

**Direction:** the end product is public and SOTA-targeting; the proven/measured/planned ledger, the architectural invariants, and the ranked roadmap are in `docs/PROJECT_THEORY_AND_GOALS.md` (§13/§13.1/§18). Recent structural work landed: span anchoring with deterministic fuzzy recovery for long near-verbatim spans (INV-1), the segment universe + exhaustive coverage (INV-8), D3 application-validity exact/span diagnostics plus externally fed D3 baseline rows with local per-baseline span-overlap diagnostics and D3 comparison protocol/preflight/score-time guard/metric-criteria metadata (INV-3 partial infrastructure), the first-class claim ledger object layer plus Phase 0 claim-anchor coverage accounting, bounded CLI/API/MCP scope/anchor-detail read surfaces, and explicit API/MCP/CLI claim-ledger pagination/count metadata or display (INV-9), retrieval-first/adversarial/BM25-style query-expanded ledger disconfirmation/claim/negative-case review first slices with bounded anchor-detail review context plus a gold-dependent D7 scorecard substrate with recall/precision Wilson intervals, local same-target/document span-IoU and Modified Hausdorff diagnostics for system and baseline rows, optional baseline point comparisons, retrieval/live-baseline prediction package validation, and D7 comparison protocol/preflight/metric-criteria/report-provenance/artifact-package/artifact-verifier/package-writer/package-runner metadata (INV-2/INV-6/INV-10 partial), first-party instruction/data separation for raw + derived prompt inputs plus explicit prompt-override placeholder exposure policy, repo-owned custom override wrapping, built-in INV-7 fixture coverage for custom override surfaces, external INV-7 live fixture manifest execution for governed held-out runs, an externally fed INV-7 prompt-injection scorecard substrate, and committed built-in INV-7 live canary artifacts including the current 5-fixture v2 canary (INV-7 partial), D4 codebook-quality protocol validation/result preflight/score-time guard plus local scorecard substrate, D6 bias-audit protocol validation/result preflight/score-time guard plus counterfactual and stratified-bias local scorecard substrates (INV-5 partial infrastructure only), D8 GT-fidelity protocol validation/result preflight/score-time guard plus local scorecard substrate (INV-4 protocol infrastructure only), D9 interpretive-preference protocol validation/result preflight/score-time guard plus local scorecard substrate, confidence-calibration protocol validation/result preflight/score-time guard plus local scorecard substrate, D10 cost/latency scorecard substrate from real observability rows plus last-local-run wall-clock metadata, Phase 0 scorecard input hashes plus adjudication protocol/sample-preflight/sample/response-validation/response-preflight/import/package-manifest substrate, category-saturation diagnostics plus diagnostic-driven sampling suggestions, loaded-document candidate export, theoretical-sampling result export, and theoretical-sampling protocol/candidate/result preflight metadata (INV-4 partial), corpus-scope/report-boundary contract slices including CLI/API read/update surfaces, missing/under-specified-scope warnings, CSV/Markdown claim-row boundary context, arbitrary-text scope phrasing lint, optional publish-preflight scope lint for Markdown/text handoff artifacts, and Phase 0 scope-record adequacy accounting, optional CLI/MCP export-audit hash manifests plus verification, publish/handoff preflight including optional inline `project export --publish-preflight` and MCP `publish_preflight=True`, opt-in local event logs, and optional SQLite event-log mirrors integrated into local CLI/script/MCP workflows as local integrity/provenance metadata, hard invalidation of stale higher-order outputs during incremental recode, opt-in thematic/GT higher-order refresh after incremental recode, and a project-level recode refresh policy with per-run force-on/force-off overrides (INV-11 partial). Next high-value lanes: semantic/embedding retrieval + held-out D7 evaluation/gold-set wiring and live baselines (INV-2 follow-up), broader held-out live injection evaluation execution/results (INV-7 follow-up), populated theoretical sampling execution/evidence beyond package recording (INV-4 when GT claims theory generation), and remaining default-policy follow-ups for INV-11.

## Architecture

```
qc_cli.py                                    # CLI entry point
  -> qc_clean/core/cli/commands/             # CLI command handlers (analyze, project, review)
  -> qc_clean/plugins/api/                   # FastAPI server (port 8002)
     -> review_ui.py                         # Browser-based code review UI (self-contained HTML)
     -> graph_ui.py                          # Interactive graph visualization (Cytoscape.js)
     -> qc_clean/core/pipeline/              # Stage-based pipeline engine
        -> pipeline_engine.py                # PipelineStage ABC + AnalysisPipeline orchestrator
        -> pipeline_factory.py               # create_pipeline(methodology) factory
        -> review.py                         # Human review loop (approve/reject/modify/merge/split)
        -> irr.py                            # Inter-rater reliability + multi-run stability
        -> saturation.py                     # Coding saturation detection
        -> theoretical_sampling.py           # Suggest next documents to code
        -> stages/                           # One file per pipeline stage
           -> ingest.py                      # Document ingestion + speaker detection
           -> thematic_coding.py             # Hierarchical code discovery
           -> perspective.py                 # Speaker/participant analysis
           -> relationship.py                # Entity & relationship mapping
           -> synthesis.py                   # Synthesis & recommendations
           -> cross_interview.py             # Cross-document pattern analysis
           -> negative_case.py               # Negative case analysis (runs LAST; disconfirming evidence)
           -> incremental_coding.py           # Incremental re-coding of new documents
           -> gt_constant_comparison.py      # GT: Iterative constant comparison coding (the live GT coder)
           -> gt_axial_coding.py             # GT: Axial coding (relationships)
           -> gt_selective_coding.py         # GT: Core category identification
           -> gt_theory_integration.py       # GT: Theoretical model building
     -> qc_clean/core/llm/llm_handler.py    # Thin adapter over llm_client for structured extraction
     -> qc_clean/core/grounding.py          # Span anchoring (INV-1): resolve quotes to char offsets+hash, verify_grounding
     -> qc_clean/core/segmentation.py       # Segment universe (INV-8): char-anchored segments + compute_coverage
     -> qc_clean/core/claims.py             # Claim ledger (INV-9): deterministic builders + summaries
     -> qc_clean/core/bench.py              # Eval-harness Phase 0 scorecard (D1-D10 local accounting substrates)
     -> qc_clean/core/d3_comparison_preflight.py # D3 comparison protocol/gold/baseline preflight (process metadata only)
     -> qc_clean/core/d4_codebook_quality_protocol.py # D4 codebook-quality protocol validator (process metadata only)
     -> qc_clean/core/d4_codebook_quality_preflight.py # D4 protocol/result preflight (process metadata only)
     -> qc_clean/core/d6_bias_protocol.py   # D6 bias-audit protocol package validator (process metadata only)
     -> qc_clean/core/d6_bias_preflight.py  # D6 protocol/result preflight (process metadata only)
     -> qc_clean/core/d8_gt_fidelity_protocol.py # D8 GT-fidelity protocol validator (process metadata only)
     -> qc_clean/core/d8_gt_fidelity_preflight.py # D8 protocol/result preflight (process metadata only)
     -> qc_clean/core/d9_interpretive_preference_protocol.py # D9 blind preference protocol validator (process metadata only)
     -> qc_clean/core/d9_interpretive_preference_preflight.py # D9 protocol/result preflight (process metadata only)
     -> qc_clean/core/confidence_calibration_protocol.py # Calibration protocol validator (process metadata only)
     -> qc_clean/core/confidence_calibration_preflight.py # Calibration protocol/result preflight (process metadata only)
     -> qc_clean/schemas/                    # Pydantic schemas
        -> domain.py                         # Unified domain model (ProjectState, Code, Codebook, AnalyticClaim, etc.)
        -> analysis_schemas.py               # LLM output schemas (CodeHierarchy, SpeakerAnalysis, etc.)
        -> gt_schemas.py                     # GT LLM output schemas (OpenCode, CoreCategory, etc.)
        -> adapters.py                       # Convert LLM output schemas to domain model
     -> qc_clean/core/persistence/           # JSON file-based project storage
        -> project_store.py                  # Save/load ProjectState as JSON files
     -> qc_clean/core/export/               # Export from ProjectState
        -> data_exporter.py                  # ProjectExporter (JSON/CSV/Markdown/QDPX)
qc_mcp_server.py                             # MCP server (20 tools for agent access)
simple_cli_web.py                            # Flask web UI (port 5003, subprocess-based)
start_server.py                              # Server startup script
```

### Key Files
- `qc_clean/schemas/domain.py` - Unified data model: ProjectState, Document, Corpus, Code, Codebook, CodeApplication, AnalyticClaim, etc.
- `qc_clean/core/claims.py` - First-class claim ledger builders/summaries for pipeline stages and read surfaces
- `qc_clean/core/pipeline/pipeline_engine.py` - PipelineStage ABC, PipelineContext (typed config), AnalysisPipeline orchestrator
- `qc_clean/core/pipeline/irr.py` - Inter-rater reliability + multi-run stability analysis
- `qc_clean/core/pipeline/review.py` - ReviewManager for human-in-the-loop code review
- `qc_clean/core/persistence/project_store.py` - JSON persistence for ProjectState
- `qc_clean/schemas/adapters.py` - Convert LLM output schemas to domain model
- `qc_clean/plugins/api/api_server.py` - API server (delegates to pipeline)
- `qc_clean/plugins/api/review_ui.py` - Self-contained HTML review UI (string.Template)
- `qc_clean/plugins/api/graph_ui.py` - Interactive graph visualization with Cytoscape.js (string.Template)
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` - Iterative segment-by-segment GT coding with saturation detection
- `qc_clean/core/pipeline/stages/incremental_coding.py` - Code new documents against existing codebook
- `qc_clean/core/llm/llm_handler.py` - Thin adapter over `llm_client.acall_llm_structured` (QC config wiring, LLMError wrapping, system prompt)
- `qc_clean/core/export/data_exporter.py` - ProjectExporter (JSON/CSV/Markdown/QDPX from ProjectState)
- `qc_cli.py` - CLI interface (analyze, project, review, status, server)
- `qc_mcp_server.py` - MCP server: 20 tools for project management, pipeline execution, codebook inspection, review, IRR/stability, export
- `tests/` - Deterministic tests plus live LLM E2E tests (`live_llm`, run separately with `make test-e2e`)

### How It Works
- `project run` runs the pipeline locally (no server needed); `analyze` uses the API server
- CLI is a pure HTTP client for `analyze` -- all analysis runs on the API server
- API server creates an `AnalysisPipeline` via the factory and runs it
- Each stage reads from / writes to `ProjectState` (single Pydantic model) via typed `PipelineContext`
- Substantive stages write `state.claims` entries or explicit no-claims events (INV-9)
- Pipeline pauses at human review checkpoints when `enable_human_review=True`
- `ReviewManager` handles approve/reject/modify/merge/split of codes
- `ProjectStore` saves/loads entire ProjectState as JSON (no database needed)
- Cross-interview analysis runs automatically for multi-document corpora
- Saturation detection compares codebooks across iterations
- Default model: `gpt-5-mini`. LLMHandler passes the bare model name to `llm_client`, whose default `routing_policy="openrouter"` resolves it to `openrouter/openai/gpt-5-mini` — so calls route through **OpenRouter** (`OPENROUTER_API_KEY`), not the OpenAI API directly. LLMHandler is a thin adapter over the shared `llm_client` library (retry, backoff, structured extraction via `acall_llm_structured` / `acall_llm_structured_batch`)
- `analysis_schemas.py` defines LLM output shapes; `adapters.py` converts them to domain objects
- Every stage produces an analytical memo (LLM reasoning trail) saved to `state.memos`
- GT constant comparison: segments documents by speaker turns or paragraph chunks, iteratively codes each segment against an evolving codebook, stops when saturation reached
- Incremental coding: `project recode` codes only uncoded documents against the existing codebook, then re-runs downstream state-driven stages; `project add-docs --recode` adds documents and invokes that same recode path in one explicit opt-in command
- Graph visualization: `/graph/{project_id}` serves interactive Cytoscape.js graphs (code hierarchy, relationships, entity map)
- Fail-loud: downstream stages raise `RuntimeError` via `ctx.require()` if upstream data is missing (no silent empty-data fallbacks). Review raises `ValueError` on unknown target types.
- Observability: LLMHandler logs model/schema/prompt_len on call, cost/usage on response. All stages log entry context (doc/code counts, model). Pipeline engine logs state context on failure.

## Working Commands

```bash
# Start server first (only needed for `analyze` command)
python start_server.py

# Run analysis via API
python qc_cli.py analyze --files file1.docx file2.docx --format json
python qc_cli.py analyze --directory /path/to/interviews/ --format json --output-file results.json

# Project management (local, no server needed)
python qc_cli.py project create --name "My Study" --methodology grounded_theory
python qc_cli.py project create --name "My Study" --methodology grounded_theory --auto-refresh-higher-order-on-recode
python qc_cli.py project list
python qc_cli.py project show <project_id>
python qc_cli.py project claims <project_id> --limit 20 --offset 0
python qc_cli.py project claims <project_id> --show-scope
python qc_cli.py project claims <project_id> --show-anchors
python qc_cli.py project add-docs <project_id> --files interview1.docx interview2.docx
python qc_cli.py project add-docs <project_id> --files interview3.docx --recode --model gpt-5-mini
python qc_cli.py project add-docs <project_id> --files interview3.docx --recode --no-refresh-higher-order
python qc_cli.py project recode-policy <project_id> --enable-auto-refresh-higher-order
python qc_cli.py project adjudication-sample <project_id> --output-file sample.json
make validate-adjudication-protocol PROTOCOL=protocol.json
make adjudication-protocol-preflight PROTOCOL=protocol.json SAMPLE=sample.json
make validate-adjudication-responses PACKAGE=sample.json
make adjudication-response-preflight PROTOCOL=protocol.json SAMPLE=sample.json RESPONSES=responses.json
make import-adjudication-responses PACKAGE=sample.json GOLD_SET_ID=study-v1 DATASET_NAME="Study dev labels" CODER_COUNT=1 ADJUDICATOR=coder-1 PROTOCOL="Single adjudicator review" PREFLIGHT_PROTOCOL=protocol.json PREFLIGHT_SAMPLE=sample.json D3_OUTPUT=d3_gold.json D7_OUTPUT=d7_gold.json
python qc_cli.py import-adjudication-responses sample.json --gold-set-id study-v1 --dataset-name "Study dev labels" --coder-count 1 --adjudicator coder-1 --protocol "Single adjudicator review" --protocol-package protocol.json --sample-package sample.json --output-d3 d3_gold.json --output-d7 d7_gold.json
python qc_cli.py validate-d3-gold d3_gold.json
python qc_cli.py validate-d7-gold d7_gold.json
python qc_cli.py validate-d3-comparison-protocol d3_protocol.json
python qc_cli.py d3-comparison-preflight d3_protocol.json d3_gold.json baseline_a.json baseline_b.json
python qc_cli.py validate-d7-comparison-protocol d7_protocol.json
python qc_cli.py d7-comparison-preflight d7_protocol.json d7_gold.json lexical.json embedding.json
make write-phase0-adjudication-package ID=<project_id> OUTPUT=phase0_package.json D3_GOLD=d3_gold.json GOLD=d7_gold.json
make lint-scope-phrasing ID=<project_id> INPUT=report.md
python qc_cli.py lint-scope-phrasing <project_id> --input-file report.md
python qc_cli.py validate-d4-codebook-quality-protocol protocol.json
python qc_cli.py d4-codebook-quality-preflight protocol.json --quality-file quality.json
python qc_cli.py validate-d6-bias-protocol protocol.json
python qc_cli.py d6-bias-preflight protocol.json --stratified-file bias_stratified.json --counterfactual-file bias_counterfactual.json
make validate-d8-gt-fidelity-protocol PROTOCOL=protocol.json
make d8-gt-fidelity-preflight PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json
python qc_cli.py validate-d8-gt-fidelity-protocol protocol.json
python qc_cli.py d8-gt-fidelity-preflight protocol.json --gt-fidelity-file gt_fidelity.json
make bench ID=<project_id> D8_PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json
make validate-d9-interpretive-preference-protocol PROTOCOL=protocol.json
make d9-interpretive-preference-preflight PROTOCOL=protocol.json PREFERENCE=preference.json
python qc_cli.py validate-d9-interpretive-preference-protocol protocol.json
python qc_cli.py d9-interpretive-preference-preflight protocol.json --preference-file preference.json
make bench ID=<project_id> D9_PROTOCOL=protocol.json PREFERENCE=preference.json
make validate-confidence-calibration-protocol PROTOCOL=protocol.json
make confidence-calibration-preflight PROTOCOL=protocol.json CALIBRATION=calibration.json
python qc_cli.py validate-confidence-calibration-protocol protocol.json
python qc_cli.py confidence-calibration-preflight protocol.json --calibration-file calibration.json
make bench ID=<project_id> CONFIDENCE_PROTOCOL=protocol.json CALIBRATION=calibration.json
make export-audit-manifest ID=<project_id> FORMAT=markdown ARTIFACTS="report.md" OUTPUT=manifest.json AUDIT_LOG=export_audit_events.jsonl AUDIT_DB=export_audit_events.sqlite
make verify-export-audit-manifest MANIFEST=manifest.json BASE_DIR=. ID=<project_id> AUDIT_LOG=export_audit_events.jsonl AUDIT_DB=export_audit_events.sqlite
make export-publish-preflight MANIFEST=manifest.json BASE_DIR=. ID=<project_id> AUDIT_LOG=export_audit_events.jsonl AUDIT_DB=export_audit_events.sqlite
make export-publish-preflight MANIFEST=manifest.json BASE_DIR=. ID=<project_id> SCOPE_LINT=1
make verify-export-audit-log LOG=export_audit_events.jsonl
make mirror-export-audit-db LOG=export_audit_events.jsonl DB=export_audit_events.sqlite
make verify-export-audit-db DB=export_audit_events.sqlite
python qc_cli.py export-audit-manifest <project_id> --format markdown --artifact report.md --output manifest.json --audit-log export_audit_events.jsonl --audit-db export_audit_events.sqlite
python qc_cli.py verify-export-audit-manifest manifest.json --base-dir . --project-id <project_id> --audit-log export_audit_events.jsonl --audit-db export_audit_events.sqlite
python qc_cli.py export-publish-preflight --manifest manifest.json --base-dir . --project-id <project_id> --audit-log export_audit_events.jsonl --audit-db export_audit_events.sqlite
python qc_cli.py export-publish-preflight --manifest manifest.json --base-dir . --project-id <project_id> --scope-lint
python qc_cli.py project export <project_id> --format markdown --output-file report.md --audit-manifest manifest.json --publish-preflight --scope-lint
python qc_cli.py verify-export-audit-log export_audit_events.jsonl
python qc_cli.py mirror-export-audit-db export_audit_events.jsonl --db export_audit_events.sqlite
python qc_cli.py verify-export-audit-db export_audit_events.sqlite
python qc_cli.py bench <project_id>                                     # Phase 0 scorecard (same engine as make bench)
python qc_cli.py bench <project_id> --confidence-calibration-protocol-file protocol.json --confidence-calibration-file calibration.json  # Same Phase 0 file/protocol flags as scripts/bench_phase0.py
python qc_cli.py bench <project_id> --artifact-dir benchmark_results    # Write versioned Phase 0 scorecard package
python qc_cli.py bench-package phase0_package.json                      # Run strict Phase 0 package manifest, including package-local projects_dir when supplied
python qc_cli.py write-phase0-adjudication-package <project_id> --output phase0_package.json --d3-gold-file d3_gold.json --gold-file d7_gold.json  # Write strict Phase 0 manifest for imported D3/D7 gold
python qc_cli.py validate-adjudication-protocol protocol.json           # Validate adjudication protocol metadata
python qc_cli.py adjudication-protocol-preflight protocol.json sample.json  # Preflight protocol/sample package match
python qc_cli.py validate-adjudication-responses responses.json         # Validate completed adjudication response package
python qc_cli.py adjudication-response-preflight protocol.json sample.json responses.json  # Preflight completed responses before import
python qc_cli.py import-adjudication-responses responses.json --gold-set-id study-v1 --dataset-name "Study dev labels" --coder-count 1 --adjudicator coder-1 --protocol "Single adjudicator review" --protocol-package protocol.json --sample-package sample.json --output-d3 d3_gold.json --output-d7 d7_gold.json  # Convert valid responses to D3/D7 gold package inputs
python qc_cli.py verify-phase0-benchmark-artifact benchmark_results/run-dir/manifest.json  # Verify Phase 0 artifact hashes/metadata

# Run pipeline on a project (local, no server needed)
python qc_cli.py project run <project_id>                          # run full pipeline
python qc_cli.py project run <project_id> --model gpt-5-mini       # specify model
python qc_cli.py project run <project_id> --review                  # pause for human review

# Export results
python qc_cli.py project export <project_id> --format json --output-file results.json
python qc_cli.py project export <project_id> --format csv --output-dir ./export/
python qc_cli.py project export <project_id> --format markdown --output-file report.md
python qc_cli.py project export <project_id> --format markdown --output-file report.md --no-overwrite  # Fail if the target already exists
python qc_cli.py project export <project_id> --format markdown --output-file report.md --audit-manifest report.manifest.json --verify-audit-manifest
python qc_cli.py project export <project_id> --format markdown --output-file report.md --audit-manifest report.manifest.json --verify-audit-manifest --audit-log export_audit_events.jsonl --audit-db export_audit_events.sqlite
python qc_cli.py project export <project_id> --format qdpx --output-file export.qdpx  # ATLAS.ti/NVivo

# Inter-rater reliability (runs coding N times with prompt variation)
python qc_cli.py project irr <project_id>                                     # 3 passes, default model
python qc_cli.py project irr <project_id> --passes 5                          # 5 passes
python qc_cli.py project irr <project_id> --models gpt-5-mini claude-sonnet-4-5-20250929  # multi-model

# Multi-run stability (same prompt N times, measures LLM non-determinism)
python qc_cli.py project stability <project_id>                               # 5 runs, default model
python qc_cli.py project stability <project_id> --runs 10                     # 10 runs
python qc_cli.py project stability <project_id> --model gpt-5-mini            # specify model

# Incremental coding (add new docs then re-code without starting over)
python qc_cli.py project recode <project_id>                                  # recode with defaults
python qc_cli.py project recode <project_id> --model gpt-5                    # specify model
python qc_cli.py project recode <project_id> --refresh-higher-order           # force refresh higher-order outputs for this run
python qc_cli.py project recode <project_id> --no-refresh-higher-order        # force hard-invalidation mode for this run
python qc_cli.py project recode-policy <project_id>                           # inspect project-level refresh default
python qc_cli.py project recode-policy <project_id> --enable-auto-refresh-higher-order  # make refresh the project default
python qc_cli.py project recode-policy <project_id> --disable-auto-refresh-higher-order # make hard invalidation the project default
python qc_cli.py project add-docs <project_id> --files new.docx --recode       # add then recode explicitly

# Review codes (CLI)
python qc_cli.py review <project_id>
python qc_cli.py review <project_id> --approve-all
python qc_cli.py review <project_id> --file decisions.json

# Review codes (browser - requires server running)
# Open http://localhost:8002/review/<project_id>

# Graph visualization (browser - requires server running)
# Open http://localhost:8002/graph/<project_id>
# Three views: Code Hierarchy, Code Relationships, Entity Map

# Check status
python qc_cli.py status --server
python qc_cli.py status --job <job_id>

# MCP server (for agent access - 20 tools)
python qc_mcp_server.py                                                   # run via stdio
# Tools: qc_list_projects, qc_create_project, qc_show_project, qc_delete_project,
#   qc_add_documents, qc_run_pipeline, qc_run_stage, qc_recode,
#   qc_run_irr, qc_run_stability, qc_get_codebook, qc_get_applications,
#   qc_get_memos, qc_get_synthesis, qc_review_summary, qc_approve_all_codes,
#   qc_review_codes, qc_export_markdown, qc_export_json, qc_grounding_report

# Run deterministic tests (excludes paid live LLM E2E)
make test

# Run live LLM E2E (requires OPENROUTER_API_KEY for the default gpt-5-mini route)
make test-e2e
```

## Configuration

API keys are read from environment variables by `llm_client` (via litellm). Default model: `gpt-5-mini`.

Key env vars:
- `OPENROUTER_API_KEY` -- **the key actually used by default** (`llm_client` routes the default model through OpenRouter). The live E2E tests gate on this key.
- `OPENAI_API_KEY` / `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` -- used only when you route direct to a provider (e.g. `--model gemini/...`, or with `routing_policy="direct"`)
- `qc_clean/config/unified_config.py` -- `UnifiedConfig` dataclass reads env vars: `API_PROVIDER`, `MODEL`, `METHODOLOGY`, `CODING_APPROACH`, `VALIDATION_LEVEL`, `TEMPERATURE`
- `qc_clean/core/config/env_config.py` -- Active server config (used by `start_server.py`)

## Model Selection Notes

Default model is `gpt-5-mini` (cheap, adequate for most stages). Can switch per-run with `--model`. Places where a stronger model (e.g. Claude Sonnet/Opus, GPT-5) could matter:

- **IRR results** — if kappa scores come back low, a better model might produce more consistent/accurate codes
- **GT axial/selective coding** — requires sophisticated reasoning about relationships between categories; if output quality is shallow, upgrading the model could help
- **Negative case analysis** — asking "what contradicts these findings?" is a harder reasoning task; now implemented as `NegativeCaseStage`

### Local Models (Ollama, vLLM, etc.)

LLMHandler uses `llm_client` which uses LiteLLM under the hood. Any LiteLLM-supported provider works:

```bash
# Ollama (install from ollama.com, then pull a model)
ollama pull llama3.1
python qc_cli.py project run <id> --model ollama/llama3.1

# vLLM or any OpenAI-compatible server
OPENAI_API_BASE=http://localhost:8000/v1 python qc_cli.py project run <id> --model openai/my-local-model

# Via MCP
qc_run_pipeline(project_id="...", model="ollama/llama3.1")
```

Local models work for all pipeline stages but quality varies. For GT axial/selective coding and negative case analysis, cloud models (GPT-5-mini+) tend to produce better structured output.

## Development Notes

- This is a research tool, not a production system
- Interview data files are gitignored (sensitive content)
- `src/` directory is legacy code (gitignored)
- **Gates need full deps**: `make check` (test + ruff lint + docs-check) requires `pip install -r requirements.txt` in `.venv` — `pypdf` and `ruff` are gate dependencies, and `docs-check` imports `enforced_planning.worktree_paths` (vendored from `~/projects/enforced-planning`). A venv missing these makes the gates red even though the code is fine.
- **Single ingestion path**: all file reading (CLI and API server) goes through `qc_clean/core/cli/utils/file_handler.py:read_file_content` (uses `pypdf`, not the unmaintained PyPDF2). `api_client.py` delegates to it — do not reintroduce a divergent reader.
- **MCP export is sandboxed**: `qc_export_json/markdown` confine `output_file` to `<projects_dir>/exports/` via `_confine_export_path` (agent-driven surface, prevents arbitrary writes). The CLI exporter keeps full path freedom for the trusted local user.

## Competitive Landscape & Positioning

Moved to the canonical theory doc: `docs/PROJECT_THEORY_AND_GOALS.md` §2 (granular feature matrix vs ATLAS.ti/MAXQDA/NVivo/QualCoder + the research prototypes) and §19 (prior art worth learning from). The honest positioning is an *auditable, methodology-aware integration* — **not** 'the only tool that does X' / SOTA (see claim discipline, §14).

## E2E Validation (updated 2026-06-21)

Pipeline validated end-to-end against real interview transcripts using gpt-5-mini. Automated E2E tests in `tests/test_e2e.py` (requires `OPENROUTER_API_KEY` for the default OpenRouter route):

- **Default methodology, 1 document**: 14 codes, 17 applications, 2 speakers detected, 7 memos, negative case analysis
- **Default methodology, 2 documents**: 14 codes, 30 applications across 2 docs, cross-interview analysis with consensus/divergent themes
- **Grounded theory, 1 document**: 8 open codes, 40 applications, 3 core categories, theoretical model generated, 6 memos
- **Incremental coding**: Initial pipeline (12 codes, 19 apps) + add doc + recode = 17 codes, 32 apps, iteration 2
- **Graph data**: 13 code nodes, 25 entity nodes, 12 entity relationships from completed state
- **Export**: JSON, Markdown, CSV all produce valid output from real pipeline results
- **Exhaustive coverage**: `exhaustive_coding=True` gives examined-and-judged coverage over the segment universe
- **Application-level IRR**: `run_irr_analysis(application_level=True)` computes positive segment x code application agreement plus segment-decision agreement (`coded` / `no_code` / `not_examined`)

Previous manual E2E (2026-02-12):
- Default 1-doc: 12 codes, 29 applications, 8 speakers (focus group)
- Default 3-doc: 12 codes, 36 properly-attributed applications, cross-interview analysis
- GT 1-doc: 25 open codes, 14 axial relationships, 3 core categories, theoretical model

Bugs found and fixed during E2E testing:
- Speaker detection: added timestamp format ("Name   0:03") alongside colon format; runs on pre-loaded docs
- Quote attribution: replaced blind duplication with substring matching to correctly attribute quotes to source documents
- Perspective stage: uses detected speaker count (not document count) to determine single vs multi-speaker mode
- Export hierarchy: case-insensitive parent_id matching + recursive tree rendering for arbitrary depth
- NegativeCase.implication: made optional (LLM sometimes omits it, causing validation failure)
- Incremental pipeline: removed ctx-dependent stages (Perspective/Relationship/Synthesis) that require data from ThematicCodingStage

## Design Lessons (from E2E testing)

1. **LLMs don't reliably fill every schema field.** Even with JSON mode, gpt-5-mini sometimes omits fields. All LLM-facing Pydantic schema fields should have defaults unless you truly want the pipeline to crash on omission. Fixed: all 30 `List` fields and 2 `Dict` fields across `analysis_schemas.py`, `gt_schemas.py`, and `negative_case.py` now have `default_factory`.

2. **Unit tests with mocks don't catch integration bugs.** Hundreds of unit tests passed, but two real bugs hid in the seams between stages: (a) `NegativeCase.implication` required but LLM omits it, (b) incremental pipeline included stages that depend on data from a stage that doesn't run. Only E2E with real LLM calls found these.

3. **Fail-loud makes integration bugs easy to diagnose.** The `ctx.require()` pattern immediately told us which field was missing and which stage needed it. Without it, the bug would have produced silent garbage output.

4. **LLM output is non-deterministic.** Same input produces 8-14 codes across runs. E2E assertions must be loose (`>= 3` not `== 12`). This is inherent to LLM-powered systems.

5. **Schema robustness** — all LLM-facing `List`/`Dict` fields now default to empty. The `TheoreticalModel.core_category` property accessor returns `""` for empty list instead of crashing.

## Known Technical Debt

1. **Schema duplication**: `analysis_schemas.py` / `gt_schemas.py` (LLM output shapes) and `domain.py` (internal model) overlap; this is intentional — adapters bridge them
2. **`methodology_config.py`**: Only imported by tests now (not production code); could be removed if tests are refactored
3. **Two segmenters** (refactor candidate): `core/segmentation.py` (canonical, char-anchored typed `Segment`) and the older dict-based segmenter inside `gt_constant_comparison.py` (`segment_documents`/`group_into_chunks`, strips offsets). The speaker-turn *regex* is now shared (`segmentation.speaker_turn_pattern`), but GT still re-segments into untyped dicts and 500-word chunks. Full unification (GT consumes typed `Segment`s + chunking moved into `segment_corpus`) would give GT exact offsets and one segmenter — but it changes GT's non-speaker granularity and ~7 direct tests, so it was deferred (not a pure refactor). Do it as its own focused change, behavior-preserving via a `chunk_target_words` param.

## Academic Standards & Honest State

Superseded by the canonical theory doc: the proven/measured/planned **state ledger** is `docs/PROJECT_THEORY_AND_GOALS.md` §13, the **architectural invariants** (INV-0..11, each MET/PARTIAL/UNMET) are §13.1, and the academic references + prior art are §19. Do **not** re-introduce a 'Tier 2 complete / validated' ledger here — it contradicts the invariants (e.g. disconfirmation is INV-2 PARTIAL / INV-6 PARTIAL and not credibility evidence; `project irr` defaults to codebook-discovery agreement; `--application-level` gives positive segment x code application agreement and segment-decision agreement).

## Next Steps

The ranked roadmap (invariants before features) lives in `docs/PROJECT_THEORY_AND_GOALS.md` §18 — evaluation harness (keystone), span anchoring (done), segment universe + exhaustive coding (INV-8, done), claim ledger object layer (INV-9, mostly done), retrieval-first/adversarial/BM25-style query-expanded disconfirmation/adjudication first slices plus D7 recall/precision Wilson intervals and optional baseline point comparisons (INV-2/INV-6/INV-10 partial), raw + derived instruction/data separation first slices plus externally fed INV-7 prompt-injection scorecard substrate (INV-7 partial), category-saturation diagnostics (INV-4 partial), corpus-scope/report-boundary contract first slices including missing-scope warnings, claim-row boundary context, and scope phrasing lint, relationship-review and negative-case-review API/MCP/browser first slices, adjudication sample export and response-validation substrate, semantic retrieval + held-out D7 evaluation/live baselines, live prompt-injection evaluation, theoretical sampling protocol, sampling-frame adequacy evaluation, etc. Don't duplicate it here.

## prompt_eval Integration (Prompt Optimization)

### Infrastructure

`PipelineContext.prompt_overrides` allows passing custom prompts to stages without editing source code. Supported stages are centrally declared in `qc_clean/core/prompt_override_registry.py`: `thematic_coding`, `gt_constant_comparison`. Overrides must include the required protected data placeholder for that stage (`{combined_text}` for thematic, `{segment_text}` for GT constant comparison) as a bare placeholder. Exposed data and metadata are registry-declared: thematic exposes `{num_interviews}` metadata; GT constant comparison exposes optional protected data `{codebook_context}` plus metadata `{seg_idx}`, `{total_segments}`, and `{doc_name}`. Missing placeholders, unknown placeholders, undeclared renderer values, item/attribute access, conversion flags, and format specs raise `ValueError` before an LLM call. Run `make lint-prompt-overrides` when adding or changing override surfaces; it fails if source uses an unregistered `prompt_overrides` key or a registered surface disappears from source. The `qc_run_pipeline` MCP tool accepts `prompt_overrides` dict.

Both MCP servers (QC + prompt_eval) are configured in `~/projects/.mcp.json`. An agent with access to both can orchestrate the full optimization loop.

### Rubric for Codebook Quality (llm_judge)

```
Score the qualitative codebook on a scale of 0.0 to 1.0.

1. CODE CLARITY (0-0.25): Are code names specific and descriptive?
   Do descriptions clearly define what data belongs under each code?
   Are codes mutually exclusive (minimal overlap)?

2. GROUNDING (0-0.25): Is each code supported by verbatim quotes
   from the data? Are the quotes relevant and illustrative?
   Do mention_counts reflect actual data frequency?

3. COVERAGE (0-0.25): Do the codes capture the major themes in the
   data? Are important patterns missing? Is there appropriate balance
   between breadth and depth? Is the hierarchy meaningful?

4. ANALYTICAL DEPTH (0-0.25): Do codes reveal latent patterns (not
   just surface content)? Is there evidence of interpretive work beyond
   manifest content? Are the analytical memos insightful?
```

### Agent Workflow (using both MCP servers)

**Workflow 1: Score existing results** (no code changes needed)
1. `qc_get_codebook(project_id)` → codebook JSON
2. `evaluate_output(output=codebook_json, evaluator_name="llm_judge", rubric=RUBRIC)` → score 0.0-1.0
3. Report score to user

**Workflow 2: A/B test coding prompts** (uses prompt_overrides)
1. `qc_run_pipeline(project_id, prompt_overrides={"thematic_coding": variant_a_prompt})` → result A
2. `evaluate_output(output=codebook_a, evaluator_name="llm_judge", rubric=RUBRIC)` → score A
3. Create new project, run with variant B prompt → score B
4. `compare(path, variant_a, variant_b)` → statistical comparison

**Workflow 3: Automated prompt optimization** (uses instruction_search)
1. Extract current thematic_coding prompt from `stages/thematic_coding.py`
2. Build prompt_eval experiment with interview text as input, CodeHierarchy as response_model
3. `run_experiment_tool(experiment_json=..., evaluator_name="llm_judge", rubric=RUBRIC)` → baseline
4. Use `instruction_search` to hill-climb from baseline prompt
5. Apply best prompt via `qc_run_pipeline(prompt_overrides={"thematic_coding": best_prompt})`

### Target Prompts (by impact)

| Stage | Prompt Location | Placeholders | Impact |
|-------|----------------|--------------|--------|
| `thematic_coding` | `stages/thematic_coding.py:_build_phase1_prompt()` | `{combined_text}`, `{num_interviews}` | Highest — determines all downstream quality |
| `gt_constant_comparison` | `stages/gt_constant_comparison.py:_build_comparison_prompt()` | `{codebook_context}`, `{segment_text}`, `{seg_idx}`, `{total_segments}`, `{doc_name}` | Highest for GT |
| `perspective` | `stages/perspective.py:_build_phase2_prompt()` | Not yet overridable | Medium |
| `negative_case` | `stages/negative_case.py` inline | Not yet overridable | Medium |
| `synthesis` | `stages/synthesis.py:_build_phase4_prompt()` | Not yet overridable | Low (downstream) |

### Evaluator Options

| Evaluator | Use Case | Notes |
|-----------|----------|-------|
| `llm_judge` + rubric | General quality scoring | Best for open-ended quality assessment. Use gpt-5 or claude as judge for reliability |
| `kappa` | Agreement with gold standard | Requires human-coded gold standard. Extract code names from CodeHierarchy |
| Custom function | Domain-specific metrics | e.g., code count in range, hierarchy depth, quote coverage ratio |

## Related Projects

| Project | Path | Relationship |
|---------|------|-------------|
| **llm_client** | `~/projects/llm_client/` | Shared LLM calling library. QC's `LLMHandler` is a thin adapter over `acall_llm_structured` |
| **prompt_eval** | `~/projects/prompt_eval/` | General-purpose prompt improvement system (v0.2.0). 4 evaluators (llm_judge, kappa, exact_match, contains), 3 optimization strategies (grid search, few-shot selection, instruction search), persistence, MCP server with all 4 evaluators as built-ins. 104 tests. |

## Commands

```bash
make test               # Run deterministic test suite (excludes live LLM E2E)
make test-quick         # Run tests, minimal output
make test-e2e           # Run live LLM E2E tests
make test-all           # Run deterministic tests and live LLM E2E tests
make lint               # Run Ruff fatal-error lint gate
make docs-check         # Run documentation and governance checks
make check              # Run deterministic tests + lint + docs checks
make status             # Show git status
make bench ID=<project_id>              # Phase 0 scorecard (D1-D10 local accounting substrates)
python qc_cli.py bench <project_id>     # Same Phase 0 scorecard through the canonical CLI; mirrors scripts/bench_phase0.py file/protocol flags
python qc_cli.py bench-package phase0_package.json  # Run a strict Phase 0 package manifest through the canonical CLI, including package-local projects_dir when supplied
make validate-d4-codebook-quality-protocol PROTOCOL=protocol.json  # Validate pre-evaluation D4 rubric protocol metadata
make d4-codebook-quality-preflight PROTOCOL=protocol.json QUALITY=quality.json  # Preflight D4 result file against protocol
python qc_cli.py validate-d4-codebook-quality-protocol protocol.json  # Canonical CLI wrapper for D4 protocol validation
python qc_cli.py d4-codebook-quality-preflight protocol.json --quality-file quality.json  # Canonical CLI wrapper for D4 protocol/result preflight
make bench ID=<project_id> D4_PROTOCOL=protocol.json CODEBOOK_QUALITY=quality.json  # Guard D4 scoring with protocol preflight
make validate-d6-bias-protocol PROTOCOL=protocol.json  # Validate pre-run D6 bias-audit protocol metadata
make d6-bias-preflight PROTOCOL=protocol.json STRATIFIED=bias_stratified.json COUNTERFACTUAL=bias_counterfactual.json  # Preflight D6 result files against protocol
python qc_cli.py validate-d6-bias-protocol protocol.json  # Canonical CLI wrapper for D6 protocol validation
python qc_cli.py d6-bias-preflight protocol.json --stratified-file bias_stratified.json --counterfactual-file bias_counterfactual.json  # Canonical CLI wrapper for D6 protocol/result preflight
make bench ID=<project_id> D6_PROTOCOL=protocol.json BIAS_STRATIFIED=bias_stratified.json BIAS_COUNTERFACTUAL=bias_counterfactual.json  # Guard D6 scoring with protocol preflight
make validate-d8-gt-fidelity-protocol PROTOCOL=protocol.json  # Validate pre-evaluation D8 GT-fidelity protocol metadata
make d8-gt-fidelity-preflight PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json  # Preflight D8 result file against protocol
python qc_cli.py validate-d8-gt-fidelity-protocol protocol.json  # Canonical CLI wrapper for D8 protocol validation
python qc_cli.py d8-gt-fidelity-preflight protocol.json --gt-fidelity-file gt_fidelity.json  # Canonical CLI wrapper for D8 protocol/result preflight
make bench ID=<project_id> D8_PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json  # Guard D8 scoring with protocol preflight
make validate-d9-interpretive-preference-protocol PROTOCOL=protocol.json  # Validate pre-evaluation D9 preference protocol metadata
make d9-interpretive-preference-preflight PROTOCOL=protocol.json PREFERENCE=preference.json  # Preflight D9 result file against protocol
python qc_cli.py validate-d9-interpretive-preference-protocol protocol.json  # Canonical CLI wrapper for D9 protocol validation
python qc_cli.py d9-interpretive-preference-preflight protocol.json --preference-file preference.json  # Canonical CLI wrapper for D9 protocol/result preflight
make bench ID=<project_id> D9_PROTOCOL=protocol.json PREFERENCE=preference.json  # Guard D9 scoring with protocol preflight
make validate-confidence-calibration-protocol PROTOCOL=protocol.json  # Validate pre-evaluation confidence-calibration protocol metadata
make confidence-calibration-preflight PROTOCOL=protocol.json CALIBRATION=calibration.json  # Preflight calibration result file against protocol
python qc_cli.py validate-confidence-calibration-protocol protocol.json  # Canonical CLI wrapper for confidence-calibration protocol validation
python qc_cli.py confidence-calibration-preflight protocol.json --calibration-file calibration.json  # Canonical CLI wrapper for confidence-calibration protocol/result preflight
make bench ID=<project_id> CONFIDENCE_PROTOCOL=protocol.json CALIBRATION=calibration.json  # Guard calibration scoring with protocol preflight
make bench ID=<project_id> GOLD=gold.json BASELINES=baselines.json  # Add external D7 gold/baselines without mutating project state
make bench ID=<project_id> BIAS_STRATIFIED=bias_stratified.json  # Add external D6 stratified correctness rows without mutating state
make bench ID=<project_id> PROMPT_INJECTION=inv7.json  # Add external INV-7 fixture results without mutating state
make bench ID=<project_id> PROMPT_INJECTION=inv7.json INV7_PROTOCOL=inv7_live_protocol.json  # Score INV-7 with live protocol preflight guard
make bench ID=<project_id> OBS_DB=path TRACE_ID=trace  # Override D10 observability DB / exact trace
make bench ID=<project_id> ARTIFACT_DIR=benchmark_results  # Write versioned Phase 0 scorecard package
make verify-phase0-benchmark-artifact ARTIFACT=benchmark_results/run-dir  # Verify Phase 0 artifact scorecard/timing/manifest hashes
make adjudication-sample ID=<project_id> OUTPUT=sample.json  # Export unlabeled human/expert review sample packet
make validate-adjudication-protocol PROTOCOL=protocol.json  # Validate pre-registered adjudication protocol metadata
python qc_cli.py validate-adjudication-protocol protocol.json  # Canonical CLI wrapper for protocol validation
make adjudication-protocol-preflight PROTOCOL=protocol.json SAMPLE=sample.json  # Preflight protocol/sample package match before labeling
python qc_cli.py adjudication-protocol-preflight protocol.json sample.json  # Canonical CLI wrapper for protocol/sample preflight
make validate-adjudication-responses PACKAGE=sample.json  # Validate completed adjudication response package shape/completeness
python qc_cli.py validate-adjudication-responses responses.json  # Canonical CLI wrapper for response validation
make adjudication-response-preflight PROTOCOL=protocol.json SAMPLE=sample.json RESPONSES=responses.json  # Preflight completed responses against protocol/sample provenance before import
python qc_cli.py adjudication-response-preflight protocol.json sample.json responses.json  # Canonical CLI wrapper for response preflight
make import-adjudication-responses PACKAGE=sample.json GOLD_SET_ID=study-v1 DATASET_NAME="Study dev labels" CODER_COUNT=1 ADJUDICATOR=coder-1 PROTOCOL="Single adjudicator review" PREFLIGHT_PROTOCOL=protocol.json PREFLIGHT_SAMPLE=sample.json D3_OUTPUT=d3_gold.json D7_OUTPUT=d7_gold.json  # Convert valid responses to D3/D7 gold package inputs with an import-time provenance guard
python qc_cli.py import-adjudication-responses responses.json --gold-set-id study-v1 --dataset-name "Study dev labels" --coder-count 1 --adjudicator coder-1 --protocol "Single adjudicator review" --protocol-package protocol.json --sample-package sample.json --output-d3 d3_gold.json --output-d7 d7_gold.json  # Canonical CLI wrapper for guarded response import
make write-phase0-adjudication-package ID=<project_id> OUTPUT=phase0_package.json D3_GOLD=d3_gold.json GOLD=d7_gold.json  # Write strict Phase 0 package manifest for imported D3/D7 gold
python qc_cli.py write-phase0-adjudication-package <project_id> --output phase0_package.json --d3-gold-file d3_gold.json --gold-file d7_gold.json  # Canonical CLI wrapper for Phase 0 adjudication package manifests
make lint-scope-phrasing ID=<project_id> INPUT=report.md  # Lint arbitrary text for unsafe population-generalizing scope phrasing
python qc_cli.py lint-scope-phrasing <project_id> --input-file report.md  # Canonical CLI wrapper for scope phrasing lint
make export-audit-manifest ID=<project_id> FORMAT=markdown ARTIFACTS="report.md" OUTPUT=manifest.json AUDIT_LOG=events.jsonl AUDIT_DB=events.sqlite  # Write export artifact hash manifest and optional audit event mirror
make verify-export-audit-manifest MANIFEST=manifest.json BASE_DIR=. ID=<project_id> AUDIT_LOG=events.jsonl AUDIT_DB=events.sqlite  # Verify manifest and optionally mirror the verification event
make export-publish-preflight MANIFEST=manifest.json BASE_DIR=. ID=<project_id> AUDIT_LOG=events.jsonl AUDIT_DB=events.sqlite  # Strict local publish/handoff preflight with optional mirrored event
make export-publish-preflight MANIFEST=manifest.json BASE_DIR=. ID=<project_id> SCOPE_LINT=1  # Also block risky Markdown/text scope phrasing before handoff
make verify-export-audit-log LOG=export_audit_events.jsonl  # Verify opt-in local hash-linked export audit event log
make mirror-export-audit-db LOG=export_audit_events.jsonl DB=export_audit_events.sqlite  # Mirror verified event log into local SQLite
make verify-export-audit-db DB=export_audit_events.sqlite  # Verify local SQLite export audit event mirror
python qc_cli.py export-audit-manifest <project_id> --format markdown --artifact report.md --output manifest.json --audit-log events.jsonl --audit-db events.sqlite  # Canonical CLI wrapper for export audit manifest writing
python qc_cli.py verify-export-audit-manifest manifest.json --base-dir . --project-id <project_id> --audit-log events.jsonl --audit-db events.sqlite  # Canonical CLI wrapper for export audit manifest verification
python qc_cli.py export-publish-preflight --manifest manifest.json --base-dir . --project-id <project_id> --audit-log events.jsonl --audit-db events.sqlite  # Canonical CLI wrapper for export publish preflight
python qc_cli.py export-publish-preflight --manifest manifest.json --base-dir . --project-id <project_id> --scope-lint  # Canonical CLI wrapper with optional scope phrasing preflight
python qc_cli.py project export <project_id> --format markdown --output-file report.md --audit-manifest manifest.json --publish-preflight --scope-lint  # Inline export manifest + publish preflight gate
python qc_cli.py verify-export-audit-log export_audit_events.jsonl  # Canonical CLI wrapper for export audit event-log verification
python qc_cli.py mirror-export-audit-db export_audit_events.jsonl --db export_audit_events.sqlite  # Canonical CLI wrapper for export audit SQLite mirroring
python qc_cli.py verify-export-audit-db export_audit_events.sqlite  # Canonical CLI wrapper for export audit SQLite verification
make validate-d3-baseline-package PACKAGE=d3_baseline.json  # Validate versioned D3 application baseline package
make validate-d3-comparison-protocol PROTOCOL=d3_protocol.json  # Validate pre-run D3 baseline comparison protocol, including optional metric criteria
make d3-comparison-preflight PROTOCOL=d3_protocol.json GOLD=d3_gold.json PREDICTIONS="baseline.json"  # Preflight D3 comparison inputs before scoring
make bench ID=<project_id> D3_GOLD=d3_gold.json D3_BASELINES=d3_baselines.json D3_PROTOCOL=d3_protocol.json  # Guard D3 baseline comparison scoring with protocol preflight and metric-criteria report when configured
python qc_cli.py validate-d3-baseline-package d3_baseline.json  # Canonical CLI wrapper for D3 baseline package validation
python qc_cli.py validate-d3-comparison-protocol d3_protocol.json  # Canonical CLI wrapper for D3 comparison protocol validation
python qc_cli.py d3-comparison-preflight d3_protocol.json d3_gold.json baseline.json  # Canonical CLI wrapper for D3 comparison preflight
make validate-d7-gold GOLD=gold_set.json  # Validate versioned held-out D7 gold-set package
make validate-d7-baseline-package PACKAGE=d7_baseline.json  # Validate versioned D7 retrieval/live baseline package
python qc_cli.py validate-d7-baseline-package d7_baseline.json  # Canonical CLI wrapper for D7 baseline package validation
make validate-theoretical-sampling-protocol PROTOCOL=theoretical_sampling_protocol.json  # Validate pre-run theoretical-sampling protocol metadata
python qc_cli.py validate-theoretical-sampling-protocol theoretical_sampling_protocol.json  # Canonical CLI wrapper for theoretical-sampling protocol validation
make export-theoretical-sampling-candidates ID=<project_id> PROTOCOL=theoretical_sampling_protocol.json OUTPUT=candidates.json  # Export loaded-document theoretical-sampling candidates
python qc_cli.py export-theoretical-sampling-candidates <project_id> --protocol theoretical_sampling_protocol.json --output candidates.json  # Canonical CLI wrapper for candidate export
make export-theoretical-sampling-results PROTOCOL=theoretical_sampling_protocol.json CANDIDATES=candidates.json SELECTED=loaded-doc-1 SUCCESS_CRITERION="..." OUTPUT=results.json  # Export selected theoretical-sampling candidates as a result package
python qc_cli.py export-theoretical-sampling-results theoretical_sampling_protocol.json --candidates-file candidates.json --selected-candidate-id loaded-doc-1 --success-criterion-met "..." --output results.json  # Canonical CLI wrapper for result export
make theoretical-sampling-preflight PROTOCOL=theoretical_sampling_protocol.json CANDIDATES=candidates.json RESULTS=results.json  # Preflight theoretical-sampling candidates/results against a protocol
python qc_cli.py theoretical-sampling-preflight theoretical_sampling_protocol.json --candidates-file candidates.json --results-file results.json  # Canonical CLI wrapper for theoretical-sampling preflight
make validate-d7-comparison-protocol PROTOCOL=d7_protocol.json  # Validate pre-run D7 retrieval comparison protocol, including optional metric criteria
make d7-comparison-preflight PROTOCOL=d7_protocol.json GOLD=d7_gold.json PREDICTIONS="lexical.json embedding.json"  # Preflight D7 comparison inputs before scoring
make compare-d7-retrieval ID=<project_id> GOLD=d7_gold.json PREDICTIONS="lexical.json embedding.json" PROTOCOL=d7_protocol.json ARTIFACT_DIR=benchmark_results  # Score D7 retrieval predictions with preflight guard, metric-criteria report when configured, input-hash provenance, and optional artifact package
make write-d7-comparison-package ID=<project_id> GOLD=d7_gold.json PREDICTIONS="lexical.json embedding.json" OUTPUT=d7_comparison_package.json  # Write strict D7 comparison package manifest after validation/preflight
make compare-d7-package PACKAGE=d7_comparison_package.json  # Run D7 retrieval comparison from a strict package manifest
make verify-d7-comparison-artifact ARTIFACT=benchmark_results/run-dir  # Verify D7 comparison artifact report/manifest hashes
make run-d7-live-baseline ID=<project_id> OUTPUT=live_baseline.json MODEL=<model>  # Write opt-in live D7 candidate-selection baseline package for BASELINES=
python qc_cli.py run-d7-retrieval <project_id> --output predictions.json  # Canonical CLI wrapper for D7 retrieval export
python qc_cli.py run-d7-live-baseline <project_id> --output live_baseline.json --model <model>  # Canonical CLI wrapper for opt-in live D7 baseline export
python qc_cli.py validate-d7-comparison-protocol d7_protocol.json  # Canonical CLI wrapper for D7 comparison protocol validation
python qc_cli.py d7-comparison-preflight d7_protocol.json d7_gold.json lexical.json embedding.json  # Canonical CLI wrapper for D7 comparison preflight
python qc_cli.py compare-d7-retrieval <project_id> --gold-file d7_gold.json --predictions-file lexical.json --predictions-file embedding.json --protocol-package d7_protocol.json --artifact-dir benchmark_results  # Canonical CLI wrapper for D7 retrieval comparison
python qc_cli.py write-d7-comparison-package <project_id> --output d7_comparison_package.json --gold-file d7_gold.json --predictions-file lexical.json  # Canonical CLI wrapper for D7 comparison package writer
python qc_cli.py compare-d7-package d7_comparison_package.json  # Canonical CLI wrapper for D7 comparison package runner
python qc_cli.py verify-d7-comparison-artifact benchmark_results/run-dir/manifest.json  # Canonical CLI wrapper for D7 comparison artifact verification
make run-inv7-fixtures OUTPUT=inv7.json  # Write structural INV-7 fixture package for PROMPT_INJECTION=
make run-inv7-live-fixtures OUTPUT=inv7_live.json MODEL=<model>  # Write opt-in live canary package for PROMPT_INJECTION=
make run-inv7-live-fixtures OUTPUT=inv7_live.json MODEL=<model> FIXTURES=manifest.json  # Run an external INV-7 live fixture manifest
python qc_cli.py run-inv7-fixtures --output inv7.json  # Canonical CLI wrapper for structural INV-7 fixtures
python qc_cli.py run-inv7-live-fixtures --output inv7_live.json --model <model>  # Canonical CLI wrapper for opt-in live INV-7 fixtures
python qc_cli.py run-inv7-live-fixtures --output inv7_live.json --model <model> --fixtures manifest.json  # Canonical CLI wrapper for external live fixture manifests
make validate-inv7-live-protocol PROTOCOL=inv7_live_protocol.json  # Validate pre-run live protocol metadata
make inv7-live-preflight PROTOCOL=inv7_live_protocol.json PACKAGE=inv7_live.json  # Preflight live result against protocol before scoring
make validate-inv7-package PACKAGE=inv7.json  # Validate schema_version=1 INV-7 package metadata
python qc_cli.py validate-inv7-package inv7.json  # Canonical CLI wrapper for INV-7 package validation
python qc_cli.py validate-inv7-live-protocol inv7_live_protocol.json  # Canonical CLI wrapper for INV-7 live protocol validation
python qc_cli.py inv7-live-preflight inv7_live_protocol.json inv7_live.json  # Canonical CLI wrapper for INV-7 live preflight
python qc_cli.py validate-d3-gold d3_gold.json  # Canonical CLI wrapper for D3 gold package validation
python qc_cli.py validate-d7-gold d7_gold.json  # Canonical CLI wrapper for D7 gold package validation
make lint-prompt-overrides  # Check prompt override source uses against registry declarations
python qc_cli.py lint-prompt-overrides --root qc_clean  # Canonical CLI wrapper for prompt override registry lint
make cost               # Show LLM spend (DAYS=7)
make errors             # Show recent error breakdown

# Pipeline (local run; `project run` needs no server, `analyze` needs the API server)
python qc_cli.py project run <project_id>
python qc_cli.py project run <project_id> --exhaustive   # code every segment (INV-8)
python qc_cli.py project scope <project_id> --phenomenon "..."  # show/update corpus scope
python qc_cli.py project claims <project_id> --limit 20 --offset 0 --show-scope --show-anchors  # inspect first-class claim ledger scope/anchors (INV-9)
python qc_cli.py project add-docs <project_id> --files new.txt --recode  # add then incremental recode
```

## Principles

- LLM-first: all semantic analysis uses structured LLM output via Pydantic schemas + JSON mode
- Fail loud: inter-stage dependency checks raise on failure; never silently degrade
- Single state model: `ProjectState` Pydantic model holds all state, saved/loaded as JSON
- Observability: all LLM calls log model/schema/prompt/cost/token usage via llm_client

## Workflow

1. Feed transcript files (txt/docx/pdf/rtf) to the pipeline
2. Default 7-stage pipeline: Ingest → Thematic Coding → Perspective Analysis → Relationship Mapping → Synthesis → Cross-Interview → Negative Case (disconfirmation runs last; INV-6)
3. Human review via CLI or browser; IRR via `project irr`
4. Inspect claim ledger via `project claims` or `/projects/{project_id}/claims?limit=100&offset=0`
5. Export to JSON/CSV/Markdown/QDPX

## References

- `CLAUDE.md` — This file (canonical operating guidance)
- `AGENTS.md` — Generated mirror for non-Claude agents
- `docs/PROJECT_THEORY_AND_GOALS.md` — **Theory, goals, honest state, and the architectural invariants (INV-0..11).** Read its state ledger (§13), invariants (§13.1), and claim-discipline table (§14) before describing the system anywhere. The end product is public and SOTA-targeting; the UNMET invariants are a committed build spec, not a wishlist.
- `docs/EVALUATION_HARNESS.md` — **The keystone**: how we prove SOTA (metrics, gold standards, baselines, `make bench`), built on `prompt_eval`. Roadmap item #1.
- `docs/` — Other design docs and plans
- `scripts/relationships.yaml` — Doc-code coupling graph
