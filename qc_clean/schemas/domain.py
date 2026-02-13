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
    confidence: float = 0.0
    applied_by: Provenance = Provenance.LLM
    codebook_version: int = 1


# ---------------------------------------------------------------------------
# Code relationships
# ---------------------------------------------------------------------------

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


class HumanReviewDecision(BaseModel):
    """Record of a human review action."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_type: str  # "code", "code_application", "codebook"
    target_id: str
    action: ReviewAction
    rationale: str = ""
    new_value: Optional[Dict[str, Any]] = None
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
    interpretation: str = ""
    timestamp: str = ""


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

    # Coding layer
    codebook: Codebook = Field(default_factory=Codebook)
    code_applications: List[CodeApplication] = Field(default_factory=list)
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

    # Analytical artifacts
    memos: List[AnalysisMemo] = Field(default_factory=list)
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
