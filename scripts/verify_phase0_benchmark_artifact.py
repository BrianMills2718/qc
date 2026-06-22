#!/usr/bin/env python3
"""Verify a Phase 0 benchmark artifact package against local files."""

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


PHASE0_ARTIFACT_VERIFICATION_CAVEAT = (
    "This verifies local Phase 0 artifact hashes and manifest/scorecard/timing "
    "consistency only; it is not methodological-validity evidence, superiority "
    "evidence, parity evidence, timing evidence, or SOTA evidence."
)


class Phase0BenchmarkArtifactManifest(BaseModel):
    """Permissive reader for Phase 0 benchmark artifact manifests."""

    schema_version: Literal[1] = Field(description="Artifact manifest schema version")
    artifact_type: Literal["qualitative_coding.phase0_scorecard"] = Field(
        description="Artifact package type"
    )
    generated_at: str = Field(description="UTC artifact generation timestamp")
    project_id: str = Field(description="Project ID used for the scorecard")
    project_name: str = Field(description="Project name used for the scorecard")
    phase: int = Field(description="Scorecard phase number")
    scorecard_file: str = Field(description="Scorecard path relative to the manifest")
    scorecard_sha256: str = Field(description="SHA-256 hash of scorecard file bytes")
    timing_file: str = Field(description="Timing artifact path relative to the manifest")
    timing_sha256: str = Field(description="SHA-256 hash of timing file bytes")
    input_hashes: dict[str, Any] = Field(
        description="Input hashes copied from scorecard _meta.input_hashes"
    )
    run_configuration_hashes: dict[str, Any] = Field(
        description="Run configuration hashes copied from scorecard _meta"
    )
    claim_discipline: Any = Field(
        description="Claim-discipline caveat copied from scorecard _meta.claims"
    )
    prompt_eval: dict[str, Any] = Field(
        description="Prompt-eval status recorded by the artifact writer"
    )
    command: dict[str, Any] = Field(description="Command provenance for the run")


class Phase0ArtifactVerificationFailure(BaseModel):
    """One Phase 0 artifact verification failure."""

    code: str = Field(description="Stable verification failure code")
    field: str = Field(description="Manifest, scorecard, or timing field that failed")
    path: str | None = Field(default=None, description="Local file path when applicable")
    expected: Any | None = Field(default=None, description="Expected value")
    actual: Any | None = Field(default=None, description="Actual value")
    message: str = Field(description="Human-readable verification failure")


class Phase0ArtifactVerificationReport(BaseModel):
    """Verification report for one Phase 0 benchmark artifact package."""

    schema_version: Literal[1] = Field(description="Verification report schema version")
    package_type: Literal["qualitative_coding.phase0_benchmark_artifact_verification"] = (
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
    scorecard_path: str | None = Field(
        default=None,
        description="Scorecard path checked by the verifier when available",
    )
    timing_path: str | None = Field(
        default=None,
        description="Timing artifact path checked by the verifier when available",
    )
    checked_scorecard_count: int = Field(description="Number of scorecard files read")
    checked_timing_count: int = Field(description="Number of timing files read")
    failure_count: int = Field(description="Number of verification failures")
    failures: list[Phase0ArtifactVerificationFailure] = Field(
        description="Structured verification failures"
    )
    caveat: str = Field(description="Claim-discipline caveat for verification")


def main(argv: Sequence[str] | None = None) -> int:
    """Verify a Phase 0 benchmark artifact and print a JSON report."""
    parser = argparse.ArgumentParser(description="Verify a Phase 0 benchmark artifact")
    parser.add_argument(
        "artifact",
        type=Path,
        help="Phase 0 artifact directory or manifest.json path",
    )
    args = parser.parse_args(argv)

    report = verify_phase0_benchmark_artifact(args.artifact)
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "verified" else 1


def verify_phase0_benchmark_artifact(path: Path) -> Phase0ArtifactVerificationReport:
    """Verify a Phase 0 benchmark artifact directory or manifest path."""
    manifest_path = _manifest_path_for(path)
    raw_manifest, load_failures = _load_manifest_payload(manifest_path)
    if load_failures:
        return _verification_report(
            artifact_type=None,
            project_id=None,
            manifest_path=manifest_path,
            scorecard_path=None,
            timing_path=None,
            checked_scorecard_count=0,
            checked_timing_count=0,
            failures=load_failures,
        )

    assert raw_manifest is not None
    try:
        manifest = Phase0BenchmarkArtifactManifest.model_validate(raw_manifest)
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
            scorecard_path=None,
            timing_path=None,
            checked_scorecard_count=0,
            checked_timing_count=0,
            failures=[
                Phase0ArtifactVerificationFailure(
                    code="invalid_manifest_shape",
                    field="manifest",
                    path=str(manifest_path),
                    message=f"Manifest payload has invalid shape: {exc}",
                )
            ],
        )

    scorecard_path = manifest_path.parent / manifest.scorecard_file
    timing_path = manifest_path.parent / manifest.timing_file
    failures: list[Phase0ArtifactVerificationFailure] = []
    checked_scorecard_count = 0
    checked_timing_count = 0

    scorecard_payload: dict[str, Any] | None = None
    try:
        scorecard_bytes = scorecard_path.read_bytes()
        checked_scorecard_count = 1
    except OSError as exc:
        failures.append(
            Phase0ArtifactVerificationFailure(
                code="scorecard_file_missing",
                field="scorecard_file",
                path=str(scorecard_path),
                expected=manifest.scorecard_file,
                message=f"Scorecard file could not be read: {exc}",
            )
        )
    else:
        actual_scorecard_hash = hashlib.sha256(scorecard_bytes).hexdigest()
        if actual_scorecard_hash != manifest.scorecard_sha256:
            failures.append(
                Phase0ArtifactVerificationFailure(
                    code="scorecard_sha256_mismatch",
                    field="scorecard_sha256",
                    path=str(scorecard_path),
                    expected=manifest.scorecard_sha256,
                    actual=actual_scorecard_hash,
                    message="Scorecard SHA-256 does not match manifest",
                )
            )
        scorecard_payload = _load_json_payload(
            scorecard_bytes,
            scorecard_path,
            label="scorecard",
            failures=failures,
        )

    timing_payload: dict[str, Any] | None = None
    try:
        timing_bytes = timing_path.read_bytes()
        checked_timing_count = 1
    except OSError as exc:
        failures.append(
            Phase0ArtifactVerificationFailure(
                code="timing_file_missing",
                field="timing_file",
                path=str(timing_path),
                expected=manifest.timing_file,
                message=f"Timing artifact file could not be read: {exc}",
            )
        )
    else:
        actual_timing_hash = hashlib.sha256(timing_bytes).hexdigest()
        if actual_timing_hash != manifest.timing_sha256:
            failures.append(
                Phase0ArtifactVerificationFailure(
                    code="timing_sha256_mismatch",
                    field="timing_sha256",
                    path=str(timing_path),
                    expected=manifest.timing_sha256,
                    actual=actual_timing_hash,
                    message="Timing artifact SHA-256 does not match manifest",
                )
            )
        timing_payload = _load_json_payload(
            timing_bytes,
            timing_path,
            label="timing",
            failures=failures,
        )

    _verify_manifest_caveats(manifest, failures)
    if scorecard_payload is not None:
        _verify_scorecard_metadata(manifest, scorecard_payload, scorecard_path, failures)
    if scorecard_payload is not None and timing_payload is not None:
        _verify_timing_payload(
            manifest,
            scorecard_payload,
            timing_payload,
            timing_path,
            failures,
        )

    return _verification_report(
        artifact_type=manifest.artifact_type,
        project_id=manifest.project_id,
        manifest_path=manifest_path,
        scorecard_path=scorecard_path,
        timing_path=timing_path,
        checked_scorecard_count=checked_scorecard_count,
        checked_timing_count=checked_timing_count,
        failures=failures,
    )


def _manifest_path_for(path: Path) -> Path:
    """Resolve an artifact directory or manifest path to a manifest path."""
    return path / "manifest.json" if path.is_dir() else path


def _load_manifest_payload(
    manifest_path: Path,
) -> tuple[dict[str, Any] | None, list[Phase0ArtifactVerificationFailure]]:
    """Load a manifest payload and return structured load failures."""
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, [
            Phase0ArtifactVerificationFailure(
                code="manifest_file_unreadable",
                field="manifest",
                path=str(manifest_path),
                message=f"Manifest file could not be read: {exc}",
            )
        ]
    except json.JSONDecodeError as exc:
        return None, [
            Phase0ArtifactVerificationFailure(
                code="manifest_json_invalid",
                field="manifest",
                path=str(manifest_path),
                message=f"Manifest file is not valid JSON: {exc}",
            )
        ]
    if not isinstance(raw, dict):
        return None, [
            Phase0ArtifactVerificationFailure(
                code="invalid_manifest_payload",
                field="manifest",
                path=str(manifest_path),
                message="Manifest payload must be a JSON object",
            )
        ]
    return raw, []


def _load_json_payload(
    payload_bytes: bytes,
    path: Path,
    *,
    label: str,
    failures: list[Phase0ArtifactVerificationFailure],
) -> dict[str, Any] | None:
    """Load a JSON artifact payload and append structured failures when invalid."""
    try:
        raw = json.loads(payload_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        failures.append(
            Phase0ArtifactVerificationFailure(
                code=f"{label}_utf8_invalid",
                field=f"{label}_file",
                path=str(path),
                message=f"{label.title()} file is not valid UTF-8: {exc}",
            )
        )
        return None
    except json.JSONDecodeError as exc:
        failures.append(
            Phase0ArtifactVerificationFailure(
                code=f"{label}_json_invalid",
                field=f"{label}_file",
                path=str(path),
                message=f"{label.title()} file is not valid JSON: {exc}",
            )
        )
        return None
    if not isinstance(raw, dict):
        failures.append(
            Phase0ArtifactVerificationFailure(
                code=f"invalid_{label}_payload",
                field=label,
                path=str(path),
                message=f"{label.title()} payload must be a JSON object",
            )
        )
        return None
    return raw


def _verify_manifest_caveats(
    manifest: Phase0BenchmarkArtifactManifest,
    failures: list[Phase0ArtifactVerificationFailure],
) -> None:
    """Verify manifest caveats required by Phase 0 claim discipline."""
    prompt_eval_status = manifest.prompt_eval.get("status")
    if prompt_eval_status != "not_run":
        failures.append(
            Phase0ArtifactVerificationFailure(
                code="prompt_eval_status_invalid",
                field="prompt_eval.status",
                expected="not_run",
                actual=prompt_eval_status,
                message="Manifest prompt_eval status must be not_run",
            )
        )
    caveat_text = _claim_discipline_text(manifest.claim_discipline)
    if "not" not in caveat_text.lower() or "sota" not in caveat_text.lower():
        failures.append(
            Phase0ArtifactVerificationFailure(
                code="claim_discipline_caveat_missing",
                field="claim_discipline",
                actual=manifest.claim_discipline,
                message="Manifest claim discipline must state this is not SOTA evidence",
            )
        )


def _verify_scorecard_metadata(
    manifest: Phase0BenchmarkArtifactManifest,
    scorecard_payload: dict[str, Any],
    scorecard_path: Path,
    failures: list[Phase0ArtifactVerificationFailure],
) -> None:
    """Verify manifest metadata copied from scorecard _meta."""
    meta = scorecard_payload.get("_meta")
    if not isinstance(meta, dict):
        failures.append(
            Phase0ArtifactVerificationFailure(
                code="scorecard_meta_missing",
                field="_meta",
                path=str(scorecard_path),
                message="Scorecard is missing _meta object",
            )
        )
        return
    input_hashes = meta.get("input_hashes")
    if input_hashes != manifest.input_hashes:
        failures.append(
            Phase0ArtifactVerificationFailure(
                code="input_hashes_mismatch",
                field="_meta.input_hashes",
                path=str(scorecard_path),
                expected=manifest.input_hashes,
                actual=input_hashes,
                message="Scorecard input hashes do not match manifest input hashes",
            )
        )
    run_configuration_hashes = meta.get("run_configuration_hashes")
    if run_configuration_hashes != manifest.run_configuration_hashes:
        failures.append(
            Phase0ArtifactVerificationFailure(
                code="run_configuration_hashes_mismatch",
                field="_meta.run_configuration_hashes",
                path=str(scorecard_path),
                expected=manifest.run_configuration_hashes,
                actual=run_configuration_hashes,
                message=(
                    "Scorecard run-configuration hashes do not match manifest "
                    "run-configuration hashes"
                ),
            )
        )
    claim_discipline = meta.get("claims")
    if claim_discipline != manifest.claim_discipline:
        failures.append(
            Phase0ArtifactVerificationFailure(
                code="claim_discipline_mismatch",
                field="_meta.claims",
                path=str(scorecard_path),
                expected=manifest.claim_discipline,
                actual=claim_discipline,
                message="Scorecard claim discipline does not match manifest",
            )
        )


def _verify_timing_payload(
    manifest: Phase0BenchmarkArtifactManifest,
    scorecard_payload: dict[str, Any],
    timing_payload: dict[str, Any],
    timing_path: Path,
    failures: list[Phase0ArtifactVerificationFailure],
) -> None:
    """Verify timing artifact metadata and copied D10 sections."""
    artifact_type = timing_payload.get("artifact_type")
    if artifact_type != "qualitative_coding.phase0_d10_timing":
        failures.append(
            Phase0ArtifactVerificationFailure(
                code="timing_artifact_type_invalid",
                field="timing.artifact_type",
                path=str(timing_path),
                expected="qualitative_coding.phase0_d10_timing",
                actual=artifact_type,
                message="Timing artifact type is invalid",
            )
        )
    source_file = timing_payload.get("source_file")
    if source_file != manifest.scorecard_file:
        failures.append(
            Phase0ArtifactVerificationFailure(
                code="timing_source_file_mismatch",
                field="timing.source_file",
                path=str(timing_path),
                expected=manifest.scorecard_file,
                actual=source_file,
                message="Timing artifact source file does not match manifest scorecard file",
            )
        )
    for section in ("cost_latency_d10", "wall_clock_d10"):
        if timing_payload.get(section) != scorecard_payload.get(section):
            failures.append(
                Phase0ArtifactVerificationFailure(
                    code=f"{section}_mismatch",
                    field=f"timing.{section}",
                    path=str(timing_path),
                    expected=scorecard_payload.get(section),
                    actual=timing_payload.get(section),
                    message=f"Timing artifact {section} does not match scorecard",
                )
            )


def _claim_discipline_text(value: Any) -> str:
    """Return searchable claim-discipline text from string or structured values."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(str(item) for item in value.values())
    return str(value)


def _verification_report(
    *,
    artifact_type: str | None,
    project_id: str | None,
    manifest_path: Path,
    scorecard_path: Path | None,
    timing_path: Path | None,
    checked_scorecard_count: int,
    checked_timing_count: int,
    failures: list[Phase0ArtifactVerificationFailure],
) -> Phase0ArtifactVerificationReport:
    """Build a Phase 0 artifact verification report."""
    return Phase0ArtifactVerificationReport(
        schema_version=1,
        package_type="qualitative_coding.phase0_benchmark_artifact_verification",
        status="verified" if not failures else "invalid",
        artifact_type=artifact_type,
        project_id=project_id,
        manifest_path=str(manifest_path),
        scorecard_path=str(scorecard_path) if scorecard_path is not None else None,
        timing_path=str(timing_path) if timing_path is not None else None,
        checked_scorecard_count=checked_scorecard_count,
        checked_timing_count=checked_timing_count,
        failure_count=len(failures),
        failures=failures,
        caveat=PHASE0_ARTIFACT_VERIFICATION_CAVEAT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
