"""
Pipeline engine: composable stage-based analysis pipeline.

Replaces the monolithic _process_analysis with an orchestrator that runs
stages sequentially, pauses at human-review checkpoints, and saves state
after each stage.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from qc_clean.schemas.domain import (
    AnalysisPhaseResult,
    PipelineStatus,
    ProjectState,
)

logger = logging.getLogger(__name__)


class PipelineContext(BaseModel):
    """Typed configuration for pipeline execution.

    Input fields are set by the caller. Inter-stage fields are populated
    by upstream stages and consumed by downstream stages.

    ``model_config`` uses ``extra="forbid"`` so that constructing with a
    misspelled field name raises immediately.
    """

    model_config = ConfigDict(extra="forbid")

    # --- Input fields (set by caller) ---
    model_name: str = "gpt-5-mini"
    interviews: List[Dict[str, Any]] = Field(default_factory=list)
    irr_prompt_suffix: str = ""

    # --- Inter-stage: thematic pipeline ---
    phase1_json: Optional[str] = None
    phase2_json: Optional[str] = None
    phase3_json: Optional[str] = None

    # --- Inter-stage: GT pipeline ---
    gt_open_codes: Optional[List[Any]] = None
    gt_open_codes_text: Optional[str] = None
    gt_axial_relationships: Optional[List[Any]] = None
    gt_axial_text: Optional[str] = None
    gt_core_categories: Optional[List[Any]] = None
    gt_core_text: Optional[str] = None

    def require(self, field: str, stage_name: str) -> str:
        """Get a required field value, raising if the upstream stage didn't populate it.

        This prevents downstream stages from silently running with empty data
        when an upstream stage was skipped or failed.
        """
        value = getattr(self, field, None)
        if not value:
            raise RuntimeError(
                f"Stage '{stage_name}' requires '{field}' but it is missing. "
                f"The upstream stage that produces this value may have been skipped or failed."
            )
        return value


class PipelineStage(ABC):
    """Abstract base class for a single analysis stage."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable stage name (used as phase key)."""
        ...

    @abstractmethod
    async def execute(self, state: ProjectState, ctx: PipelineContext) -> ProjectState:
        """
        Run this stage, mutating and returning *state*.

        Implementations should update ``state`` in-place (add codes, entities,
        etc.) and return the same object.
        """
        ...

    def can_execute(self, state: ProjectState) -> bool:
        """Return True if preconditions for this stage are met."""
        return True

    def requires_human_review(self) -> bool:
        """Return True if pipeline should pause after this stage."""
        return False


class AnalysisPipeline:
    """
    Orchestrator that runs a sequence of PipelineStage objects.

    * Runs stages sequentially.
    * Records an AnalysisPhaseResult for each stage.
    * Pauses when a stage declares ``requires_human_review()``.
    * Calls an optional ``on_stage_complete`` callback after each stage
      (useful for persistence / progress reporting).
    """

    def __init__(
        self,
        stages: List[PipelineStage],
        on_stage_complete=None,
    ):
        self.stages = stages
        self.on_stage_complete = on_stage_complete  # async callable(state)

    async def run(
        self,
        state: ProjectState,
        ctx: PipelineContext,
        resume_from: Optional[str] = None,
    ) -> ProjectState:
        """
        Execute the pipeline.

        Parameters
        ----------
        state : ProjectState
            The project being analyzed.
        config : dict
            Runtime configuration (model name, etc.).
        resume_from : str, optional
            If set, skip stages up to and including this one
            (used to resume after a human-review pause).

        Returns the (mutated) ProjectState.
        """
        state.pipeline_status = PipelineStatus.RUNNING
        skipping = resume_from is not None

        # Validate resume_from matches a known stage
        if resume_from is not None:
            known_stages = {s.name() for s in self.stages}
            if resume_from not in known_stages:
                raise ValueError(
                    f"Invalid resume_from '{resume_from}'. "
                    f"Known stages: {', '.join(sorted(known_stages))}"
                )

        for stage in self.stages:
            # Handle resume: skip stages already completed
            if skipping:
                if stage.name() == resume_from:
                    skipping = False
                logger.info("Skipping already-completed stage: %s", stage.name())
                continue

            # Check preconditions
            if not stage.can_execute(state):
                logger.info("Skipping stage %s (preconditions not met)", stage.name())
                phase_result = AnalysisPhaseResult(
                    phase_name=stage.name(),
                    status=PipelineStatus.SKIPPED,
                )
                state.add_phase_result(phase_result)
                continue

            # Execute
            state.current_phase = stage.name()
            phase_result = AnalysisPhaseResult(
                phase_name=stage.name(),
                status=PipelineStatus.RUNNING,
                started_at=datetime.now().isoformat(),
            )
            state.add_phase_result(phase_result)
            logger.info("Starting stage: %s", stage.name())

            try:
                state = await stage.execute(state, ctx)
                phase_result.status = PipelineStatus.COMPLETED
                phase_result.completed_at = datetime.now().isoformat()
                state.add_phase_result(phase_result)
                logger.info("Completed stage: %s", stage.name())
            except Exception as exc:
                phase_result.status = PipelineStatus.FAILED
                phase_result.error_message = str(exc)
                phase_result.completed_at = datetime.now().isoformat()
                state.add_phase_result(phase_result)
                state.pipeline_status = PipelineStatus.FAILED
                logger.error(
                    "Stage %s failed: %s (docs=%d, codes=%d, applications=%d)",
                    stage.name(), exc, state.corpus.num_documents,
                    len(state.codebook.codes), len(state.code_applications),
                )
                raise

            # Post-stage callback (e.g. save state)
            if self.on_stage_complete:
                await self.on_stage_complete(state)

            # Pause for human review if required
            if stage.requires_human_review():
                state.pipeline_status = PipelineStatus.PAUSED_FOR_REVIEW
                state.current_phase = stage.name()
                logger.info("Paused for human review after stage: %s", stage.name())
                return state

        # All stages complete
        state.pipeline_status = PipelineStatus.COMPLETED
        state.current_phase = None
        state.touch()
        return state
