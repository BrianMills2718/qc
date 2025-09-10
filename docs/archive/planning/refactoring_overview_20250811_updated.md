# Qualitative Coding System Refactoring Overview
## Code-First Architecture Transformation

**Date**: 2025-08-11 (Updated)  
**Status**: Implementation Ready  

---

## Executive Summary

This document outlines the comprehensive refactoring plan to transform the current entity-centric qualitative coding system into a **code-first architecture**. The primary goal is to make thematic codes the central organizing principle, with quotes, speakers, entities, and relationships flowing from codes rather than existing independently.

---

## Target Architecture

### Core Principles

#### 1. Code-First Data Model
```
Codes (Hierarchical Taxonomy)
  ├── Quotes (many-to-many with codes)
  │   ├── Properties: text, context_summary, location, interview_id, line_start/end
  │   ├── Speaker: {name, confidence, role, organization, ...} (embedded property)
  │   └── Associated: entities, relationships discovered in quote context
  └── Flexible Navigation: explore from codes, quotes, speakers, or entities
```

#### 2. Two-Phase Extraction Workflow

**Phase 1: Cross-Interview Code Discovery**
- Concatenate ALL interviews into single LLM call (utilizing 1M token context window)
- Generate comprehensive hierarchical code taxonomy based on analytic question
- Configurable hierarchy depth (default: 2 levels)
- Skip this phase for closed coding approach
- No max_tokens limit - use full context window

**Phase 2: Per-Interview Code Application**
- Apply discovered codes to each interview (strict matching only)
- Extract relevant quotes with flexible boundaries determined by LLM
- Generate context summary for each quote along with exact text
- Identify speakers with confidence ratings and configurable properties
- LLM uses contextual clues to determine speaker identity flexibly
- Extract entities and relationships at three levels:
  - Quote-level: entities/relationships within specific quote
  - Interview-level: entities/relationships across interview
  - Global-level: cross-interview entity/relationship network

#### 3. Configurable Extraction Pipeline

**Coding Approaches:**
- **Open Coding**: System discovers all codes based solely on analytic question
- **Closed Coding**: Apply predefined codes only (skip Phase 1)
- **Mixed Coding**: Start with existing codes, discover additional themes in Phase 1

**Configuration Schema:**
```yaml
extraction_config:
  # Core Configuration
  analytic_question: "What are the key themes regarding AI adoption?"
  coding_approach: "open" # open, closed, or mixed
  interview_files:
    - "path/to/interview1.docx"
    - "path/to/interview2.docx"
  
  # Hierarchy Configuration
  hierarchy:
    max_depth: 2  # default: 2 levels
    # No min_quotes_per_code - let this emerge naturally
  
  # Speaker Properties Schema
  speaker_properties:
    - name: "role"
      type: "string"
      required: true
    - name: "organization"
      type: "string"
      required: false
    - name: "expertise_areas"
      type: "list"
      required: false
    - name: "seniority"
      type: "string"
      required: false
  
  # Predefined Codes (for closed/mixed approaches)
  predefined_codes:
    - name: "AI Benefits"
      description: "Positive impacts of AI adoption"
    - name: "AI Challenges"
      description: "Barriers and difficulties with AI"
  
  # Output Configuration
  output:
    format: "both"  # both JSON files and Neo4j import
    json_path: "output/extraction_results.json"
    auto_import: true  # Import to Neo4j without review step
  
  # LLM Configuration
  llm:
    model: "gemini-1.5-pro"
    max_tokens: null  # Use maximum available
    temperature: 0.1  # Low temperature for consistency
```

---

## Implementation Plan

### Phase 1: Data Model Enhancement

#### 1.1 Hierarchical Code Structure
```python
class HierarchicalCode(BaseModel):
    id: str
    name: str
    description: str
    semantic_definition: str  # LLM-generated meaning
    parent_id: Optional[str]  # For hierarchy
    level: int  # 0 for root, 1 for first level, etc.
    confidence: float
    
    # Aggregated metrics
    quote_count: int
    entity_associations: List[str]
    cross_interview_frequency: Dict[str, int]
```

#### 1.2 Enhanced Quote Model
```python
class EnhancedQuote(BaseModel):
    id: str
    text: str  # Exact quote text
    context_summary: str  # LLM-generated summary of surrounding context
    code_ids: List[str]  # Multiple code associations allowed
    
    # Provenance
    interview_id: str
    interview_title: str
    line_start: int
    line_end: int
    
    # Speaker information (embedded property)
    speaker: SpeakerInfo  # Contains name, confidence, role, organization, etc.
    
    # Multi-level associations
    quote_entities: List[EntityReference]  # Entities in this quote
    quote_relationships: List[RelationshipReference]  # Relations in this quote
    # Interview and global level tracked separately in database
```

#### 1.3 Speaker Information Model
```python
class SpeakerInfo(BaseModel):
    name: str  # Best guess at speaker name
    confidence: float  # Confidence in identification (0-1)
    identification_method: str  # How speaker was identified
    
    # Configurable properties from schema
    role: Optional[str]
    organization: Optional[str]
    expertise_areas: Optional[List[str]]
    seniority: Optional[str]
    # Additional properties loaded from config
```

### Phase 2: Extraction Pipeline Implementation

#### 2.1 Cross-Interview Code Discovery
```python
class CodeTaxonomyDiscovery:
    async def discover_codes(self, config: ExtractionConfig) -> CodeTaxonomy:
        """
        Single LLM call analyzing all interviews for comprehensive code discovery
        Uses full 1M token context window - no max_tokens limit
        """
        if config.coding_approach == 'closed':
            return self.load_predefined_codes(config.predefined_codes)
        
        # Concatenate all interviews for single LLM call
        combined_text = self.concatenate_interviews(config.interview_files)
        
        # Build prompt based on approach
        if config.coding_approach == 'mixed':
            prompt = self.build_mixed_discovery_prompt(
                text=combined_text,
                analytic_question=config.analytic_question,
                existing_codes=config.predefined_codes,
                max_hierarchy_depth=config.hierarchy.max_depth
            )
        else:  # open coding
            prompt = self.build_open_discovery_prompt(
                text=combined_text,
                analytic_question=config.analytic_question,
                max_hierarchy_depth=config.hierarchy.max_depth
            )
        
        # Extract hierarchical code structure (no token limit)
        taxonomy = await self.llm.extract_structured(
            prompt=prompt,
            schema=CodeTaxonomySchema,
            max_tokens=None  # Use maximum available
        )
        
        return taxonomy
```

#### 2.2 Per-Interview Code Application
```python
class CodeApplicationEngine:
    async def apply_codes(self, 
                          interview: Interview, 
                          taxonomy: CodeTaxonomy,
                          config: ExtractionConfig) -> CodedInterview:
        """
        Apply discovered codes to individual interview with strict matching
        """
        prompt = self.build_application_prompt(
            interview_text=interview.text,
            codes=taxonomy.codes,
            analytic_question=config.analytic_question,
            speaker_schema=config.speaker_properties
        )
        
        # Add specific instructions for flexible processing
        instructions = """
        For each code in the taxonomy:
        1. Find ALL quotes that relate to this code
        2. Determine quote boundaries flexibly based on semantic completeness
        3. Generate a context summary explaining the quote's surrounding discussion
        4. Identify the speaker using ANY contextual clues available:
           - Explicit speaker labels
           - Meeting notes headers
           - Conversational context
           - Document metadata
           Provide confidence score for speaker identification
        5. Extract speaker properties based on the provided schema
        6. Identify entities and relationships at quote, interview, and global levels
        
        A single quote may relate to multiple codes - include it under ALL relevant codes.
        """
        
        coded_data = await self.llm.extract_structured(
            prompt=prompt,
            schema=CodedInterviewSchema,
            instructions=instructions,
            max_tokens=None
        )
        
        return coded_data
```

#### 2.3 Output Generation
```python
class OutputManager:
    def generate_outputs(self, results: ExtractionResults, config: ExtractionConfig):
        """
        Generate both JSON files and Neo4j import without review step
        """
        # Always generate JSON for archival
        json_output = self.generate_json_output(results)
        self.save_json(json_output, config.output.json_path)
        
        # Auto-import to Neo4j if configured
        if config.output.auto_import:
            self.import_to_neo4j(results)
        
        # Generate confidence report
        confidence_report = self.generate_confidence_report(results)
        self.save_report(confidence_report)
```

### Phase 3: Flexible Navigation System

Once the database is populated, users can navigate from multiple entry points:

#### 3.1 Navigation Paths
- **Code → Quotes**: View all quotes for a specific code
- **Code → Speakers**: See all speakers discussing a code
- **Code → Entities**: Find entities associated with a code
- **Speaker → Quotes**: All quotes from a specific speaker
- **Speaker → Codes**: Topics a speaker discusses
- **Entity → Quotes**: Quotes mentioning an entity
- **Entity → Codes**: Codes associated with an entity
- **Cross-cutting**: Complex queries across dimensions

#### 3.2 API Endpoints
```python
# Code-centric endpoints
GET /api/codes/hierarchy           # Full code taxonomy
GET /api/codes/{code_id}/quotes    # All quotes for a code
GET /api/codes/{code_id}/speakers  # Speakers discussing this code
GET /api/codes/{code_id}/entities  # Entities related to this code

# Speaker-centric endpoints
GET /api/speakers                  # All identified speakers
GET /api/speakers/{speaker_id}/quotes  # All quotes by speaker
GET /api/speakers/{speaker_id}/codes   # Codes this speaker discusses

# Entity-centric endpoints (still available)
GET /api/entities/{entity_id}/quotes  # Quotes mentioning entity
GET /api/entities/{entity_id}/codes   # Codes associated with entity

# Quote-level endpoints
GET /api/quotes/{quote_id}         # Full quote details with all associations
```

---

## Key Implementation Decisions

### No Manual Review Step
- System generates confidence scores for all extractions
- Outputs are immediately available in both JSON and Neo4j
- Users can query and filter by confidence levels post-extraction

### Flexible Quote Boundaries
- LLM determines semantically complete quote boundaries
- Not restricted to sentences or paragraphs
- Includes context summary for understanding

### Speaker Identification Strategy
- No hardcoded rules for speaker detection
- LLM uses all available contextual clues
- Handles varied formats (transcripts, notes, multi-speaker interviews)
- Confidence scores indicate reliability

### Multi-Level Entity/Relationship Extraction
- Quote-level: What's mentioned in this specific quote
- Interview-level: Entities across the whole interview
- Global-level: Cross-interview entity network

### Quote-Code Many-to-Many
- Single quote can support multiple codes
- Reduces artificial boundaries
- More accurate thematic representation

---

## Migration Strategy

### Complete Re-extraction Approach
1. Archive existing Neo4j data
2. Configure extraction pipeline with analytic question
3. Run Phase 1 for code discovery (or load predefined codes)
4. Run Phase 2 for each interview
5. Generate JSON outputs
6. Import to fresh Neo4j instance
7. Validate extraction quality via confidence reports

### No Preservation of Old Data
- Previous entity-centric extractions discarded
- Fresh start with code-first approach
- Ensures consistency across all data

---

## Success Metrics

### Extraction Quality
- Average speaker identification confidence > 0.7
- Average code assignment confidence > 0.8
- Successful quote extraction for all codes
- Entity/relationship extraction at all three levels

### System Capabilities
- Handle 100+ interviews in single Phase 1 call (within 1M tokens)
- Support 2+ hierarchy levels effectively
- Generate comprehensive navigation paths
- Maintain sub-second query response times

### User Experience
- Navigate from any entry point (code, speaker, entity, quote)
- Filter by confidence levels
- Export subsets of data
- Understand quote context via summaries

---

## Remaining Clarification Questions

### 1. Quote Context Summary
- How detailed should the context summary be? (1-2 sentences? Paragraph?)
- Should it explain why the quote relates to the assigned codes?

### 2. Confidence Thresholds
- Should there be minimum confidence for inclusion? (e.g., ignore speakers with <0.3 confidence?)
- Or include everything and let users filter?

### 3. Output File Structure
- One JSON file per interview, or single combined file?
- Include intermediate Phase 1 taxonomy as separate file?

### 4. Entity/Relationship Types
- Should we maintain the existing entity types (Person, Organization, Method, Tool)?
- What relationship types beyond "SUPPORTS" should we extract?

### 5. Interview File Processing
- How should we handle different file formats (DOCX, TXT, PDF)?
- Any preprocessing needed (remove headers, page numbers)?

### 6. Error Handling
- What if an interview has no relevant content for the analytic question?
- How to handle interviews that exceed token limits in Phase 2?

These clarifications will help finalize the implementation details while maintaining the flexible, configurable architecture you've outlined.