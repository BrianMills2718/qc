# Qualitative Coding Analysis System

LLM-powered qualitative coding analysis for interview transcripts. Runs a 4-phase analysis pipeline producing structured, evidence-grounded output.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Start the API server
python start_server.py

# Run analysis (in another terminal)
python qc_cli.py analyze --files interview1.docx interview2.docx --format json --output-file results.json
```

## How It Works

The system runs a 4-phase qualitative coding pipeline:

1. **Open Code Discovery** — Identifies 10-15 hierarchical thematic codes grounded in interview content
2. **Speaker/Participant Analysis** — Identifies participants, maps perspectives to codes, detects internal tensions
3. **Entity & Relationship Mapping** — Extracts key entities and maps 10-15 evidence-backed relationships
4. **Synthesis & Recommendations** — Integrates findings with verbatim quotes and actionable recommendations

Each phase uses structured LLM output (Pydantic schemas + JSON mode) — no fragile text parsing.

## Supported Formats

- `.txt` — Plain text
- `.docx` — Microsoft Word
- `.pdf` — PDF documents
- `.rtf` — Rich Text Format

## Output

JSON output includes:
- **codes_identified** — Thematic codes with actual mention counts and calibrated confidence scores
- **speakers_identified** — Named participants with roles and perspective summaries
- **key_relationships** — Entity relationships with evidence
- **key_themes** — Major findings with verbatim quotes (no fabricated statistics)
- **recommendations** — Actionable recommendations grounded in interview content
- **data_warnings** — Flags for truncated or incomplete input documents

## CLI Options

```bash
# Analyze specific files
python qc_cli.py analyze --files file1.docx file2.docx --format json

# Analyze a directory
python qc_cli.py analyze --directory /path/to/interviews/ --format json

# Save to file
python qc_cli.py analyze --files file.docx --format json --output-file results.json

# Check server/job status
python qc_cli.py status --server
python qc_cli.py status --job <job_id>
```

## Development

```bash
# Run tests (28 passing)
python -m pytest tests/ -v

# Start web UI (optional, port 5003)
python simple_cli_web.py
```

## Architecture

- **CLI** (`qc_cli.py`) — Thin HTTP client that talks to the API server
- **API Server** (`qc_clean/plugins/api/api_server.py`) — FastAPI on port 8002, runs analysis in background
- **LLM Handler** (`qc_clean/core/llm/llm_handler.py`) — LiteLLM integration with `extract_structured()`
- **Schemas** (`qc_clean/schemas/analysis_schemas.py`) — Pydantic models for all 4 phases
- **Default model**: gpt-5-mini (OpenAI)
