"""INV-11 regression: incremental recode must invalidate stale higher-order outputs.

`project recode` does not recompute perspective/entities/synthesis/GT outputs.
When the corpus changes, those become stale; the system must invalidate them
rather than silently retain them as if current. These tests cover the detector
and invalidator.
"""

from qc_clean.core.pipeline.stages.incremental_coding import (
    invalidate_stale_higher_order_outputs,
    _stale_higher_order_outputs,
)
from qc_clean.schemas.domain import (
    AnalyticClaim,
    AnalysisPhaseResult,
    ClaimKind,
    ClaimScope,
    CodeRelationship,
    Corpus,
    CoreCategoryResult,
    DomainEntityRelationship,
    Document,
    Entity,
    Methodology,
    PerspectiveAnalysis,
    PipelineStatus,
    ProjectConfig,
    ProjectState,
    HumanReviewDecision,
    ReviewAction,
    Synthesis,
    TheoreticalModelResult,
)


def _state(**kwargs) -> ProjectState:
    defaults = dict(
        name="t",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d1.txt", content="content")]),
    )
    defaults.update(kwargs)
    return ProjectState(**defaults)


def test_no_higher_order_outputs_returns_empty():
    assert _stale_higher_order_outputs(_state()) == []


def test_detects_populated_outputs():
    state = _state(
        synthesis=Synthesis(executive_summary="s"),
        perspective_analysis=PerspectiveAnalysis(),
        code_relationships=[CodeRelationship(source_code_id="c1", target_code_id="c2")],
        entities=[Entity(name="X")],
        entity_relationships=[
            DomainEntityRelationship(
                entity_1_id="e1",
                entity_2_id="e2",
                relationship_type="influences",
            )
        ],
        core_categories=[CoreCategoryResult(category_name="C")],
        theoretical_model=TheoreticalModelResult(
            model_name="M",
            propositions=["P"],
        ),
    )
    stale = _stale_higher_order_outputs(state)
    assert "synthesis" in stale
    assert "perspective_analysis" in stale
    assert "code_relationships" in stale
    assert "entities" in stale
    assert "entity_relationships" in stale
    assert "core_categories" in stale
    assert "theoretical_model" in stale


def test_empty_collections_not_flagged():
    # An empty entities list is not a stale output.
    state = _state(entities=[], core_categories=[])
    assert _stale_higher_order_outputs(state) == []


def test_invalidate_stale_higher_order_outputs_clears_outputs_phase_results_and_claims():
    state = _state(
        synthesis=Synthesis(executive_summary="stale"),
        perspective_analysis=PerspectiveAnalysis(),
        code_relationships=[CodeRelationship(source_code_id="c1", target_code_id="c2")],
        entities=[Entity(id="e1", name="Entity")],
        entity_relationships=[
            DomainEntityRelationship(
                entity_1_id="e1",
                entity_2_id="e2",
                relationship_type="influences",
            )
        ],
        core_categories=[CoreCategoryResult(category_name="Core")],
        theoretical_model=TheoreticalModelResult(
            model_name="Theory",
            propositions=["P"],
        ),
        claims=[
            _claim("synthesis", ClaimKind.SYNTHESIS_FINDING),
            _claim("perspective", ClaimKind.PERSPECTIVE),
            _claim("relationship", ClaimKind.RELATIONSHIP),
            _claim("gt_axial_coding", ClaimKind.RELATIONSHIP),
            _claim("gt_selective_coding", ClaimKind.GT_CATEGORY),
            _claim("gt_theory_integration", ClaimKind.GT_PROPOSITION),
            _claim("thematic_coding", ClaimKind.CODE),
            _claim("cross_interview", ClaimKind.CROSS_CASE),
            _claim("negative_case_analysis", ClaimKind.NEGATIVE_CASE),
        ],
        phase_results=[
            AnalysisPhaseResult(phase_name="synthesis", status=PipelineStatus.COMPLETED),
            AnalysisPhaseResult(phase_name="relationship", status=PipelineStatus.COMPLETED),
            AnalysisPhaseResult(phase_name="gt_selective_coding", status=PipelineStatus.COMPLETED),
            AnalysisPhaseResult(phase_name="thematic_coding", status=PipelineStatus.COMPLETED),
            AnalysisPhaseResult(phase_name="cross_interview", status=PipelineStatus.COMPLETED),
        ],
    )

    invalidated = invalidate_stale_higher_order_outputs(state)

    assert set(invalidated) == {
        "synthesis",
        "perspective_analysis",
        "code_relationships",
        "entities",
        "entity_relationships",
        "core_categories",
        "theoretical_model",
    }
    assert state.synthesis is None
    assert state.perspective_analysis is None
    assert state.code_relationships == []
    assert state.entities == []
    assert state.entity_relationships == []
    assert state.core_categories == []
    assert state.theoretical_model is None
    assert {claim.source_stage for claim in state.claims} == {
        "thematic_coding",
        "cross_interview",
        "negative_case_analysis",
    }
    assert [result.phase_name for result in state.phase_results] == [
        "thematic_coding",
        "cross_interview",
    ]


def test_invalidate_marks_review_decisions_for_removed_claims_inactive():
    state = _state(
        synthesis=Synthesis(executive_summary="stale"),
        claims=[
            _claim("synthesis", ClaimKind.SYNTHESIS_FINDING, claim_id="claim-stale"),
            _claim("thematic_coding", ClaimKind.CODE, claim_id="claim-current"),
        ],
        review_decisions=[
            HumanReviewDecision(
                target_type="claim",
                target_id="claim-stale",
                action=ReviewAction.APPROVE,
            ),
            HumanReviewDecision(
                target_type="claim",
                target_id="claim-current",
                action=ReviewAction.APPROVE,
            ),
            HumanReviewDecision(
                target_type="code",
                target_id="C1",
                action=ReviewAction.APPROVE,
            ),
        ],
    )

    invalidate_stale_higher_order_outputs(state)

    stale_decision = state.review_decisions[0]
    current_claim_decision = state.review_decisions[1]
    code_decision = state.review_decisions[2]
    assert stale_decision.is_active is False
    assert stale_decision.inactive_at is not None
    assert "claim invalidated by incremental recode" in stale_decision.inactive_reason
    assert current_claim_decision.is_active is True
    assert current_claim_decision.inactive_reason == ""
    assert current_claim_decision.inactive_at is None
    assert code_decision.is_active is True
    assert code_decision.inactive_reason == ""


def test_markdown_export_surfaces_data_warnings(tmp_path):
    """data_warnings must be rendered in the Markdown report (INV-11)."""
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _state(
        data_warnings=["Incremental recode ... invalidated: synthesis."],
    )
    out = tmp_path / "report.md"
    ProjectExporter().export_markdown(state, str(out))
    text = out.read_text()
    assert "Data warnings" in text
    assert "invalidated: synthesis" in text


def _claim(source_stage: str, kind: ClaimKind, *, claim_id: str | None = None) -> AnalyticClaim:
    return AnalyticClaim(
        id=claim_id or f"claim-{source_stage}",
        claim_kind=kind,
        source_stage=source_stage,
        claim_text=f"{source_stage} claim",
        scope=ClaimScope(corpus_level=True),
        origin_object_type="fixture",
        origin_object_id=source_stage,
    )
