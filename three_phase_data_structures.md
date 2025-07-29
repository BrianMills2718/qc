# Three-Phase Qualitative Coding Data Structures

## 🎯 Overview: Exact JSON Schemas for Each Phase

Based on review of existing `qualitative_coding_extractor.py` and Gemini structured output documentation, here are the precise data structures for each phase of the three-phase coding process.

**Key Design Decisions**:
- Use Pydantic models with Gemini's `response_schema` configuration (recommended approach)
- Each phase builds incrementally on previous phases
- Full JSON schemas with property ordering for consistent output
- Real quotes with exact line number mappings

---

## 📊 Phase 1: Open Coding Data Structures

### Core Open Coding Models
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SegmentType(str, Enum):
    """Types of coded segments"""
    QUOTE = "quote"
    PARAPHRASE = "paraphrase"
    OBSERVATION = "observation"
    CONTEXT = "context"

class CodedSegment(BaseModel):
    """Individual coded segment from interview"""
    id: str = Field(description="Unique identifier for this segment")
    text: str = Field(description="Exact text of the segment")
    start_line: int = Field(description="Line number where segment starts")
    end_line: int = Field(description="Line number where segment ends")  
    participant_id: Optional[str] = Field(description="Speaker identifier if available")
    segment_type: SegmentType = Field(default=SegmentType.QUOTE)
    context_before: Optional[str] = Field(description="Context preceding this segment")
    context_after: Optional[str] = Field(description="Context following this segment")

class OpenCode(BaseModel):
    """Individual code discovered during open coding"""
    id: str = Field(description="Unique identifier for this code")
    name: str = Field(description="Descriptive name of the code")
    definition: str = Field(description="Clear definition of what this code represents")
    segments: List[CodedSegment] = Field(description="Segments supporting this code")
    frequency: int = Field(description="Number of times this code appears")
    theoretical_notes: Optional[str] = Field(description="Initial theoretical observations")
    
    @property
    def segment_count(self) -> int:
        return len(self.segments)

class AnalyticalMemo(BaseModel):
    """Analytical memo explaining coding decisions"""
    id: str = Field(description="Unique identifier for this memo")
    memo_type: str = Field(description="Type of memo (code, theoretical, methodological)")
    title: str = Field(description="Brief title for the memo")
    content: str = Field(description="Full memo content explaining reasoning")
    related_codes: List[str] = Field(description="Code IDs this memo relates to")
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in this analysis")

class OpenCodingResult(BaseModel):
    """Complete result from Phase 1: Open Coding"""
    interview_id: str = Field(description="Identifier of the processed interview")
    codes: List[OpenCode] = Field(description="All codes discovered in open coding")
    memos: List[AnalyticalMemo] = Field(description="Analytical memos explaining decisions")
    total_segments_coded: int = Field(description="Total number of segments coded")
    coverage_percentage: float = Field(ge=0.0, le=100.0, description="Percentage of interview coded")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        # Property ordering for consistent Gemini output
        property_ordering = ["interview_id", "codes", "memos", "total_segments_coded", "coverage_percentage"]
```

### Phase 1 Gemini Configuration
```python
# Gemini call configuration for Open Coding
OPEN_CODING_CONFIG = {
    "response_mime_type": "application/json",
    "response_schema": OpenCodingResult,
    "temperature": 0.3,
    "max_output_tokens": 60000
}

OPEN_CODING_PROMPT_TEMPLATE = """
Perform OPEN CODING on this interview transcript using grounded theory methodology.

Research Question: {research_question}

INSTRUCTIONS:
1. Read the entire transcript carefully
2. Identify meaningful segments that relate to experiences, feelings, challenges, strategies
3. Assign descriptive codes to these segments
4. Write analytical memos explaining WHY each code was applied
5. Focus on participant's perspective and meaning-making

For each coded segment:
- Extract the EXACT quote with line numbers
- Create descriptive code name that captures the essence
- Write clear definition explaining what the code represents
- Add analytical memo explaining the significance
- Note any initial theoretical insights

Interview text:
{interview_text}

Return comprehensive open coding results matching the required JSON schema.
"""
```

---

## 🔗 Phase 2: Axial Coding Data Structures

### Axial Coding Models
```python
class CategoryProperty(BaseModel):
    """Property of a category with its dimensions"""
    property_name: str = Field(description="Name of the property")
    dimensions: List[str] = Field(description="Range of values for this property")
    examples: List[str] = Field(description="Example segments showing this property")

class CategoryRelationship(BaseModel):
    """Relationship between categories"""
    relationship_type: str = Field(description="Type of relationship (causal, contextual, etc.)")
    source_category_id: str = Field(description="ID of the source category")
    target_category_id: str = Field(description="ID of the target category")
    description: str = Field(description="Description of how categories relate")
    supporting_evidence: List[str] = Field(description="Segment IDs supporting this relationship")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this relationship")

class Category(BaseModel):
    """Category grouping related codes"""
    id: str = Field(description="Unique identifier for this category")
    name: str = Field(description="Descriptive name of the category")
    description: str = Field(description="What this category represents")
    related_codes: List[str] = Field(description="Open code IDs that belong to this category")
    properties: List[CategoryProperty] = Field(description="Properties and dimensions")
    
    # Grounded theory paradigm elements
    causal_conditions: List[str] = Field(description="What leads to this category")
    context: List[str] = Field(description="Contextual factors influencing this category")  
    intervening_conditions: List[str] = Field(description="Factors that facilitate/constrain")
    action_strategies: List[str] = Field(description="How people respond/deal with this")
    consequences: List[str] = Field(description="Outcomes resulting from this category")
    
    theoretical_density: float = Field(ge=0.0, le=1.0, description="How theoretically developed")

class AxialCodingResult(BaseModel):
    """Complete result from Phase 2: Axial Coding"""
    interview_id: str = Field(description="Identifier of the processed interview")
    categories: List[Category] = Field(description="Categories formed from open codes")
    relationships: List[CategoryRelationship] = Field(description="Relationships between categories")
    paradigm_model: Dict[str, List[str]] = Field(description="Grounded theory paradigm model")
    theoretical_development: str = Field(description="Theoretical insights about relationships")
    integration_level: float = Field(ge=0.0, le=1.0, description="How well integrated the analysis is")
    
    class Config:
        property_ordering = ["interview_id", "categories", "relationships", "paradigm_model", "theoretical_development"]
```

### Phase 2 Gemini Configuration
```python
AXIAL_CODING_CONFIG = {
    "response_mime_type": "application/json", 
    "response_schema": AxialCodingResult,
    "temperature": 0.3,
    "max_output_tokens": 60000
}

AXIAL_CODING_PROMPT_TEMPLATE = """
Perform AXIAL CODING to organize open codes into categories and find relationships.

{existing_codebook_context}

Open codes from this interview:
{open_codes_json}

INSTRUCTIONS:
1. Group related codes into substantive categories (3-7 categories maximum)
2. Identify properties and dimensions of each category
3. Find relationships between categories using grounded theory paradigm:
   - Causal conditions (what leads to this?)
   - Context (what influences this?)
   - Intervening conditions (what facilitates/constrains?)
   - Action/interaction strategies (how do people respond?)
   - Consequences (what are the outcomes?)

4. Develop theoretical connections between categories
5. Write analytical notes about category development
6. Build hierarchical structure showing relationships

Focus on the most significant patterns and relationships.
Return results matching the required JSON schema.
"""
```

---

## 🎯 Phase 3: Selective Coding Data Structures

### Selective Coding Models
```python
class CoreCategoryConnection(BaseModel):
    """How other categories connect to the core category"""
    category_id: str = Field(description="ID of the connecting category")
    connection_type: str = Field(description="Type of connection to core category")
    connection_strength: float = Field(ge=0.0, le=1.0, description="Strength of connection")
    explanation: str = Field(description="How this category relates to core category")

class TheoreticalModel(BaseModel):
    """Theoretical model explaining the core phenomenon"""
    model_name: str = Field(description="Name of the theoretical model")
    description: str = Field(description="Explanation of the theoretical model")
    key_processes: List[str] = Field(description="Key processes in the model")
    model_relationships: List[str] = Field(description="How elements relate in the model")
    supporting_evidence: List[str] = Field(description="Evidence supporting this model")

class TheoreticalInsight(BaseModel):
    """Key theoretical insight from the analysis"""
    insight_id: str = Field(description="Unique identifier for this insight")
    title: str = Field(description="Brief title of the insight")
    description: str = Field(description="Detailed description of the insight")
    theoretical_significance: str = Field(description="Why this insight matters theoretically")
    practical_implications: List[str] = Field(description="Practical implications of this insight")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in this insight")

class SelectiveCodingResult(BaseModel):
    """Complete result from Phase 3: Selective Coding"""
    interview_id: str = Field(description="Identifier of the processed interview")
    
    # Core category identification
    core_category_id: str = Field(description="ID of the central category")
    core_category_name: str = Field(description="Name of the core category")
    core_phenomenon: str = Field(description="The central phenomenon being explained")
    
    # Connections and integration
    category_connections: List[CoreCategoryConnection] = Field(description="How categories connect to core")
    theoretical_story: str = Field(description="The overall theoretical story")
    theoretical_model: TheoreticalModel = Field(description="Theoretical model of the phenomenon")
    
    # Insights and implications
    key_insights: List[TheoreticalInsight] = Field(description="Key theoretical insights")
    theoretical_saturation_notes: str = Field(description="Notes about theoretical development")
    
    # Quality metrics
    integration_completeness: float = Field(ge=0.0, le=1.0, description="How complete the integration is")
    theoretical_density: float = Field(ge=0.0, le=1.0, description="Theoretical density achieved")
    
    class Config:
        property_ordering = ["interview_id", "core_category_name", "core_phenomenon", 
                           "category_connections", "theoretical_story", "key_insights"]
```

### Phase 3 Gemini Configuration
```python
SELECTIVE_CODING_CONFIG = {
    "response_mime_type": "application/json",
    "response_schema": SelectiveCodingResult, 
    "temperature": 0.2,  # Lower temperature for theoretical precision
    "max_output_tokens": 60000
}

SELECTIVE_CODING_PROMPT_TEMPLATE = """
Perform SELECTIVE CODING to identify the core category and theoretical story.

Categories from axial coding:
{categories_json}

Existing codebook context:
{existing_codebook_context}

INSTRUCTIONS:
1. Identify the CENTRAL phenomenon that ties everything together
2. Show how all other categories relate to this core category
3. Develop the overall theoretical story the data tells
4. Generate key theoretical insights
5. Explain the process or experience at the heart of this data

The core category should:
- Appear frequently in the data  
- Connect to most other categories
- Have explanatory power for the phenomenon
- Be sufficiently abstract to be theoretical
- Capture the main story of what's happening

Provide a theoretical model explaining the core phenomenon.
Return results matching the required JSON schema.
"""
```

---

## 🔄 Codebook Evolution Data Structures

### Codebook Management Models
```python
class CodebookVersion(BaseModel):
    """Version information for codebook evolution"""
    version: str = Field(description="Version identifier (e.g., '1.2.0')")
    created_date: datetime = Field(default_factory=datetime.now)
    interviews_processed: int = Field(description="Number of interviews in this version")
    changes_summary: str = Field(description="Summary of changes in this version")
    saturation_assessment: Optional[str] = Field(description="Saturation notes for this version")

class CodeEvolution(BaseModel):
    """How a code has evolved across interviews"""
    code_id: str = Field(description="Unique identifier for this code")
    original_name: str = Field(description="Original code name")
    current_name: str = Field(description="Current code name after evolution")
    definition_evolution: List[str] = Field(description="How definition has evolved")
    frequency_by_interview: Dict[str, int] = Field(description="Frequency in each interview")
    theoretical_development: List[str] = Field(description="How theoretical understanding evolved")

class Codebook(BaseModel):
    """Complete codebook with evolution tracking"""
    version_info: CodebookVersion = Field(description="Version and metadata")
    themes: List[str] = Field(description="High-level themes discovered")
    categories: List[Category] = Field(description="All categories across interviews")
    codes: List[OpenCode] = Field(description="All codes with their full development")
    code_evolution: List[CodeEvolution] = Field(description="How codes have evolved")
    theoretical_insights: List[TheoreticalInsight] = Field(description="Cross-interview insights")
    saturation_indicators: Dict[str, float] = Field(description="Saturation metrics by domain")
    
    def to_context_string(self) -> str:
        """Format codebook for LLM context in subsequent interviews"""
        context_parts = [
            f"Codebook Version: {self.version_info.version}",
            f"Interviews Processed: {self.version_info.interviews_processed}",
            "",
            "EXISTING THEMES:",
            *[f"- {theme}" for theme in self.themes],
            "",
            "EXISTING CATEGORIES:",
            *[f"- {cat.name}: {cat.description}" for cat in self.categories],
            "",
            "EXISTING CODES (showing top 10 by frequency):",
        ]
        
        # Sort codes by frequency and show top 10
        sorted_codes = sorted(self.codes, key=lambda c: c.frequency, reverse=True)[:10]
        for code in sorted_codes:
            context_parts.append(f"- {code.name}: {code.definition} (frequency: {code.frequency})")
        
        context_parts.extend([
            "",
            "KEY THEORETICAL INSIGHTS:",
            *[f"- {insight.title}: {insight.description}" for insight in self.theoretical_insights[:5]],
            "",
            "GUIDANCE: When coding new interviews, consider how new codes relate to existing ones.",
            "Create new codes only when existing ones don't capture the meaning.",
            "Build on existing theoretical insights while remaining open to new discoveries."
        ])
        
        return "\n".join(context_parts)
```

---

## 📊 Batch Processing Data Structures

### Batch Results Models
```python
class InterviewProcessingResult(BaseModel):
    """Result from processing a single interview"""
    interview_id: str = Field(description="Unique identifier for the interview")
    file_path: str = Field(description="Path to the original interview file")
    processing_status: str = Field(description="Success, failed, or partial")
    
    # Three-phase results
    open_coding_result: Optional[OpenCodingResult] = None
    axial_coding_result: Optional[AxialCodingResult] = None  
    selective_coding_result: Optional[SelectiveCodingResult] = None
    
    # Processing metadata
    processing_time_seconds: float = Field(description="Total processing time")
    token_usage: Dict[str, int] = Field(description="Token usage breakdown")
    error_log: List[str] = Field(default_factory=list, description="Any errors encountered")
    confidence_metrics: Dict[str, float] = Field(default_factory=dict)

class BatchProcessingResult(BaseModel):
    """Result from processing a batch of interviews"""
    batch_id: str = Field(description="Unique identifier for this batch")
    batch_number: int = Field(description="Sequential batch number")
    interview_results: List[InterviewProcessingResult] = Field(description="Results for each interview")
    
    # Batch-level aggregation
    successful_interviews: int = Field(description="Number of successfully processed interviews")
    failed_interviews: int = Field(description="Number of failed interviews")
    total_processing_time: float = Field(description="Total batch processing time")
    
    # Codebook evolution for this batch
    pre_batch_codebook: Optional[Codebook] = Field(description="Codebook before this batch")
    post_batch_codebook: Optional[Codebook] = Field(description="Codebook after this batch")
    
    # Saturation assessment
    saturation_assessment: Optional[str] = Field(description="LLM assessment of saturation")
    continue_processing: bool = Field(description="Whether to continue with more batches")

class FinalAnalysisResult(BaseModel):
    """Final analysis across all batches"""
    study_id: str = Field(description="Unique identifier for the complete study")
    total_interviews_processed: int = Field(description="Total interviews across all batches")
    batches_completed: int = Field(description="Number of batches processed")
    
    # Final codebook and insights
    final_codebook: Codebook = Field(description="Final evolved codebook")
    cross_interview_themes: List[str] = Field(description="Themes that emerged across interviews")
    theoretical_model: TheoreticalModel = Field(description="Final theoretical model")
    
    # Quality and saturation
    theoretical_saturation_reached: bool = Field(description="Whether saturation was achieved")
    saturation_evidence: str = Field(description="Evidence for saturation decision")
    
    # Outputs for different audiences
    policy_brief: Optional[str] = Field(description="Policy-oriented summary if requested")
    contradictions_identified: List[str] = Field(description="Contradictions found in data")
    
    # Processing metadata
    total_processing_time_hours: float = Field(description="Total study processing time")
    total_token_usage: Dict[str, int] = Field(description="Complete token usage breakdown")
    
    class Config:
        property_ordering = ["study_id", "total_interviews_processed", "final_codebook", 
                           "cross_interview_themes", "theoretical_model", "policy_brief"]
```

---

## ✅ Implementation Notes

### JSON Schema Validation
```python
# Example of how to use these models with Gemini
async def perform_open_coding(interview_text: str, research_question: str) -> OpenCodingResult:
    """Perform open coding with structured output"""
    
    prompt = OPEN_CODING_PROMPT_TEMPLATE.format(
        research_question=research_question,
        interview_text=interview_text
    )
    
    response = await gemini_client.generate_content(
        prompt,
        generation_config=OPEN_CODING_CONFIG
    )
    
    # Automatic validation with Pydantic
    try:
        result = OpenCodingResult.parse_raw(response.text)
        logger.info(f"Open coding successful: {len(result.codes)} codes, {result.total_segments_coded} segments")
        return result
    except ValidationError as e:
        logger.error(f"Open coding validation failed: {e}")
        raise LLMSchemaValidationError(f"Open coding response doesn't match schema: {e}") from e
```

### Property Ordering for Consistent Output
Per Gemini documentation, property ordering is critical for quality results. Each model includes `property_ordering` in the Config class to ensure consistent LLM output.

### Real Quote Mapping
All `CodedSegment` objects include precise line number mapping (`start_line`, `end_line`) to enable exact quote attribution back to source interviews.

These data structures provide the foundation for reliable, structured qualitative coding with full traceability and theoretical development.