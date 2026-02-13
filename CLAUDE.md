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
     -> review_ui.py                         # Browser-based code review UI (self-contained HTML)
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
        -> data_exporter.py                  # ProjectExporter (JSON/CSV/Markdown/QDPX)
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
- `qc_clean/plugins/api/review_ui.py` - Self-contained HTML review UI (string.Template)
- `qc_clean/core/llm/llm_handler.py` - LLM handler with `extract_structured()` method
- `qc_clean/core/export/data_exporter.py` - ProjectExporter (JSON/CSV/Markdown/QDPX from ProjectState)
- `qc_cli.py` - CLI interface (analyze, project, review, status, server)
- `tests/` - 201 passing tests

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
python qc_cli.py project export <project_id> --format qdpx --output-file export.qdpx  # ATLAS.ti/NVivo

# Review codes (CLI)
python qc_cli.py review <project_id>
python qc_cli.py review <project_id> --approve-all
python qc_cli.py review <project_id> --file decisions.json

# Review codes (browser - requires server running)
# Open http://localhost:8002/review/<project_id>

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
- `src/` directory is legacy code (gitignored)

## Competitive Landscape (assessed 2026-02-12)

### Our Unique Position
Only open-source tool combining: full GT pipeline (open -> axial -> selective -> theory integration), methodology-aware multi-stage pipeline engine, structured LLM output via Pydantic schemas, human review loop (approve/reject/modify/merge/split), cross-interview analysis, speaker detection, saturation detection, and theoretical sampling.

### Open-Source Competitors
| Tool | Stars | Approach | Key Difference from Us |
|------|-------|----------|----------------------|
| **QualCoder** | 560 | Desktop QDA (PyQt6/SQLite), AI bolted on via RAG+LangChain | Manual-first; AI is assistive chat, not automated pipeline. Has IRR (Cohen's kappa). No GT pipeline. |
| **LLMCode** | 69 | Jupyter notebooks for thematic analysis | Academic (CHI paper). Can compare LLM vs human codes. No pipeline orchestration, no GT. |
| **qc (Proctor)** | 23 | CLI QDA tool, YAML codebook, JOSS published | Manual coding with Unix composability. No LLM pipeline. Multi-coder support. |
| **iQual** (World Bank) | 25 | Scale human codes via ML classifiers | No LLMs. Train-on-human-examples approach. Has formal bias/reliability testing. |
| **Yale LLM-TA Tool** | 2 | Multi-model thematic analysis with IRR | Runs same analysis across 6+ models, computes Cohen's kappa + cosine similarity. No GT. |
| **CRISP-T** | 8 | GT-focused NLP/ML toolkit, adding Claude agent | Successor to QRMine. GT mentions but no formal pipeline. Transitioning to LLM. |

### Commercial Competitors (AI Features)
| Tool | AI Approach | Weakness |
|------|-----------|----------|
| **ATLAS.ti** ($750-1840/yr) | AI open coding (GPT), Intentional AI Coding | Produces 450+ irrelevant codes; no methodology awareness; locked to OpenAI |
| **NVivo** ($849-2500/yr) | Subcode suggestions, summarization, autocoding | Conservative AI; no pipeline; expensive collaboration ($499 add-on) |
| **MAXQDA** ($253-1499/yr) | AI code/subcode suggestions, summarization, chat | AI Assist is add-on; no cross-document intelligence; no GT pipeline |
| **Dedoose** ($15/mo) | Keyword-based auto-coding only | Minimal AI; traditional NLP not LLM-powered |

### Strategic Insight
Commercial tools treat AI as a **feature bolted onto manual coding**. We treat AI as the **core engine of a methodology-aware pipeline**. No commercial or open-source tool offers: (1) automated GT pipeline, (2) cross-interview analysis, (3) structured LLM output with schema validation, (4) integrated human review checkpoints. The market gap is "academic-grade, LLM-native, methodology-aware QDA tool."

### What Competitors Have That We Don't
- **Inter-rater reliability**: QualCoder, iQual, Yale tool all compute IRR metrics
- **Desktop GUI**: QualCoder has full PyQt6 desktop app with audio/video/image coding
- **Academic publications**: LLMCode (CHI), qc (JOSS), iQual (World Bank paper), DeTAILS (ACM CUI)
- **Local model support** (documented): QualCoder supports Ollama; our LiteLLM can route to local models but this isn't documented
- **RAG/vector search**: QualCoder uses FAISS + embeddings for semantic search across corpus

## E2E Validation (completed 2026-02-12)

Pipeline validated end-to-end against real interview transcripts using gpt-5-mini:

- **Default methodology, 1 document**: 12 codes, 29 applications, 8 speakers detected (focus group), perspective/relationship/synthesis all working
- **Default methodology, 3 documents**: 12 codes, 36 properly-attributed applications, cross-interview analysis with 6 shared/6 consensus/6 divergent themes
- **Grounded theory, 1 document**: 25 open codes, 14 axial relationships, 3 core categories, theoretical model generated

Bugs found and fixed during E2E testing:
- Speaker detection: added timestamp format ("Name   0:03") alongside colon format; runs on pre-loaded docs
- Quote attribution: replaced blind duplication with substring matching to correctly attribute quotes to source documents
- Perspective stage: uses detected speaker count (not document count) to determine single vs multi-speaker mode
- Export hierarchy: case-insensitive parent_id matching + recursive tree rendering for arbitrary depth

## Known Technical Debt

1. **Schema duplication**: `analysis_schemas.py` / `gt_schemas.py` (LLM output shapes) and `domain.py` (internal model) overlap; this is intentional -- adapters bridge them
2. **Test gaps**: No unit tests for real pipeline stages (require mocked LLM) or most CLI commands

## Academic Standards Gap Analysis (assessed 2026-02-12)

Evaluated against Strauss & Corbin GT, Charmaz constructivist GT, COREQ/SRQR reporting standards, Lincoln & Guba trustworthiness criteria, and emerging LLM-assisted QC validation requirements.

### What We Have (Tier 1 — Publishable Basics)
- Human-in-the-loop code review with approve/reject/modify/merge/split
- Hierarchical codebook with definitions, confidence, provenance (LLM vs human)
- Quote-to-code attribution with source documents and speaker detection
- Multi-format export (JSON/CSV/Markdown/QDPX for ATLAS.ti/NVivo)
- Methodology declaration in ProjectConfig
- Codebook versioning via ReviewManager

### Critical Gaps (Tier 2 — Expected by Reviewers)

| Gap | Severity | Description |
|-----|----------|-------------|
| **Inter-rater reliability** | High | No multi-pass coding or kappa/alpha computation. Reviewers expect IRR >= 0.70. |
| **Memo generation** | High | AnalysisMemo schema exists but pipeline never generates memos. GT requires continuous memo-writing. |
| **Audit trail for LLM decisions** | High | Phase timing logged but not *why* each code was created. Lincoln & Guba dependability criterion. |
| **Negative case analysis** | High | No mechanism to seek/flag data contradicting emerging categories. |
| **Multi-run stability** | Moderate | LLMs are non-deterministic. No way to show consistent results across runs. |

### GT-Specific Gaps (Tier 3 — Required for GT Publications)

| Gap | Severity | Description |
|-----|----------|-------------|
| **Constant comparison** | Critical | Open coding runs as single LLM batch. True GT requires iterative segment-by-segment coding with continuous code-to-code comparison. |
| **Iterative re-coding** | High | Pipeline runs each stage once. GT requires re-examining earlier data as categories evolve. |
| **Theoretical sampling** | Moderate | Current heuristic uses speaker count + uncoded status. Should identify under-developed categories and seek data to develop them. |
| **Per-category saturation** | Moderate | `saturation.py` checks codebook-level stability. GT requires per-category property/dimension tracking. |
| **Full axial paradigm** | Low | Partially covers Strauss & Corbin paradigm (conditions, consequences) but not full decomposition (context vs intervening conditions). |

### Key Academic References
- Strauss & Corbin (2008) *Basics of Qualitative Research* 3rd ed — canonical Straussian GT
- Charmaz (2014) *Constructing Grounded Theory* 2nd ed — constructivist GT criteria: credibility, originality, resonance, usefulness
- Lincoln & Guba (1985) — trustworthiness: credibility, transferability, dependability, confirmability
- COREQ (Tong et al. 2007) — 32-item reporting checklist for interview/focus group research
- SRQR (O'Brien et al. 2014) — 21-item reporting standard for all qualitative approaches
- Ashwin, Chhabra & Rao (2025) — LLM coding errors may be systematically biased, not random
- O'Connor & Joffe (2020) — IRR thresholds depend on manifest vs latent content
- Krippendorff (2004) — alpha >= 0.80 for reliable conclusions, >= 0.67 for tentative

## Next Steps

### Short-term
- **Pipeline stage tests**: Unit tests for individual stages with mocked LLM handler

### Medium-term (Academic Credibility)
- **Inter-rater reliability**: Run multiple LLM passes, compute Cohen's kappa / Krippendorff's alpha. Every major CAQDAS has this.
- **Memo generation in pipeline**: LLM produces analytical memos alongside codes at each stage. Connect memo schema to actual output.
- **Audit trail enhancement**: Log LLM reasoning for each code creation/categorization. Export in project artifacts.
- **Negative case analysis**: Pipeline sub-step asking "what contradicts the emerging categories?"

### Medium-term (Feature)
- **Incremental coding**: Add new documents to an existing project and re-code without starting over
- **Graph visualization**: NetworkX for code relationship graphs, D3.js/Cytoscape.js in browser review UI
- **Prompt optimization**: A/B test different prompts for code discovery quality

### Long-term (GT Fidelity)
- **Constant comparison loop**: Refactor open coding from single-batch to iterative segment-by-segment with codebook revision
- **Iterative re-coding**: Re-run coding stages with evolved codebook, track iterations
- **True theoretical sampling**: Identify under-developed categories, suggest data sources to develop them

### Long-term (Platform)
- **Multi-model consensus**: Run analysis across GPT/Claude/Gemini and merge codebooks
- **Active learning**: Use human review decisions to fine-tune prompting for the project
- **Collaborative coding**: Multiple human reviewers with conflict resolution
