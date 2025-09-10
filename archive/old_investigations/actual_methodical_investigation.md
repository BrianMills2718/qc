# Actual Methodical File Investigation - All 86 Files

**Progress**: 10/86 completed
**Current Batch**: Files 11-20

## Investigation Log

### File #1: `src/qc/__init__.py`
- **Lines**: 27
- **Purpose**: Package init file that exposes main components for external use
- **Key imports**: UniversalModelClient, EnhancedNeo4jManager, MultiPassExtractor, CypherQueryBuilder
- **Version**: 2.1.0
- **Functionality**: Makes core classes available when someone does `from qc import ...`

### File #2: `src/qc/analysis/analytical_memos.py`
- **Lines**: 737 (large file)
- **Purpose**: Sophisticated analytical memo generation using LLM
- **Key classes**: AnalyticalMemoGenerator, MemoType enum, ThematicPattern, ResearchInsight, AnalyticalMemo
- **Main functionality**: Generates different types of memos (pattern analysis, theoretical, cross-case analysis), uses LLM for structured insights, handles data preparation and export
- **Dependencies**: Requires LLM handler, uses Pydantic for structured output
- **Assessment**: Very comprehensive system for generating research insights

### File #3: `src/qc/analysis/connection_quality_monitor.py`
- **Lines**: 395
- **Purpose**: Quality monitoring system specifically for thematic connections in focus group processing
- **Key classes**: ConnectionQualityMonitor, ConnectionQualityMetrics, QualityAlert
- **Main functionality**: Analyzes connection quality metrics, provides quality alerts, configurable thresholds
- **Dependencies**: Standard library only (json, dataclasses, datetime)
- **Assessment**: Appears specialized for focus group analysis

### File #4: `src/qc/analysis/cross_interview_analyzer.py`
- **Lines**: 887 (large file)
- **Purpose**: Cross-interview pattern detection and analysis - finds consensus, divergence, and evolution patterns
- **Key classes**: CrossInterviewAnalyzer, ConsensusPattern, DivergencePattern, EvolutionPattern
- **Main functionality**: Analyzes consensus patterns, identifies divergence patterns, tracks temporal evolution
- **Dependencies**: Neo4j manager for data access
- **Assessment**: Sophisticated analysis tool for comparing multiple interviews

### File #5: `src/qc/analysis/discourse_analyzer.py`
- **Lines**: 960 (large file)
- **Purpose**: Advanced discourse analysis for conversational/dialogue analysis
- **Key classes**: DiscourseAnalyzer, DialogicalCooccurrence, TurnTakingPattern, ConversationalSequence
- **Main functionality**: Analyzes thematic code co-occurrence across speaker turns, studies turn-taking dynamics
- **Dependencies**: Uses code-first schemas from extraction module
- **Assessment**: Highly specialized for conversational analysis rather than general qualitative coding

### File #6: `src/qc/analysis/division_insights_analyzer.py`
- **Lines**: 216
- **Purpose**: Analyzes division-specific patterns from frequency data
- **Key classes**: DivisionInsightsAnalyzer with hardcoded division mappings
- **Main functionality**: Maps people to organizational divisions, analyzes patterns by division, loads CSV data
- **Dependencies**: Pandas for data processing
- **Assessment**: Very specific to particular organizational structure (RAND Corp based on names/divisions)

### File #7: `src/qc/analysis/frequency_analyzer.py`
- **Lines**: 269
- **Purpose**: Frequency-based analysis for qualitative coding patterns - basic frequency counting
- **Key classes**: FrequencyAnalyzer, FrequencyChain, FrequencyPattern
- **Main functionality**: Simple scalable frequency counting, extracts code chains, scale-aware configuration
- **Dependencies**: Pandas, error handler, standard collections
- **Assessment**: Focuses on basic frequency analysis rather than advanced statistics

### File #8: `src/qc/analysis/quality_assessment.py`
- **Lines**: 466
- **Purpose**: Quality assessment framework that integrates connection monitoring into main processing pipeline
- **Key classes**: QualityAssessmentFramework
- **Main functionality**: Comprehensive quality assessment, connection quality, code application quality, speaker ID quality
- **Dependencies**: ConnectionQualityMonitor from file #3
- **Assessment**: Integrates multiple quality checks into single framework for focus group processing

### File #9: `src/qc/analysis/real_frequency_analyzer.py`
- **Lines**: 458
- **Purpose**: Real frequency-based analysis that loads actual participant data from JSON files
- **Key classes**: RealFrequencyAnalyzer, RealFrequencyChain, RealFrequencyPattern
- **Main functionality**: Loads JSON interview data, counts actual frequencies vs estimated ones
- **Dependencies**: Pandas, JSON processing, file globbing
- **Assessment**: Name contrasts with frequency_analyzer.py, suggesting that one provides "fake" frequencies

### File #10: `src/qc/analytics/__init__.py`
- **Lines**: 26
- **Purpose**: Package init for quote-based analytics module
- **Key imports**: QuotePatternAnalyzer, ContradictionMapper, QuoteFrequencyAnalyzer, AdvancedQuoteAggregator
- **Main functionality**: Exposes quote-centric analytics classes
- **Assessment**: Package init for analytics focused specifically on quote analysis
