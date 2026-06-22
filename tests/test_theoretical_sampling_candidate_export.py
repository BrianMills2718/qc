"""Tests for theoretical-sampling candidate package export."""

from __future__ import annotations

import pytest
import hashlib
import json

from qc_clean.core.theoretical_sampling_candidates import (
    export_theoretical_sampling_candidates,
)
from qc_clean.core.theoretical_sampling_preflight import (
    preflight_theoretical_sampling_payloads,
)
from qc_clean.schemas.domain import (
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    ProjectState,
)


def test_exports_preflight_ready_candidate_package():
    state = _state_with_uncoded_document()
    protocol = _valid_protocol(state)

    package = export_theoretical_sampling_candidates(state, protocol)
    report = preflight_theoretical_sampling_payloads(protocol, package)

    assert package["schema_version"] == 1
    assert package["package_type"] == "qualitative_coding.theoretical_sampling_candidates"
    assert package["protocol_id"] == "ts-protocol-v1"
    assert package["project_id"] == state.id
    assert len(package["project_state_sha256"]) == 64
    assert len(package["corpus_sha256"]) == 64
    assert package["candidate_source"] == "loaded_uncoded_documents"
    assert package["collection_mode"] == "select_existing_documents"
    assert package["candidates"][0]["candidate_id"] == "loaded-doc-2"
    assert package["candidates"][0]["source_kind"] == "loaded_document"
    assert package["candidates"][0]["gap_codes"] == ["ACCESS", "TRUST"]
    assert package["candidates"][0]["gap_types"] == [
        "needs_properties",
        "needs_dimensions",
    ]
    assert report.status == "pass"


def test_candidate_export_rejects_external_only_protocol():
    state = _state_with_uncoded_document()
    protocol = _valid_protocol(state)
    protocol["candidate_source"] = "external_recruitment_pool"
    protocol["collection_mode"] = "collect_new_data"

    with pytest.raises(ValueError, match="loaded-document candidate exporter"):
        export_theoretical_sampling_candidates(state, protocol)


def test_candidate_export_does_not_mutate_project_state():
    state = _state_with_uncoded_document()
    before = state.model_dump(mode="json")

    export_theoretical_sampling_candidates(state, _valid_protocol(state))

    assert state.model_dump(mode="json") == before


def _valid_protocol(state: ProjectState) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.theoretical_sampling_protocol",
        "protocol_id": "ts-protocol-v1",
        "project_id": "project-gt-export",
        "corpus_sha256": _sha256_jsonable(state.corpus.model_dump(mode="json")),
        "project_state_sha256": _sha256_jsonable(state.model_dump(mode="json")),
        "registered_before_sampling": True,
        "candidate_source": "loaded_uncoded_documents",
        "collection_mode": "select_existing_documents",
        "target_gap_codes": ["TRUST", "ACCESS"],
        "target_gap_types": ["needs_properties", "needs_dimensions"],
        "thresholds": {
            "min_properties": 2,
            "min_dimensions": 2,
            "min_supporting_applications": 3,
            "min_supporting_documents": 2,
        },
        "max_suggestions": 2,
        "collection_rules": [
            "Prioritize loaded uncoded documents that can elaborate target gaps.",
        ],
        "stopping_rule": "Stop only after gap-specific sampling decisions are recorded.",
        "success_criteria": [
            "Every targeted gap has an explicit sampling decision.",
        ],
        "caution": "Protocol metadata only; not saturation evidence.",
    }


def _state_with_uncoded_document() -> ProjectState:
    coded_doc = Document(
        id="doc-1",
        name="coded.txt",
        content="Trust was discussed in the first interview.",
        detected_speakers=["A"],
    )
    uncoded_doc = Document(
        id="doc-2",
        name="uncoded.txt",
        content="The second interview discusses access and trust.",
        detected_speakers=["B", "C"],
    )
    state = ProjectState(
        id="project-gt-export",
        name="GT export test",
        corpus=Corpus(documents=[coded_doc, uncoded_doc]),
        codebook=Codebook(
            codes=[
                Code(
                    id="TRUST",
                    name="Trust",
                    description="Trust in the process",
                    properties=["institutional"],
                ),
                Code(id="ACCESS", name="Access", description="Access constraints"),
            ]
        ),
        code_applications=[
            CodeApplication(
                id="app-1",
                code_id="TRUST",
                doc_id="doc-1",
                quote_text="Trust was discussed",
                start_char=0,
                end_char=19,
            )
        ],
    )
    return state


def _sha256_jsonable(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
