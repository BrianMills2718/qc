# Qualitative Coding Analysis System

LLM-powered qualitative coding analysis for interview transcripts. Stage-based pipeline with human-in-the-loop review, producing structured, evidence-grounded output.

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

Two analysis methodologies, each running as a stage-based pipeline:

**Default/Thematic Analysis:**
1. **Ingest** -- Load documents, detect speakers, flag truncation
2. **Thematic Coding** -- Discover 10-15 hierarchical codes grounded in content
3. **Perspective Analysis** -- Map participants to codes, detect consensus/tensions
4. **Relationship Mapping** -- Extract entities and evidence-backed relationships
5. **Synthesis** -- Integrate findings with verbatim quotes and recommendations
6. **Cross-Interview Analysis** -- Identify patterns across documents (multi-doc only)

**Grounded Theory:**
1. **Ingest** -- Same as above
2. **Open Coding** -- Line-by-line code discovery
3. **Axial Coding** -- Identify relationships between codes
4. **Selective Coding** -- Core category identification
5. **Theory Integration** -- Build theoretical model
6. **Cross-Interview Analysis** -- Same as above

Each stage uses structured LLM output (Pydantic schemas + JSON mode). The pipeline can pause for human review between stages.

## Project Management

Projects persist analysis state locally as JSON -- no database needed.

```bash
# Create a project
python qc_cli.py project create --name "My Study" --methodology grounded_theory

# Add documents
python qc_cli.py project add-docs <project_id> --files interview1.docx interview2.docx

# Run the pipeline (local, no server needed)
python qc_cli.py project run <project_id>
python qc_cli.py project run <project_id> --review    # pause for human review

# Export results
python qc_cli.py project export <project_id> --format json --output-file results.json
python qc_cli.py project export <project_id> --format csv --output-dir ./export/
python qc_cli.py project export <project_id> --format markdown --output-file report.md

# List projects
python qc_cli.py project list

# Review codes (approve/reject/modify)
python qc_cli.py review <project_id>
python qc_cli.py review <project_id> --approve-all
python qc_cli.py review <project_id> --file decisions.json
```

## Supported Formats

- `.txt` -- Plain text
- `.docx` -- Microsoft Word (requires python-docx)
- `.pdf` -- PDF documents (requires PyPDF2)
- `.rtf` -- Rich Text Format (requires striprtf)

## Output

JSON output includes:
- **codes_identified** -- Thematic codes with actual mention counts and calibrated confidence scores
- **speakers_identified** -- Named participants with roles and perspective summaries
- **key_relationships** -- Entity relationships with evidence
- **key_themes** -- Major findings with verbatim quotes (no fabricated statistics)
- **recommendations** -- Actionable recommendations grounded in interview content
- **memos** -- Analytical memos (cross-interview patterns, causal chains)
- **pipeline_phases** -- Status of each pipeline stage
- **data_warnings** -- Flags for truncated or incomplete input documents

## Development

```bash
# Run tests (147 passing)
python -m pytest tests/ -v

# Start web UI (optional, port 5003)
python simple_cli_web.py
```

## Architecture

- **CLI** (`qc_cli.py`) -- Thin HTTP client that talks to the API server
- **API Server** (`qc_clean/plugins/api/api_server.py`) -- FastAPI on port 8002, delegates to pipeline
- **Pipeline** (`qc_clean/core/pipeline/`) -- Stage-based engine with PipelineStage ABC
- **Review** (`qc_clean/core/pipeline/review.py`) -- Human review loop for codes
- **Domain Model** (`qc_clean/schemas/domain.py`) -- ProjectState holding all analysis state
- **Persistence** (`qc_clean/core/persistence/`) -- JSON file storage for projects
- **LLM Handler** (`qc_clean/core/llm/llm_handler.py`) -- LiteLLM with `extract_structured()`
- **Default model**: gpt-5-mini (OpenAI)

See `CLAUDE.md` for detailed architecture and development notes.
