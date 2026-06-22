"""Export coverage for the INV-9 claim ledger."""

import csv
import json
from pathlib import Path

from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimKind,
    ClaimScope,
    ClaimSupportStatus,
    CorpusScope,
    ProjectState,
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
