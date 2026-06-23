"""Tests for the theoretical-sampling candidate export script."""

from __future__ import annotations

import json
import hashlib

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import (
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    ProjectState,
)
from scripts import export_theoretical_sampling_candidates


def test_export_theoretical_sampling_candidates_writes_output_and_stdout(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = _state_with_uncoded_document()
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    protocol_path = tmp_path / "protocol.json"
    output_file = tmp_path / "candidates.json"
    protocol_path.write_text(json.dumps(_valid_protocol(state)), encoding="utf-8")
    monkeypatch.setattr(export_theoretical_sampling_candidates, "ProjectStore", lambda: store)

    exit_code = export_theoretical_sampling_candidates.main([
        state.id,
        "--protocol",
        str(protocol_path),
        "--output",
        str(output_file),
        "--max-suggestions",
        "1",
    ])

    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert stdout_payload == file_payload
    assert stdout_payload["package_type"] == "qualitative_coding.theoretical_sampling_candidates"
    assert stdout_payload["project_id"] == state.id
    assert stdout_payload["candidates"][0]["doc_id"] == "doc-2"


def test_export_theoretical_sampling_candidates_accepts_projects_dir(tmp_path, capsys):
    state = _state_with_uncoded_document()
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    protocol_path = tmp_path / "protocol.json"
    output_file = tmp_path / "candidates.json"
    protocol_path.write_text(json.dumps(_valid_protocol(state)), encoding="utf-8")

    exit_code = export_theoretical_sampling_candidates.main([
        state.id,
        "--projects-dir",
        str(store.projects_dir),
        "--protocol",
        str(protocol_path),
        "--output",
        str(output_file),
        "--max-suggestions",
        "1",
    ])

    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert stdout_payload == file_payload
    assert stdout_payload["project_id"] == state.id
    assert stdout_payload["candidates"][0]["candidate_id"] == "loaded-doc-2"


def test_export_theoretical_sampling_candidates_missing_project_returns_json_error(
    tmp_path,
    monkeypatch,
    capsys,
):
    store = ProjectStore(projects_dir=tmp_path / "projects")
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(
        json.dumps(_valid_protocol(_state_with_uncoded_document())),
        encoding="utf-8",
    )
    monkeypatch.setattr(export_theoretical_sampling_candidates, "ProjectStore", lambda: store)

    exit_code = export_theoretical_sampling_candidates.main([
        "missing-project",
        "--protocol",
        str(protocol_path),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "missing-project" in output["error"]


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
    return ProjectState(
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


def _sha256_jsonable(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
