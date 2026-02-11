# Qualitative Coding Analysis System

## What This Project Does

LLM-powered qualitative coding analysis for interview transcripts. Accepts .txt, .docx, .pdf, .rtf files and runs a 4-phase analysis pipeline:

1. **Open Code Discovery** - Identifies hierarchical thematic codes from interview content
2. **Speaker/Participant Analysis** - Identifies participants and maps their perspectives to codes
3. **Entity & Relationship Mapping** - Extracts entities and maps relationships between them
4. **Synthesis & Recommendations** - Integrates findings into actionable recommendations

All phases use structured LLM output via Pydantic schemas + JSON mode (not text parsing).

## Architecture

```
qc_cli.py                          # CLI entry point (thin HTTP client)
  -> qc_clean/core/cli/commands/   # CLI command handlers
  -> qc_clean/plugins/api/         # FastAPI server (port 8002)
     -> qc_clean/core/llm/         # LiteLLM integration with structured extraction
     -> qc_clean/schemas/          # Pydantic schemas for all 4 analysis phases
simple_cli_web.py                   # Flask web UI (port 5003, subprocess-based)
```

### Key Files
- `qc_clean/plugins/api/api_server.py` - API server with 4-phase analysis pipeline
- `qc_clean/core/llm/llm_handler.py` - LLM handler with `extract_structured()` method
- `qc_clean/schemas/analysis_schemas.py` - Pydantic schemas: CodeHierarchy, SpeakerAnalysis, EntityMapping, AnalysisSynthesis
- `qc_cli.py` - CLI interface (analyze, query, status, server commands)
- `simple_cli_web.py` - Web UI that wraps CLI via subprocess

### How It Works
- CLI is a pure HTTP client — all analysis runs on the API server
- API server uses `LLMHandler.extract_structured()` with Pydantic schemas for each phase
- LLM calls go through LiteLLM with `response_format: {"type": "json_object"}`
- Each phase feeds its structured output into the next phase's prompt
- Default model: gpt-5-mini via OpenAI API (note: gpt-5 models don't support temperature param)

## Working Commands

```bash
# Start server first
python start_server.py

# Run analysis
python qc_cli.py analyze --files file1.docx file2.docx --format json
python qc_cli.py analyze --directory /path/to/interviews/ --format json --output-file results.json
python qc_cli.py analyze --files file.docx --quiet  # suppress progress logs

# Check status
python qc_cli.py status --server
python qc_cli.py status --job <job_id>
```

## Development Notes

- This is a research tool, not a production system
- Interview data files are gitignored (sensitive content)
- The `src/` and `tests/` directories are legacy code from a previous architecture — they are gitignored
- The web UI (`simple_cli_web.py`) works but is fragile — it parses CLI stdout for JSON
- No working test suite exists currently
