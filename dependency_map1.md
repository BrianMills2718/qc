# Qualitative Coding System - Dependency Map v1

## Overview

This dependency map shows the modular architecture for the qualitative coding system, based on preserved components from the cleanup process and lessons learned from the previous implementation.

---

## 🏗️ Module Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                    │
├─────────────────────────────────────────────────────────────┤
│  CLI Module          │  Configuration Module               │
│  - cli.py            │  - cli_config.py                   │
│  - argument parsing  │  - environment validation          │
│  - user interaction  │  - settings management             │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                         │
├─────────────────────────────────────────────────────────────┤
│  Batch Processing    │  Workflow Manager                   │
│  - parallel_batch_   │  - interview sequencing            │
│    processor.py      │  - progress tracking               │
│  - rate limiting     │  - error recovery                  │
│  - concurrency       │  - state management                │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 QUALITATIVE CODING CORE                     │
├─────────────────────────────────────────────────────────────┤
│  QC Engine           │  Theme Management                   │
│  - qualitative_      │  - hierarchy creation              │
│    coding_extractor  │  - code evolution                  │
│  - theme extraction  │  - analytical memos                │
│  - code hierarchy    │  - saturation tracking             │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM INTEGRATION LAYER                    │
├─────────────────────────────────────────────────────────────┤
│  Universal Client    │  Provider Adapters                  │
│  - llm_client.py     │  - simple_gemini_client.py         │
│  - fallback chains   │  - response parsing                │
│  - retry logic       │  - token optimization              │
│  - error handling    │  - rate limiting                   │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                      │
├─────────────────────────────────────────────────────────────┤
│  Core Utilities      │  Security & Observability          │
│  - config_manager    │  - input_validator.py              │
│  - robust_error_     │  - structured_logger.py            │
│    handling         │  - SecretStr patterns               │
│  - llm_content_      │  - correlation tracking            │
│    extractor        │  - JSON logging                     │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     OUTPUT LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  Report Generation   │  Export & Visualization            │
│  - markdown export   │  - CSV generation                  │
│  - policy briefs     │  - JSON export                     │
│  - analytical memos  │  - theme visualizations            │
│  - contradiction     │  - progress reports                │
│    detection        │                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Dependency Details

### 1. Infrastructure Layer (Foundation)
**Status**: ✅ **PRESERVED** - Production-ready utilities from cleanup

**Components**:
- `utils/config_manager.py` - SecretStr, environment validation
- `utils/robust_error_handling.py` - Error classification, retry logic
- `utils/structured_logger.py` - JSON logging, correlation tracking
- `utils/input_validator.py` - Security, sanitization, injection protection
- `utils/llm_content_extractor.py` - Universal LLM response parsing

**Dependencies**: None (foundation layer)
**Dependents**: All other modules

**Build Priority**: ✅ Complete (already exists)

---

### 2. LLM Integration Layer
**Status**: ✅ **PRESERVED** - Universal client patterns from cleanup

**Components**:
- `qc/core/llm_client.py` - Universal LLM client with fallback chains
- `qc/core/simple_gemini_client.py` - Gemini 2.5 Flash integration
- Response format handling and standardization
- Token optimization and rate limiting

**Dependencies**:
- Infrastructure Layer (error handling, logging, content extraction)

**Dependents**:
- Qualitative Coding Core
- Processing Layer

**Build Priority**: ✅ Complete (needs integration testing)

---

### 3. Qualitative Coding Core
**Status**: ✅ **PRESERVED** - True QC implementation exists

**Components**:
- `qc/core/qualitative_coding_extractor.py` - ACTUAL qualitative coding
- Theme hierarchy creation (themes → categories → codes)
- Analytical memo generation and linking
- Grounded theory development patterns
- Code saturation tracking

**Dependencies**:
- Infrastructure Layer (error handling, logging)
- LLM Integration Layer (for extraction calls)

**Dependents**:
- Processing Layer (batch operations)
- Output Layer (report generation)

**Build Priority**: 🔨 **NEEDS INTEGRATION** (core exists, needs wiring)

---

### 4. Processing Layer
**Status**: 🔄 **NEEDS ADAPTATION** - Patterns exist but entity-focused

**Components**:
- `qc/core/parallel_batch_processor.py` - Concurrent interview processing (ADAPT)
- Interview document parsing and preparation
- Workflow orchestration and state management
- Progress tracking and resume capability
- Error recovery and partial result handling

**Dependencies**:
- Infrastructure Layer (error handling, logging)
- LLM Integration Layer (for API calls)
- Qualitative Coding Core (for extraction logic)

**Dependents**:
- User Interface Layer (CLI integration)
- Output Layer (result aggregation)

**Build Priority**: 🔨 **HIGH** - Critical for batch interview processing

---

### 5. Configuration & Interface Layer
**Status**: 🔄 **NEEDS REFACTORING** - CLI exists but wired to entity extraction

**Components**:
- `utils/cli_config.py` - Configuration management (REFACTORED ✅)
- `qc/cli.py` - Command-line interface (NEEDS REWIRING)
- Argument parsing and validation
- User interaction and feedback
- Session management

**Dependencies**:
- Infrastructure Layer (config management, validation)
- Processing Layer (workflow execution)

**Dependents**: None (top-level interface)

**Build Priority**: 🔨 **HIGH** - Entry point for users

---

### 6. Output Layer
**Status**: 🚧 **NEEDS CREATION** - Export patterns exist but minimal

**Components**:
- Markdown report generation
- Policy brief creation (QC-specific settings enabled)
- Contradiction detection across interviews
- CSV export for analysis
- JSON export for integration
- Progress and summary reports

**Dependencies**:
- Infrastructure Layer (content formatting, file operations)
- Qualitative Coding Core (theme data structures)
- Processing Layer (aggregated results)

**Dependents**: None (output layer)

**Build Priority**: 🔨 **MEDIUM** - Can use basic exports initially

---

## 🔗 Critical Dependency Chains

### Primary Workflow Chain
```
CLI → Configuration → Processing → QC Core → LLM Integration → Infrastructure
 ↓                                                                    ↑
Output ← Results ← Batch Processing ← Theme Extraction ← API Calls ← Utilities
```

### Error Handling Chain
```
Infrastructure (Error Classification) → LLM Integration (Retry Logic) → 
QC Core (Graceful Degradation) → Processing (Recovery) → CLI (User Feedback)
```

### Data Flow Chain
```
User Input → CLI Config → Batch Processor → Interview Parser → 
QC Extractor → LLM Client → Response Parser → Theme Hierarchy → 
Report Generator → Output Files
```

---

## 🚨 Critical Integration Points

### 1. CLI → Processing Integration
**Current Issue**: CLI wired to entity extraction pipeline
**Solution Required**: Rewire to use QC extractor instead
**Impact**: High - Entry point for all operations

### 2. Batch Processing → QC Core Integration
**Current Issue**: Parallel processor optimized for entity extraction
**Solution Required**: Adapt for theme extraction workflows
**Impact**: High - Core functionality for interview processing

### 3. QC Core → Output Integration
**Current Issue**: No integration between QC extractor and report generation
**Solution Required**: Create output adapters for theme hierarchies
**Impact**: Medium - Can start with basic JSON export

---

## 📋 Build Sequence Recommendation

### Phase 1: Foundation (Week 1)
1. ✅ Validate Infrastructure Layer (already complete)
2. ✅ Test LLM Integration Layer (already exists)
3. 🔨 Create basic integration tests

### Phase 2: Core Integration (Week 2)
1. 🔨 Wire QC Core to LLM Integration
2. 🔨 Adapt Batch Processing for QC workflows
3. 🔨 Create basic CLI integration with QC pipeline

### Phase 3: User Interface (Week 3)
1. 🔨 Rewire CLI from entity extraction to QC
2. 🔨 Implement proper configuration handling
3. 🔨 Add progress tracking and user feedback

### Phase 4: Output & Polish (Week 4)
1. 🔨 Create report generation system
2. 🔨 Implement policy brief generation
3. 🔨 Add contradiction detection
4. 🔨 Create comprehensive testing

---

## 🎯 Success Criteria

### Module Completeness
- [ ] All modules have clear interfaces and boundaries
- [ ] Dependencies are explicit and minimal
- [ ] Each module can be tested independently
- [ ] Error handling is consistent across modules

### Integration Quality
- [ ] CLI successfully processes interview batches
- [ ] QC Core generates proper theme hierarchies
- [ ] Output Layer produces readable reports
- [ ] Error recovery works across module boundaries

### Production Readiness
- [ ] Comprehensive logging and observability
- [ ] Security validation for all user inputs
- [ ] Performance monitoring and optimization
- [ ] Comprehensive test coverage

---

## 📚 Implementation Notes

### Preserved Assets (High Value)
- **Infrastructure utilities**: Production-grade security, logging, error handling
- **LLM client patterns**: Universal client with fallback chains
- **QC core implementation**: True qualitative coding with themes/categories/codes
- **Batch processing patterns**: Concurrency, rate limiting, error recovery

### Archived Components (Entity Extraction)
- Neo4j integration and graph database components
- Entity extraction pipeline and relationship discovery
- Cypher query builder and natural language query system
- Entity-focused analysis and frequency analysis

### Critical Missing Pieces
- Integration between QC core and batch processing
- CLI rewiring from entity pipeline to QC pipeline
- Output generation for theme hierarchies
- Comprehensive testing for QC workflows

---

*This dependency map provides the foundation for systematic development of the qualitative coding system using preserved high-quality components while avoiding the architectural misalignment of the previous entity extraction system.*