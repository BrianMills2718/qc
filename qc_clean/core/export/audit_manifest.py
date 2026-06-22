"""Hash manifest support for exported qualitative-coding artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, Sequence

from pydantic import BaseModel, Field

from qc_clean.schemas.domain import ProjectState


ExportFormat = Literal["json", "csv", "markdown", "qdpx"]

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


def _sha256_jsonable(value: object) -> str:
    """Return a deterministic SHA-256 hash for a JSON-serializable value."""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
