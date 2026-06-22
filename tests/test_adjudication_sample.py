"""Tests for deterministic adjudication sample package export."""

import json

from qc_clean.core.adjudication_sample import (
    build_adjudication_sample_package,
    validate_adjudication_response_payload,
    write_adjudication_sample_package,
)
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


def test_builds_deterministic_adjudication_sample_package(tmp_path):
    """Package includes provenance, context, stable ordering, and response templates."""
    state = _adjudication_state()

    package = build_adjudication_sample_package(
        state,
        limit_per_type=10,
        context_chars=8,
    )
    payload = package.model_dump(mode="json")

    assert payload["schema_version"] == 1
    assert payload["package_type"] == "adjudication_sample"
    assert payload["project_id"] == "adj-proj"
    assert payload["project_name"] == "Adjudication Project"
    assert payload["hash_algorithm"] == "sha256"
    assert len(payload["project_state_sha256"]) == 64
    assert len(payload["corpus_sha256"]) == 64
    assert payload["sample_policy"]["limit_per_type"] == 10
    assert payload["sample_policy"]["context_chars"] == 8
    assert payload["item_counts"]["returned"]["total"] == 5
    assert [item["item_id"] for item in payload["items"]] == [
        "code_application:A1",
        "claim:claim-1",
        "negative_case:neg-1",
        "code_relationship:R1",
        "entity_relationship:ER1",
    ]

    app_item = payload["items"][0]
    assert app_item["target_type"] == "code_application"
    assert app_item["payload"]["code_name"] == "Autonomy"
    assert app_item["source_context"]["doc_name"] == "interview.txt"
    assert app_item["source_context"]["quote_text"] == "autonomy matters"
    assert app_item["source_context"]["context_before"].endswith("says ")
    assert app_item["source_context"]["context_after"].startswith(" for")
    assert app_item["response_template"] == {
        "validity": "",
        "rationale": "",
        "corrected_value": None,
        "adjudicator_id": "",
    }

    claim_item = payload["items"][1]
    assert claim_item["target_type"] == "claim"
    assert claim_item["payload"]["claim_kind"] == "code"
    assert claim_item["payload"]["supporting_anchors"][0]["doc_name"] == "interview.txt"

    negative_item = payload["items"][2]
    assert negative_item["target_type"] == "negative_case"
    assert negative_item["payload"]["claim_kind"] == "negative_case"
    assert negative_item["payload"]["scope"]["claim_ids"] == ["claim-1"]

    out = tmp_path / "sample.json"
    written = write_adjudication_sample_package(package, out)
    assert written == str(out)
    assert json.loads(out.read_text(encoding="utf-8")) == payload


def test_limit_per_type_and_negative_case_split():
    """Limits apply per type and negative-case claims are separated from claims."""
    state = _adjudication_state()
    state.claims.extend(
        [
            AnalyticClaim(
                id="claim-2",
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="Second generic claim.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="code",
                origin_object_id="C1",
            ),
            AnalyticClaim(
                id="neg-2",
                claim_kind=ClaimKind.NEGATIVE_CASE,
                source_stage="negative_case_analysis",
                claim_text="Second negative case.",
                scope=ClaimScope(claim_ids=["claim-2"]),
                origin_object_type="negative_case",
                origin_object_id="negative_case:1",
            ),
        ]
    )

    package = build_adjudication_sample_package(state, limit_per_type=1)
    payload = package.model_dump(mode="json")

    assert payload["item_counts"]["available"]["claim"] == 2
    assert payload["item_counts"]["available"]["negative_case"] == 2
    assert payload["item_counts"]["returned"]["claim"] == 1
    assert payload["item_counts"]["returned"]["negative_case"] == 1
    assert [item["item_id"] for item in payload["items"] if item["target_type"] == "claim"] == [
        "claim:claim-1"
    ]
    assert [
        item["item_id"] for item in payload["items"] if item["target_type"] == "negative_case"
    ] == ["negative_case:neg-1"]


def test_validate_complete_adjudication_responses():
    payload = _completed_response_payload()

    report = validate_adjudication_response_payload(payload)
    report_payload = report.model_dump(mode="json")

    assert report_payload["schema_version"] == 1
    assert report_payload["status"] == "complete"
    assert report_payload["total_items"] == 5
    assert report_payload["valid_response_count"] == 5
    assert report_payload["error_count"] == 0
    assert report_payload["counts_by_validity"] == {
        "valid": 3,
        "invalid": 1,
        "unclear": 1,
    }
    assert "not expert evidence" in report_payload["caution"]


def test_validate_adjudication_responses_reports_errors():
    payload = _completed_response_payload()
    payload["items"][0].pop("response")
    payload["items"][1]["response"] = {
        "validity": "maybe",
        "rationale": "Not a valid label.",
        "corrected_value": None,
        "adjudicator_id": "coder-1",
    }
    payload["items"][2]["response"] = {
        "validity": "unclear",
        "rationale": "",
        "corrected_value": None,
        "adjudicator_id": "coder-1",
    }
    payload["items"][3]["response"] = {
        "validity": "valid",
        "rationale": "",
        "corrected_value": None,
        "adjudicator_id": "",
    }

    report = validate_adjudication_response_payload(payload).model_dump(mode="json")

    assert report["status"] == "invalid"
    assert report["valid_response_count"] == 1
    assert report["error_count"] == 4
    errors_by_item = {error["item_id"]: error["message"] for error in report["errors"]}
    assert "missing response" in errors_by_item["code_application:A1"]
    assert "validity must be one of" in errors_by_item["claim:claim-1"]
    assert "rationale is required" in errors_by_item["negative_case:neg-1"]
    assert "adjudicator_id is required" in errors_by_item["code_relationship:R1"]


def test_validate_adjudication_responses_rejects_duplicate_item_ids():
    payload = _completed_response_payload()
    payload["items"].append(dict(payload["items"][0]))

    report = validate_adjudication_response_payload(payload).model_dump(mode="json")

    assert report["status"] == "invalid"
    assert any(
        error["item_id"] == "code_application:A1"
        and "duplicate item_id" in error["message"]
        for error in report["errors"]
    )


def test_validate_adjudication_responses_script(tmp_path, capsys):
    from scripts import validate_adjudication_responses

    valid_path = tmp_path / "valid_responses.json"
    valid_path.write_text(json.dumps(_completed_response_payload()), encoding="utf-8")

    valid_exit = validate_adjudication_responses.main([str(valid_path)])
    valid_report = json.loads(capsys.readouterr().out)

    assert valid_exit == 0
    assert valid_report["status"] == "complete"

    invalid_payload = _completed_response_payload()
    invalid_payload["items"][0]["response"]["validity"] = ""
    invalid_path = tmp_path / "invalid_responses.json"
    invalid_path.write_text(json.dumps(invalid_payload), encoding="utf-8")

    invalid_exit = validate_adjudication_responses.main([str(invalid_path)])
    invalid_report = json.loads(capsys.readouterr().out)

    assert invalid_exit == 1
    assert invalid_report["status"] == "invalid"


def _completed_response_payload() -> dict:
    package = build_adjudication_sample_package(
        _adjudication_state(),
        limit_per_type=10,
        context_chars=8,
    ).model_dump(mode="json")
    labels = ["valid", "invalid", "unclear", "valid", "valid"]
    for item, validity in zip(package["items"], labels):
        item["response"] = {
            "validity": validity,
            "rationale": "Reviewed by coder.",
            "corrected_value": None,
            "adjudicator_id": "coder-1",
        }
    return package


def _adjudication_state() -> ProjectState:
    text = "Alice says autonomy matters for scheduling. Bob disagrees later."
    start = text.index("autonomy matters")
    end = start + len("autonomy matters")
    doc = Document(id="d1", name="interview.txt", content=text)
    anchor = ClaimAnchor(
        doc_id="d1",
        start_char=start,
        end_char=end,
        quote_text="autonomy matters",
        quote_hash="a" * 64,
        code_application_id="A1",
    )
    return ProjectState(
        id="adj-proj",
        name="Adjudication Project",
        corpus=Corpus(documents=[doc]),
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
