#!/usr/bin/env python3
"""Build a deterministic reviewer demo packet for qualitative_coding.

The packet is intentionally synthetic and LLM-free. It demonstrates the local
software surfaces that Brian can inspect before any live-data or live-model
review: project state, exports, API/review/graph snapshots, and Phase 0
structural scorecard artifacts.
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from qc_clean.core.export.data_exporter import ProjectExporter
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.process_tracing_handoff import write_process_tracing_handoff_package
from qc_clean.plugins.api.api_server import QCAPIServer
from qc_clean.schemas.domain import (
    AbductiveCandidateExplanation,
    AnalyticClaim,
    AnalysisMemo,
    AnalysisPhaseResult,
    CausalInterpretationStatus,
    ClaimAdjudicationStatus,
    ClaimAnchor,
    ClaimKind,
    ClaimScope,
    ClaimSupportStatus,
    Code,
    CodeApplication,
    CodeRelationship,
    Codebook,
    Corpus,
    CorpusScope,
    Document,
    DomainEntityRelationship,
    Entity,
    Methodology,
    ObservedPattern,
    ObservedPatternKind,
    PipelineStatus,
    ProjectConfig,
    ProjectState,
    Provenance,
    Recommendation,
    Segment,
    Synthesis,
)
from scripts import bench_phase0


PROJECT_ID = "reviewer-demo"
DEFAULT_OUTPUT_DIR = Path("test_output/reviewer_demo")
DEMO_CAVEAT = (
    "Deterministic reviewer demo built from synthetic, hand-authored fixture "
    "state; not methodological validity evidence and not SOTA evidence."
)


def build_reviewer_demo(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    """Build the reviewer demo packet and return its manifest payload."""
    output_dir = Path(output_dir)
    projects_dir = output_dir / "projects"
    transcripts_dir = output_dir / "transcripts"
    exports_dir = output_dir / "exports"
    snapshots_dir = output_dir / "api_snapshots"
    benchmark_dir = output_dir / "benchmark_artifacts"
    handoff_dir = output_dir / "handoff"

    for directory in [
        output_dir,
        projects_dir,
        transcripts_dir,
        exports_dir,
        snapshots_dir,
        benchmark_dir,
        handoff_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    state = _demo_state()
    _write_fixture_transcripts(state, transcripts_dir)

    store = ProjectStore(projects_dir=projects_dir)
    project_state_path = store.save(state)

    exporter = ProjectExporter()
    json_export = Path(
        exporter.export_json(
            state,
            str(exports_dir / "reviewer-demo-export.json"),
        )
    )
    markdown_export = Path(
        exporter.export_markdown(
            state,
            str(exports_dir / "reviewer-demo-report.md"),
        )
    )

    snapshots = _write_api_snapshots(projects_dir, snapshots_dir)
    process_tracing_handoff = handoff_dir / "process_tracing_handoff.json"
    write_process_tracing_handoff_package(state, process_tracing_handoff)
    scorecard, benchmark_manifest = _write_scorecard_artifacts(
        projects_dir,
        output_dir,
        benchmark_dir,
    )

    readme = output_dir / "README.md"
    self_review = output_dir / "SELF_REVIEW.md"
    _write_readme(readme, output_dir, projects_dir)
    _write_self_review(self_review)

    manifest = {
        "schema_version": 1,
        "project_id": state.id,
        "generated_at": datetime.now().isoformat(),
        "caveat": DEMO_CAVEAT,
        "output_dir": str(output_dir),
        "projects_dir": str(projects_dir),
        "readme": str(readme),
        "self_review": str(self_review),
        "project_state": str(project_state_path),
        "markdown_export": str(markdown_export),
        "json_export": str(json_export),
        "scorecard": str(scorecard),
        "benchmark_manifest": str(benchmark_manifest),
        "process_tracing_handoff": str(process_tracing_handoff),
        **snapshots,
    }
    manifest_path = output_dir / "packet_manifest.json"
    _write_json(manifest_path, manifest)
    manifest["packet_manifest"] = str(manifest_path)
    return manifest


def _demo_state() -> ProjectState:
    """Construct a synthetic but review-rich project state."""
    doc_avery = Document(
        id="doc-avery",
        name="avery_operations_manager.txt",
        content=(
            "Avery: The triage board helps us see blocked intake work.\n"
            "Avery: It also makes some staff feel watched when every pause is visible.\n"
            "Avery: When the network drops, the paper board keeps the shift moving.\n"
        ),
        detected_speakers=["Avery"],
        metadata={"fixture": "reviewer_demo", "role": "operations_manager"},
    )
    doc_jordan = Document(
        id="doc-jordan",
        name="jordan_clinical_lead.txt",
        content=(
            "Jordan: The board helped nurses coordinate handoffs during rushes.\n"
            "Jordan: We still keep a paper fallback because network outages stop the board.\n"
            "Jordan: Staff accept the tool when supervisors use it to unblock work, not to score people.\n"
        ),
        detected_speakers=["Jordan"],
        metadata={"fixture": "reviewer_demo", "role": "clinical_lead"},
    )
    documents = [doc_avery, doc_jordan]

    codes = [
        Code(
            id="C_VISIBILITY",
            name="Workflow Visibility",
            description="Shared board visibility helps staff locate blocked work.",
            definition="References to seeing, coordinating, or unblocking work.",
            mention_count=2,
            confidence=0.91,
            provenance=Provenance.SYSTEM,
            example_quotes=[
                "The triage board helps us see blocked intake work.",
                "The board helped nurses coordinate handoffs during rushes.",
            ],
            reasoning="Synthetic fixture code used to exercise anchored applications.",
        ),
        Code(
            id="C_MONITORING",
            name="Monitoring Concern",
            description="Visibility can feel like surveillance or performance scoring.",
            definition="References to feeling watched, scored, or monitored.",
            mention_count=2,
            confidence=0.84,
            provenance=Provenance.SYSTEM,
            example_quotes=[
                "some staff feel watched when every pause is visible",
                "not to score people",
            ],
            reasoning="Synthetic fixture code used to exercise contrary evidence.",
        ),
        Code(
            id="C_FALLBACK",
            name="Fallback Workarounds",
            description="Paper backups remain necessary when the digital board fails.",
            definition="References to fallback processes during outages.",
            mention_count=2,
            confidence=0.88,
            provenance=Provenance.SYSTEM,
            example_quotes=[
                "the paper board keeps the shift moving",
                "paper fallback because network outages stop the board",
            ],
            reasoning="Synthetic fixture code used to exercise scope-bound claims.",
        ),
    ]

    applications = [
        _application(
            "A_VISIBILITY_AVERY",
            "C_VISIBILITY",
            doc_avery,
            "The triage board helps us see blocked intake work.",
            "Avery",
            0.92,
        ),
        _application(
            "A_VISIBILITY_JORDAN",
            "C_VISIBILITY",
            doc_jordan,
            "The board helped nurses coordinate handoffs during rushes.",
            "Jordan",
            0.89,
        ),
        _application(
            "A_MONITORING_AVERY",
            "C_MONITORING",
            doc_avery,
            "some staff feel watched when every pause is visible",
            "Avery",
            0.86,
        ),
        _application(
            "A_MONITORING_JORDAN",
            "C_MONITORING",
            doc_jordan,
            "not to score people",
            "Jordan",
            0.80,
        ),
        _application(
            "A_FALLBACK_AVERY",
            "C_FALLBACK",
            doc_avery,
            "the paper board keeps the shift moving",
            "Avery",
            0.87,
        ),
        _application(
            "A_FALLBACK_JORDAN",
            "C_FALLBACK",
            doc_jordan,
            "paper fallback because network outages stop the board",
            "Jordan",
            0.90,
        ),
    ]

    segments = _segments_for_documents(documents)
    app_by_id = {app.id: app for app in applications}
    observed_patterns = [
        ObservedPattern(
            id="pattern:reviewer_demo:consensus_code:C_VISIBILITY",
            source_stage="cross_interview",
            pattern_kind=ObservedPatternKind.CONSENSUS_CODE,
            summary=(
                "Workflow visibility appears in both synthetic transcripts as a "
                "coordination aid."
            ),
            code_ids=["C_VISIBILITY"],
            doc_ids=["doc-avery", "doc-jordan"],
            application_ids=["A_VISIBILITY_AVERY", "A_VISIBILITY_JORDAN"],
            support_anchors=[
                _anchor_from_application(app_by_id["A_VISIBILITY_AVERY"]),
                _anchor_from_application(app_by_id["A_VISIBILITY_JORDAN"]),
            ],
            strength=1.0,
            count=2,
            total=2,
            metadata={"denominator": "documents_with_code_applications"},
            causal_interpretation_status=(
                CausalInterpretationStatus.CANDIDATE_EXPLANATION_GENERATED
            ),
            created_by=Provenance.SYSTEM,
        ),
        ObservedPattern(
            id="pattern:reviewer_demo:consensus_code:C_FALLBACK",
            source_stage="cross_interview",
            pattern_kind=ObservedPatternKind.CONSENSUS_CODE,
            summary=(
                "Fallback workaround talk appears in both synthetic transcripts."
            ),
            code_ids=["C_FALLBACK"],
            doc_ids=["doc-avery", "doc-jordan"],
            application_ids=["A_FALLBACK_AVERY", "A_FALLBACK_JORDAN"],
            support_anchors=[
                _anchor_from_application(app_by_id["A_FALLBACK_AVERY"]),
                _anchor_from_application(app_by_id["A_FALLBACK_JORDAN"]),
            ],
            strength=1.0,
            count=2,
            total=2,
            metadata={"denominator": "documents_with_code_applications"},
            causal_interpretation_status=(
                CausalInterpretationStatus.CANDIDATE_EXPLANATION_GENERATED
            ),
            created_by=Provenance.SYSTEM,
        ),
        ObservedPattern(
            id="pattern:reviewer_demo:code_co_occurrence:C_VISIBILITY:C_MONITORING",
            source_stage="cross_interview",
            pattern_kind=ObservedPatternKind.CODE_CO_OCCURRENCE,
            summary=(
                "Visibility and monitoring concern co-occur in the fixture, "
                "creating a tension for interpretation."
            ),
            code_ids=["C_VISIBILITY", "C_MONITORING"],
            doc_ids=["doc-avery", "doc-jordan"],
            application_ids=[
                "A_VISIBILITY_AVERY",
                "A_VISIBILITY_JORDAN",
                "A_MONITORING_AVERY",
                "A_MONITORING_JORDAN",
            ],
            support_anchors=[
                _anchor_from_application(app_by_id["A_VISIBILITY_AVERY"]),
                _anchor_from_application(app_by_id["A_MONITORING_AVERY"]),
                _anchor_from_application(app_by_id["A_MONITORING_JORDAN"]),
            ],
            count=2,
            total=2,
            metadata={"denominator": "documents_with_both_codes"},
            causal_interpretation_status=(
                CausalInterpretationStatus.CANDIDATE_EXPLANATION_GENERATED
            ),
            created_by=Provenance.SYSTEM,
        ),
    ]
    abductive_explanations = [
        AbductiveCandidateExplanation(
            id="abductive:reviewer_demo:coordination_control_tension",
            source_stage="abductive_synthesis",
            source_pattern_ids=[
                "pattern:reviewer_demo:consensus_code:C_VISIBILITY",
                "pattern:reviewer_demo:code_co_occurrence:C_VISIBILITY:C_MONITORING",
            ],
            explanation_text=(
                "The board may help coordination when visibility is framed as "
                "unblocking work, but create resistance when the same visibility "
                "is interpreted as monitoring."
            ),
            mechanism_summary=(
                "Shared visibility changes adoption through a framing mechanism: "
                "coordination support versus performance surveillance."
            ),
            rival_explanations=[
                "The monitoring concern may be a generic workplace concern rather than board-specific.",
                "Differences between roles may explain the tension without a single mechanism.",
            ],
            observable_implications=[
                "Future interviews should show stronger acceptance where supervisors use the board to unblock work.",
                "Cases with scoring language should show more monitoring concern.",
            ],
            evidence_gaps=[
                "No direct process trace yet shows how supervisors used board data.",
                "The fixture has only two synthetic transcripts and no follow-up observations.",
            ],
            confidence=0.42,
            created_by=Provenance.SYSTEM,
        ),
        AbductiveCandidateExplanation(
            id="abductive:reviewer_demo:fallback_resilience",
            source_stage="abductive_synthesis",
            source_pattern_ids=[
                "pattern:reviewer_demo:consensus_code:C_FALLBACK",
            ],
            explanation_text=(
                "Fallback practices may be part of adoption rather than a sign "
                "that the digital board failed."
            ),
            mechanism_summary=(
                "Operational resilience depends on switching between digital "
                "coordination and paper backup during outages."
            ),
            rival_explanations=[
                "Fallback talk could indicate low trust in the digital tool.",
            ],
            observable_implications=[
                "Teams with explicit fallback routines should recover faster from outages.",
            ],
            evidence_gaps=[
                "No outage timeline or operational metric is included in the fixture.",
            ],
            confidence=0.35,
            created_by=Provenance.SYSTEM,
        ),
    ]

    claims = [
        AnalyticClaim(
            id="claim_visibility_coordination",
            claim_kind=ClaimKind.SYNTHESIS_FINDING,
            source_stage="synthesis",
            claim_text=(
                "In this synthetic fixture, the board is framed as useful "
                "for making blocked work and handoffs visible."
            ),
            scope=ClaimScope(
                corpus_level=True,
                doc_ids=["doc-avery", "doc-jordan"],
                code_ids=["C_VISIBILITY"],
                application_ids=["A_VISIBILITY_AVERY", "A_VISIBILITY_JORDAN"],
                participant_names=["Avery", "Jordan"],
            ),
            origin_object_type="synthesis",
            origin_object_id="fixture_finding_visibility",
            supporting_anchors=[
                _anchor_from_application(app_by_id["A_VISIBILITY_AVERY"]),
                _anchor_from_application(app_by_id["A_VISIBILITY_JORDAN"]),
            ],
            support_status=ClaimSupportStatus.SUPPORTED,
            adjudication_status=ClaimAdjudicationStatus.PENDING,
            created_by=Provenance.SYSTEM,
        ),
        AnalyticClaim(
            id="claim_visibility_only_positive",
            claim_kind=ClaimKind.CROSS_CASE,
            source_stage="cross_interview",
            claim_text=(
                "A simple positive-efficiency interpretation is incomplete "
                "because one participant describes visibility as feeling watched."
            ),
            scope=ClaimScope(
                corpus_level=True,
                claim_ids=["claim_visibility_coordination"],
                doc_ids=["doc-avery", "doc-jordan"],
                code_ids=["C_VISIBILITY", "C_MONITORING"],
                application_ids=["A_VISIBILITY_AVERY", "A_MONITORING_AVERY"],
            ),
            origin_object_type="memo",
            origin_object_id="M_CROSS_CASE",
            supporting_anchors=[_anchor_from_application(app_by_id["A_VISIBILITY_AVERY"])],
            contrary_anchors=[_anchor_from_application(app_by_id["A_MONITORING_AVERY"])],
            support_status=ClaimSupportStatus.MIXED,
            adjudication_status=ClaimAdjudicationStatus.PENDING,
            created_by=Provenance.SYSTEM,
        ),
        AnalyticClaim(
            id="claim_fallback_resilience",
            claim_kind=ClaimKind.SYNTHESIS_FINDING,
            source_stage="synthesis",
            claim_text=(
                "Both synthetic participants describe paper fallback practices "
                "as part of keeping work moving during outages."
            ),
            scope=ClaimScope(
                corpus_level=True,
                doc_ids=["doc-avery", "doc-jordan"],
                code_ids=["C_FALLBACK"],
                application_ids=["A_FALLBACK_AVERY", "A_FALLBACK_JORDAN"],
            ),
            origin_object_type="synthesis",
            origin_object_id="fixture_finding_fallback",
            supporting_anchors=[
                _anchor_from_application(app_by_id["A_FALLBACK_AVERY"]),
                _anchor_from_application(app_by_id["A_FALLBACK_JORDAN"]),
            ],
            support_status=ClaimSupportStatus.SUPPORTED,
            adjudication_status=ClaimAdjudicationStatus.PENDING,
            created_by=Provenance.SYSTEM,
        ),
        AnalyticClaim(
            id="claim_negative_case_monitoring",
            claim_kind=ClaimKind.NEGATIVE_CASE,
            source_stage="negative_case",
            claim_text=(
                "Monitoring concern is a negative case against treating "
                "workflow visibility as purely coordination support."
            ),
            scope=ClaimScope(
                corpus_level=True,
                claim_ids=["claim_visibility_coordination"],
                doc_ids=["doc-avery"],
                code_ids=["C_MONITORING"],
                application_ids=["A_MONITORING_AVERY"],
            ),
            origin_object_type="negative_case",
            origin_object_id="fixture_negative_case_monitoring",
            contrary_anchors=[_anchor_from_application(app_by_id["A_MONITORING_AVERY"])],
            support_status=ClaimSupportStatus.MIXED,
            adjudication_status=ClaimAdjudicationStatus.PENDING,
            created_by=Provenance.SYSTEM,
        ),
    ]

    return ProjectState(
        id=PROJECT_ID,
        name="Reviewer Demo: Shift Coordination",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            model_name="deterministic-fixture-no-llm",
        ),
        corpus=Corpus(documents=documents),
        corpus_scope=CorpusScope(
            phenomenon="Use of a shared triage board in clinic shift coordination",
            population="Synthetic clinic operations stakeholders",
            sampling_frame="Two hand-authored fixture transcripts for software review only",
            inclusion_criteria=["Synthetic transcript created for demo review"],
            exclusion_criteria=["Real patient, staff, or private operational data"],
            notes=(
                "This scope exists to exercise report-boundary surfaces; it "
                "does not support population generalization."
            ),
        ),
        codebook=Codebook(
            methodology=Methodology.THEMATIC_ANALYSIS.value,
            created_by=Provenance.SYSTEM,
            codes=codes,
        ),
        code_applications=applications,
        segments=segments,
        code_relationships=[
            CodeRelationship(
                id="REL_VISIBILITY_MONITORING",
                source_code_id="C_VISIBILITY",
                target_code_id="C_MONITORING",
                relationship_type="tension_with",
                strength=0.72,
                evidence=["some staff feel watched when every pause is visible"],
                conditions=["Visibility is used for performance scoring"],
                consequences=["Coordination benefits may be interpreted as surveillance"],
            ),
            CodeRelationship(
                id="REL_FALLBACK_VISIBILITY",
                source_code_id="C_FALLBACK",
                target_code_id="C_VISIBILITY",
                relationship_type="qualifies",
                strength=0.66,
                evidence=["paper fallback because network outages stop the board"],
                conditions=["Network outage"],
                consequences=["Digital coordination requires backup process"],
            ),
        ],
        entities=[
            Entity(
                id="E_TRIAGE_BOARD",
                name="Triage board",
                entity_type="tool",
                description="Synthetic shared board used in the fixture.",
                doc_ids=["doc-avery", "doc-jordan"],
            ),
            Entity(
                id="E_PAPER_BOARD",
                name="Paper fallback",
                entity_type="process",
                description="Synthetic backup process during outages.",
                doc_ids=["doc-avery", "doc-jordan"],
            ),
        ],
        entity_relationships=[
            DomainEntityRelationship(
                id="ER_BOARD_FALLBACK",
                entity_1_id="E_TRIAGE_BOARD",
                entity_2_id="E_PAPER_BOARD",
                relationship_type="requires_backup",
                strength=0.76,
                supporting_evidence=[
                    "paper fallback because network outages stop the board",
                ],
            )
        ],
        synthesis=Synthesis(
            executive_summary=(
                "This deterministic fixture shows how the software represents "
                "codes, anchored applications, claim scope, contrary evidence, "
                "and review surfaces. It is not a live analysis result."
            ),
            key_findings=[
                "Workflow visibility is represented with two anchored applications.",
                "Monitoring concern challenges a simple efficiency-only reading.",
                "Fallback workarounds show scope-limited operational resilience.",
            ],
            cross_cutting_patterns=[
                "Visibility is both a coordination aid and a potential monitoring concern.",
                "Digital workflows remain dependent on non-digital fallback processes.",
            ],
            recommendations=[
                Recommendation(
                    title="Review monitoring claims before external use",
                    description=(
                        "The mixed-support claim should be inspected by a human "
                        "reviewer before any report language is reused."
                    ),
                    priority="high",
                    supporting_themes=["Monitoring Concern", "Workflow Visibility"],
                )
            ],
            confidence_assessment={
                "fixture_confidence": "deterministic",
                "live_llm_run": False,
                "validity_claim": "none",
            },
        ),
        memos=[
            AnalysisMemo(
                id="M_CROSS_CASE",
                memo_type="cross_case",
                title="Synthetic Cross-Case Memo",
                content=(
                    "Both participants describe the board as useful, but the "
                    "fixture deliberately includes a contrary monitoring concern."
                ),
                code_refs=["C_VISIBILITY", "C_MONITORING"],
                doc_refs=["doc-avery", "doc-jordan"],
                created_by=Provenance.SYSTEM,
            ),
            AnalysisMemo(
                id="M_NEGATIVE_CASE",
                memo_type="negative_case",
                title="Synthetic Negative Case Memo",
                content=(
                    "The 'feel watched' passage is a bounded contrary anchor "
                    "against an efficiency-only interpretation."
                ),
                code_refs=["C_MONITORING"],
                doc_refs=["doc-avery"],
                created_by=Provenance.SYSTEM,
            ),
            AnalysisMemo(
                id="M_ABDUCTIVE_CANDIDATES",
                memo_type="methodological",
                title="Synthetic Abductive Candidate Memo",
                content=(
                    "The abductive candidates in this packet are hand-authored "
                    "software fixtures. They demonstrate candidate-explanation "
                    "storage and read surfaces only, not causal proof."
                ),
                code_refs=["C_VISIBILITY", "C_MONITORING", "C_FALLBACK"],
                doc_refs=["doc-avery", "doc-jordan"],
                created_by=Provenance.SYSTEM,
            ),
        ],
        observed_patterns=observed_patterns,
        abductive_explanations=abductive_explanations,
        claims=claims,
        phase_results=[
            _phase("Ingest"),
            _phase("Thematic Coding"),
            _phase("Perspective Analysis"),
            _phase("Relationship Mapping"),
            _phase("Synthesis"),
            _phase("Cross-Interview"),
            _phase("Negative Case"),
        ],
        current_phase="Negative Case",
        pipeline_status=PipelineStatus.COMPLETED,
        data_warnings=[DEMO_CAVEAT],
    )


def _application(
    app_id: str,
    code_id: str,
    doc: Document,
    quote: str,
    speaker: str,
    confidence: float,
) -> CodeApplication:
    """Create an anchored code application from an exact quote."""
    start, end, digest = _quote_span(doc, quote)
    return CodeApplication(
        id=app_id,
        code_id=code_id,
        doc_id=doc.id,
        quote_text=quote,
        speaker=speaker,
        start_char=start,
        end_char=end,
        quote_hash=digest,
        confidence=confidence,
        applied_by=Provenance.SYSTEM,
    )


def _anchor_from_application(app: CodeApplication) -> ClaimAnchor:
    """Convert a code application into a claim anchor."""
    return ClaimAnchor(
        doc_id=app.doc_id,
        start_char=app.start_char,
        end_char=app.end_char,
        quote_text=app.quote_text,
        quote_hash=app.quote_hash,
        code_application_id=app.id,
    )


def _quote_span(doc: Document, quote: str) -> tuple[int, int, str]:
    """Return exact span offsets and SHA-256 hash for a quote."""
    start = doc.content.index(quote)
    end = start + len(quote)
    digest = hashlib.sha256(doc.content[start:end].encode("utf-8")).hexdigest()
    return start, end, digest


def _segments_for_documents(documents: list[Document]) -> list[Segment]:
    """Create one segment per non-empty transcript line."""
    segments: list[Segment] = []
    for doc in documents:
        cursor = 0
        index = 0
        for raw_line in doc.content.splitlines(keepends=True):
            line = raw_line.rstrip("\n")
            start = cursor
            end = start + len(line)
            cursor += len(raw_line)
            if not line.strip():
                continue
            speaker = line.split(":", 1)[0] if ":" in line else ""
            segments.append(
                Segment(
                    id=f"SEG_{doc.id}_{index}",
                    doc_id=doc.id,
                    index=index,
                    start_char=start,
                    end_char=end,
                    speaker=speaker,
                    text=line,
                    decision="coded",
                )
            )
            index += 1
    return segments


def _phase(name: str) -> AnalysisPhaseResult:
    """Create a completed phase result for the fixture run ledger."""
    return AnalysisPhaseResult(
        phase_name=name,
        status=PipelineStatus.COMPLETED,
        input_summary={"fixture": True},
        output_summary={"demo": "deterministic"},
        metadata={"live_llm_call": False},
    )


def _write_fixture_transcripts(state: ProjectState, transcripts_dir: Path) -> None:
    """Write the synthetic transcript files used by the packet."""
    for doc in state.corpus.documents:
        (transcripts_dir / doc.name).write_text(doc.content, encoding="utf-8")


def _write_api_snapshots(projects_dir: Path, snapshots_dir: Path) -> dict[str, str]:
    """Write JSON snapshots from the same API routes used by browser surfaces."""
    previous_projects_dir = os.environ.get("QC_PROJECTS_DIR")
    os.environ["QC_PROJECTS_DIR"] = str(projects_dir)
    try:
        server = QCAPIServer(config={"background_processing_enabled": False})
        server._app = FastAPI()
        server._register_default_endpoints()
        client = TestClient(server._app)

        endpoints = {
            "project_snapshot": f"/projects/{PROJECT_ID}",
            "scope_snapshot": f"/projects/{PROJECT_ID}/scope",
            "claims_snapshot": f"/projects/{PROJECT_ID}/claims?limit=2&offset=0",
            "claims_page_2_snapshot": f"/projects/{PROJECT_ID}/claims?limit=2&offset=2",
            "patterns_snapshot": f"/projects/{PROJECT_ID}/patterns?limit=5&offset=0",
            "abductive_snapshot": (
                f"/projects/{PROJECT_ID}/abductive-explanations?limit=5&offset=0"
            ),
            "review_summary_snapshot": f"/projects/{PROJECT_ID}/review",
            "review_codes_snapshot": f"/projects/{PROJECT_ID}/review/codes",
            "review_claims_snapshot": f"/projects/{PROJECT_ID}/review/claims?limit=2&offset=0",
            "review_negative_cases_snapshot": (
                f"/projects/{PROJECT_ID}/review/negative-cases?limit=2&offset=0"
            ),
            "review_relationships_snapshot": (
                f"/projects/{PROJECT_ID}/review/relationships?limit=2&offset=0"
            ),
            "review_abductive_candidates_snapshot": (
                f"/projects/{PROJECT_ID}/review/abductive-candidates?limit=5&offset=0"
            ),
            "graph_codes_snapshot": f"/projects/{PROJECT_ID}/graph/codes",
            "graph_entities_snapshot": f"/projects/{PROJECT_ID}/graph/entities",
        }
        snapshots: dict[str, str] = {}
        for key, endpoint in endpoints.items():
            response = client.get(endpoint)
            response.raise_for_status()
            path = snapshots_dir / f"{key}.json"
            _write_json(path, response.json())
            snapshots[key] = str(path)
        return snapshots
    finally:
        if previous_projects_dir is None:
            os.environ.pop("QC_PROJECTS_DIR", None)
        else:
            os.environ["QC_PROJECTS_DIR"] = previous_projects_dir


def _write_scorecard_artifacts(
    projects_dir: Path,
    output_dir: Path,
    benchmark_dir: Path,
) -> tuple[Path, Path]:
    """Run the deterministic Phase 0 scorecard into the demo packet."""
    scorecard = output_dir / "phase0_scorecard.json"
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = bench_phase0.main(
            [
                PROJECT_ID,
                "--projects-dir",
                str(projects_dir),
                "--output",
                str(scorecard),
                "--artifact-dir",
                str(benchmark_dir),
            ]
        )
    (output_dir / "phase0_stdout.json").write_text(stdout.getvalue(), encoding="utf-8")
    if exit_code != 0:
        raise RuntimeError(f"Phase 0 scorecard failed: {stdout.getvalue()}")

    manifests = sorted(benchmark_dir.glob("*/manifest.json"))
    if not manifests:
        raise RuntimeError("Phase 0 artifact manifest was not written")
    return scorecard, manifests[-1]


def _write_readme(readme: Path, output_dir: Path, projects_dir: Path) -> None:
    """Write the human walkthrough for the generated packet."""
    readme.write_text(
        "\n".join(
            [
                "# Reviewer Demo Packet",
                "",
                DEMO_CAVEAT,
                "",
                "## Generate",
                "",
                "```bash",
                f"make reviewer-demo OUTPUT={output_dir}",
                "```",
                "",
                "## Inspect From CLI",
                "",
                "```bash",
                f"QC_PROJECTS_DIR={projects_dir} python qc_cli.py project show {PROJECT_ID}",
                f"QC_PROJECTS_DIR={projects_dir} python qc_cli.py project claims {PROJECT_ID} --show-scope --show-anchors --limit 2",
                f"QC_PROJECTS_DIR={projects_dir} python qc_cli.py project patterns {PROJECT_ID} --show-anchors --limit 5",
                f"QC_PROJECTS_DIR={projects_dir} python qc_cli.py project abductive {PROJECT_ID} --limit 5",
                f"QC_PROJECTS_DIR={projects_dir} python qc_cli.py export-process-tracing-handoff {PROJECT_ID} --output {output_dir / 'handoff' / 'rerun_process_tracing_handoff.json'}",
                f"QC_PROJECTS_DIR={projects_dir} python qc_cli.py project export {PROJECT_ID} --format markdown --output-file {output_dir / 'exports' / 'rerun-report.md'}",
                "```",
                "",
                "## Inspect Browser Surfaces",
                "",
                "```bash",
                f"QC_PROJECTS_DIR={projects_dir} python start_server.py",
                "```",
                "",
                f"- Review UI: http://localhost:8002/review/{PROJECT_ID}",
                f"- Graph UI: http://localhost:8002/graph/{PROJECT_ID}",
                f"- Claim API: http://localhost:8002/projects/{PROJECT_ID}/claims?limit=2&offset=0",
                f"- Observed Pattern API: http://localhost:8002/projects/{PROJECT_ID}/patterns?limit=5&offset=0",
                f"- Abductive Candidate API: http://localhost:8002/projects/{PROJECT_ID}/abductive-explanations?limit=5&offset=0",
                f"- Abductive Candidate Review API: http://localhost:8002/projects/{PROJECT_ID}/review/abductive-candidates?limit=5&offset=0",
                "",
                "## Main Files",
                "",
                "- `SELF_REVIEW.md` - readiness critique and caveats",
                "- `exports/reviewer-demo-report.md` - Markdown report export",
                "- `exports/reviewer-demo-export.json` - full JSON export",
                "- `handoff/process_tracing_handoff.json` - QC-to-process-tracing handoff package",
                "- `api_snapshots/` - JSON snapshots from API/review/graph routes",
                "- `phase0_scorecard.json` - deterministic structural scorecard",
                "- `benchmark_artifacts/` - versioned Phase 0 artifact package",
                "",
                "## Interpretation Boundary",
                "",
                "This packet demonstrates software behavior and review surfaces. "
                "It is not expert adjudication, held-out benchmark evidence, "
                "methodological validity evidence, or SOTA evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_self_review(self_review: Path) -> None:
    """Write the self-review caveat that gates Brian handoff."""
    self_review.write_text(
        "\n".join(
            [
                "# Self Review",
                "",
                "## Ready For Brian Review",
                "",
                "- The packet is generated from an isolated synthetic project store.",
                "- CLI, API/review, graph, export, and Phase 0 scorecard artifacts are present.",
                "- Claim rows include scope plus supporting/contrary anchor details.",
                "- The fixture contains a negative-case claim for review-surface inspection.",
                "",
                "## Not Evidence",
                "",
                "- This is not methodological validity evidence.",
                "- This is not SOTA evidence.",
                "- This is not a live LLM pipeline run.",
                "- This is not expert adjudication or held-out D3/D7 benchmark evidence.",
                "- The synthetic claims are hand-authored to exercise software surfaces.",
                "",
                "## What To Review",
                "",
                "- Whether the output is understandable enough for a reviewer to inspect.",
                "- Whether claim scope, anchors, and contrary evidence are visible.",
                "- Whether the caveats prevent overclaiming.",
                "- Whether the next milestone should be a live LLM smoke run or a UI polish pass.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_json(path: Path, payload: Any) -> None:
    """Write JSON with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for reviewer demo packet generation."""
    parser = argparse.ArgumentParser(description="Build deterministic reviewer demo packet")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for generated packet artifacts",
    )
    args = parser.parse_args(argv)

    manifest = build_reviewer_demo(Path(args.output_dir))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
