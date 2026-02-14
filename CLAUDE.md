# Qualitative Coding Analysis System (v2.1)

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
- `qc_clean/core/llm/llm_handler.py` - LLM handler with `extract_structured()` method
- `qc_clean/core/export/data_exporter.py` - ProjectExporter (JSON/CSV/Markdown/QDPX from ProjectState)
- `qc_cli.py` - CLI interface (analyze, project, review, status, server)
- `tests/` - 461 unit tests + 6 E2E tests (22 test files)

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
- Default model: gpt-5-mini via OpenAI API (note: gpt-5 models don't support temperature param)
- `analysis_schemas.py` defines LLM output shapes; `adapters.py` converts them to domain objects
- Every stage produces an analytical memo (LLM reasoning trail) saved to `state.memos`
- GT constant comparison: segments documents by speaker turns or paragraph chunks, iteratively codes each segment against an evolving codebook, stops when saturation reached
- Incremental coding: `project recode` codes only uncoded documents against the existing codebook, then re-runs downstream stages
- Graph visualization: `/graph/{project_id}` serves interactive Cytoscape.js graphs (code hierarchy, relationships, entity map)
- Fail-loud: downstream stages raise `RuntimeError` via `ctx.require()` if upstream data is missing (no silent empty-data fallbacks). Review raises `ValueError` on unknown target types.
- Observability: LLMHandler logs model/schema/prompt_len/duration/tokens on every call. All stages log entry context (doc/code counts, model). Pipeline engine logs state context on failure.

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

# Run tests
python -m pytest tests/ -v
```

## Configuration

The LLM handler reads API keys from environment variables. Default model: `gpt-5-mini`.

Key env vars:
- `OPENAI_API_KEY` / `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` -- API key for the model provider
- `qc_clean/config/unified_config.py` -- `UnifiedConfig` dataclass reads env vars: `API_PROVIDER`, `MODEL`, `METHODOLOGY`, `CODING_APPROACH`, `VALIDATION_LEVEL`, `TEMPERATURE`
- `qc_clean/core/config/env_config.py` -- Active server config (used by `start_server.py`)

## Model Selection Notes

Default model is `gpt-5-mini` (cheap, adequate for most stages). Can switch per-run with `--model`. Places where a stronger model (e.g. Claude Sonnet/Opus, GPT-5) could matter:

- **IRR results** — if kappa scores come back low, a better model might produce more consistent/accurate codes
- **GT axial/selective coding** — requires sophisticated reasoning about relationships between categories; if output quality is shallow, upgrading the model could help
- **Negative case analysis** — asking "what contradicts these findings?" is a harder reasoning task; now implemented as `NegativeCaseStage`

## Development Notes

- This is a research tool, not a production system
- Interview data files are gitignored (sensitive content)
- `src/` directory is legacy code (gitignored)

## Competitive Landscape (assessed 2026-02-12)

### Our Unique Position
Only open-source tool combining: full GT pipeline (constant comparison -> axial -> selective -> theory integration), methodology-aware multi-stage pipeline engine, structured LLM output via Pydantic schemas, human review loop (approve/reject/modify/merge/split), cross-interview analysis, speaker detection, saturation detection, theoretical sampling, incremental re-coding, and interactive graph visualization.

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
- ~~**Inter-rater reliability**: QualCoder, iQual, Yale tool all compute IRR metrics~~ (Now implemented)
- **Desktop GUI**: QualCoder has full PyQt6 desktop app with audio/video/image coding
- **Academic publications**: LLMCode (CHI), qc (JOSS), iQual (World Bank paper), DeTAILS (ACM CUI)
- **Local model support** (documented): QualCoder supports Ollama; our LiteLLM can route to local models but this isn't documented
- **RAG/vector search**: QualCoder uses FAISS + embeddings for semantic search across corpus

## E2E Validation (updated 2026-02-13)

Pipeline validated end-to-end against real interview transcripts using gpt-5-mini. Automated E2E tests in `tests/test_e2e.py` (requires `OPENAI_API_KEY`):

- **Default methodology, 1 document**: 14 codes, 17 applications, 2 speakers detected, 7 memos, negative case analysis
- **Default methodology, 2 documents**: 14 codes, 30 applications across 2 docs, cross-interview analysis with consensus/divergent themes
- **Grounded theory, 1 document**: 8 open codes, 40 applications, 3 core categories, theoretical model generated, 6 memos
- **Incremental coding**: Initial pipeline (12 codes, 19 apps) + add doc + recode = 17 codes, 32 apps, iteration 2
- **Graph data**: 13 code nodes, 25 entity nodes, 12 entity relationships from completed state
- **Export**: JSON, Markdown, CSV all produce valid output from real pipeline results

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

1. **LLMs don't reliably fill every schema field.** Even with JSON mode, gpt-5-mini sometimes omits fields. All LLM-facing Pydantic schema fields should have defaults unless you truly want the pipeline to crash on omission. Currently fixed: `NegativeCase.implication`. Still vulnerable: several fields in `TheoreticalModel`, `OpenCode`, `AxialRelationship` — see schema robustness audit below.

2. **Unit tests with mocks don't catch integration bugs.** 461 unit tests passed, but two real bugs hid in the seams between stages: (a) `NegativeCase.implication` required but LLM omits it, (b) incremental pipeline included stages that depend on data from a stage that doesn't run. Only E2E with real LLM calls found these.

3. **Fail-loud makes integration bugs easy to diagnose.** The `ctx.require()` pattern immediately told us which field was missing and which stage needed it. Without it, the bug would have produced silent garbage output.

4. **LLM output is non-deterministic.** Same input produces 8-14 codes across runs. E2E assertions must be loose (`>= 3` not `== 12`). This is inherent to LLM-powered systems.

5. **Schema robustness priority list** (fields that could fail if LLM omits them):
   - `TheoreticalModel.core_categories` — empty list crashes the `.core_category` property accessor
   - `OpenCode.supporting_quotes` — used for code application matching
   - `AxialRelationship.conditions/consequences` — required lists with no defaults
   - `EntityRelationship.supporting_evidence` — required list with no default

## Known Technical Debt

1. **Schema duplication**: `analysis_schemas.py` / `gt_schemas.py` (LLM output shapes) and `domain.py` (internal model) overlap; this is intentional — adapters bridge them
2. **LLM schema fragility**: Several LLM-facing schemas have required fields with no defaults. The LLM can omit these, causing `ValidationError`. See "Design Lessons" above for the priority list.
3. **`methodology_config.py`**: Only imported by tests now (not production code); could be removed if tests are refactored

## Academic Standards Gap Analysis (assessed 2026-02-12)

Evaluated against Strauss & Corbin GT, Charmaz constructivist GT, COREQ/SRQR reporting standards, Lincoln & Guba trustworthiness criteria, and emerging LLM-assisted QC validation requirements.

### What We Have (Tier 1 — Publishable Basics)
- Inter-rater reliability: multi-pass LLM coding with prompt variation, Cohen's kappa / Fleiss' kappa / percent agreement
- Human-in-the-loop code review with approve/reject/modify/merge/split
- Hierarchical codebook with definitions, confidence, provenance (LLM vs human)
- Quote-to-code attribution with source documents and speaker detection
- Multi-format export (JSON/CSV/Markdown/QDPX for ATLAS.ti/NVivo)
- Methodology declaration in ProjectConfig
- Codebook versioning via ReviewManager
- Analytical memo generation: all pipeline stages produce LLM-generated memos with reasoning, uncertainties, and emerging patterns
- Per-code audit trail: each code includes LLM reasoning for why it was created (Lincoln & Guba dependability)
- Negative case analysis: automated search for disconfirming evidence after coding (Lincoln & Guba credibility)
- Multi-run stability analysis: run identical coding N times, per-code stability scores, stable/moderate/unstable classification

### Critical Gaps (Tier 2 — Expected by Reviewers)

| Gap | Severity | Description |
|-----|----------|-------------|
| **Inter-rater reliability** | ~~High~~ **Done** | Implemented: multi-pass coding with prompt variation, Cohen's/Fleiss' kappa, Landis & Koch interpretation. CLI: `project irr`. |
| **Memo generation** | ~~High~~ **Done** | All 8 pipeline stages generate analytical memos via LLM `analytical_memo` field. Exported in Markdown, CSV (`memos.csv`), and QDPX (`<Notes>`). |
| **Audit trail for LLM decisions** | ~~High~~ **Done** | Per-code `reasoning` field explains why each code was created. Exported in CSV (`reasoning` column) and Markdown (Audit Trail section). |
| **Negative case analysis** | ~~High~~ **Done** | `NegativeCaseStage` runs after coding in both pipelines. LLM searches for disconfirming evidence and produces structured negative case memos. |
| **Multi-run stability** | ~~Moderate~~ **Done** | `project stability` runs N identical passes, computes per-code stability scores, classifies as stable/moderate/unstable. Exported in Markdown and CSV. |

### GT-Specific Gaps (Tier 3 — Required for GT Publications)

| Gap | Severity | Description |
|-----|----------|-------------|
| **Constant comparison** | ~~Critical~~ **Done** | `GTConstantComparisonStage` replaces batch open coding. Segments documents by speaker turns or paragraph chunks, iteratively codes each segment against evolving codebook, checks saturation after each pass. |
| **Iterative re-coding** | ~~High~~ **Done** | `project recode` command: codes only new/uncoded documents against existing codebook, merges results, re-runs downstream stages. |
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

### Completed (v2.1)
- ~~**Inter-rater reliability**~~ — `project irr` CLI command (multi-pass, Cohen's/Fleiss' kappa)
- ~~**Memo generation**~~ — all 8 stages produce analytical memos
- ~~**Audit trail**~~ — per-code `reasoning` field + Audit Trail export
- ~~**Negative case analysis**~~ — `NegativeCaseStage` in both pipelines
- ~~**Pipeline stage tests**~~ — 28 mocked-LLM tests covering all 8 stages + cross-interview + edge cases
- ~~**Multi-run stability**~~ — `project stability` CLI command, per-code stability scores, Markdown/CSV export
- ~~**Incremental coding**~~ — `project recode` codes new documents against existing codebook, merges results, re-runs downstream stages
- ~~**Graph visualization**~~ — `/graph/{project_id}` interactive Cytoscape.js graphs (code hierarchy, relationships, entity map) with search, PNG export
- ~~**Constant comparison**~~ — `GTConstantComparisonStage` replaces batch open coding: segment-by-segment iterative coding with saturation detection
- ~~**Fail-loud enforcement**~~ — `PipelineContext.require()` for inter-stage data dependencies, `ValueError` on bad review decisions, no silent fallbacks
- ~~**Observability**~~ — LLM call instrumentation (model/schema/duration/tokens), stage entry context logging, failure state logging

### Short-term — Code Quality
- ~~**Typed PipelineContext**~~ — `PipelineContext` Pydantic model replaces `config: dict` across all 14 stages (`extra="forbid"` catches typos)
- ~~**Typed return values**~~ — `CodebookChangeResult`, `SaturationCheckResult`, `CrossInterviewResult`, `ReviewSummary`, `SamplingSuggestion` replace plain dicts
- ~~**CLI utility tests**~~ — 57 tests for file_handler, formatters (json/table/human), progress utilities
- ~~**E2E validation**~~ — 6 E2E tests with real LLM calls: default/GT/incremental pipelines, graph data, export. Caught 2 bugs unit tests missed.
- **LLM schema robustness audit**: Several LLM-facing schemas have required fields the LLM may omit (see Design Lessons below). Add defaults to remaining vulnerable fields.

### Future — GT Fidelity (Tier 3)
- **True theoretical sampling** (Moderate): Identify under-developed categories, suggest specific data sources to develop them
- **Per-category saturation** (Moderate): Track property/dimension saturation per category, not just codebook-level stability
- **Full axial paradigm** (Low): Decompose Strauss & Corbin paradigm fully (context vs intervening conditions vs causal conditions)

### Future — Features
- **Prompt optimization**: A/B test different prompts for code discovery quality
- **Multi-model consensus**: Run analysis across GPT/Claude/Gemini and merge codebooks
- **Active learning**: Use human review decisions to fine-tune prompting for the project
- **Collaborative coding**: Multiple human reviewers with conflict resolution
