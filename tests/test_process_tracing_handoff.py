"""Tests for QC process-tracing handoff package export."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.process_tracing_handoff import (
    HANDOFF_PACKAGE_TYPE,
    build_process_tracing_handoff_package,
    validate_process_tracing_handoff_payload,
    write_process_tracing_handoff_package,
)
from qc_clean.schemas.domain import (
    AbductiveCandidateExplanation,
    AnalyticClaim,
    CausalInterpretationStatus,
    ClaimAnchor,
    ClaimKind,
    ClaimScope,
    ClaimSupportStatus,
    Codebook,
    Corpus,
    CorpusScope,
    Document,
    ObservedPattern,
    ObservedPatternKind,
    ProjectState,
)
from scripts import export_process_tracing_handoff, validate_process_tracing_handoff


def _handoff_state() -> ProjectState:
    quote = "The board helped nurses coordinate handoffs."
    return ProjectState(
        id="handoff-proj",
        name="Handoff Project",
        corpus=Corpus(documents=[
            Document(id="doc-1", name="interview.txt", content=f"Jordan: {quote}"),
        ]),
        corpus_scope=CorpusScope(
            phenomenon="AI workflow adoption",
            population="Clinic staff",
            sampling_frame="Pilot clinic interviewees",
            inclusion_criteria=["Participated in the pilot"],
        ),
        codebook=Codebook(),
        observed_patterns=[
            ObservedPattern(
                id="pattern-1",
                source_stage="cross_interview",
                pattern_kind=ObservedPatternKind.CONSENSUS_CODE,
                summary="Workflow visibility appeared across documents.",
                code_ids=["C_VISIBILITY"],
                doc_ids=["doc-1"],
                application_ids=["app-1"],
                count=1,
                total=1,
                support_anchors=[
                    ClaimAnchor(
                        doc_id="doc-1",
                        start_char=8,
                        end_char=8 + len(quote),
                        quote_text=quote,
                        quote_hash="hash-pattern",
                        code_application_id="app-1",
                    )
                ],
                causal_interpretation_status=(
                    CausalInterpretationStatus.CANDIDATE_EXPLANATION_GENERATED
                ),
            )
        ],
        abductive_explanations=[
            AbductiveCandidateExplanation(
                id="abductive-1",
                source_stage="abductive_synthesis",
                source_pattern_ids=["pattern-1"],
                explanation_text="Visibility may support coordination.",
                mechanism_summary="Shared visibility reduces handoff friction.",
                rival_explanations=["Supervisor behavior may explain it."],
                observable_implications=["More handoffs should show stronger effects."],
                evidence_gaps=["Need a process chronology."],
                confidence=0.45,
            )
        ],
        claims=[
            AnalyticClaim(
                id="claim-1",
                claim_kind=ClaimKind.SYNTHESIS_FINDING,
                source_stage="synthesis",
                claim_text="Visibility supported coordination in the fixture.",
                scope=ClaimScope(corpus_level=True, code_ids=["C_VISIBILITY"]),
                support_status=ClaimSupportStatus.SUPPORTED,
                supporting_anchors=[
                    ClaimAnchor(
                        doc_id="doc-1",
                        start_char=8,
                        end_char=8 + len(quote),
                        quote_text=quote,
                        quote_hash="hash-claim",
                        code_application_id="app-1",
                    )
                ],
                origin_object_type="synthesis",
                origin_object_id="synthesis:0",
            )
        ],
    )


def test_export_process_tracing_handoff_package_shape(tmp_path):
    state = _handoff_state()
    output = tmp_path / "handoff.json"

    package = write_process_tracing_handoff_package(state, output)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert package.schema_version == 1
    assert payload["package_type"] == HANDOFF_PACKAGE_TYPE
    assert payload["project_id"] == "handoff-proj"
    assert payload["corpus_scope"]["phenomenon"] == "AI workflow adoption"
    assert payload["documents"][0]["doc_id"] == "doc-1"
    assert len(payload["documents"][0]["content_sha256"]) == 64
    assert payload["observed_patterns"][0]["support_anchor_ids"]
    assert payload["abductive_candidates"][0]["source_pattern_ids"] == ["pattern-1"]
    assert payload["analytic_claims"][0]["supporting_anchor_ids"]
    assert len(payload["anchors"]) == 2
    assert "not causal proof" in " ".join(payload["caveats"])
    assert len(payload["provenance"]["project_state_sha256"]) == 64

    validated = validate_process_tracing_handoff_payload(payload)
    assert validated.project_id == "handoff-proj"


def test_validate_rejects_missing_candidate_pattern_reference():
    payload = build_process_tracing_handoff_package(_handoff_state()).model_dump(mode="json")
    payload["abductive_candidates"][0]["source_pattern_ids"] = ["missing-pattern"]

    try:
        validate_process_tracing_handoff_payload(payload)
    except ValueError as exc:
        assert "source_pattern_ids not found" in str(exc)
    else:
        raise AssertionError("Expected missing source pattern reference to fail")


def test_validate_rejects_missing_anchor_document_reference():
    payload = build_process_tracing_handoff_package(_handoff_state()).model_dump(mode="json")
    payload["anchors"][0]["doc_id"] = "missing-doc"

    try:
        validate_process_tracing_handoff_payload(payload)
    except ValueError as exc:
        assert "Anchor doc_id values not found" in str(exc)
    else:
        raise AssertionError("Expected missing anchor document reference to fail")


def test_validate_rejects_process_tracing_inference_fields():
    payload = build_process_tracing_handoff_package(_handoff_state()).model_dump(mode="json")
    payload["comparative_support"] = {"h1": 0.8}

    try:
        validate_process_tracing_handoff_payload(payload)
    except ValueError as exc:
        assert "Forbidden process-tracing inference fields" in str(exc)
    else:
        raise AssertionError("Expected forbidden PT inference field to fail")


def test_cli_exports_and_validates_handoff_package(tmp_path):
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(_handoff_state())
    output = tmp_path / "handoff.json"

    export_code = export_process_tracing_handoff.main([
        "handoff-proj",
        "--projects-dir",
        str(tmp_path / "projects"),
        "--output",
        str(output),
    ])
    validate_code = validate_process_tracing_handoff.main([str(output)])

    assert export_code == 0
    assert validate_code == 0
    payload = json.loads(Path(output).read_text(encoding="utf-8"))
    assert payload["abductive_candidates"][0]["id"] == "abductive-1"


def test_top_level_qc_cli_exports_and_validates_handoff_package(tmp_path):
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(_handoff_state())
    output = tmp_path / "handoff_cli.json"

    export_run = subprocess.run(
        [
            sys.executable,
            "qc_cli.py",
            "export-process-tracing-handoff",
            "handoff-proj",
            "--projects-dir",
            str(tmp_path / "projects"),
            "--output",
            str(output),
        ],
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    validate_run = subprocess.run(
        [
            sys.executable,
            "qc_cli.py",
            "validate-process-tracing-handoff",
            str(output),
        ],
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert export_run.returncode == 0, export_run.stderr
    assert validate_run.returncode == 0, validate_run.stderr
    assert output.exists()
