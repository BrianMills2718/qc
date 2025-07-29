# System Architecture: Policy-Focused Qualitative Coding

## Overview

An LLM-native global analysis system leveraging Gemini 2.5 Flash's 1M token context window to analyze all 103 interviews simultaneously, with systematic three-phase fallback if needed.

---

## Core Architecture Principles

1. **Global Context Analysis**: All interviews processed simultaneously (2 LLM calls total)
2. **LLM-Native Processing**: Leverage LLM's pattern recognition across entire dataset
3. **Comprehensive Output**: Quote chains, code progressions, stakeholder mapping, contradictions
4. **Research Tool Focus**: Maximize insight quality over enterprise complexity
5. **Systematic Fallback**: Three-phase approach available if global analysis insufficient

---

## Configuration

All settings via `.env` file:

```bash
# Model Configuration
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your-key-here
GEMINI_INPUT_PRICE=0.30    # per 1M tokens
GEMINI_OUTPUT_PRICE=2.50   # per 1M tokens

# Batch Processing
MAX_BATCH_TOKENS=200000    # Conservative limit (configurable)
MAX_CONCURRENT_BATCHES=5   # Parallel processing limit
BATCH_MIXING_STRATEGY=none # Options: none, random, balanced

# Analysis Configuration
CODING_MODE=HYBRID         # OPEN, CLOSED, or HYBRID
ENTITY_MODE=HYBRID         # OPEN, CLOSED, or HYBRID
MIN_CODE_FREQUENCY=2       # Minimum appearances to keep code
DETECT_CONTRADICTIONS=true
IDENTIFY_CONSENSUS=true

# Operational Features
SHOW_PROGRESS=true
AUTO_QUARANTINE=true
COST_LIMIT=10.00          # Maximum cost per analysis
CONFIRM_COST=true         # Ask before proceeding

# Output Settings
GENERATE_POLICY_BRIEF=true
GENERATE_CONTRADICTION_MATRIX=true
GENERATE_EXECUTIVE_SUMMARY=true
```

---

## Three-Phase Aggregation Workflow

### Phase 1: Initial Unconstrained Coding
- Process interviews in batches under MAX_BATCH_TOKENS
- No frequency limits or constraints
- Extract ALL patterns and entities
- Each batch processes independently
- Automatic quarantine of corrupted interviews

### Phase 2: Intelligent Aggregation
- Single LLM call sees ALL codes from ALL batches
- Semantic deduplication (e.g., "regulatory_burden" = "red_tape")
- Build hierarchical code structure
- Detect contradictions between stakeholder groups
- Identify consensus areas
- Apply frequency thresholds with policy significance override

### Phase 3: Final Consistent Coding
- Apply refined codebook across all interviews
- Consistent code application
- Final entity extraction with relationships
- Cross-layer linking

---

## Dual-Layer Architecture

### Layer 1: Qualitative Codes (CODE_*)
- Themes, patterns, meanings
- Hierarchical organization
- Frequency tracking
- Quote examples

### Layer 2: Knowledge Entities (ENT_*)
- People, organizations, tools, methods
- Policy entities: recommendations, barriers, metaphors
- Properties and relationships
- Stakeholder type tracking

### Cross-Layer Integration
- Codes linked to entities
- Entity properties inform code interpretation
- Contradiction detection across both layers
- Voice counting (unique entities per code)

---

## Three-Mode System

### OPEN Mode
- **Purpose**: Emergent pattern discovery
- **Use Case**: Exploratory analysis, new policy areas
- **Behavior**: No predefined codes/entities, discover from data

### CLOSED Mode
- **Purpose**: Framework validation
- **Use Case**: Testing specific theories or policies
- **Behavior**: ONLY predefined codes/entities allowed
- **Enforcement**: Structured output with enum constraints

### HYBRID Mode
- **Purpose**: Framework enhancement
- **Use Case**: Known framework with room for discovery
- **Behavior**: Apply framework AND discover new patterns
- **Tracking**: Distinguish predefined vs emergent

---

## Batch Processing Strategy

```python
# Flexible batching based on token count
def create_batches(interviews: List[str], max_tokens: int) -> List[Batch]:
    """
    Pack interviews into batches under token limit.
    Example: 50 interviews might become [21, 19, 10] per batch
    """
    batches = []
    current_batch = Batch()
    
    for interview in interviews:
        tokens = estimate_tokens(interview)
        
        if current_batch.total_tokens + tokens > max_tokens:
            batches.append(current_batch)
            current_batch = Batch()
            
        current_batch.add_interview(interview)
    
    if current_batch.interviews:
        batches.append(current_batch)
        
    return batches
```

---

## Policy-Specific Features

### Stakeholder Mapping
- Automatic extraction from text
- Properties: role, department, organization, stakeholder_type
- Types: implementer, beneficiary, regulator, advocate, etc.

### Contradiction Detection
- Identify opposing views on same issues
- Link to stakeholder types
- Severity ratings (low/medium/high)
- Generate contradiction matrix

### Executive Summary Generation
- One-page policy briefs
- Key themes by frequency and significance
- Stakeholder positions summary
- Consensus vs conflict areas
- Implementation barriers by severity
- Policy recommendations by urgency

---

## Operational Features

### Progress Tracking
```python
class ProgressTracker:
    def update(phase: str, percent: float, message: str):
        # Real-time updates during processing
        # Phase tracking: Initialization → Phase 1 → Phase 2 → Phase 3 → Reporting
        # No specific performance promises
```

### Cost Management
```python
class CostTracker:
    INPUT_PRICE = 0.30   # per 1M tokens (from .env)
    OUTPUT_PRICE = 2.50  # per 1M tokens (from .env)
    
    def estimate_cost(interviews: List[str]) -> float:
        # Pre-execution estimation
        # 3 phases × token usage × prices
        
    def confirm_with_user(estimated_cost: float) -> bool:
        # Optional user confirmation
```

### Error Recovery
```python
class ErrorRecovery:
    def validate_interview(interview: str) -> bool:
        # Check for corruption, encoding issues
        
    def quarantine_invalid(interview: Interview, reason: str):
        # Move to quarantine, log reason
        # Continue with valid interviews
```

---

## Data Flow

1. **Input**: Interview texts (any format)
2. **Validation**: Check encoding, minimum length
3. **Batching**: Group into token-limited batches
4. **Phase 1**: Parallel batch processing
5. **Phase 2**: Aggregation and refinement
6. **Phase 3**: Final coding application
7. **Output**: Codes, entities, relationships, reports

---

## Storage

- **Input**: File-based (text, JSON, CSV)
- **Processing**: In-memory during analysis
- **Output**: JSON for codes/entities
- **Future**: Neo4j for relationship queries

---

## Implementation Status

### Completed
- Architecture design and documentation
- Three-phase workflow specification
- Dual-layer design with policy entities
- Three-mode system design

### Pending (High Priority)
- Batch processing infrastructure
- Three-phase implementation
- Progress tracking system
- Cost management system
- Error recovery system

### Pending (Medium Priority)
- Cross-layer queries
- Report generation
- Visualization tools
- Neo4j integration

---

## Key Decisions

1. **No Fixed Scale**: System handles whatever interviews provided
2. **Flexible Batching**: Not all interviews in one batch
3. **No Performance Promises**: Processing time varies by content
4. **Conservative Defaults**: 200K token batches (configurable)
5. **All Configuration in .env**: No hardcoded values
6. **Gemini 2.5 Flash**: Latest model with better pricing

---

## Future Considerations

- **Batch Mixing**: Option to redistribute interviews across iterations
- **Incremental Processing**: Add new interviews without full reanalysis
- **Multi-Language**: Support for non-English interviews
- **Real-time Monitoring**: Web UI for progress tracking