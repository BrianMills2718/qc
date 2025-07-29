# Test-Driven Development Implementation Plan
## Systematic Approach for Qualitative Coding System

---

## 🎯 TDD Strategy Overview

### Core Principles
1. **Interface-First Design** - Define all contracts before implementation
2. **Test Specifications First** - Write comprehensive test suites before any code
3. **Bottom-Up Testing** - Unit → Integration → End-to-End
4. **Continuous Validation** - Every component tested in isolation and integration

### Testing Hierarchy
```
End-to-End Tests (CLI → Full Pipeline → Output Files)
           ↑
Integration Tests (Module Boundaries & Data Flow) 
           ↑
Unit Tests (Individual Functions & Classes)
           ↑
Interface Contracts (Type Definitions & Protocols)
```

---

## 📋 Phase 1: Interface Definition & Contracts

### 1.1 Core Data Contracts
**File**: `qc/contracts/data_contracts.py`

```python
from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

# === CORE DATA STRUCTURES ===

@dataclass
class Theme:
    """Top-level thematic concept"""
    id: str
    name: str
    description: str
    categories: List['Category']
    prevalence: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    memos: List['AnalyticalMemo']

@dataclass 
class Category:
    """Mid-level grouping within themes"""
    id: str
    name: str
    description: str
    parent_theme_id: str
    codes: List['Code']
    prevalence: float

@dataclass
class Code:
    """Specific coding instance"""
    id: str
    name: str
    definition: str
    category_id: str
    quotes: List['Quote']
    frequency: int
    confidence: float

@dataclass
class Quote:
    """Supporting evidence from interviews"""
    text: str
    interview_id: str
    participant_id: str
    line_number: Optional[int]
    context: str

@dataclass
class AnalyticalMemo:
    """Researcher insights and theoretical development"""
    id: str
    content: str
    theme_id: str
    timestamp: float
    memo_type: str  # "theoretical", "methodological", "analytical"

@dataclass
class Interview:
    """Processed interview with metadata"""
    id: str
    title: str
    participant_id: str
    interview_type: str  # "individual", "focus_group"
    content: str
    metadata: Dict[str, Any]
    processing_status: str

@dataclass
class QCResult:
    """Complete qualitative coding result"""
    session_id: str
    themes: List[Theme]
    interviews_processed: List[str]
    total_codes: int
    confidence_metrics: Dict[str, float]
    processing_metadata: Dict[str, Any]
```

### 1.2 Processing Contracts
**File**: `qc/contracts/processing_contracts.py`

```python
# === PROCESSING INTERFACES ===

class LLMClientProtocol(Protocol):
    """Contract for LLM integration"""
    
    async def extract_themes(self, content: str, 
                           existing_codebook: Optional[Dict] = None) -> QCResult:
        """Extract themes from interview content"""
        ...
    
    async def validate_themes(self, themes: List[Theme]) -> Dict[str, Any]:
        """Validate theme hierarchy consistency"""
        ...
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Return token usage and performance metrics"""
        ...

class DocumentParserProtocol(Protocol):
    """Contract for document processing"""
    
    def parse_interview(self, file_path: str) -> Interview:
        """Parse interview document to structured format"""
        ...
    
    def validate_content(self, content: str) -> Dict[str, Any]:
        """Validate interview content quality"""
        ...

class BatchProcessorProtocol(Protocol):
    """Contract for batch processing"""
    
    async def process_batch(self, interviews: List[Interview], 
                          config: 'AnalysisConfig') -> QCResult:
        """Process multiple interviews concurrently"""
        ...
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current processing progress"""
        ...

class OutputGeneratorProtocol(Protocol):
    """Contract for output generation"""
    
    def generate_report(self, result: QCResult, 
                       format: str = "markdown") -> str:
        """Generate analysis report"""
        ...
    
    def generate_policy_brief(self, result: QCResult) -> str:
        """Generate policy-focused brief"""
        ...
    
    def detect_contradictions(self, result: QCResult) -> List[Dict]:
        """Identify contradictory themes"""
        ...
```

### 1.3 Error & Result Contracts  
**File**: `qc/contracts/result_contracts.py`

```python
# === ERROR HANDLING & RESULTS ===

@dataclass
class ProcessingError:
    """Standardized error representation"""
    error_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    context: Dict[str, Any]
    recovery_suggestion: str
    timestamp: float

@dataclass  
class ProcessingResult:
    """Standard result wrapper"""
    success: bool
    data: Any = None
    errors: List[ProcessingError] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    processing_time: float = 0.0
    
    def add_error(self, error_type: str, severity: str, message: str, 
                  context: Dict = None, suggestion: str = ""):
        if not self.errors:
            self.errors = []
        self.errors.append(ProcessingError(
            error_type=error_type, severity=severity, message=message,
            context=context or {}, recovery_suggestion=suggestion,
            timestamp=time.time()
        ))
        if severity in ["high", "critical"]:
            self.success = False

@dataclass
class ValidationResult:
    """Validation outcome with details"""
    is_valid: bool
    issues: List[str] = None
    warnings: List[str] = None
    quality_score: float = 1.0
    recommendations: List[str] = None
```

---

## 📝 Phase 2: Comprehensive Test Specifications

### 2.1 Unit Test Specifications
**File**: `tests/specifications/unit_test_specs.md`

#### Infrastructure Layer Tests
```python
# tests/unit/test_infrastructure.py

class TestConfigManager:
    def test_secret_str_handling():
        """Verify API keys are properly secured"""
        
    def test_environment_validation():
        """Test missing/invalid env vars are caught"""
        
    def test_configuration_persistence():
        """Test save/load configuration files"""

class TestErrorHandling:
    def test_error_classification():
        """Verify errors are properly categorized by severity"""
        
    def test_retry_logic():
        """Test exponential backoff and retry limits"""
        
    def test_error_context_preservation():
        """Ensure error context is maintained through call stack"""

class TestInputValidator:
    def test_injection_protection():
        """Test XSS/SQL injection pattern detection"""
        
    def test_content_sanitization():
        """Verify malicious content is cleaned"""
        
    def test_file_validation():
        """Test file type and size validation"""

class TestStructuredLogger:
    def test_json_log_format():
        """Verify logs are properly structured JSON"""
        
    def test_correlation_tracking():
        """Test correlation IDs propagate through operations"""
        
    def test_performance_metrics():
        """Verify timing and performance data is captured"""

class TestLLMContentExtractor:
    def test_multi_provider_parsing():
        """Test response parsing for OpenAI, Gemini, Claude"""
        
    def test_malformed_response_recovery():
        """Test recovery from partial/malformed JSON"""
        
    def test_content_extraction_fallbacks():
        """Test multiple extraction strategies"""
```

#### QC Core Tests
```python
# tests/unit/test_qc_core.py

class TestQCModels:
    def test_theme_hierarchy_creation():
        """Test Theme → Category → Code hierarchy"""
        
    def test_analytical_memo_linking():
        """Test memo association with themes"""
        
    def test_quote_attribution():
        """Test quote linking to interviews and participants"""
        
    def test_confidence_score_validation():
        """Test confidence scores are 0.0-1.0"""

class TestQualitativeCodingExtractor:
    def test_three_phase_extraction():
        """Test Phase 1: Discovery → Phase 2: Organization → Phase 3: Validation"""
        
    def test_theme_saturation_detection():
        """Test when new themes stop emerging"""
        
    def test_grounded_theory_development():
        """Test theoretical insight generation"""
        
    def test_codebook_evolution():
        """Test how codebook changes with new interviews"""
        
    def test_empty_content_handling():
        """Test behavior with empty/minimal content"""
        
    def test_large_content_chunking():
        """Test handling of content exceeding token limits"""

class TestThemeAnalyzer:
    def test_co_occurrence_analysis():
        """Test themes appearing together in interviews"""
        
    def test_frequency_calculation():
        """Test code frequency and prevalence metrics"""
        
    def test_contradiction_detection():
        """Test identification of conflicting themes"""
        
    def test_quality_metrics():
        """Test confidence, coverage, and saturation metrics"""
```

#### LLM Integration Tests
```python
# tests/unit/test_llm_integration.py

class TestUniversalLLMClient:
    def test_fallback_chain():
        """Test Gemini → Claude → OpenAI fallback"""
        
    def test_retry_with_backoff():
        """Test retry logic with exponential backoff"""
        
    def test_usage_tracking():
        """Test token counting and rate limiting"""
        
    def test_provider_health_monitoring():
        """Test detection of provider failures"""

class TestGeminiClient:
    def test_2_5_flash_integration():
        """Test Gemini 2.5 Flash API calls"""
        
    def test_token_optimization():
        """Test 1M context / 60K output handling"""
        
    def test_response_format_handling():
        """Test parsing Gemini-specific response formats"""
        
    def test_rate_limit_compliance():
        """Test adherence to Gemini rate limits"""

class TestResponseParser:
    def test_qc_specific_json_parsing():
        """Test parsing of theme hierarchy JSON"""
        
    def test_partial_response_recovery():
        """Test handling of truncated responses"""
        
    def test_quality_validation():
        """Test validation of extracted theme quality"""
        
    def test_format_standardization():
        """Test conversion to standard QC data structures"""
```

### 2.2 Integration Test Specifications
**File**: `tests/specifications/integration_test_specs.md`

#### Module Boundary Tests
```python
# tests/integration/test_module_boundaries.py

class TestInfrastructure_LLM_Integration:
    def test_error_handling_propagation():
        """Test errors flow properly from LLM to infrastructure"""
        
    def test_logging_correlation():
        """Test correlation IDs track across module calls"""
        
    def test_config_usage():
        """Test LLM layer uses infrastructure configuration"""

class TestLLM_QCCore_Integration:
    def test_extraction_pipeline():
        """Test full extraction: LLM calls → QC models"""
        
    def test_error_recovery():
        """Test QC core handles LLM failures gracefully"""
        
    def test_result_transformation():
        """Test LLM responses become QC data structures"""

class TestQCCore_Processing_Integration:
    def test_batch_theme_extraction():
        """Test multiple interviews processed through QC core"""
        
    def test_progress_tracking():
        """Test processing progress propagated correctly"""
        
    def test_partial_result_aggregation():
        """Test combining results from multiple interviews"""

class TestProcessing_Interface_Integration:
    def test_cli_workflow_execution():
        """Test CLI commands trigger processing workflows"""
        
    def test_user_feedback_display():
        """Test progress and results shown to user"""
        
    def test_error_user_presentation():
        """Test errors presented in user-friendly format"""

class TestQCCore_Output_Integration:
    def test_theme_hierarchy_formatting():
        """Test QC results formatted for reports"""
        
    def test_multi_format_export():
        """Test same data exported as Markdown, JSON, CSV"""
        
    def test_policy_brief_generation():
        """Test policy-focused analysis from themes"""
```

#### End-to-End Workflow Tests
```python
# tests/integration/test_e2e_workflows.py

class TestSingleInterviewWorkflow:
    def test_docx_to_markdown_report():
        """Test: DOCX input → theme extraction → Markdown report"""
        
    def test_error_recovery_workflow():
        """Test workflow continues despite individual failures"""
        
    def test_confidence_threshold_filtering():
        """Test low-confidence themes are filtered appropriately"""

class TestBatchProcessingWorkflow:
    def test_multiple_interviews_aggregation():
        """Test: Multiple DOCXs → aggregated theme analysis"""
        
    def test_session_resume_capability():
        """Test processing can resume after interruption"""
        
    def test_parallel_processing_correctness():
        """Test concurrent processing produces correct results"""

class TestConfigurationWorkflow:
    def test_yaml_config_override():
        """Test YAML config overrides CLI arguments"""
        
    def test_environment_validation():
        """Test missing env vars are caught before processing"""
        
    def test_output_directory_creation():
        """Test output directories created automatically"""
```

### 2.3 End-to-End Test Specifications
**File**: `tests/specifications/e2e_test_specs.md`

#### Complete System Tests
```python
# tests/e2e/test_complete_system.py

class TestRealWorldUsage:
    def test_researcher_workflow():
        """Test complete researcher workflow with real interview data"""
        # Setup: 6 RAND interview files from fixtures/
        # Execute: Full CLI processing pipeline
        # Validate: Meaningful themes extracted, quality reports generated
        
    def test_policy_analyst_workflow():
        """Test policy-focused analysis workflow"""
        # Setup: Policy-relevant interview content
        # Execute: Enable policy brief generation 
        # Validate: Actionable recommendations produced
        
    def test_large_dataset_processing():
        """Test system with 20+ interviews"""
        # Setup: Large interview dataset
        # Execute: Batch processing with concurrency
        # Validate: Performance, memory usage, result quality

class TestErrorRecoveryScenarios:
    def test_network_interruption_recovery():
        """Test system handles API failures gracefully"""
        
    def test_malformed_document_handling():
        """Test corrupted/invalid documents don't crash system"""
        
    def test_disk_space_exhaustion():
        """Test graceful handling of storage limitations"""

class TestPerformanceRequirements:
    def test_processing_speed_requirements():
        """Test system meets performance benchmarks"""
        # Requirement: <2 minutes per interview for Gemini 2.5 Flash
        
    def test_memory_usage_constraints():
        """Test system respects memory limitations"""
        # Requirement: <2GB RAM for 10 concurrent interviews
        
    def test_token_usage_optimization():
        """Test efficient token usage"""
        # Requirement: <300K tokens per interview processing
```

---

## 🏗️ Phase 3: Test-First Implementation Strategy

### 3.1 Implementation Order (Bottom-Up)

#### Week 1: Foundation (Infrastructure + Contracts)
```bash
# Day 1-2: Interface Contracts
tests/unit/test_data_contracts.py          # ✍️ Write tests first
qc/contracts/data_contracts.py             # 🔨 Implement to pass tests

tests/unit/test_processing_contracts.py     # ✍️ Write tests first  
qc/contracts/processing_contracts.py       # 🔨 Implement to pass tests

# Day 3-5: Infrastructure Validation
tests/unit/test_infrastructure.py          # ✍️ Comprehensive test suite
# Infrastructure already exists ✅ - validate with tests
```

#### Week 2: Core Components
```bash
# Day 1-3: QC Core Foundation
tests/unit/test_qc_models.py               # ✍️ Write tests first
qc/models/qc_models.py                     # 🔨 Implement data structures

tests/unit/test_qualitative_coding_extractor.py  # ✍️ Write tests first
# Adapt existing extractor to use new models

# Day 4-5: LLM Integration
tests/unit/test_response_parser.py         # ✍️ Write tests first
qc/llm/response_parser.py                  # 🔨 Implement QC-specific parsing

tests/integration/test_llm_qc_integration.py  # ✍️ Write integration tests
# Test LLM → QC Core boundary
```

#### Week 3: Processing & Interface
```bash
# Day 1-3: Document Processing
tests/unit/test_interview_parser.py        # ✍️ Write tests first
qc/processing/interview_parser.py          # 🔨 Implement document parsing

tests/unit/test_workflow_manager.py        # ✍️ Write tests first
qc/processing/workflow_manager.py          # 🔨 Implement orchestration

# Day 4-5: CLI Integration
tests/integration/test_cli_integration.py  # ✍️ Write integration tests
qc/cli.py                                  # 🔄 Adapt existing CLI

tests/e2e/test_basic_workflows.py          # ✍️ Write E2E tests
```

#### Week 4: Output & Polish
```bash
# Day 1-3: Output Generation
tests/unit/test_report_generator.py        # ✍️ Write tests first
qc/output/report_generator.py              # 🔨 Implement report generation

tests/unit/test_policy_brief_generator.py  # ✍️ Write tests first
qc/output/policy_brief_generator.py        # 🔨 Implement policy briefs

# Day 4-5: Complete System Validation
tests/e2e/test_complete_system.py          # ✍️ Full system tests
# Final integration and performance validation
```

### 3.2 Test Automation Strategy

#### Continuous Testing Setup
```yaml
# .github/workflows/test.yml
name: Comprehensive Testing
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=qc --cov-report=term-missing
      
  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          
  e2e-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run E2E tests
        run: pytest tests/e2e/ -v --slow
```

#### Test Data Management
```python
# tests/fixtures/test_data.py
@pytest.fixture
def sample_interview():
    """Real interview data for testing"""
    return Interview(
        id="test_001",
        title="RAND Methods Alice Huguet",
        participant_id="alice_huguet", 
        interview_type="individual",
        content=load_test_interview("RAND Methods Alice Huguet.docx"),
        metadata={"division": "RAND", "role": "researcher"}
    )

@pytest.fixture
def expected_themes():
    """Expected theme extraction results"""
    return [
        Theme(
            id="theme_001",
            name="AI Integration Challenges",
            description="Challenges in integrating AI into research methods",
            categories=[...],
            confidence=0.85
        )
    ]
```

---

## 🎯 Success Criteria & Validation

### Test Coverage Requirements
- **Unit Tests**: 95% code coverage
- **Integration Tests**: All module boundaries tested
- **E2E Tests**: Complete workflows validated
- **Performance Tests**: Requirements met under load

### Quality Gates
1. **All tests pass** before any code merge
2. **No regression** in existing functionality
3. **Performance benchmarks** met for real-world usage
4. **Documentation** updated with interface changes

### Validation Metrics
- **Processing Speed**: <2 minutes per interview
- **Memory Usage**: <2GB for 10 concurrent interviews  
- **Token Efficiency**: <300K tokens per interview
- **Result Quality**: Meaningful themes with >0.7 confidence

---

This systematic TDD approach ensures we build exactly what we need, with bulletproof interfaces and comprehensive validation. Every component will be tested before implementation, preventing integration issues and ensuring production quality.

Ready to start with Phase 1 interface contracts?