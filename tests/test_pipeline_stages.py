"""
Tests for pipeline stage execution with mocked LLM.

Validates that each stage correctly:
- Calls the LLM with the right schema
- Converts the response to domain objects via adapters
- Mutates ProjectState correctly (codebook, applications, perspectives, etc.)
- Stashes config for downstream stages
- Handles edge cases (empty data, single vs multi doc/speaker)
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from qc_clean.schemas.analysis_schemas import (
    AnalysisRecommendation,
    AnalysisSynthesis,
    CodeHierarchy,
    ConfidenceEntry,
    EntityMapping,
    EntityRelationship,
    ParticipantProfile,
    SpeakerAnalysis,
    ThematicCode,
)
from qc_clean.schemas.gt_schemas import (
    AxialRelationship,
    CoreCategory,
    OpenCode,
    TheoreticalModel,
)
from qc_clean.schemas.domain import (
    Code,
    Codebook,
    Corpus,
    CoreCategoryResult,
    Document,
    Methodology,
    ProjectConfig,
    ProjectState,
    Provenance,
)


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------

def _make_state(**kwargs) -> ProjectState:
    """Build a ProjectState with a default corpus for testing."""
    defaults = dict(
        name="test_project",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[
            Document(
                name="interview1.txt",
                content="Interviewer: Tell me about AI.\nJane: We use AI for everything now. It changed our workflow completely.",
                detected_speakers=["Jane"],
            ),
        ]),
    )
    defaults.update(kwargs)
    return ProjectState(**defaults)


def _make_multi_doc_state() -> ProjectState:
    """Build a ProjectState with multiple documents."""
    return _make_state(
        corpus=Corpus(documents=[
            Document(
                name="interview1.txt",
                content="Jane: We use AI for everything now. It changed our workflow.",
                detected_speakers=["Jane"],
            ),
            Document(
                name="interview2.txt",
                content="Bob: AI adoption was slow at first. We had concerns about data privacy.",
                detected_speakers=["Bob"],
            ),
        ])
    )


def _sample_code_hierarchy(**overrides) -> CodeHierarchy:
    """Create a minimal CodeHierarchy response."""
    defaults = dict(
        codes=[
            ThematicCode(
                id="AI_ADOPTION",
                name="AI Adoption",
                description="How organizations adopt AI technologies",
                semantic_definition="References to AI implementation decisions",
                parent_id=None,
                level=0,
                example_quotes=["We use AI for everything now"],
                mention_count=5,
                discovery_confidence=0.8,
                reasoning="Multiple mentions of AI implementation.",
            ),
            ThematicCode(
                id="WORKFLOW_CHANGE",
                name="Workflow Change",
                description="How workflows changed after AI adoption",
                semantic_definition="References to changed work processes",
                parent_id="AI_ADOPTION",
                level=1,
                example_quotes=["It changed our workflow completely"],
                mention_count=3,
                discovery_confidence=0.7,
                reasoning="Direct consequence of AI adoption.",
            ),
        ],
        total_codes=2,
        analysis_confidence=0.85,
        analytical_memo="Key decision: separated adoption from workflow impact.",
    )
    defaults.update(overrides)
    return CodeHierarchy(**defaults)


def _sample_speaker_analysis(**overrides) -> SpeakerAnalysis:
    defaults = dict(
        participants=[
            ParticipantProfile(
                name="Jane",
                role="Manager",
                characteristics=["tech-savvy", "pragmatic"],
                perspective_summary="Views AI as transformative for workflows.",
                codes_emphasized=["AI_ADOPTION", "WORKFLOW_CHANGE"],
            ),
        ],
        consensus_themes=["AI is beneficial"],
        divergent_viewpoints=["Concerns about pace of change"],
        perspective_mapping={"Jane": ["AI_ADOPTION", "WORKFLOW_CHANGE"]},
        analytical_memo="Single speaker interview.",
    )
    defaults.update(overrides)
    return SpeakerAnalysis(**defaults)


def _sample_entity_mapping(**overrides) -> EntityMapping:
    defaults = dict(
        entities=["AI Technology", "Workflow"],
        relationships=[
            EntityRelationship(
                entity_1="AI Technology",
                entity_2="Workflow",
                relationship_type="transforms",
                strength=0.9,
                supporting_evidence=["It changed our workflow completely"],
            ),
        ],
        cause_effect_chains=["AI adoption -> workflow transformation"],
        conceptual_connections=["Technology and organizational change linked"],
        analytical_memo="Clear causal relationship in data.",
    )
    defaults.update(overrides)
    return EntityMapping(**defaults)


def _sample_synthesis(**overrides) -> AnalysisSynthesis:
    defaults = dict(
        executive_summary="AI adoption transforms organizational workflows.",
        key_findings=["AI is widely adopted", "Workflows changed significantly"],
        cross_cutting_patterns=["Technology drives organizational change"],
        actionable_recommendations=[
            AnalysisRecommendation(
                title="Invest in AI training",
                description="Train staff on AI tools to maximize adoption benefits.",
                priority="high",
                supporting_themes=["AI_ADOPTION"],
            ),
        ],
        confidence_assessment={"AI_ADOPTION": {"level": "high", "score": 0.85}},
        analytical_memo="Synthesis reflects strong convergence across themes.",
    )
    defaults.update(overrides)
    return AnalysisSynthesis(**defaults)


# ---------------------------------------------------------------------------
# ThematicCodingStage
# ---------------------------------------------------------------------------

class TestThematicCodingStage:

    def test_produces_codebook_and_applications(self):
        from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage

        state = _make_state()
        config = {}
        mock_response = _sample_code_hierarchy()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(ThematicCodingStage().execute(state, config))

        # Codebook populated
        assert len(result.codebook.codes) == 2
        assert result.codebook.codes[0].id == "AI_ADOPTION"
        assert result.codebook.codes[0].name == "AI Adoption"
        assert result.codebook.codes[1].parent_id == "AI_ADOPTION"
        assert result.codebook.codes[0].reasoning == "Multiple mentions of AI implementation."

        # Applications created from quotes
        assert len(result.code_applications) >= 2
        assert all(a.applied_by == Provenance.LLM for a in result.code_applications)

        # Config stashed for downstream
        assert "_phase1_json" in config

    def test_quote_matching_to_correct_doc(self):
        """Quotes should be attributed to the document they appear in."""
        from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage

        state = _make_multi_doc_state()
        config = {}
        mock_response = _sample_code_hierarchy(
            codes=[
                ThematicCode(
                    id="PRIVACY",
                    name="Privacy Concerns",
                    description="Concerns about data privacy",
                    semantic_definition="References to privacy",
                    level=0,
                    example_quotes=["concerns about data privacy"],
                    mention_count=1,
                    discovery_confidence=0.6,
                ),
            ],
            total_codes=1,
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(ThematicCodingStage().execute(state, config))

        # Quote "concerns about data privacy" appears in interview2, not interview1
        assert len(result.code_applications) == 1
        app = result.code_applications[0]
        assert app.doc_id == state.corpus.documents[1].id

    def test_irr_prompt_suffix_appended(self):
        """IRR prompt suffix should be appended to the prompt."""
        from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage

        state = _make_state()
        config = {"irr_prompt_suffix": "Focus on frequency of themes."}
        mock_response = _sample_code_hierarchy()
        captured_prompt = None

        async def capture_prompt(prompt, schema):
            nonlocal captured_prompt
            captured_prompt = prompt
            return mock_response

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(side_effect=capture_prompt)
            asyncio.run(ThematicCodingStage().execute(state, config))

        assert "Focus on frequency of themes." in captured_prompt

    def test_human_review_flag(self):
        from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage

        stage = ThematicCodingStage(pause_for_review=True)
        assert stage.requires_human_review() is True
        assert ThematicCodingStage().requires_human_review() is False


# ---------------------------------------------------------------------------
# PerspectiveStage
# ---------------------------------------------------------------------------

class TestPerspectiveStage:

    def test_produces_perspective_analysis(self):
        from qc_clean.core.pipeline.stages.perspective import PerspectiveStage

        state = _make_state()
        config = {"_phase1_json": "{}"}
        mock_response = _sample_speaker_analysis()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(PerspectiveStage().execute(state, config))

        assert len(result.perspective_analysis.participants) == 1
        assert result.perspective_analysis.participants[0].name == "Jane"
        assert result.perspective_analysis.consensus_themes == ["AI is beneficial"]
        assert result.perspective_analysis.perspective_mapping == {"Jane": ["AI_ADOPTION", "WORKFLOW_CHANGE"]}
        assert "_phase2_json" in config

    def test_single_speaker_detection(self):
        """Single speaker should trigger single-speaker prompt."""
        from qc_clean.core.pipeline.stages.perspective import PerspectiveStage

        state = _make_state()  # 1 speaker: Jane
        config = {"_phase1_json": "{}"}
        captured_prompt = None

        async def capture_prompt(prompt, schema):
            nonlocal captured_prompt
            captured_prompt = prompt
            return _sample_speaker_analysis()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(side_effect=capture_prompt)
            asyncio.run(PerspectiveStage().execute(state, config))

        assert "SINGLE-SPEAKER" in captured_prompt

    def test_multi_speaker_detection(self):
        """Multiple speakers should trigger multi-speaker prompt."""
        from qc_clean.core.pipeline.stages.perspective import PerspectiveStage

        state = _make_state(
            corpus=Corpus(documents=[
                Document(
                    name="focus_group.txt",
                    content="Jane: I like AI.\nBob: I disagree.",
                    detected_speakers=["Jane", "Bob"],
                ),
            ])
        )
        config = {"_phase1_json": "{}"}
        captured_prompt = None

        async def capture_prompt(prompt, schema):
            nonlocal captured_prompt
            captured_prompt = prompt
            return _sample_speaker_analysis()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(side_effect=capture_prompt)
            asyncio.run(PerspectiveStage().execute(state, config))

        assert "SINGLE-SPEAKER" not in captured_prompt
        assert "multi-speaker" in captured_prompt.lower() or "different participant" in captured_prompt.lower()


# ---------------------------------------------------------------------------
# RelationshipStage
# ---------------------------------------------------------------------------

class TestRelationshipStage:

    def test_produces_entities_and_relationships(self):
        from qc_clean.core.pipeline.stages.relationship import RelationshipStage

        state = _make_state()
        config = {"_phase1_json": "{}", "_phase2_json": "{}"}
        mock_response = _sample_entity_mapping()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(RelationshipStage().execute(state, config))

        # Entities
        assert len(result.entities) == 2
        entity_names = {e.name for e in result.entities}
        assert "AI Technology" in entity_names
        assert "Workflow" in entity_names

        # Relationships
        assert len(result.entity_relationships) == 1
        rel = result.entity_relationships[0]
        assert rel.relationship_type == "transforms"
        assert rel.strength == 0.9

        # Config stashed
        assert "_phase3_json" in config

    def test_causal_chains_create_memo(self):
        from qc_clean.core.pipeline.stages.relationship import RelationshipStage

        state = _make_state()
        config = {"_phase1_json": "{}", "_phase2_json": "{}"}
        mock_response = _sample_entity_mapping()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(RelationshipStage().execute(state, config))

        # Should have causal chains memo + analytical memo
        causal_memos = [m for m in result.memos if m.memo_type == "relationship"]
        assert len(causal_memos) == 1
        assert "workflow transformation" in causal_memos[0].content

    def test_no_causal_memo_when_empty(self):
        from qc_clean.core.pipeline.stages.relationship import RelationshipStage

        state = _make_state()
        config = {"_phase1_json": "{}", "_phase2_json": "{}"}
        mock_response = _sample_entity_mapping(
            cause_effect_chains=[],
            conceptual_connections=[],
            analytical_memo="",
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(RelationshipStage().execute(state, config))

        assert len(result.memos) == 0


# ---------------------------------------------------------------------------
# SynthesisStage
# ---------------------------------------------------------------------------

class TestSynthesisStage:

    def test_produces_synthesis(self):
        from qc_clean.core.pipeline.stages.synthesis import SynthesisStage

        state = _make_state(
            codebook=Codebook(codes=[
                Code(id="AI_ADOPTION", name="AI Adoption", description="test"),
            ])
        )
        config = {"_phase1_json": "{}", "_phase2_json": "{}", "_phase3_json": "{}"}
        mock_response = _sample_synthesis()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(SynthesisStage().execute(state, config))

        assert result.synthesis.executive_summary == "AI adoption transforms organizational workflows."
        assert len(result.synthesis.key_findings) == 2
        assert len(result.synthesis.recommendations) == 1
        assert result.synthesis.recommendations[0].title == "Invest in AI training"
        assert result.synthesis.recommendations[0].priority == "high"
        assert "AI_ADOPTION" in result.synthesis.confidence_assessment


# ---------------------------------------------------------------------------
# GTOpenCodingStage
# ---------------------------------------------------------------------------

class TestGTOpenCodingStage:

    def _sample_open_codes_response(self, **overrides):
        from qc_clean.core.pipeline.stages.gt_open_coding import OpenCodesResponse
        defaults = dict(
            open_codes=[
                OpenCode(
                    code_name="AI Integration",
                    description="How AI is integrated into existing systems",
                    properties=["speed", "resistance"],
                    dimensions=["fast vs slow"],
                    supporting_quotes=["We use AI for everything now"],
                    frequency=5,
                    confidence=0.8,
                    reasoning="Recurring pattern in data.",
                    parent_id=None,
                    level=0,
                ),
                OpenCode(
                    code_name="Workflow Impact",
                    description="Effects on daily workflows",
                    properties=["efficiency"],
                    dimensions=["positive vs negative"],
                    supporting_quotes=["It changed our workflow completely"],
                    frequency=3,
                    confidence=0.7,
                    parent_id="AI_INTEGRATION",
                    level=1,
                ),
            ],
            analytical_memo="Focused on action-oriented codes.",
        )
        defaults.update(overrides)
        return OpenCodesResponse(**defaults)

    def test_produces_codebook_and_applications(self):
        from qc_clean.core.pipeline.stages.gt_open_coding import GTOpenCodingStage

        state = _make_state()
        config = {}
        mock_response = self._sample_open_codes_response()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(GTOpenCodingStage().execute(state, config))

        # Codebook
        assert len(result.codebook.codes) == 2
        assert result.codebook.methodology == "grounded_theory"
        assert result.codebook.codes[0].name == "AI Integration"
        assert result.codebook.codes[0].reasoning == "Recurring pattern in data."

        # Applications from supporting quotes
        assert len(result.code_applications) >= 2

        # Config stashed for downstream GT stages
        assert "_gt_open_codes" in config
        assert "_gt_open_codes_text" in config

    def test_quote_matching_to_docs(self):
        """Quotes should be matched to the correct document."""
        from qc_clean.core.pipeline.stages.gt_open_coding import GTOpenCodingStage

        state = _make_multi_doc_state()
        config = {}
        from qc_clean.core.pipeline.stages.gt_open_coding import OpenCodesResponse
        mock_response = OpenCodesResponse(
            open_codes=[
                OpenCode(
                    code_name="Privacy",
                    description="Data privacy concerns",
                    properties=["sensitivity"],
                    dimensions=["high vs low"],
                    supporting_quotes=["concerns about data privacy"],
                    frequency=1,
                    confidence=0.6,
                ),
            ],
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(GTOpenCodingStage().execute(state, config))

        # "concerns about data privacy" is in interview2
        assert len(result.code_applications) == 1
        assert result.code_applications[0].doc_id == state.corpus.documents[1].id

    def test_human_review_flag(self):
        from qc_clean.core.pipeline.stages.gt_open_coding import GTOpenCodingStage

        stage = GTOpenCodingStage(pause_for_review=True)
        assert stage.requires_human_review() is True


# ---------------------------------------------------------------------------
# GTAxialCodingStage
# ---------------------------------------------------------------------------

class TestGTAxialCodingStage:

    def _sample_axial_response(self, **overrides):
        from qc_clean.core.pipeline.stages.gt_axial_coding import AxialRelationshipsResponse
        defaults = dict(
            axial_relationships=[
                AxialRelationship(
                    central_category="AI Integration",
                    related_category="Workflow Impact",
                    relationship_type="causal",
                    conditions=["Management support"],
                    consequences=["Increased efficiency"],
                    supporting_evidence=["AI changed our workflow"],
                    strength=0.85,
                ),
            ],
            analytical_memo="Clear causal link between integration and impact.",
        )
        defaults.update(overrides)
        return AxialRelationshipsResponse(**defaults)

    def test_produces_code_relationships(self):
        from qc_clean.core.pipeline.stages.gt_axial_coding import GTAxialCodingStage

        state = _make_state(
            codebook=Codebook(codes=[
                Code(id="AI_INTEGRATION", name="AI Integration", description="test"),
                Code(id="WORKFLOW_IMPACT", name="Workflow Impact", description="test"),
            ])
        )
        config = {"_gt_open_codes_text": "- AI Integration\n- Workflow Impact"}
        mock_response = self._sample_axial_response()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(GTAxialCodingStage().execute(state, config))

        assert len(result.code_relationships) == 1
        rel = result.code_relationships[0]
        assert rel.source_code_id == "AI_INTEGRATION"
        assert rel.target_code_id == "WORKFLOW_IMPACT"
        assert rel.relationship_type == "causal"
        assert rel.strength == 0.85
        assert rel.conditions == ["Management support"]
        assert rel.consequences == ["Increased efficiency"]

        # Config stashed
        assert "_gt_axial_relationships" in config
        assert "_gt_axial_text" in config

    def test_can_execute_requires_codes(self):
        from qc_clean.core.pipeline.stages.gt_axial_coding import GTAxialCodingStage

        stage = GTAxialCodingStage()
        empty_state = _make_state()  # no codebook codes
        assert stage.can_execute(empty_state) is False

        state_with_codes = _make_state(
            codebook=Codebook(codes=[Code(id="X", name="X", description="x")])
        )
        assert stage.can_execute(state_with_codes) is True


# ---------------------------------------------------------------------------
# GTSelectiveCodingStage
# ---------------------------------------------------------------------------

class TestGTSelectiveCodingStage:

    def _sample_selective_response(self, **overrides):
        from qc_clean.core.pipeline.stages.gt_selective_coding import CoreCategoriesResponse
        defaults = dict(
            core_categories=[
                CoreCategory(
                    category_name="Digital Transformation",
                    definition="Organizational change driven by technology",
                    central_phenomenon="How AI reshapes work",
                    related_categories=["AI Integration", "Workflow Impact"],
                    theoretical_properties=["scope", "speed", "depth"],
                    explanatory_power="Explains the connection between AI and organizational change",
                    integration_rationale="Subsumes both AI adoption and workflow changes",
                ),
            ],
            analytical_memo="Single core category emerged clearly.",
        )
        defaults.update(overrides)
        return CoreCategoriesResponse(**defaults)

    def test_produces_core_categories(self):
        from qc_clean.core.pipeline.stages.gt_selective_coding import GTSelectiveCodingStage

        state = _make_state(
            codebook=Codebook(codes=[Code(id="X", name="X", description="x")])
        )
        config = {"_gt_open_codes_text": "codes", "_gt_axial_text": "rels"}
        mock_response = self._sample_selective_response()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(GTSelectiveCodingStage().execute(state, config))

        assert len(result.core_categories) == 1
        cc = result.core_categories[0]
        assert cc.category_name == "Digital Transformation"
        assert cc.central_phenomenon == "How AI reshapes work"
        assert "AI Integration" in cc.related_categories
        assert cc.integration_rationale == "Subsumes both AI adoption and workflow changes"

        # Config stashed
        assert "_gt_core_categories" in config
        assert "_gt_core_text" in config

    def test_can_execute_requires_codes(self):
        from qc_clean.core.pipeline.stages.gt_selective_coding import GTSelectiveCodingStage

        stage = GTSelectiveCodingStage()
        empty_state = _make_state()
        assert stage.can_execute(empty_state) is False


# ---------------------------------------------------------------------------
# GTTheoryIntegrationStage
# ---------------------------------------------------------------------------

class TestGTTheoryIntegrationStage:

    def _sample_theoretical_model(self, **overrides):
        defaults = dict(
            model_name="Digital Transformation Theory",
            core_categories=["Digital Transformation"],
            theoretical_framework="AI adoption drives organizational change through workflow transformation.",
            propositions=[
                "If AI is adopted with management support, workflow efficiency increases.",
                "If workflow change is rapid, employee resistance emerges.",
            ],
            conceptual_relationships=["AI -> Workflow -> Efficiency"],
            scope_conditions=["Applies to knowledge-work organizations"],
            implications=["Organizations should manage change carefully"],
            future_research=["Study long-term effects of AI on job satisfaction"],
            analytical_memo="Theory integrates all prior stages well.",
        )
        defaults.update(overrides)
        return TheoreticalModel(**defaults)

    def test_produces_theoretical_model(self):
        from qc_clean.core.pipeline.stages.gt_theory_integration import GTTheoryIntegrationStage

        state = _make_state(
            core_categories=[
                CoreCategoryResult(
                    category_name="Digital Transformation",
                    definition="test",
                )
            ]
        )
        config = {
            "_gt_open_codes_text": "codes",
            "_gt_axial_text": "rels",
            "_gt_core_text": "- Digital Transformation: test",
        }
        mock_response = self._sample_theoretical_model()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(GTTheoryIntegrationStage().execute(state, config))

        tm = result.theoretical_model
        assert tm.model_name == "Digital Transformation Theory"
        assert "Digital Transformation" in tm.core_categories
        assert len(tm.propositions) == 2
        assert "knowledge-work" in tm.scope_conditions[0]

    def test_can_execute_requires_core_categories(self):
        from qc_clean.core.pipeline.stages.gt_theory_integration import GTTheoryIntegrationStage

        stage = GTTheoryIntegrationStage()
        empty_state = _make_state()
        assert stage.can_execute(empty_state) is False

        state_with_cc = _make_state(
            core_categories=[
                CoreCategoryResult(category_name="X", definition="x")
            ]
        )
        assert stage.can_execute(state_with_cc) is True


# ---------------------------------------------------------------------------
# CrossInterviewStage (no LLM, pure logic)
# ---------------------------------------------------------------------------

class TestCrossInterviewStage:

    def test_skips_single_document(self):
        from qc_clean.core.pipeline.stages.cross_interview import CrossInterviewStage

        stage = CrossInterviewStage()
        state = _make_state()  # 1 document
        assert stage.can_execute(state) is False

    def test_runs_with_multiple_documents(self):
        from qc_clean.core.pipeline.stages.cross_interview import CrossInterviewStage

        stage = CrossInterviewStage()
        state = _make_multi_doc_state()
        assert stage.can_execute(state) is True

    def test_identifies_shared_and_unique_codes(self):
        from qc_clean.core.pipeline.stages.cross_interview import CrossInterviewStage
        from qc_clean.schemas.domain import CodeApplication

        state = _make_multi_doc_state()
        doc1_id = state.corpus.documents[0].id
        doc2_id = state.corpus.documents[1].id

        state.codebook = Codebook(codes=[
            Code(id="SHARED", name="Shared Theme", description="test"),
            Code(id="UNIQUE1", name="Only Doc1", description="test"),
        ])
        state.code_applications = [
            CodeApplication(code_id="SHARED", doc_id=doc1_id, quote_text="q1"),
            CodeApplication(code_id="SHARED", doc_id=doc2_id, quote_text="q2"),
            CodeApplication(code_id="UNIQUE1", doc_id=doc1_id, quote_text="q3"),
        ]

        result = asyncio.run(CrossInterviewStage().execute(state, {}))

        # Should produce a cross-interview memo
        cross_memos = [m for m in result.memos if m.memo_type == "cross_case"]
        assert len(cross_memos) == 1
        assert "Shared Theme" in cross_memos[0].content

    def test_consensus_and_divergent_detection(self):
        from qc_clean.core.pipeline.stages.cross_interview import (
            CrossInterviewStage,
            analyze_cross_interview_patterns,
        )
        from qc_clean.schemas.domain import CodeApplication

        state = _make_state(
            corpus=Corpus(documents=[
                Document(name=f"doc{i}.txt", content=f"content {i}")
                for i in range(3)
            ])
        )
        doc_ids = [d.id for d in state.corpus.documents]

        state.codebook = Codebook(codes=[
            Code(id="CONSENSUS", name="Consensus", description="test"),
            Code(id="DIVERGENT", name="Divergent", description="test"),
        ])
        # CONSENSUS appears in all 3 docs, DIVERGENT in only 1
        state.code_applications = [
            CodeApplication(code_id="CONSENSUS", doc_id=doc_ids[0], quote_text="q"),
            CodeApplication(code_id="CONSENSUS", doc_id=doc_ids[1], quote_text="q"),
            CodeApplication(code_id="CONSENSUS", doc_id=doc_ids[2], quote_text="q"),
            CodeApplication(code_id="DIVERGENT", doc_id=doc_ids[0], quote_text="q"),
        ]

        results = analyze_cross_interview_patterns(state)
        consensus_ids = [c["code_id"] for c in results["consensus_themes"]]
        divergent_ids = [d["code_id"] for d in results["divergent_themes"]]

        assert "CONSENSUS" in consensus_ids
        assert "DIVERGENT" in divergent_ids


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestStageEdgeCases:

    def test_thematic_coding_empty_quotes(self):
        """Stage should handle codes with no quotes gracefully."""
        from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage

        state = _make_state()
        config = {}
        mock_response = _sample_code_hierarchy(
            codes=[
                ThematicCode(
                    id="EMPTY",
                    name="Empty Code",
                    description="Code with no quotes",
                    semantic_definition="test",
                    level=0,
                    example_quotes=[],
                    mention_count=0,
                    discovery_confidence=0.3,
                ),
            ],
            total_codes=1,
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(ThematicCodingStage().execute(state, config))

        assert len(result.codebook.codes) == 1
        assert len(result.code_applications) == 0

    def test_relationship_no_causal_chains(self):
        """Relationship stage with empty causal chains should not produce extra memo."""
        from qc_clean.core.pipeline.stages.relationship import RelationshipStage

        state = _make_state()
        config = {"_phase1_json": "{}", "_phase2_json": "{}"}
        mock_response = _sample_entity_mapping(
            cause_effect_chains=[],
            conceptual_connections=[],
            analytical_memo="",
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(RelationshipStage().execute(state, config))

        # No memos when no causal chains and no analytical memo
        assert len(result.memos) == 0

    def test_gt_open_coding_fallback_doc_assignment(self):
        """Quotes not found verbatim should be assigned to first document."""
        from qc_clean.core.pipeline.stages.gt_open_coding import GTOpenCodingStage, OpenCodesResponse

        state = _make_state()
        config = {}
        mock_response = OpenCodesResponse(
            open_codes=[
                OpenCode(
                    code_name="Test",
                    description="test",
                    properties=["p"],
                    dimensions=["d"],
                    supporting_quotes=["This quote does not appear in any document"],
                    frequency=1,
                    confidence=0.5,
                ),
            ],
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(GTOpenCodingStage().execute(state, config))

        # Should fall back to first document
        assert len(result.code_applications) == 1
        assert result.code_applications[0].doc_id == state.corpus.documents[0].id

    def test_axial_coding_unresolved_code_names(self):
        """Axial relationships with unrecognized code names should use raw names as IDs."""
        from qc_clean.core.pipeline.stages.gt_axial_coding import GTAxialCodingStage, AxialRelationshipsResponse

        state = _make_state(
            codebook=Codebook(codes=[
                Code(id="KNOWN", name="Known Code", description="test"),
            ])
        )
        config = {"_gt_open_codes_text": "codes"}
        mock_response = AxialRelationshipsResponse(
            axial_relationships=[
                AxialRelationship(
                    central_category="Known Code",
                    related_category="Unknown Code",
                    relationship_type="contextual",
                    conditions=[],
                    consequences=[],
                    supporting_evidence=[],
                    strength=0.5,
                ),
            ],
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(GTAxialCodingStage().execute(state, config))

        rel = result.code_relationships[0]
        assert rel.source_code_id == "KNOWN"
        assert rel.target_code_id == "Unknown Code"  # falls back to raw name
