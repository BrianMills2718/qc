# LLM-Native Global Analysis Approach

## 🎯 Core Philosophy: Leverage LLM's Global Context Advantage

Instead of mimicking human cognitive limitations (processing interviews one-by-one), use the LLM's ability to see patterns across the entire 103-interview dataset simultaneously.

---

## 📊 Efficiency Comparison

| Approach | LLM Calls | Dev Time | Quality | Debugging |
|----------|-----------|----------|---------|-----------|
| **LLM-Native Global** | **2** | **2 days** | **TBD** | **Hard** |
| Systematic Three-Phase | 330-345 | 15 days | High | Easy |
| Batched Three-Phase | 36-40 | 5 days | Medium | Medium |
| Progressive Sampling | 125-155 | 10 days | Medium | Medium |

---

## 🧠 The LLM-Native Implementation

### Step 1: Load All Interviews
```python
# qc/core/global_qualitative_analyzer.py
async def load_all_interviews(self) -> str:
    """Load all 103 interviews with metadata for global analysis"""
    all_content = []
    
    for i, file_path in enumerate(self.interview_files):
        interview_data = self.docx_parser.parse_interview_file(file_path)
        
        # Add metadata markers for traceability
        content_with_metadata = f"""
=== INTERVIEW {i+1:03d}: {interview_data['metadata']['file_name']} ===
WORD_COUNT: {interview_data['metadata']['word_count']}
SOURCE: {interview_data['metadata']['file_path']}

{interview_data['content']}

=== END INTERVIEW {i+1:03d} ===
"""
        all_content.append(content_with_metadata)
    
    # Verify token count
    full_text = "\n\n".join(all_content)
    token_count = self.token_counter.count_tokens(full_text)
    
    if token_count > 900_000:  # Leave room for prompt
        raise ValueError(f"Total content too large: {token_count:,} tokens")
    
    logger.info(f"Loaded {len(self.interview_files)} interviews: {token_count:,} tokens")
    return full_text
```

### Step 2: Comprehensive Global Analysis (Call 1)
```python
async def comprehensive_global_analysis(self, all_interviews: str) -> GlobalCodingResult:
    """Single LLM call analyzing all interviews with global context"""
    
    prompt = f"""
Analyze these 103 interviews using grounded theory methodology with GLOBAL CONTEXT.

Unlike human researchers who must process interviews sequentially, you can see ALL the data simultaneously. Use this advantage to:

1. **IDENTIFY THEMES** that emerge across the ENTIRE dataset
2. **TRACK CONCEPT DEVELOPMENT** - how ideas evolve from Interview 001 to 103
3. **FIND QUOTE CHAINS** - sequences of related quotes showing progression
4. **ASSESS THEORETICAL SATURATION** - identify when new interviews stopped adding new insights
5. **DETECT CONTRADICTIONS** - opposing viewpoints with evidence from both sides
6. **MAP STAKEHOLDER POSITIONS** - who says what about which topics

RESEARCH QUESTION: {self.config.research_question}

METHODOLOGICAL INSTRUCTIONS:
- Apply grounded theory principles but leverage your global perspective
- Create codes that capture meaning across ALL interviews
- Build themes hierarchically (themes → categories → codes)
- Track which interviews support each finding
- Provide exact quotes with interview numbers and line references
- Assess when theoretical saturation naturally occurred in the sequence

ALL 103 INTERVIEWS:
{all_interviews}

Return comprehensive analysis following the GlobalCodingResult schema.
"""

    response = await self.gemini_client.generate_content(
        prompt,
        generation_config={
            'response_mime_type': 'application/json',
            'response_schema': GlobalCodingResult,
            'max_output_tokens': 60000,
            'temperature': 0.3
        }
    )
    
    return GlobalCodingResult.parse_raw(response.text)
```

### Step 3: Refinement for Traceability (Call 2)
```python
async def refine_for_traceability(self, initial_result: GlobalCodingResult) -> EnhancedResult:
    """Second LLM call to enhance traceability and quote chains"""
    
    prompt = f"""
Enhance this qualitative analysis with FULL TRACEABILITY and QUOTE CHAINS.

Initial Analysis:
{initial_result.model_dump_json(indent=2)}

ENHANCEMENT TASKS:
1. **QUOTE CHAINS**: For each major theme, create chains showing:
   - Initial mention → Development → Contradictions → Resolution
   - Which interviews contain each part of the chain
   - How concepts evolved across the dataset

2. **CODE PROGRESSION**: For key codes, show:
   - First appearance (interview number)
   - How definition evolved
   - Peak frequency period
   - Final stabilization

3. **STAKEHOLDER MAPPING**: Create clear position matrix:
   - Who supports/opposes each major theme
   - Evidence quotes for each position
   - Contradictions between stakeholders

4. **TRACEABILITY**: Ensure every insight can be traced to specific:
   - Interview numbers
   - Line numbers (approximate)
   - Exact quotes
   - Supporting evidence

Return enhanced analysis with complete CSV export data and markdown report content.
"""

    response = await self.gemini_client.generate_content(
        prompt,
        generation_config={
            'response_mime_type': 'application/json',
            'response_schema': EnhancedResult,
            'max_output_tokens': 60000,
            'temperature': 0.2  # Lower temperature for precise traceability
        }
    )
    
    return EnhancedResult.parse_raw(response.text)
```

---

## 📋 Data Models for Global Analysis

### Global Analysis Models
```python
# qc/models/comprehensive_analysis_models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class GlobalCode(BaseModel):
    """Code identified across entire dataset"""
    id: str = Field(description="Unique code identifier")
    name: str = Field(description="Descriptive code name")
    definition: str = Field(description="What this code represents")
    frequency: int = Field(description="Total occurrences across all interviews")
    interviews_present: List[str] = Field(description="Interview IDs where this code appears")
    key_quotes: List[str] = Field(description="Most representative quotes")
    first_appearance: str = Field(description="Interview where first mentioned")
    evolution_notes: str = Field(description="How this code developed across dataset")

class CrossInterviewTheme(BaseModel):
    """Theme that spans multiple interviews"""
    id: str = Field(description="Unique theme identifier")
    name: str = Field(description="Theme name")
    description: str = Field(description="What this theme represents")
    codes: List[str] = Field(description="Code IDs that belong to this theme")
    prevalence: int = Field(description="Number of interviews containing this theme")
    quote_chain: List[str] = Field(description="Chain of quotes showing theme development")
    contradictions: List[str] = Field(description="Opposing viewpoints on this theme")
    stakeholder_positions: Dict[str, str] = Field(description="Who supports/opposes this theme")

class TheoricalSaturationAssessment(BaseModel):
    """Assessment of when theoretical saturation occurred"""
    saturation_point: int = Field(description="Interview number where saturation reached")
    evidence: str = Field(description="Why saturation occurred at this point")
    new_codes_per_interview: List[int] = Field(description="New codes found in each interview")
    stabilization_indicators: List[str] = Field(description="Signs that theory stabilized")

class GlobalCodingResult(BaseModel):
    """Complete result from global analysis"""
    study_id: str = Field(description="Unique identifier for this analysis")
    interviews_analyzed: int = Field(description="Total interviews processed")
    total_tokens_analyzed: int = Field(description="Token count of entire dataset")
    
    # Core findings
    themes: List[CrossInterviewTheme] = Field(description="Major themes across dataset")
    codes: List[GlobalCode] = Field(description="All codes with global context")
    quote_chains: List[QuoteChain] = Field(description="Sequences showing idea development")
    contradictions: List[ContradictionPair] = Field(description="Opposing viewpoints found")
    stakeholder_positions: List[StakeholderPosition] = Field(description="Position mapping")
    
    # Methodology assessment
    saturation_assessment: TheoricalSaturationAssessment = Field(description="When saturation occurred")
    theoretical_insights: List[str] = Field(description="Key theoretical discoveries")
    methodological_notes: str = Field(description="Notes on analysis process")
    
    # Processing metadata
    processing_time_seconds: float = Field(description="Total analysis time")
    llm_calls_used: int = Field(description="Number of LLM calls (should be 1)")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Overall confidence in analysis")

class EnhancedResult(BaseModel):
    """Enhanced result with full traceability"""
    global_analysis: GlobalCodingResult = Field(description="Original global analysis")
    
    # Enhanced traceability
    csv_export_data: Dict[str, List[Dict]] = Field(description="Data for all CSV tables")
    markdown_report: str = Field(description="Complete markdown report with quote chains")
    traceability_matrix: Dict[str, List[str]] = Field(description="Theme -> Quote -> Interview mapping")
    
    # Quality metrics
    traceability_completeness: float = Field(ge=0.0, le=1.0, description="% of findings with full traceability")
    quote_chain_coverage: float = Field(ge=0.0, le=1.0, description="% of themes with quote chains")
    stakeholder_coverage: float = Field(ge=0.0, le=1.0, description="% of participants mapped")
```

---

## 🧪 Testing Strategy

### Day 1: Proof of Concept
```python
# Test with 10 interviews first
async def test_small_sample():
    analyzer = GlobalQualitativeAnalyzer()
    sample_files = interview_files[:10]
    
    result = await analyzer.analyze_global(sample_files)
    
    # Quality checks
    assert len(result.themes) > 0
    assert len(result.codes) > 0
    assert result.confidence_score > 0.7
    assert result.llm_calls_used == 2
```

### Day 2: Full Analysis
```python
# Test with all 103 interviews
async def test_full_dataset():
    analyzer = GlobalQualitativeAnalyzer()
    all_files = load_all_interview_files()
    
    result = await analyzer.analyze_global(all_files)
    
    # Export tests
    csv_exports = analyzer.export_all_csv(result)
    markdown_report = analyzer.export_markdown(result)
    
    # Store in Neo4j for graph queries
    neo4j_client.store_global_result(result)
```

---

## ✅ Success Criteria

### Quality Metrics:
- [ ] **Themes identified**: Should find 8-15 major themes
- [ ] **Quote chains present**: Each theme has progression of quotes
- [ ] **Contradictions identified**: Opposing viewpoints with evidence
- [ ] **Traceability complete**: Every finding traceable to specific interviews
- [ ] **Saturation assessment**: Clear point where new insights stopped

### Efficiency Metrics:
- [ ] **Total LLM calls**: 2 (vs 330+ for systematic approach)
- [ ] **Processing time**: <2 hours for full analysis
- [ ] **Token usage**: <1M tokens total input
- [ ] **Development time**: Complete system in 2-3 days

### Fallback Criteria:
If LLM-native approach fails on any quality metric, fall back to systematic three-phase approach with 36-40 LLM calls (batched by phase).

---

## 🎯 Implementation Priority

1. **Day 1**: Build and test with 10 interviews
2. **Day 2**: Scale to all 103 interviews 
3. **Day 3**: Export CSV/Markdown, store in Neo4j
4. **Days 4-5**: Compare quality with systematic approach (if needed)

The goal is to leverage LLM's global processing advantage rather than artificially constraining it to human-style sequential processing.