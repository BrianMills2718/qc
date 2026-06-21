"""INV-4 tests for category-level saturation diagnostics."""

from qc_clean.core.pipeline.saturation import assess_category_saturation
from qc_clean.schemas.domain import (
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    ProjectState,
)


def test_category_saturation_flags_underdeveloped_categories():
    state = ProjectState(
        codebook=Codebook(codes=[
            Code(id="TRUST", name="Trust", description="Trust in the system"),
        ]),
    )

    summary = assess_category_saturation(state)

    assert summary.status == "diagnostic"
    assert summary.all_categories_adequate is False
    assert summary.underdeveloped_count == 1
    category = summary.categories[0]
    assert category.code_id == "TRUST"
    assert category.status == "underdeveloped"
    assert category.property_count == 0
    assert category.dimension_count == 0
    assert category.supporting_application_count == 0
    assert category.supporting_document_count == 0
    assert category.gaps == [
        "needs_properties",
        "needs_dimensions",
        "needs_supporting_applications",
        "needs_supporting_documents",
    ]
    assert "diagnostic only" in summary.note


def test_category_saturation_marks_adequate_categories_without_claiming_gt_saturation():
    doc = Document(id="d1", name="interview.txt", content="Trust varied by context.")
    state = ProjectState(
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[
            Code(
                id="TRUST",
                name="Trust",
                description="Trust in the system",
                properties=["institutional trust"],
                dimensions=["low-to-high"],
            ),
        ]),
        code_applications=[
            CodeApplication(
                code_id="TRUST",
                doc_id=doc.id,
                quote_text="Trust varied by context.",
            ),
        ],
    )

    summary = assess_category_saturation(state)

    assert summary.status == "diagnostic"
    assert summary.all_categories_adequate is True
    assert summary.adequate_count == 1
    assert summary.underdeveloped_count == 0
    assert summary.categories[0].status == "adequate"
    assert summary.categories[0].gaps == []
    assert "not proof of grounded-theory saturation" in summary.note
