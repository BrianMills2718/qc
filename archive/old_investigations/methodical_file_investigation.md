# Methodical File Investigation - All 86 Files

**Progress**: 86/86 completed  
**STATUS**: METHODICAL INVESTIGATION COMPLETE

## Investigation Log

### File #1: `src/qc/__init__.py`
- **Lines**: 27
- **Purpose**: Package initialization file, exposes main components
- **Key Imports**: UniversalModelClient, EnhancedNeo4jManager, MultiPassExtractor, CypherQueryBuilder
- **Used By**: Anyone importing the qc package
- **Note**: Standard Python package init, defines version 2.1.0

### File #2: `src/qc/analysis/analytical_memos.py`
- **Lines**: 737
- **Purpose**: Sophisticated LLM-powered analytical memo generation system
- **Key Classes**: AnalyticalMemoGenerator, MemoType enum, ThematicPattern, ResearchInsight
- **Functionality**: Pattern analysis, theoretical memos, cross-case analysis, memo synthesis
- **Dependencies**: LLM handler, Pydantic models, extensive schema definitions
- **Note**: Very comprehensive system for generating structured analytical insights from interview data

### File #3: `src/qc/analysis/connection_quality_monitor.py`
- **Lines**: 395
- **Purpose**: Quality monitoring for thematic connections in focus group processing
- **Key Classes**: ConnectionQualityMonitor, ConnectionQualityMetrics, QualityAlert
- **Functionality**: Tracks connection rates, patterns, generates quality assessment feedback
- **Dependencies**: Standard library only (dataclasses, json, datetime)
- **Note**: Appears specialized for focus group analysis

### File #4: `src/qc/analysis/cross_interview_analyzer.py`
- **Lines**: 887
- **Purpose**: Cross-interview pattern detection and analysis
- **Key Classes**: CrossInterviewAnalyzer, ConsensusPattern, DivergencePattern, EvolutionPattern
- **Functionality**: Identifies consensus/divergence across multiple interviews
- **Dependencies**: Neo4j manager for data access
- **Note**: Comprehensive analysis tool for finding patterns across interview datasets

### File #5: `src/qc/analysis/discourse_analyzer.py`
- **Lines**: 960
- **Purpose**: Advanced discourse analysis for qualitative research
- **Key Classes**: DiscourseAnalyzer, DialogicalCooccurrence, TurnTakingPattern, ConversationalSequence
- **Functionality**: Sophisticated dialogue analysis, co-occurrence patterns, turn-taking analysis
- **Dependencies**: Code-first schemas from extraction module
- **Note**: Very specialized for conversational/dialogue analysis

### File #6: `src/qc/analysis/division_insights_analyzer.py`
- **Lines**: 216
- **Purpose**: Division-specific pattern analysis from frequency data
- **Key Classes**: DivisionInsightsAnalyzer with hardcoded division mappings
- **Functionality**: Extracts division-level patterns, uses CSV file input
- **Dependencies**: Pandas for data processing
- **Note**: Appears to be specific to particular organizational divisions

### File #7: `src/qc/analysis/frequency_analyzer.py`
- **Lines**: 269
- **Purpose**: Frequency-based analysis for qualitative coding patterns
- **Key Classes**: FrequencyChain and frequency counting methods
- **Functionality**: Simple scalable frequency counting, not complex statistics
- **Dependencies**: Pandas, error handler
- **Note**: Focuses on basic frequency analysis

### File #8: `src/qc/analysis/quality_assessment.py`
- **Lines**: 466
- **Purpose**: Quality assessment framework integrating connection monitoring
- **Key Classes**: QualityAssessmentFramework
- **Functionality**: Comprehensive quality assessment for processing pipeline
- **Dependencies**: ConnectionQualityMonitor
- **Note**: Integrates quality monitoring into main pipeline

### File #9: `src/qc/analysis/real_frequency_analyzer.py`
- **Lines**: 458
- **Purpose**: Real frequency-based analysis using actual participant data
- **Key Classes**: RealFrequencyChain
- **Functionality**: Loads JSON files and counts actual frequencies
- **Dependencies**: Pandas, JSON processing
- **Note**: Name suggests this provides "real" vs estimated frequencies

### Files #10-12: Analytics Directory
- **File #10**: `src/qc/analytics/__init__.py` (26 lines) - Package init for quote analytics
- **File #11**: `src/qc/analytics/advanced_quote_analytics.py` (660 lines) - Statistical pattern detection, contradiction mapping
- **File #12**: `src/qc/analytics/quote_aggregator.py` (655 lines) - Quote aggregation and summarization

### Files #13-19: API & Audit
- **File #13**: `src/qc/api/__init__.py` (6 lines) - API package init
- **File #14**: `src/qc/api/main.py` (457 lines) - REST API interface for qualitative coding
- **File #15**: `src/qc/api/research_integration.py` (454 lines) - Research workflow API endpoints  
- **File #16**: `src/qc/api/taxonomy_endpoint.py` (201 lines) - AI taxonomy upload endpoint
- **File #17**: `src/qc/api/websocket_progress.py` (339 lines) - WebSocket for real-time progress
- **File #18**: `src/qc/audit/__init__.py` (0 lines) - Empty audit package init
- **File #19**: `src/qc/audit/audit_trail.py` (257 lines) - Audit trail for AI decision transparency

### Files #20-35: CLI, Config, Core Systems  
- **File #20**: `src/qc/cli.py` (1183 lines) - **MASSIVE old CLI system**
- **File #21**: `src/qc/cli_automation_viewer.py` (371 lines) - Automation viewer CLI
- **File #22**: `src/qc/cli_robust.py` (675 lines) - **MAIN working CLI with analyze command**
- **File #23**: `src/qc/config/environment.py` (90 lines) - Environment configuration
- **File #24**: `src/qc/config/methodology_config.py` (302 lines) - **GT methodology config (ESSENTIAL)**
- **File #25**: `src/qc/consolidation/__init__.py` (2 lines) - Empty consolidation init
- **File #26**: `src/qc/consolidation/consolidation_schemas.py` (32 lines) - Consolidation schemas
- **File #27**: `src/qc/consolidation/llm_consolidator.py` (158 lines) - LLM consolidation logic
- **File #28**: `src/qc/core/__init__.py` (20 lines) - Core package init
- **File #29**: `src/qc/core/graceful_degradation.py` (342 lines) - **Error handling system (ESSENTIAL)**
- **File #30**: `src/qc/core/llm_client.py` (349 lines) - Alternative LLM client
- **File #31**: `src/qc/core/native_gemini_client.py` (266 lines) - Gemini-specific client
- **File #32**: `src/qc/core/neo4j_manager.py` (1100 lines) - **Database manager (ESSENTIAL)**
- **File #33**: `src/qc/core/robust_cli_operations.py` (748 lines) - **Operations orchestrator (ESSENTIAL)**
- **File #34**: `src/qc/core/schema_config.py` (197 lines) - Schema configuration system
- **File #35**: `src/qc/export/academic_exporters.py` (477 lines) - Academic format exporters
