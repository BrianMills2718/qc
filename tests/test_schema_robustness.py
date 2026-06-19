"""Regression tests for LLM-output schema robustness.

LLMs do not reliably populate every schema field even under JSON mode (see the
"Design Lessons" in CLAUDE.md). Every List/Dict field on an LLM-facing schema
must therefore carry a ``default_factory`` so an omitted field validates to an
empty collection instead of raising. These tests feed each schema the minimal
set of *required scalar* fields with all collection fields omitted, and assert
the collections default safely. A regression that drops a ``default_factory``
would otherwise pass the entire mocked unit suite and only surface in live E2E.
"""

import pytest

from qc_clean.schemas.analysis_schemas import (
    AnalysisSynthesis,
    CodeHierarchy,
    EntityMapping,
    SpeakerAnalysis,
    ThematicCode,
)
from qc_clean.schemas.gt_schemas import (
    AxialRelationship,
    CoreCategory,
    OpenCode,
    TheoreticalModel,
)
from qc_clean.core.pipeline.stages.negative_case import NegativeCaseResponse


def test_open_code_collections_default_when_omitted():
    code = OpenCode.model_validate(
        {"code_name": "trust", "description": "d", "frequency": 3, "confidence": 0.5}
    )
    assert code.properties == []
    assert code.dimensions == []
    assert code.supporting_quotes == []
    assert code.child_codes == []


def test_axial_relationship_collections_default_when_omitted():
    rel = AxialRelationship.model_validate(
        {
            "central_category": "a",
            "related_category": "b",
            "relationship_type": "causal",
            "strength": 0.7,
        }
    )
    assert rel.conditions == []
    assert rel.consequences == []
    assert rel.supporting_evidence == []


def test_core_category_collections_default_when_omitted():
    cat = CoreCategory.model_validate(
        {
            "category_name": "n",
            "definition": "d",
            "central_phenomenon": "p",
            "explanatory_power": "e",
            "integration_rationale": "r",
        }
    )
    assert cat.related_categories == []
    assert cat.theoretical_properties == []


def test_theoretical_model_collections_default_and_core_category_property():
    model = TheoreticalModel.model_validate(
        {"model_name": "m", "theoretical_framework": "f"}
    )
    assert model.core_categories == []
    assert model.propositions == []
    # Backward-compat accessor must not raise on the empty list.
    assert model.core_category == ""


def test_thematic_code_example_quotes_default_when_omitted():
    code = ThematicCode.model_validate(
        {
            "id": "TRUST",
            "name": "Trust",
            "description": "d",
            "semantic_definition": "s",
            "level": 0,
            "mention_count": 2,
            "discovery_confidence": 0.5,
        }
    )
    assert code.example_quotes == []


def test_code_hierarchy_codes_default_when_omitted():
    hierarchy = CodeHierarchy.model_validate(
        {"total_codes": 0, "analysis_confidence": 0.5}
    )
    assert hierarchy.codes == []


def test_speaker_analysis_collections_default_when_omitted():
    analysis = SpeakerAnalysis.model_validate({})
    assert analysis.participants == []
    assert analysis.consensus_themes == []
    assert analysis.divergent_viewpoints == []
    assert analysis.perspective_mapping == []


def test_entity_mapping_collections_default_when_omitted():
    mapping = EntityMapping.model_validate({})
    assert mapping.entities == []
    assert mapping.relationships == []
    assert mapping.cause_effect_chains == []


def test_analysis_synthesis_collections_default_when_omitted():
    synthesis = AnalysisSynthesis.model_validate({"executive_summary": "summary"})
    assert synthesis.key_findings == []
    assert synthesis.actionable_recommendations == []
    assert synthesis.confidence_assessment == []


def test_negative_case_response_collections_default_when_omitted():
    response = NegativeCaseResponse.model_validate({"overall_assessment": "none found"})
    assert response.negative_cases == []


@pytest.mark.parametrize(
    "model_cls, kwargs, list_fields",
    [
        (OpenCode, {"code_name": "c", "description": "d", "frequency": 1, "confidence": 0.5},
         ["properties", "dimensions", "supporting_quotes", "child_codes"]),
        (TheoreticalModel, {"model_name": "m", "theoretical_framework": "f"},
         ["core_categories", "propositions", "conceptual_relationships"]),
    ],
)
def test_omitted_list_fields_are_independent_instances(model_cls, kwargs, list_fields):
    """default_factory (not a shared mutable default) must give each instance its own list."""
    a = model_cls.model_validate(dict(kwargs))
    b = model_cls.model_validate(dict(kwargs))
    for field in list_fields:
        getattr(a, field).append("x")
        assert getattr(b, field) == [], f"{model_cls.__name__}.{field} shares a mutable default"
