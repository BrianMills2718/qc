"""
Tests for schema adapters (qc_clean.schemas.adapters).
"""

import pytest

from qc_clean.schemas.analysis_schemas import (
    AnalysisRecommendation,
    AnalysisSynthesis,
    CodeHierarchy,
    EntityMapping,
    EntityRelationship,
    ParticipantProfile,
    SpeakerAnalysis,
    ThematicCode,
)
from qc_clean.schemas.adapters import (
    analysis_synthesis_to_synthesis,
    build_project_state_from_phases,
    code_hierarchy_to_applications,
    code_hierarchy_to_codebook,
    entity_mapping_to_entities,
    project_state_to_cross_interview_input,
    speaker_analysis_to_perspectives,
)
from qc_clean.schemas.domain import Provenance


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_hierarchy():
    codes = [
        ThematicCode(
            id="AI_USAGE",
            name="AI Usage",
            description="Use of AI tools.",
            semantic_definition="Any AI usage.",
            parent_id=None,
            level=0,
            example_quotes=["I use AI daily.", "AI helps with coding."],
            mention_count=5,
            discovery_confidence=0.8,
        ),
        ThematicCode(
            id="AI_LIMITS",
            name="AI Limitations",
            description="Limits of AI.",
            semantic_definition="Where AI falls short.",
            parent_id="AI_USAGE",
            level=1,
            example_quotes=["AI hallucinates."],
            mention_count=2,
            discovery_confidence=0.6,
        ),
    ]
    return CodeHierarchy(codes=codes, total_codes=2, analysis_confidence=0.75)


@pytest.fixture
def sample_speaker_analysis():
    p = ParticipantProfile(
        name="Alice",
        role="Researcher",
        characteristics=["quantitative"],
        perspective_summary="Favors AI.",
        codes_emphasized=["AI_USAGE"],
    )
    return SpeakerAnalysis(
        participants=[p],
        consensus_themes=["AI saves time"],
        divergent_viewpoints=["trust issues"],
        perspective_mapping={"Alice": ["AI_USAGE"]},
    )


@pytest.fixture
def sample_entity_mapping():
    return EntityMapping(
        entities=["AI", "Research"],
        relationships=[
            EntityRelationship(
                entity_1="AI",
                entity_2="Research",
                relationship_type="enables",
                strength=0.9,
                supporting_evidence=["AI accelerates research."],
            )
        ],
        cause_effect_chains=["AI -> faster research"],
        conceptual_connections=["AI links to methods"],
    )


@pytest.fixture
def sample_synthesis():
    rec = AnalysisRecommendation(
        title="Train staff",
        description="Run workshops.",
        priority="high",
        supporting_themes=["AI_USAGE"],
    )
    return AnalysisSynthesis(
        executive_summary="AI is transformative.",
        key_findings=["AI helps coding"],
        cross_cutting_patterns=["efficiency vs trust"],
        actionable_recommendations=[rec],
        confidence_assessment={"AI_USAGE": {"level": "high", "score": 0.85}},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCodeHierarchyToCodebook:
    def test_code_count(self, sample_hierarchy):
        cb = code_hierarchy_to_codebook(sample_hierarchy)
        assert len(cb.codes) == 2

    def test_code_fields(self, sample_hierarchy):
        cb = code_hierarchy_to_codebook(sample_hierarchy)
        c = cb.get_code("AI_USAGE")
        assert c is not None
        assert c.name == "AI Usage"
        assert c.definition == "Any AI usage."
        assert c.mention_count == 5
        assert c.confidence == 0.8
        assert c.provenance == Provenance.LLM

    def test_hierarchy_preserved(self, sample_hierarchy):
        cb = code_hierarchy_to_codebook(sample_hierarchy)
        children = cb.children_of("AI_USAGE")
        assert len(children) == 1
        assert children[0].id == "AI_LIMITS"

    def test_version(self, sample_hierarchy):
        cb = code_hierarchy_to_codebook(sample_hierarchy, version=3)
        assert cb.version == 3


class TestCodeHierarchyToApplications:
    def test_application_count(self, sample_hierarchy):
        apps = code_hierarchy_to_applications(sample_hierarchy, "doc1")
        # AI_USAGE has 2 quotes, AI_LIMITS has 1
        assert len(apps) == 3

    def test_application_fields(self, sample_hierarchy):
        apps = code_hierarchy_to_applications(sample_hierarchy, "doc1")
        assert all(a.doc_id == "doc1" for a in apps)
        assert all(a.applied_by == Provenance.LLM for a in apps)


class TestSpeakerAnalysisToPerspectives:
    def test_conversion(self, sample_speaker_analysis):
        pa = speaker_analysis_to_perspectives(sample_speaker_analysis)
        assert len(pa.participants) == 1
        assert pa.participants[0].name == "Alice"
        assert pa.consensus_themes == ["AI saves time"]
        assert pa.perspective_mapping == {"Alice": ["AI_USAGE"]}


class TestEntityMappingConversion:
    def test_entity_count(self, sample_entity_mapping):
        entities, rels = entity_mapping_to_entities(sample_entity_mapping, "doc1")
        assert len(entities) == 2
        assert len(rels) == 1

    def test_relationship_fields(self, sample_entity_mapping):
        _, rels = entity_mapping_to_entities(sample_entity_mapping)
        assert rels[0].relationship_type == "enables"
        assert rels[0].strength == 0.9


class TestSynthesisConversion:
    def test_fields(self, sample_synthesis):
        s = analysis_synthesis_to_synthesis(sample_synthesis)
        assert s.executive_summary == "AI is transformative."
        assert len(s.recommendations) == 1
        assert s.recommendations[0].title == "Train staff"
        assert s.confidence_assessment["AI_USAGE"]["score"] == 0.85


class TestBuildProjectState:
    def test_all_sections_populated(
        self, sample_hierarchy, sample_speaker_analysis,
        sample_entity_mapping, sample_synthesis,
    ):
        state = build_project_state_from_phases(
            sample_hierarchy,
            sample_speaker_analysis,
            sample_entity_mapping,
            sample_synthesis,
            doc_id="d1",
            doc_name="test.docx",
            project_name="Test Study",
        )

        assert state.name == "Test Study"
        assert state.corpus.num_documents == 1
        assert len(state.codebook.codes) == 2
        assert len(state.code_applications) == 3
        assert state.perspective_analysis is not None
        assert len(state.entities) == 2
        assert state.synthesis is not None
        assert state.synthesis.executive_summary == "AI is transformative."


class TestCrossInterviewInput:
    def test_structure(
        self, sample_hierarchy, sample_speaker_analysis,
        sample_entity_mapping, sample_synthesis,
    ):
        state = build_project_state_from_phases(
            sample_hierarchy,
            sample_speaker_analysis,
            sample_entity_mapping,
            sample_synthesis,
            doc_id="d1",
        )
        ci = project_state_to_cross_interview_input(state)
        assert len(ci["documents"]) == 1
        assert ci["codebook_version"] == 1
        assert len(ci["codes"]) == 2
        # All applications are for doc d1
        assert len(ci["documents"][0]["applied_code_ids"]) == 3
