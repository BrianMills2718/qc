# Qualitative Coding Analysis System (v2.1)

## What This Project Does

LLM-powered qualitative coding analysis for interview transcripts. Accepts .txt, .docx, .pdf, .rtf files. Supports two methodologies:

- **Default/Thematic Analysis** - 6-stage pipeline: Ingest -> Thematic Coding -> Perspective Analysis -> Relationship Mapping -> Synthesis -> Cross-Interview Analysis
- **Grounded Theory** - 6-stage pipeline: Ingest -> Open Coding -> Axial Coding -> Selective Coding -> Theory Integration -> Cross-Interview Analysis

All stages use structured LLM output via Pydantic schemas + JSON mode. State is held in a single `ProjectState` Pydantic model that can be saved/loaded as JSON.

## Architecture

```
qc_cli.py                                    # CLI entry point
  -> qc_clean/core/cli/commands/             # CLI command handlers (analyze, project, review)
  -> qc_clean/plugins/api/                   # FastAPI server (port 8002)
     -> qc_clean/core/pipeline/              # Stage-based pipeline engine
        -> pipeline_engine.py                # PipelineStage ABC + AnalysisPipeline orchestrator
        -> pipeline_factory.py               # create_pipeline(methodology) factory
        -> review.py                         # Human review loop (approve/reject/modify/merge/split)
        -> saturation.py                     # Coding saturation detection
        -> theoretical_sampling.py           # Suggest next documents to code
        -> stages/                           # One file per pipeline stage
           -> ingest.py                      # Document ingestion + speaker detection
           -> thematic_coding.py             # Hierarchical code discovery
           -> perspective.py                 # Speaker/participant analysis
           -> relationship.py                # Entity & relationship mapping
           -> synthesis.py                   # Synthesis & recommendations
           -> cross_interview.py             # Cross-document pattern analysis
           -> gt_open_coding.py              # GT: Open coding
           -> gt_axial_coding.py             # GT: Axial coding (relationships)
           -> gt_selective_coding.py         # GT: Core category identification
           -> gt_theory_integration.py       # GT: Theoretical model building
     -> qc_clean/core/llm/llm_handler.py    # LiteLLM with extract_structured()
     -> qc_clean/schemas/                    # Pydantic schemas
        -> domain.py                         # Unified domain model (ProjectState, Code, Codebook, etc.)
        -> analysis_schemas.py               # LLM output schemas (CodeHierarchy, SpeakerAnalysis, etc.)
        -> gt_schemas.py                     # GT LLM output schemas (OpenCode, CoreCategory, etc.)
        -> adapters.py                       # Convert LLM output schemas to domain model
     -> qc_clean/core/persistence/           # JSON file-based project storage
        -> project_store.py                  # Save/load ProjectState as JSON files
     -> qc_clean/core/export/               # Export from ProjectState
        -> data_exporter.py                  # ProjectExporter (JSON/CSV/Markdown)
simple_cli_web.py                            # Flask web UI (port 5003, subprocess-based)
start_server.py                              # Server startup script
```

### Key Files
- `qc_clean/schemas/domain.py` - Unified data model: ProjectState, Document, Corpus, Code, Codebook, CodeApplication, etc.
- `qc_clean/core/pipeline/pipeline_engine.py` - PipelineStage ABC and AnalysisPipeline orchestrator
- `qc_clean/core/pipeline/review.py` - ReviewManager for human-in-the-loop code review
- `qc_clean/core/persistence/project_store.py` - JSON persistence for ProjectState
- `qc_clean/schemas/adapters.py` - Convert LLM output schemas to domain model
- `qc_clean/plugins/api/api_server.py` - API server (delegates to pipeline)
- `qc_clean/core/llm/llm_handler.py` - LLM handler with `extract_structured()` method
- `qc_clean/core/export/data_exporter.py` - ProjectExporter (JSON/CSV/Markdown from ProjectState)
- `qc_cli.py` - CLI interface (analyze, project, review, query, status, server)
- `tests/` - 132 passing tests

### How It Works
- `project run` runs the pipeline locally (no server needed); `analyze` uses the API server
- CLI is a pure HTTP client for `analyze` -- all analysis runs on the API server
- API server creates an `AnalysisPipeline` via the factory and runs it
- Each stage reads from / writes to `ProjectState` (single Pydantic model)
- Pipeline pauses at human review checkpoints when `enable_human_review=True`
- `ReviewManager` handles approve/reject/modify/merge/split of codes
- `ProjectStore` saves/loads entire ProjectState as JSON (no database needed)
- Cross-interview analysis runs automatically for multi-document corpora
- Saturation detection compares codebooks across iterations
- Default model: gpt-5-mini via OpenAI API (note: gpt-5 models don't support temperature param)
- `analysis_schemas.py` defines LLM output shapes; `adapters.py` converts them to domain objects

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

# Review codes
python qc_cli.py review <project_id>
python qc_cli.py review <project_id> --approve-all
python qc_cli.py review <project_id> --file decisions.json

# Check status
python qc_cli.py status --server
python qc_cli.py status --job <job_id>

# Run tests
python -m pytest tests/ -v
```

## Configuration

The LLM handler reads API keys from environment variables. Default model: `gpt-5-mini`.

Key env vars:
- `OPENAI_API_KEY` / `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` -- API key for the model provider
- `qc_clean/config/unified_config.py` -- `UnifiedConfig` dataclass reads env vars: `API_PROVIDER`, `MODEL`, `METHODOLOGY`, `CODING_APPROACH`, `VALIDATION_LEVEL`, `TEMPERATURE`
- `qc_clean/core/config/env_config.py` -- Active server config (used by `start_server.py`)

## Development Notes

- This is a research tool, not a production system
- Interview data files are gitignored (sensitive content)
- Output quality validated: real mention counts, calibrated confidence (0.65-0.90), no fabricated %s
- `src/` directory is legacy code (gitignored)

## Known Technical Debt

1. **Schema duplication**: `analysis_schemas.py` / `gt_schemas.py` (LLM output shapes) and `domain.py` (internal model) overlap; this is intentional -- adapters bridge them
2. **Config duplication**: `unified_config.py` and `methodology_config.py` in `qc_clean/config/` are used by `llm_handler.py`; `env_config.py` in `qc_clean/core/config/` is used by the server. Should consolidate.
3. **Test gaps**: No unit tests for LLM handler, real pipeline stages (require mocked LLM), API HTTP handlers, or most CLI commands

## Next Steps

### Short-term
- **End-to-end LLM test**: Run the full pipeline against real interviews and validate output quality
- **LLM handler tests**: Unit tests with mocked LiteLLM calls
- **ATLAS.ti/NVivo export**: Add QDX/QDPX export format for interoperability with other QDA tools

### Medium-term
- **Web UI for review**: Replace CLI review with browser-based code review interface
- **Incremental coding**: Add new documents to an existing project and re-code without starting over
- **Inter-rater reliability**: Run multiple LLM passes and compute agreement metrics
- **Prompt optimization**: A/B test different prompts for code discovery quality

### Long-term
- **Multi-model consensus**: Run analysis across GPT/Claude/Gemini and merge codebooks
- **Active learning**: Use human review decisions to fine-tune prompting for the project
- **Graph visualization**: Interactive code relationship graphs
- **Collaborative coding**: Multiple human reviewers with conflict resolution
