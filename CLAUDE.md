# Qualitative Coding Analysis System

## What This Project Does

LLM-powered qualitative coding analysis for interview transcripts. Accepts .txt, .docx, .pdf, .rtf files and runs a 4-phase analysis pipeline:

1. **Open Code Discovery** - Identifies 10-15 hierarchical thematic codes (not over-coded)
2. **Speaker/Participant Analysis** - Adapts for single vs multi-speaker interviews
3. **Entity & Relationship Mapping** - Extracts entities and 10-15 key relationships
4. **Synthesis & Recommendations** - Integrates findings with verbatim evidence (no fabricated statistics)

All phases use structured LLM output via Pydantic schemas + JSON mode.

## Architecture

```
qc_cli.py                          # CLI entry point (thin HTTP client)
  -> qc_clean/core/cli/commands/   # CLI command handlers
  -> qc_clean/plugins/api/         # FastAPI server (port 8002)
     -> qc_clean/core/llm/         # LiteLLM integration with structured extraction
     -> qc_clean/schemas/          # Pydantic schemas for all 4 analysis phases
simple_cli_web.py                   # Flask web UI (port 5003, subprocess-based)
start_server.py                     # Server startup script
```

### Key Files
- `qc_clean/plugins/api/api_server.py` - API server with 4-phase analysis pipeline
- `qc_clean/core/llm/llm_handler.py` - LLM handler with `extract_structured()` method
- `qc_clean/schemas/analysis_schemas.py` - Pydantic schemas: CodeHierarchy, SpeakerAnalysis, EntityMapping, AnalysisSynthesis
- `qc_cli.py` - CLI interface (analyze, query, status, server commands)
- `tests/test_analysis_quality.py` - 28 passing tests (schemas, truncation, output validation)

### How It Works
- CLI is a pure HTTP client — all analysis runs on the API server
- API server uses `LLMHandler.extract_structured()` with Pydantic schemas for each phase
- LLM calls go through LiteLLM with `response_format: {"type": "json_object"}`
- Each phase feeds its structured output into the next phase's prompt
- Default model: gpt-5-mini via OpenAI API (note: gpt-5 models don't support temperature param)
- Single-speaker interviews get adapted Phase 2 prompts (no fabricated consensus/divergence)
- Truncated interviews are detected and flagged in `data_warnings`

## Working Commands

```bash
# Start server first
python start_server.py

# Run analysis
python qc_cli.py analyze --files file1.docx file2.docx --format json
python qc_cli.py analyze --directory /path/to/interviews/ --format json --output-file results.json

# Check status
python qc_cli.py status --server
python qc_cli.py status --job <job_id>

# Run tests
python -m pytest tests/ -v
```

## Development Notes

- This is a research tool, not a production system
- Interview data files are gitignored (sensitive content)
- Output quality validated: real mention counts, calibrated confidence (0.65-0.90), no fabricated %s
- `src/` directory is legacy code (gitignored)
- Branches: `main` and `clean-final` are in sync
