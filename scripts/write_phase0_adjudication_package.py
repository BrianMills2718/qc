#!/usr/bin/env python3
"""Write Phase 0 benchmark package manifests for imported adjudication gold."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Literal, Sequence

from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d3_gold import D3GoldSetPackage, load_d3_gold_set
from qc_clean.core.d7_gold import D7GoldSetPackage, load_d7_gold_set
from scripts.run_phase0_benchmark_package import Phase0BenchmarkPackage


PACKAGE_CAUTION = (
    "Phase 0 adjudication benchmark packages are orchestration/provenance "
    "artifacts only; they are not methodological validity evidence unless the "
    "referenced labels were collected under a documented expert protocol and "
    "scored separately."
)


class Phase0AdjudicationPackageReport(BaseModel):
    """Machine-readable report for a written Phase 0 adjudication package."""

    schema_version: Literal[1] = Field(description="Report schema version")
    package_type: Literal["phase0_adjudication_benchmark_package"] = Field(
        description="Report package kind"
    )
    status: Literal["complete"] = Field(description="Manifest write status")
    project_id: str = Field(description="Project ID recorded in the manifest")
    package_file: str = Field(description="Written Phase 0 package manifest path")
    d3_gold_file: str | None = Field(
        default=None,
        description="Validated D3 gold package path when supplied",
    )
    d7_gold_file: str | None = Field(
        default=None,
        description="Validated D7 gold package path when supplied",
    )
    scorecard_output: str | None = Field(
        default=None,
        description="Optional scorecard output path recorded in the manifest",
    )
    artifact_dir: str | None = Field(
        default=None,
        description="Optional artifact directory recorded in the manifest",
    )
    caution: str = Field(description="Claim-discipline caveat for the package")


def main(argv: Sequence[str] | None = None) -> int:
    """Write a Phase 0 package manifest from adjudication gold-package files."""
    parser = argparse.ArgumentParser(
        description="Write a Phase 0 package manifest for imported D3/D7 adjudication gold"
    )
    parser.add_argument("project_id", help="Project ID to score with the package")
    parser.add_argument("--output", required=True, type=Path, help="Output manifest path")
    parser.add_argument(
        "--d3-gold-file",
        type=Path,
        help="Optional versioned D3 adjudication gold package path",
    )
    parser.add_argument(
        "--d7-gold-file",
        "--gold-file",
        dest="d7_gold_file",
        type=Path,
        help="Optional versioned D7 adjudication gold package path",
    )
    parser.add_argument(
        "--scorecard-output",
        type=Path,
        help="Optional scorecard output path for the Phase 0 package",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="Optional artifact root directory for the Phase 0 package",
    )
    parser.add_argument(
        "--observability-db",
        type=Path,
        help="Optional llm_client observability SQLite path for D10 scoring",
    )
    parser.add_argument("--trace-id", help="Optional exact trace ID for D10 scoring")
    args = parser.parse_args(argv)

    try:
        report = write_phase0_adjudication_package(
            project_id=args.project_id,
            output_file=args.output,
            d3_gold_file=args.d3_gold_file,
            d7_gold_file=args.d7_gold_file,
            scorecard_output=args.scorecard_output,
            artifact_dir=args.artifact_dir,
            observability_db=args.observability_db,
            trace_id=args.trace_id,
        )
    except ValueError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0


def write_phase0_adjudication_package(
    *,
    project_id: str,
    output_file: str | Path,
    d3_gold_file: str | Path | None = None,
    d7_gold_file: str | Path | None = None,
    scorecard_output: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    observability_db: str | Path | None = None,
    trace_id: str | None = None,
) -> Phase0AdjudicationPackageReport:
    """Write and verify a Phase 0 manifest for D3/D7 adjudication packages."""
    manifest = build_phase0_adjudication_package_manifest(
        project_id=project_id,
        output_file=output_file,
        d3_gold_file=d3_gold_file,
        d7_gold_file=d7_gold_file,
        scorecard_output=scorecard_output,
        artifact_dir=artifact_dir,
        observability_db=observability_db,
        trace_id=trace_id,
    )
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest.model_dump(mode="json", exclude_none=True), indent=2),
        encoding="utf-8",
    )

    return Phase0AdjudicationPackageReport(
        schema_version=1,
        package_type="phase0_adjudication_benchmark_package",
        status="complete",
        project_id=manifest.project_id,
        package_file=str(output_path),
        d3_gold_file=str(d3_gold_file) if d3_gold_file is not None else None,
        d7_gold_file=str(d7_gold_file) if d7_gold_file is not None else None,
        scorecard_output=str(scorecard_output) if scorecard_output is not None else None,
        artifact_dir=str(artifact_dir) if artifact_dir is not None else None,
        caution=PACKAGE_CAUTION,
    )


def build_phase0_adjudication_package_manifest(
    *,
    project_id: str,
    output_file: str | Path,
    d3_gold_file: str | Path | None = None,
    d7_gold_file: str | Path | None = None,
    scorecard_output: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    observability_db: str | Path | None = None,
    trace_id: str | None = None,
) -> Phase0BenchmarkPackage:
    """Build a strict Phase 0 manifest after validating D3/D7 package inputs."""
    if d3_gold_file is None and d7_gold_file is None:
        raise ValueError("At least one of d3_gold_file or d7_gold_file is required")

    output_path = Path(output_file)
    manifest_dir = output_path.parent
    d3_package = _load_d3_package(d3_gold_file) if d3_gold_file is not None else None
    d7_package = _load_d7_package(d7_gold_file) if d7_gold_file is not None else None
    if d3_package is not None and d7_package is not None:
        _require_matching_provenance(d3_package, d7_package)

    return Phase0BenchmarkPackage(
        schema_version=1,
        project_id=project_id,
        d3_gold_file=(
            _manifest_input_path(manifest_dir, d3_gold_file) if d3_gold_file is not None else None
        ),
        gold_file=(
            _manifest_input_path(manifest_dir, d7_gold_file) if d7_gold_file is not None else None
        ),
        output=_manifest_output_path(manifest_dir, scorecard_output),
        artifact_dir=_manifest_output_path(manifest_dir, artifact_dir),
        observability_db=(
            _manifest_input_path(manifest_dir, observability_db)
            if observability_db is not None
            else None
        ),
        trace_id=trace_id,
    )


def _load_d3_package(path: str | Path | None) -> D3GoldSetPackage:
    """Load a versioned D3 gold package or raise a context-rich error."""
    if path is None:
        raise ValueError("D3 gold package path is required")
    try:
        return load_d3_gold_set(path)
    except ValueError as exc:
        raise ValueError(
            f"D3 gold file must be a versioned D3 gold-set package: {exc}"
        ) from exc


def _load_d7_package(path: str | Path | None) -> D7GoldSetPackage:
    """Load a versioned D7 gold package or raise a context-rich error."""
    if path is None:
        raise ValueError("D7 gold package path is required")
    try:
        return load_d7_gold_set(path)
    except ValueError as exc:
        raise ValueError(
            f"D7 gold file must be a versioned D7 gold-set package: {exc}"
        ) from exc


def _require_matching_provenance(
    d3_package: D3GoldSetPackage,
    d7_package: D7GoldSetPackage,
) -> None:
    """Fail when D3 and D7 packages do not describe the same adjudication set."""
    comparisons = {
        "gold_set_id": (d3_package.gold_set_id, d7_package.gold_set_id),
        "dataset_name": (d3_package.dataset_name, d7_package.dataset_name),
        "split": (d3_package.split, d7_package.split),
        "corpus_sha256": (d3_package.corpus_sha256, d7_package.corpus_sha256),
        "project_state_sha256": (
            d3_package.project_state_sha256,
            d7_package.project_state_sha256,
        ),
        "prompt_frozen": (d3_package.prompt_frozen, d7_package.prompt_frozen),
        "contamination_checked": (
            d3_package.contamination_checked,
            d7_package.contamination_checked,
        ),
        "adjudication.coder_count": (
            d3_package.adjudication.coder_count,
            d7_package.adjudication.coder_count,
        ),
        "adjudication.adjudicator": (
            d3_package.adjudication.adjudicator,
            d7_package.adjudication.adjudicator,
        ),
        "adjudication.protocol": (
            d3_package.adjudication.protocol,
            d7_package.adjudication.protocol,
        ),
    }
    mismatches = [field for field, values in comparisons.items() if values[0] != values[1]]
    if mismatches:
        raise ValueError(
            "D3/D7 package provenance mismatch: " + ", ".join(sorted(mismatches))
        )


def _manifest_input_path(manifest_dir: Path, raw_path: str | Path) -> str:
    """Return a package path relative to the manifest when possible."""
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = path.resolve()
    return _relative_or_absolute(manifest_dir, path)


def _manifest_output_path(manifest_dir: Path, raw_path: str | Path | None) -> str | None:
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
