"""Tests for the first-class analytic claim ledger (INV-9)."""

from qc_clean.core.claims import (
    claims_for_code_applications,
    claims_for_codes,
    claims_for_cross_interview,
    claims_for_gt_categories,
    claims_for_gt_theory,
    claims_for_negative_cases,
    claims_for_perspectives,
    claims_for_relationships,
    claims_for_synthesis,
    disconfirmation_targets,
    summarize_disconfirmation_coverage,
    summarize_claim_ledger,
)
from qc_clean.core.pipeline.stages.cross_interview import analyze_cross_interview_patterns
from qc_clean.core.pipeline.stages.negative_case import NegativeCase
from qc_clean.schemas.domain import (
    ClaimAdjudicationStatus,
    ClaimAnchor,
    ClaimKind,
    ClaimRevision,
    ClaimScope,
    ClaimSupportStatus,
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    CoreCategoryResult,
    Document,
    DomainEntityRelationship,
    Entity,
    ParticipantPerspective,
    PerspectiveAnalysis,
    ProjectState,
    Provenance,
    Recommendation,
    Synthesis,
    TheoreticalModelResult,
    AnalyticClaim,
)


def test_claim_models_round_trip_with_empty_ledger():
    """Existing/minimal project states carry an empty claim ledger."""
    state = ProjectState(name="study")

    assert state.claims == []

    loaded = ProjectState.model_validate_json(state.model_dump_json())
    assert loaded.claims == []


def test_claim_with_supporting_anchor_round_trips():
    """A supported claim can cite an anchored source span."""
    doc = Document(id="d1", name="d.txt", content="Alex: AI saved time.")
    app = CodeApplication(
        id="a1",
        code_id="C1",
        doc_id=doc.id,
        quote_text="AI saved time",
        start_char=6,
        end_char=19,
        quote_hash="hash1",
        applied_by=Provenance.LLM,
    )
    claim = AnalyticClaim(
        claim_kind=ClaimKind.CODE_APPLICATION,
        source_stage="thematic_coding",
        claim_text="The passage says AI saved time.",
        scope=ClaimScope(doc_ids=[doc.id], code_ids=["C1"]),
        origin_object_type="code_application",
        origin_object_id=app.id,
        supporting_anchors=[
            ClaimAnchor(
                doc_id=doc.id,
                start_char=app.start_char,
                end_char=app.end_char,
                quote_text=app.quote_text,
                quote_hash=app.quote_hash,
                code_application_id=app.id,
            )
        ],
        support_status=ClaimSupportStatus.SUPPORTED,
    )

    state = ProjectState(
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[Code(id="C1", name="Efficiency")]),
        code_applications=[app],
        claims=[claim],
    )

    loaded = ProjectState.model_validate_json(state.model_dump_json())
    loaded_claim = loaded.claims[0]
    assert loaded_claim.claim_kind == ClaimKind.CODE_APPLICATION
    assert loaded_claim.support_status == ClaimSupportStatus.SUPPORTED
    assert loaded_claim.supporting_anchors[0].doc_id == "d1"
    assert loaded_claim.supporting_anchors[0].start_char == 6
    assert loaded_claim.supporting_anchors[0].quote_hash == "hash1"


def test_unanchored_claim_is_visible_not_silently_supported():
    """Claims without anchors must explicitly expose the support gap."""
    claim = AnalyticClaim(
        claim_kind=ClaimKind.SYNTHESIS_FINDING,
        source_stage="synthesis",
        claim_text="Participants generally trust the tool.",
        scope=ClaimScope(corpus_level=True),
        origin_object_type="synthesis",
        origin_object_id="s1",
        support_status=ClaimSupportStatus.NEEDS_ANCHOR,
    )

    assert claim.supporting_anchors == []
    assert claim.support_status == ClaimSupportStatus.NEEDS_ANCHOR


def test_revision_history_records_actor_action_and_text_change():
    """Claim revisions preserve the human/agent action history."""
    revision = ClaimRevision(
        actor=Provenance.HUMAN,
        action="revise",
        rationale="Narrowed to the document actually cited.",
        previous_claim_text="All participants trust the tool.",
        new_claim_text="Alex trusts the tool.",
    )
    claim = AnalyticClaim(
        claim_kind=ClaimKind.PERSPECTIVE,
        source_stage="perspective",
        claim_text="Alex trusts the tool.",
        scope=ClaimScope(participant_names=["Alex"]),
        origin_object_type="participant_perspective",
        origin_object_id="Alex",
        adjudication_status=ClaimAdjudicationStatus.REVISED,
        revision_history=[revision],
    )

    loaded = AnalyticClaim.model_validate_json(claim.model_dump_json())
    assert loaded.adjudication_status == ClaimAdjudicationStatus.REVISED
    assert loaded.revision_history[0].actor == Provenance.HUMAN
    assert loaded.revision_history[0].previous_claim_text == "All participants trust the tool."
    assert loaded.revision_history[0].new_claim_text == "Alex trusts the tool."


def test_claim_summary_counts_by_kind_stage_status_and_support():
    """Agent-facing summaries are deterministic and compact."""
    state = ProjectState(
        claims=[
            AnalyticClaim(
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="Efficiency is a code.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="code",
                origin_object_id="C1",
                support_status=ClaimSupportStatus.SUPPORTED,
            ),
            AnalyticClaim(
                claim_kind=ClaimKind.SYNTHESIS_FINDING,
                source_stage="synthesis",
                claim_text="Trust is a cross-cutting finding.",
                scope=ClaimScope(corpus_level=True),
                origin_object_type="synthesis",
                origin_object_id="finding:0",
                support_status=ClaimSupportStatus.NEEDS_ANCHOR,
                adjudication_status=ClaimAdjudicationStatus.NEEDS_REVIEW,
            ),
        ]
    )

    summary = summarize_claim_ledger(state)
    assert summary == {
        "total_claims": 2,
        "by_kind": {"code": 1, "synthesis_finding": 1},
        "by_stage": {"synthesis": 1, "thematic_coding": 1},
        "by_adjudication_status": {"needs_review": 1, "pending": 1},
        "by_support_status": {"needs_anchor": 1, "supported": 1},
        "unsupported_or_needing_anchor": 1,
    }


def test_disconfirmation_targets_exclude_negative_and_no_claim_events():
    """Only live substantive claims become disconfirmation targets."""
    state = ProjectState(claims=[
        AnalyticClaim(
            id="claim-code",
            claim_kind=ClaimKind.CODE,
            source_stage="thematic_coding",
            claim_text="Efficiency is a code.",
            scope=ClaimScope(code_ids=["C1"]),
            origin_object_type="code",
            origin_object_id="C1",
        ),
        AnalyticClaim(
            id="claim-negative",
            claim_kind=ClaimKind.NEGATIVE_CASE,
            source_stage="negative_case_analysis",
            claim_text="Negative case for Efficiency.",
            scope=ClaimScope(claim_ids=["claim-code"], code_ids=["C1"]),
            origin_object_type="negative_case",
            origin_object_id="negative_case:0:Efficiency",
        ),
        AnalyticClaim(
            id="claim-none",
            claim_kind=ClaimKind.NO_CLAIMS_EVENT,
            source_stage="relationship",
            claim_text="No analytic claims emitted.",
            scope=ClaimScope(corpus_level=True),
            origin_object_type="stage",
            origin_object_id="relationship",
        ),
        AnalyticClaim(
            id="claim-withdrawn",
            claim_kind=ClaimKind.SYNTHESIS_FINDING,
            source_stage="synthesis",
            claim_text="Withdrawn finding.",
            scope=ClaimScope(corpus_level=True),
            origin_object_type="synthesis",
            origin_object_id="finding:0",
            adjudication_status=ClaimAdjudicationStatus.WITHDRAWN,
        ),
    ])

    targets = disconfirmation_targets(state)

    assert [claim.id for claim in targets] == ["claim-code"]


def test_disconfirmation_coverage_counts_challenged_claim_ids():
    """Coverage summaries count exact claim IDs challenged by negative cases."""
    state = ProjectState(claims=[
        AnalyticClaim(
            id="claim-code",
            claim_kind=ClaimKind.CODE,
            source_stage="thematic_coding",
            claim_text="Efficiency is a code.",
            scope=ClaimScope(code_ids=["C1"]),
            origin_object_type="code",
            origin_object_id="C1",
        ),
        AnalyticClaim(
            id="claim-synthesis",
            claim_kind=ClaimKind.SYNTHESIS_FINDING,
            source_stage="synthesis",
            claim_text="Efficiency improves workflow.",
            scope=ClaimScope(corpus_level=True, code_ids=["C1"]),
            origin_object_type="synthesis",
            origin_object_id="finding:0",
        ),
        AnalyticClaim(
            id="claim-negative",
            claim_kind=ClaimKind.NEGATIVE_CASE,
            source_stage="negative_case_analysis",
            claim_text="Negative case for Efficiency.",
            scope=ClaimScope(claim_ids=["claim-code"], code_ids=["C1"]),
            origin_object_type="negative_case",
            origin_object_id="negative_case:0:Efficiency",
        ),
    ])

    summary = summarize_disconfirmation_coverage(state)

    assert summary == {
        "total_targets": 2,
        "challenged_targets": 1,
        "unchallenged_targets": 1,
        "challenged_rate": 0.5,
        "challenged_claim_ids": ["claim-code"],
        "unchallenged_claim_ids": ["claim-synthesis"],
        "negative_case_claims": 1,
    }


def test_code_and_application_builders_include_supporting_anchors():
    """Code and application builders preserve anchored evidence."""
    doc = Document(id="d1", name="d.txt", content="Alex: AI saved time.")
    app = CodeApplication(
        id="a1",
        code_id="C1",
        doc_id=doc.id,
        quote_text="AI saved time",
        start_char=6,
        end_char=19,
        quote_hash="hash1",
    )
    state = ProjectState(
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[Code(id="C1", name="Efficiency", description="Time savings")]),
        code_applications=[app],
    )

    code_claims = claims_for_codes(state)
    app_claims = claims_for_code_applications(state)

    assert len(code_claims) == 1
    assert code_claims[0].claim_kind == ClaimKind.CODE
    assert code_claims[0].support_status == ClaimSupportStatus.SUPPORTED
    assert code_claims[0].supporting_anchors[0].code_application_id == "a1"

    assert len(app_claims) == 1
    assert app_claims[0].claim_kind == ClaimKind.CODE_APPLICATION
    assert app_claims[0].origin_object_id == "a1"
    assert app_claims[0].supporting_anchors[0].start_char == 6


def test_higher_order_builders_mark_unanchored_claims_as_needing_anchors():
    """Perspective, relationship, and synthesis prose starts visibly unanchored."""
    state = ProjectState(
        perspective_analysis=PerspectiveAnalysis(
            participants=[
                ParticipantPerspective(
                    name="Alex",
                    perspective_summary="Alex sees AI as a time saver.",
                    codes_emphasized=["C1"],
                )
            ],
            consensus_themes=["AI is useful"],
            divergent_viewpoints=["Privacy concerns remain"],
        ),
        entities=[Entity(id="e1", name="AI"), Entity(id="e2", name="Workflow")],
        entity_relationships=[
            DomainEntityRelationship(
                id="r1",
                entity_1_id="e1",
                entity_2_id="e2",
                relationship_type="changes",
                supporting_evidence=["AI changed workflow"],
            )
        ],
        synthesis=Synthesis(
            key_findings=["AI saves time."],
            cross_cutting_patterns=["Efficiency and privacy are linked."],
            recommendations=[Recommendation(title="Train staff", supporting_themes=["C1"])],
            confidence_assessment={"AI saves time": {"level": "high", "score": 0.8}},
        ),
    )

    claims = (
        claims_for_perspectives(state)
        + claims_for_relationships(state)
        + claims_for_synthesis(state)
    )

    assert {claim.claim_kind for claim in claims} == {
        ClaimKind.PERSPECTIVE,
        ClaimKind.RELATIONSHIP,
        ClaimKind.SYNTHESIS_FINDING,
    }
    assert all(claim.support_status == ClaimSupportStatus.NEEDS_ANCHOR for claim in claims)
    assert any(claim.scope.participant_names == ["Alex"] for claim in claims)
    assert any(claim.scope.entity_ids == ["e1", "e2"] for claim in claims)
    assert any(claim.scope.code_ids == ["C1"] for claim in claims)


def test_cross_case_builder_uses_code_application_support():
    """Cross-case claims inherit support from code applications for their code."""
    docs = [
        Document(id="d1", name="a.txt", content="AI helps."),
        Document(id="d2", name="b.txt", content="AI helps again."),
    ]
    apps = [
        CodeApplication(
            id="a1",
            code_id="C1",
            doc_id="d1",
            quote_text="AI helps",
            start_char=0,
            end_char=8,
            quote_hash="h1",
        ),
        CodeApplication(
            id="a2",
            code_id="C1",
            doc_id="d2",
            quote_text="AI helps again",
            start_char=0,
            end_char=14,
            quote_hash="h2",
        ),
    ]
    state = ProjectState(
        corpus=Corpus(documents=docs),
        codebook=Codebook(codes=[Code(id="C1", name="AI Use")]),
        code_applications=apps,
    )
    results = analyze_cross_interview_patterns(state)

    claims = claims_for_cross_interview(state, results)

    assert len(claims) >= 1
    consensus = [claim for claim in claims if "present in 2/2 documents" in claim.claim_text]
    assert consensus
    assert consensus[0].claim_kind == ClaimKind.CROSS_CASE
    assert consensus[0].support_status == ClaimSupportStatus.SUPPORTED
    assert {a.code_application_id for a in consensus[0].supporting_anchors} == {"a1", "a2"}


def test_gt_builders_emit_category_and_proposition_claims():
    """GT domain results become first-class claim objects."""
    state = ProjectState(
        core_categories=[
            CoreCategoryResult(
                category_name="Managed adoption",
                definition="AI adoption is staged and managed.",
                related_categories=["Training"],
            )
        ],
        theoretical_model=TheoreticalModelResult(
            model_name="Adoption model",
            propositions=["If training is strong, adoption resistance falls."],
            scope_conditions=["Workplace AI implementation"],
            implications=["Invest in training"],
        ),
    )

    claims = claims_for_gt_categories(state) + claims_for_gt_theory(state)

    assert [claim.claim_kind for claim in claims].count(ClaimKind.GT_CATEGORY) == 1
    assert [claim.claim_kind for claim in claims].count(ClaimKind.GT_PROPOSITION) == 3
    assert all(claim.support_status == ClaimSupportStatus.NEEDS_ANCHOR for claim in claims)
    assert any("If training is strong" in claim.claim_text for claim in claims)


def test_negative_case_builder_resolves_unique_contrary_anchor():
    """Negative cases become claims with contrary anchors when evidence resolves."""
    doc = Document(id="d1", name="d.txt", content="Alex abandoned AI after errors.")
    state = ProjectState(
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[Code(id="C1", name="AI Adoption")]),
    )
    negative = NegativeCase(
        code_name="AI Adoption",
        disconfirming_evidence="abandoned AI after errors",
        explanation="This challenges a simple adoption narrative.",
        implication="Adoption has failure cases.",
    )

    claims = claims_for_negative_cases(state, [negative])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_kind == ClaimKind.NEGATIVE_CASE
    assert claim.scope.code_ids == ["C1"]
    assert claim.support_status == ClaimSupportStatus.SUPPORTED
    assert len(claim.contrary_anchors) == 1
    assert claim.contrary_anchors[0].doc_id == "d1"
    assert claim.contrary_anchors[0].quote_text == "abandoned AI after errors"
