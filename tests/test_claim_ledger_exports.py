"""Export coverage for the INV-9 claim ledger."""

import csv
import json
from pathlib import Path

from qc_clean.schemas.domain import (
    AbductiveCandidateExplanation,
    AnalyticClaim,
    ClaimRelationship,
    ClaimKind,
    ClaimScope,
    ClaimSupportStatus,
    CorpusScope,
    ObservedPattern,
    ObservedPatternKind,
    ProjectState,
    Recommendation,
    Synthesis,
)


def _claim_state() -> ProjectState:
    return ProjectState(
        id="claims",
        name="Claim Study",
        claims=[
            AnalyticClaim(
                id="claim-1",
                claim_kind=ClaimKind.SYNTHESIS_FINDING,
                source_stage="synthesis",
                claim_text="AI changes workflow.",
                scope=ClaimScope(corpus_level=True),
                origin_object_type="synthesis_key_finding",
                origin_object_id="finding:0",
                support_status=ClaimSupportStatus.NEEDS_ANCHOR,
            )
        ],
    )


def test_csv_export_writes_claims_file(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    paths = ProjectExporter().export_csv(_claim_state(), str(tmp_path))

    assert str(tmp_path / "claims.csv") in paths
    with open(tmp_path / "claims.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["claim_id"] == "claim-1"
    assert rows[0]["kind"] == "synthesis_finding"
    assert rows[0]["support_status"] == "needs_anchor"
    assert rows[0]["claim_text"] == "AI changes workflow."


def test_csv_claim_rows_include_scope_and_loaded_document_boundary(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    ProjectExporter().export_csv(_claim_state(), str(tmp_path))

    with open(tmp_path / "claims.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["claim_scope"] == "corpus"
    assert "Loaded document corpus only" in rows[0]["corpus_scope_boundary"]
    assert "no CorpusScope recorded" in rows[0]["corpus_scope_boundary"]


def test_csv_claim_rows_include_recorded_scope_boundary(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    state.corpus_scope = CorpusScope(
        phenomenon="AI-assisted workflow change",
        population="Operations teams in the pilot clinics",
        sampling_frame="Volunteer interviewees from two pilot clinics",
        inclusion_criteria=["Participated in the AI workflow pilot"],
        exclusion_criteria=["No direct workflow involvement"],
        notes="Bounded to the loaded transcript corpus.",
    )

    ProjectExporter().export_csv(state, str(tmp_path))

    with open(tmp_path / "claims.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    boundary = rows[0]["corpus_scope_boundary"]
    assert "phenomenon=AI-assisted workflow change" in boundary
    assert "population=Operations teams in the pilot clinics" in boundary
    assert "sampling_frame=Volunteer interviewees from two pilot clinics" in boundary
    assert "inclusion=Participated in the AI workflow pilot" in boundary
    assert "exclusion=No direct workflow involvement" in boundary
    assert "notes=Bounded to the loaded transcript corpus." in boundary


def test_csv_claim_rows_flag_population_without_sampling_frame(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    state.corpus_scope = CorpusScope(population="Operations teams in pilot clinics")

    ProjectExporter().export_csv(state, str(tmp_path))

    with open(tmp_path / "claims.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["corpus_scope_boundary"] == (
        "Unvalidated population boundary: Operations teams in pilot clinics; "
        "sampling frame not recorded."
    )


def test_csv_export_writes_scope_warning_file_when_claims_have_no_scope(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    paths = ProjectExporter().export_csv(_claim_state(), str(tmp_path))

    warning_path = tmp_path / "export_warnings.csv"
    assert str(warning_path) in paths
    with open(warning_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["code"] == "missing_corpus_scope"
    assert rows[0]["applies_to"] == "claim_ledger"
    assert rows[0]["claim_count"] == "1"
    assert "No corpus scope is recorded" in rows[0]["message"]
    assert "bounded to the loaded documents" in rows[0]["message"]


def test_csv_export_writes_all_scope_warnings(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    state.corpus_scope = CorpusScope(population="Operations teams in pilot clinics")

    paths = ProjectExporter().export_csv(state, str(tmp_path))

    warning_path = tmp_path / "export_warnings.csv"
    assert str(warning_path) in paths
    with open(warning_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert [row["code"] for row in rows] == ["missing_sampling_frame"]
    assert rows[0]["applies_to"] == "claim_ledger"
    assert rows[0]["claim_count"] == "1"
    assert "population is recorded without a sampling frame" in rows[0]["message"]
    assert "defensible generalization boundary" in rows[0]["message"]


def test_csv_export_omits_scope_warning_file_without_claims(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    paths = ProjectExporter().export_csv(ProjectState(name="Minimal"), str(tmp_path))

    assert str(tmp_path / "export_warnings.csv") not in paths
    assert not (tmp_path / "export_warnings.csv").exists()


def test_json_export_warns_when_claims_have_no_corpus_scope(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    out = tmp_path / "claims.json"
    ProjectExporter().export_json(_claim_state(), str(out))

    data = json.loads(out.read_text(encoding="utf-8"))
    warnings = data["export_warnings"]
    assert warnings[0]["code"] == "missing_corpus_scope"
    assert warnings[0]["applies_to"] == "claim_ledger"
    assert warnings[0]["claim_count"] == 1
    assert "No corpus scope is recorded" in warnings[0]["message"]
    assert "bounded to the loaded documents" in warnings[0]["message"]
    assert data["claims"][0]["id"] == "claim-1"


def test_json_export_warns_when_corpus_scope_is_empty(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    state.corpus_scope = CorpusScope()
    out = tmp_path / "empty-scope.json"
    ProjectExporter().export_json(state, str(out))

    data = json.loads(out.read_text(encoding="utf-8"))
    warnings = data["export_warnings"]
    assert warnings[0]["code"] == "empty_corpus_scope"
    assert warnings[0]["applies_to"] == "claim_ledger"
    assert warnings[0]["claim_count"] == 1
    assert "scope record exists" in warnings[0]["message"]
    assert "no scope details are specified" in warnings[0]["message"]


def test_json_export_omits_missing_scope_warning_without_claims(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    out = tmp_path / "minimal.json"
    ProjectExporter().export_json(ProjectState(name="Minimal"), str(out))

    data = json.loads(out.read_text(encoding="utf-8"))
    assert "export_warnings" not in data


def test_json_export_omits_scope_warnings_when_scope_is_complete(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    state.corpus_scope = CorpusScope(
        phenomenon="AI-assisted workflow change",
        population="Operations teams in the pilot clinics",
        sampling_frame="Volunteer interviewees from two pilot clinics",
        inclusion_criteria=["Participated in the AI workflow pilot"],
        exclusion_criteria=["No direct workflow involvement"],
        notes="Bounded to the loaded transcript corpus.",
    )
    out = tmp_path / "complete-scope.json"
    ProjectExporter().export_json(state, str(out))

    data = json.loads(out.read_text(encoding="utf-8"))
    assert "export_warnings" not in data


def test_markdown_export_includes_claim_ledger_summary(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    out = tmp_path / "claims.md"
    ProjectExporter().export_markdown(_claim_state(), str(out))

    content = Path(out).read_text()
    assert "## Claim Ledger" in content
    assert "**Total claims**: 1" in content
    assert "synthesis_finding" in content
    assert "AI changes workflow." in content


def test_export_markdown_includes_observed_patterns(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    state.observed_patterns = [
        ObservedPattern(
            id="pattern-1",
            source_stage="cross_interview",
            pattern_kind=ObservedPatternKind.CODE_CO_OCCURRENCE,
            summary="Codes C1 and C2 co-occurred in the loaded corpus.",
            code_ids=["C1", "C2"],
            doc_ids=["d1"],
            application_ids=["A1", "A2"],
            count=1,
            total=4,
        )
    ]
    out = tmp_path / "patterns.md"
    ProjectExporter().export_markdown(state, str(out))

    content = Path(out).read_text()
    assert "## Observed Patterns" in content
    assert "Descriptive observed patterns only" in content
    assert "**Total patterns**: 1" in content
    assert "code_co_occurrence" in content
    assert "descriptive_only" in content
    assert "codes=C1,C2; docs=d1; applications=A1,A2" in content
    assert "not causal proof" in content


def test_export_markdown_includes_claim_relationships(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    state.claims.append(
        AnalyticClaim(
            id="claim-2",
            claim_kind=ClaimKind.PERSPECTIVE,
            source_stage="perspective",
            claim_text="AI should be governed in routine work.",
            scope=ClaimScope(participant_names=["Alice"]),
            origin_object_type="participant_perspective",
            origin_object_id="Alice",
            support_status=ClaimSupportStatus.SUPPORTED,
        )
    )
    state.claim_relationships = [
        ClaimRelationship(
            source_stage="cross_interview",
            source_claim_id="claim-1",
            target_claim_id="claim-2",
            relationship_type="synthesizes",
            rationale="Cross-case synthesis summarizes a participant-level claim.",
        )
    ]
    out = tmp_path / "claim_relationships.md"
    ProjectExporter().export_markdown(state, str(out))

    content = Path(out).read_text()
    assert "## Claim Relationships" in content
    assert "**Total claim relationships**: 1" in content
    assert "synthesizes" in content
    assert "Cross-case synthesis summarizes a participant-level claim." in content


def test_export_markdown_includes_abductive_candidates(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    state.abductive_explanations = [
        AbductiveCandidateExplanation(
            id="abductive-1",
            source_stage="abductive_synthesis",
            source_pattern_ids=["pattern-1"],
            explanation_text="Coordination friction may explain the pattern.",
            mechanism_summary="More handoffs create adoption friction.",
            rival_explanations=["Documentation artifacts could explain it."],
            observable_implications=["High-handoff teams show more friction."],
            evidence_gaps=["Need process evidence about handoffs."],
            confidence=0.4,
        )
    ]
    out = tmp_path / "abductive.md"
    ProjectExporter().export_markdown(state, str(out))

    content = Path(out).read_text()
    assert "## Abductive Candidate Explanations" in content
    assert "Provisional hypotheses only" in content
    assert "**Total candidates**: 1" in content
    assert "pattern-1" in content
    assert "Coordination friction may explain the pattern." in content
    assert "More handoffs create adoption friction." in content
    assert "Rivals: Documentation artifacts could explain it." in content
    assert "Observable implications: High-handoff teams show more friction." in content
    assert "Evidence gaps: Need process evidence about handoffs." in content
    assert "not causal proof" in content


def test_markdown_claim_rows_include_scope_and_boundary_columns(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    out = tmp_path / "claims.md"
    ProjectExporter().export_markdown(_claim_state(), str(out))

    content = Path(out).read_text()
    assert "| Kind | Stage | Scope | Corpus boundary | Support | Adjudication | Claim |" in content
    assert "| synthesis_finding | synthesis | corpus |" in content
    assert "Loaded document corpus only" in content
    assert "no CorpusScope recorded" in content


def test_markdown_claim_rows_do_not_rewrite_claim_text(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    original_text = state.claims[0].claim_text
    out = tmp_path / "claims.md"

    ProjectExporter().export_markdown(state, str(out))

    content = Path(out).read_text()
    assert state.claims[0].claim_text == original_text
    assert "| AI changes workflow. |" in content
    assert "Loaded document corpus only: AI changes workflow." not in content


def test_markdown_export_warns_when_claims_have_no_corpus_scope(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    out = tmp_path / "missing-scope.md"
    ProjectExporter().export_markdown(_claim_state(), str(out))

    content = Path(out).read_text()
    assert "## Corpus Scope" in content
    assert "No corpus scope is recorded" in content
    assert "bounded to the loaded documents" in content


def test_markdown_export_warns_when_population_has_no_sampling_frame(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    state.corpus_scope = CorpusScope(population="Operations teams in pilot clinics")
    out = tmp_path / "missing-sampling-frame.md"
    ProjectExporter().export_markdown(state, str(out))

    content = Path(out).read_text()
    assert "## Corpus Scope" in content
    assert "**Population**: Operations teams in pilot clinics" in content
    assert "population is recorded without a sampling frame" in content
    assert "defensible generalization boundary" in content


def test_markdown_export_omits_missing_scope_warning_without_claims(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    out = tmp_path / "minimal.md"
    ProjectExporter().export_markdown(ProjectState(name="Minimal"), str(out))

    content = Path(out).read_text()
    assert "## Corpus Scope" not in content
    assert "No corpus scope is recorded" not in content


def test_markdown_export_includes_corpus_scope(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _claim_state()
    state.corpus_scope = CorpusScope(
        phenomenon="AI-assisted workflow change",
        population="Operations teams in the pilot clinics",
        sampling_frame="Volunteer interviewees from two pilot clinics",
        inclusion_criteria=["Participated in the AI workflow pilot"],
        exclusion_criteria=["No direct workflow involvement"],
        notes="Bounded to the loaded transcript corpus.",
    )

    out = tmp_path / "scope.md"
    ProjectExporter().export_markdown(state, str(out))

    content = Path(out).read_text()
    assert "## Corpus Scope" in content
    assert "**Phenomenon**: AI-assisted workflow change" in content
    assert "**Population**: Operations teams in the pilot clinics" in content
    assert "**Sampling frame**: Volunteer interviewees from two pilot clinics" in content
    assert "- Participated in the AI workflow pilot" in content
    assert "- No direct workflow involvement" in content
    assert "Bounded to the loaded transcript corpus." in content


def test_markdown_recommendations_include_claim_trace_and_support_status(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = ProjectState(
        id="recommendation-trace",
        name="Recommendation Trace Study",
        synthesis=Synthesis(
            recommendations=[
                Recommendation(
                    title="Train staff",
                    description="Invest in staff training.",
                    priority="high",
                    supporting_themes=["C1"],
                )
            ],
        ),
        claims=[
            AnalyticClaim(
                id="claim-rec-1",
                claim_kind=ClaimKind.SYNTHESIS_FINDING,
                source_stage="synthesis",
                claim_text="Recommendation: Train staff. Invest in staff training.",
                scope=ClaimScope(corpus_level=True, code_ids=["C1"]),
                origin_object_type="synthesis_recommendation",
                origin_object_id="recommendation:0",
                support_status=ClaimSupportStatus.NEEDS_ANCHOR,
            )
        ],
    )

    out = tmp_path / "recommendations.md"
    ProjectExporter().export_markdown(state, str(out))

    content = Path(out).read_text()
    assert "## Recommendations" in content
    assert "### Train staff" in content
    assert "**Evidence status**: needs_anchor" in content
    assert "**Trace claim(s)**: claim-rec-1" in content
    assert "**Anchor counts**: 0 supporting, 0 contrary" in content
    assert "**Supporting themes**: C1" in content


def test_markdown_recommendations_without_claim_trace_are_marked_unverified(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = ProjectState(
        id="recommendation-untraced",
        name="Recommendation Untraced Study",
        synthesis=Synthesis(
            recommendations=[
                Recommendation(
                    title="Monitor narratives",
                    description="Create a monitoring process.",
                    priority="medium",
                )
            ],
        ),
    )

    out = tmp_path / "recommendations-untraced.md"
    ProjectExporter().export_markdown(state, str(out))

    content = Path(out).read_text()
    assert "### Monitor narratives" in content
    assert "no recommendation claim ledger entry found" in content
    assert "treat as unverified" in content
