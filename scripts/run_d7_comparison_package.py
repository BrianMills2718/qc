#!/usr/bin/env python3
"""Run D7 comparison scoring from a versioned package manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import compare_d7_retrieval, verify_d7_comparison_artifact


class D7ComparisonPackage(BaseModel):
    """Versioned manifest for one deterministic D7 comparison run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(description="Manifest schema version; currently 1")
    project_id: str = Field(description="Project ID to compare")
    gold_file: str = Field(description="D7 gold JSON path")
    prediction_files: list[str] = Field(
        description="Ordered D7 retrieval/live-baseline prediction package paths"
    )
    protocol_package: str | None = Field(
        default=None,
        description="Optional D7 comparison protocol JSON path",
    )
    output: str | None = Field(default=None, description="Optional comparison report path")
    artifact_dir: str | None = Field(
        default=None,
        description="Optional D7 comparison artifact root directory",
    )
    verify_artifact: bool = Field(
        default=False,
        description="Whether to verify the artifact created by this package run",
    )

    @model_validator(mode="after")
    def require_supported_manifest(self) -> "D7ComparisonPackage":
        """Reject unsupported or unusable D7 comparison package manifests."""
        if self.schema_version != 1:
            raise ValueError("D7 comparison package schema_version must be 1")
        self.project_id = self.project_id.strip()
        if not self.project_id:
            raise ValueError("D7 comparison package project_id must be non-empty")
        self.gold_file = self.gold_file.strip()
        if not self.gold_file:
            raise ValueError("D7 comparison package gold_file must be non-empty")
        self.prediction_files = [path.strip() for path in self.prediction_files]
        if not self.prediction_files or any(not path for path in self.prediction_files):
            raise ValueError("D7 comparison package prediction_files must be non-empty")
        if self.protocol_package is not None:
            self.protocol_package = self.protocol_package.strip() or None
        if self.output is not None:
            self.output = self.output.strip() or None
        if self.artifact_dir is not None:
            self.artifact_dir = self.artifact_dir.strip() or None
        if self.verify_artifact and self.artifact_dir is None:
            raise ValueError(
                "D7 comparison package verify_artifact requires artifact_dir"
            )
        return self


def main(argv: Sequence[str] | None = None) -> int:
    """Run the canonical D7 comparison CLI from a package manifest."""
    parser = argparse.ArgumentParser(description="Run a D7 comparison package")
    parser.add_argument("package_file", help="Path to the D7 comparison package JSON")
    args = parser.parse_args(argv)

    package_path = Path(args.package_file)
    try:
        package = load_d7_comparison_package(package_path)
        package_dir = package_path.parent
        compare_argv = d7_package_to_compare_argv(package, package_dir)
        artifact_root = _resolved_artifact_root(package, package_dir)
        before_artifacts = _artifact_run_dirs(artifact_root) if package.verify_artifact else set()
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    exit_code = compare_d7_retrieval.main(compare_argv)
    if exit_code != 0 or not package.verify_artifact:
        return exit_code

    assert artifact_root is not None
    try:
        artifact_dir = _created_artifact_dir(artifact_root, before_artifacts)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    verification = verify_d7_comparison_artifact.verify_d7_comparison_artifact(
        artifact_dir
    )
    if verification.status != "verified":
        print(json.dumps(verification.model_dump(mode="json"), indent=2))
        return 1
    return 0


def load_d7_comparison_package(path: Path) -> D7ComparisonPackage:
    """Load and validate a D7 comparison package manifest."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D7 comparison package '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D7 comparison package '{path}' is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("D7 comparison package must be a JSON object")
    try:
        return D7ComparisonPackage.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid D7 comparison package: {exc}") from exc


def d7_package_to_compare_argv(
    package: D7ComparisonPackage,
    package_dir: Path,
) -> list[str]:
    """Convert a D7 comparison package to canonical compare argv."""
    argv = [
        package.project_id,
        "--gold-file",
        str(_resolve_manifest_path(package_dir, package.gold_file)),
    ]
    for prediction_file in package.prediction_files:
        argv.extend([
            "--predictions-file",
            str(_resolve_manifest_path(package_dir, prediction_file)),
        ])
    if package.output is not None:
        argv.extend(["--output", str(_resolve_manifest_path(package_dir, package.output))])
    if package.protocol_package is not None:
        argv.extend([
            "--protocol-package",
            str(_resolve_manifest_path(package_dir, package.protocol_package)),
        ])
    artifact_root = _resolved_artifact_root(package, package_dir)
    if artifact_root is not None:
        argv.extend(["--artifact-dir", str(artifact_root)])
    return argv


def _resolved_artifact_root(
    package: D7ComparisonPackage,
    package_dir: Path,
) -> Path | None:
    """Return resolved artifact root when configured."""
    if package.artifact_dir is None:
        return None
    return _resolve_manifest_path(package_dir, package.artifact_dir)


def _resolve_manifest_path(package_dir: Path, raw_path: str) -> Path:
    """Resolve a package path relative to its manifest directory."""
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return package_dir / path


def _artifact_run_dirs(artifact_root: Path | None) -> set[Path]:
    """Return current direct child directories under an artifact root."""
    if artifact_root is None or not artifact_root.exists():
        return set()
    return {path for path in artifact_root.iterdir() if path.is_dir()}


def _created_artifact_dir(artifact_root: Path, before_artifacts: set[Path]) -> Path:
    """Return the one artifact directory created by this package run."""
    after_artifacts = _artifact_run_dirs(artifact_root)
    created = sorted(after_artifacts - before_artifacts)
    if len(created) != 1:
        raise ValueError(
            "D7 comparison package verification expected exactly one new artifact "
            f"directory under '{artifact_root}', found {len(created)}"
        )
    return created[0]


if __name__ == "__main__":
    raise SystemExit(main())
