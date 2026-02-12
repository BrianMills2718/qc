# Qualitative Coding Analysis System (v2.0)

## What This Project Does

LLM-powered qualitative coding analysis for interview transcripts. Accepts .txt, .docx, .pdf, .rtf files. Supports two methodologies:

- **Default/Thematic Analysis** - 6-stage pipeline: Ingest -> Thematic Coding -> Perspective Analysis -> Relationship Mapping -> Synthesis -> Cross-Interview Analysis
- **Grounded Theory** - 6-stage pipeline: Ingest -> Open Coding -> Axial Coding -> Selective Coding -> Theory Integration -> Cross-Interview Analysis

All stages use structured LLM output via Pydantic schemas + JSON mode. State is held in a single `ProjectState` Pydantic model that can be saved/loaded as JSON.

## Architecture

```
qc_cli.py                                    # CLI entry point (thin HTTP client)
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
           -> thematic_coding.py             # Phase 1: Hierarchical code discovery
           -> perspective.py                 # Phase 2: Speaker/participant analysis
           -> relationship.py                # Phase 3: Entity & relationship mapping
           -> synthesis.py                   # Phase 4: Synthesis & recommendations
           -> cross_interview.py             # Cross-document pattern analysis
           -> gt_open_coding.py              # GT: Open coding
           -> gt_axial_coding.py             # GT: Axial coding (relationships)
           -> gt_selective_coding.py         # GT: Core category identification
           -> gt_theory_integration.py       # GT: Theoretical model building
     -> qc_clean/core/llm/                   # LiteLLM integration with structured extraction
     -> qc_clean/schemas/                    # Pydantic schemas
        -> analysis_schemas.py               # LLM output schemas (CodeHierarchy, SpeakerAnalysis, etc.)
        -> domain.py                         # Unified domain model (ProjectState, Code, Codebook, etc.)
        -> adapters.py                       # Convert LLM output schemas to domain model
     -> qc_clean/core/persistence/           # JSON file-based project storage
        -> project_store.py                  # Save/load ProjectState as JSON files
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
- `qc_cli.py` - CLI interface (analyze, project, review, query, status, server)
- `tests/` - 116 passing tests

### How It Works
- CLI is a pure HTTP client -- all analysis runs on the API server
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
# Start server first
python start_server.py

# Run analysis (via API)
python qc_cli.py analyze --files file1.docx file2.docx --format json
python qc_cli.py analyze --directory /path/to/interviews/ --format json --output-file results.json

# Project management (local, no server needed)
python qc_cli.py project create --name "My Study" --methodology grounded_theory
python qc_cli.py project list
python qc_cli.py project show <project_id>
python qc_cli.py project add-docs <project_id> --files interview1.docx interview2.docx

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

Environment-driven via `qc_clean/config/unified_config.py`. Key env vars:
- `API_PROVIDER` (openai/google/anthropic), `MODEL`, `OPENAI_API_KEY`/`GEMINI_API_KEY`/`ANTHROPIC_API_KEY`
- `METHODOLOGY` (grounded_theory/thematic_analysis), `CODING_APPROACH`, `VALIDATION_LEVEL`
- `THEORETICAL_SENSITIVITY`, `CODING_DEPTH`, `TEMPERATURE`

## Development Notes

- This is a research tool, not a production system
- Interview data files are gitignored (sensitive content)
- Output quality validated: real mention counts, calibrated confidence (0.65-0.90), no fabricated %s
- `src/` directory is legacy code (gitignored)
- `qc_clean/core/analysis/` has been cleaned -- legacy Neo4j-dependent modules removed
- Legacy code in `qc_clean/core/cli/robust_cli_operations.py`, `qc_clean/core/cli/cli_robust.py`, and some plugin files still uses old `from core.` import paths; these are not on the active code path but could be cleaned up

## Known Technical Debt

1. **Legacy import paths**: Some plugin/CLI files use `from core.` instead of `from qc_clean.core.` -- these are not reachable from the active pipeline but should be fixed if those modules are revived
2. **Multiple config managers**: 5 config modules exist (`config_manager.py`, `enhanced_config_manager.py`, `unified_config.py`, `methodology_config.py`, `core/config/env_config.py`); should consolidate
3. **Schema duplication**: `analysis_schemas.py` (LLM output shapes) and `domain.py` (internal model) overlap; this is intentional -- adapters bridge them
4. **`grounded_theory.py` workflow**: Large file (73KB) in `core/workflow/` with GT base classes; GT pipeline stages import from it but it contains unused Neo4j storage code

## Next Steps

### Short-term (v2.1)
- **End-to-end LLM test**: Run the full pipeline against real interviews and validate output quality vs v0.1-lite
- **Pipeline resume from API**: Wire the `/projects/{id}/resume` endpoint to actually re-run remaining stages
- **Iterative coding CLI flow**: `project run <id>` command that runs pipeline, pauses for review, resumes
- **Export formats**: JSON, CSV, ATLAS.ti/NVivo-compatible export from ProjectState

### Medium-term (v2.2)
- **Web UI for review**: Replace CLI review with browser-based code review interface
- **Incremental coding**: Add new documents to an existing project and re-code without starting over
- **Inter-rater reliability**: Run multiple LLM passes and compute agreement metrics
- **Prompt optimization**: A/B test different prompts for code discovery quality

### Long-term (v3.0)
- **Multi-model consensus**: Run analysis across GPT/Claude/Gemini and merge codebooks
- **Active learning**: Use human review decisions to fine-tune prompting for the project
- **Graph visualization**: Interactive code relationship graphs (replace Neo4j with lightweight in-memory graph)
- **Collaborative coding**: Multiple human reviewers with conflict resolution
