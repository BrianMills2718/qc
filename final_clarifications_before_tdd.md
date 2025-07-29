# Final Clarifications Before TDD Implementation

## 🔍 Critical Unknowns That Must Be Resolved

### 1. **Data Structure Specifications - INCOMPLETE**

**Issue**: We have conceptual models but not concrete data structures for each phase.

**Missing Specifications**:
```python
# What exactly does OpenCodingResult contain?
@dataclass
class OpenCodingResult:
    codes: List[???]  # What structure?
    segments: List[???]  # How are quotes linked?
    memos: List[???]  # What format?
    # ???

# How do phases connect?
class AxialCodingResult:
    categories: List[???]  # How do these relate to OpenCodingResult?
    relationships: List[???]  # What structure for relationships?
    # ???

class SelectiveCodingResult:
    core_category: ???  # String? Object? 
    theory: ???  # How is theory represented?
    # ???
```

**MUST DEFINE**: Exact JSON schemas for each phase result before writing tests.

### 2. **LLM Response Format Contracts - UNCLEAR**

**Issue**: How do we ensure LLM responses match our expected schemas?

**Critical Questions**:
```python
# Do we use Pydantic models in prompts?
prompt = f"""
Return JSON matching this schema:
{OpenCodingResult.model_json_schema()}
"""

# Or describe structure in natural language?
prompt = f"""
Return JSON with this structure:
- codes: array of code objects with name, definition, segments
- memos: array of analytical memos
"""

# How do we handle schema validation failures?
try:
    result = OpenCodingResult.parse_raw(llm_response)
except ValidationError:
    # What's the recovery strategy?
```

**MUST DECIDE**: Schema communication and validation approach.

### 3. **Error Recovery Strategies - VAGUE**

**Issue**: "Use robust error handling" isn't specific enough for TDD.

**Specific Scenarios Needing Clear Strategies**:
```python
# Scenario 1: Phase 2 fails, Phase 1 succeeded
def test_axial_coding_failure_recovery():
    # Do we retry just Phase 2?
    # Do we restart from Phase 1?
    # Do we return partial results?
    pass

# Scenario 2: JSON partially valid
def test_partial_json_recovery():
    response = '{"codes": [{"name": "trust_issues"}]}'  # Incomplete
    # Do we accept partial results?
    # Do we retry with more specific prompt?
    # Do we fail the entire interview?
    pass

# Scenario 3: LLM returns completely wrong format
def test_wrong_format_recovery():
    response = "I think the main themes are trust and communication..."  # Not JSON
    # How many retries?
    # Do we adjust the prompt?
    # Do we try different temperature?
    pass
```

**MUST SPECIFY**: Exact recovery strategy for each error type.

### 4. **Codebook Context Passing - UNDEFINED**

**Issue**: How exactly does codebook context get passed between batches?

**Critical Implementation Details**:
```python
# How is existing codebook formatted in prompts?
def format_codebook_for_prompt(codebook: Codebook) -> str:
    # Option A: Full JSON dump
    return codebook.to_json()
    
    # Option B: Structured summary
    return f"""
    Existing themes: {[theme.name for theme in codebook.themes]}
    Existing codes: {[code.name for code in codebook.all_codes]}
    """
    
    # Option C: Examples-based
    return f"""
    Here are examples of existing codes:
    {codebook.get_examples()}
    """

# How does LLM incorporate this context?
# Do we give explicit instructions about using existing codes?
# Do we let LLM decide when to create new vs use existing?
```

**MUST DEFINE**: Exact format and instructions for codebook context.

### 5. **Test Data Requirements - MISSING**

**Issue**: We need realistic test data to write meaningful tests.

**Required Test Data**:
```python
# What format are our test interviews?
test_interviews = {
    "simple_individual": {
        "format": "speaker_labels",  # "Alice: I think..."
        "length": "short",  # <1000 words
        "content": "???",  # Actual interview text
    },
    "complex_focus_group": {
        "format": "timestamps",  # "[00:15:23] Participant A:"
        "length": "long",  # >5000 words
        "content": "???",
    },
    "notes_format": {
        "format": "unstructured",  # Just paragraphs
        "length": "medium",
        "content": "???",
    }
}
```

**MUST CREATE**: Realistic test interview data in multiple formats.

### 6. **Performance Expectations - UNSPECIFIED**

**Issue**: No concrete performance targets for tests.

**Need Benchmarks**:
```python
def test_performance_requirements():
    # How long should each phase take?
    assert open_coding_time < ???  # 30 seconds? 2 minutes?
    
    # How much does 3-phase cost?
    assert total_tokens_used < ???  # 100K? 500K? per interview
    
    # Memory usage acceptable?
    assert memory_usage < ???  # 1GB? 500MB?
    
    # Batch processing speed?
    assert batch_of_5_interviews < ???  # 10 minutes? 30 minutes?
```

**MUST SET**: Realistic performance targets based on Gemini capabilities.

### 7. **Integration Test Boundaries - FUZZY**

**Issue**: Where do unit tests end and integration tests begin?

**Boundary Questions**:
```python
# Is this a unit test or integration test?
def test_open_coding():
    result = await qc_pipeline.open_coding(interview_text, research_question)
    # This calls Gemini API - integration?
    # Or do we mock Gemini - unit?

# How do we test 3-phase integration without 3x API costs?
def test_three_phase_flow():
    # Mock all LLM calls?
    # Use real API with test credits?
    # Use cached responses?
```

**MUST DECIDE**: Testing strategy for LLM-dependent code.

### 8. **Configuration Test Requirements - INCOMPLETE**

**Issue**: How thoroughly do we test configuration scenarios?

**Configuration Test Scenarios**:
```python
# Do we test all environment variable combinations?
def test_config_matrix():
    scenarios = [
        {"GEMINI_MODEL": "gemini-2.5-flash", "QC_BATCH_SIZE": "3"},
        {"GEMINI_MODEL": "gemini-1.5-pro", "QC_BATCH_SIZE": "5"},
        # Test all combinations?
    ]

# How do we test missing vs invalid vs default configs?
def test_invalid_config_handling():
    # What should happen with invalid batch size?
    # What about missing API key?
    # Invalid research question format?
```

**MUST SPECIFY**: Configuration testing scope and expected behaviors.

### 9. **Mocking Strategy - UNDEFINED**

**Issue**: How do we mock LLM responses for deterministic tests?

**Mocking Approach Options**:
```python
# Option A: Mock at HTTP level
@patch('google.genai.Client.generate_content')
def test_with_http_mock(mock_generate):
    mock_generate.return_value = MockResponse('{"codes": [...]}')

# Option B: Mock at client level  
@patch('qc.core.simple_gemini_client.SimpleGeminiExtractor.extract')
def test_with_client_mock(mock_extract):
    mock_extract.return_value = OpenCodingResult(...)

# Option C: Dependency injection
class TestableQCPipeline(QCPipeline):
    def __init__(self, mock_client):
        self.gemini_client = mock_client
```

**MUST CHOOSE**: Mocking level and implementation approach.

### 10. **Test Organization Strategy - UNCLEAR**

**Issue**: How do we organize tests for complex multi-phase system?

**Test Structure Questions**:
```python
# File organization?
tests/
├── unit/
│   ├── test_open_coding.py      # Just Phase 1?
│   ├── test_axial_coding.py     # Just Phase 2?
│   ├── test_selective_coding.py # Just Phase 3?
│   └── test_data_structures.py  # Models?
├── integration/
│   ├── test_three_phase_flow.py # All phases together?
│   ├── test_batch_processing.py # Multi-interview?
│   └── test_codebook_evolution.py # Cross-batch?
└── e2e/
    └── test_full_pipeline.py    # File to report?

# Test data sharing strategy?
# Fixtures for each phase?
# How to chain phase outputs for testing?
```

**MUST PLAN**: Test file organization and data sharing approach.

---

## 🎯 Required Decisions Summary

### CRITICAL (Must resolve before any coding):
1. **Data Structure Schemas** - Exact JSON format for each phase
2. **LLM Response Contracts** - How to ensure schema compliance
3. **Error Recovery Strategies** - Specific actions for each failure type
4. **Test Data Creation** - Realistic interview samples
5. **Mocking Strategy** - How to test LLM-dependent code

### IMPORTANT (Can start with simple approach):
6. **Codebook Context Format** - How context passes between batches
7. **Performance Targets** - Reasonable benchmarks for tests
8. **Integration Boundaries** - Unit vs integration test scope
9. **Configuration Testing** - How thorough to be
10. **Test Organization** - File structure and data sharing

---

## 📋 Recommended Resolution Process

### Day 1: Data Structure Definition (4 hours)
1. **Define exact schemas** for OpenCodingResult, AxialCodingResult, SelectiveCodingResult
2. **Create Pydantic models** with validation
3. **Write schema compliance prompts** for LLM
4. **Test schema parsing** with sample JSON

### Day 2: Error Handling Specification (4 hours)
1. **List all possible failure points** in 3-phase process
2. **Define recovery strategy** for each error type
3. **Create error handling test cases**
4. **Implement basic error recovery logic**

### Day 3: Test Data & Mocking (4 hours)
1. **Create realistic test interviews** (3-4 different formats)
2. **Choose mocking approach** and implement
3. **Create test fixtures** for each phase
4. **Validate test data works with schemas**

### Day 4: Test Structure Planning (2 hours)
1. **Organize test files** and decide boundaries
2. **Set performance benchmarks** (reasonable estimates)
3. **Plan configuration testing** approach
4. **Create test execution strategy**

**ONLY THEN**: Start writing actual TDD tests.

## ❌ We Are NOT Ready for TDD Yet

The framework looks solid, but we have too many undefined implementation details. TDD requires knowing exactly what "correct" behavior looks like - we still have too many "???" in our specifications.

**Recommendation**: Spend 3-4 days on detailed specification, then begin TDD with confidence.