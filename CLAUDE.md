# Qualitative Coding Analysis System

*Last Updated: 2026-06-21*

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

  (Negative Case Analysis runs last and now sees bounded claim-ledger targets by claim ID plus BM25-style lexical/query-expanded retrieval-first source candidates. It has adversarial prompt framing and configurable `disconfirmation_model_name`, but remains non-embedding retrieval and not held-out D7-evaluated. INV-6 remains PARTIAL and INV-2 is PARTIAL, not full credibility evidence. See `docs/PROJECT_THEORY_AND_GOALS.md`.)

All stages use structured LLM output via Pydantic schemas + JSON mode. State is held in a single `ProjectState` Pydantic model that can be saved/loaded as JSON.

## Current State

The software is **built and software-validated** (deterministic tests + live-LLM E2E; ruff + docs gates green) — "the program does what it's built to do," *not* evidence the analysis is methodologically valid. Implemented:

- Thematic and **GT-inspired** (not "full GT") pipelines; `NegativeCaseStage` runs **last** in both (INV-6), automatic cross-interview analysis for multi-doc corpora.
- GT constant comparison; category-saturation diagnostics and diagnostic-driven sampling suggestions separate from codebook stability (INV-4 partial); incremental re-coding via `project recode` (hard-invalidates stale higher-order outputs it cannot recompute, INV-11 partial).
- **Span-anchored grounding** (INV-1, mostly met): quotes resolve to char offsets + hash or are dropped + warned; `verify_grounding`/`make bench` measure the rate.
- **Segment universe + coverage** (INV-8): every doc split into char-anchored segments; `project run --exhaustive` codes *every* segment (examined-and-judged coverage, segment-anchored applications), else traversal coverage.
- **First-class claim ledger** (INV-9 object layer): substantive stage outputs become `AnalyticClaim` objects or no-claims events, with source stage, kind, scope, support/adjudication status, anchors where available, and CLI/API/MCP/export read surfaces.
- **Retrieval-first/adversarial ledger disconfirmation + claim review first slices** (INV-2/INV-6/INV-10 partial): negative-case prompts include bounded claim targets by ID and BM25-style lexical/query-expanded source-candidate passages; valid `candidate_id`s attach exact contrary anchors; `disconfirmation_model_name` can route interpretation through a separate model; coverage summaries report challenged/unchallenged targets; `make bench` includes a D7 scorecard substrate with recall/precision Wilson intervals when adjudicated contrary-evidence gold anchors are supplied via project metadata or `GOLD=gold.json`, plus optional baseline point comparisons via `BASELINES=baselines.json`; `ReviewManager` supports `target_type="claim"` approve/reject/modify decisions with revision history.
- **Corpus-scope contract first slices**: optional `ProjectState.corpus_scope` records phenomenon, population, sampling frame, inclusion/exclusion criteria, and caveats; Markdown export surfaces it before analytic claims and warns when claim-bearing reports have no scope; CLI/API scope read/update surfaces are agent-drivable. This is report-boundary context, not sampling-frame validation.
- **Instruction/data separation first slices** (INV-7 partial): raw transcript/document/segment prompt sections and downstream LLM/codebook artifacts are rendered as untrusted `DATA>` lines via `qc_clean/core/prompting.py`; current prompt override surfaces fail loudly if they omit required protected data placeholders; deterministic prompt-injection regressions exist; `make bench` can score externally supplied prompt-injection fixture outcomes via `PROMPT_INJECTION=results.json`. Broader custom-prompt governance and live adversarial evaluation remain.
- Human review (CLI + browser), `project irr` (LLM-pass *codebook-discovery* agreement by default; **application-level** positive segment × code agreement plus segment-decision agreement via `--application-level`, using exhaustive coding), `project stability`.
- D10 cost/latency scorecard substrate: `make bench` queries real `llm_client` observability rows by project trace prefix or `TRACE_ID=...` and reports last-local-`project run` wall-clock metadata when available; missing rows/timing report `not_available`, never estimated.
- Phase 0 provenance substrate: `make bench` emits `_meta.input_hashes` for the loaded project state, corpus, and supplied benchmark files; hashes are reproducibility metadata, not validity evidence.
- Graph viz, JSON/CSV/Markdown/QDPX export, per-stage memos, per-code audit trail; typed `PipelineContext`/results, fail-loud inter-stage checks, `llm_client` observability.

**Direction:** the end product is public and SOTA-targeting; the proven/measured/planned ledger, the architectural invariants, and the ranked roadmap are in `docs/PROJECT_THEORY_AND_GOALS.md` (§13/§13.1/§18). Recent structural work landed: span anchoring (INV-1), the segment universe + exhaustive coverage (INV-8), the first-class claim ledger object layer (INV-9), retrieval-first/adversarial/BM25-style query-expanded ledger disconfirmation/claim review first slices plus a gold-dependent D7 scorecard substrate with recall/precision Wilson intervals and optional baseline point comparisons (INV-2/INV-6/INV-10 partial), first-party instruction/data separation for raw + derived prompt inputs plus an externally fed INV-7 prompt-injection scorecard substrate (INV-7 partial), D10 cost/latency scorecard substrate from real observability rows plus last-local-run wall-clock metadata, Phase 0 scorecard input hashes, category-saturation diagnostics plus diagnostic-driven sampling suggestions (INV-4 partial), corpus-scope/report-boundary contract slices including CLI/API read/update surfaces and missing-scope report warnings, and hard invalidation of stale higher-order outputs during incremental recode (INV-11 partial). Next high-value lanes: semantic/embedding retrieval + held-out D7 evaluation/gold-set wiring and live baselines (INV-2 follow-up), live injection evaluation / broader custom-prompt governance (INV-7 follow-up), and a full theoretical sampling protocol (INV-4 when GT claims theory generation).

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
     -> qc_clean/core/bench.py              # Eval-harness Phase 0 scorecard (D1/D2/D5 plus gold-dependent D7 with intervals/baselines)
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
- Incremental coding: `project recode` codes only uncoded documents against the existing codebook, then re-runs downstream stages
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
python qc_cli.py project list
python qc_cli.py project show <project_id>
python qc_cli.py project claims <project_id> --limit 20
python qc_cli.py project add-docs <project_id> --files interview1.docx interview2.docx
python qc_cli.py bench <project_id>                                     # Phase 0 scorecard (same engine as make bench)
python qc_cli.py bench <project_id> --artifact-dir benchmark_results    # Write versioned Phase 0 scorecard package

# Run pipeline on a project (local, no server needed)
python qc_cli.py project run <project_id>                          # run full pipeline
python qc_cli.py project run <project_id> --model gpt-5-mini       # specify model
python qc_cli.py project run <project_id> --review                  # pause for human review

# Export results
python qc_cli.py project export <project_id> --format json --output-file results.json
python qc_cli.py project export <project_id> --format csv --output-dir ./export/
python qc_cli.py project export <project_id> --format markdown --output-file report.md
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

The ranked roadmap (invariants before features) lives in `docs/PROJECT_THEORY_AND_GOALS.md` §18 — evaluation harness (keystone), span anchoring (done), segment universe + exhaustive coding (INV-8, done), claim ledger object layer (INV-9, mostly done), retrieval-first/adversarial/BM25-style query-expanded disconfirmation/adjudication first slices plus D7 recall/precision Wilson intervals and optional baseline point comparisons (INV-2/INV-6/INV-10 partial), raw + derived instruction/data separation first slices plus externally fed INV-7 prompt-injection scorecard substrate (INV-7 partial), category-saturation diagnostics (INV-4 partial), corpus-scope/report-boundary contract first slices including missing-scope warnings, semantic retrieval + held-out D7 evaluation/live baselines, live prompt-injection evaluation, theoretical sampling protocol, broader scope-aware claim/report phrasing, etc. Don't duplicate it here.

### Maintenance Follow-Ups (2026-06-19)
- **Line endings**: Normalize mixed CRLF/LF files in one mechanical commit with no behavior changes, then run `make check`.
- **Ruff expansion**: Add `F541` next and remove f-strings with no placeholders. Defer `F401` and `E402` until wrapper/re-export patterns are reviewed.
- **Cost observability target**: Verify `make cost`; if `llm_client cost` is unavailable or unstable, replace the fallback with an explicit repo-local helper like `make errors`.
- **Boundary tests**: Add API/MCP regression tests for invalid project IDs so traversal-like inputs stay mapped to explicit not-found/invalid responses.
- **Exporter overwrite policy**: Current exporters overwrite existing output paths. Decide whether that is intended; either document/test overwrite semantics or add an explicit force/no-clobber policy later.

## prompt_eval Integration (Prompt Optimization)

### Infrastructure

`PipelineContext.prompt_overrides` allows passing custom prompts to stages without editing source code. Supported stages: `thematic_coding`, `gt_constant_comparison`. Overrides must include the required protected data placeholder for that stage (`{combined_text}` for thematic, `{segment_text}` for GT constant comparison); missing placeholders raise `ValueError` before an LLM call. The `qc_run_pipeline` MCP tool accepts `prompt_overrides` dict.

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
make bench ID=<project_id>              # Phase 0 scorecard (D1/D2/D5/D10 plus optional D7/INV-7 scores)
python qc_cli.py bench <project_id>     # Same Phase 0 scorecard through the canonical CLI
make bench ID=<project_id> GOLD=gold.json BASELINES=baselines.json  # Add external D7 gold/baselines without mutating project state
make bench ID=<project_id> PROMPT_INJECTION=inv7.json  # Add external INV-7 fixture results without mutating state
make bench ID=<project_id> OBS_DB=path TRACE_ID=trace  # Override D10 observability DB / exact trace
make bench ID=<project_id> ARTIFACT_DIR=benchmark_results  # Write versioned Phase 0 scorecard package
make cost               # Show LLM spend (DAYS=7)
make errors             # Show recent error breakdown

# Pipeline (local run; `project run` needs no server, `analyze` needs the API server)
python qc_cli.py project run <project_id>
python qc_cli.py project run <project_id> --exhaustive   # code every segment (INV-8)
python qc_cli.py project scope <project_id> --phenomenon "..."  # show/update corpus scope
python qc_cli.py project claims <project_id>              # inspect first-class claim ledger (INV-9)
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
4. Inspect claim ledger via `project claims` or `/projects/{project_id}/claims`
5. Export to JSON/CSV/Markdown/QDPX

## References

- `CLAUDE.md` — This file (canonical operating guidance)
- `AGENTS.md` — Generated mirror for non-Claude agents
- `docs/PROJECT_THEORY_AND_GOALS.md` — **Theory, goals, honest state, and the architectural invariants (INV-0..11).** Read its state ledger (§13), invariants (§13.1), and claim-discipline table (§14) before describing the system anywhere. The end product is public and SOTA-targeting; the UNMET invariants are a committed build spec, not a wishlist.
- `docs/EVALUATION_HARNESS.md` — **The keystone**: how we prove SOTA (metrics, gold standards, baselines, `make bench`), built on `prompt_eval`. Roadmap item #1.
- `docs/` — Other design docs and plans
- `scripts/relationships.yaml` — Doc-code coupling graph
