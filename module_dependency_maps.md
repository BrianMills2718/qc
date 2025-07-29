# Module Internal Dependency Maps

This document provides detailed internal dependency analysis for each of the 6 modules in the qualitative coding system.

---

## 🏗️ Module 1: Infrastructure Layer
**Status**: ✅ **COMPLETE** - Production-ready utilities preserved from cleanup

### Internal Component Map
```
┌─────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  config_manager.py (CORE)                                  │
│  ├── SecretStr handling                                    │
│  ├── Environment validation                                │
│  ├── Pydantic models                                       │
│  └── Configuration persistence                             │
│                    │                                       │
│                    ▼                                       │
│  input_validator.py (SECURITY)                            │
│  ├── XSS/SQL injection protection                         │
│  ├── Input sanitization                                   │
│  ├── File validation                                      │
│  └── Pattern matching (DEPENDS: config_manager patterns)  │
│                    │                                       │
│                    ▼                                       │
│  structured_logger.py (OBSERVABILITY)                     │
│  ├── JSON log formatting                                  │
│  ├── Correlation ID tracking                              │
│  ├── Context variables                                    │
│  ├── Performance metrics                                  │
│  └── Log level management                                 │
│                    │                                       │
│                    ▼                                       │
│  robust_error_handling.py (RELIABILITY)                   │
│  ├── Error classification system                          │
│  ├── Retry logic with exponential backoff                 │
│  ├── Recovery strategies                                  │
│  ├── Error context preservation                           │
│  └── Severity-based routing (DEPENDS: structured_logger)  │
│                    │                                       │
│                    ▼                                       │
│  llm_content_extractor.py (PARSING)                       │
│  ├── Multi-provider response parsing                      │
│  ├── Format detection (OpenAI, Gemini, Claude)           │
│  ├── Content extraction strategies                        │
│  └── Fallback parsing (DEPENDS: robust_error_handling)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Internal Dependencies
1. **config_manager.py** → Foundation (no internal deps)
2. **input_validator.py** → Uses config patterns from config_manager
3. **structured_logger.py** → Independent (only external Python libs)
4. **robust_error_handling.py** → Uses structured_logger for error logging
5. **llm_content_extractor.py** → Uses robust_error_handling for parsing failures

### Build Order
1. ✅ config_manager.py (complete)
2. ✅ structured_logger.py (complete) 
3. ✅ input_validator.py (complete)
4. ✅ robust_error_handling.py (complete)
5. ✅ llm_content_extractor.py (complete)

---

## 🤖 Module 2: LLM Integration Layer
**Status**: ✅ **EXISTS** - Universal client patterns preserved, needs integration testing

### Internal Component Map
```
┌─────────────────────────────────────────────────────────────┐
│                 LLM INTEGRATION LAYER                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Provider Adapters (BASE LEVEL)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  simple_gemini_client.py                           │   │
│  │  ├── Gemini 2.5 Flash API integration             │   │
│  │  ├── Token optimization (1M context, 60K output)  │   │
│  │  ├── Response format handling                      │   │
│  │  └── Rate limiting                                 │   │
│  │            │                                       │   │
│  │            ▼                                       │   │
│  │  [Future] claude_client.py                        │   │
│  │  [Future] openai_client.py                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Response Processing (MIDDLE LEVEL)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  response_parser.py (CREATE)                       │   │
│  │  ├── JSON extraction and validation                │   │
│  │  ├── Theme structure parsing                       │   │
│  │  ├── Error recovery for partial responses          │   │
│  │  └── Quality validation                            │   │
│  │  (DEPENDS: llm_content_extractor, error_handling)  │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Universal Client (TOP LEVEL)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  llm_client.py                                      │   │
│  │  ├── Multi-provider fallback chains                │   │
│  │  ├── Request routing and load balancing            │   │
│  │  ├── Retry logic with backoff                      │   │
│  │  ├── Usage tracking and optimization               │   │
│  │  └── Provider health monitoring                    │   │
│  │  (DEPENDS: all provider adapters, response_parser) │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Internal Dependencies
1. **simple_gemini_client.py** → Infrastructure layer (config, error handling, logging)
2. **response_parser.py** (CREATE) → Infrastructure (llm_content_extractor, error handling)
3. **llm_client.py** → All provider clients + response_parser

### Build Order
1. ✅ simple_gemini_client.py (exists, test needed)
2. 🔨 **response_parser.py** (CREATE - critical for QC-specific parsing)
3. ✅ llm_client.py (exists, integration test needed)
4. 🔨 **Integration testing** with Infrastructure layer

### Missing Components (CREATE)
- **response_parser.py** - QC-specific JSON parsing and validation
- **token_optimizer.py** - Intelligent batching for large interviews
- **[Future]** claude_client.py, openai_client.py for fallback chains

---

## 🧠 Module 3: Qualitative Coding Core
**Status**: ✅ **EXISTS** - True QC implementation preserved, needs integration

### Internal Component Map
```
┌─────────────────────────────────────────────────────────────┐
│                QUALITATIVE CODING CORE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Data Models (FOUNDATION)                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  qc_models.py (CREATE)                              │   │
│  │  ├── Theme, Category, Code classes                  │   │
│  │  ├── AnalyticalMemo class                          │   │
│  │  ├── Interview class with metadata                  │   │
│  │  ├── CodeHierarchy management                       │   │
│  │  └── Saturation tracking models                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Core Extraction Engine (MAIN)                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  qualitative_coding_extractor.py ✅                 │   │
│  │  ├── Three-phase extraction pipeline               │   │
│  │  │   ├── Phase 1: Unconstrained theme discovery    │   │
│  │  │   ├── Phase 2: Hierarchical organization        │   │
│  │  │   └── Phase 3: Code consistency validation      │   │
│  │  ├── Grounded theory development                    │   │
│  │  ├── Analytical memo generation                     │   │
│  │  └── Theme saturation detection                     │   │
│  │  (DEPENDS: qc_models, LLM Integration Layer)        │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Analysis & Validation (SUPPORT)                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  theme_analyzer.py (CREATE)                        │   │
│  │  ├── Theme co-occurrence analysis                   │   │
│  │  ├── Code frequency tracking                        │   │
│  │  ├── Saturation assessment                          │   │
│  │  ├── Quality metrics calculation                    │   │
│  │  └── Contradiction detection                        │   │
│  │  (DEPENDS: qc_models, qualitative_coding_extractor) │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Codebook Management (EVOLUTION)                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  codebook_manager.py (CREATE)                      │   │
│  │  ├── Codebook versioning and evolution             │   │
│  │  ├── Theme hierarchy persistence                    │   │
│  │  ├── Memo linking and organization                  │   │
│  │  ├── Code definition management                     │   │
│  │  └── Export/import functionality                    │   │
│  │  (DEPENDS: qc_models, Infrastructure persistence)   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Internal Dependencies
1. **qc_models.py** (CREATE) → Infrastructure layer only
2. **qualitative_coding_extractor.py** ✅ → qc_models + LLM Integration
3. **theme_analyzer.py** (CREATE) → qc_models + extractor
4. **codebook_manager.py** (CREATE) → qc_models + Infrastructure persistence

### Build Order
1. 🔨 **qc_models.py** (CREATE - foundation data structures)
2. ✅ qualitative_coding_extractor.py (exists, adapt to use qc_models)
3. 🔨 **theme_analyzer.py** (CREATE - analysis and validation)
4. 🔨 **codebook_manager.py** (CREATE - persistence and evolution)

### Missing Components (CREATE)
- **qc_models.py** - Core data structures for themes, codes, memos
- **theme_analyzer.py** - Analysis, metrics, contradiction detection
- **codebook_manager.py** - Persistence and codebook evolution

---

## ⚙️ Module 4: Processing Layer
**Status**: 🔄 **NEEDS ADAPTATION** - Batch patterns exist but entity-focused

### Internal Component Map
```
┌─────────────────────────────────────────────────────────────┐
│                   PROCESSING LAYER                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Document Handling (INPUT)                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  interview_parser.py (CREATE)                       │   │
│  │  ├── DOCX file parsing                              │   │
│  │  ├── Text extraction and cleaning                   │   │
│  │  ├── Metadata extraction (participant, date, type)  │   │
│  │  ├── Interview segmentation                         │   │
│  │  └── Quality validation                             │   │
│  │  (DEPENDS: Infrastructure input_validator)          │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Batch Orchestration (CORE)                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  parallel_batch_processor.py 🔄                     │   │
│  │  ├── Concurrent interview processing                │   │
│  │  ├── Rate limiting and throttling                   │   │
│  │  ├── Progress tracking                              │   │
│  │  ├── Error recovery and retry                       │   │
│  │  ├── Partial result aggregation                     │   │
│  │  └── State persistence for resume                   │   │
│  │  (NEEDS ADAPTATION from entity to QC processing)    │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Workflow Management (ORCHESTRATION)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  workflow_manager.py (CREATE)                      │   │
│  │  ├── Interview sequencing and dependencies         │   │
│  │  ├── Phase coordination (3-phase QC pipeline)      │   │
│  │  ├── Resource allocation and optimization          │   │
│  │  ├── Progress monitoring and reporting             │   │
│  │  └── Failure handling and recovery                 │   │
│  │  (DEPENDS: parallel_batch_processor, QC Core)      │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  State Management (PERSISTENCE)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  session_manager.py (CREATE)                       │   │
│  │  ├── Processing session persistence                │   │
│  │  ├── Resume capability after interruption          │   │
│  │  ├── Progress state tracking                       │   │
│  │  ├── Partial result preservation                   │   │
│  │  └── Session metadata management                   │   │
│  │  (DEPENDS: Infrastructure config_manager, qc_models)│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Internal Dependencies
1. **interview_parser.py** (CREATE) → Infrastructure input_validator
2. **parallel_batch_processor.py** 🔄 → All other components (needs major adaptation)
3. **workflow_manager.py** (CREATE) → batch_processor + QC Core
4. **session_manager.py** (CREATE) → Infrastructure + QC models

### Build Order
1. 🔨 **interview_parser.py** (CREATE - document handling foundation)
2. 🔄 **parallel_batch_processor.py** (ADAPT from entity to QC focus)
3. 🔨 **workflow_manager.py** (CREATE - orchestration logic)
4. 🔨 **session_manager.py** (CREATE - state persistence)

### Major Adaptations Needed
- **parallel_batch_processor.py**: Change from entity extraction to QC theme extraction
- Remove Neo4j integration, add QC Core integration
- Adapt error handling for QC-specific failures
- Change result aggregation from entities to themes

---

## 🖥️ Module 5: Interface Layer
**Status**: 🔄 **NEEDS REWIRING** - CLI exists but wired to entity extraction

### Internal Component Map
```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACE LAYER                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Configuration (FOUNDATION)                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  cli_config.py ✅                                   │   │
│  │  ├── AnalysisConfig dataclass                       │   │
│  │  ├── YAML/JSON configuration loading                │   │
│  │  ├── Environment validation                         │   │
│  │  ├── QC-specific settings (coding_mode, etc.)       │   │
│  │  └── File discovery and validation                  │   │
│  │  (RECENTLY REFACTORED for QC)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Argument Processing (INPUT)                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  arg_parser.py (CREATE)                            │   │
│  │  ├── Command-line argument definitions             │   │
│  │  ├── Sub-command structure (analyze, batch, etc.)  │   │
│  │  ├── Validation and help text                      │   │
│  │  ├── Configuration file integration                │   │
│  │  └── Interactive mode support                      │   │
│  │  (DEPENDS: cli_config.py)                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Main CLI Interface (ORCHESTRATION)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  cli.py 🔄                                          │   │
│  │  ├── Main entry point and command routing          │   │
│  │  ├── User interaction and feedback                 │   │
│  │  ├── Progress display and reporting                │   │
│  │  ├── Error handling and user guidance              │   │
│  │  └── Results presentation                          │   │
│  │  (NEEDS REWIRING from entity to QC pipeline)       │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  User Experience (PRESENTATION)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ui_components.py (CREATE)                         │   │
│  │  ├── Progress bars and status display              │   │
│  │  ├── Table formatting for results                  │   │
│  │  ├── Interactive prompts and confirmations         │   │
│  │  ├── Error message formatting                      │   │
│  │  └── Success/completion notifications              │   │
│  │  (DEPENDS: cli.py, Infrastructure logging)         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Internal Dependencies
1. **cli_config.py** ✅ → Infrastructure layer (already refactored)
2. **arg_parser.py** (CREATE) → cli_config.py
3. **cli.py** 🔄 → arg_parser + Processing Layer (needs major rewiring)
4. **ui_components.py** (CREATE) → cli.py + Infrastructure logging

### Build Order
1. ✅ cli_config.py (complete - already refactored for QC)
2. 🔨 **arg_parser.py** (CREATE - clean argument handling)
3. 🔄 **cli.py** (MAJOR REWIRING from entity pipeline to QC pipeline)
4. 🔨 **ui_components.py** (CREATE - user experience components)

### Major Rewiring Needed
- **cli.py**: Remove all entity extraction pipeline calls
- Replace with QC Core + Processing Layer integration
- Update command structure for QC workflows
- Change output handling for theme hierarchies instead of entities

---

## 📊 Module 6: Output Layer
**Status**: 🚧 **NEEDS CREATION** - Basic export patterns exist but minimal

### Internal Component Map
```
┌─────────────────────────────────────────────────────────────┐
│                     OUTPUT LAYER                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Data Formatters (FOUNDATION)                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  data_formatters.py (CREATE)                       │   │
│  │  ├── Theme hierarchy to structured data             │   │
│  │  ├── JSON serialization with metadata              │   │
│  │  ├── CSV flattening for analysis tools             │   │
│  │  ├── Table formatting for display                  │   │
│  │  └── Quote extraction and formatting               │   │
│  │  (DEPENDS: QC Core models)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Report Generation (CORE)                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  report_generator.py (CREATE)                      │   │
│  │  ├── Markdown report templates                     │   │
│  │  ├── Executive summary generation                  │   │
│  │  ├── Theme analysis sections                       │   │
│  │  ├── Supporting quotes and evidence                │   │
│  │  ├── Methodology documentation                     │   │
│  │  └── Appendix with raw data                        │   │
│  │  (DEPENDS: data_formatters, QC Core)               │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Specialized Outputs (FEATURES)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  policy_brief_generator.py (CREATE)                │   │
│  │  ├── Policy-focused theme analysis                 │   │
│  │  ├── Actionable recommendations                    │   │
│  │  ├── Evidence-based conclusions                    │   │
│  │  ├── Stakeholder-appropriate language              │   │
│  │  └── Implementation guidance                       │   │
│  │                                                     │   │
│  │  contradiction_detector.py (CREATE)                │   │
│  │  ├── Cross-interview theme comparison              │   │
│  │  ├── Conflicting code identification               │   │
│  │  ├── Tension and paradox highlighting              │   │
│  │  └── Nuanced interpretation guidance               │   │
│  │  (BOTH DEPEND: QC Core theme_analyzer)             │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                       │
│                    ▼                                       │
│  Export & Integration (OUTPUT)                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  export_manager.py (CREATE)                        │   │
│  │  ├── Multi-format export coordination              │   │
│  │  ├── File organization and naming                  │   │
│  │  ├── Batch export for multiple interviews          │   │
│  │  ├── Progress tracking for large exports           │   │
│  │  └── Quality validation of outputs                 │   │
│  │  (DEPENDS: all other output components)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Internal Dependencies
1. **data_formatters.py** (CREATE) → QC Core models
2. **report_generator.py** (CREATE) → data_formatters + QC Core
3. **policy_brief_generator.py** (CREATE) → QC Core theme_analyzer
4. **contradiction_detector.py** (CREATE) → QC Core theme_analyzer
5. **export_manager.py** (CREATE) → All other output components

### Build Order
1. 🔨 **data_formatters.py** (CREATE - foundation for all outputs)
2. 🔨 **report_generator.py** (CREATE - core markdown reports)
3. 🔨 **policy_brief_generator.py** (CREATE - QC config setting enabled)
4. 🔨 **contradiction_detector.py** (CREATE - QC config setting enabled)
5. 🔨 **export_manager.py** (CREATE - orchestration and batch export)

### All Components Need Creation
This is the most "greenfield" module - we have excellent patterns from LESSONS_LEARNED.md but need to build everything from scratch, adapted for qualitative coding instead of entity extraction.

---

## 🎯 Cross-Module Integration Points

### Critical Integration Dependencies
```
CLI (Module 5) → Processing (Module 4) → QC Core (Module 3) → LLM Integration (Module 2) → Infrastructure (Module 1)
                    ↓                                                ↓
Output (Module 6) ← Results Aggregation ← Theme Hierarchies ← Response Parsing ← Utilities
```

### Build Priority Matrix
| Module | Status | Priority | Dependencies | Blockers |
|--------|--------|----------|-------------|----------|
| 1. Infrastructure | ✅ Complete | N/A | None | None |
| 2. LLM Integration | ✅ Exists | High | Module 1 | Need response_parser.py |
| 3. QC Core | ✅ Exists | High | Modules 1,2 | Need qc_models.py |
| 4. Processing | 🔄 Adapt | Critical | Modules 1,2,3 | Major rewiring needed |
| 5. Interface | 🔄 Rewire | Critical | Module 4 | CLI pipeline rewiring |
| 6. Output | 🚧 Create | Medium | Module 3 | Can start simple |

### Next Steps
1. **Create missing foundation components** (qc_models.py, response_parser.py)
2. **Adapt existing components** (parallel_batch_processor.py, cli.py) 
3. **Build new components** (interview_parser.py, report_generator.py)
4. **Integration testing** across module boundaries

This detailed internal mapping shows exactly what needs to be built, adapted, or integrated within each module to create a working qualitative coding system.