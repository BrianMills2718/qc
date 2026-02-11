"""
Pipeline factory: create an AnalysisPipeline from configuration.
"""

from __future__ import annotations

import logging
from typing import Optional

from qc_clean.schemas.domain import Methodology
from .pipeline_engine import AnalysisPipeline

logger = logging.getLogger(__name__)


def create_pipeline(
    methodology: str = "default",
    on_stage_complete=None,
    enable_human_review: bool = False,
) -> AnalysisPipeline:
    """
    Build an AnalysisPipeline with the appropriate stages.

    Parameters
    ----------
    methodology : str
        One of "default", "thematic_analysis", "grounded_theory".
    on_stage_complete : callable, optional
        Async callback invoked after each stage (e.g. for persistence).
    enable_human_review : bool
        If True, the coding stage will pause for human review.
    """
    from .stages.ingest import IngestStage
    from .stages.thematic_coding import ThematicCodingStage
    from .stages.perspective import PerspectiveStage
    from .stages.relationship import RelationshipStage
    from .stages.synthesis import SynthesisStage

    from .stages.cross_interview import CrossInterviewStage

    if methodology == Methodology.GROUNDED_THEORY.value or methodology == "grounded_theory":
        from .stages.gt_open_coding import GTOpenCodingStage
        from .stages.gt_axial_coding import GTAxialCodingStage
        from .stages.gt_selective_coding import GTSelectiveCodingStage
        from .stages.gt_theory_integration import GTTheoryIntegrationStage

        stages = [
            IngestStage(),
            GTOpenCodingStage(pause_for_review=enable_human_review),
            GTAxialCodingStage(pause_for_review=enable_human_review),
            GTSelectiveCodingStage(),
            GTTheoryIntegrationStage(),
            CrossInterviewStage(),  # only runs if corpus > 1 doc
        ]
    else:
        # Default / thematic analysis pipeline
        stages = [
            IngestStage(),
            ThematicCodingStage(pause_for_review=enable_human_review),
            PerspectiveStage(),
            RelationshipStage(),
            SynthesisStage(),
            CrossInterviewStage(),  # only runs if corpus > 1 doc
        ]

    logger.info(
        "Created %s pipeline with %d stages (human_review=%s)",
        methodology, len(stages), enable_human_review,
    )
    return AnalysisPipeline(stages=stages, on_stage_complete=on_stage_complete)
