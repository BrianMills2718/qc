#!/usr/bin/env python3
"""Verify a D7 comparison artifact package against its local report file."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Literal, Sequence

from pydantic import BaseModel, Field, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


D7_ARTIFACT_VERIFICATION_CAVEAT = (
    "This verifies local D7 comparison artifact hashes and manifest/report "
    "consistency only; it is not held-out D7 evidence, live-baseline evidence, "
    "superiority evidence, methodological-validity evidence, or SOTA evidence."
)


class D7ComparisonArtifactManifest(BaseModel):
    """Permissive reader for D7 comparison artifact manifests."""

    schema_version: Literal[1] = Field(description="Artifact manifest schema version")
    artifact_type: Literal["qualitative_coding.d7_retrieval_comparison"] = Field(
        description="Artifact package type"
    )
    generated_at: str = Field(description="UTC artifact generation timestamp")
    project_id: str = Field(description="Project ID used for the comparison")
    project_name: str = Field(description="Project name used for the comparison")
    report_file: str = Field(description="Report file path relative to the manifest")
    report_sha256: str = Field(description="SHA-256 hash of report file bytes")
    input_hashes: dict[str, Any] = Field(
        description="Input hashes copied from report _meta.input_hashes"
    )
    command: dict[str, Any] = Field(
        description="Command provenance copied from report _meta.command"
    )
    claim_discipline: dict[str, Any] = Field(
        description="Claim-discipline caveats recorded by the artifact writer"
    )
    prompt_eval: dict[str, Any] = Field(
        description="Prompt-eval status recorded by the artifact writer"
    )


class D7ArtifactVerificationFailure(BaseModel):
    """One D7 artifact verification failure."""

    code: str = Field(description="Stable verification failure code")
    field: str = Field(description="Manifest or report field that failed")
    path: str | None = Field(default=None, description="Local file path when applicable")
    expected: Any | None = Field(default=None, description="Expected value")
    actual: Any | None = Field(default=None, description="Actual value")
    message: str = Field(description="Human-readable verification failure")


class D7ArtifactVerificationReport(BaseModel):
    """Verification report for one D7 comparison artifact package."""

    schema_version: Literal[1] = Field(description="Verification report schema version")
    package_type: Literal["qualitative_coding.d7_comparison_artifact_verification"] = (
        Field(description="Verification report package kind")
    )
    status: Literal["verified", "invalid"] = Field(
        description="Overall verification status"
    )
    artifact_type: str | None = Field(
        default=None,
        description="Artifact type from the manifest when available",
    )
    project_id: str | None = Field(
        default=None,
        description="Project ID from the manifest when available",
    )
    manifest_path: str = Field(description="Manifest path checked by the verifier")
    report_path: str | None = Field(
        default=None,
        description="Report path checked by the verifier when available",
    )
    checked_report_count: int = Field(description="Number of report files read")
    failure_count: int = Field(description="Number of verification failures")
    failures: list[D7ArtifactVerificationFailure] = Field(
        description="Structured verification failures"
    )
    caveat: str = Field(description="Claim-discipline caveat for verification")


def main(argv: Sequence[str] | None = None) -> int:
    """Verify a D7 comparison artifact and print a JSON report."""
    parser = argparse.ArgumentParser(description="Verify a D7 comparison artifact")
    parser.add_argument(
        "artifact",
        type=Path,
        help="D7 comparison artifact directory or manifest.json path",
    )
    args = parser.parse_args(argv)

    report = verify_d7_comparison_artifact(args.artifact)
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "verified" else 1


def verify_d7_comparison_artifact(path: Path) -> D7ArtifactVerificationReport:
    """Verify a D7 comparison artifact directory or manifest path."""
    manifest_path = _manifest_path_for(path)
    raw_manifest, load_failures = _load_manifest_payload(manifest_path)
    if load_failures:
        return _verification_report(
            artifact_type=None,
            project_id=None,
            manifest_path=manifest_path,
            report_path=None,
            checked_report_count=0,
            failures=load_failures,
        )

    assert raw_manifest is not None
    try:
        manifest = D7ComparisonArtifactManifest.model_validate(raw_manifest)
    except ValidationError as exc:
        return _verification_report(
            artifact_type=(
                raw_manifest.get("artifact_type")
                if isinstance(raw_manifest.get("artifact_type"), str)
                else None
            ),
            project_id=(
                raw_manifest.get("project_id")
                if isinstance(raw_manifest.get("project_id"), str)
                else None
            ),
            manifest_path=manifest_path,
            report_path=None,
            checked_report_count=0,
            failures=[
                D7ArtifactVerificationFailure(
                    code="invalid_manifest_shape",
                    field="manifest",
                    path=str(manifest_path),
                    message=f"Manifest payload has invalid shape: {exc}",
                )
            ],
        )

    report_path = manifest_path.parent / manifest.report_file
    failures: list[D7ArtifactVerificationFailure] = []
    checked_report_count = 0

    report_payload: dict[str, Any] | None = None
    try:
        report_bytes = report_path.read_bytes()
        checked_report_count = 1
    except OSError as exc:
        failures.append(
            D7ArtifactVerificationFailure(
                code="report_file_missing",
                field="report_file",
                path=str(report_path),
                expected=manifest.report_file,
                message=f"Report file could not be read: {exc}",
            )
        )
    else:
        actual_report_hash = hashlib.sha256(report_bytes).hexdigest()
        if actual_report_hash != manifest.report_sha256:
            failures.append(
                D7ArtifactVerificationFailure(
                    code="report_sha256_mismatch",
                    field="report_sha256",
                    path=str(report_path),
                    expected=manifest.report_sha256,
                    actual=actual_report_hash,
                    message="Report SHA-256 does not match manifest",
                )
            )
        report_payload = _load_report_payload(report_bytes, report_path, failures)

    _verify_manifest_caveats(manifest, failures)
    if report_payload is not None:
        _verify_report_metadata(manifest, report_payload, report_path, failures)

    return _verification_report(
        artifact_type=manifest.artifact_type,
        project_id=manifest.project_id,
        manifest_path=manifest_path,
        report_path=report_path,
        checked_report_count=checked_report_count,
        failures=failures,
    )


def _manifest_path_for(path: Path) -> Path:
    """Resolve an artifact directory or manifest path to a manifest path."""
    return path / "manifest.json" if path.is_dir() else path


def _load_manifest_payload(
    manifest_path: Path,
) -> tuple[dict[str, Any] | None, list[D7ArtifactVerificationFailure]]:
    """Load a manifest payload and return structured load failures."""
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, [
            D7ArtifactVerificationFailure(
                code="manifest_file_unreadable",
                field="manifest",
                path=str(manifest_path),
                message=f"Manifest file could not be read: {exc}",
            )
        ]
    except json.JSONDecodeError as exc:
        return None, [
            D7ArtifactVerificationFailure(
                code="manifest_json_invalid",
                field="manifest",
                path=str(manifest_path),
                message=f"Manifest file is not valid JSON: {exc}",
            )
        ]
    if not isinstance(raw, dict):
        return None, [
            D7ArtifactVerificationFailure(
                code="invalid_manifest_payload",
                field="manifest",
                path=str(manifest_path),
                message="Manifest payload must be a JSON object",
            )
        ]
    return raw, []


def _load_report_payload(
    report_bytes: bytes,
    report_path: Path,
    failures: list[D7ArtifactVerificationFailure],
) -> dict[str, Any] | None:
    """Load report JSON and append structured failures when it is invalid."""
    try:
        raw_report = json.loads(report_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        failures.append(
            D7ArtifactVerificationFailure(
                code="report_utf8_invalid",
                field="report_file",
                path=str(report_path),
                message=f"Report file is not valid UTF-8: {exc}",
            )
        )
        return None
    except json.JSONDecodeError as exc:
        failures.append(
            D7ArtifactVerificationFailure(
                code="report_json_invalid",
                field="report_file",
                path=str(report_path),
                message=f"Report file is not valid JSON: {exc}",
            )
        )
        return None
    if not isinstance(raw_report, dict):
        failures.append(
            D7ArtifactVerificationFailure(
                code="invalid_report_payload",
                field="report",
                path=str(report_path),
                message="Report payload must be a JSON object",
            )
        )
        return None
    return raw_report


def _verify_manifest_caveats(
    manifest: D7ComparisonArtifactManifest,
    failures: list[D7ArtifactVerificationFailure],
) -> None:
    """Verify manifest caveats required by D7 claim discipline."""
    prompt_eval_status = manifest.prompt_eval.get("status")
    if prompt_eval_status != "not_run":
        failures.append(
            D7ArtifactVerificationFailure(
                code="prompt_eval_status_invalid",
                field="prompt_eval.status",
                expected="not_run",
                actual=prompt_eval_status,
                message="Manifest prompt_eval status must be not_run",
            )
        )
    caveat = manifest.claim_discipline.get("caveat")
    if not isinstance(caveat, str) or "not held-out D7 evidence" not in caveat:
        failures.append(
            D7ArtifactVerificationFailure(
                code="claim_discipline_caveat_missing",
                field="claim_discipline.caveat",
                actual=caveat,
                message="Manifest claim caveat must state this is not held-out D7 evidence",
            )
        )


def _verify_report_metadata(
    manifest: D7ComparisonArtifactManifest,
    report_payload: dict[str, Any],
    report_path: Path,
    failures: list[D7ArtifactVerificationFailure],
) -> None:
    """Verify manifest metadata copied from report _meta."""
    meta = report_payload.get("_meta")
    if not isinstance(meta, dict):
        failures.append(
            D7ArtifactVerificationFailure(
                code="report_meta_missing",
                field="_meta",
                path=str(report_path),
                message="Report is missing _meta object",
            )
        )
        return
    input_hashes = meta.get("input_hashes")
    if input_hashes != manifest.input_hashes:
        failures.append(
            D7ArtifactVerificationFailure(
                code="input_hashes_mismatch",
                field="_meta.input_hashes",
                path=str(report_path),
                expected=manifest.input_hashes,
                actual=input_hashes,
                message="Report input hashes do not match manifest input hashes",
            )
        )
    command = meta.get("command")
    if command != manifest.command:
        failures.append(
            D7ArtifactVerificationFailure(
                code="command_mismatch",
                field="_meta.command",
                path=str(report_path),
                expected=manifest.command,
                actual=command,
                message="Report command provenance does not match manifest command",
            )
        )


def _verification_report(
    *,
    artifact_type: str | None,
    project_id: str | None,
    manifest_path: Path,
    report_path: Path | None,
    checked_report_count: int,
    failures: list[D7ArtifactVerificationFailure],
) -> D7ArtifactVerificationReport:
    """Build a D7 artifact verification report."""
    return D7ArtifactVerificationReport(
        schema_version=1,
        package_type="qualitative_coding.d7_comparison_artifact_verification",
        status="verified" if not failures else "invalid",
        artifact_type=artifact_type,
        project_id=project_id,
        manifest_path=str(manifest_path),
        report_path=str(report_path) if report_path is not None else None,
        checked_report_count=checked_report_count,
        failure_count=len(failures),
        failures=failures,
        caveat=D7_ARTIFACT_VERIFICATION_CAVEAT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
