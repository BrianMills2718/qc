"""
Unified domain model for the qualitative coding system.

All analysis state lives inside a ProjectState -- a single Pydantic model
that can be saved/loaded as JSON. No database required.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Provenance(str, Enum):
    """Who created this artifact."""
    LLM = "llm"
    HUMAN = "human"
    SYSTEM = "system"


class ReviewAction(str, Enum):
    """Actions a human reviewer can take."""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    MERGE = "merge"
    SPLIT = "split"


class ClaimKind(str, Enum):
    """Types of substantive analytic claims recorded in the INV-9 ledger."""
    CODE = "code"
    CODE_APPLICATION = "code_application"
    PERSPECTIVE = "perspective"
    RELATIONSHIP = "relationship"
    SYNTHESIS_FINDING = "synthesis_finding"
    CROSS_CASE = "cross_case"
    NEGATIVE_CASE = "negative_case"
    GT_CATEGORY = "gt_category"
    GT_PROPOSITION = "gt_proposition"
    NO_CLAIMS_EVENT = "no_claims_event"


class ClaimSupportStatus(str, Enum):
    """Whether a claim currently has adequate source support."""
    SUPPORTED = "supported"
    NEEDS_ANCHOR = "needs_anchor"
    UNSUPPORTED = "unsupported"
    MIXED = "mixed"
    CONTRADICTED = "contradicted"


class ClaimAdjudicationStatus(str, Enum):
    """Human/agent adjudication state for an analytic claim."""
    PENDING = "pending"
    RETAINED = "retained"
    REVISED = "revised"
    WITHDRAWN = "withdrawn"
    NEEDS_REVIEW = "needs_review"


class ObservedPatternKind(str, Enum):
    """Descriptive pattern types derived from observed coding artifacts."""
    CONSENSUS_CODE = "consensus_code"
    DIVERGENT_CODE = "divergent_code"
    CODE_CO_OCCURRENCE = "code_co_occurrence"


class CausalInterpretationStatus(str, Enum):
    """How far a descriptive pattern has moved toward causal interpretation."""
    DESCRIPTIVE_ONLY = "descriptive_only"
    CANDIDATE_EXPLANATION_GENERATED = "candidate_explanation_generated"
    TESTED_BY_PROCESS_TRACING = "tested_by_process_tracing"
    ELIGIBLE_FOR_CROSS_CASE_MODEL = "eligible_for_cross_case_model"


class AbductiveExplanationStatus(str, Enum):
    """Review and promotion status for an abductive candidate explanation."""
    CANDIDATE = "candidate"
    NEEDS_EVIDENCE_REVIEW = "needs_evidence_review"
    REJECTED = "rejected"
    PROMOTED_TO_PROCESS_TRACING = "promoted_to_process_tracing"


class PipelineStatus(str, Enum):
    """Status of a pipeline stage."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED_FOR_REVIEW = "paused_for_review"
    FAILED = "failed"
    SKIPPED = "skipped"


class Methodology(str, Enum):
    """Supported analysis methodologies."""
    THEMATIC_ANALYSIS = "thematic_analysis"
    GROUNDED_THEORY = "grounded_theory"
    DEFAULT = "default"


# ---------------------------------------------------------------------------
# Document layer
# ---------------------------------------------------------------------------

class Document(BaseModel):
    """A source document (interview transcript, etc.)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    detected_speakers: List[str] = Field(default_factory=list)
    is_truncated: bool = False


class Corpus(BaseModel):
    """Collection of documents being analyzed."""
    documents: List[Document] = Field(default_factory=list)

    def add_document(self, doc: Document) -> None:
        self.documents.append(doc)

    def get_document(self, doc_id: str) -> Optional[Document]:
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None

    @property
    def num_documents(self) -> int:
        return len(self.documents)


class CorpusScope(BaseModel):
    """Analytic boundary for interpreting corpus-level claims."""
    phenomenon: str = Field(
        default="",
        description="Phenomenon, topic, or research question the analysis is scoped to.",
    )
    population: str = Field(
        default="",
        description="Population, community, or case universe that claims may apply to.",
    )
    sampling_frame: str = Field(
        default="",
        description="How the source documents or participants were selected for the corpus.",
    )
    inclusion_criteria: List[str] = Field(
        default_factory=list,
        description="Criteria that qualified documents or participants for inclusion.",
    )
    exclusion_criteria: List[str] = Field(
        default_factory=list,
        description="Criteria that ruled documents or participants out of scope.",
    )
    notes: str = Field(
        default="",
        description="Additional caveats, scope conditions, or boundary notes.",
    )


# ---------------------------------------------------------------------------
# Codebook layer
# ---------------------------------------------------------------------------

class Code(BaseModel):
    """A qualitative code."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    definition: str = ""
    parent_id: Optional[str] = None
    level: int = 0
    properties: List[str] = Field(default_factory=list)
    dimensions: List[str] = Field(default_factory=list)
    provenance: Provenance = Provenance.LLM
    version: int = 1
    example_quotes: List[str] = Field(default_factory=list)
    mention_count: int = 0
    confidence: float = 0.0
    reasoning: str = ""


class Codebook(BaseModel):
    """Versioned set of codes."""
    version: int = 1
    methodology: str = "default"
    created_by: Provenance = Provenance.LLM
    codes: List[Code] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    def get_code(self, code_id: str) -> Optional[Code]:
        for code in self.codes:
            if code.id == code_id:
                return code
        return None

    def get_code_by_name(self, name: str) -> Optional[Code]:
        for code in self.codes:
            if code.name == name:
                return code
        return None

    def top_level_codes(self) -> List[Code]:
        return [c for c in self.codes if c.parent_id is None]

    def children_of(self, code_id: str) -> List[Code]:
        return [c for c in self.codes if c.parent_id == code_id]


# ---------------------------------------------------------------------------
# Code applications (quote-to-code assignments)
# ---------------------------------------------------------------------------

class CodeApplication(BaseModel):
    """A code applied to a specific passage."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code_id: str
    doc_id: str
    quote_text: str
    speaker: Optional[str] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    quote_hash: Optional[str] = None  # sha256 of doc.content[start_char:end_char] (INV-1)
    confidence: float = 0.0
    applied_by: Provenance = Provenance.LLM
    codebook_version: int = 1


# ---------------------------------------------------------------------------
# Code relationships
# ---------------------------------------------------------------------------

class Segment(BaseModel):
    """One examined textual unit of a document (the INV-8 denominator).

    Char offsets index the original ``Document.content`` so coverage and
    agreement can be computed against a stable, examinable set of units.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    index: int = 0
    start_char: int = 0
    end_char: int = 0
    speaker: str = ""
    text: str = ""
    # Exhaustive-coding decision (INV-8): None = not examined, "coded" = >=1 code
    # applied, "no_code" = examined but no code applies. Distinguishes
    # "not relevant" from "never examined".
    decision: Optional[str] = None


class CodeRelationship(BaseModel):
    """Relationship between two codes."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_code_id: str
    target_code_id: str
    relationship_type: str = "related_to"
    strength: float = 0.0
    evidence: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    consequences: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

class Entity(BaseModel):
    """A named entity extracted from the corpus."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    entity_type: str = "concept"  # person, organization, concept, tool, etc.
    description: str = ""
    doc_ids: List[str] = Field(default_factory=list)


class DomainEntityRelationship(BaseModel):
    """Relationship between two entities."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_1_id: str
    entity_2_id: str
    relationship_type: str
    strength: float = 0.0
    supporting_evidence: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Analysis artifacts
# ---------------------------------------------------------------------------

class AnalysisMemo(BaseModel):
    """Analytical memo."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    memo_type: str = "theoretical"  # theoretical, methodological, pattern, cross_case
    title: str = ""
    content: str = ""
    code_refs: List[str] = Field(default_factory=list)
    doc_refs: List[str] = Field(default_factory=list)
    created_by: Provenance = Provenance.LLM
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ObservedPattern(BaseModel):
    """A first-class descriptive pattern observed in the analyzed corpus.

    Patterns are accounting objects, not causal claims. They may become inputs to
    later abductive or process-tracing stages, but they default to descriptive
    status and must not be reported as causal proof.
    """
    id: str = Field(default_factory=lambda: f"pattern_{uuid.uuid4()}")
    source_stage: str = Field(description="Pipeline stage or component that produced this pattern")
    pattern_kind: ObservedPatternKind = Field(description="Kind of descriptive pattern observed")
    summary: str = Field(description="Human-readable description of the observed pattern")
    code_ids: List[str] = Field(default_factory=list, description="Code IDs involved in the pattern")
    doc_ids: List[str] = Field(default_factory=list, description="Document IDs in the pattern scope")
    application_ids: List[str] = Field(default_factory=list, description="CodeApplication IDs supporting the pattern")
    support_anchors: List[ClaimAnchor] = Field(default_factory=list, description="Source spans supporting the pattern when available")
    strength: Optional[float] = Field(default=None, description="Descriptive strength within the observed denominator, when applicable")
    count: int = Field(default=0, description="Observed count for this pattern within the producing stage's denominator")
    total: int = Field(default=0, description="Denominator count used by the producing stage, when applicable")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional stage-specific descriptive metadata")
    causal_interpretation_status: CausalInterpretationStatus = Field(
        default=CausalInterpretationStatus.DESCRIPTIVE_ONLY,
        description="Interpretive status; defaults to descriptive-only and is not causal proof.",
    )
    created_by: Provenance = Field(default=Provenance.SYSTEM, description="Who produced this pattern")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class AbductiveCandidateExplanation(BaseModel):
    """A provisional explanation candidate generated from observed patterns.

    Candidate explanations are hypotheses for review and future process tracing.
    They are not causal proof and are not promoted into analytic claims by
    default.
    """
    id: str = Field(default_factory=lambda: f"abductive_{uuid.uuid4()}")
    source_stage: str = Field(description="Pipeline stage or component that produced this candidate")
    source_pattern_ids: List[str] = Field(description="ObservedPattern IDs this candidate attempts to explain")
    explanation_text: str = Field(description="Plain-language provisional explanation")
    mechanism_summary: str = Field(description="Concise mechanism or process implied by the explanation")
    rival_explanations: List[str] = Field(
        default_factory=list,
        description="Plausible alternative explanations that could account for the same pattern",
    )
    observable_implications: List[str] = Field(
        default_factory=list,
        description="What should be observable in the data or future process trace if this explanation is right",
    )
    evidence_gaps: List[str] = Field(
        default_factory=list,
        description="Missing evidence needed before this candidate could be treated as more than provisional",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional provisional confidence; not calibration evidence",
    )
    status: AbductiveExplanationStatus = Field(
        default=AbductiveExplanationStatus.CANDIDATE,
        description="Candidate review/promotion status; defaults to provisional candidate",
    )
    created_by: Provenance = Field(default=Provenance.LLM, description="Who produced this candidate")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ClaimAnchor(BaseModel):
    """A source-span reference supporting or contradicting an analytic claim."""
    doc_id: str = Field(description="Document containing the anchored evidence span")
    start_char: Optional[int] = Field(default=None, description="Start offset in the source document")
    end_char: Optional[int] = Field(default=None, description="End offset in the source document")
    quote_text: str = Field(default="", description="Evidence text for human inspection")
    quote_hash: Optional[str] = Field(default=None, description="Hash of the anchored source span")
    segment_id: Optional[str] = Field(default=None, description="Segment ID when the anchor maps to INV-8 segment universe")
    code_application_id: Optional[str] = Field(default=None, description="CodeApplication ID when the anchor originates from a code application")


class ClaimScope(BaseModel):
    """The bounded analytic scope a claim applies to."""
    corpus_level: bool = Field(default=False, description="True when the claim is scoped to the analyzed corpus as a whole")
    claim_ids: List[str] = Field(default_factory=list, description="AnalyticClaim IDs this claim refers to or challenges")
    doc_ids: List[str] = Field(default_factory=list, description="Document IDs the claim is scoped to")
    code_ids: List[str] = Field(default_factory=list, description="Code IDs the claim refers to")
    segment_ids: List[str] = Field(default_factory=list, description="Segment IDs the claim refers to")
    application_ids: List[str] = Field(default_factory=list, description="CodeApplication IDs the claim refers to")
    entity_ids: List[str] = Field(default_factory=list, description="Entity IDs the claim refers to")
    relationship_ids: List[str] = Field(default_factory=list, description="Relationship IDs the claim refers to")
    participant_names: List[str] = Field(default_factory=list, description="Participant names or labels the claim refers to")


class ClaimRevision(BaseModel):
    """One retained revision/adjudication event for an analytic claim."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="System-assigned revision identifier")
    actor: Provenance = Field(description="Who performed the revision or adjudication action")
    action: str = Field(description="Action performed, such as approve, revise, withdraw, or challenge")
    rationale: str = Field(default="", description="Reason the action was taken")
    previous_claim_text: Optional[str] = Field(default=None, description="Claim text before the revision, if changed")
    new_claim_text: Optional[str] = Field(default=None, description="Claim text after the revision, if changed")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Revision timestamp")


class AnalyticClaim(BaseModel):
    """A first-class substantive analytic assertion (INV-9)."""
    id: str = Field(default_factory=lambda: f"claim_{uuid.uuid4()}", description="System-assigned claim identifier")
    claim_kind: ClaimKind = Field(description="Type of claim being represented")
    source_stage: str = Field(description="Pipeline stage or component that produced the claim")
    claim_text: str = Field(description="Human-readable analytic assertion")
    scope: ClaimScope = Field(default_factory=ClaimScope, description="Bounded scope of the claim")
    origin_object_type: str = Field(description="Domain object type the claim was derived from")
    origin_object_id: str = Field(description="Domain object ID or stable synthetic key the claim was derived from")
    supporting_anchors: List[ClaimAnchor] = Field(default_factory=list, description="Source spans that support the claim")
    contrary_anchors: List[ClaimAnchor] = Field(default_factory=list, description="Source spans that challenge or contradict the claim")
    support_status: ClaimSupportStatus = Field(default=ClaimSupportStatus.NEEDS_ANCHOR, description="Current support state for the claim")
    adjudication_status: ClaimAdjudicationStatus = Field(default=ClaimAdjudicationStatus.PENDING, description="Current adjudication state")
    revision_history: List[ClaimRevision] = Field(default_factory=list, description="Chronological review/revision history")
    created_by: Provenance = Field(default=Provenance.LLM, description="Who produced the initial claim")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Claim creation timestamp")


class HumanReviewDecision(BaseModel):
    """Record of a human review action."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_type: str  # "code", "code_application", "codebook", "claim"
    target_id: str
    action: ReviewAction
    rationale: str = ""
    new_value: Optional[Dict[str, Any]] = None
    is_active: bool = Field(
        default=True,
        description="True when this decision applies to the current target object.",
    )
    inactive_reason: str = Field(
        default="",
        description="Reason this decision is historical-only when is_active is false.",
    )
    inactive_at: Optional[str] = Field(
        default=None,
        description="Timestamp when this decision became historical-only.",
    )
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------------
# Pipeline tracking
# ---------------------------------------------------------------------------

class AnalysisPhaseResult(BaseModel):
    """Audit trail entry for a single pipeline phase."""
    phase_name: str
    status: PipelineStatus = PipelineStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    input_summary: Dict[str, Any] = Field(default_factory=dict)
    output_summary: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Speaker / Perspective analysis
# ---------------------------------------------------------------------------

class ParticipantPerspective(BaseModel):
    """A participant's perspective derived from analysis."""
    name: str
    role: str = ""
    characteristics: List[str] = Field(default_factory=list)
    perspective_summary: str = ""
    codes_emphasized: List[str] = Field(default_factory=list)
    doc_id: Optional[str] = None


class PerspectiveAnalysis(BaseModel):
    """Speaker/perspective analysis results."""
    participants: List[ParticipantPerspective] = Field(default_factory=list)
    consensus_themes: List[str] = Field(default_factory=list)
    divergent_viewpoints: List[str] = Field(default_factory=list)
    perspective_mapping: Dict[str, List[str]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------

class Recommendation(BaseModel):
    """An actionable recommendation."""
    title: str
    description: str = ""
    priority: str = "medium"
    supporting_themes: List[str] = Field(default_factory=list)


class Synthesis(BaseModel):
    """Final synthesis from the analysis."""
    executive_summary: str = ""
    key_findings: List[str] = Field(default_factory=list)
    cross_cutting_patterns: List[str] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    confidence_assessment: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Grounded Theory specific
# ---------------------------------------------------------------------------

class IRRCodingPass(BaseModel):
    """Record of a single coding pass for inter-rater reliability."""
    pass_index: int
    prompt_suffix: str
    model_name: str
    codes_discovered: List[str] = Field(default_factory=list)
    code_details: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str = ""


class IRRResult(BaseModel):
    """Inter-rater reliability analysis results."""
    num_passes: int
    passes: List[IRRCodingPass] = Field(default_factory=list)
    aligned_codes: List[str] = Field(default_factory=list)
    unmatched_codes: List[str] = Field(default_factory=list)
    coding_matrix: Dict[str, List[int]] = Field(default_factory=dict)
    percent_agreement: float = 0.0
    cohens_kappa: Optional[float] = None
    fleiss_kappa: Optional[float] = None
    gwet_ac1: Optional[float] = None
    interpretation: str = ""
    # Application-level agreement (requires exhaustive coding). Positive
    # application metrics compare segment x code cells; segment-decision metrics
    # compare coded/no_code/not_examined decisions over the segment universe.
    application_level: bool = False
    application_units: int = 0  # number of (segment, code) cells compared
    application_percent_agreement: Optional[float] = None
    application_cohens_kappa: Optional[float] = None
    application_fleiss_kappa: Optional[float] = None
    application_gwet_ac1: Optional[float] = None
    application_interpretation: str = ""
    application_matrix: Dict[str, List[int]] = Field(default_factory=dict)
    segment_decision_units: int = 0  # number of segment decision rows compared
    segment_decision_percent_agreement: Optional[float] = None
    segment_decision_cohens_kappa: Optional[float] = None
    segment_decision_fleiss_kappa: Optional[float] = None
    segment_decision_gwet_ac1: Optional[float] = None
    segment_decision_interpretation: str = ""
    segment_decision_matrix: Dict[str, List[str]] = Field(default_factory=dict)
    timestamp: str = ""


class StabilityResult(BaseModel):
    """Multi-run stability analysis results.

    Shows how consistently the LLM produces codes across identical runs,
    addressing non-determinism concerns for academic reviewers.
    """
    num_runs: int
    code_stability: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-code stability score: fraction of runs the code appeared in",
    )
    stable_codes: List[str] = Field(
        default_factory=list,
        description="Codes appearing in >= 80% of runs",
    )
    moderate_codes: List[str] = Field(
        default_factory=list,
        description="Codes appearing in 50-79% of runs",
    )
    unstable_codes: List[str] = Field(
        default_factory=list,
        description="Codes appearing in < 50% of runs",
    )
    overall_stability: float = 0.0
    coding_matrix: Dict[str, List[int]] = Field(default_factory=dict)
    run_details: List[Dict[str, Any]] = Field(default_factory=list)
    model_name: str = ""
    timestamp: str = ""


# ---------------------------------------------------------------------------
# Typed return models for pure functions
# ---------------------------------------------------------------------------

class CodebookChangeResult(BaseModel):
    """Result of comparing two codebooks."""
    pct_change: float = 0.0
    added_codes: List[str] = Field(default_factory=list)
    removed_codes: List[str] = Field(default_factory=list)
    modified_codes: List[str] = Field(default_factory=list)
    stable_codes: List[str] = Field(default_factory=list)
    old_code_count: int = 0
    new_code_count: int = 0


class SaturationCheckResult(BaseModel):
    """Result of a saturation check."""
    saturated: bool = False
    change_metrics: Optional[CodebookChangeResult] = None
    iteration: int = 1
    message: str = ""


class CategorySaturationDiagnostic(BaseModel):
    """Per-category diagnostic for grounded-theory category adequacy."""
    code_id: str = Field(description="Code/category identifier being assessed")
    code_name: str = Field(description="Human-readable code/category name")
    property_count: int = Field(description="Number of named properties recorded for the category")
    dimension_count: int = Field(description="Number of dimensional variations recorded for the category")
    supporting_application_count: int = Field(description="Number of code applications supporting the category")
    supporting_document_count: int = Field(description="Number of distinct documents supporting the category")
    status: str = Field(description="Diagnostic status: adequate, developing, or underdeveloped")
    gaps: List[str] = Field(default_factory=list, description="Named adequacy gaps for this category")


class CategorySaturationSummary(BaseModel):
    """Diagnostic summary for GT category adequacy, separate from codebook stability."""
    status: str = Field(description="Diagnostic availability/status label")
    categories: List[CategorySaturationDiagnostic] = Field(
        default_factory=list,
        description="Per-category adequacy diagnostics",
    )
    all_categories_adequate: bool = Field(description="True when every observed category meets thresholds")
    adequate_count: int = Field(description="Number of categories meeting deterministic adequacy thresholds")
    developing_count: int = Field(description="Number of partially developed categories")
    underdeveloped_count: int = Field(description="Number of categories with no observed development")
    min_properties: int = Field(description="Minimum properties threshold used by the diagnostic")
    min_dimensions: int = Field(description="Minimum dimensions threshold used by the diagnostic")
    min_supporting_applications: int = Field(description="Minimum supporting applications threshold used")
    min_supporting_documents: int = Field(description="Minimum supporting documents threshold used")
    note: str = Field(description="Honest framing for interpreting the diagnostic")


class CrossInterviewResult(BaseModel):
    """Result of cross-interview pattern analysis."""
    shared_codes: Dict[str, List[str]] = Field(default_factory=dict)
    unique_codes: Dict[str, List[str]] = Field(default_factory=dict)
    consensus_themes: List[Dict[str, Any]] = Field(default_factory=list)
    divergent_themes: List[Dict[str, Any]] = Field(default_factory=list)
    co_occurrences: List[Dict[str, Any]] = Field(default_factory=list)
    code_doc_matrix: Dict[str, List[str]] = Field(default_factory=dict)
    doc_code_matrix: Dict[str, List[str]] = Field(default_factory=dict)


class ReviewSummary(BaseModel):
    """Summary of review state."""
    codes_count: int = 0
    applications_count: int = 0
    claims_count: int = 0
    relationships_count: int = 0
    abductive_candidates_count: int = 0
    existing_decisions: int = 0
    active_decisions: int = Field(
        default=0,
        description="Number of review decisions that still apply to current targets",
    )
    inactive_decisions: int = Field(
        default=0,
        description="Number of historical-only review decisions whose targets no longer apply",
    )
    pipeline_status: str = ""
    current_phase: Optional[str] = None


class SamplingSuggestion(BaseModel):
    """A suggestion for which document to code next."""
    doc_id: str
    doc_name: str
    reason: str = ""
    gap_codes: List[str] = Field(default_factory=list)
    priority_score: float = 0.0


class CoreCategoryResult(BaseModel):
    """Core category from grounded theory selective coding."""
    category_name: str
    definition: str = ""
    central_phenomenon: str = ""
    related_categories: List[str] = Field(default_factory=list)
    theoretical_properties: List[str] = Field(default_factory=list)
    explanatory_power: str = ""
    integration_rationale: str = ""


class TheoreticalModelResult(BaseModel):
    """Theoretical model from grounded theory integration."""
    model_name: str = ""
    core_categories: List[str] = Field(default_factory=list)
    theoretical_framework: str = ""
    propositions: List[str] = Field(default_factory=list)
    conceptual_relationships: List[str] = Field(default_factory=list)
    scope_conditions: List[str] = Field(default_factory=list)
    implications: List[str] = Field(default_factory=list)
    future_research: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level container
# ---------------------------------------------------------------------------

class ProjectConfig(BaseModel):
    """Configuration snapshot for the project."""
    methodology: Methodology = Methodology.DEFAULT
    model_name: str = "gpt-5-mini"
    auto_refresh_higher_order_on_recode: bool = Field(
        default=False,
        description=(
            "When true, incremental recode defaults to refreshing "
            "methodology-specific higher-order outputs after coding new documents."
        ),
    )
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    extra: Dict[str, Any] = Field(default_factory=dict)


class ProjectState(BaseModel):
    """
    Top-level container holding the entire analysis state.

    Can be serialized to / deserialized from JSON for persistence.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Project"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Configuration
    config: ProjectConfig = Field(default_factory=ProjectConfig)

    # Document layer
    corpus: Corpus = Field(default_factory=Corpus)
    corpus_scope: Optional[CorpusScope] = Field(
        default=None,
        description="Optional analytic boundary that constrains interpretation of corpus-level claims.",
    )

    # Coding layer
    codebook: Codebook = Field(default_factory=Codebook)
    code_applications: List[CodeApplication] = Field(default_factory=list)
    segments: List[Segment] = Field(default_factory=list)  # the INV-8 segment universe
    code_relationships: List[CodeRelationship] = Field(default_factory=list)

    # Entity layer
    entities: List[Entity] = Field(default_factory=list)
    entity_relationships: List[DomainEntityRelationship] = Field(default_factory=list)

    # Perspectives
    perspective_analysis: Optional[PerspectiveAnalysis] = None

    # Synthesis
    synthesis: Optional[Synthesis] = None

    # Grounded theory specifics (populated only for GT methodology)
    core_categories: List[CoreCategoryResult] = Field(default_factory=list)
    theoretical_model: Optional[TheoreticalModelResult] = None

    # Inter-rater reliability
    irr_result: Optional[IRRResult] = None
    stability_result: Optional[StabilityResult] = None

    # Analytical artifacts
    memos: List[AnalysisMemo] = Field(default_factory=list)
    observed_patterns: List[ObservedPattern] = Field(default_factory=list)
    abductive_explanations: List[AbductiveCandidateExplanation] = Field(default_factory=list)
    claims: List[AnalyticClaim] = Field(default_factory=list)
    review_decisions: List[HumanReviewDecision] = Field(default_factory=list)

    # Pipeline tracking
    phase_results: List[AnalysisPhaseResult] = Field(default_factory=list)
    current_phase: Optional[str] = None
    pipeline_status: PipelineStatus = PipelineStatus.PENDING

    # Iteration tracking
    iteration: int = 1
    codebook_history: List[Codebook] = Field(default_factory=list)

    # Data warnings
    data_warnings: List[str] = Field(default_factory=list)

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now().isoformat()

    def get_phase_result(self, phase_name: str) -> Optional[AnalysisPhaseResult]:
        """Get result for a specific phase."""
        for pr in self.phase_results:
            if pr.phase_name == phase_name:
                return pr
        return None

    def add_phase_result(self, result: AnalysisPhaseResult) -> None:
        """Add or update a phase result."""
        for i, pr in enumerate(self.phase_results):
            if pr.phase_name == result.phase_name:
                self.phase_results[i] = result
                return
        self.phase_results.append(result)

    def get_coded_doc_ids(self) -> set:
        """Return set of document IDs that have at least one code application."""
        return {app.doc_id for app in self.code_applications}

    def get_uncoded_doc_ids(self) -> list:
        """Return list of document IDs with no code applications."""
        coded = self.get_coded_doc_ids()
        return [d.id for d in self.corpus.documents if d.id not in coded]
