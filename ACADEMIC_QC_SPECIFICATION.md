# Academic-Grade Qualitative Coding System Specification

## Core Philosophy

**"Autonomous Policy Analysis"** - AI-driven system for processing large-scale policy consultations and interviews efficiently while maintaining analytical rigor.

## UPDATED IMPLEMENTATION PLAN: Three-Mode Adaptive System for Policy Analysis

### Core Design: Flexible Coding Modes

1. **OPEN MODE (Thematic Analysis)**
   - Codes emerge from data
   - No predefined categories
   - Exploratory approach
   - "Let the data speak"

2. **CLOSED MODE (Framework Analysis)**  
   - Strict predefined categories only
   - Test existing frameworks
   - Deductive approach
   - Structured analysis

3. **HYBRID MODE (Best of Both)**
   - Start with framework
   - Allow emergent codes
   - Track predefined vs emergent
   - Framework evolution

### Goal-Oriented vs Exploratory Analysis

- **Directed**: "I want to understand X" - focused analysis
- **Exploratory**: "What emerges from the data?" - open discovery

### Key Features to Implement

1. **Iterative Hermeneutic Cycles** ✓
   - Re-read same data with evolved understanding
   - NOT the same as constant comparison
   - 2-3 cycles per interview

2. **Constant Comparison** (for Grounded Theory mode)
   - Compare new segments with existing codes
   - Optional based on methodology

3. **Negative Case Analysis** ✓
   - Actively seek contradicting evidence
   - Refine theories based on exceptions

4. **Theoretical Sampling Guidance** ✓
   - What data to collect next
   - Based on theory gaps

5. **Comprehensive Audit Trail** ✓
   - Every coding decision recorded
   - Rationale and alternatives tracked

6. **Meaningful Report Generation** ✓
   - Academic-quality outputs
   - Full data export capability

### Dual-Layer Architecture with Batch Processing

**Two Distinct Analytical Layers**:
1. **Qualitative Layer** - Themes, codes, meanings (interpretive)
2. **Knowledge Layer** - Entities, facts, relationships (factual)

**Three-Phase Aggregation Architecture**:
- **Phase 1**: Parallel unconstrained coding (capture everything)
- **Phase 2**: Intelligent aggregation (deduplicate, hierarchize, refine)
- **Phase 3**: Consistent final coding (apply refined codebook)
- **Batch size**: Configurable via MAX_BATCH_TOKENS (default 200K)
- **Processing**: Automatic batching based on token count

**Key Features**:
- Both layers support OPEN/CLOSED/HYBRID modes independently
- Process multiple interviews in single LLM calls
- Clear naming conventions (CODE_* vs ENT_*)
- Cross-layer linking for rich insights
- True saturation detection across full dataset

**Example Configuration**:
```python
analyzer = BatchDualLayerExtractor(
    qual_mode=CodingMode.OPEN,       # Let themes emerge
    entity_mode=CodingMode.HYBRID,    # Use predefined + emergent entities
    batch_size_tokens=os.getenv('MAX_BATCH_TOKENS', 200_000),  # From config
    entity_schema=POLICY_ENTITY_SCHEMA # Include policy-specific types
)

# Process all provided interviews
results = await analyzer.analyze_project(interviews)
# Automatic batching and parallel processing
```

### Policy-Specific Entity Types
```python
POLICY_ENTITY_SCHEMA = {
    # Base types
    "person": {"properties": ["role", "department", "stakeholder_type"]},
    "organization": {"properties": ["type", "sector", "size"]},
    "tool": {"properties": ["category", "purpose"]},
    "method": {"properties": ["approach", "domain"]},
    
    # Policy-specific types
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

---

## Essential Architecture Components

### 1. **Data Architecture**

```python
class ResearchProject:
    """Complete research project container"""
    
    # Data Sources
    interviews: List[Interview]
    observations: List[FieldNote]
    documents: List[Document]
    media: List[MediaFile]
    
    # Organization
    cases: List[Case]  # Participants/sites with attributes
    waves: List[DataWave]  # For longitudinal studies
    
    # Analysis
    codebook: EvolvingCodebook
    memos: MemoSystem
    theories: List[EmergingTheory]
    
    # Meta
    methodology: MethodologyConfig
    researchers: List[Researcher]
    audit_trail: CompleteAuditTrail

class Case:
    """Individual participant/site/unit of analysis"""
    id: str
    attributes: Dict[str, Any]  # Demographics, context
    data_sources: List[DataSource]
    case_summary: CaseMemo
    
class DataSource:
    """Any source of data with full context"""
    id: str
    type: DataType
    case_id: str
    collection_date: datetime
    collector: Researcher
    context: Dict[str, Any]
    transcription_notes: Optional[str]
    
    # Key feature: Segments can overlap and have multiple codes
    segments: List[Segment]
    
class Segment:
    """Unit of meaning - can be any size"""
    id: str
    start: Position  # Character, time, or paragraph
    end: Position
    text: str
    
    # Multiple coding perspective
    codings: List[Coding]  # Same segment can have multiple interpretations
    
class Coding:
    """Single coding decision with full context"""
    code_id: str
    segment_id: str
    coder: Researcher
    timestamp: datetime
    confidence: float
    rationale: str  # Why this code?
    
    # Relationships to other codings
    supports: List[str]  # Other coding IDs this supports
    contradicts: List[str]  # Other coding IDs this challenges
    
    # Theoretical significance
    theoretical_importance: ImportanceLevel
    contributes_to_pattern: Optional[str]
```

### 2. **Methodological Framework System**

```python
class MethodologyFramework:
    """Configurable methodology that guides the analysis"""
    
    def __init__(self, approach: str):
        self.approach = approach  # 'grounded_theory', 'thematic_analysis', etc.
        self.phases = self._load_phases()
        self.quality_criteria = self._load_criteria()
        
    def get_current_phase_guidance(self, project_state: ProjectState) -> Guidance:
        """What should researcher do next?"""
        current_phase = self._determine_phase(project_state)
        
        return Guidance(
            phase_name=current_phase.name,
            objectives=current_phase.objectives,
            suggested_actions=self._suggest_actions(project_state),
            quality_checks=self._get_quality_checks(current_phase),
            warnings=self._check_methodological_violations(project_state)
        )
    
    def validate_coding_decision(self, coding: Coding, context: CodingContext) -> Validation:
        """Is this coding decision methodologically sound?"""
        if self.approach == 'grounded_theory':
            return self._validate_grounded_theory_coding(coding, context)
        elif self.approach == 'ipa':
            return self._validate_ipa_coding(coding, context)
        # etc.

class GroundedTheoryFramework(MethodologyFramework):
    def _validate_grounded_theory_coding(self, coding, context):
        checks = []
        
        # Is it grounded in data?
        if not coding.rationale_references_text():
            checks.append("Code should emerge from data, not impose external concepts")
            
        # Constant comparison performed?
        if not context.compared_with_existing:
            checks.append("Compare with previously coded segments")
            
        # Moving toward theoretical saturation?
        if self._is_just_repeating_codes(coding, context):
            checks.append("Consider if theoretical saturation reached")
            
        return ValidationResult(checks)
```

### 3. **Intelligent Coding Assistant**

```python
class CodingAssistant:
    """AI that assists but doesn't replace human judgment"""
    
    def analyze_segment(self, segment: Segment, context: ProjectContext) -> CodingAssistance:
        """Provide intelligent assistance for coding decision"""
        
        # What would different methodologies see here?
        perspectives = {
            'phenomenological': self._phenomenological_reading(segment),
            'narrative': self._narrative_reading(segment),
            'discursive': self._discourse_reading(segment),
            'grounded': self._grounded_reading(segment)
        }
        
        # Based on project methodology, emphasize relevant perspective
        primary_perspective = perspectives[context.methodology.approach]
        
        # Find similar segments
        similar_segments = self._find_conceptually_similar(segment, context)
        
        # Identify what's unique
        unique_elements = self._identify_unique_aspects(segment, similar_segments)
        
        # Check for theoretical significance
        theoretical_links = self._find_theoretical_connections(segment, context.emerging_theories)
        
        return CodingAssistance(
            suggested_codes=self._suggest_codes_with_rationale(segment, context),
            similar_segments=similar_segments,
            unique_aspects=unique_elements,
            theoretical_significance=theoretical_links,
            questions_for_researcher=self._generate_reflexive_questions(segment),
            potential_negative_case=self._check_if_negative_case(segment, context),
            methodological_prompts=self._get_methodology_specific_prompts(segment, context)
        )
    
    def _generate_reflexive_questions(self, segment: Segment) -> List[str]:
        """Prompt researcher reflexivity"""
        return [
            "What assumptions are you bringing to this interpretation?",
            "How might your background influence how you read this?",
            "What alternative interpretations are possible?",
            "What is the participant NOT saying here?",
            "How does this relate to your theoretical framework?"
        ]
```

### 4. **Collaborative Coding System**

```python
class CollaborativeCodingSystem:
    """Support team-based coding with reliability"""
    
    def parallel_code(self, segment: Segment, coders: List[Researcher]) -> ParallelCodingResult:
        """Multiple coders code same segment"""
        codings = []
        
        for coder in coders:
            # Each coder works independently
            coding = self._get_coding_from_coder(segment, coder)
            codings.append(coding)
            
        # Calculate agreement
        reliability = self._calculate_reliability(codings)
        
        # Identify agreements and disagreements
        analysis = self._analyze_coding_patterns(codings)
        
        return ParallelCodingResult(
            codings=codings,
            reliability_scores={
                'percent_agreement': analysis.percent_agreement,
                'cohens_kappa': analysis.kappa,
                'krippendorff_alpha': analysis.alpha
            },
            agreements=analysis.agreements,
            disagreements=analysis.disagreements,
            resolution_needed=analysis.conflicts
        )
    
    def resolve_disagreement(self, disagreement: CodingDisagreement) -> Resolution:
        """Facilitate resolution of coding disagreements"""
        
        # Get each coder's rationale
        rationales = [c.rationale for c in disagreement.codings]
        
        # AI analyzes the disagreement
        analysis = self._analyze_disagreement(disagreement)
        
        # Suggest resolution strategies
        if analysis.is_complementary:
            # Both codes might apply
            suggestion = "Consider applying both codes as they capture different aspects"
        elif analysis.is_hierarchical:
            # One code might be parent of other
            suggestion = f"Consider making '{analysis.broader_code}' parent of '{analysis.narrower_code}'"
        elif analysis.is_definitional:
            # Code definitions might need clarification
            suggestion = "Review and clarify code definitions"
        else:
            # True disagreement
            suggestion = "Discuss theoretical implications of each interpretation"
            
        return Resolution(
            analysis=analysis,
            suggestion=suggestion,
            discussion_prompts=self._generate_discussion_prompts(disagreement)
        )
```

### 5. **Theory Building Engine**

```python
class TheoryBuildingEngine:
    """Support theory development from coded data"""
    
    def analyze_patterns(self, project: ResearchProject) -> TheoreticalAnalysis:
        """Identify patterns that might indicate theory"""
        
        patterns = []
        
        # Frequency is just the start
        frequency_patterns = self._analyze_code_frequency(project)
        
        # Conceptual density matters more
        conceptual_patterns = self._analyze_conceptual_density(project)
        
        # Relationships between codes
        relationship_patterns = self._analyze_code_relationships(project)
        
        # Temporal patterns (for process theories)
        temporal_patterns = self._analyze_temporal_sequences(project)
        
        # Conditional patterns (X occurs when Y)
        conditional_patterns = self._analyze_conditions(project)
        
        # Negative cases that don't fit
        negative_cases = self._identify_negative_cases(project)
        
        return TheoreticalAnalysis(
            patterns=patterns,
            emerging_concepts=self._identify_emerging_concepts(patterns),
            theoretical_gaps=self._identify_gaps(patterns),
            rival_explanations=self._generate_rival_explanations(patterns),
            testable_propositions=self._formulate_propositions(patterns)
        )
    
    def theoretical_sampling_guidance(self, current_theory: EmergingTheory) -> SamplingGuidance:
        """What data to collect next to develop theory"""
        
        # Where is theory weak?
        weak_areas = self._identify_weak_areas(current_theory)
        
        # What would challenge theory?
        challenging_cases = self._suggest_challenging_cases(current_theory)
        
        # What would extend theory?
        extending_cases = self._suggest_extending_cases(current_theory)
        
        return SamplingGuidance(
            priority_areas=weak_areas,
            suggested_case_types=challenging_cases + extending_cases,
            interview_questions=self._generate_theoretical_questions(current_theory),
            saturation_assessment=self._assess_saturation(current_theory)
        )
```

### 6. **Query and Analysis System**

```python
class QuerySystem:
    """Complex queries for analysis"""
    
    def query(self, query_string: str, project: ResearchProject) -> QueryResult:
        """Natural language or structured queries"""
        
        # Parse query intent
        intent = self._parse_query_intent(query_string)
        
        if intent.type == 'co_occurrence':
            return self._query_co_occurrence(intent.params, project)
        elif intent.type == 'comparison':
            return self._query_comparison(intent.params, project)
        elif intent.type == 'trajectory':
            return self._query_trajectory(intent.params, project)
        # etc.
    
    def matrix_query(self, rows: QueryDimension, cols: QueryDimension, 
                     cells: AggregationFunction) -> Matrix:
        """Create analysis matrices"""
        
        # Example: Codes (rows) by Cases (cols) showing frequency
        # Example: Themes (rows) by Time Period (cols) showing evolution
        # Example: Codes (rows) by Researcher (cols) showing coding patterns
        
        matrix = self._build_matrix(rows, cols)
        self._populate_cells(matrix, cells)
        return matrix
    
    def proximity_analysis(self, code1: str, code2: str) -> ProximityResult:
        """How often do codes appear near each other?"""
        
        proximities = []
        for segment in self._get_all_segments():
            if code1 in segment.codes:
                nearby = self._find_nearby_segments(segment)
                for near in nearby:
                    if code2 in near.codes:
                        proximities.append(self._calculate_proximity(segment, near))
                        
        return ProximityResult(proximities)
```

### 7. **Visualization and Reporting**

```python
class VisualizationEngine:
    """Create academic-grade visualizations"""
    
    def create_code_network(self, project: ResearchProject) -> NetworkDiagram:
        """Interactive code relationship network"""
        nodes = self._create_code_nodes(project.codebook)
        edges = self._calculate_relationships(project)
        
        return NetworkDiagram(
            nodes=nodes,
            edges=edges,
            layout_algorithm='force_directed',
            interactive=True,
            exportable_formats=['svg', 'png', 'graphml']
        )
    
    def create_theoretical_model(self, theory: EmergingTheory) -> TheoryDiagram:
        """Visual representation of emerging theory"""
        
        # Core category at center
        # Related categories around
        # Conditions, consequences, strategies positioned meaningfully
        # Arrows showing relationships
        
        return TheoryDiagram(theory)
    
    def generate_audit_trail_report(self, project: ResearchProject) -> AuditReport:
        """Complete methodological audit trail"""
        
        return AuditReport(
            coding_decisions=self._document_all_decisions(project),
            code_evolution=self._track_code_changes(project),
            theoretical_development=self._track_theory_emergence(project),
            reflexivity_notes=self._compile_reflexivity(project),
            methodology_adherence=self._check_methodology_compliance(project)
        )
```

### 8. **Export and Integration System**

```python
class ExportSystem:
    """Integration with academic workflows"""
    
    def export_for_publication(self, project: ResearchProject) -> PublicationPackage:
        """Generate publication-ready materials"""
        
        return PublicationPackage(
            methods_section=self._generate_methods_section(project),
            findings_section=self._generate_findings_section(project),
            evidence_table=self._create_evidence_table(project),
            supplementary_materials=self._create_supplementary(project),
            prisma_diagram=self._create_prisma_if_applicable(project),
            coreq_checklist=self._complete_coreq_checklist(project)
        )
    
    def export_to_stats(self, project: ResearchProject, format: str) -> StatsFile:
        """Export for mixed methods analysis"""
        
        if format == 'spss':
            return self._export_to_spss(project)
        elif format == 'r':
            return self._export_to_r(project)
        elif format == 'stata':
            return self._export_to_stata(project)
```

---

## Critical Success Factors

### 1. **Transparency**
Every AI suggestion must explain its reasoning in terms researchers understand.

### 2. **Flexibility**
Support multiple methodologies without forcing one approach.

### 3. **Rigor**
Build quality checks into the workflow, don't rely on post-hoc validation.

### 4. **Collaboration**
Team coding is the norm in academic research, not the exception.

### 5. **Integration**
Must work with existing academic workflows, not replace them.

### 6. **Learning**
System should learn from researcher corrections, not just apply generic patterns.

---

## Implementation Priority

### Phase 1: Foundation (MVP)
- Multi-pass coding
- Hierarchical codebook with definitions
- Basic memo system
- Simple query system
- Audit trail

### Phase 2: Academic Essentials  
- Team coding with reliability
- Constant comparison
- Multiple methodology support
- Advanced memo types
- Code evolution tracking

### Phase 3: Advanced Features
- Theory building tools
- Visual modeling
- Complex queries
- Statistical export
- Publication support

### Phase 4: Innovation
- Adaptive AI that learns from each project
- Real-time collaborative coding
- Automated literature integration
- Hypothesis testing
- Predictive theoretical sampling

---

## The Bottom Line

A policy-focused QC system must:
1. **Process at scale** - Handle large public consultations efficiently
2. **Extract actionable insights** - Identify patterns for policy decisions
3. **Track stakeholder positions** - Understand different group perspectives
4. **Maintain transparency** - Provide audit trails for public accountability
5. **Enable evidence-based policy** - Support data-driven decision making

It's about autonomous processing of large-scale qualitative data to inform policy decisions.

## Future Research Areas

The following features are not included in v1 but could be valuable additions:
- **Researcher Reflexivity** - Tracking positionality and bias evolution
- **Inter-Rater Reliability** - Cohen's Kappa for contested policy areas
- **Literature Integration** - Linking to existing policy frameworks