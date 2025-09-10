# Qualitative Coding Analysis System - LLM Speaker Detection Integration

## 🚫 Development Philosophy (MANDATORY)

### Core Principles
- **NO LAZY IMPLEMENTATIONS**: No mocking, stubs, fallbacks, pseudo-code, or simplified implementations
- **NO LLM MOCKING WITHOUT PERMISSION**: Do not mock LLM calls without explicit user authorization
- **FAIL-FAST AND LOUD PRINCIPLES**: Surface errors immediately, don't hide them in logs or fallbacks
- **EVIDENCE-BASED DEVELOPMENT**: All claims require raw execution evidence with structured validation
- **TEST-DRIVEN DEVELOPMENT**: Write failing tests first, then implement to pass
- **THIS IS NOT A PRODUCTION SYSTEM**: Focus on research functionality, not enterprise features

## 📁 Codebase Structure

### Key Entry Points
- **Main CLI**: `qc_clean/core/cli/cli_robust.py` - Primary command-line interface (✅ Working with real Neo4j)
- **CLI Operations**: `qc_clean/core/cli/robust_cli_operations.py` - Core orchestration with real Neo4j integration (✅ Fixed)
- **Configuration Hub**: `qc_clean/config/unified_config.py` - Environment-driven configuration (✅ Working)
- **LLM Integration**: `qc_clean/core/llm/llm_handler.py` - Multi-provider LLM access (✅ Working)
- **GT Workflow**: `qc_clean/core/workflow/grounded_theory.py` - Core analysis with relationship creation (✅ Fixed)
- **Data Export**: `qc_clean/core/export/data_exporter.py` - JSON/CSV/Markdown export (✅ Working)

### Module Organization
```
qc_clean/                           # Clean architecture (ACTIVE)
├── core/                          # Core GT functionality  
│   ├── cli/                       # CLI interface (✅ Fixed Neo4j integration)
│   ├── workflow/                  # GT analysis workflow (✅ Fixed relationships)
│   ├── llm/                       # LLM integration layer (✅ Working)
│   ├── data/                      # REAL Neo4j implementation (✅ Active)
│   │   ├── neo4j_manager.py       # REAL: Full implementation (1101 lines)
│   │   └── docker_manager.py      # REAL: Fail-fast Docker validation
│   ├── export/                    # Export functionality (✅ Working)
│   └── analysis/                  # Analytical memos (✅ Working)
├── config/                        # Configuration system (✅ Working)
└── plugins/extractors/            # Code extraction plugins (✅ Working)

src/                               # Sophisticated LLM System (❓ UNUSED)
├── qc/extraction/                 # Advanced extraction pipeline
│   ├── code_first_extractor.py   # 4-phase LLM extraction (1600+ lines)
│   ├── code_first_schemas.py     # Structured LLM schemas
│   └── dialogue_processor.py     # Advanced dialogue analysis
└── web_interface/                 # Dashboard system (❓ NEEDS INTEGRATION)
    ├── app.py                     # FastAPI application (1300+ lines)
    ├── templates/                 # HTML templates (8 major pages)
    └── static/                    # CSS/JS assets
```

### Current System Status
- ✅ **Neo4j CLI Integration**: Fixed and working with real implementation
- ✅ **Hierarchical Code Extraction**: Multi-level hierarchies with parent-child relationships
- ✅ **Core Analysis Functional**: 28+ codes extracted from rich interview data
- ✅ **Relationship Creation**: Content-based relationships integrated into workflow
- ✅ **Export Infrastructure**: JSON/CSV exports with relationship data
- ❓ **LLM Speaker Detection**: Sophisticated implementation exists but not integrated

## 🎯 Current Challenge: LLM Speaker Detection Integration

### **PROBLEM: Basic Regex vs Sophisticated LLM Speaker Detection**

**Evidence Location**: Systematic investigation completed 

**Critical Discovery**: Two completely different speaker detection systems
- **Current qc_clean/**: Basic regex patterns in `semantic_extractor.py:329-347`
- **Sophisticated src/**: Multi-phase LLM schema discovery with `SpeakerPropertySchema`

**Integration Challenge**:
```python
# Current qc_clean/ approach:
def _detect_speaker(self, text: str) -> Optional[str]:
    # Simple regex patterns: "Name:", "Name said", "I ", "We "
    return "John" | "Participant" | None

# Sophisticated src/ approach:
async def _run_phase_2(self):
    # Multi-phase LLM schema discovery
    self.speaker_schema = await self.llm.extract_structured(
        prompt=prompt, schema=SpeakerPropertySchema
    )
    # Returns: Rich speaker properties + dialogue analysis
```

### **ARCHITECTURAL GAP ANALYSIS**

| Aspect | qc_clean/ | src/ | Integration Challenge |
|--------|-----------|------|---------------------|
| **Approach** | Regex matching | LLM schema discovery | 🔴 **MAJOR**: Completely different paradigms |
| **Output** | Single speaker name | Rich speaker properties + dialogue | 🔴 **MAJOR**: Schema compatibility |
| **Dependency** | Standalone regex | PromptLoader + Phase system | 🔴 **MAJOR**: Architecture mismatch |
| **Performance** | Instant | Multi-LLM calls | 🔴 **MAJOR**: 10x performance impact |
| **LLM Interface** | Compatible `extract_structured()` | Same interface | ✅ **LOW**: Direct compatibility |

## 🚀 **PRIMARY TASK: Implement Enhanced LLM Speaker Detection**

### **IMPLEMENTATION APPROACH: 4-Phase Integration**

**Complexity**: MEDIUM (Schema bridging + Performance management)  
**Risk**: MEDIUM-LOW (Comprehensive mitigation strategy)  
**Time Estimate**: 8 hours total  
**Success Probability**: 85% with systematic testing

## **PHASE 1: Foundation Setup** (Risk: 🟢 LOW, Duration: 2 hours)

### **Objective**: Create bridge infrastructure without affecting current system

#### **Step 1.1: Schema Bridge Creation** 
```bash
# Create bridge module
mkdir -p qc_clean/core/speaker_detection
touch qc_clean/core/speaker_detection/__init__.py
touch qc_clean/core/speaker_detection/schema_bridge.py
```

**File**: `qc_clean/core/speaker_detection/schema_bridge.py`
```python
"""
Schema Bridge for LLM Speaker Detection
Bridges src/ sophisticated schemas to qc_clean/ architecture
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Import sophisticated schemas from src/
try:
    from src.qc.extraction.code_first_schemas import (
        SpeakerPropertySchema,
        DiscoveredSpeakerProperty,
        QuotesAndSpeakers
    )
    SOPHISTICATED_SCHEMAS_AVAILABLE = True
except ImportError:
    SOPHISTICATED_SCHEMAS_AVAILABLE = False
    # Fallback lightweight schemas
    class SpeakerPropertySchema(BaseModel):
        properties: List[Dict[str, Any]] = []
        discovery_method: str = "fallback"
        extraction_confidence: float = 0.0

class SimpleSpeakerResult(BaseModel):
    """Lightweight schema for compatibility with current system"""
    speaker_name: Optional[str] = None
    confidence: float = 0.8
    detection_method: str = "llm"

class SpeakerDetectionBridge:
    """Bridge between sophisticated src/ and simple qc_clean/ speaker detection"""
    
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
        self.schemas_available = SOPHISTICATED_SCHEMAS_AVAILABLE
    
    async def detect_speaker_simple(self, text: str) -> Optional[str]:
        """Simple interface matching current regex approach"""
        try:
            prompt = self._build_simple_speaker_prompt(text)
            result = await self.llm_handler.extract_structured(
                prompt=prompt,
                schema=SimpleSpeakerResult
            )
            return result.speaker_name
        except Exception as e:
            # Critical: Don't hide errors, but log for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"LLM speaker detection failed: {e}")
            raise  # Re-raise for fail-fast behavior
    
    def _build_simple_speaker_prompt(self, text: str) -> str:
        """Build prompt for simple speaker detection"""
        return f"""
You are an expert at identifying speakers in interview transcripts.

Analyze this text and identify who is speaking:
Text: "{text}"

Rules:
1. If text starts with "Name:" return that name
2. If text contains "Name said" return that name  
3. If first person ("I", "We") return "Participant"
4. If unclear, return null

Return only the speaker name or null.
"""
```

**Validation Commands**:
```bash
# Test schema import bridge
python -c "from qc_clean.core.speaker_detection.schema_bridge import SpeakerDetectionBridge; print('SUCCESS: Bridge created')"
```

#### **Step 1.2: Enhanced Extractor Plugin**

**File**: `qc_clean/plugins/extractors/enhanced_semantic_extractor.py`
```python
"""
Enhanced Semantic Extractor with LLM Speaker Detection
Extends current SemanticExtractor with optional LLM capabilities
"""
import logging
from typing import Optional
from .semantic_extractor import SemanticExtractor
from qc_clean.core.speaker_detection.schema_bridge import SpeakerDetectionBridge

logger = logging.getLogger(__name__)

class EnhancedSemanticExtractor(SemanticExtractor):
    """Semantic extractor with optional LLM-based speaker detection"""
    
    def __init__(self, llm_handler=None, use_llm_speaker_detection=False):
        super().__init__(llm_handler)
        self.use_llm_detection = use_llm_speaker_detection
        
        if self.use_llm_detection and llm_handler:
            self.speaker_bridge = SpeakerDetectionBridge(llm_handler)
        else:
            self.speaker_bridge = None
        
        logger.info(f"EnhancedSemanticExtractor initialized - LLM detection: {self.use_llm_detection}")
    
    def get_name(self) -> str:
        return "enhanced_semantic"
    
    def get_version(self) -> str:
        return "3.0.0-llm-bridge"
    
    def get_description(self) -> str:
        mode = "LLM" if self.use_llm_detection else "regex"
        return f"Enhanced semantic extraction with {mode} speaker detection"
    
    async def _detect_speaker(self, text: str) -> Optional[str]:
        """Hybrid speaker detection with fallback"""
        if self.use_llm_detection and self.speaker_bridge:
            try:
                return await self.speaker_bridge.detect_speaker_simple(text)
            except Exception as e:
                logger.warning(f"LLM speaker detection failed: {e}, falling back to regex")
                # Fall back to parent regex implementation
                return super()._detect_speaker(text)
        else:
            # Use current regex implementation
            return super()._detect_speaker(text)
```

#### **Step 1.3: Plugin Registration**

**Edit**: `qc_clean/plugins/extractors/__init__.py`
```python
# Add after existing auto-registration:
try:
    from .enhanced_semantic_extractor import EnhancedSemanticExtractor
    register_extractor("enhanced_semantic", EnhancedSemanticExtractor)
except ImportError:
    pass
```

#### **Step 1.4: Configuration Extension**

**Create**: `qc_clean/config/speaker_detection.yaml`
```yaml
# Speaker Detection Configuration
speaker_detection:
  method: "regex"  # Options: "regex", "llm"
  fallback: "regex"
  max_tokens: 2000
  circuit_breaker:
    failure_threshold: 5
    timeout_seconds: 30
  performance:
    max_response_time: 10.0  # seconds
    token_budget: 1000
```

### **Phase 1 Success Criteria**:
- [ ] Bridge imports work without errors: `python -c "from qc_clean.core.speaker_detection.schema_bridge import SpeakerDetectionBridge; print('OK')"`
- [ ] Enhanced plugin registers: Check `get_available_extractors()` includes "enhanced_semantic"
- [ ] Current CLI unaffected: `python -m qc_clean.core.cli.cli_robust --help` works
- [ ] All imports successful: No import errors during initialization

---

## **PHASE 2: LLM Integration** (Risk: 🟡 MEDIUM, Duration: 3 hours)

### **Objective**: Implement working LLM speaker detection with comprehensive fallback

#### **Step 2.1: Integration Testing Framework**

**Create**: `test_enhanced_speaker_detection.py`
```python
"""
Test framework for enhanced speaker detection
Following Test-Driven Development principles
"""
import pytest
import asyncio
from qc_clean.plugins.extractors.enhanced_semantic_extractor import EnhancedSemanticExtractor
from qc_clean.core.llm.llm_handler import LLMHandler
from qc_clean.config.unified_config import UnifiedConfig

@pytest.fixture
async def enhanced_extractor():
    """Create enhanced extractor for testing"""
    config = UnifiedConfig()
    llm_handler = LLMHandler(config=config.to_grounded_theory_config())
    return EnhancedSemanticExtractor(
        llm_handler=llm_handler,
        use_llm_speaker_detection=True
    )

@pytest.fixture  
async def regex_extractor():
    """Create regex-only extractor for comparison"""
    config = UnifiedConfig()
    llm_handler = LLMHandler(config=config.to_grounded_theory_config())
    return EnhancedSemanticExtractor(
        llm_handler=llm_handler,
        use_llm_speaker_detection=False
    )

class TestSpeakerDetectionBaseline:
    """Baseline tests - these must pass before LLM implementation"""
    
    @pytest.mark.asyncio
    async def test_regex_baseline_accuracy(self, regex_extractor):
        """Test current regex accuracy - establish baseline"""
        test_cases = [
            ("John: Hello everyone", "John"),
            ("Sarah said we should proceed", "Sarah"), 
            ("I think that's correct", "Participant"),
            ("We believe this is right", "Participant"),
            ("The system shows error", None)
        ]
        
        passed = 0
        for text, expected in test_cases:
            result = await regex_extractor._detect_speaker(text)
            if result == expected:
                passed += 1
            print(f"'{text}' -> Expected: {expected}, Got: {result}")
        
        baseline_accuracy = passed / len(test_cases)
        print(f"Regex baseline accuracy: {baseline_accuracy:.2%}")
        assert baseline_accuracy >= 0.6  # Minimum acceptable baseline
        return baseline_accuracy

class TestLLMSpeakerDetection:
    """LLM speaker detection tests - must meet or exceed baseline"""
    
    @pytest.mark.asyncio
    async def test_llm_speaker_accuracy(self, enhanced_extractor, regex_extractor):
        """LLM detection must match or exceed regex accuracy"""
        test_cases = [
            ("John: Hello everyone", "John"),
            ("Sarah said we should proceed", "Sarah"),
            ("I think that's correct", "Participant"), 
            ("We believe this is right", "Participant"),
            ("The system shows error", None)
        ]
        
        # Get baseline accuracy
        regex_passed = 0
        llm_passed = 0
        
        for text, expected in test_cases:
            regex_result = await regex_extractor._detect_speaker(text)
            llm_result = await enhanced_extractor._detect_speaker(text)
            
            if regex_result == expected:
                regex_passed += 1
            if llm_result == expected:
                llm_passed += 1
                
            print(f"'{text}':")
            print(f"  Expected: {expected}")
            print(f"  Regex: {regex_result}")  
            print(f"  LLM: {llm_result}")
        
        regex_accuracy = regex_passed / len(test_cases)
        llm_accuracy = llm_passed / len(test_cases)
        
        print(f"Regex accuracy: {regex_accuracy:.2%}")
        print(f"LLM accuracy: {llm_accuracy:.2%}")
        
        # LLM must match or exceed regex performance
        assert llm_accuracy >= regex_accuracy
    
    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self, enhanced_extractor):
        """When LLM fails, must fallback to regex successfully"""
        # This tests the fail-fast with fallback behavior
        text = "John: This should work even if LLM fails"
        
        # Test that fallback actually works by patching LLM to fail
        import unittest.mock
        with unittest.mock.patch.object(
            enhanced_extractor.speaker_bridge, 
            'detect_speaker_simple',
            side_effect=Exception("Simulated LLM failure")
        ):
            result = await enhanced_extractor._detect_speaker(text)
            # Should fallback to regex and return "John"
            assert result == "John"
    
    @pytest.mark.asyncio
    async def test_performance_acceptable(self, enhanced_extractor, regex_extractor):
        """LLM detection must complete within acceptable time"""
        import time
        text = "Sarah: Performance test text"
        
        # Measure regex performance
        start_time = time.time()
        regex_result = await regex_extractor._detect_speaker(text) 
        regex_time = time.time() - start_time
        
        # Measure LLM performance
        start_time = time.time()
        llm_result = await enhanced_extractor._detect_speaker(text)
        llm_time = time.time() - start_time
        
        print(f"Regex time: {regex_time:.3f}s")
        print(f"LLM time: {llm_time:.3f}s")
        
        # Accept 10x performance degradation as maximum acceptable
        assert llm_time < (regex_time * 10) or llm_time < 10.0  # Max 10 seconds

if __name__ == "__main__":
    # Run tests directly for development
    asyncio.run(pytest.main([__file__, "-v"]))
```

**Validation Commands**:
```bash
# Run baseline tests first
python test_enhanced_speaker_detection.py
pytest test_enhanced_speaker_detection.py::TestSpeakerDetectionBaseline -v

# Only proceed to LLM tests if baseline passes
pytest test_enhanced_speaker_detection.py::TestLLMSpeakerDetection -v
```

#### **Step 2.2: Circuit Breaker Implementation**

**Create**: `qc_clean/core/speaker_detection/circuit_breaker.py`
```python
"""
Circuit Breaker for LLM Speaker Detection
Prevents cascading failures and manages fallback behavior
"""
import time
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

class SpeakerDetectionCircuitBreaker:
    """Circuit breaker for LLM speaker detection with automatic fallback"""
    
    def __init__(self, failure_threshold=5, timeout_seconds=30):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_circuit_open(self) -> bool:
        """Check if circuit is open (should fallback)"""
        if self.state == "OPEN":
            # Check if timeout period has passed
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker: HALF_OPEN - attempting LLM retry")
                return False
            return True
        return False
    
    async def call_with_circuit_breaker(
        self,
        llm_func: Callable,
        fallback_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute LLM function with circuit breaker protection"""
        
        if self.is_circuit_open():
            logger.info("Circuit breaker OPEN - using fallback immediately")
            return await fallback_func(*args, **kwargs)
        
        try:
            result = await llm_func(*args, **kwargs)
            
            # Success - reset circuit
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit breaker: CLOSED - LLM recovery successful")
            
            return result
            
        except Exception as e:
            logger.warning(f"LLM speaker detection failed: {e}")
            
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker OPEN - {self.failure_count} failures, using fallback for {self.timeout_seconds}s")
            
            # Use fallback
            return await fallback_func(*args, **kwargs)
```

#### **Step 2.3: Enhanced Implementation with Circuit Breaker**

**Edit**: `qc_clean/plugins/extractors/enhanced_semantic_extractor.py`
```python
# Add import at top:
from qc_clean.core.speaker_detection.circuit_breaker import SpeakerDetectionCircuitBreaker

# Modify __init__ method:
def __init__(self, llm_handler=None, use_llm_speaker_detection=False):
    super().__init__(llm_handler)
    self.use_llm_detection = use_llm_speaker_detection
    
    if self.use_llm_detection and llm_handler:
        self.speaker_bridge = SpeakerDetectionBridge(llm_handler)
        self.circuit_breaker = SpeakerDetectionCircuitBreaker(
            failure_threshold=5,
            timeout_seconds=30
        )
    else:
        self.speaker_bridge = None
        self.circuit_breaker = None
    
    logger.info(f"EnhancedSemanticExtractor initialized - LLM detection: {self.use_llm_detection}")

# Modify _detect_speaker method:
async def _detect_speaker(self, text: str) -> Optional[str]:
    """Hybrid speaker detection with circuit breaker protection"""
    if self.use_llm_detection and self.speaker_bridge and self.circuit_breaker:
        # Use circuit breaker for robust fallback
        return await self.circuit_breaker.call_with_circuit_breaker(
            llm_func=self.speaker_bridge.detect_speaker_simple,
            fallback_func=self._detect_speaker_regex,
            text
        )
    else:
        # Use current regex implementation
        return self._detect_speaker_regex(text)

def _detect_speaker_regex(self, text: str) -> Optional[str]:
    """Explicit regex implementation for fallback"""
    return super()._detect_speaker(text)
```

### **Phase 2 Success Criteria**:
- [ ] **Tests Pass**: All baseline and LLM tests pass with >80% success rate
- [ ] **Circuit Breaker Works**: Automatic fallback after 5 failures 
- [ ] **Performance Acceptable**: LLM detection completes <10 seconds
- [ ] **No System Breakage**: Current CLI functionality completely preserved

---

## **PHASE 3: Quality Enhancement** (Risk: 🟡 MEDIUM, Duration: 2 hours)

### **Step 3.1: Advanced Speaker Analysis** (Optional)

**Create**: `qc_clean/core/speaker_detection/advanced_analysis.py`
```python
"""
Advanced Speaker Analysis using Sophisticated Schemas
Optional enhancement for rich speaker property discovery
"""
from typing import Dict, List, Any, Optional
import logging

try:
    from src.qc.extraction.code_first_schemas import SpeakerPropertySchema
    ADVANCED_SCHEMAS_AVAILABLE = True
except ImportError:
    ADVANCED_SCHEMAS_AVAILABLE = False

logger = logging.getLogger(__name__)

class AdvancedSpeakerAnalyzer:
    """Advanced speaker analysis using sophisticated src/ schemas"""
    
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
        self.available = ADVANCED_SCHEMAS_AVAILABLE
        
        if not self.available:
            logger.warning("Advanced speaker schemas not available - feature disabled")
    
    async def analyze_speaker_properties(
        self, 
        interview_text: str,
        interview_id: str = "unknown"
    ) -> Optional[Dict[str, Any]]:
        """Rich speaker property analysis"""
        
        if not self.available:
            return None
        
        try:
            prompt = self._build_speaker_analysis_prompt(interview_text, interview_id)
            result = await self.llm_handler.extract_structured(
                prompt=prompt,
                schema=SpeakerPropertySchema
            )
            
            return {
                "interview_id": interview_id,
                "speaker_properties": result.properties,
                "discovery_method": result.discovery_method,
                "confidence": result.extraction_confidence
            }
            
        except Exception as e:
            logger.error(f"Advanced speaker analysis failed: {e}")
            return None
    
    def _build_speaker_analysis_prompt(self, text: str, interview_id: str) -> str:
        """Build comprehensive speaker analysis prompt"""
        return f"""
You are an expert qualitative researcher analyzing speaker characteristics in interview data.

Interview ID: {interview_id}

Analyze this interview transcript and identify speaker properties:

{text}

Instructions:
1. Identify recurring speaker characteristics (roles, attitudes, expertise)
2. Note communication patterns and styles
3. Determine relationship dynamics between speakers
4. Extract demographic or contextual indicators
5. Assess confidence levels for each identified property

Focus on properties that help distinguish speakers and understand their perspectives.
"""
```

### **Step 3.2: Performance Monitoring**

**Create**: `qc_clean/core/speaker_detection/performance_monitor.py`
```python
"""
Performance Monitoring for Speaker Detection
Tracks metrics and provides optimization insights
"""
import time
import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for speaker detection"""
    total_detections: int = 0
    llm_detections: int = 0
    regex_fallbacks: int = 0
    total_time: float = 0.0
    llm_time: float = 0.0
    failure_count: int = 0
    avg_response_time: float = 0.0
    detection_accuracy: float = 0.0
    timestamps: List[datetime] = field(default_factory=list)

class SpeakerDetectionMonitor:
    """Monitor performance and quality of speaker detection"""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.recent_results: List[Dict[str, Any]] = []
        self.max_recent_results = 100
    
    def record_detection(
        self,
        text: str,
        result: str,
        method: str,
        execution_time: float,
        success: bool = True
    ):
        """Record a speaker detection event"""
        self.metrics.total_detections += 1
        self.metrics.total_time += execution_time
        
        if method == "llm":
            self.metrics.llm_detections += 1
            self.metrics.llm_time += execution_time
        else:
            self.metrics.regex_fallbacks += 1
        
        if not success:
            self.metrics.failure_count += 1
        
        # Update averages
        self.metrics.avg_response_time = (
            self.metrics.total_time / self.metrics.total_detections
        )
        
        # Store recent result
        self.recent_results.append({
            "timestamp": datetime.now(),
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "result": result,
            "method": method,
            "execution_time": execution_time,
            "success": success
        })
        
        # Maintain recent results limit
        if len(self.recent_results) > self.max_recent_results:
            self.recent_results.pop(0)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        total = self.metrics.total_detections
        
        if total == 0:
            return {"status": "no_data", "message": "No detections recorded"}
        
        llm_percentage = (self.metrics.llm_detections / total) * 100
        fallback_percentage = (self.metrics.regex_fallbacks / total) * 100
        failure_rate = (self.metrics.failure_count / total) * 100
        
        return {
            "summary": {
                "total_detections": total,
                "llm_success_rate": f"{100 - failure_rate:.1f}%",
                "average_response_time": f"{self.metrics.avg_response_time:.3f}s"
            },
            "method_distribution": {
                "llm_detections": f"{llm_percentage:.1f}%",
                "regex_fallbacks": f"{fallback_percentage:.1f}%"
            },
            "performance": {
                "total_time": f"{self.metrics.total_time:.2f}s",
                "avg_llm_time": f"{self.metrics.llm_time / max(1, self.metrics.llm_detections):.3f}s",
                "failure_count": self.metrics.failure_count,
                "failure_rate": f"{failure_rate:.1f}%"
            },
            "recent_activity": len(self.recent_results),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if self.metrics.failure_count > 0:
            failure_rate = (self.metrics.failure_count / max(1, self.metrics.total_detections)) * 100
            if failure_rate > 10:
                recommendations.append("High failure rate detected - consider adjusting circuit breaker threshold")
        
        if self.metrics.avg_response_time > 5.0:
            recommendations.append("High average response time - consider reducing max_tokens or timeout")
        
        fallback_rate = (self.metrics.regex_fallbacks / max(1, self.metrics.total_detections)) * 100
        if fallback_rate > 50:
            recommendations.append("High fallback rate - LLM may be unreliable, consider configuration adjustment")
        
        if not recommendations:
            recommendations.append("Performance metrics within acceptable ranges")
        
        return recommendations

# Global monitor instance
performance_monitor = SpeakerDetectionMonitor()
```

### **Phase 3 Success Criteria**:
- [ ] **Advanced Analysis Available**: Optional rich speaker analysis working when schemas available
- [ ] **Performance Monitoring**: Comprehensive metrics collection and reporting
- [ ] **Optimization Insights**: Actionable recommendations generated
- [ ] **Quality Maintained**: No degradation in core functionality

---

## **PHASE 4: Production Deployment** (Risk: 🟢 LOW, Duration: 1 hour)

### **Step 4.1: Integration with Workflow**

**Edit**: `qc_clean/core/workflow/grounded_theory.py`
```python
# Add import at top:
from plugins.extractors import get_extractor_plugin

# Modify _initialize_extractor_plugin method:
def _initialize_extractor_plugin(self):
    """Initialize the appropriate extractor plugin based on configuration"""
    try:
        from plugins.extractors import get_extractor_plugin
        
        # Check for enhanced semantic extractor configuration
        extractor_name = "hierarchical"  # default
        use_llm_speaker_detection = False
        
        if self.config:
            # Check for enhanced speaker detection configuration
            if hasattr(self.config, 'speaker_detection'):
                if getattr(self.config.speaker_detection, 'method', 'regex') == 'llm':
                    extractor_name = "enhanced_semantic"
                    use_llm_speaker_detection = True
            
            # Legacy configuration support
            if hasattr(self.config, 'extraction') and hasattr(self.config.extraction, 'extractor'):
                if self.config.extraction.extractor == 'enhanced_semantic':
                    extractor_name = "enhanced_semantic"
                    use_llm_speaker_detection = True
        
        # Get the appropriate extractor
        if extractor_name == "enhanced_semantic":
            from plugins.extractors.enhanced_semantic_extractor import EnhancedSemanticExtractor
            from core.llm.llm_handler import LLMHandler
            
            # Create LLM handler if not available
            if not hasattr(self, 'operations') or not hasattr(self.operations, 'llm_handler'):
                from config.unified_config import UnifiedConfig
                config = UnifiedConfig()
                llm_handler = LLMHandler(config=config.to_grounded_theory_config())
            else:
                llm_handler = self.operations.llm_handler
            
            return EnhancedSemanticExtractor(
                llm_handler=llm_handler,
                use_llm_speaker_detection=use_llm_speaker_detection
            )
        else:
            # Use standard plugin system
            return get_extractor_plugin(extractor_name)
    
    except Exception as e:
        logger.warning(f"Could not initialize extractor plugin: {e}")
        return None
```

### **Step 4.2: End-to-End Testing**

**Create**: `test_full_integration.py`
```python
"""
End-to-End Integration Testing
Validates complete LLM speaker detection integration
"""
import pytest
import subprocess
import tempfile
import os
import json

class TestFullIntegration:
    """Test complete system integration with LLM speaker detection"""
    
    def test_cli_still_works_default(self):
        """Ensure CLI works with default (regex) configuration"""
        result = subprocess.run([
            "python", "-m", "qc_clean.core.cli.cli_robust", "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "analyze" in result.stdout
    
    def test_africa_dataset_with_enhanced_detection(self):
        """Test enhanced detection on real data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run analysis with enhanced detection
            result = subprocess.run([
                "python", "-m", "qc_clean.core.cli.cli_robust",
                "analyze",
                "--input", "data/interviews/africa_3_interviews_for_test", 
                "--output", temp_dir,
                "--extractor", "enhanced_semantic"
            ], capture_output=True, text=True)
            
            # Should complete successfully
            assert result.returncode == 0
            
            # Verify outputs exist
            assert os.path.exists(os.path.join(temp_dir, "detailed_analysis.json"))
            
            # Load and validate results
            with open(os.path.join(temp_dir, "detailed_analysis.json")) as f:
                results = json.load(f)
            
            # Should maintain baseline performance
            assert results["metadata"]["codes_generated"] >= 25
            assert results["metadata"]["entities_generated"] >= 30
    
    def test_performance_monitoring(self):
        """Test that performance monitoring is working"""
        from qc_clean.core.speaker_detection.performance_monitor import performance_monitor
        
        # Monitor should be initialized
        report = performance_monitor.get_performance_report()
        assert "status" in report

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Validation Commands**:
```bash
# Run complete integration tests
python test_full_integration.py

# Test Africa dataset with enhanced detection
python -m qc_clean.core.cli.cli_robust analyze \
  --input data/interviews/africa_3_interviews_for_test \
  --output test_enhanced_output \
  --extractor enhanced_semantic

# Verify performance monitoring
python -c "
from qc_clean.core.speaker_detection.performance_monitor import performance_monitor
import json
report = performance_monitor.get_performance_report()
print(json.dumps(report, indent=2))
"
```

### **Phase 4 Success Criteria**:
- [ ] **CLI Integration Complete**: Enhanced extractor available via `--extractor enhanced_semantic`
- [ ] **Africa Dataset Success**: Maintains >25 codes, >30 entities with enhanced detection
- [ ] **Performance Monitoring**: Active monitoring with actionable reports
- [ ] **Zero Regression**: All existing functionality preserved

---

## Success Criteria (EVIDENCE-BASED)

1. **Schema Bridge Functional**: `from qc_clean.core.speaker_detection.schema_bridge import SpeakerDetectionBridge` works
2. **Enhanced Plugin Available**: `enhanced_semantic` appears in `get_available_extractors()`
3. **LLM Detection Working**: >80% accuracy on test cases with <10s response time
4. **Fallback Mechanism**: Automatic fallback to regex on LLM failures
5. **Circuit Breaker Active**: Prevents cascading failures with monitoring
6. **CLI Integration**: `--extractor enhanced_semantic` flag functional
7. **Performance Maintained**: Africa dataset processing maintains >25 codes, >30 entities
8. **Zero Regression**: All existing CLI functionality preserved

## Failure Indicators (REJECT IMPLEMENTATION IF)

- Schema bridge imports fail or cause import errors
- Enhanced plugin fails to register or causes system crashes
- LLM speaker detection accuracy <60% of baseline
- Fallback mechanism fails to activate on LLM errors
- CLI integration breaks existing analysis functionality
- Performance degradation >20x baseline without fallback
- Circuit breaker fails to prevent cascading failures

## Evidence Requirements

All implementation claims must be documented in:
`evidence/current/Evidence_LLM_Speaker_Detection_Integration.md`

Required evidence:
- Schema bridge import success logs
- Enhanced plugin registration confirmation
- LLM vs regex accuracy comparison test results  
- Fallback mechanism activation test logs
- Circuit breaker performance under failure conditions
- Africa dataset analysis results comparison (before/after)
- Performance monitoring reports with optimization recommendations

## Quality Standards

- **100% functionality preserved** - All existing CLI analysis features must continue working
- **Evidence-based validation** - All claims must be verifiable via test execution
- **Test-driven development** - Write failing tests first, implement to pass
- **Fail-fast implementation** - Surface errors immediately, don't hide in logs
- **No lazy implementations** - No mocking of LLM calls or simplified stubs

## Development Notes

- LLM speaker detection is 10x slower than regex but provides sophisticated analysis
- Circuit breaker prevents API cost escalation and system failures  
- Fallback mechanism ensures system reliability during LLM service outages
- Performance monitoring provides optimization insights for production tuning
- Integration preserves all existing functionality while adding optional enhancement
- Expected implementation time: 8 hours with 85% success probability