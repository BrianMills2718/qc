# QUALITATIVE CODING PROJECT - COMPLETE TDD ROADMAP

**Project Goal**: Build a qualitative coding system leveraging LLM's global context advantage to analyze all 103 interviews simultaneously, with fallback to systematic three-phase methodology if needed.

**Current Status**: LLM-native approach working with 2 calls. Need to implement missing CSV outputs, hierarchical coding, and fix model configuration.

---

## 🚨 **IMMEDIATE FIXES NEEDED**

### **Priority 1: Model Configuration**
- [ ] **Change to gemini-2.5-flash** from gemini-2.0-flash in SimpleGeminiClient
- [ ] Update all model references and token limits
- [ ] Test with new model to ensure compatibility

### **Priority 2: Missing CSV Files Implementation**
1. [ ] **theme_analysis.csv** - Theme statistics with exemplar quote references
2. [ ] **quote_evidence.csv** - Full quote traceability with line numbers and context
3. [ ] **code_progression.csv** - How codes evolve from initial mention to resolution
4. [ ] **contradiction_matrix.csv** - Opposing viewpoints with evidence from both sides
5. [ ] **stakeholder_positions.csv** - Policy positions with supporting evidence chains

### **Priority 3: Core Data Structure Fixes**
- [ ] **Hierarchical Coding Structure**
  - [ ] Add parent_code_id field to code model
  - [ ] Implement code hierarchy detection logic
  - [ ] Update CSV exports to show parent-child relationships
- [ ] **Theme-Code Linkage**
  - [ ] Fix empty theme_id column in codes.csv
  - [ ] Ensure proper theme assignment for all codes
- [ ] **Line Number Tracking**
  - [ ] Extract actual line numbers from DOCX files
  - [ ] Store position information with quotes
  - [ ] Enable source document navigation

### **Priority 4: Analysis Enhancement Features**
- [ ] **Quote Chains Implementation** - Sequential progressions showing idea development
- [ ] **Code Evolution Tracking** - Monitor how codes develop across interviews
- [ ] **Stakeholder Position Analysis** - Extract and categorize policy positions
- [ ] **Contradiction Detection** - Identify and matrix opposing viewpoints

---

## 📝 **IMPLEMENTATION DETAILS**

### **1. Model Configuration Update (gemini-2.5-flash)**
```python
# In qc/core/simple_gemini_client.py
model: str = "gemini-2.5-flash"  # Update from gemini-2.0-flash
# Update token limits and pricing if different
```

### **2. CSV File Implementations**

#### **theme_analysis.csv**
```python
# Columns: theme_id, theme_name, prevalence, interview_count, code_count, 
#          exemplar_quote_1, exemplar_quote_2, exemplar_quote_3, 
#          key_insights, saturation_point
```

#### **quote_evidence.csv**
```python
# Columns: quote_id, text, speaker_name, speaker_role, interview_id, 
#          document_name, line_number, paragraph_number, 
#          preceding_context, following_context, codes, themes
```

#### **code_progression.csv**
```python
# Columns: code_id, code_name, first_appearance, evolution_stage_1, 
#          evolution_stage_2, evolution_stage_3, final_form, 
#          interview_progression, saturation_interview
```

#### **contradiction_matrix.csv**
```python
# Columns: contradiction_id, topic, position_1, position_1_holders, 
#          position_1_quotes, position_2, position_2_holders, 
#          position_2_quotes, resolution_suggested
```

#### **stakeholder_positions.csv**
```python
# Columns: stakeholder_id, stakeholder_name, stakeholder_type, 
#          position_summary, supporting_quotes, opposing_quotes, 
#          influence_level, policy_recommendations
```

### **3. Hierarchical Coding Implementation**
```python
# Add to GlobalCode model:
parent_code_id: Optional[str] = None
hierarchy_level: int = 0  # 0=top-level, 1=sub-code, 2=sub-sub-code
child_codes: List[str] = []
```

### **4. Line Number Extraction**
```python
# Enhance DOCX parser to track:
- Paragraph numbers
- Character positions
- Section headings
- Speaker changes
```

### **5. Processing Pipeline Improvements**
- Interview rotation to ensure equal representation
- Chunking strategy for large datasets
- Coverage validation metrics

---

## 🎯 **PHASE 1: LLM-NATIVE APPROACH (Days 1-3)**

### **Day 1: Test LLM-Native Global Analysis**

#### Morning (4 hours)
- [ ] **1.1** Fix import issues in qc/__init__.py to enable testing
- [ ] **1.2** Create qc/parsing/__init__.py (empty file for proper module structure)
- [ ] **1.3** Create qc/utils/__init__.py (empty file for proper module structure)
- [ ] **1.4** Test DOCX parser and token counter work properly
- [ ] **1.5** Load all 103 interviews and verify total tokens < 900K (fits in 1M context)

#### Afternoon (4 hours)
- [ ] **1.6** Create qc/models/comprehensive_analysis_models.py with global analysis Pydantic models:
  - [ ] **GlobalCodingResult** (all codes across entire dataset)
  - [ ] **CrossInterviewThemes** (themes that span multiple interviews)
  - [ ] **QuoteChain** (chain of related quotes showing progression)
  - [ ] **CodeProgression** (how codes develop across interviews)
  - [ ] **StakeholderPosition** (policy positions with evidence)
  - [ ] **ContradictionPair** (opposing viewpoints with evidence)
  - [ ] **TheoricalSaturationAssessment** (when saturation naturally occurred)
- [ ] **1.7** Ensure all models work with Gemini structured output (response_schema compatibility)
- [ ] **1.8** Write basic model validation tests (test instantiation, serialization)

### **Day 2: Implement LLM-Native Global Analysis**

#### Morning (4 hours)
- [ ] **2.1** Create qc/core/global_qualitative_analyzer.py
- [ ] **2.2** Implement LLM-native analysis methods:
  - [ ] async def load_all_interviews() -> str (concatenate all 103 with metadata)
  - [ ] async def comprehensive_global_analysis(all_interviews) -> GlobalCodingResult
  - [ ] async def refine_analysis_for_traceability(initial_result) -> EnhancedResult
- [ ] **2.3** Create comprehensive analysis prompt template leveraging global context

#### Afternoon (4 hours)
- [ ] **2.4** Test LLM-native approach with sample of 10 interviews first
- [ ] **2.5** Run full 103-interview analysis (2 LLM calls total)
- [ ] **2.6** Implement error handling with robust_error_handling.py integration  
- [ ] **2.7** Add comprehensive logging and token usage tracking

### **Day 3: Neo4j Desktop Integration & Real Data Testing**

#### Morning (4 hours)
- [ ] **3.1** Install Neo4j Desktop (free local version, no Docker needed)
- [ ] **3.2** Create qc/storage/simple_neo4j_client.py:
  - [ ] Simple connection management (no pooling/production features)
  - [ ] store_three_phase_result() method
  - [ ] Basic schema creation (Interview -> Code -> Category -> Theme nodes)
  - [ ] Graph query methods for quote chains and code progressions
- [ ] **3.3** Create environment variables for Neo4j connection (just bolt://localhost:7687)
- [ ] **3.4** Test Neo4j connection and basic graph queries

#### Afternoon (4 hours)
- [ ] **3.5** Create tests/integration/test_global_analysis.py
- [ ] **3.6** Write first integration test: test_global_analysis_end_to_end()
  - [ ] Load all 103 DOCX files
  - [ ] Run global LLM analysis (2 calls total)
  - [ ] Store results in Neo4j and export CSV/Markdown
  - [ ] Verify quote chains and code progressions exist
- [ ] **3.7** Compare results quality with traditional three-phase approach
- [ ] **3.8** Document effectiveness of LLM-native vs systematic approach

---

## 🏗️ **PHASE 2: FALLBACK SYSTEMATIC APPROACH (Days 4-8)**
*Implement only if LLM-native approach doesn't meet quality standards*

### **Day 4: Implement Systematic Three-Phase Fallback**

#### Morning (4 hours)
- [ ] **4.1** If LLM-native approach insufficient, implement three-phase models:
  - [ ] OpenCodingResult (codes, segments, memos)
  - [ ] AxialCodingResult (categories, relationships, paradigm) 
  - [ ] SelectiveCodingResult (core category, theoretical model)
- [ ] **4.2** Create batched three-phase pipeline (36-40 LLM calls total)
- [ ] **4.3** Test systematic approach quality vs LLM-native approach

#### Afternoon (4 hours)
- [ ] **4.4** Test Open Coding with 5 different real interview types:
  - [ ] AI interview transcript
  - [ ] Africa interview notes
  - [ ] Long interview (>5000 words)
  - [ ] Short interview (<1000 words)
  - [ ] Complex interview (multiple speakers)
- [ ] **4.5** Refine Open Coding based on real data performance
- [ ] **4.6** Ensure consistent JSON schema compliance

### **Day 5: Phase 2 (Axial Coding) TDD**

#### Morning (4 hours)
- [ ] **5.1** Write comprehensive tests for Axial Coding:
  - [ ] test_axial_coding_with_open_codes()
  - [ ] test_axial_coding_with_existing_codebook()
  - [ ] test_axial_coding_relationship_detection()
  - [ ] test_axial_coding_category_formation()
- [ ] **5.2** Run tests, identify failures
- [ ] **5.3** Implement/fix Axial Coding to pass all tests

#### Afternoon (4 hours)
- [ ] **5.4** Test Axial Coding integration with Phase 1 results
- [ ] **5.5** Test codebook evolution logic
- [ ] **5.6** Verify relationship mapping works correctly
- [ ] **5.7** Test with real interview progression (batch of 3-5 interviews)

### **Day 6: Phase 3 (Selective Coding) TDD**

#### Morning (4 hours)
- [ ] **6.1** Write comprehensive tests for Selective Coding:
  - [ ] test_selective_coding_core_category_identification()
  - [ ] test_selective_coding_theoretical_model_creation()
  - [ ] test_selective_coding_integration_with_previous_phases()
  - [ ] test_selective_coding_theme_hierarchy()
- [ ] **6.2** Run tests, identify failures
- [ ] **6.3** Implement/fix Selective Coding to pass all tests

#### Afternoon (4 hours)
- [ ] **6.4** Test complete three-phase pipeline integration
- [ ] **6.5** Verify theoretical coherence across all phases
- [ ] **6.6** Test with complex multi-interview scenarios
- [ ] **6.7** Validate final output quality and structure

### **Day 7: Error Handling & Recovery TDD**

#### Morning (4 hours)
- [ ] **7.1** Write comprehensive error handling tests:
  - [ ] test_api_timeout_recovery()
  - [ ] test_malformed_json_recovery()
  - [ ] test_schema_validation_failure_recovery()
  - [ ] test_phase_failure_cascading_recovery()
- [ ] **7.2** Test circuit breaker patterns with API rate limits
- [ ] **7.3** Test retry mechanisms with exponential backoff

#### Afternoon (4 hours)
- [ ] **7.4** Write basic Neo4j error handling tests:
  - [ ] test_neo4j_connection_retry() (simple reconnection)
  - [ ] test_neo4j_query_failure_handling()
  - [ ] test_graph_data_retrieval_errors()
- [ ] **7.5** Test DOCX parsing error scenarios
- [ ] **7.6** Implement comprehensive error logging and reporting
- [ ] **7.7** Test error recovery with real failure injection

### **Day 8: Performance & Optimization TDD**

#### Morning (4 hours)
- [ ] **8.1** Write performance tests:
  - [ ] test_single_interview_processing_time()
  - [ ] test_batch_processing_optimization()
  - [ ] test_token_budget_management()
  - [ ] test_api_rate_limit_compliance()
- [ ] **8.2** Implement token-aware batch processing
- [ ] **8.3** Test parallel processing capabilities

#### Afternoon (4 hours)
- [ ] **8.4** Write scalability tests:
  - [ ] test_10_interviews_sequential()
  - [ ] test_10_interviews_parallel()
  - [ ] test_memory_usage_large_batch()
- [ ] **8.5** Optimize performance based on test results
- [ ] **8.6** Document performance characteristics and limits

---

## 🎯 **PHASE 3: PRODUCTION FEATURES (Days 9-12)**

### **Day 9: Batch Processing & Codebook Evolution TDD**

#### Morning (4 hours)
- [ ] **9.1** Write batch processing tests:
  - [ ] test_batch_processing_with_codebook_evolution()
  - [ ] test_cross_interview_code_merging()
  - [ ] test_theoretical_saturation_detection()
- [ ] **9.2** Implement intelligent codebook evolution using LLM
- [ ] **9.3** Test codebook consistency across batches

#### Afternoon (4 hours)
- [ ] **9.4** Implement LLM-driven saturation assessment
- [ ] **9.5** Test with real interview progressions (20+ interviews)
- [ ] **9.6** Verify code stability and theoretical development
- [ ] **9.7** Test batch mixing strategies and their effectiveness

### **Day 10: Output Generation & Reporting TDD**

#### Morning (4 hours)
- [ ] **10.1** Write output generation tests:
  - [ ] test_markdown_report_generation()
  - [ ] test_json_export_completeness()
  - [ ] test_csv_export_for_analysis()
- [ ] **10.2** Implement qc/output/report_generator.py
- [ ] **10.3** Create template systems for different output formats:
  - [ ] **Markdown templates with exemplar quote chains**
  - [ ] **CSV export templates with full traceability**
  - [ ] **JSON structured output with stakeholder analysis**

#### Afternoon (4 hours)
- [ ] **10.4** Write advanced reporting tests:
  - [ ] test_policy_brief_generation()
  - [ ] test_contradiction_detection()
  - [ ] test_stakeholder_mapping()
  - [ ] **test_quote_chain_analysis()** (progression of related quotes)
  - [ ] **test_code_development_chains()** (how codes evolve)
  - [ ] **test_full_csv_traceability()** (all quotes traceable to source)
- [ ] **10.5** Implement LLM-driven report enhancement features
- [ ] **10.6** Test report quality with real interview data

### **Day 11: CLI Integration & User Experience TDD**

#### Morning (4 hours)
- [ ] **11.1** Write CLI integration tests:
  - [ ] test_cli_single_file_processing()
  - [ ] test_cli_directory_batch_processing()
  - [ ] test_cli_configuration_options()
  - [ ] test_cli_progress_reporting()
- [ ] **11.2** Implement/enhance CLI interface
- [ ] **11.3** Add comprehensive progress tracking

#### Afternoon (4 hours)
- [ ] **11.4** Write user experience tests:
  - [ ] test_error_message_clarity()
  - [ ] test_configuration_validation()
  - [ ] test_help_system_completeness()
- [ ] **11.5** Implement user-friendly error messages
- [ ] **11.6** Create comprehensive documentation
- [ ] **11.7** Test full user workflows end-to-end

### **Day 12: Final Integration & Production Readiness**

#### Morning (4 hours)
- [ ] **12.1** Write comprehensive integration tests:
  - [ ] test_full_103_interview_processing()
  - [ ] test_production_error_scenarios()
  - [ ] test_data_integrity_across_full_pipeline()
- [ ] **12.2** Run complete test suite and fix any failures
- [ ] **12.3** Performance tune based on full-scale testing

#### Afternoon (4 hours)
- [ ] **12.4** Write deployment tests:
  - [ ] test_docker_containerization()
  - [ ] test_environment_variable_configuration()
  - [ ] test_production_deployment_readiness()
- [ ] **12.5** Create deployment documentation
- [ ] **12.6** Final code review and cleanup
- [ ] **12.7** Tag release version and create release notes

---

## 🧪 **PHASE 4: COMPREHENSIVE TESTING & VALIDATION (Days 13-15)**

### **Day 13: Full System Validation**

#### Morning (4 hours)
- [ ] **13.1** Run complete test suite (all 200+ tests)
- [ ] **13.2** Process all 18 AI interviews end-to-end
- [ ] **13.3** Process all 85 Africa interviews end-to-end
- [ ] **13.4** Validate output quality and theoretical coherence

#### Afternoon (4 hours)
- [ ] **13.5** Performance validation:
  - [ ] Measure actual processing times
  - [ ] Validate API usage efficiency
  - [ ] Test memory usage and resource consumption
- [ ] **13.6** Generate comprehensive validation report
- [ ] **13.7** Document any limitations or areas for improvement

### **Day 14: Security & Robustness Testing**

#### Morning (4 hours)
- [ ] **14.1** Security testing:
  - [ ] Test API key security
  - [ ] Test data privacy and protection
  - [ ] Test input validation and sanitization
- [ ] **14.2** Robustness testing:
  - [ ] Test with corrupted interview files
  - [ ] Test with extreme edge cases
  - [ ] Test system recovery after crashes

#### Afternoon (4 hours)
- [ ] **14.3** Load testing:
  - [ ] Test with maximum API rate limits
  - [ ] Test with large batches of interviews
  - [ ] Test concurrent processing scenarios
- [ ] **14.4** Document security and robustness characteristics
- [ ] **14.5** Create incident response procedures

### **Day 15: Documentation & Knowledge Transfer**

#### Morning (4 hours)
- [ ] **15.1** Complete technical documentation:
  - [ ] API documentation
  - [ ] Architecture documentation
  - [ ] Testing documentation
- [ ] **15.2** Create user guides:
  - [ ] Installation guide
  - [ ] User manual
  - [ ] Troubleshooting guide

#### Afternoon (4 hours)
- [ ] **15.3** Create training materials:
  - [ ] Video tutorials
  - [ ] Example workflows
  - [ ] Best practices guide
- [ ] **15.4** Final project review and handoff preparation
- [ ] **15.5** Archive all development artifacts
- [ ] **15.6** Project completion celebration! 🎉

---

## 📊 **SUCCESS CRITERIA**

### **Technical Criteria**
- [ ] All 103 interview files process successfully
- [ ] Three-phase coding works with real Gemini API
- [ ] Neo4j integration stores and retrieves data correctly
- [ ] Error recovery handles all failure scenarios gracefully
- [ ] Performance meets requirements (1M tokens/minute limit)
- [ ] Output quality meets qualitative research standards

### **Testing Criteria**  
- [ ] 95%+ test coverage across all modules
- [ ] All tests pass consistently
- [ ] Integration tests use real data, API, and database
- [ ] Performance tests validate scalability
- [ ] Error handling tests validate robustness

### **Research Tool Criteria**
- [ ] Simple local execution (no Docker required)
- [ ] Configuration via environment variables
- [ ] Clear logging for debugging
- [ ] User-friendly CLI interface
- [ ] Complete documentation for research use

### **Quality Criteria**
- [ ] Code follows established patterns and conventions
- [ ] Proper grounded theory methodology implementation
- [ ] Output suitable for academic/policy research
- [ ] Theoretical coherence and validity maintained

### **Chain Analysis & Traceability Criteria**
- [ ] **Quote chains show progression of ideas** across interviews
- [ ] **Code development patterns** tracked from initial mention to resolution
- [ ] **All findings linked to exemplar quotes** with exact line numbers
- [ ] **Stakeholder positions** supported by evidence chains
- [ ] **Contradictions documented** with opposing quote sequences
- [ ] **Full CSV traceability** - every insight traceable to source quotes
- [ ] **Markdown reports use exemplar chains** for all key findings

---

## 🎯 **DAILY WORKFLOW**

### **Each Day Structure**
1. **Morning standup** (15 min): Review previous day, plan current day
2. **TDD cycles** (45 min work + 15 min break): Red-Green-Refactor methodology
3. **Integration testing** (1 hour): Test with real data after each major component
4. **Documentation updates** (30 min): Keep docs current with implementation
5. **End-of-day review** (15 min): Update progress, plan next day

### **TDD Cycle Process**
1. **RED**: Write failing test that defines desired behavior
2. **GREEN**: Write minimal code to make test pass
3. **REFACTOR**: Improve code quality while keeping tests green
4. **INTEGRATE**: Test with real data/API/database
5. **DOCUMENT**: Update documentation and comments

### **Quality Gates**
- No code commits without passing tests
- No new features without integration testing
- No day ends without working end-to-end pipeline
- No phase completion without comprehensive error handling

### **Original Development Standards**
- **NO lazy mocking/stubs/fallbacks/pseudo code** - Every implementation must be fully functional
- **NO simplified implementations** - Build complete functionality or don't build it  
- **NO hiding errors** - All errors must surface immediately with clear context
- **Fail-fast approach** - Code must fail immediately on invalid inputs rather than degrading gracefully
- **NO temporary workarounds** - Fix root causes, not symptoms
- **Evidence-Based Development** - Nothing is working until proven working with logs
- **TDD mandatory** - Write tests FIRST, then implementation, then verify
- **100% functionality preserved** - No regressions during refactoring
- **Complete test coverage** - >95% coverage on all modified code
- **Production-ready only** - Every change must be deployment-ready

---

## 📋 **ENHANCED OUTPUT SPECIFICATIONS**

### **Complete CSV Export Structure**
1. **quote_evidence.csv** - Full quote traceability with line numbers and context
2. **quote_chains.csv** - Sequential quote progressions showing idea development  
3. **code_progression.csv** - How codes evolve from initial mention to resolution
4. **stakeholder_positions.csv** - Policy positions with supporting evidence chains
5. **contradiction_matrix.csv** - Opposing viewpoints with evidence from both sides
6. **theme_analysis.csv** - Theme statistics with exemplar quote references

### **Enhanced Markdown Reports**
- **Every finding supported by exemplar quote chains**
- **Contradictions show opposing evidence sequences**
- **Progressive development patterns with quote progressions**
- **Stakeholder analysis with position-supporting chains**
- **All insights linked to traceable source quotes**

### **JSON Output Enhancements**
- **Quote chain objects** with progression analysis  
- **Code development objects** tracking evolution patterns
- **Stakeholder position objects** with evidence arrays
- **Contradiction objects** with opposing quote sequences
- **Full line number mapping** for every extracted quote

---

This roadmap takes us from current state (foundation components) to production-ready system in 15 days using rigorous TDD methodology with real systems throughout, ensuring **full traceability** from every insight back to specific interview quotes with **exemplar chain analysis** throughout.