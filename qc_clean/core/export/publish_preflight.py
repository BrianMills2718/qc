"""Strict local preflight for export publish/handoff workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from qc_clean.core.export.audit_manifest import (
    ExportAuditManifest,
    ExportAuditVerificationFailure,
    ExportAuditVerificationReport,
    load_export_audit_manifest,
    _resolve_manifest_artifact_path,
    verify_export_audit_manifest_payload,
)
from qc_clean.core.scope_lint import ScopePhrasingLintReport, lint_scope_phrasing
from qc_clean.schemas.domain import ProjectState


PublishPreflightStatus = Literal["pass", "fail"]
ScopeLintPreflightStatus = Literal["not_run", "pass", "warn"]
SCOPE_LINT_TEXT_SUFFIXES = frozenset({".md", ".markdown", ".txt"})

PUBLISH_PREFLIGHT_CAVEAT = (
    "Export publish preflight is a local integrity/handoff gate only; it is not "
    "signing, not append-only logging, not a complete tamper-evident audit "
    "substrate, and not methodological validity evidence. Optional scope lint "
    "is report discipline only; it is not sampling adequacy evidence."
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
    scope_lint_status: ScopeLintPreflightStatus = Field(
        default="not_run",
        description="Optional corpus-scope phrasing lint status",
    )
    scope_lint_reports: list[ScopePhrasingLintReport] = Field(
        default_factory=list,
        description="Scope-phrasing lint reports for checked textual artifacts",
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
    scope_lint: bool = False,
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
    failures = list(verification.failures)
    scope_lint_status: ScopeLintPreflightStatus = "not_run"
    scope_lint_reports: list[ScopePhrasingLintReport] = []
    if scope_lint:
        if state is None:
            failures.append(
                ExportAuditVerificationFailure(
                    code="scope_lint_requires_project_state",
                    field="scope_lint",
                    path=str(path),
                    expected="project state supplied",
                    actual="missing",
                    message="Scope lint requires a loaded ProjectState",
                )
            )
        elif verification.status == "verified":
            scope_lint_status, scope_lint_reports, scope_lint_failures = _scope_lint_artifacts(
                manifest,
                base_dir=base_dir if base_dir is not None else path.parent,
                state=state,
            )
            failures.extend(scope_lint_failures)
    return _preflight_report(
        manifest_path=path,
        verification=verification,
        failures=failures,
        scope_lint_status=scope_lint_status,
        scope_lint_reports=scope_lint_reports,
    )


def _preflight_report(
    *,
    manifest_path: Path,
    verification: ExportAuditVerificationReport | None,
    failures: list[ExportAuditVerificationFailure],
    scope_lint_status: ScopeLintPreflightStatus = "not_run",
    scope_lint_reports: list[ScopePhrasingLintReport] | None = None,
) -> ExportPublishPreflightReport:
    """Build a preflight report with consistent status and caveat."""
    return ExportPublishPreflightReport(
        schema_version=1,
        package_type="export_publish_preflight",
        status="fail" if failures else "pass",
        manifest_path=str(manifest_path),
        verification=verification,
        scope_lint_status=scope_lint_status,
        scope_lint_reports=scope_lint_reports or [],
        failure_count=len(failures),
        failures=failures,
        caveat=PUBLISH_PREFLIGHT_CAVEAT,
    )


def _scope_lint_artifacts(
    manifest: ExportAuditManifest,
    *,
    base_dir: str | Path,
    state: ProjectState,
) -> tuple[
    ScopeLintPreflightStatus,
    list[ScopePhrasingLintReport],
    list[ExportAuditVerificationFailure],
]:
    """Run scope phrasing lint on manifest artifacts that are textual reports."""
    base = Path(base_dir).resolve()
    reports: list[ScopePhrasingLintReport] = []
    failures: list[ExportAuditVerificationFailure] = []
    for artifact in manifest.artifacts:
        if not _is_scope_lint_text_artifact(artifact.path):
            continue
        artifact_path = _resolve_manifest_artifact_path(artifact.path, base_dir=base)
        try:
            text = artifact_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            failures.append(
                ExportAuditVerificationFailure(
                    code="scope_lint_artifact_read_failed",
                    field="scope_lint",
                    path=artifact.path,
                    expected="readable UTF-8 text artifact",
                    actual=type(exc).__name__,
                    message=f"Scope lint could not read textual artifact: {exc}",
                )
            )
            continue
        report = lint_scope_phrasing(state, text, source=artifact.path)
        reports.append(report)
        for warning in report.warnings:
            failures.append(
                ExportAuditVerificationFailure(
                    code=f"scope_lint_{warning.code}",
                    field="scope_lint",
                    path=warning.source,
                    expected="no risky population-generalizing phrasing under current corpus scope",
                    actual=warning.matched_text,
                    message=(
                        f"Scope lint warning on line {warning.line_number}: "
                        f"{warning.message}"
                    ),
                )
            )

    status: ScopeLintPreflightStatus = "warn" if failures else "pass"
    return status, reports, failures


def _is_scope_lint_text_artifact(path: str) -> bool:
    """Return whether a manifest artifact is a text report for scope linting."""
    return Path(path).suffix.lower() in SCOPE_LINT_TEXT_SUFFIXES
