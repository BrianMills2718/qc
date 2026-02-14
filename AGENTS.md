# Qualitative Coding Analysis System (v2.2)

## What This Project Does

LLM-powered qualitative coding analysis for interview transcripts. Accepts .txt, .docx, .pdf, .rtf files. Supports two methodologies:

- **Default/Thematic Analysis** - 7-stage pipeline: Ingest -> Thematic Coding -> Perspective Analysis -> Relationship Mapping -> Synthesis -> Negative Case Analysis -> Cross-Interview Analysis
- **Grounded Theory** - 7-stage pipeline: Ingest -> Constant Comparison Coding -> Axial Coding -> Selective Coding -> Theory Integration -> Negative Case Analysis -> Cross-Interview Analysis

All stages use structured LLM output via Pydantic schemas + JSON mode. State is held in a single `ProjectState` Pydantic model that can be saved/loaded as JSON.

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
           -> negative_case.py               # Negative case analysis (disconfirming evidence)
           -> cross_interview.py             # Cross-document pattern analysis
           -> incremental_coding.py           # Incremental re-coding of new documents
           -> gt_constant_comparison.py      # GT: Iterative constant comparison coding
           -> gt_open_coding.py              # GT: Open coding (legacy, replaced by constant comparison)
           -> gt_axial_coding.py             # GT: Axial coding (relationships)
           -> gt_selective_coding.py         # GT: Core category identification
           -> gt_theory_integration.py       # GT: Theoretical model building
     -> qc_clean/core/llm/llm_handler.py    # Thin adapter over llm_client for structured extraction
     -> qc_clean/schemas/                    # Pydantic schemas
        -> domain.py                         # Unified domain model (ProjectState, Code, Codebook, etc.)
        -> analysis_schemas.py               # LLM output schemas (CodeHierarchy, SpeakerAnalysis, etc.)
        -> gt_schemas.py                     # GT LLM output schemas (OpenCode, CoreCategory, etc.)
        -> adapters.py                       # Convert LLM output schemas to domain model
     -> qc_clean/core/persistence/           # JSON file-based project storage
        -> project_store.py                  # Save/load ProjectState as JSON files
     -> qc_clean/core/export/               # Export from ProjectState
        -> data_exporter.py                  # ProjectExporter (JSON/CSV/Markdown/QDPX)
qc_mcp_server.py                             # MCP server (19 tools for agent access)
simple_cli_web.py                            # Flask web UI (port 5003, subprocess-based)
start_server.py                              # Server startup script
```

### Key Files
- `qc_clean/schemas/domain.py` - Unified data model: ProjectState, Document, Corpus, Code, Codebook, CodeApplication, etc.
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
- `qc_mcp_server.py` - MCP server: 19 tools for project management, pipeline execution, codebook inspection, review, IRR/stability, export
- `tests/` - 483 unit tests + 6 E2E tests (23 test files)

### How It Works
- `project run` runs the pipeline locally (no server needed); `analyze` uses the API server
- CLI is a pure HTTP client for `analyze` -- all analysis runs on the API server
- API server creates an `AnalysisPipeline` via the factory and runs it
- Each stage reads from / writes to `ProjectState` (single Pydantic model) via typed `PipelineContext`
- Pipeline pauses at human review checkpoints when `enable_human_review=True`
- `ReviewManager` handles approve/reject/modify/merge/split of codes
- `ProjectStore` saves/loads entire ProjectState as JSON (no database needed)
- Cross-interview analysis runs automatically for multi-document corpora
- Saturation detection compares codebooks across iterations
- Default model: gpt-5-mini via OpenAI API. LLMHandler is a thin adapter over shared `llm_client` library (retry, backoff, structured extraction via `acall_llm_structured` / `acall_llm_structured_batch`)
- `analysis_schemas.py` defines LLM output shapes; `adapters.py` converts them to domain objects
- Every stage produces an analytical memo (LLM reasoning trail) saved to `state.memos`
- GT constant comparison: segments documents by speaker turns or paragraph chunks, iteratively codes each segment against an evolving codebook, stops when saturation reached
- Incremental coding: `project recode` codes only uncoded documents against the existing codebook, then re-runs downstream stages
- Graph visualization: `/graph/{project_id}` serves interactive Cytoscape.js graphs (code hierarchy, relationships, entity map)
- Fail-loud: downstream stages raise `RuntimeError` via `ctx.require()` if upstream data is missing (no silent empty-data fallbacks). Review raises `ValueError` on unknown target types.
- Observability: LLMHandler logs model/schema/prompt_len on call, cost/usage on response. All stages log entry context (doc/code counts, model). Pipeline engine logs state context on failure.
- Prompt overrides: `PipelineContext.prompt_overrides` allows custom prompts per stage for A/B testing without editing source code.

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
python qc_cli.py project add-docs <project_id> --files interview1.docx interview2.docx

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

# MCP server (for agent access - 19 tools)
python qc_mcp_server.py                                                   # run via stdio
# Tools: qc_list_projects, qc_create_project, qc_show_project, qc_delete_project,
#   qc_add_documents, qc_run_pipeline, qc_run_stage, qc_recode,
#   qc_run_irr, qc_run_stability, qc_get_codebook, qc_get_applications,
#   qc_get_memos, qc_get_synthesis, qc_review_summary, qc_approve_all_codes,
#   qc_review_codes, qc_export_markdown, qc_export_json

# Run tests
python -m pytest tests/ -v
```

## Configuration

API keys are read from environment variables by `llm_client` (via litellm). Default model: `gpt-5-mini`.

Key env vars:
- `OPENAI_API_KEY` / `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` -- API key for the model provider
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

## Known Technical Debt

1. **Schema duplication**: `analysis_schemas.py` / `gt_schemas.py` (LLM output shapes) and `domain.py` (internal model) overlap; this is intentional — adapters bridge them
2. **`methodology_config.py`**: Only imported by tests now (not production code); could be removed if tests are refactored

## Related Projects

| Project | Path | Relationship |
|---------|------|-------------|
| **llm_client** | `~/projects/llm_client/` | Shared LLM calling library. QC's `LLMHandler` is a thin adapter over `acall_llm_structured` |
| **prompt_eval** | `~/projects/prompt_eval/` | General-purpose prompt improvement system (v0.2.0). 4 evaluators (llm_judge, kappa, exact_match, contains), 3 optimization strategies (grid search, few-shot selection, instruction search), persistence, MCP server with all 4 evaluators as built-ins. |
