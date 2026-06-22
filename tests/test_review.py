"""
Tests for the human review loop (qc_clean.core.pipeline.review).
"""

import pytest

from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimAdjudicationStatus,
    ClaimKind,
    ClaimScope,
    Code,
    CodeApplication,
    CodeRelationship,
    Codebook,
    Corpus,
    DomainEntityRelationship,
    Document,
    Entity,
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
        assert summary.codes_count == 3
        assert summary.applications_count == 4
        assert summary.claims_count == 0
        assert summary.existing_decisions == 0
        assert summary.active_decisions == 0
        assert summary.inactive_decisions == 0
        assert summary.pipeline_status == "paused_for_review"

    def test_review_summary_counts_active_and_inactive_decisions(self, review_state):
        review_state.review_decisions = [
            HumanReviewDecision(
                target_type="code",
                target_id="C1",
                action=ReviewAction.APPROVE,
            ),
            HumanReviewDecision(
                target_type="claim",
                target_id="claim-old",
                action=ReviewAction.REJECT,
                is_active=False,
                inactive_reason="target claim invalidated by incremental recode",
                inactive_at="2026-06-21T00:00:00",
            ),
        ]
        rm = ReviewManager(review_state)

        summary = rm.get_review_summary()

        assert summary.existing_decisions == 2
        assert summary.active_decisions == 1
        assert summary.inactive_decisions == 1

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

    def test_claim_review_approve_reject_modify_updates_claim_adjudication(self, review_state):
        review_state.claims = [
            AnalyticClaim(
                id="claim-1",
                claim_kind=ClaimKind.SYNTHESIS_FINDING,
                source_stage="synthesis",
                claim_text="Efficiency improves workflow.",
                scope=ClaimScope(corpus_level=True, code_ids=["C1"]),
                origin_object_type="synthesis",
                origin_object_id="finding:0",
            )
        ]
        rm = ReviewManager(review_state)
        assert rm.get_pending_claims()[0].id == "claim-1"
        assert rm.get_review_summary().claims_count == 1

        rm.apply_decision(HumanReviewDecision(
            target_type="claim",
            target_id="claim-1",
            action=ReviewAction.APPROVE,
            rationale="Supported by reviewed evidence.",
        ))
        claim = review_state.claims[0]
        assert claim.adjudication_status == ClaimAdjudicationStatus.RETAINED
        assert claim.revision_history[-1].action == "approve"

        rm.apply_decision(HumanReviewDecision(
            target_type="claim",
            target_id="claim-1",
            action=ReviewAction.MODIFY,
            rationale="Narrow scope.",
            new_value={"claim_text": "Efficiency improves workflow for Alex."},
        ))
        assert claim.claim_text == "Efficiency improves workflow for Alex."
        assert claim.adjudication_status == ClaimAdjudicationStatus.REVISED
        assert claim.revision_history[-1].previous_claim_text == "Efficiency improves workflow."
        assert claim.revision_history[-1].new_claim_text == "Efficiency improves workflow for Alex."

        rm.apply_decision(HumanReviewDecision(
            target_type="claim",
            target_id="claim-1",
            action=ReviewAction.REJECT,
            rationale="Contradicted by a negative case.",
        ))
        assert claim.adjudication_status == ClaimAdjudicationStatus.WITHDRAWN
        assert claim.revision_history[-1].action == "reject"

    def test_claim_review_invalid_claim_id_fails_loud(self, review_state):
        rm = ReviewManager(review_state)
        with pytest.raises(ValueError, match="Claim not found"):
            rm.apply_decision(HumanReviewDecision(
                target_type="claim",
                target_id="missing-claim",
                action=ReviewAction.APPROVE,
            ))

    def test_claim_review_unsupported_action_fails_loud(self, review_state):
        review_state.claims = [
            AnalyticClaim(
                id="claim-1",
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="Theme A is a code.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="code",
                origin_object_id="C1",
            )
        ]
        rm = ReviewManager(review_state)
        with pytest.raises(ValueError, match="not supported for claim targets"):
            rm.apply_decision(HumanReviewDecision(
                target_type="claim",
                target_id="claim-1",
                action=ReviewAction.MERGE,
            ))

    def test_relationship_review_summary_and_pending_rows(self, review_state):
        review_state.entities = [
            Entity(id="E1", name="Scheduler", entity_type="tool"),
            Entity(id="E2", name="Front desk", entity_type="team"),
        ]
        review_state.code_relationships = [
            CodeRelationship(
                id="CR1",
                source_code_id="C1",
                target_code_id="C2",
                relationship_type="supports",
                strength=0.7,
                evidence=["quote one"],
            )
        ]
        review_state.entity_relationships = [
            DomainEntityRelationship(
                id="ER1",
                entity_1_id="E1",
                entity_2_id="E2",
                relationship_type="used_by",
                strength=0.8,
                supporting_evidence=["quote two"],
            )
        ]
        rm = ReviewManager(review_state)

        summary = rm.get_review_summary()
        rows = rm.get_pending_relationships()

        assert summary.relationships_count == 2
        assert [row["target_type"] for row in rows] == [
            "code_relationship",
            "entity_relationship",
        ]
        assert rows[0]["source_name"] == "Theme A"
        assert rows[0]["target_name"] == "Theme B"
        assert rows[0]["evidence_count"] == 1
        assert rows[1]["source_name"] == "Scheduler"
        assert rows[1]["target_name"] == "Front desk"

    def test_code_relationship_review_reject_modify_and_missing_id(self, review_state):
        review_state.code_relationships = [
            CodeRelationship(
                id="CR1",
                source_code_id="C1",
                target_code_id="C2",
                relationship_type="supports",
                strength=0.7,
                evidence=["old evidence"],
            ),
            CodeRelationship(
                id="CR2",
                source_code_id="C2",
                target_code_id="C3",
                relationship_type="contrasts",
                strength=0.4,
            ),
        ]
        rm = ReviewManager(review_state)

        rm.apply_decision(HumanReviewDecision(
            target_type="code_relationship",
            target_id="CR1",
            action=ReviewAction.REJECT,
            rationale="Not supported.",
        ))
        assert [rel.id for rel in review_state.code_relationships] == ["CR2"]

        rm.apply_decision(HumanReviewDecision(
            target_type="code_relationship",
            target_id="CR2",
            action=ReviewAction.MODIFY,
            rationale="Narrowed after review.",
            new_value={
                "relationship_type": "moderates",
                "strength": 0.9,
                "evidence": ["updated evidence"],
                "conditions": ["when staffing is thin"],
                "consequences": ["handoffs change"],
            },
        ))
        rel = review_state.code_relationships[0]
        assert rel.relationship_type == "moderates"
        assert rel.strength == 0.9
        assert rel.evidence == ["updated evidence"]
        assert rel.conditions == ["when staffing is thin"]
        assert rel.consequences == ["handoffs change"]

        with pytest.raises(ValueError, match="Code relationship not found"):
            rm.apply_decision(HumanReviewDecision(
                target_type="code_relationship",
                target_id="missing",
                action=ReviewAction.APPROVE,
            ))

    def test_entity_relationship_review_reject_modify_and_unsupported_action(self, review_state):
        review_state.entity_relationships = [
            DomainEntityRelationship(
                id="ER1",
                entity_1_id="E1",
                entity_2_id="E2",
                relationship_type="used_by",
                strength=0.8,
                supporting_evidence=["old evidence"],
            ),
            DomainEntityRelationship(
                id="ER2",
                entity_1_id="E2",
                entity_2_id="E3",
                relationship_type="reports_to",
                strength=0.5,
            ),
        ]
        rm = ReviewManager(review_state)

        rm.apply_decision(HumanReviewDecision(
            target_type="entity_relationship",
            target_id="ER1",
            action=ReviewAction.REJECT,
            rationale="Rejected by reviewer.",
        ))
        assert [rel.id for rel in review_state.entity_relationships] == ["ER2"]

        rm.apply_decision(HumanReviewDecision(
            target_type="entity_relationship",
            target_id="ER2",
            action=ReviewAction.MODIFY,
            rationale="Updated type.",
            new_value={
                "relationship_type": "coordinates_with",
                "strength": 0.6,
                "supporting_evidence": ["new evidence"],
            },
        ))
        rel = review_state.entity_relationships[0]
        assert rel.relationship_type == "coordinates_with"
        assert rel.strength == 0.6
        assert rel.supporting_evidence == ["new evidence"]

        with pytest.raises(ValueError, match="not supported for entity_relationship targets"):
            rm.apply_decision(HumanReviewDecision(
                target_type="entity_relationship",
                target_id="ER2",
                action=ReviewAction.MERGE,
            ))

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
