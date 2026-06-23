#!/usr/bin/env python3
"""Write D7 comparison package manifests from validated inputs."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Literal, Sequence

from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d7_baseline_package import validate_d7_baseline_package_payload
from qc_clean.core.d7_gold import load_d7_gold_set
from scripts import preflight_d7_comparison
from scripts.run_d7_comparison_package import D7ComparisonPackage


PACKAGE_CAUTION = (
    "D7 comparison package writing is orchestration/provenance infrastructure "
    "only; it is not held-out D7 evidence, live-baseline evidence, "
    "methodological-validity evidence, superiority evidence, or SOTA evidence."
)


class D7ComparisonPackageWriteReport(BaseModel):
    """Machine-readable report for a written D7 comparison package."""

    schema_version: Literal[1] = Field(description="Report schema version")
    package_type: Literal["d7_comparison_package_write"] = Field(
        description="Report package kind"
    )
    status: Literal["complete"] = Field(description="Manifest write status")
    project_id: str = Field(description="Project ID recorded in the manifest")
    projects_dir: str | None = Field(
        default=None,
        description="Optional project store directory recorded in the manifest",
    )
    package_file: str = Field(description="Written D7 comparison package path")
    gold_file: str = Field(description="Validated D7 gold package path")
    prediction_files: list[str] = Field(
        description="Validated D7 retrieval/live-baseline prediction package paths"
    )
    protocol_package: str | None = Field(
        default=None,
        description="Optional preflighted D7 comparison protocol package path",
    )
    comparison_output: str | None = Field(
        default=None,
        description="Optional comparison report output path recorded in the manifest",
    )
    artifact_dir: str | None = Field(
        default=None,
        description="Optional artifact root directory recorded in the manifest",
    )
    verify_artifact: bool = Field(
        description="Whether the manifest asks the runner to verify the created artifact"
    )
    preflight_status: Literal["not_run", "pass"] = Field(
        description="Existing D7 comparison preflight status for protocol packages"
    )
    caution: str = Field(description="Claim-discipline caveat for the package")


def main(argv: Sequence[str] | None = None) -> int:
    """Write a D7 comparison package manifest and emit a JSON report."""
    parser = argparse.ArgumentParser(
        description="Write a D7 comparison package manifest from validated inputs"
    )
    parser.add_argument("project_id", help="Project ID to compare with the package")
    parser.add_argument(
        "--projects-dir",
        type=Path,
        help="Optional project store directory recorded in the package",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output manifest path")
    parser.add_argument(
        "--gold-file",
        required=True,
        type=Path,
        help="Versioned D7 gold package path",
    )
    parser.add_argument(
        "--predictions-file",
        action="append",
        required=True,
        type=Path,
        help="Versioned D7 retrieval/live-baseline prediction package path",
    )
    parser.add_argument(
        "--protocol-package",
        type=Path,
        help="Optional D7 comparison protocol package path to preflight before writing",
    )
    parser.add_argument(
        "--comparison-output",
        type=Path,
        help="Optional D7 comparison report output path for the package",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="Optional artifact root directory for the package",
    )
    parser.add_argument(
        "--verify-artifact",
        action="store_true",
        help="Ask the package runner to verify the artifact created by the run",
    )
    args = parser.parse_args(argv)

    try:
        report = write_d7_comparison_package(
            project_id=args.project_id,
            projects_dir=args.projects_dir,
            output_file=args.output,
            gold_file=args.gold_file,
            prediction_files=args.predictions_file,
            protocol_package=args.protocol_package,
            comparison_output=args.comparison_output,
            artifact_dir=args.artifact_dir,
            verify_artifact=args.verify_artifact,
        )
    except ValueError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0


def write_d7_comparison_package(
    *,
    project_id: str,
    projects_dir: str | Path | None = None,
    output_file: str | Path,
    gold_file: str | Path,
    prediction_files: Sequence[str | Path],
    protocol_package: str | Path | None = None,
    comparison_output: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    verify_artifact: bool = False,
) -> D7ComparisonPackageWriteReport:
    """Write and verify a D7 comparison package manifest."""
    manifest, preflight_status = build_d7_comparison_package_manifest(
        project_id=project_id,
        projects_dir=projects_dir,
        output_file=output_file,
        gold_file=gold_file,
        prediction_files=prediction_files,
        protocol_package=protocol_package,
        comparison_output=comparison_output,
        artifact_dir=artifact_dir,
        verify_artifact=verify_artifact,
    )
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest.model_dump(mode="json", exclude_none=True), indent=2),
        encoding="utf-8",
    )

    return D7ComparisonPackageWriteReport(
        schema_version=1,
        package_type="d7_comparison_package_write",
        status="complete",
        project_id=manifest.project_id,
        projects_dir=str(projects_dir) if projects_dir is not None else None,
        package_file=str(output_path),
        gold_file=str(gold_file),
        prediction_files=[str(path) for path in prediction_files],
        protocol_package=str(protocol_package) if protocol_package is not None else None,
        comparison_output=str(comparison_output) if comparison_output is not None else None,
        artifact_dir=str(artifact_dir) if artifact_dir is not None else None,
        verify_artifact=manifest.verify_artifact,
        preflight_status=preflight_status,
        caution=PACKAGE_CAUTION,
    )


def build_d7_comparison_package_manifest(
    *,
    project_id: str,
    projects_dir: str | Path | None = None,
    output_file: str | Path,
    gold_file: str | Path,
    prediction_files: Sequence[str | Path],
    protocol_package: str | Path | None = None,
    comparison_output: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    verify_artifact: bool = False,
) -> tuple[D7ComparisonPackage, Literal["not_run", "pass"]]:
    """Build a strict D7 comparison manifest after validating inputs."""
    if not prediction_files:
        raise ValueError("At least one D7 prediction file is required")
    _load_d7_gold_package(gold_file)
    for prediction_file in prediction_files:
        _load_d7_prediction_package(prediction_file)

    preflight_status: Literal["not_run", "pass"] = "not_run"
    if protocol_package is not None:
        _run_d7_comparison_preflight(
            protocol_package=protocol_package,
            gold_file=gold_file,
            prediction_files=prediction_files,
        )
        preflight_status = "pass"

    output_path = Path(output_file)
    manifest_dir = output_path.parent
    return (
        D7ComparisonPackage(
            schema_version=1,
            project_id=project_id,
            projects_dir=(
                _manifest_input_path(manifest_dir, projects_dir)
                if projects_dir is not None
                else None
            ),
            gold_file=_manifest_input_path(manifest_dir, gold_file),
            prediction_files=[
                _manifest_input_path(manifest_dir, prediction_file)
                for prediction_file in prediction_files
            ],
            protocol_package=(
                _manifest_input_path(manifest_dir, protocol_package)
                if protocol_package is not None
                else None
            ),
            output=_manifest_output_path(manifest_dir, comparison_output),
            artifact_dir=_manifest_output_path(manifest_dir, artifact_dir),
            verify_artifact=verify_artifact,
        ),
        preflight_status,
    )


def _load_d7_gold_package(path: str | Path) -> None:
    """Load a versioned D7 gold package or raise a context-rich error."""
    try:
        load_d7_gold_set(path)
    except ValueError as exc:
        raise ValueError(
            f"D7 gold file must be a versioned D7 gold-set package: {exc}"
        ) from exc


def _load_d7_prediction_package(path: str | Path) -> None:
    """Load a versioned D7 prediction package or raise a context-rich error."""
    prediction_path = Path(path)
    try:
        raw = json.loads(prediction_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"D7 prediction file '{prediction_path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"D7 prediction file '{prediction_path}' is not valid JSON: {exc}"
        ) from exc
    try:
        validate_d7_baseline_package_payload(raw)
    except ValueError as exc:
        raise ValueError(
            "D7 prediction file must be a versioned D7 prediction package: "
            f"{prediction_path}: {exc}"
        ) from exc


def _run_d7_comparison_preflight(
    *,
    protocol_package: str | Path,
    gold_file: str | Path,
    prediction_files: Sequence[str | Path],
) -> None:
    """Run the existing D7 comparison preflight without leaking stdout."""
    argv = [
        str(protocol_package),
        str(gold_file),
        *[str(prediction_file) for prediction_file in prediction_files],
    ]
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        exit_code = preflight_d7_comparison.main(argv)
    if exit_code != 0:
        raise ValueError(
            "D7 comparison preflight failed before package write: "
            f"{captured.getvalue().strip()}"
        )


def _manifest_input_path(manifest_dir: Path, raw_path: str | Path) -> str:
    """Return a package path relative to the manifest when possible."""
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = path.resolve()
    return _relative_or_absolute(manifest_dir, path)


def _manifest_output_path(
    manifest_dir: Path,
    raw_path: str | Path | None,
) -> str | None:
    """Return an output path that the package runner will resolve correctly."""
    if raw_path is None:
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        return path.as_posix()
    return _relative_or_absolute(manifest_dir, path)


def _relative_or_absolute(manifest_dir: Path, path: Path) -> str:
    """Represent path relative to manifest_dir if it is inside that directory."""
    resolved_manifest_dir = manifest_dir.resolve()
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(resolved_manifest_dir).as_posix()
    except ValueError:
        return str(resolved_path)


if __name__ == "__main__":
    raise SystemExit(main())
