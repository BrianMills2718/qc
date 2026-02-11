"""
Adapters to convert between existing analysis schemas and the unified domain model.
"""

from __future__ import annotations

from typing import List, Optional

from .analysis_schemas import (
    AnalysisSynthesis,
    CodeHierarchy,
    EntityMapping,
    SpeakerAnalysis,
)
from .domain import (
    Code,
    CodeApplication,
    Codebook,
    CodeRelationship,
    CoreCategoryResult,
    DomainEntityRelationship,
    Entity,
    Methodology,
    ParticipantPerspective,
    PerspectiveAnalysis,
    ProjectState,
    Provenance,
    Recommendation,
    Synthesis,
    TheoreticalModelResult,
)


# ---------------------------------------------------------------------------
# Phase 1 (CodeHierarchy) -> Codebook + CodeApplications
# ---------------------------------------------------------------------------

def code_hierarchy_to_codebook(
    hierarchy: CodeHierarchy,
    version: int = 1,
    methodology: str = "default",
) -> Codebook:
    """Convert a Phase 1 CodeHierarchy to a domain Codebook."""
    codes = []
    for tc in hierarchy.codes:
        code = Code(
            id=tc.id,
            name=tc.name,
            description=tc.description,
            definition=tc.semantic_definition,
            parent_id=tc.parent_id,
            level=tc.level,
            provenance=Provenance.LLM,
            version=version,
            example_quotes=tc.example_quotes,
            mention_count=tc.mention_count,
            confidence=tc.discovery_confidence,
        )
        codes.append(code)

    return Codebook(
        version=version,
        methodology=methodology,
        created_by=Provenance.LLM,
        codes=codes,
    )


def code_hierarchy_to_applications(
    hierarchy: CodeHierarchy,
    doc_id: str,
    codebook_version: int = 1,
) -> List[CodeApplication]:
    """Extract CodeApplications from Phase 1 example_quotes."""
    applications = []
    for tc in hierarchy.codes:
        for quote in tc.example_quotes:
            app = CodeApplication(
                code_id=tc.id,
                doc_id=doc_id,
                quote_text=quote,
                confidence=tc.discovery_confidence,
                applied_by=Provenance.LLM,
                codebook_version=codebook_version,
            )
            applications.append(app)
    return applications


# ---------------------------------------------------------------------------
# Phase 2 (SpeakerAnalysis) -> PerspectiveAnalysis
# ---------------------------------------------------------------------------

def speaker_analysis_to_perspectives(
    sa: SpeakerAnalysis,
) -> PerspectiveAnalysis:
    """Convert Phase 2 SpeakerAnalysis to domain PerspectiveAnalysis."""
    participants = []
    for p in sa.participants:
        pp = ParticipantPerspective(
            name=p.name,
            role=p.role,
            characteristics=p.characteristics,
            perspective_summary=p.perspective_summary,
            codes_emphasized=p.codes_emphasized,
        )
        participants.append(pp)

    return PerspectiveAnalysis(
        participants=participants,
        consensus_themes=sa.consensus_themes,
        divergent_viewpoints=sa.divergent_viewpoints,
        perspective_mapping=sa.perspective_mapping,
    )


# ---------------------------------------------------------------------------
# Phase 3 (EntityMapping) -> Entities + EntityRelationships
# ---------------------------------------------------------------------------

def entity_mapping_to_entities(
    em: EntityMapping,
    doc_id: Optional[str] = None,
) -> tuple[list[Entity], list[DomainEntityRelationship]]:
    """Convert Phase 3 EntityMapping to domain Entities and relationships."""
    # Build entity objects from the flat entity name list
    entity_map: dict[str, Entity] = {}
    for name in em.entities:
        ent = Entity(
            name=name,
            entity_type="concept",
            doc_ids=[doc_id] if doc_id else [],
        )
        entity_map[name] = ent

    # Also capture entities mentioned in relationships but not in the list
    for rel in em.relationships:
        for name in (rel.entity_1, rel.entity_2):
            if name not in entity_map:
                ent = Entity(
                    name=name,
                    entity_type="concept",
                    doc_ids=[doc_id] if doc_id else [],
                )
                entity_map[name] = ent

    # Build relationships
    relationships = []
    for rel in em.relationships:
        e1 = entity_map.get(rel.entity_1)
        e2 = entity_map.get(rel.entity_2)
        if e1 and e2:
            dr = DomainEntityRelationship(
                entity_1_id=e1.id,
                entity_2_id=e2.id,
                relationship_type=rel.relationship_type,
                strength=rel.strength,
                supporting_evidence=rel.supporting_evidence,
            )
            relationships.append(dr)

    return list(entity_map.values()), relationships


# ---------------------------------------------------------------------------
# Phase 4 (AnalysisSynthesis) -> Synthesis
# ---------------------------------------------------------------------------

def analysis_synthesis_to_synthesis(
    asyn: AnalysisSynthesis,
) -> Synthesis:
    """Convert Phase 4 AnalysisSynthesis to domain Synthesis."""
    recs = []
    for ar in asyn.actionable_recommendations:
        recs.append(Recommendation(
            title=ar.title,
            description=ar.description,
            priority=ar.priority,
            supporting_themes=ar.supporting_themes,
        ))

    return Synthesis(
        executive_summary=asyn.executive_summary,
        key_findings=asyn.key_findings,
        cross_cutting_patterns=asyn.cross_cutting_patterns,
        recommendations=recs,
        confidence_assessment=asyn.confidence_assessment,
    )


# ---------------------------------------------------------------------------
# Grounded Theory adapters
# ---------------------------------------------------------------------------

def open_codes_to_codebook(
    open_codes: list,  # List[grounded_theory.OpenCode]
    version: int = 1,
) -> Codebook:
    """Convert GT OpenCode list to a domain Codebook."""
    codes = []
    for oc in open_codes:
        code = Code(
            id=oc.code_name.upper().replace(" ", "_"),
            name=oc.code_name,
            description=oc.description,
            properties=oc.properties,
            dimensions=oc.dimensions,
            parent_id=oc.parent_id,
            level=oc.level,
            provenance=Provenance.LLM,
            version=version,
            example_quotes=oc.supporting_quotes,
            mention_count=oc.frequency,
            confidence=oc.confidence,
        )
        codes.append(code)

    return Codebook(
        version=version,
        methodology="grounded_theory",
        created_by=Provenance.LLM,
        codes=codes,
    )


def codebook_to_open_codes(codebook: Codebook) -> list:
    """Convert domain Codebook back to GT OpenCode list (lazy import to avoid circular)."""
    from qc_clean.core.workflow.grounded_theory import OpenCode

    open_codes = []
    for code in codebook.codes:
        oc = OpenCode(
            code_name=code.name,
            description=code.description,
            properties=code.properties,
            dimensions=code.dimensions,
            supporting_quotes=code.example_quotes,
            frequency=code.mention_count,
            confidence=code.confidence,
            parent_id=code.parent_id,
            level=code.level,
            child_codes=[],
        )
        open_codes.append(oc)
    return open_codes


def axial_relationships_to_code_relationships(
    axial_rels: list,  # List[grounded_theory.AxialRelationship]
    codebook: Codebook,
) -> List[CodeRelationship]:
    """Convert GT AxialRelationship list to domain CodeRelationships."""
    relationships = []
    for ar in axial_rels:
        # Resolve code IDs by name
        source = codebook.get_code_by_name(ar.central_category)
        target = codebook.get_code_by_name(ar.related_category)
        source_id = source.id if source else ar.central_category
        target_id = target.id if target else ar.related_category

        cr = CodeRelationship(
            source_code_id=source_id,
            target_code_id=target_id,
            relationship_type=ar.relationship_type,
            strength=ar.strength,
            evidence=ar.supporting_evidence,
            conditions=ar.conditions,
            consequences=ar.consequences,
        )
        relationships.append(cr)
    return relationships


def core_category_to_domain(
    core_cat,  # grounded_theory.CoreCategory
) -> CoreCategoryResult:
    """Convert GT CoreCategory to domain CoreCategoryResult."""
    return CoreCategoryResult(
        category_name=core_cat.category_name,
        definition=core_cat.definition,
        central_phenomenon=core_cat.central_phenomenon,
        related_categories=core_cat.related_categories,
        theoretical_properties=core_cat.theoretical_properties,
        explanatory_power=core_cat.explanatory_power,
        integration_rationale=core_cat.integration_rationale,
    )


def theoretical_model_to_domain(
    tm,  # grounded_theory.TheoreticalModel
) -> TheoreticalModelResult:
    """Convert GT TheoreticalModel to domain TheoreticalModelResult."""
    return TheoreticalModelResult(
        model_name=tm.model_name,
        core_categories=tm.core_categories,
        theoretical_framework=tm.theoretical_framework,
        propositions=tm.propositions,
        conceptual_relationships=tm.conceptual_relationships,
        scope_conditions=tm.scope_conditions,
        implications=tm.implications,
        future_research=tm.future_research,
    )


# ---------------------------------------------------------------------------
# Composite: build ProjectState from existing 4-phase output
# ---------------------------------------------------------------------------

def build_project_state_from_phases(
    phase1: CodeHierarchy,
    phase2: SpeakerAnalysis,
    phase3: EntityMapping,
    phase4: AnalysisSynthesis,
    doc_id: str = "doc_1",
    doc_name: str = "interview",
    doc_content: str = "",
    project_name: str = "Untitled Project",
) -> ProjectState:
    """Build a complete ProjectState from the four analysis phases."""
    from .domain import Corpus, Document, ProjectConfig

    state = ProjectState(name=project_name)

    # Corpus
    doc = Document(id=doc_id, name=doc_name, content=doc_content)
    state.corpus = Corpus(documents=[doc])

    # Codebook + applications
    state.codebook = code_hierarchy_to_codebook(phase1)
    state.code_applications = code_hierarchy_to_applications(phase1, doc_id)

    # Perspectives
    state.perspective_analysis = speaker_analysis_to_perspectives(phase2)

    # Entities
    entities, entity_rels = entity_mapping_to_entities(phase3, doc_id)
    state.entities = entities
    state.entity_relationships = entity_rels

    # Synthesis
    state.synthesis = analysis_synthesis_to_synthesis(phase4)

    state.touch()
    return state


# ---------------------------------------------------------------------------
# Cross-interview helper
# ---------------------------------------------------------------------------

def project_state_to_cross_interview_input(
    state: ProjectState,
) -> dict:
    """Prepare data for the cross-interview analyzer from ProjectState."""
    docs = []
    for doc in state.corpus.documents:
        # Gather codes applied to this document
        doc_codes = [
            app.code_id
            for app in state.code_applications
            if app.doc_id == doc.id
        ]
        docs.append({
            "doc_id": doc.id,
            "doc_name": doc.name,
            "applied_code_ids": doc_codes,
            "speakers": doc.detected_speakers,
        })

    return {
        "documents": docs,
        "codebook_version": state.codebook.version,
        "codes": [
            {"id": c.id, "name": c.name, "description": c.description}
            for c in state.codebook.codes
        ],
    }
