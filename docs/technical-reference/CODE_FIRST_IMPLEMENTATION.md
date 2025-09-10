# Code-First Extraction Implementation Guide

## Overview

This document describes the complete implementation of the **4-Phase Code-First Extraction Pipeline** for qualitative coding. The system transforms interview data through intelligent schema discovery and application, producing hierarchical codes, speaker-attributed quotes, and entity/relationship networks.

## Architecture

### 4-Phase Extraction Pipeline

```
Phase 0: Schema Parsing (Optional)
  ├── Parse user-provided code definitions
  ├── Parse speaker property schemas  
  └── Parse entity/relationship types

Phase 1: Code Taxonomy Discovery (1 LLM call with ALL interviews)
  ├── Concatenate all interviews (up to 1M tokens)
  ├── Discover hierarchical code structure
  └── Output: taxonomy.json

Phase 2: Speaker Schema Discovery (1 LLM call with ALL interviews)
  ├── Identify speaker properties to track
  ├── Determine property types and values
  └── Output: speaker_schema.json

Phase 3: Entity/Relationship Schema Discovery (1 LLM call with ALL interviews)
  ├── Discover entity types
  ├── Identify relationship patterns
  └── Output: entity_schema.json

Phase 4: Per-Interview Application (1 LLM call per interview)
  ├── Apply all schemas to extract quotes
  ├── Link quotes to codes (many-to-many)
  ├── Identify speakers with properties
  ├── Extract entities/relationships at 3 levels
  └── Output: One JSON per interview + Neo4j import
```

## System Architecture

### Enhanced LLM Integration

The system uses **Universal LLM Kit** integration for reliable, cost-effective language model operations:

**Current Capabilities**:
- **Smart Model Routing**: Automatically selects optimal models based on content characteristics and complexity
- **Multi-Provider Support**: Seamless integration with Gemini, Claude, OpenAI, and other providers via LiteLLM
- **Automatic Fallbacks**: Prevents single-point-of-failure with intelligent model fallback chains
- **Cost Optimization**: Routes content to cost-effective models while maintaining quality
- **Structured Output**: Full support for Pydantic schema-based extraction

**Implementation Details**:
- `UniversalModelClient` with LiteLLM integration provides provider abstraction
- Intelligent error handling and retry mechanisms
- Configuration-driven model selection and routing
- Built-in timeout and rate limit management

### Web Interface & API

The system includes a **FastAPI-based web interface** for interactive result exploration:

**Current Features**:
- **REST API**: Complete endpoint suite for analysis, status tracking, and querying
- **Interactive Documentation**: Swagger UI at `/docs` with live API testing
- **Result Browser**: Web interface for exploring quotes, codes, entities, and relationships
- **Confidence Visualization**: Display of extraction confidence scores and evidence
- **Real-time Status**: Job tracking and progress monitoring

**API Endpoints**:
- `POST /analyze` - Start interview analysis
- `GET /jobs/{job_id}` - Analysis status and results
- `GET /query` - Database queries and filtering
- `GET /health` - System health and diagnostics

**Usage**:
```bash
# Start web interface
python -m qc.cli serve --host 0.0.0.0 --port 8000

# Access interactive docs
open http://localhost:8000/docs
```

## Key Features

### 1. Configurable Extraction Approaches

Each phase supports three approaches:

- **Open**: Discover schemas from data based on analytic question
- **Closed**: Use predefined schemas only (skip discovery phases)
- **Mixed**: Start with predefined, discover additional patterns

### 2. No Max Token Limits

The system uses the full context window (1M tokens for Gemini 1.5 Pro):
- Phase 1-3: All interviews concatenated in single LLM call
- Phase 4: Full interview context per call
- No artificial token limits that would truncate data

### 3. Flexible Schema Definition

For closed/mixed approaches, users provide schemas in plain text/DOCX:
- System uses LLM to parse informal definitions
- No need for technical JSON/YAML formatting
- Supports hierarchical codes naturally

### 4. Many-to-Many Relationships

- Single quote can support multiple codes
- Codes can have multiple supporting quotes
- Entities can relate to multiple codes
- Flexible relationship networks

## File Structure

```
qualitative_coding/
├── src/
│   └── qc/
│       ├── extraction/
│       │   ├── code_first_schemas.py      # All Pydantic models
│       │   ├── schema_parser.py           # Phase 0 implementation
│       │   └── code_first_extractor.py    # Main pipeline orchestrator
│       └── llm/
│           └── llm_handler.py             # LLM interface (no max_tokens)
├── config/
│   ├── extraction_config.yaml             # Main configuration
│   ├── extraction_config_example.yaml     # Example configuration
│   └── schemas/                           # User-provided schemas
│       ├── example_codes.txt
│       ├── example_speaker_properties.txt
│       └── example_entity_relationships.txt
├── run_code_first_extraction.py           # CLI script
└── test_code_first_extraction.py          # Test suite
```

## Configuration

### Basic Configuration (Open Approach)

```yaml
# config/extraction_config.yaml
analytic_question: "What are the key themes in AI adoption?"
interview_files:
  - "data/interviews/interview_001.docx"
  - "data/interviews/interview_002.txt"
coding_approach: "open"
speaker_approach: "open"  
entity_approach: "open"
output_dir: "output/extraction_results"
auto_import_neo4j: true
llm_model: "gemini-1.5-pro"
temperature: 0.1
```

### Closed/Mixed Configuration

```yaml
coding_approach: "mixed"
predefined_codes_file: "config/schemas/initial_codes.txt"
speaker_approach: "closed"
predefined_speaker_schema_file: "config/schemas/speaker_props.docx"
entity_approach: "open"  # Can mix approaches
```

## Usage

### 1. Basic Extraction

```bash
# Run with default config
python run_code_first_extraction.py

# Run with specific config
python run_code_first_extraction.py config/my_config.yaml

# Dry run to validate configuration
python run_code_first_extraction.py --dry-run
```

### 2. Providing Schemas (Closed/Mixed)

Create informal text files with your schemas:

**codes.txt:**
```
Technical Challenges
Description: Issues with AI implementation
Examples: "Integration was complex", "Data quality problems"

  Data Quality (child of Technical Challenges)
  Description: Problems with data preparation
  Examples: "Spent months cleaning data"
```

**speaker_properties.txt:**
```
Role: The person's job title (required)
Organization: Their company (required)
Seniority: Junior/Mid/Senior (optional)
AI Experience: Novice/Expert (optional)
```

### 3. Output Structure

```
output/
├── taxonomy.json                    # Phase 1: Code hierarchy
├── speaker_schema.json              # Phase 2: Speaker properties
├── entity_schema.json               # Phase 3: Entity/relationship types
├── interviews/
│   ├── interview_001.json          # Coded interview with quotes
│   ├── interview_002.json
│   └── ...
└── extraction_results.json         # Complete aggregated results
```

## Data Architecture

### Quote-Centric Data Model

The system implements a **quote-centric architecture** where quotes are first-class entities, not properties of other entities. This design enables complex queries across quotes, speakers, and themes while providing stable references for analysis.

**Core Architectural Principles**:
- **Quotes as First-Class Entities**: Neo4j Quote nodes with unique IDs and comprehensive properties
- **Line-Based Location Tracking**: Uses line numbers (`line_start`, `line_end`, `sequence_position`) for stable references
- **Multi-Dimensional Relationships**: Quotes connect to multiple entity types via direct relationships
- **Speaker Attribution System**: Track speaker identity at quote level for dialogue analysis
- **Thematic Connection Network**: Model how ideas connect across speakers in conversations

### Neo4j Schema Implementation

**Node Types**:
- **Quote**: Primary entity with properties: `id`, `text`, `line_start`, `line_end`, `sequence_position`, `interview_id`, `speaker_name`
- **Code**: Hierarchical code structure with parent/child relationships
- **Speaker**: Speaker information with dynamic properties based on schema
- **Interview**: Interview metadata and context
- **Entity**: Domain-specific entities discovered during extraction

**Relationship Types**:
- **SUPPORTS**: Quote → Code (many-to-many code assignment)
- **SPOKEN_BY**: Quote → Speaker (speaker attribution)
- **FROM_INTERVIEW**: Quote → Interview (source tracking)
- **THEMATIC_CONNECTION**: Quote → Quote (dialogue flow and idea connections)
- **PARENT_OF**: Code → Code (hierarchical structure)
- **MENTIONS**: Quote → Entity (entity references)

## Data Models

### Code Hierarchy
```python
HierarchicalCode:
  - id: Unique identifier
  - name: Code name
  - description: What it represents
  - parent_id: For hierarchy
  - level: Depth in hierarchy
  - example_quotes: From discovery
```

### Enhanced Quote
```python
EnhancedQuote:
  - text: Exact quote
  - context_summary: Variable-length explanation
  - code_ids: Multiple codes (many-to-many)
  - speaker: Embedded speaker info with properties
  - line_start/end: Provenance
  - quote_entities: Entities in quote
  - quote_relationships: Relations in quote
```

### Speaker Information
```python
SpeakerInfo:
  - name: Identified speaker
  - confidence: ID confidence
  - properties: Dynamic based on schema
    - role: "CTO"
    - organization: "TechCorp"
    - seniority: "Senior"
    - [any discovered/defined properties]
```

## Testing

Run the test suite to verify installation:

```bash
python test_code_first_extraction.py
```

Tests verify:
1. Configuration loading
2. File reading (DOCX/TXT)
3. Schema parsing
4. LLM handler setup
5. No max_tokens limits

### Graph Query Examples

The quote-centric architecture enables powerful analytical queries:

**Finding Code Relationships**:
```cypher
// Find quotes that support multiple related codes
MATCH (q:Quote)-[:SUPPORTS]->(c:Code)
WHERE c.name CONTAINS "AI"
RETURN q.text, collect(c.name) as codes
```

**Dialogue Analysis**:
```cypher
// Trace thematic connections across speakers
MATCH (q1:Quote)-[:THEMATIC_CONNECTION]->(q2:Quote)
RETURN q1.speaker_name, q1.text, q2.speaker_name, q2.text
```

**Speaker Pattern Analysis**:
```cypher
// Analyze speaker contributions by code
MATCH (s:Speaker)<-[:SPOKEN_BY]-(q:Quote)-[:SUPPORTS]->(c:Code)
RETURN s.name, c.name, count(q) as quote_count
ORDER BY quote_count DESC
```

## Neo4j Integration

When `auto_import_neo4j: true`, the system creates a comprehensive graph database with the quote-centric schema described above. The implementation provides:

### Performance Considerations
- **Indexes**: Line-based and interview-based indexes for efficient queries
- **Direct Relationships**: Avoid expensive joins through direct quote relationships
- **Scalability**: First-class Quote nodes support large interview datasets
- **Query Optimization**: Graph structure optimized for typical qualitative coding queries

### Advanced Analysis Capabilities
- **Cross-Interview Analysis**: Compare themes and patterns across multiple interviews
- **Temporal Analysis**: Track idea development using sequence positions and line numbers
- **Speaker Network Analysis**: Understand how ideas flow between speakers
- **Thematic Clustering**: Identify related concepts through connection networks

## Advanced Features

### 1. Context Summaries
Each quote includes a variable-length context summary that explains the surrounding discussion. Length adapts to complexity - no fixed limits.

### 2. Confidence Scores
Every extraction includes confidence scores:
- Speaker identification confidence
- Code assignment confidence
- Entity extraction confidence
- Overall extraction confidence

### 3. Three-Level Entity Extraction
- **Quote-level**: Entities within specific quotes
- **Interview-level**: Entities across whole interview
- **Global-level**: Cross-interview entity network

### 4. Flexible Speaker Detection
LLM uses all available clues:
- Explicit labels ("Interviewer:", "Participant 1:")
- Document headers ("Interview with [Name]")
- Conversational context
- Meeting notes format

## Troubleshooting

### Issue: Configuration validation fails
**Solution**: Check that all interview files exist and schema files (if specified) are present.

### Issue: LLM calls timing out
**Solution**: Large Phase 1-3 calls may take several minutes. Ensure stable connection.

### Issue: Neo4j import fails
**Solution**: Ensure Neo4j is running (`docker-compose up -d`) and accessible on port 7687.

### Issue: Memory errors with large interview sets
**Solution**: Process in batches or increase system memory. The 1M token window requires significant RAM.

## Performance Considerations

### Token Usage
- Phase 1-3: Each uses full concatenated text (~1M tokens per call)
- Phase 4: One call per interview (~10-50K tokens each)
- Total: ~3M tokens baseline + (interviews × average_size)

### Processing Time
- Phase 1-3: 1-3 minutes each for discovery
- Phase 4: 30-60 seconds per interview
- Total: ~10-30 minutes for 10 interviews

### Optimization Tips
1. Use closed approach to skip discovery phases
2. Process interviews in parallel (if API supports)
3. Cache Phase 1-3 results for re-use
4. Use lower temperature (0.1) for consistency

## Enhancement Roadmap

### Planned LLM Improvements
**Multi-Model Consensus System** (Phase 2-3):
- Multi-model validation for quality assurance
- Consensus scoring and confidence metrics  
- Selective validation for complex/problematic content
- Automated quality gates and error recovery
- Production monitoring and cost optimization

### Planned UI Enhancements
**Advanced Web Interface Features**:
- **Real-time Updates**: WebSocket integration for live analysis progress
- **Multi-Model Consensus View**: Side-by-side model comparison with confidence scores
- **Interactive Visualizations**: Code hierarchies, theory evolution timelines
- **Theory Development Tools**: Drag-and-drop code organization, iteration scrubbing
- **Multi-User Support**: Authentication, project management, collaboration

**Alternative UI Options**:
- **Streamlit Interface**: Research-friendly rapid prototyping interface
- **React Application**: Production multi-user interface with advanced visualizations
- **Jupyter Integration**: Notebook-based interactive analysis and exploration

## Next Steps

1. **Update Configuration**: Edit `config/extraction_config.yaml` with your files
2. **Prepare Interviews**: Ensure DOCX/TXT files are accessible
3. **Define Schemas** (Optional): Create schema files for closed/mixed approach
4. **Run Extraction**: `python run_code_first_extraction.py`
5. **Explore Results**: Review JSON outputs, query Neo4j, or use web interface at `/docs`
6. **Iterate**: Refine analytic question and schemas based on results

## Support

For issues or questions:
1. Check test suite: `python test_code_first_extraction.py`
2. Review logs in `logs/` directory
3. Validate configuration: `python run_code_first_extraction.py --dry-run`
4. Consult example schemas in `config/schemas/`