"""INV-6 regression: disconfirmation must cover the final claim set.

Negative-case analysis runs last in every pipeline (verified in
test_pipeline_engine) and must challenge the cross-interview claims, not only the
codebook. These tests lock in the plumbing that surfaces the cross-interview
``cross_case`` memo to the disconfirmation prompt.
"""

from qc_clean.core.claims import claims_for_negative_cases
from qc_clean.core.pipeline.stages.negative_case import (
    NegativeCase,
    _format_cross_interview_claims,
)
from qc_clean.schemas.domain import (
    AnalyticClaim,
    AnalysisMemo,
    ClaimKind,
    ClaimScope,
    ClaimSupportStatus,
    Code,
    Codebook,
    Corpus,
    Document,
    Methodology,
    ProjectConfig,
    ProjectState,
)


def _state(**kwargs) -> ProjectState:
    defaults = dict(
        name="t",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d1.txt", content="content")]),
    )
    defaults.update(kwargs)
    return ProjectState(**defaults)


def test_no_cross_interview_memo_returns_empty():
    # Single-doc corpora never run cross-interview; disconfirmation should not
    # invent a section.
    state = _state()
    assert _format_cross_interview_claims(state) == ""


def test_returns_cross_case_memo_content():
    state = _state(memos=[
        AnalysisMemo(memo_type="coding", title="x", content="not this"),
        AnalysisMemo(
            memo_type="cross_case",
            title="Cross-Interview Pattern Analysis",
            content="Consensus: trust matters. Divergent: autonomy.",
        ),
    ])
    out = _format_cross_interview_claims(state)
    assert "Consensus: trust matters" in out
    assert "not this" not in out


def test_returns_latest_cross_case_memo():
    state = _state(memos=[
        AnalysisMemo(memo_type="cross_case", title="x", content="OLD"),
        AnalysisMemo(memo_type="cross_case", title="x", content="NEW"),
    ])
    assert _format_cross_interview_claims(state) == "NEW"


def test_negative_case_claim_links_challenged_cross_case_claim_and_contrary_anchor():
    state = _state(
        corpus=Corpus(documents=[
            Document(id="d1", name="d1.txt", content="Alex abandoned AI after errors.")
        ]),
        codebook=Codebook(codes=[Code(id="C1", name="AI Adoption")]),
        claims=[
            AnalyticClaim(
                id="claim-cross-ai",
                claim_kind=ClaimKind.CROSS_CASE,
                source_stage="cross_interview",
                claim_text="AI Adoption is present across interviews.",
                scope=ClaimScope(corpus_level=True, code_ids=["C1"]),
                origin_object_type="cross_interview_consensus",
                origin_object_id="consensus:C1",
                support_status=ClaimSupportStatus.SUPPORTED,
            ),
            AnalyticClaim(
                id="claim-other",
                claim_kind=ClaimKind.CROSS_CASE,
                source_stage="cross_interview",
                claim_text="Another theme is present.",
                scope=ClaimScope(corpus_level=True, code_ids=["C2"]),
                origin_object_type="cross_interview_consensus",
                origin_object_id="consensus:C2",
                support_status=ClaimSupportStatus.SUPPORTED,
            ),
        ],
    )
    negative_case = NegativeCase(
        code_name="AI Adoption",
        disconfirming_evidence="abandoned AI after errors",
        explanation="This challenges a simple cross-case adoption claim.",
        implication="Adoption needs a failure boundary condition.",
    )

    claims = claims_for_negative_cases(state, [negative_case])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_kind == ClaimKind.NEGATIVE_CASE
    assert claim.scope.code_ids == ["C1"]
    assert claim.scope.claim_ids == ["claim-cross-ai"]
    assert claim.support_status == ClaimSupportStatus.SUPPORTED
    assert claim.contrary_anchors[0].doc_id == "d1"
