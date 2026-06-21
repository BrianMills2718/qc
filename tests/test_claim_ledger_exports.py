"""Export coverage for the INV-9 claim ledger."""

import csv
from pathlib import Path

from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimKind,
    ClaimScope,
    ClaimSupportStatus,
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


def test_markdown_export_includes_claim_ledger_summary(tmp_path):
    from qc_clean.core.export.data_exporter import ProjectExporter

    out = tmp_path / "claims.md"
    ProjectExporter().export_markdown(_claim_state(), str(out))

    content = Path(out).read_text()
    assert "## Claim Ledger" in content
    assert "**Total claims**: 1" in content
    assert "synthesis_finding" in content
    assert "AI changes workflow." in content
