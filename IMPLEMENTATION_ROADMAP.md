# Implementation Roadmap: Academic QC System

## Overview

Building an LLM-native qualitative coding system that leverages Gemini 2.5 Flash's full context window to analyze all 103 interviews simultaneously (2 LLM calls total), with systematic three-phase fallback if needed.

---

## Key Architecture Decision: Global Context Analysis

Leveraging Gemini 2.5 Flash capabilities:
- **Input limit**: 1,048,576 tokens (all 103 interviews fit comfortably)
- **Output limit**: 65,536 tokens (sufficient for comprehensive analysis)
- **Rate limit**: 4,000,000 tokens/minute (no rate limiting needed)
- **Strategy**: Process entire dataset in 2 calls instead of 330+ sequential calls
- **Innovation**: Use LLM's global pattern recognition instead of human-style sequential processing

---

## Phase 1: Foundation with Dual-Layer Batch Architecture (Week 1)

### 1.1 Core Three-Mode System for BOTH Layers
```python
# qc/core/coding_modes.py
- CodingMode enum (OPEN, CLOSED, HYBRID)
- AnalysisGoal (directed vs exploratory)
- CodingFramework model for predefined codes
- EntitySchema model with POLICY_ENTITY_TYPES
- DualLayerExtractor main class

# qc/core/policy_entities.py
POLICY_ENTITY_TYPES = {
    "person": {"properties": ["role", "department", "stakeholder_type"]},
    "organization": {"properties": ["type", "sector", "size"]},
    "tool": {"properties": ["category", "purpose"]},
    "method": {"properties": ["approach", "domain"]},
    "policy_recommendation": {
        "properties": ["urgency", "complexity", "cost_implication"]
    },
    "implementation_barrier": {
        "properties": ["type", "severity", "affected_groups"]
    },
    "metaphor": {
        "properties": ["source_domain", "target_domain", "implication"]
    }
}
```

### 1.2 Batch Processing Infrastructure with Operational Features
```python
# qc/core/batch_processor.py
- Token counting and flexible batch creation based on MAX_BATCH_TOKENS
- Error recovery with interview quarantine
- Progress tracking with phase visibility
- Cost estimation before execution

# qc/core/gemini_batch_client.py
- Configure for gemini-2.5-flash model
- Handle 1M input / 65K output limits
- Implement retry logic with exponential backoff
- Real-time cost tracking

# qc/core/progress_tracker.py
class ProgressTracker:
    phases = [
        "Initializing",
        "Phase 1: Initial Coding", 
        "Phase 2: Aggregation",
        "Phase 3: Final Coding",
        "Generating Reports"
    ]
    
    def update(self, phase: str, percent: float, message: str):
        # Console and/or web UI updates
        print(f"[{phase}] {percent}% - {message}")

# qc/core/cost_tracker.py
class CostTracker:
    INPUT_PRICE_PER_MILLION = float(os.getenv('GEMINI_INPUT_PRICE', '0.30'))
    OUTPUT_PRICE_PER_MILLION = float(os.getenv('GEMINI_OUTPUT_PRICE', '2.50'))
    
    def estimate_cost(self, interviews: List[str]) -> float:
        # Pre-execution cost estimation
        
    def track_actual(self, tokens_used: int):
        # Real-time cost tracking
```

### 1.3 Dual-Layer Batch Architecture with Error Handling
```python
# qc/core/dual_layer_batch_extractor.py
- Process all interviews in flexible batches based on token count
- Separate prompts for qual and entity layers
- Parallel processing of both layers
- Interview-level error boundaries
- Clear naming (CODE_ vs ENT_)

# qc/core/error_recovery.py
class ErrorRecovery:
    def __init__(self):
        self.quarantine = []  # Bad interviews
        self.retry_queue = []  # Temporary failures
        
    async def process_with_recovery(self, interviews: List[Interview]):
        results = []
        for interview in interviews:
            try:
                result = await self.process_single(interview)
                results.append(result)
            except CorruptedDataError:
                self.quarantine.append(interview)
                self.log_quarantine(interview.id, reason)
            except TemporaryError:
                self.retry_queue.append(interview)
        
        # Process retries with backoff
        retry_results = await self.process_retries()
        
        return results + retry_results, self.quarantine
```

### 1.4 Three-Phase Aggregation Architecture
```python
# qc/core/aggregation_workflow.py
- Phase 1: Parallel unconstrained coding
- Phase 2: Intelligent aggregation with contradiction detection
- Phase 3: Final coding with refined codebook
- Optional hermeneutic cycles after Phase 3

# qc/core/code_aggregator.py
- Semantic deduplication logic
- Hierarchy building from flat codes
- Frequency analysis across batches
- Contradiction detection across stakeholder groups
- Policy significance detection

# qc/core/contradiction_detector.py
- Identify opposing views on same issues
- Link contradictions to stakeholder types
- Generate tension analysis
```

### Deliverables
- [ ] Batch processing infrastructure (200K tokens/batch)
- [ ] Three-phase aggregation workflow with contradiction detection
- [ ] Parallel execution system
- [ ] Intelligent code aggregation with policy focus
- [ ] Dual-layer architecture with policy entity types
- [ ] Three modes (OPEN/CLOSED/HYBRID) for BOTH layers
- [ ] Structured output for CLOSED mode enforcement
- [ ] Stakeholder mapping via entity properties
- [ ] Optional hermeneutic cycles

---

## Phase 2: Academic Features (Week 2)

### 2.1 Negative Case Analysis
```python
# qc/core/negative_case_analysis.py
- Find contradicting evidence
- Theory refinement based on exceptions
- Strengthen findings
```

### 2.2 Audit Trail System
```python
# qc/core/audit_trail.py
- Record Phase 1 initial codes
- Track aggregation decisions (merges, deletions)
- Record Phase 3 final applications
- Track optional hermeneutic cycle changes
- Export complete decision history
- Methods section auto-generation for reports
```

### 2.4 Interview Metadata System
```python
# qc/core/metadata_extractor.py
- Flexible metadata extraction with LLM
- Common fields with smart defaults
- Support for additional custom fields
- Won't break on missing data
```

### 2.3 Theoretical Sampling Guidance
```python
# qc/core/theoretical_sampling.py
- Identify theory gaps
- Suggest participant criteria
- Generate interview questions
- Saturation assessment
```

### Deliverables
- [ ] Negative case analyzer
- [ ] Complete audit trail for all phases
- [ ] Interview metadata extraction
- [ ] Sampling recommendations
- [ ] Quality dashboard for debugging

---

## Phase 3: Analysis & Reporting (Week 3)

### 3.1 Cross-Interview Analysis
```python
# qc/core/cross_case_analysis.py
- Compare codes across interviews
- Pattern identification
- Theme consolidation
- Framework validation (for CLOSED/HYBRID)
```

### 3.2 Report Generation
```python
# qc/core/report_generator.py
- Executive summary for policy makers
- Theme descriptions with stakeholder breakdown
- Entity analysis sections
- Cross-layer insights
- Contradiction matrix
- Methods section auto-generation
- Full data export (SPSS, R, JSON, CSV)

# qc/core/policy_brief_generator.py
- One-page policy brief format
- Key findings by stakeholder group
- Implementation barriers summary
- Policy recommendations with urgency
- Areas of consensus and conflict
```

### 3.3 Dual-Layer Queries
```python
# qc/core/dual_layer_queries.py
- Find entities by code
- Find codes by entity
- Cross-layer patterns
- Co-occurrence analysis
- Voice counting (unique entities per code)
- Stakeholder position mapping
- Contradiction identification
```

### 3.4 Visualization
```python
# qc/core/visualizations.py
- Code hierarchy diagrams
- Entity network graphs
- Cross-layer relationship maps
- Theme relationships
- Framework coverage (HYBRID mode)
- Saturation curves
- Contradiction matrix visualization
- Stakeholder position maps
- Code co-occurrence matrices
```

### Deliverables
- [ ] Cross-case analysis tools
- [ ] Dual-layer report generator
- [ ] Cross-layer query engine
- [ ] Dual-layer visualizations
- [ ] Export formats for both layers

---

## Phase 4: Advanced Features (Week 4)

### 4.1 Policy Analysis Features
```python
# qc/core/policy_analytics.py
- Stakeholder consensus analysis
- Implementation feasibility scoring
- Policy recommendation extraction
- Barrier severity assessment

# qc/core/quant_integration.py
- Survey data integration templates
- Demographic weighting functions
- Mixed methods validation
- Convergence analysis
```

### 4.2 Framework Evolution (HYBRID mode special)
```python
# qc/core/framework_evolution.py
- Track emergent codes
- Suggest framework updates
- Version control for frameworks
- Gap analysis
```

### 4.3 Quality Metrics
```python
# qc/core/quality_metrics.py
- Code density by stakeholder group
- Policy coherence metrics
- Saturation metrics
- Audit completeness
- Contradiction resolution tracking
- Evidence strength indicators
```

### Deliverables
- [ ] Optional GT features
- [ ] Framework evolution tools
- [ ] Quality dashboard
- [ ] Performance metrics

---

## Implementation Priorities

### Must Have (MVP)
1. Three-mode system (OPEN/CLOSED/HYBRID)
2. Goal setting (directed/exploratory)
3. Policy entity types in schema
4. Hierarchical coding
5. Negative case analysis
6. Audit trail with methods generation
7. Executive summary generation
8. Contradiction detection

### Should Have
1. Theoretical sampling guidance
2. Cross-case analysis
3. Policy-focused visualizations
4. Framework evolution tracking
5. Multiple export formats
6. Quantitative data integration
7. Stakeholder consensus metrics

### Could Have
1. Constant comparison
2. Inter-rater reliability
3. Real-time collaboration
4. Statistical integration
5. Multiple methodology support

### Won't Have (v1)
1. Team collaboration features
2. Video/audio transcription
3. Multiple language support
4. Cloud deployment
5. Mobile interface

---

## Technical Decisions

### Architecture
- Build new BatchDualLayerExtractor for Gemini 2.5 Flash
- Extend SimpleGeminiExtractor for batch support
- Parallel processing infrastructure
- Clear separation of layers and modes

### Batch Processing
- Token limit per batch from .env (MAX_BATCH_TOKENS)
- Parallel execution with rate limiting
- Progress tracking across batches
- Automatic retry on failures

### Data Storage
- JSON for frameworks and codebooks
- File-based audit trails
- Neo4j for entity relationships
- Batch result consolidation
- Export to standard formats

### Performance Targets
- Flexible interview count based on available data
- Automatic batching based on token limits
- Cost estimation before execution
- Real-time progress updates
- Graceful handling of corrupted interviews

### UI Considerations
- CLI with batch progress bars
- Real-time saturation metrics
- Cycle completion notifications
- Clear mode indicators

---

## Success Metrics

### Functionality
- [ ] All three modes working for both layers
- [ ] Three-phase aggregation workflow complete
- [ ] Structured output enforces CLOSED mode
- [ ] Negative cases identified
- [ ] Audit trail tracks all phases
- [ ] Reports meet academic standards

### Performance
- [ ] Efficient batch processing for any interview count
- [ ] Parallel batch processing working
- [ ] Stay within 4M tokens/minute limit
- [ ] Accurate semantic deduplication

### Quality
- [ ] Coherent coding across all batches
- [ ] Proper hierarchy generation
- [ ] Flexible metadata extraction
- [ ] Cross-layer insights working
- [ ] Contradiction detection accurate
- [ ] Stakeholder mapping complete
- [ ] Policy recommendations extracted

### Usability
- [ ] Clear mode selection via .env
- [ ] Quality dashboard for debugging
- [ ] Helpful sampling guidance
- [ ] Professional policy briefs
- [ ] Executive summaries
- [ ] Contradiction matrices

---

## Risk Mitigation

### Technical Risks
- **LLM consistency**: Use temperature 0.3-0.4, structured outputs
- **Mode confusion**: Clear prompts, validation checks
- **Framework rigidity**: Hybrid mode as safety valve

### Research Risks
- **Over-automation**: Keep human in loop, show rationale
- **Theoretical weakness**: Emphasize augmentation not replacement
- **Methodological mixing**: Clear mode boundaries

---

## Next Steps

1. **Immediate**: Implement three-mode base system
2. **This Week**: Get OPEN mode fully working
3. **Next Week**: Add CLOSED and HYBRID modes
4. **Testing**: Use sample interviews for each mode
5. **Documentation**: Update with examples

---

## Notes

- Start simple, build incrementally
- Test with real policy consultation data
- Get feedback from policy analysts
- Don't over-engineer v1
- Focus on practical policy utility

## Operational Features

### Progress Visibility
```python
# Real-time progress updates
Phase 1: Initial Coding [████████░░] 80% - Processing batch 2/3
Phase 2: Aggregation [██░░░░░░░░] 20% - Detecting contradictions
Progress: Detecting contradictions...
```

### Cost Management
```python
# Pre-execution cost estimation
Analysis Cost Estimate:
- Interview count: 50 (~100K tokens)
- 3 phases × 100K = 300K tokens
- Input cost: 0.3M × $0.30 = $0.09
- Output cost: 0.05M × $2.50 = $0.125
- Total estimated: $0.22

Proceed? [Y/n]
```

### Error Recovery
```python
# Graceful handling of bad data
Processing Results:
- Successfully processed: 48/50 interviews
- Quarantined (corrupted): 2 interviews
  - Interview_23.txt: Encoding error (appears to be binary file)
  - Interview_41.txt: Empty file
  
Continuing with 48 valid interviews...
```

## Future Research Areas

Not included in v1 but potentially valuable:
- **Researcher Reflexivity**: For politically sensitive topics
- **Inter-Rater Reliability**: For contested policy areas  
- **Literature Integration**: For evidence-based policy frameworks
- **Large-scale processing**: Hierarchical batching for thousands of interviews