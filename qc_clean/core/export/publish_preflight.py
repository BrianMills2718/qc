"""Strict local preflight for export publish/handoff workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from qc_clean.core.export.audit_manifest import (
    ExportAuditVerificationFailure,
    ExportAuditVerificationReport,
    load_export_audit_manifest,
    verify_export_audit_manifest_payload,
)
from qc_clean.schemas.domain import ProjectState


PublishPreflightStatus = Literal["pass", "fail"]

PUBLISH_PREFLIGHT_CAVEAT = (
    "Export publish preflight is a local integrity/handoff gate only; it is not "
    "signing, not append-only logging, not a complete tamper-evident audit "
    "substrate, and not methodological validity evidence."
)


class ExportPublishPreflightReport(BaseModel):
    """Report for a strict export publish/handoff preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["export_publish_preflight"] = Field(
        description="Preflight report package kind"
    )
    status: PublishPreflightStatus = Field(description="Overall preflight status")
    manifest_path: str = Field(description="Manifest path checked by the preflight")
    verification: ExportAuditVerificationReport | None = Field(
        default=None,
        description="Export-audit verification report when a manifest could be loaded",
    )
    failure_count: int = Field(description="Number of preflight failures")
    failures: list[ExportAuditVerificationFailure] = Field(
        description="Verification or manifest-loading failures"
    )
    caveat: str = Field(description="Claim-discipline caveat for the preflight")


def run_export_publish_preflight(
    manifest_path: str | Path,
    *,
    base_dir: str | Path | None = None,
    state: ProjectState | None = None,
) -> ExportPublishPreflightReport:
    """Run strict local export publish preflight against a required manifest."""
    path = Path(manifest_path)
    if not path.exists():
        failure = ExportAuditVerificationFailure(
            code="manifest_missing",
            field="manifest_path",
            path=str(path),
            expected="file exists",
            actual="missing",
            message="Export publish preflight requires an existing export-audit manifest",
        )
        return _preflight_report(
            manifest_path=path,
            verification=None,
            failures=[failure],
        )

    try:
        manifest = load_export_audit_manifest(path)
    except ValueError as exc:
        failure = ExportAuditVerificationFailure(
            code="manifest_invalid",
            field="manifest",
            path=str(path),
            message=str(exc),
        )
        return _preflight_report(
            manifest_path=path,
            verification=None,
            failures=[failure],
        )

    verification = verify_export_audit_manifest_payload(
        manifest,
        base_dir=base_dir if base_dir is not None else path.parent,
        state=state,
    )
    return _preflight_report(
        manifest_path=path,
        verification=verification,
        failures=list(verification.failures),
    )


def _preflight_report(
    *,
    manifest_path: Path,
    verification: ExportAuditVerificationReport | None,
    failures: list[ExportAuditVerificationFailure],
) -> ExportPublishPreflightReport:
    """Build a preflight report with consistent status and caveat."""
    return ExportPublishPreflightReport(
        schema_version=1,
        package_type="export_publish_preflight",
        status="fail" if failures else "pass",
        manifest_path=str(manifest_path),
        verification=verification,
        failure_count=len(failures),
        failures=failures,
        caveat=PUBLISH_PREFLIGHT_CAVEAT,
    )
