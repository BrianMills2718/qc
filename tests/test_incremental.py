"""
Tests for incremental coding feature.

Covers:
- ProjectState helper methods (get_coded_doc_ids, get_uncoded_doc_ids)
- IncrementalCodingStage with mocked LLM
- Pipeline factory for incremental pipeline
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.stages.incremental_coding import (
    IncrementalCodingStage,
    _format_codebook_for_prompt,
)
from qc_clean.core.pipeline.pipeline_factory import create_incremental_pipeline
from qc_clean.schemas.analysis_schemas import CodeHierarchy, ThematicCode
from qc_clean.schemas.domain import (
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    Methodology,
    ProjectConfig,
    ProjectState,
    Provenance,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state_with_codes() -> ProjectState:
    """Create a state with existing codes and one coded document."""
    doc1 = Document(
        id="doc1",
        name="interview1.txt",
        content="We use AI for everything. It changed our workflow completely.",
    )
    doc2 = Document(
        id="doc2",
        name="interview2.txt",
        content="Data privacy is our top concern. We encrypt all user data.",
    )

    state = ProjectState(
        name="test_project",
        config=ProjectConfig(methodology=Methodology.DEFAULT),
        corpus=Corpus(documents=[doc1, doc2]),
        codebook=Codebook(
            version=1,
            codes=[
                Code(
                    id="AI_ADOPTION",
                    name="AI Adoption",
                    description="Use of AI in workflows",
                    example_quotes=["We use AI for everything"],
                    mention_count=3,
                    confidence=0.8,
                ),
                Code(
                    id="WORKFLOW_CHANGE",
                    name="Workflow Change",
                    description="Changes to work processes",
                    example_quotes=["It changed our workflow"],
                    mention_count=2,
                    confidence=0.7,
                ),
            ],
        ),
        code_applications=[
            CodeApplication(
                code_id="AI_ADOPTION",
                doc_id="doc1",
                quote_text="We use AI for everything",
                confidence=0.8,
            ),
            CodeApplication(
                code_id="WORKFLOW_CHANGE",
                doc_id="doc1",
                quote_text="It changed our workflow",
                confidence=0.7,
            ),
        ],
    )
    return state


def _make_code_hierarchy(code_defs: list[dict]) -> CodeHierarchy:
    """Build a CodeHierarchy from a list of dicts."""
    codes = []
    for cd in code_defs:
        codes.append(ThematicCode(
            id=cd.get("id", cd["name"].upper().replace(" ", "_")),
            name=cd["name"],
            description=cd.get("description", f"Description of {cd['name']}"),
            semantic_definition=cd.get("semantic_definition", f"Definition of {cd['name']}"),
            level=cd.get("level", 0),
            example_quotes=cd.get("example_quotes", [f"Quote about {cd['name']}"]),
            mention_count=cd.get("mention_count", 1),
            discovery_confidence=cd.get("confidence", 0.7),
        ))
    return CodeHierarchy(
        codes=codes,
        total_codes=len(codes),
        analysis_confidence=0.8,
    )


# ---------------------------------------------------------------------------
# ProjectState helper tests
# ---------------------------------------------------------------------------

class TestProjectStateHelpers:

    def test_get_coded_doc_ids(self):
        state = _make_state_with_codes()
        coded = state.get_coded_doc_ids()
        assert coded == {"doc1"}

    def test_get_uncoded_doc_ids(self):
        state = _make_state_with_codes()
        uncoded = state.get_uncoded_doc_ids()
        assert uncoded == ["doc2"]

    def test_all_docs_coded(self):
        state = _make_state_with_codes()
        # Add an application for doc2
        state.code_applications.append(CodeApplication(
            code_id="AI_ADOPTION", doc_id="doc2", quote_text="quote",
        ))
        assert state.get_uncoded_doc_ids() == []

    def test_no_docs_coded(self):
        state = ProjectState(
            corpus=Corpus(documents=[
                Document(id="d1", name="a.txt", content="text"),
                Document(id="d2", name="b.txt", content="text"),
            ]),
        )
        assert len(state.get_uncoded_doc_ids()) == 2
        assert state.get_coded_doc_ids() == set()


# ---------------------------------------------------------------------------
# IncrementalCodingStage tests
# ---------------------------------------------------------------------------

class TestIncrementalCodingStage:

    def test_can_execute_with_uncoded_docs(self):
        state = _make_state_with_codes()
        stage = IncrementalCodingStage()
        assert stage.can_execute(state) is True

    def test_cannot_execute_all_coded(self):
        state = _make_state_with_codes()
        state.code_applications.append(CodeApplication(
            code_id="AI_ADOPTION", doc_id="doc2", quote_text="q",
        ))
        stage = IncrementalCodingStage()
        assert stage.can_execute(state) is False

    def test_cannot_execute_no_codebook(self):
        state = ProjectState(
            corpus=Corpus(documents=[
                Document(id="d1", name="a.txt", content="text"),
            ]),
        )
        stage = IncrementalCodingStage()
        assert stage.can_execute(state) is False

    def test_incremental_coding_applies_existing_codes(self):
        """LLM applies existing codes to new doc — no new codes created."""
        state = _make_state_with_codes()

        # LLM response: applies existing codes to new doc
        response = _make_code_hierarchy([
            {
                "id": "AI_ADOPTION",
                "name": "AI Adoption",
                "description": "Use of AI in workflows",
                "example_quotes": ["Data privacy is our top concern"],
                "confidence": 0.8,
            },
        ])

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=response)
            result = asyncio.run(
                IncrementalCodingStage().execute(state, PipelineContext())
            )

        # Should have original 2 + 1 new application
        assert len(result.code_applications) == 3
        # Codebook should still have 2 codes (no new codes)
        assert len(result.codebook.codes) == 2
        # Iteration should be incremented
        assert result.iteration == 2
        # History should have the old codebook
        assert len(result.codebook_history) == 1

    def test_incremental_coding_adds_new_codes(self):
        """LLM discovers new code in new doc — codebook grows."""
        state = _make_state_with_codes()

        # LLM response: existing code + new code
        response = _make_code_hierarchy([
            {
                "id": "AI_ADOPTION",
                "name": "AI Adoption",
                "example_quotes": ["Data privacy is our top concern"],
                "confidence": 0.8,
            },
            {
                "id": "DATA_PRIVACY",
                "name": "Data Privacy",
                "description": "Concerns about data protection",
                "example_quotes": ["We encrypt all user data"],
                "confidence": 0.9,
            },
        ])

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=response)
            result = asyncio.run(
                IncrementalCodingStage().execute(state, PipelineContext())
            )

        # Codebook should now have 3 codes
        assert len(result.codebook.codes) == 3
        code_names = {c.name for c in result.codebook.codes}
        assert "Data Privacy" in code_names

    def test_incremental_preserves_existing_applications(self):
        """Existing code applications should not be removed."""
        state = _make_state_with_codes()
        original_apps = len(state.code_applications)

        response = _make_code_hierarchy([
            {
                "name": "AI Adoption",
                "example_quotes": ["Data privacy is our top concern"],
                "confidence": 0.8,
            },
        ])

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=response)
            result = asyncio.run(
                IncrementalCodingStage().execute(state, PipelineContext())
            )

        # Must have at least the original applications
        assert len(result.code_applications) >= original_apps

    def test_stage_name(self):
        assert IncrementalCodingStage().name() == "incremental_coding"

    def test_gt_methodology(self):
        """Incremental coding should work with GT methodology."""
        from qc_clean.core.pipeline.stages.gt_open_coding import OpenCodesResponse
        from qc_clean.schemas.gt_schemas import OpenCode

        state = _make_state_with_codes()
        state.config.methodology = Methodology.GROUNDED_THEORY

        response = OpenCodesResponse(
            open_codes=[
                OpenCode(
                    code_name="AI Adoption",
                    description="Use of AI",
                    properties=["p"],
                    dimensions=["d"],
                    supporting_quotes=["Data privacy is our top concern"],
                    frequency=1,
                    confidence=0.8,
                ),
            ],
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=response)
            result = asyncio.run(
                IncrementalCodingStage().execute(state, PipelineContext())
            )

        # Should work without error
        assert len(result.code_applications) >= 2


# ---------------------------------------------------------------------------
# Pipeline factory tests
# ---------------------------------------------------------------------------

class TestIncrementalPipeline:

    def test_creates_default_pipeline(self):
        pipeline = create_incremental_pipeline("default")
        stage_names = [s.name() for s in pipeline.stages]
        assert "incremental_coding" in stage_names
        assert "thematic_coding" not in stage_names
        assert "ingest" not in stage_names

    def test_creates_gt_pipeline(self):
        pipeline = create_incremental_pipeline("grounded_theory")
        stage_names = [s.name() for s in pipeline.stages]
        assert "incremental_coding" in stage_names
        assert "gt_open_coding" not in stage_names
        assert "gt_axial_coding" in stage_names


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestFormatCodebook:

    def test_formats_codebook(self):
        codebook = Codebook(codes=[
            Code(id="C1", name="Theme A", description="First theme",
                 example_quotes=["quote 1"]),
            Code(id="C2", name="Theme B", description="Second theme"),
        ])
        result = _format_codebook_for_prompt(codebook)
        assert "Theme A" in result
        assert "Theme B" in result
        assert "First theme" in result
        assert "quote 1" in result
