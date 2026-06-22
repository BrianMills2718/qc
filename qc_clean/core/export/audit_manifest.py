"""Hash manifest support for exported qualitative-coding artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, Sequence

from pydantic import BaseModel, Field, ValidationError

from qc_clean.schemas.domain import ProjectState


ExportFormat = Literal["json", "csv", "markdown", "qdpx"]
VerificationStatus = Literal["verified", "invalid"]
ProjectStateHashStatus = Literal["verified", "invalid", "not_checked"]

EXPORT_AUDIT_CAVEAT = (
    "This manifest records local artifact hashes for integrity/provenance. It is "
    "not a complete tamper-evident audit log, not cryptographic signing, and not "
    "evidence that the analysis is methodologically valid."
)


class ExportAuditArtifact(BaseModel):
    """One hashed export artifact entry."""

    path: str = Field(description="Artifact path relative to the manifest base when possible")
    size_bytes: int = Field(description="Artifact size in bytes")
    sha256: str = Field(description="SHA-256 hash of the artifact bytes")


class ExportAuditManifest(BaseModel):
    """Versioned hash manifest for project export artifacts."""

    schema_version: Literal[1] = Field(description="Export audit manifest schema version")
    package_type: Literal["export_audit_manifest"] = Field(description="Manifest package kind")
    export_format: ExportFormat = Field(description="Export format represented by the artifacts")
    project_id: str = Field(description="Project ID used to build the export")
    project_name: str = Field(description="Project name used to build the export")
    hash_algorithm: Literal["sha256"] = Field(description="Hash algorithm used for all hashes")
    project_state_sha256: str = Field(description="SHA-256 of the source ProjectState JSON")
    artifact_count: int = Field(description="Number of artifact files in the manifest")
    artifacts: list[ExportAuditArtifact] = Field(description="Hashed export artifact entries")
    manifest_sha256: str = Field(description="SHA-256 of this manifest with this field blanked")
    caveat: str = Field(description="Claim-discipline caveat for the manifest")


class ExportAuditVerificationFailure(BaseModel):
    """One export audit manifest verification failure."""

    code: str = Field(description="Stable verification failure code")
    field: str = Field(description="Manifest field or artifact property that failed")
    path: str | None = Field(default=None, description="Artifact path when applicable")
    expected: str | None = Field(default=None, description="Expected value from the manifest")
    actual: str | None = Field(default=None, description="Actual recomputed value")
    message: str = Field(description="Human-readable verification failure")


class ExportAuditVerificationReport(BaseModel):
    """Verification report for an export audit manifest."""

    schema_version: Literal[1] = Field(description="Verification report schema version")
    package_type: Literal["export_audit_verification"] = Field(
        description="Verification report package kind"
    )
    status: VerificationStatus = Field(description="Overall verification status")
    export_format: ExportFormat | None = Field(
        default=None,
        description="Export format from the manifest when available",
    )
    project_id: str | None = Field(default=None, description="Project ID from the manifest")
    project_name: str | None = Field(default=None, description="Project name from the manifest")
    manifest_self_hash_status: VerificationStatus = Field(
        description="Whether the manifest self-hash matched"
    )
    project_state_hash_status: ProjectStateHashStatus = Field(
        description="Whether the optional project-state hash check matched"
    )
    artifact_count: int = Field(description="Number of artifacts listed in the manifest")
    checked_artifact_count: int = Field(description="Number of artifact files read for checking")
    failure_count: int = Field(description="Number of verification failures")
    failures: list[ExportAuditVerificationFailure] = Field(
        description="Structured verification failures"
    )
    caveat: str = Field(description="Claim-discipline caveat for verification")


def build_export_audit_manifest(
    state: ProjectState,
    *,
    export_format: ExportFormat,
    artifact_paths: Sequence[str | Path],
    base_dir: str | Path | None = None,
) -> ExportAuditManifest:
    """Build a deterministic hash manifest for existing export artifacts."""
    if not artifact_paths:
        raise ValueError("At least one export artifact path is required")

    base = Path(base_dir).resolve() if base_dir is not None else None
    artifacts = [
        _artifact_entry(Path(path), base_dir=base)
        for path in artifact_paths
    ]
    artifacts.sort(key=lambda artifact: artifact.path)

    manifest = ExportAuditManifest(
        schema_version=1,
        package_type="export_audit_manifest",
        export_format=export_format,
        project_id=state.id,
        project_name=state.name,
        hash_algorithm="sha256",
        project_state_sha256=_sha256_jsonable(state.model_dump(mode="json")),
        artifact_count=len(artifacts),
        artifacts=artifacts,
        manifest_sha256="",
        caveat=EXPORT_AUDIT_CAVEAT,
    )
    manifest.manifest_sha256 = _sha256_jsonable(manifest.model_dump(mode="json"))
    return manifest


def write_export_audit_manifest(
    manifest: ExportAuditManifest,
    output_file: str | Path,
) -> str:
    """Write an export audit manifest to JSON and return the output path."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path)


def load_export_audit_manifest(path: str | Path) -> ExportAuditManifest:
    """Load an export audit manifest JSON file."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Export audit manifest '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Export audit manifest '{path}' is not valid JSON: {exc}") from exc
    try:
        return ExportAuditManifest.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Export audit manifest '{path}' has invalid shape: {exc}") from exc


def verify_export_audit_manifest_payload(
    payload: object,
    *,
    base_dir: str | Path | None = None,
    state: ProjectState | None = None,
) -> ExportAuditVerificationReport:
    """Verify an export audit manifest payload against local files and state."""
    raw_payload = _payload_to_dict(payload)
    if raw_payload is None:
        failure = ExportAuditVerificationFailure(
            code="invalid_manifest_payload",
            field="manifest",
            message="Manifest payload must be a JSON object",
        )
        return _verification_report(
            export_format=None,
            project_id=None,
            project_name=None,
            manifest_self_hash_status="invalid",
            project_state_hash_status="not_checked",
            artifact_count=0,
            checked_artifact_count=0,
            failures=[failure],
        )

    try:
        manifest = ExportAuditManifest.model_validate(raw_payload)
    except ValidationError as exc:
        failure = ExportAuditVerificationFailure(
            code="invalid_manifest_shape",
            field="manifest",
            message=f"Manifest payload has invalid shape: {exc}",
        )
        return _verification_report(
            export_format=None,
            project_id=raw_payload.get("project_id") if isinstance(raw_payload.get("project_id"), str) else None,
            project_name=(
                raw_payload.get("project_name")
                if isinstance(raw_payload.get("project_name"), str)
                else None
            ),
            manifest_self_hash_status="invalid",
            project_state_hash_status="not_checked",
            artifact_count=0,
            checked_artifact_count=0,
            failures=[failure],
        )

    base = Path(base_dir).resolve() if base_dir is not None else None
    failures: list[ExportAuditVerificationFailure] = []

    actual_manifest_hash = _manifest_payload_hash(raw_payload)
    manifest_self_hash_status: VerificationStatus = "verified"
    if actual_manifest_hash != manifest.manifest_sha256:
        manifest_self_hash_status = "invalid"
        failures.append(
            ExportAuditVerificationFailure(
                code="manifest_sha256_mismatch",
                field="manifest_sha256",
                expected=manifest.manifest_sha256,
                actual=actual_manifest_hash,
                message="Manifest self-hash does not match manifest content",
            )
        )

    project_state_hash_status: ProjectStateHashStatus = "not_checked"
    if state is not None:
        actual_state_hash = _sha256_jsonable(state.model_dump(mode="json"))
        project_state_hash_status = "verified"
        if actual_state_hash != manifest.project_state_sha256:
            project_state_hash_status = "invalid"
            failures.append(
                ExportAuditVerificationFailure(
                    code="project_state_sha256_mismatch",
                    field="project_state_sha256",
                    expected=manifest.project_state_sha256,
                    actual=actual_state_hash,
                    message="Current project state hash does not match manifest source hash",
                )
            )

    checked_artifact_count = 0
    for artifact in manifest.artifacts:
        artifact_path = _resolve_manifest_artifact_path(artifact.path, base_dir=base)
        if not artifact_path.exists():
            failures.append(
                ExportAuditVerificationFailure(
                    code="artifact_missing",
                    field="path",
                    path=artifact.path,
                    expected="file exists",
                    actual="missing",
                    message="Manifest artifact does not exist",
                )
            )
            continue
        if not artifact_path.is_file():
            failures.append(
                ExportAuditVerificationFailure(
                    code="artifact_not_file",
                    field="path",
                    path=artifact.path,
                    expected="file",
                    actual="not_file",
                    message="Manifest artifact path is not a file",
                )
            )
            continue

        checked_artifact_count += 1
        actual_size = artifact_path.stat().st_size
        if actual_size != artifact.size_bytes:
            failures.append(
                ExportAuditVerificationFailure(
                    code="artifact_size_mismatch",
                    field="size_bytes",
                    path=artifact.path,
                    expected=str(artifact.size_bytes),
                    actual=str(actual_size),
                    message="Artifact size does not match manifest",
                )
            )
        actual_sha = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if actual_sha != artifact.sha256:
            failures.append(
                ExportAuditVerificationFailure(
                    code="artifact_sha256_mismatch",
                    field="sha256",
                    path=artifact.path,
                    expected=artifact.sha256,
                    actual=actual_sha,
                    message="Artifact SHA-256 does not match manifest",
                )
            )

    return _verification_report(
        export_format=manifest.export_format,
        project_id=manifest.project_id,
        project_name=manifest.project_name,
        manifest_self_hash_status=manifest_self_hash_status,
        project_state_hash_status=project_state_hash_status,
        artifact_count=manifest.artifact_count,
        checked_artifact_count=checked_artifact_count,
        failures=failures,
    )


def _artifact_entry(path: Path, *, base_dir: Path | None) -> ExportAuditArtifact:
    """Build one manifest artifact entry from an existing file path."""
    resolved = path.resolve()
    if not resolved.exists():
        raise ValueError(f"Export artifact does not exist: {path}")
    if not resolved.is_file():
        raise ValueError(f"Export artifact is not a file: {path}")

    return ExportAuditArtifact(
        path=_manifest_path(resolved, original=path, base_dir=base_dir),
        size_bytes=resolved.stat().st_size,
        sha256=hashlib.sha256(resolved.read_bytes()).hexdigest(),
    )


def _manifest_path(path: Path, *, original: Path, base_dir: Path | None) -> str:
    """Return a stable manifest path for one artifact."""
    if base_dir is not None:
        try:
            return path.relative_to(base_dir).as_posix()
        except ValueError:
            return path.as_posix()
    return original.as_posix()


def _resolve_manifest_artifact_path(path: str, *, base_dir: Path | None) -> Path:
    """Resolve a manifest artifact path for local verification."""
    artifact_path = Path(path)
    if artifact_path.is_absolute() or base_dir is None:
        return artifact_path
    return base_dir / artifact_path


def _payload_to_dict(payload: object) -> dict[str, object] | None:
    """Return a JSON-like dict from a manifest payload object."""
    if isinstance(payload, ExportAuditManifest):
        return payload.model_dump(mode="json")
    if isinstance(payload, dict):
        return dict(payload)
    return None


def _manifest_payload_hash(payload: dict[str, object]) -> str:
    """Return the expected self-hash for a manifest payload."""
    manifest_without_hash = dict(payload)
    manifest_without_hash["manifest_sha256"] = ""
    return _sha256_jsonable(manifest_without_hash)


def _verification_report(
    *,
    export_format: ExportFormat | None,
    project_id: str | None,
    project_name: str | None,
    manifest_self_hash_status: VerificationStatus,
    project_state_hash_status: ProjectStateHashStatus,
    artifact_count: int,
    checked_artifact_count: int,
    failures: list[ExportAuditVerificationFailure],
) -> ExportAuditVerificationReport:
    """Build a verification report with consistent status and caveat."""
    return ExportAuditVerificationReport(
        schema_version=1,
        package_type="export_audit_verification",
        status="invalid" if failures else "verified",
        export_format=export_format,
        project_id=project_id,
        project_name=project_name,
        manifest_self_hash_status=manifest_self_hash_status,
        project_state_hash_status=project_state_hash_status,
        artifact_count=artifact_count,
        checked_artifact_count=checked_artifact_count,
        failure_count=len(failures),
        failures=failures,
        caveat=(
            "Export manifest verification checks local hashes only; it is not a "
            "signed or append-only audit log and not methodological validity evidence."
        ),
    )


def _sha256_jsonable(value: object) -> str:
    """Return a deterministic SHA-256 hash for a JSON-serializable value."""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
