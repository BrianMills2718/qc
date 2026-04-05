# Qualitative Coding Analysis System (v2.2)

LLM-powered qualitative coding analysis for interview transcripts. The system supports both thematic analysis and grounded theory, uses structured Pydantic-backed LLM output throughout, and keeps project state in a single JSON-serializable `ProjectState`.

## Quick Start

The local project workflow is the main path for v2.2. The API server is only required for one-shot `analyze` runs and the browser UIs.

```bash
# Install dependencies
pip install -r requirements.txt

# Set an API key for your chosen provider
export OPENAI_API_KEY=sk-...

# Create a project
python qc_cli.py project create --name "My Study" --methodology grounded_theory

# Add interview files
python qc_cli.py project add-docs <project_id> --files interview1.docx interview2.docx

# Run the full pipeline locally
python qc_cli.py project run <project_id>

# Export results
python qc_cli.py project export <project_id> --format markdown --output-file report.md
```

For the API-backed one-shot flow:

```bash
python start_server.py
python qc_cli.py analyze --files interview1.docx interview2.docx --format json --output-file results.json
```

## Methodologies

### Default / Thematic Analysis

1. **Ingest**: load documents and detect speakers
2. **Thematic Coding**: discover hierarchical codes grounded in the transcripts
3. **Perspective Analysis**: analyze participant perspectives and tensions
4. **Relationship Mapping**: extract entities and evidence-backed relationships
5. **Synthesis**: integrate findings and recommendations
6. **Negative Case Analysis**: identify disconfirming evidence
7. **Cross-Interview Analysis**: compare patterns across documents when the corpus has multiple interviews

### Grounded Theory

1. **Ingest**: load documents and detect speakers
2. **Constant Comparison Coding**: iteratively code transcript segments against an evolving codebook
3. **Axial Coding**: identify relationships between categories
4. **Selective Coding**: identify core categories
5. **Theory Integration**: build the theoretical model
6. **Negative Case Analysis**: identify disconfirming evidence
7. **Cross-Interview Analysis**: compare patterns across documents when the corpus has multiple interviews

Both methodologies use structured LLM output, fail-loud stage dependencies, and optional human review checkpoints.

## v2.2 Capabilities

- Full thematic and grounded theory pipelines, including negative case analysis in both methodologies
- Automatic cross-interview analysis for multi-document corpora
- Incremental re-coding of newly added documents via `python qc_cli.py project recode <project_id>`
- Human review in both CLI and browser flows
- Inter-rater reliability analysis via `project irr`
- Multi-run stability analysis via `project stability`
- Interactive graph visualization in the browser
- JSON, CSV, and Markdown export from persisted project state
- Analytical memos at every stage plus per-code reasoning and audit-trail output

## Common Commands

```bash
# Create and inspect projects
python qc_cli.py project create --name "My Study" --methodology grounded_theory
python qc_cli.py project list
python qc_cli.py project show <project_id>

# Add documents from explicit files
python qc_cli.py project add-docs <project_id> --files interview1.docx interview2.docx

# Run locally
python qc_cli.py project run <project_id>
python qc_cli.py project run <project_id> --model gpt-5-mini
python qc_cli.py project run <project_id> --review

# Incremental coding for newly added documents
python qc_cli.py project recode <project_id>

# Reliability and stability analysis
python qc_cli.py project irr <project_id>
python qc_cli.py project stability <project_id>

# Export results
python qc_cli.py project export <project_id> --format json --output-file results.json
python qc_cli.py project export <project_id> --format csv --output-dir ./export
python qc_cli.py project export <project_id> --format markdown --output-file report.md

# Review codes from the CLI
python qc_cli.py review <project_id>
python qc_cli.py review <project_id> --approve-all
python qc_cli.py review <project_id> --file decisions.json
```

Browser flows require the API server:

```bash
python start_server.py
```

- Review UI: `http://localhost:8002/review/<project_id>`
- Graph UI: `http://localhost:8002/graph/<project_id>`

## Supported Input Formats

- `.txt`
- `.docx`
- `.pdf`
- `.rtf`

## Output and State

Projects are persisted locally as JSON via `ProjectState`; no database is required. Completed runs can include:

- Hierarchical codebooks with mention counts, confidence, provenance, and reasoning
- Code applications tied to source documents and speakers
- Participant perspective analysis
- Entity and relationship maps
- Synthesis findings and recommendations
- Negative case findings
- Cross-interview analysis
- Analytical memos
- IRR and stability results when those analyses are run

## Development

```bash
# Run the full test suite
python -m pytest tests/ -v
```

`tests/test_e2e.py` covers end-to-end flows and requires an API key for live model execution.

## Architecture

- `qc_cli.py`: CLI entry point for project management, local pipeline runs, review, and one-shot analysis
- `qc_clean/core/pipeline/`: stage-based pipeline engine and methodology factory
- `qc_clean/core/pipeline/stages/`: one file per pipeline stage
- `qc_clean/core/pipeline/review.py`: human review loop
- `qc_clean/core/pipeline/irr.py`: inter-rater reliability and stability analysis
- `qc_clean/core/persistence/`: JSON project storage
- `qc_clean/core/export/data_exporter.py`: export from `ProjectState`
- `qc_clean/plugins/api/`: FastAPI server plus review and graph browser UIs

See `CLAUDE.md` for the canonical project documentation.
