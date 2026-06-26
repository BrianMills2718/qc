"""Versioned product-gate evidence package writer.

The package ties together reviewer/audit reports, baseline comparison artifacts,
review packets, review responses, and export manifests with hashes. It is an
evidence ledger for the finished-product gate, not a declaration that the gate
has passed.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


PRODUCT_GATE_PACKAGE_TYPE = "qualitative_coding.product_gate_evidence"
PRODUCT_GATE_PACKAGE_CAUTION = (
    "This package records product-gate evidence artifacts and hashes. It is not "
    "a SOTA, expert-parity, held-out validity, or finished-product pass claim "
    "unless every registered gate criterion has independent passing evidence."
)


ArtifactRole = Literal[
    "reviewer_report",
    "audit_report",
    "baseline_package",
    "baseline_comparison",
    "review_packet",
    "review_response",
    "export_manifest",
]


class ProductGateArtifact(BaseModel):
    """One artifact included in a product-gate evidence package."""

    model_config = ConfigDict(extra="forbid")

    role: ArtifactRole = Field(description="Role this artifact plays in the gate package")
    path: str = Field(description="Artifact path as supplied to the package writer")
    sha256: str = Field(description="SHA-256 hash of the artifact bytes")
    byte_size: int = Field(description="Artifact byte size")
    package_type: str | None = Field(
        default=None,
        description="JSON package_type value when the artifact is a recognized JSON package",
    )


class ProductGatePackage(BaseModel):
    """Versioned package of product-gate evidence artifact hashes."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(description="Product-gate package schema version")
    package_type: Literal["qualitative_coding.product_gate_evidence"] = Field(
        description="Package type discriminator"
    )
    project_id: str = Field(description="Project ID this evidence package belongs to")
    generated_at: str = Field(description="UTC ISO timestamp when the package was generated")
    artifacts: list[ProductGateArtifact] = Field(description="Hashed product-gate artifacts")
    caution: str = Field(
        default=PRODUCT_GATE_PACKAGE_CAUTION,
        description="Claim-discipline caution for this evidence package",
    )

    @model_validator(mode="after")
    def validate_artifacts(self) -> "ProductGatePackage":
        roles = [artifact.role for artifact in self.artifacts]
        if len(roles) != len(set(roles)):
            raise ValueError("Product-gate package artifact roles must be unique")
        if "reviewer_report" not in roles:
            raise ValueError("Product-gate package requires a reviewer_report artifact")
        return self


def build_product_gate_package(
    *,
    project_id: str,
    reviewer_report: Path,
    audit_report: Path | None = None,
    baseline_package: Path | None = None,
    baseline_comparison: Path | None = None,
    review_packet: Path | None = None,
    review_response: Path | None = None,
    export_manifest: Path | None = None,
) -> dict:
    """Build a product-gate evidence package from existing artifacts."""
    if not project_id:
        raise ValueError("project_id is required")

    artifacts = [
        _artifact(project_id, "reviewer_report", reviewer_report),
    ]
    optional_artifacts: list[tuple[ArtifactRole, Path | None]] = [
        ("audit_report", audit_report),
        ("baseline_package", baseline_package),
        ("baseline_comparison", baseline_comparison),
        ("review_packet", review_packet),
        ("review_response", review_response),
        ("export_manifest", export_manifest),
    ]
    artifacts.extend(
        _artifact(project_id, role, path)
        for role, path in optional_artifacts
        if path is not None
    )

    package = ProductGatePackage(
        schema_version=1,
        package_type=PRODUCT_GATE_PACKAGE_TYPE,
        project_id=project_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        artifacts=artifacts,
    )
    return package.model_dump(mode="json")


def build_product_gate_package_from_files(
    *,
    project_id: str,
    reviewer_report: Path,
    audit_report: Path | None = None,
    baseline_package: Path | None = None,
    baseline_comparison: Path | None = None,
    review_packet: Path | None = None,
    review_response: Path | None = None,
    export_manifest: Path | None = None,
) -> dict:
    """Compatibility wrapper for script callers."""
    return build_product_gate_package(
        project_id=project_id,
        reviewer_report=reviewer_report,
        audit_report=audit_report,
        baseline_package=baseline_package,
        baseline_comparison=baseline_comparison,
        review_packet=review_packet,
        review_response=review_response,
        export_manifest=export_manifest,
    )


def _artifact(project_id: str, role: ArtifactRole, path: Path) -> ProductGateArtifact:
    """Hash and validate one artifact."""
    if not path.exists():
        raise FileNotFoundError(f"{role} artifact does not exist: {path}")
    content = path.read_bytes()
    package_type = _validate_known_json_artifact(project_id, role, path)
    return ProductGateArtifact(
        role=role,
        path=str(path),
        sha256=hashlib.sha256(content).hexdigest(),
        byte_size=len(content),
        package_type=package_type,
    )


def _validate_known_json_artifact(
    project_id: str,
    role: ArtifactRole,
    path: Path,
) -> str | None:
    """Validate package type and project ID for known JSON package roles."""
    expected_types = {
        "baseline_package": "qualitative_coding.report_baseline_outputs",
        "baseline_comparison": "qualitative_coding.report_baseline_comparison",
        "review_packet": "qualitative_coding.report_review_packet",
        "review_response": "qualitative_coding.report_review_response",
    }
    expected_type = expected_types.get(role)
    if expected_type is None:
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    package_type = payload.get("package_type")
    if package_type != expected_type:
        raise ValueError(
            f"{role} artifact package_type must be {expected_type!r}, got {package_type!r}"
        )

    artifact_project_id = _project_id_for_role(role, payload)
    if artifact_project_id != project_id:
        raise ValueError(
            f"{role} artifact project_id must be {project_id!r}, got {artifact_project_id!r}"
        )
    return package_type


def _project_id_for_role(role: ArtifactRole, payload: dict) -> str | None:
    """Extract the project ID field for a known package role."""
    if role == "baseline_package":
        return payload.get("report_baseline_run", {}).get("project_id")
    if role == "baseline_comparison":
        return payload.get("comparison", {}).get("baseline_project_id")
    if role == "review_packet":
        return payload.get("review_packet", {}).get("baseline_project_id")
    if role == "review_response":
        return payload.get("review_response", {}).get("baseline_project_id")
    return None
