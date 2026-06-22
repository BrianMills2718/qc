#!/usr/bin/env python3
"""Run Phase 0 benchmark scoring from a versioned package manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import bench_phase0


_PATH_FLAGS = {
    "d3_gold_file": "--d3-gold-file",
    "d3_baselines_file": "--d3-baselines-file",
    "gold_file": "--gold-file",
    "d7_baselines_file": "--d7-baselines-file",
    "prompt_injection_file": "--prompt-injection-file",
    "bias_counterfactual_file": "--bias-counterfactual-file",
    "codebook_quality_file": "--codebook-quality-file",
    "gt_fidelity_file": "--gt-fidelity-file",
    "interpretive_preference_file": "--interpretive-preference-file",
    "confidence_calibration_file": "--confidence-calibration-file",
    "observability_db": "--observability-db",
    "output": "--output",
    "artifact_dir": "--artifact-dir",
}


class Phase0BenchmarkPackage(BaseModel):
    """Versioned manifest for one deterministic Phase 0 benchmark run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(description="Manifest schema version; currently 1")
    project_id: str = Field(description="Project ID to score")
    d3_gold_file: str | None = Field(default=None, description="Optional D3 gold JSON path")
    d3_baselines_file: str | None = Field(
        default=None,
        description="Optional D3 baseline predictions JSON path",
    )
    gold_file: str | None = Field(default=None, description="Optional D7 gold JSON path")
    d7_baselines_file: str | None = Field(
        default=None,
        description="Optional D7 baseline predictions JSON path",
    )
    prompt_injection_file: str | None = Field(
        default=None,
        description="Optional INV-7 prompt-injection fixture JSON path",
    )
    bias_counterfactual_file: str | None = Field(
        default=None,
        description="Optional D6 counterfactual JSON path",
    )
    codebook_quality_file: str | None = Field(
        default=None,
        description="Optional D4 codebook-quality rubric JSON path",
    )
    gt_fidelity_file: str | None = Field(
        default=None,
        description="Optional D8 GT-fidelity rubric JSON path",
    )
    interpretive_preference_file: str | None = Field(
        default=None,
        description="Optional D9 preference JSON path",
    )
    confidence_calibration_file: str | None = Field(
        default=None,
        description="Optional confidence-calibration JSON path",
    )
    observability_db: str | None = Field(
        default=None,
        description="Optional llm_client observability SQLite path",
    )
    trace_id: str | None = Field(default=None, description="Optional exact trace ID")
    output: str | None = Field(default=None, description="Optional scorecard output path")
    artifact_dir: str | None = Field(
        default=None,
        description="Optional benchmark artifact root directory",
    )

    @model_validator(mode="after")
    def require_supported_manifest(self) -> "Phase0BenchmarkPackage":
        """Reject unsupported or unusable package manifests."""
        if self.schema_version != 1:
            raise ValueError("Phase 0 benchmark package schema_version must be 1")
        self.project_id = self.project_id.strip()
        if not self.project_id:
            raise ValueError("Phase 0 benchmark package project_id must be non-empty")
        return self


def main(argv: Sequence[str] | None = None) -> int:
    """Run the canonical Phase 0 benchmark CLI from a package manifest."""
    parser = argparse.ArgumentParser(description="Run a Phase 0 benchmark package")
    parser.add_argument("package_file", help="Path to the Phase 0 benchmark package JSON")
    args = parser.parse_args(argv)

    package_path = Path(args.package_file)
    try:
        package = load_phase0_benchmark_package(package_path)
        bench_argv = phase0_package_to_bench_argv(package, package_path.parent)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    return bench_phase0.main(bench_argv)


def load_phase0_benchmark_package(path: Path) -> Phase0BenchmarkPackage:
    """Load and validate a Phase 0 benchmark package manifest."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Phase 0 benchmark package '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Phase 0 benchmark package '{path}' is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Phase 0 benchmark package must be a JSON object")
    try:
        return Phase0BenchmarkPackage.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid Phase 0 benchmark package: {exc}") from exc


def phase0_package_to_bench_argv(
    package: Phase0BenchmarkPackage,
    package_dir: Path,
) -> list[str]:
    """Convert a validated package manifest to canonical bench_phase0 argv."""
    argv = [package.project_id]
    payload: dict[str, Any] = package.model_dump()
    for field_name, flag in _PATH_FLAGS.items():
        raw_path = payload.get(field_name)
        if raw_path is None:
            continue
        argv.extend([flag, str(_resolve_manifest_path(package_dir, raw_path))])
    if package.trace_id:
        argv.extend(["--trace-id", package.trace_id])
    return argv


def _resolve_manifest_path(package_dir: Path, raw_path: str) -> Path:
    """Resolve a package path relative to its manifest directory."""
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return package_dir / path


if __name__ == "__main__":
    raise SystemExit(main())
