"""
End-to-end tests with real LLM calls.

These tests require OPENAI_API_KEY to be set and make actual API calls.
They validate the full pipeline produces meaningful output, not just that
it runs without errors.

Run with:
    OPENAI_API_KEY=... python -m pytest tests/test_e2e.py -v -s

Skip in CI:
    Tests are automatically skipped if OPENAI_API_KEY is not set.
"""

import asyncio
import os

import pytest

from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.pipeline_factory import (
    create_incremental_pipeline,
    create_pipeline,
)
from qc_clean.schemas.domain import (
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    Methodology,
    PipelineStatus,
    ProjectConfig,
    ProjectState,
)

# Skip all tests in this module if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)

# Sample interview text for testing
INTERVIEW_1 = """
Interviewer: Can you tell me about how AI has changed your work?

Jane Smith: Absolutely. We started using AI tools about two years ago, and it
completely transformed our workflow. Before AI, we spent about 60% of our time
on data entry and routine analysis. Now the AI handles most of that, and we
can focus on strategic decision-making.

Interviewer: What concerns do you have about AI in the workplace?

Jane Smith: Privacy is my biggest concern. We're feeding sensitive client data
into these systems, and I'm not always sure where that data ends up. We also
had an incident where the AI made a recommendation based on biased training
data, which could have led to discriminatory outcomes if we hadn't caught it.

Interviewer: How do your colleagues feel about these changes?

Jane Smith: It's mixed. The younger staff love it — they adapted quickly and
see it as an enhancement. But several senior employees feel threatened. One
colleague told me she's worried about becoming obsolete. There's definitely
a generational divide in how people perceive AI at work.
"""

INTERVIEW_2 = """
Interviewer: What has your experience been with AI implementation?

Robert Chen: We took a cautious approach. Rather than replacing existing
processes, we introduced AI as a supplementary tool. Staff can choose to
use it or not. That voluntary adoption model has worked well — about 70%
of the team now uses AI daily, and the resistance we expected never really
materialized.

Interviewer: Have you encountered any challenges?

Robert Chen: The learning curve was steeper than expected. We budgeted one
month for training, but it really took three months before people felt
comfortable. Cost is another factor — the enterprise AI licenses are
expensive, and we're still trying to measure ROI. Also, the AI sometimes
generates plausible-sounding but incorrect analyses, so we always need
human verification.

Interviewer: What advice would you give to other organizations?

Robert Chen: Start small. Pick one specific use case, prove the value, then
expand. Don't try to automate everything at once. And invest heavily in
training — that's where most organizations underinvest.
"""


@pytest.fixture
def single_doc_state():
    """State with a single interview document."""
    return ProjectState(
        name="E2E Single Doc",
        config=ProjectConfig(methodology=Methodology.DEFAULT),
        corpus=Corpus(documents=[
            Document(name="interview1.txt", content=INTERVIEW_1),
        ]),
    )


@pytest.fixture
def multi_doc_state():
    """State with two interview documents."""
    return ProjectState(
        name="E2E Multi Doc",
        config=ProjectConfig(methodology=Methodology.DEFAULT),
        corpus=Corpus(documents=[
            Document(name="interview1.txt", content=INTERVIEW_1),
            Document(name="interview2.txt", content=INTERVIEW_2),
        ]),
    )


@pytest.fixture
def gt_state():
    """State configured for grounded theory."""
    return ProjectState(
        name="E2E Grounded Theory",
        config=ProjectConfig(methodology=Methodology.GROUNDED_THEORY),
        corpus=Corpus(documents=[
            Document(name="interview1.txt", content=INTERVIEW_1),
        ]),
    )


# ---------------------------------------------------------------------------
# Default pipeline E2E
# ---------------------------------------------------------------------------

class TestDefaultPipelineE2E:

    def test_single_doc_pipeline(self, single_doc_state):
        """Full default pipeline on one document produces meaningful output."""
        pipeline = create_pipeline(methodology="default")
        ctx = PipelineContext(
            interviews=[{"name": "interview1.txt", "content": INTERVIEW_1}],
        )

        result = asyncio.run(pipeline.run(single_doc_state, ctx))

        # Pipeline completed
        assert result.pipeline_status == PipelineStatus.COMPLETED

        # Codes were discovered
        assert len(result.codebook.codes) >= 3, (
            f"Expected at least 3 codes, got {len(result.codebook.codes)}"
        )

        # Code applications exist
        assert len(result.code_applications) >= 3, (
            f"Expected at least 3 applications, got {len(result.code_applications)}"
        )

        # Each code has a name and description
        for code in result.codebook.codes:
            assert code.name, f"Code {code.id} has no name"
            assert code.description, f"Code {code.name} has no description"

        # Applications have quotes
        for app in result.code_applications:
            assert app.quote_text, f"Application for {app.code_id} has no quote"

        # Memos were generated (at least from thematic coding stage)
        assert len(result.memos) >= 1, "Expected at least 1 analytical memo"

        # Speaker detection worked
        doc = result.corpus.documents[0]
        assert len(doc.detected_speakers) >= 2, (
            f"Expected at least 2 speakers, got {doc.detected_speakers}"
        )

        # Phase results were recorded
        assert len(result.phase_results) >= 5

        print(f"\n  Codes: {len(result.codebook.codes)}")
        print(f"  Applications: {len(result.code_applications)}")
        print(f"  Speakers: {doc.detected_speakers}")
        print(f"  Memos: {len(result.memos)}")
        for code in result.codebook.codes:
            print(f"    - {code.name} (mentions={code.mention_count})")

    def test_multi_doc_pipeline(self, multi_doc_state):
        """Multi-document pipeline produces cross-interview analysis."""
        pipeline = create_pipeline(methodology="default")
        ctx = PipelineContext(
            interviews=[
                {"name": "interview1.txt", "content": INTERVIEW_1},
                {"name": "interview2.txt", "content": INTERVIEW_2},
            ],
        )

        result = asyncio.run(pipeline.run(multi_doc_state, ctx))

        assert result.pipeline_status == PipelineStatus.COMPLETED
        assert len(result.codebook.codes) >= 3

        # Cross-interview memo should exist (2 docs)
        cross_memos = [m for m in result.memos if m.memo_type == "cross_case"]
        assert len(cross_memos) >= 1, "Expected cross-interview analysis memo"

        # Applications should reference both documents
        doc_ids_in_apps = {app.doc_id for app in result.code_applications}
        corpus_doc_ids = {d.id for d in result.corpus.documents}
        assert len(doc_ids_in_apps & corpus_doc_ids) >= 2, (
            "Expected applications from at least 2 documents"
        )

        print(f"\n  Codes: {len(result.codebook.codes)}")
        print(f"  Applications: {len(result.code_applications)}")
        print(f"  Docs with applications: {len(doc_ids_in_apps)}")
        print(f"  Memos: {len(result.memos)}")


# ---------------------------------------------------------------------------
# GT constant comparison E2E
# ---------------------------------------------------------------------------

class TestGTConstantComparisonE2E:

    def test_gt_pipeline(self, gt_state):
        """GT pipeline with constant comparison produces open codes + theory."""
        pipeline = create_pipeline(methodology="grounded_theory")
        ctx = PipelineContext(
            interviews=[{"name": "interview1.txt", "content": INTERVIEW_1}],
        )

        result = asyncio.run(pipeline.run(gt_state, ctx))

        assert result.pipeline_status == PipelineStatus.COMPLETED

        # Open codes discovered
        assert len(result.codebook.codes) >= 3, (
            f"Expected at least 3 codes from GT, got {len(result.codebook.codes)}"
        )

        # Code applications exist
        assert len(result.code_applications) >= 2

        # Core categories identified
        assert len(result.core_categories) >= 1, (
            f"Expected at least 1 core category, got {len(result.core_categories)}"
        )

        # Theoretical model produced
        assert result.theoretical_model is not None
        assert result.theoretical_model.model_name

        # Memos from GT stages
        assert len(result.memos) >= 1

        print(f"\n  Codes: {len(result.codebook.codes)}")
        print(f"  Applications: {len(result.code_applications)}")
        print(f"  Core categories: {len(result.core_categories)}")
        print(f"  Theory: {result.theoretical_model.model_name}")
        print(f"  Memos: {len(result.memos)}")
        for code in result.codebook.codes[:5]:
            print(f"    - {code.name}")


# ---------------------------------------------------------------------------
# Incremental coding E2E
# ---------------------------------------------------------------------------

class TestIncrementalCodingE2E:

    def test_recode_adds_new_doc(self, single_doc_state):
        """After initial pipeline, adding a new doc and recoding works."""
        # Step 1: Run initial pipeline
        pipeline = create_pipeline(methodology="default")
        ctx = PipelineContext(
            interviews=[{"name": "interview1.txt", "content": INTERVIEW_1}],
        )
        state = asyncio.run(pipeline.run(single_doc_state, ctx))
        assert state.pipeline_status == PipelineStatus.COMPLETED

        initial_codes = len(state.codebook.codes)
        initial_apps = len(state.code_applications)

        # Step 2: Add a new document
        state.corpus.add_document(
            Document(name="interview2.txt", content=INTERVIEW_2)
        )

        # Verify the new doc is uncoded
        uncoded = state.get_uncoded_doc_ids()
        assert len(uncoded) == 1

        # Step 3: Run incremental pipeline
        state.pipeline_status = PipelineStatus.PENDING
        incr_pipeline = create_incremental_pipeline(methodology="default")
        ctx2 = PipelineContext()
        state = asyncio.run(incr_pipeline.run(state, ctx2))

        assert state.pipeline_status == PipelineStatus.COMPLETED

        # Should have more applications now
        assert len(state.code_applications) > initial_apps, (
            f"Expected more apps after recode: {len(state.code_applications)} vs {initial_apps}"
        )

        # All docs should now be coded
        assert len(state.get_uncoded_doc_ids()) == 0

        # Codebook history should have the old codebook
        assert len(state.codebook_history) >= 1

        # Iteration should be incremented
        assert state.iteration >= 2

        print(f"\n  Initial codes: {initial_codes}, after recode: {len(state.codebook.codes)}")
        print(f"  Initial apps: {initial_apps}, after recode: {len(state.code_applications)}")
        print(f"  Iteration: {state.iteration}")
        print(f"  Codebook history entries: {len(state.codebook_history)}")


# ---------------------------------------------------------------------------
# Graph data endpoint E2E
# ---------------------------------------------------------------------------

class TestGraphDataE2E:

    def test_graph_data_from_completed_state(self, multi_doc_state):
        """Graph data endpoints return valid data after pipeline completes."""
        pipeline = create_pipeline(methodology="default")
        ctx = PipelineContext(
            interviews=[
                {"name": "interview1.txt", "content": INTERVIEW_1},
                {"name": "interview2.txt", "content": INTERVIEW_2},
            ],
        )
        state = asyncio.run(pipeline.run(multi_doc_state, ctx))

        # Test graph code data construction (same logic as the API endpoint)
        nodes = []
        for code in state.codebook.codes:
            nodes.append({
                "id": code.id,
                "name": code.name,
                "level": code.level,
                "mention_count": code.mention_count,
                "confidence": code.confidence,
            })

        assert len(nodes) >= 3
        for node in nodes:
            assert node["name"]
            assert node["id"]

        # Entity nodes
        entity_nodes = [
            {"id": e.id, "name": e.name, "type": e.entity_type}
            for e in state.entities
        ]
        # Entities may or may not be present depending on the data

        print(f"\n  Code nodes: {len(nodes)}")
        print(f"  Entity nodes: {len(entity_nodes)}")
        print(f"  Code relationships: {len(state.code_relationships)}")
        print(f"  Entity relationships: {len(state.entity_relationships)}")


# ---------------------------------------------------------------------------
# Export E2E
# ---------------------------------------------------------------------------

class TestExportE2E:

    def test_export_completed_state(self, single_doc_state, tmp_path):
        """Export works on a state that went through a real pipeline."""
        pipeline = create_pipeline(methodology="default")
        ctx = PipelineContext(
            interviews=[{"name": "interview1.txt", "content": INTERVIEW_1}],
        )
        state = asyncio.run(pipeline.run(single_doc_state, ctx))

        from qc_clean.core.export.data_exporter import ProjectExporter
        exporter = ProjectExporter()

        # JSON export
        json_path = exporter.export_json(state, str(tmp_path / "export.json"))
        assert os.path.exists(json_path)
        import json
        with open(json_path) as f:
            data = json.load(f)
        assert "codebook" in data
        assert len(data["codebook"]["codes"]) >= 3

        # Markdown export
        md_path = exporter.export_markdown(state, str(tmp_path / "report.md"))
        assert os.path.exists(md_path)
        md_content = open(md_path).read()
        assert "## Codebook" in md_content or "## Codes" in md_content

        # CSV export
        csv_paths = exporter.export_csv(state, str(tmp_path / "csv"))
        assert len(csv_paths) >= 2  # codes.csv + applications.csv at minimum

        print(f"\n  JSON: {json_path}")
        print(f"  Markdown: {md_path}")
        print(f"  CSV files: {csv_paths}")
