"""Tests for the first-class analytic claim ledger (INV-9)."""

from qc_clean.core.claims import summarize_claim_ledger
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
    Document,
    ProjectState,
    Provenance,
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
