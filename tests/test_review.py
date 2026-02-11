"""
Tests for the human review loop (qc_clean.core.pipeline.review).
"""

import pytest

from qc_clean.schemas.domain import (
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    HumanReviewDecision,
    PipelineStatus,
    ProjectState,
    Provenance,
    ReviewAction,
)
from qc_clean.core.pipeline.review import ReviewManager


@pytest.fixture
def review_state():
    """A state with a codebook and applications, paused for review."""
    codes = [
        Code(id="C1", name="Theme A", description="desc A", mention_count=5, confidence=0.8),
        Code(id="C2", name="Theme B", description="desc B", mention_count=3, confidence=0.6),
        Code(id="C3", name="Theme C", description="desc C", mention_count=1, confidence=0.3),
    ]
    apps = [
        CodeApplication(id="A1", code_id="C1", doc_id="d1", quote_text="quote1"),
        CodeApplication(id="A2", code_id="C1", doc_id="d1", quote_text="quote2"),
        CodeApplication(id="A3", code_id="C2", doc_id="d1", quote_text="quote3"),
        CodeApplication(id="A4", code_id="C3", doc_id="d1", quote_text="quote4"),
    ]
    return ProjectState(
        corpus=Corpus(documents=[Document(id="d1", name="test.txt")]),
        codebook=Codebook(codes=codes),
        code_applications=apps,
        pipeline_status=PipelineStatus.PAUSED_FOR_REVIEW,
        current_phase="thematic_coding",
    )


class TestReviewManager:
    def test_get_review_summary(self, review_state):
        rm = ReviewManager(review_state)
        summary = rm.get_review_summary()
        assert summary["codes_count"] == 3
        assert summary["applications_count"] == 4
        assert summary["pipeline_status"] == "paused_for_review"

    def test_approve_code(self, review_state):
        rm = ReviewManager(review_state)
        decision = HumanReviewDecision(
            target_type="code",
            target_id="C1",
            action=ReviewAction.APPROVE,
            rationale="Good code",
        )
        rm.apply_decision(decision)
        code = review_state.codebook.get_code("C1")
        assert code.provenance == Provenance.HUMAN
        assert len(review_state.review_decisions) == 1

    def test_reject_code(self, review_state):
        rm = ReviewManager(review_state)
        decision = HumanReviewDecision(
            target_type="code",
            target_id="C3",
            action=ReviewAction.REJECT,
        )
        rm.apply_decision(decision)
        assert review_state.codebook.get_code("C3") is None
        # Applications for C3 should also be removed
        assert all(a.code_id != "C3" for a in review_state.code_applications)
        assert len(review_state.code_applications) == 3  # A1, A2, A3 remain

    def test_modify_code(self, review_state):
        rm = ReviewManager(review_state)
        decision = HumanReviewDecision(
            target_type="code",
            target_id="C2",
            action=ReviewAction.MODIFY,
            new_value={"name": "Theme B (revised)", "description": "updated desc"},
        )
        rm.apply_decision(decision)
        code = review_state.codebook.get_code("C2")
        assert code.name == "Theme B (revised)"
        assert code.description == "updated desc"
        assert code.provenance == Provenance.HUMAN

    def test_merge_codes(self, review_state):
        rm = ReviewManager(review_state)
        decision = HumanReviewDecision(
            target_type="code",
            target_id="C3",
            action=ReviewAction.MERGE,
            new_value={"merge_into": "C1"},
        )
        rm.apply_decision(decision)
        # C3 should be gone
        assert review_state.codebook.get_code("C3") is None
        # Application A4 (was C3) should now point to C1
        a4 = next(a for a in review_state.code_applications if a.id == "A4")
        assert a4.code_id == "C1"

    def test_split_code(self, review_state):
        rm = ReviewManager(review_state)
        decision = HumanReviewDecision(
            target_type="code",
            target_id="C1",
            action=ReviewAction.SPLIT,
            new_value={
                "new_codes": [
                    {"id": "C1a", "name": "Theme A1", "description": "first half"},
                    {"id": "C1b", "name": "Theme A2", "description": "second half"},
                ]
            },
        )
        rm.apply_decision(decision)
        assert review_state.codebook.get_code("C1") is None
        assert review_state.codebook.get_code("C1a") is not None
        assert review_state.codebook.get_code("C1b") is not None
        assert review_state.codebook.get_code("C1a").provenance == Provenance.HUMAN

    def test_reject_application(self, review_state):
        rm = ReviewManager(review_state)
        decision = HumanReviewDecision(
            target_type="code_application",
            target_id="A2",
            action=ReviewAction.REJECT,
        )
        rm.apply_decision(decision)
        assert all(a.id != "A2" for a in review_state.code_applications)
        assert len(review_state.code_applications) == 3

    def test_approve_all_codes(self, review_state):
        rm = ReviewManager(review_state)
        result = rm.approve_all_codes()
        assert result["applied"] == 3
        for code in review_state.codebook.codes:
            assert code.provenance == Provenance.HUMAN

    def test_can_resume(self, review_state):
        rm = ReviewManager(review_state)
        assert rm.can_resume() is True

        review_state.pipeline_status = PipelineStatus.COMPLETED
        assert rm.can_resume() is False

    def test_prepare_for_resume_no_modifications(self, review_state):
        rm = ReviewManager(review_state)
        rm.approve_all_codes()
        resume_from = rm.prepare_for_resume()
        assert resume_from == "thematic_coding"
        assert review_state.pipeline_status == PipelineStatus.RUNNING
        # No codebook version bump (only approvals)
        assert review_state.codebook.version == 1

    def test_prepare_for_resume_with_modifications(self, review_state):
        rm = ReviewManager(review_state)
        # Modify a code
        rm.apply_decision(HumanReviewDecision(
            target_type="code",
            target_id="C1",
            action=ReviewAction.MODIFY,
            new_value={"name": "Modified"},
        ))
        resume_from = rm.prepare_for_resume()
        assert resume_from == "thematic_coding"
        # Codebook should have been bumped
        assert review_state.codebook.version == 2
        assert len(review_state.codebook_history) == 1

    def test_apply_batch_decisions(self, review_state):
        rm = ReviewManager(review_state)
        decisions = [
            HumanReviewDecision(
                target_type="code", target_id="C1", action=ReviewAction.APPROVE
            ),
            HumanReviewDecision(
                target_type="code", target_id="C2", action=ReviewAction.APPROVE
            ),
            HumanReviewDecision(
                target_type="code", target_id="C3", action=ReviewAction.REJECT
            ),
        ]
        result = rm.apply_decisions(decisions)
        assert result["applied"] == 3
        assert review_state.codebook.get_code("C3") is None
        assert len(review_state.codebook.codes) == 2
