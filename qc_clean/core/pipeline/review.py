"""
Human review logic for the analysis pipeline.

Supports reviewing codes, code applications, and codebook modifications.
When codes are modified, creates a new codebook version and supports
re-coding the corpus with the refined codebook.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimAdjudicationStatus,
    ClaimRevision,
    Code,
    CodeApplication,
    CodeRelationship,
    DomainEntityRelationship,
    HumanReviewDecision,
    PipelineStatus,
    ProjectState,
    Provenance,
    ReviewAction,
    ReviewSummary,
)

logger = logging.getLogger(__name__)


class ReviewManager:
    """Manage human review of analysis artifacts."""

    def __init__(self, state: ProjectState):
        self.state = state

    # ------------------------------------------------------------------
    # Query pending items
    # ------------------------------------------------------------------

    def get_pending_codes(self) -> List[Code]:
        """Get all codes in the current codebook for review."""
        return list(self.state.codebook.codes)

    def get_pending_applications(self, code_id: Optional[str] = None) -> List[CodeApplication]:
        """Get code applications for review, optionally filtered by code."""
        if code_id:
            return [a for a in self.state.code_applications if a.code_id == code_id]
        return list(self.state.code_applications)

    def get_pending_claims(self) -> List[AnalyticClaim]:
        """Get all analytic claims available for review."""
        return list(self.state.claims)

    def get_pending_relationships(self) -> List[Dict]:
        """Get code and entity relationships available for review."""
        code_names = {code.id: code.name for code in self.state.codebook.codes}
        entity_names = {entity.id: entity.name for entity in self.state.entities}
        rows: List[Dict] = []

        for rel in self.state.code_relationships:
            rows.append({
                "target_type": "code_relationship",
                "relationship_family": "code",
                "id": rel.id,
                "source_id": rel.source_code_id,
                "target_id": rel.target_code_id,
                "source_name": code_names.get(rel.source_code_id, rel.source_code_id),
                "target_name": code_names.get(rel.target_code_id, rel.target_code_id),
                "relationship_type": rel.relationship_type,
                "strength": rel.strength,
                "evidence": list(rel.evidence),
                "evidence_count": len(rel.evidence),
                "conditions": list(rel.conditions),
                "consequences": list(rel.consequences),
            })

        for rel in self.state.entity_relationships:
            rows.append({
                "target_type": "entity_relationship",
                "relationship_family": "entity",
                "id": rel.id,
                "source_id": rel.entity_1_id,
                "target_id": rel.entity_2_id,
                "source_name": entity_names.get(rel.entity_1_id, rel.entity_1_id),
                "target_name": entity_names.get(rel.entity_2_id, rel.entity_2_id),
                "relationship_type": rel.relationship_type,
                "strength": rel.strength,
                "evidence": list(rel.supporting_evidence),
                "evidence_count": len(rel.supporting_evidence),
            })

        return rows

    def get_review_summary(self) -> ReviewSummary:
        """Summary of what's available for review."""
        active_decisions = sum(1 for decision in self.state.review_decisions if decision.is_active)
        return ReviewSummary(
            codes_count=len(self.state.codebook.codes),
            applications_count=len(self.state.code_applications),
            claims_count=len(self.state.claims),
            relationships_count=(
                len(self.state.code_relationships) + len(self.state.entity_relationships)
            ),
            existing_decisions=len(self.state.review_decisions),
            active_decisions=active_decisions,
            inactive_decisions=len(self.state.review_decisions) - active_decisions,
            pipeline_status=self.state.pipeline_status.value,
            current_phase=self.state.current_phase,
        )

    # ------------------------------------------------------------------
    # Apply decisions
    # ------------------------------------------------------------------

    def apply_decision(self, decision: HumanReviewDecision) -> None:
        """Apply a single review decision to the project state."""
        self.state.review_decisions.append(decision)

        if decision.target_type == "code":
            self._apply_code_decision(decision)
        elif decision.target_type == "code_application":
            self._apply_application_decision(decision)
        elif decision.target_type == "codebook":
            self._apply_codebook_decision(decision)
        elif decision.target_type == "claim":
            self._apply_claim_decision(decision)
        elif decision.target_type == "code_relationship":
            self._apply_code_relationship_decision(decision)
        elif decision.target_type == "entity_relationship":
            self._apply_entity_relationship_decision(decision)
        else:
            raise ValueError(
                f"Unknown target_type: '{decision.target_type}'. "
                "Must be 'code', 'code_application', 'codebook', 'claim', "
                "'code_relationship', or 'entity_relationship'."
            )

        self.state.touch()

    def apply_decisions(self, decisions: List[HumanReviewDecision]) -> Dict:
        """Apply a batch of review decisions. Returns summary."""
        applied = 0
        for d in decisions:
            self.apply_decision(d)
            applied += 1
        return {"applied": applied}

    def approve_all_codes(self) -> Dict:
        """Approve all codes in the current codebook."""
        decisions = []
        for code in self.state.codebook.codes:
            d = HumanReviewDecision(
                target_type="code",
                target_id=code.id,
                action=ReviewAction.APPROVE,
                rationale="Bulk approved",
            )
            decisions.append(d)
        return self.apply_decisions(decisions)

    # ------------------------------------------------------------------
    # Resume pipeline
    # ------------------------------------------------------------------

    def can_resume(self) -> bool:
        """Check if the pipeline can be resumed after review."""
        return self.state.pipeline_status == PipelineStatus.PAUSED_FOR_REVIEW

    def prepare_for_resume(self) -> str:
        """
        Prepare state for pipeline resumption.

        Returns the phase name to resume from.
        """
        if not self.can_resume():
            raise ValueError(
                f"Cannot resume: pipeline is {self.state.pipeline_status.value}"
            )

        # Check if codebook was modified -- if so, bump version
        code_modifications = [
            d for d in self.state.review_decisions
            if d.target_type == "code" and d.action in (
                ReviewAction.MODIFY, ReviewAction.MERGE, ReviewAction.SPLIT, ReviewAction.REJECT
            )
        ]
        if code_modifications:
            self._bump_codebook_version()

        resume_from = self.state.current_phase
        self.state.pipeline_status = PipelineStatus.RUNNING
        return resume_from

    # ------------------------------------------------------------------
    # Internal decision handlers
    # ------------------------------------------------------------------

    def _apply_code_decision(self, decision: HumanReviewDecision) -> None:
        action = decision.action
        code = self.state.codebook.get_code(decision.target_id)

        if action == ReviewAction.APPROVE:
            if code:
                code.provenance = Provenance.HUMAN
            logger.info("Approved code: %s", decision.target_id)

        elif action == ReviewAction.REJECT:
            if code:
                self.state.codebook.codes = [
                    c for c in self.state.codebook.codes if c.id != decision.target_id
                ]
                # Also remove related applications
                self.state.code_applications = [
                    a for a in self.state.code_applications if a.code_id != decision.target_id
                ]
            logger.info("Rejected code: %s", decision.target_id)

        elif action == ReviewAction.MODIFY:
            if code and decision.new_value:
                for key, value in decision.new_value.items():
                    if hasattr(code, key):
                        setattr(code, key, value)
                code.provenance = Provenance.HUMAN
            logger.info("Modified code: %s", decision.target_id)

        elif action == ReviewAction.MERGE:
            # new_value should contain {"merge_into": "target_code_id"}
            if decision.new_value and "merge_into" in decision.new_value:
                merge_target = decision.new_value["merge_into"]
                # Validate merge target exists
                if not self.state.codebook.get_code(merge_target):
                    logger.error("Merge target code %s does not exist", merge_target)
                    return
                # Re-assign applications from source to target
                for app in self.state.code_applications:
                    if app.code_id == decision.target_id:
                        app.code_id = merge_target
                # Remove the merged-away code
                self.state.codebook.codes = [
                    c for c in self.state.codebook.codes if c.id != decision.target_id
                ]
            logger.info("Merged code %s", decision.target_id)

        elif action == ReviewAction.SPLIT:
            # new_value should contain {"new_codes": [{"id": ..., "name": ..., ...}]}
            if decision.new_value and "new_codes" in decision.new_value:
                new_code_ids = []
                for new_code_data in decision.new_value["new_codes"]:
                    if "name" not in new_code_data:
                        logger.error("Split code missing required 'name' field")
                        continue
                    new_code = Code(
                        provenance=Provenance.HUMAN,
                        **new_code_data,
                    )
                    self.state.codebook.codes.append(new_code)
                    new_code_ids.append(new_code.id)
                # Reassign applications: assign to first new code by default
                if new_code_ids:
                    for app in self.state.code_applications:
                        if app.code_id == decision.target_id:
                            app.code_id = new_code_ids[0]
                # Remove the original code
                self.state.codebook.codes = [
                    c for c in self.state.codebook.codes if c.id != decision.target_id
                ]
            logger.info("Split code %s", decision.target_id)

    def _apply_application_decision(self, decision: HumanReviewDecision) -> None:
        if decision.action == ReviewAction.REJECT:
            self.state.code_applications = [
                a for a in self.state.code_applications if a.id != decision.target_id
            ]
            logger.info("Rejected application: %s", decision.target_id)
        elif decision.action == ReviewAction.APPROVE:
            for app in self.state.code_applications:
                if app.id == decision.target_id:
                    app.applied_by = Provenance.HUMAN
            logger.info("Approved application: %s", decision.target_id)
        elif decision.action == ReviewAction.MODIFY:
            if decision.new_value:
                for app in self.state.code_applications:
                    if app.id == decision.target_id:
                        for key, value in decision.new_value.items():
                            if hasattr(app, key):
                                setattr(app, key, value)
                        app.applied_by = Provenance.HUMAN
            logger.info("Modified application: %s", decision.target_id)
        else:
            raise ValueError(
                f"Action '{decision.action.value}' not supported for code_application targets. "
                f"Supported: approve, reject, modify."
            )

    def _apply_codebook_decision(self, decision: HumanReviewDecision) -> None:
        if decision.action == ReviewAction.APPROVE:
            for code in self.state.codebook.codes:
                code.provenance = Provenance.HUMAN
            logger.info("Codebook approved (all codes marked human-reviewed)")
        else:
            raise ValueError(
                f"Action '{decision.action.value}' not supported for codebook targets. "
                f"Supported: approve."
            )

    def _apply_claim_decision(self, decision: HumanReviewDecision) -> None:
        claim = self._get_claim(decision.target_id)
        if claim is None:
            raise ValueError(f"Claim not found: {decision.target_id}")

        if decision.action == ReviewAction.APPROVE:
            claim.adjudication_status = ClaimAdjudicationStatus.RETAINED
            claim.revision_history.append(ClaimRevision(
                actor=Provenance.HUMAN,
                action=decision.action.value,
                rationale=decision.rationale,
            ))
            logger.info("Approved claim: %s", decision.target_id)
        elif decision.action == ReviewAction.REJECT:
            claim.adjudication_status = ClaimAdjudicationStatus.WITHDRAWN
            claim.revision_history.append(ClaimRevision(
                actor=Provenance.HUMAN,
                action=decision.action.value,
                rationale=decision.rationale,
            ))
            logger.info("Rejected claim: %s", decision.target_id)
        elif decision.action == ReviewAction.MODIFY:
            previous_text = claim.claim_text
            if decision.new_value and "claim_text" in decision.new_value:
                claim.claim_text = str(decision.new_value["claim_text"])
            claim.adjudication_status = ClaimAdjudicationStatus.REVISED
            claim.revision_history.append(ClaimRevision(
                actor=Provenance.HUMAN,
                action=decision.action.value,
                rationale=decision.rationale,
                previous_claim_text=previous_text,
                new_claim_text=claim.claim_text,
            ))
            logger.info("Modified claim: %s", decision.target_id)
        else:
            raise ValueError(
                f"Action '{decision.action.value}' not supported for claim targets. "
                f"Supported: approve, reject, modify."
            )

    def _get_claim(self, claim_id: str) -> AnalyticClaim | None:
        """Return a claim by ID."""
        for claim in self.state.claims:
            if claim.id == claim_id:
                return claim
        return None

    def _apply_code_relationship_decision(self, decision: HumanReviewDecision) -> None:
        rel = self._get_code_relationship(decision.target_id)
        if rel is None:
            raise ValueError(f"Code relationship not found: {decision.target_id}")

        if decision.action == ReviewAction.APPROVE:
            logger.info("Approved code relationship: %s", decision.target_id)
        elif decision.action == ReviewAction.REJECT:
            self.state.code_relationships = [
                r for r in self.state.code_relationships if r.id != decision.target_id
            ]
            logger.info("Rejected code relationship: %s", decision.target_id)
        elif decision.action == ReviewAction.MODIFY:
            self._update_relationship_fields(
                rel,
                decision,
                allowed_fields={
                    "relationship_type",
                    "strength",
                    "evidence",
                    "conditions",
                    "consequences",
                },
                target_label="code_relationship",
            )
            logger.info("Modified code relationship: %s", decision.target_id)
        else:
            raise ValueError(
                f"Action '{decision.action.value}' not supported for code_relationship targets. "
                f"Supported: approve, reject, modify."
            )

    def _apply_entity_relationship_decision(self, decision: HumanReviewDecision) -> None:
        rel = self._get_entity_relationship(decision.target_id)
        if rel is None:
            raise ValueError(f"Entity relationship not found: {decision.target_id}")

        if decision.action == ReviewAction.APPROVE:
            logger.info("Approved entity relationship: %s", decision.target_id)
        elif decision.action == ReviewAction.REJECT:
            self.state.entity_relationships = [
                r for r in self.state.entity_relationships if r.id != decision.target_id
            ]
            logger.info("Rejected entity relationship: %s", decision.target_id)
        elif decision.action == ReviewAction.MODIFY:
            self._update_relationship_fields(
                rel,
                decision,
                allowed_fields={"relationship_type", "strength", "supporting_evidence"},
                target_label="entity_relationship",
            )
            logger.info("Modified entity relationship: %s", decision.target_id)
        else:
            raise ValueError(
                f"Action '{decision.action.value}' not supported for entity_relationship targets. "
                f"Supported: approve, reject, modify."
            )

    def _get_code_relationship(self, relationship_id: str) -> CodeRelationship | None:
        """Return a code relationship by ID."""
        for rel in self.state.code_relationships:
            if rel.id == relationship_id:
                return rel
        return None

    def _get_entity_relationship(
        self,
        relationship_id: str,
    ) -> DomainEntityRelationship | None:
        """Return an entity relationship by ID."""
        for rel in self.state.entity_relationships:
            if rel.id == relationship_id:
                return rel
        return None

    def _update_relationship_fields(
        self,
        rel: CodeRelationship | DomainEntityRelationship,
        decision: HumanReviewDecision,
        *,
        allowed_fields: set[str],
        target_label: str,
    ) -> None:
        """Apply a relationship modification after rejecting unknown fields."""
        if not decision.new_value:
            return

        unknown_fields = sorted(set(decision.new_value) - allowed_fields)
        if unknown_fields:
            raise ValueError(
                f"Unsupported fields for {target_label} modify: {', '.join(unknown_fields)}"
            )

        for key, value in decision.new_value.items():
            setattr(rel, key, value)

    def _bump_codebook_version(self) -> None:
        """Save current codebook to history and create new version."""
        import copy
        old_codebook = copy.deepcopy(self.state.codebook)
        self.state.codebook_history.append(old_codebook)
        self.state.codebook.version += 1
        self.state.codebook.created_by = Provenance.HUMAN
        logger.info("Codebook bumped to version %d", self.state.codebook.version)
