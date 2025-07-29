# TDD Test Definition Readiness Assessment

## 🎯 The 3-Phase Coding Process Explained

Looking at `qualitative_coding_extractor.py`, we have three distinct prompts:

### Phase 1: OPEN CODING
```python
OPEN_CODING_PROMPT = """
STEP 1 - OPEN CODING:
1. Read the entire transcript carefully
2. Identify meaningful segments that relate to experiences, feelings, challenges, strategies
3. Assign descriptive codes to these segments
4. Write analytical memos explaining WHY each code was applied
"""
```
**Purpose**: Initial code discovery from raw data. Like highlighting meaningful passages.

### Phase 2: AXIAL CODING  
```python
AXIAL_CODING_PROMPT = """
1. Group related codes into substantive categories
2. Identify properties and dimensions of each category
3. Find relationships between categories (causal, contextual, intervening)
4. Develop each category with:
   - Conditions (what leads to it)
   - Consequences (what results from it)
   - Strategies (how people deal with it)
"""
```
**Purpose**: Organize codes into categories, find relationships.

### Phase 3: SELECTIVE CODING
```python
SELECTIVE_CODING_PROMPT = """
1. The CENTRAL phenomenon that ties everything together
2. How all other categories relate to this core category
3. The overall theoretical story the data tells
4. Key theoretical insights
"""
```
**Purpose**: Identify the core category that explains the main story.

### The Three-Phase Implementation: THREE SEPARATE LLM CALLS

**Corrected Understanding**: Each phase is a separate LLM call for proper grounded theory methodology:

```python
# Phase 1: Open Coding - Discover initial codes
open_codes = await gemini_client.open_coding(
    interview_text, 
    research_question,
    max_output_tokens=60000
)

# Phase 2: Axial Coding - Build categories and relationships  
categories = await gemini_client.axial_coding(
    interview_text,
    open_codes=open_codes,
    existing_codebook=existing_codebook,
    max_output_tokens=60000
)

# Phase 3: Selective Coding - Identify core category
themes = await gemini_client.selective_coding(
    interview_text,
    categories=categories, 
    existing_codebook=existing_codebook,
    max_output_tokens=60000
)
```

**Why Three Calls**:
- Each phase builds on the previous
- Allows for iterative refinement
- Follows proper grounded theory methodology
- Each phase can use different prompting strategies

---

## 📊 Batching Approach Clarification

You're right - I misunderstood. The approach is:

1. **Batch 1**: Process N interviews → Extract initial codes
2. **Aggregate**: Merge similar codes into codebook v1
3. **Batch 2**: Process next N interviews WITH codebook v1 context → New + refined codes
4. **Aggregate**: Update to codebook v2
5. **Continue** until saturation or limits

This makes sense! Each batch builds on previous discoveries.

---

## ✅ ARE WE READY TO DEFINE TESTS?

### What We Know Well Enough to Test:

**1. Data Structures** ✓
```python
def test_interview_object_creation():
    """Test Interview dataclass with all required fields"""
    interview = Interview(
        id="test_001",
        content="Interview text here",
        estimated_tokens=1500,
        # etc.
    )
    assert interview.estimated_tokens == int(interview.word_count * 1.3)

def test_theme_hierarchy():
    """Test Theme → Category → Code → Segment structure"""
    # We know this structure from QC extractor
```

**2. JSON Response Format** ✓
```python
def test_gemini_json_response_format():
    """Test that response_mime_type='application/json' returns valid JSON"""
    # This is well-defined enough to test
    
def test_json_schema_compliance():
    """Test response matches QualitativeCodingResult schema"""
    # We have the schema from the extractor
```

**3. Error Handling** ✓
```python
def test_llm_timeout_handling():
    """Test retry logic with exponential backoff"""
    # We know the error types and retry strategy

def test_malformed_json_recovery():
    """Test extraction from partial/malformed JSON"""
    # Recovery strategies are defined
```

**4. Configuration** ✓
```python
def test_config_loading_precedence():
    """Test env vars → config file → defaults precedence"""
    # Clear from cli_config.py
```

### What We Need to Clarify Before Writing Tests:

**1. LLM-Driven Interview Parser** ✅ **CLARIFIED**
```python
def test_llm_speaker_identification():
    """Test LLM-based speaker identification"""
    # LLM analyzes text and identifies speakers intelligently
    # Handles all formats: "Name:", "[Speaker]", context clues
    
def test_llm_quote_location_mapping():
    """Test LLM mapping quotes back to sources"""
    # LLM finds exact locations and provides context
    # More intelligent than simple line counting
```

**2. LLM-Driven Codebook Evolution** ✅ **CLARIFIED**
```python
def test_llm_codebook_evolution():
    """Test LLM-based codebook evolution"""
    # LLM makes intelligent decisions about code similarity
    # Considers semantic meaning, not just string matching
    
def test_llm_saturation_assessment():
    """Test LLM assessment of theoretical saturation"""
    # LLM evaluates whether new data adds theoretical insights
    # More nuanced than simple percentage thresholds
```

**3. LLM-Driven Batch Processing** ✅ **CLARIFIED**  
```python
def test_batch_with_llm_codebook_context():
    """Test processing batch with LLM-managed codebook context"""
    # LLM receives previous codebook as structured context
    # Makes decisions about incorporating existing knowledge
```

---

## 🎯 TDD Approach Assessment

### TDD is GOOD Here Because:
1. **Complex integrations** - Tests ensure components work together
2. **Critical correctness** - QC research needs accuracy
3. **Clear specifications** - We mostly know what correct behavior is
4. **Regression prevention** - Tests catch breaking changes

### But We Need "Pragmatic TDD":
1. **Test the critical path first** - Interview → Themes → Report
2. **Mock expensive operations** - Don't call Gemini in every test
3. **Test behavior, not implementation** - Focus on outcomes
4. **Allow learning** - Some tests will evolve as we learn

---

## 📋 Recommended Test Definition Order

### Phase 1: Unit Tests We Can Write NOW
```python
# 1. Data structure tests
test_interview_object_creation()
test_theme_hierarchy_structure()
test_error_classification()

# 2. Configuration tests  
test_config_loading()
test_environment_validation()

# 3. Mock-based extraction tests
test_extractor_with_mock_gemini()
test_json_response_parsing()
```

### Phase 2: Integration Tests (Need Some Clarification)
```python
# 1. Parser tests (need speaker strategy)
test_docx_parsing()
test_speaker_extraction()

# 2. Codebook tests (need merge strategy)
test_codebook_evolution()
test_code_merging()
```

### Phase 3: End-to-End Tests (After Basics Work)
```python
# Real Gemini calls
test_single_interview_extraction()
test_batch_processing_with_saturation()
```

---

## ✅ Readiness Verdict: READY WITH CAVEATS

**We ARE ready to start TDD** for:
- Data structures
- Configuration
- Error handling
- Basic extraction flow (with mocks)

**We NEED quick decisions on**:
1. **Speaker handling**: Simple rule like "Name:" at line start = speaker?
2. **Code merging**: Exact string match for now, improve later?
3. **Saturation metric**: <10% new codes = saturated?

**Recommended approach**:
1. Start with tests we can write now
2. Make simple decisions for unclear areas
3. Write tests for those decisions
4. Refine as we learn

The key is to start with what we know and iterate, rather than waiting for perfect clarity on everything.