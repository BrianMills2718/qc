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
    Code,
    CodeApplication,
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

    def get_review_summary(self) -> ReviewSummary:
        """Summary of what's available for review."""
        return ReviewSummary(
            codes_count=len(self.state.codebook.codes),
            applications_count=len(self.state.code_applications),
            existing_decisions=len(self.state.review_decisions),
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
        else:
            raise ValueError(
                f"Unknown target_type: '{decision.target_type}'. "
                f"Must be 'code', 'code_application', or 'codebook'."
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

    def _bump_codebook_version(self) -> None:
        """Save current codebook to history and create new version."""
        import copy
        old_codebook = copy.deepcopy(self.state.codebook)
        self.state.codebook_history.append(old_codebook)
        self.state.codebook.version += 1
        self.state.codebook.created_by = Provenance.HUMAN
        logger.info("Codebook bumped to version %d", self.state.codebook.version)
