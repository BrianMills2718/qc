"""Tests for importing adjudication responses into D3/D7 gold packages."""

import json

import pytest

from qc_clean.core.adjudication_import import (
    build_adjudication_gold_import,
    write_adjudication_gold_import,
)
from qc_clean.core.adjudication_sample import build_adjudication_sample_package
from qc_clean.core.d3_gold import validate_d3_gold_set_payload
from qc_clean.core.d7_gold import validate_d7_gold_set_payload
from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimAnchor,
    ClaimKind,
    ClaimScope,
    Code,
    CodeApplication,
    CodeRelationship,
    Codebook,
    Corpus,
    Document,
    DomainEntityRelationship,
    Entity,
    ProjectState,
)


def test_imports_valid_responses_to_d3_and_d7_gold_packages(tmp_path):
    payload = _completed_response_payload()

    result = build_adjudication_gold_import(
        payload,
        gold_set_id="adj-import-v1",
        dataset_name="Adjudication Import Fixture",
        split="dev",
        coder_count=1,
        adjudicator="coder-1",
        protocol="Single reviewed response package fixture.",
        include_d3=True,
        include_d7=True,
    )
    d3_payload = result.d3_gold_package.model_dump(mode="json")
    d7_payload = result.d7_gold_package.model_dump(mode="json")

    validate_d3_gold_set_payload(d3_payload)
    validate_d7_gold_set_payload(d7_payload)
    assert result.report.status == "complete"
    assert result.report.valid_d3_anchor_count == 1
    assert result.report.valid_d7_anchor_count == 1
    assert result.report.excluded_response_count == 3
    assert d3_payload["application_gold"] == [
        {
            "code_id": "C1",
            "doc_id": "d1",
            "start_char": 11,
            "end_char": 27,
            "segment_id": None,
            "quote_text": "autonomy matters",
        }
    ]
    assert d7_payload["contrary_evidence"] == [
        {
            "target_claim_id": "claim-1",
            "doc_id": "d1",
            "start_char": 11,
            "end_char": 27,
            "segment_id": None,
            "quote_text": "autonomy matters",
        }
    ]
    assert "not methodological validity evidence" in result.report.caution

    d3_out = tmp_path / "d3_gold.json"
    d7_out = tmp_path / "d7_gold.json"
    outputs = write_adjudication_gold_import(result, d3_output=d3_out, d7_output=d7_out)

    assert outputs == {"d3_output": str(d3_out), "d7_output": str(d7_out)}
    assert validate_d3_gold_set_payload(json.loads(d3_out.read_text(encoding="utf-8")))
    assert validate_d7_gold_set_payload(json.loads(d7_out.read_text(encoding="utf-8")))


def test_import_rejects_invalid_response_package():
    payload = _completed_response_payload()
    payload["items"][0].pop("response")

    with pytest.raises(ValueError, match="response package is invalid"):
        build_adjudication_gold_import(
            payload,
            gold_set_id="adj-import-v1",
            dataset_name="Adjudication Import Fixture",
            split="dev",
            coder_count=1,
            adjudicator="coder-1",
            protocol="Single reviewed response package fixture.",
            include_d3=True,
            include_d7=True,
        )


def test_import_fails_requested_output_with_no_valid_anchors():
    payload = _completed_response_payload()
    for item in payload["items"]:
        if item["target_type"] == "code_application":
            item["response"]["validity"] = "invalid"
            item["response"]["rationale"] = "Rejected by adjudicator."

    with pytest.raises(ValueError, match="No valid D3 code-application responses"):
        build_adjudication_gold_import(
            payload,
            gold_set_id="adj-import-v1",
            dataset_name="Adjudication Import Fixture",
            split="dev",
            coder_count=1,
            adjudicator="coder-1",
            protocol="Single reviewed response package fixture.",
            include_d3=True,
            include_d7=False,
        )


def test_import_adjudication_responses_script_writes_outputs(tmp_path, capsys):
    from scripts import import_adjudication_responses

    response_path = tmp_path / "responses.json"
    response_path.write_text(json.dumps(_completed_response_payload()), encoding="utf-8")
    d3_out = tmp_path / "d3_gold.json"
    d7_out = tmp_path / "d7_gold.json"

    exit_code = import_adjudication_responses.main(
        [
            str(response_path),
            "--output-d3",
            str(d3_out),
            "--output-d7",
            str(d7_out),
            "--gold-set-id",
            "adj-import-v1",
            "--dataset-name",
            "Adjudication Import Fixture",
            "--split",
            "dev",
            "--coder-count",
            "1",
            "--adjudicator",
            "coder-1",
            "--protocol",
            "Single reviewed response package fixture.",
        ]
    )
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert report["status"] == "complete"
    assert report["d3_output"] == str(d3_out)
    assert report["d7_output"] == str(d7_out)
    assert validate_d3_gold_set_payload(json.loads(d3_out.read_text(encoding="utf-8")))
    assert validate_d7_gold_set_payload(json.loads(d7_out.read_text(encoding="utf-8")))


def _completed_response_payload() -> dict:
    package = build_adjudication_sample_package(
        _import_state(),
        limit_per_type=10,
        context_chars=8,
    ).model_dump(mode="json")
    labels_by_type = {
        "code_application": "valid",
        "claim": "unclear",
        "negative_case": "valid",
        "code_relationship": "invalid",
        "entity_relationship": "invalid",
    }
    for item in package["items"]:
        validity = labels_by_type[item["target_type"]]
        item["response"] = {
            "validity": validity,
            "rationale": "Reviewed by coder.",
            "corrected_value": None,
            "adjudicator_id": "coder-1",
        }
    return package


def _import_state() -> ProjectState:
    text = "Alice says autonomy matters for scheduling. Bob disagrees later."
    start = text.index("autonomy matters")
    end = start + len("autonomy matters")
    anchor = ClaimAnchor(
        doc_id="d1",
        start_char=start,
        end_char=end,
        quote_text="autonomy matters",
        quote_hash="a" * 64,
        code_application_id="A1",
    )
    return ProjectState(
        id="adj-import-proj",
        name="Adjudication Import Project",
        corpus=Corpus(documents=[Document(id="d1", name="interview.txt", content=text)]),
        codebook=Codebook(codes=[Code(id="C1", name="Autonomy")]),
        code_applications=[
            CodeApplication(
                id="A1",
                code_id="C1",
                doc_id="d1",
                quote_text="autonomy matters",
                start_char=start,
                end_char=end,
                quote_hash="a" * 64,
            )
        ],
        claims=[
            AnalyticClaim(
                id="claim-1",
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="Autonomy is a salient code.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="code",
                origin_object_id="C1",
                supporting_anchors=[anchor],
            ),
            AnalyticClaim(
                id="neg-1",
                claim_kind=ClaimKind.NEGATIVE_CASE,
                source_stage="negative_case_analysis",
                claim_text="Bob complicates the autonomy claim.",
                scope=ClaimScope(claim_ids=["claim-1"], code_ids=["C1"]),
                origin_object_type="negative_case",
                origin_object_id="negative_case:0",
                contrary_anchors=[anchor],
            ),
        ],
        code_relationships=[
            CodeRelationship(
                id="R1",
                source_code_id="C1",
                target_code_id="C2",
                relationship_type="contrasts_with",
                strength=0.7,
                evidence=["Bob disagrees later."],
            )
        ],
        entities=[Entity(id="E1", name="Alice"), Entity(id="E2", name="Bob")],
        entity_relationships=[
            DomainEntityRelationship(
                id="ER1",
                entity_1_id="E1",
                entity_2_id="E2",
                relationship_type="disagrees_with",
                strength=0.8,
                supporting_evidence=["Bob disagrees later."],
            )
        ],
    )
