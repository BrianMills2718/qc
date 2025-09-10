# Clean Qualitative Coding System - Functional Specification

## Overview
Simplified GT analysis system focused on practical research functionality, extracted from 25K+ line academic system down to ~4K lines of essential functionality.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLEAN GT ANALYSIS SYSTEM                     │
└─────────────────────────────────────────────────────────────────┘

INPUT LAYER
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Interview Files   │    │  Configuration      │    │  User Commands      │
│                     │    │                     │    │                     │
│ • .txt files        │    │ • gt_config.yaml    │    │ • analyze           │
│ • .md files         │    │ • methodology.yaml  │    │ • report            │
│ • Directory input   │    │ • llm_settings.yaml │    │ • export            │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CLI INTERFACE                               │
│                                                                 │
│  python cli.py analyze --input data/interviews --output reports│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                GROUNDED THEORY WORKFLOW                         │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   PHASE 1   │  │   PHASE 2   │  │   PHASE 3   │  │   PHASE 4   │ │
│  │             │  │             │  │             │  │             │ │
│  │    OPEN     │─▶│    AXIAL    │─▶│  SELECTIVE  │─▶│ THEORETICAL │ │
│  │   CODING    │  │   CODING    │  │   CODING    │  │INTEGRATION  │ │
│  │             │  │             │  │             │  │             │ │
│  │• Concepts   │  │• Relations  │  │• Core Cat   │  │• Model      │ │
│  │• Properties │  │• Conditions │  │• Integration│  │• Framework  │ │
│  │• Dimensions │  │• Actions    │  │• Validation │  │• Theory     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATA PROCESSING                               │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │    LLM      │    │  STORAGE    │    │    VALIDATION       │  │
│  │ HANDLER     │    │             │    │                     │  │
│  │             │    │ • Neo4j     │    │ • Confidence Check  │  │
│  │• Prompts    │◀──▶│ • Codes     │◀──▶│ • Completeness     │  │
│  │• Analysis   │    │ • Relations │    │ • Basic Quality     │  │
│  │• Confidence │    │ • Hierarchy │    │ • Error Handling    │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
OUTPUT LAYER
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   GT REPORTS        │    │   DATA EXPORTS      │    │   ANALYSIS FILES    │
│                     │    │                     │    │                     │
│ • Academic Report   │    │ • JSON (raw data)   │    │ • Codes.json        │
│ • Executive Summary │    │ • CSV (for Excel)   │    │ • Hierarchy.json    │
│ • Methodology Notes │    │ • Neo4j backup      │    │ • Relationships.json│
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘

```

## Core Functionality Matrix

| Feature | Description | Essential? | Complexity | Lines |
|---------|-------------|------------|------------|-------|
| **CLI Interface** | Single `analyze` command | ✅ Yes | Low | 200 |
| **GT 4-Phase Workflow** | Complete methodology | ✅ Yes | High | 897 |
| **Hierarchical Codes** | Parent/child structure | ✅ Yes | Medium | included |
| **Multiple Core Categories** | GT requirement | ✅ Yes | Medium | included |
| **LLM Integration** | Clean LLM handling | ✅ Yes | Medium | 280 |
| **Neo4j Storage** | Essential data ops | ✅ Yes | Medium | 300 |
| **Report Generation** | 3 report types | ✅ Yes | Medium | 400 |
| **Configuration System** | GT parameters | ✅ Yes | Low | 190 |
| **Error Handling** | Basic robustness | ✅ Yes | Low | 150 |
| **Token Management** | LLM efficiency | ✅ Yes | Low | 200 |

## Data Flow Diagram

```
Interview Files (.txt/.md)
         │
         ▼
┌─────────────────────┐
│   File Loader       │ ──── Validates: encoding, format, content
│   • Read files      │
│   • Parse content   │
│   • Validate format │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Configuration      │ ──── Loads: methodology, LLM, storage params
│  • Load GT config   │
│  • Set parameters   │
│  • Initialize LLM   │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ PHASE 1: Open Code  │ ──── LLM Analysis: concepts, properties, dimensions
│ • Identify concepts │
│ • Extract properties│
│ • Quote support     │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ PHASE 2: Axial     │ ──── LLM Analysis: relationships, conditions, consequences
│ • Find relations   │
│ • Identify context │
│ • Build network    │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ PHASE 3: Selective │ ──── LLM Analysis: core category, integration
│ • Core category    │
│ • Integration      │
│ • Validation       │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ PHASE 4: Theory    │ ──── LLM Analysis: theoretical model, framework
│ • Build model      │
│ • Generate theory  │
│ • Create memos     │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   Neo4j Storage    │ ──── Stores: codes, relationships, hierarchy, quotes
│ • Save codes       │
│ • Store hierarchy  │
│ • Index relations  │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Report Generator  │ ──── Produces: academic, executive, raw data
│ • Academic report  │
│ • Executive summary│
│ • Raw data export  │
└─────────────────────┘
```

## Data Schemas

### Core Data Structures

#### OpenCode Schema
```json
{
  "code_name": "string",
  "description": "string", 
  "properties": ["string"],
  "dimensions": ["string"],
  "supporting_quotes": ["string"],
  "frequency": "integer",
  "confidence": "float (0-1)",
  "parent_id": "string|null",
  "level": "integer (0=top-level)",
  "child_codes": ["string"]
}
```

#### AxialRelationship Schema
```json
{
  "central_category": "string",
  "related_category": "string", 
  "relationship_type": "string",
  "conditions": ["string"],
  "consequences": ["string"],
  "supporting_evidence": ["string"],
  "strength": "float (0-1)"
}
```

#### CoreCategory Schema
```json
{
  "category_name": "string",
  "definition": "string",
  "central_phenomenon": "string",
  "related_categories": ["string"],
  "theoretical_properties": ["string"],
  "explanatory_power": "string",
  "integration_rationale": "string"
}
```

#### TheoreticalModel Schema
```json
{
  "model_name": "string",
  "core_category": "string",
  "theoretical_framework": "string",
  "propositions": ["string"],
  "conceptual_relationships": ["string"],
  "scope_conditions": ["string"],
  "implications": ["string"],
  "future_research": ["string"]
}
```

## Configuration Parameters

### GT Methodology Configuration (`gt_config.yaml`)
```yaml
grounded_theory:
  # Core methodology parameters
  theoretical_sensitivity: "moderate"  # low, moderate, high
  coding_depth: "comprehensive"       # basic, standard, comprehensive
  validation_level: "standard"       # minimal, standard, rigorous
  
  # Analysis behavior
  minimum_code_frequency: 2
  confidence_threshold: 0.7
  enable_hierarchical_codes: true
  max_hierarchy_levels: 3
  allow_multiple_core_categories: true
  
  # Quality controls
  require_quote_support: true
  minimum_quotes_per_code: 1
  enable_theoretical_memos: true
```

### LLM Configuration (`llm_config.yaml`)  
```yaml
llm:
  # Model settings
  model: "gpt-4"
  temperature: 0.1
  max_tokens: 4000
  
  # Retry and reliability
  max_retries: 3
  timeout_seconds: 60
  retry_backoff: true
  
  # Token management
  chunk_size: 3000
  overlap_tokens: 200
  enable_caching: true
```

### Storage Configuration (`storage_config.yaml`)
```yaml
storage:
  neo4j:
    uri: "bolt://localhost:7687" 
    database: "qualitative_coding"
    
  # Backup settings
  auto_backup: true
  backup_frequency: "daily"
  retention_days: 30
```

## Command Interface

### Primary Commands
```bash
# Basic GT analysis
python cli.py analyze --input data/interviews/ --output reports/

# With custom configuration  
python cli.py analyze --input data/interviews/ --output reports/ --config custom_gt.yaml

# Specific methodology settings
python cli.py analyze --input data/interviews/ --output reports/ \
    --theoretical-sensitivity high \
    --coding-depth comprehensive \
    --enable-hierarchy

# Export formats
python cli.py export --format json --output exports/
python cli.py export --format csv --output exports/
```

### Configuration Options
```bash
# Methodology parameters
--theoretical-sensitivity [low|moderate|high]
--coding-depth [basic|standard|comprehensive]  
--validation-level [minimal|standard|rigorous]

# Analysis behavior
--min-frequency INT
--confidence-threshold FLOAT
--enable-hierarchy / --disable-hierarchy
--max-hierarchy-levels INT
--multiple-core-categories / --single-core-category

# Quality controls  
--require-quotes / --no-require-quotes
--min-quotes-per-code INT
--enable-memos / --disable-memos
```

## Output Files

### Reports Generated
1. **Academic Report** (`academic_report.md`)
   - Full GT methodology documentation
   - Phase-by-phase findings
   - Hierarchical code structure
   - Core category analysis
   - Theoretical model
   - Research implications

2. **Executive Summary** (`executive_summary.md`) 
   - Key findings overview
   - Hierarchical theme visualization
   - Business insights
   - Actionable recommendations

3. **Methodology Documentation** (`methodology_notes.md`)
   - Configuration used
   - Analysis parameters
   - Quality metrics
   - Validation results

### Data Exports
1. **Raw Data** (`raw_data.json`)
   - Complete analysis results
   - All codes with hierarchy
   - Relationships and core categories
   - Theoretical model data

2. **Hierarchy Export** (`code_hierarchy.json`)
   - Tree structure visualization
   - Parent-child relationships
   - Level indicators
   - Frequency data

3. **Neo4j Backup** (`analysis_backup.cypher`)
   - Complete graph export
   - Recreatable database state
   - All relationships preserved

## Quality Assurance

### Built-in Validation
- **Confidence Thresholds**: Filter low-confidence results
- **Completeness Checks**: Ensure all phases completed
- **Hierarchy Validation**: Check parent-child consistency
- **Quote Support**: Verify evidence backing
- **Error Recovery**: Graceful failure handling

### Success Metrics
- Analysis completion rate: >95%
- Code confidence average: >0.7
- Hierarchy completeness: >80%
- Report generation: 100%
- Processing time: <30min for 10 interviews

## Performance Characteristics

### Processing Times (Estimated)
- Small dataset (3-5 interviews): 5-10 minutes
- Medium dataset (6-15 interviews): 15-25 minutes  
- Large dataset (16-30 interviews): 25-45 minutes

### Resource Requirements
- Memory: <2GB RAM
- Storage: <100MB per analysis
- Network: LLM API calls only
- CPU: Standard modern processor

## Migration from Current System

### Preserved Functionality
✅ Complete 4-phase GT methodology
✅ Hierarchical code structures  
✅ Multiple core categories
✅ Academic report generation
✅ Neo4j data storage
✅ Configuration flexibility

### Removed Complexity
❌ Academic validation bloat (Cohen's Kappa, etc.)
❌ Natural language query systems
❌ Web interface dashboards
❌ QCA analysis subsystem
❌ Multiple competing extractors
❌ Complex validation pipelines

### Result: **83% Code Reduction** with **100% GT Functionality**