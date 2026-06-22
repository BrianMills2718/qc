#!/usr/bin/env python3
"""Compare exported D7 retrieval prediction packages against a gold file."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d7_comparison_preflight import (
    D7ComparisonPreflightReport,
    preflight_d7_comparison_payloads,
)
from qc_clean.core.d7_comparison_protocol import (
    D7MetricCriteriaReport,
    evaluate_d7_comparison_metric_criteria,
)
from qc_clean.core.d7_retrieval import compare_d7_retrieval_predictions
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import ProjectState
from scripts.bench_phase0 import load_d7_gold_file

D7_COMPARISON_ARTIFACT_CAVEAT = (
    "This D7 comparison artifact is local provenance/accounting metadata only; "
    "it is not held-out D7 evidence, live-baseline evidence, superiority "
    "evidence, methodological-validity evidence, or SOTA evidence."
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the retrieval prediction comparison CLI."""
    parser = argparse.ArgumentParser(
        description="Score D7 retrieval prediction packages against one gold file"
    )
    parser.add_argument("project_id", help="Project ID to score")
    parser.add_argument("--gold-file", required=True, type=Path, help="D7 gold JSON file")
    parser.add_argument(
        "--predictions-file",
        required=True,
        action="append",
        type=Path,
        help="Retrieval prediction package JSON file; repeat to compare multiple packages",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON report output path")
    parser.add_argument(
        "--protocol-package",
        type=Path,
        help="Optional D7 comparison protocol package used to preflight before scoring",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="Optional root directory for a versioned D7 comparison artifact package",
    )
    args = parser.parse_args(argv)

    store = ProjectStore()
    try:
        state = store.load(args.project_id)
        gold_payload = load_d7_gold_file(args.gold_file)
        packages = [load_prediction_package(path) for path in args.predictions_file]
        protocol_payload = _load_protocol_if_requested(args)
        preflight_report = _run_preflight_if_requested(
            args,
            gold_payload,
            packages,
            protocol_payload,
        )
        if preflight_report is not None and preflight_report.status != "pass":
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": "D7 comparison preflight failed",
                        "preflight_report": preflight_report.model_dump(mode="json"),
                    },
                    indent=2,
                )
            )
            return 1
        report = compare_d7_retrieval_predictions(
            state,
            gold_payload=gold_payload,
            prediction_packages=packages,
        )
        metric_criteria_report = _evaluate_metric_criteria_if_requested(
            protocol_payload,
            report,
        )
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    if preflight_report is not None:
        report["preflight_report"] = preflight_report.model_dump(mode="json")
    if metric_criteria_report is not None:
        report["metric_criteria_report"] = metric_criteria_report.model_dump(mode="json")
    report["_meta"] = {
        "input_hashes": _comparison_input_hashes(args, state),
        "command": _comparison_command_provenance(args),
    }
    text = json.dumps(report, indent=2)
    if args.artifact_dir:
        try:
            write_d7_comparison_artifact(
                report,
                args.artifact_dir,
                state=state,
                report_text=text,
            )
        except (OSError, ValueError) as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


def load_prediction_package(path: Path) -> dict[str, Any]:
    """Load one retrieval prediction package from disk."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D7 retrieval prediction file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D7 retrieval prediction file '{path}' is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"D7 retrieval prediction file '{path}' must be a JSON object")
    return raw


def _run_preflight_if_requested(
    args: argparse.Namespace,
    gold_payload: Any,
    prediction_packages: list[dict[str, Any]],
    protocol_payload: Any | None,
) -> D7ComparisonPreflightReport | None:
    """Run D7 comparison preflight when a protocol package is supplied."""
    if protocol_payload is None:
        return None
    prediction_hashes: dict[str, str] = {}
    for path, package in zip(args.predictions_file, prediction_packages, strict=True):
        prediction_hash = _sha256_file(path, label="prediction")
        for baseline_name in _baseline_names(package):
            prediction_hashes[baseline_name] = prediction_hash
    return preflight_d7_comparison_payloads(
        protocol_payload,
        gold_payload,
        prediction_packages,
        prediction_file_sha256_by_baseline=prediction_hashes,
    )


def _load_protocol_if_requested(args: argparse.Namespace) -> Any | None:
    """Load the optional D7 comparison protocol payload."""
    if args.protocol_package is None:
        return None
    return _load_json(args.protocol_package, label="protocol package")


def _evaluate_metric_criteria_if_requested(
    protocol_payload: Any | None,
    report: dict[str, Any],
) -> D7MetricCriteriaReport | None:
    """Evaluate optional protocol metric criteria after a passing comparison."""
    if protocol_payload is None:
        return None
    return evaluate_d7_comparison_metric_criteria(protocol_payload, report)


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D7 comparison {label} '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D7 comparison {label} '{path}' is not valid JSON: {exc}") from exc


def _baseline_names(payload: dict[str, Any]) -> list[str]:
    """Return baseline names from a prediction payload when structurally available."""
    raw_baselines = payload.get("disconfirmation_baselines")
    if not isinstance(raw_baselines, list):
        return []
    names: list[str] = []
    for raw_baseline in raw_baselines:
        if isinstance(raw_baseline, dict) and isinstance(raw_baseline.get("name"), str):
            names.append(raw_baseline["name"])
    return names


def _comparison_input_hashes(
    args: argparse.Namespace,
    state: ProjectState,
) -> dict[str, Any]:
    """Return deterministic input hashes for one D7 comparison report."""
    return {
        "hash_algorithm": "sha256",
        "project_id": args.project_id,
        "project_state_sha256": _sha256_jsonable(state.model_dump(mode="json")),
        "corpus_sha256": _sha256_jsonable(state.corpus.model_dump(mode="json")),
        "gold_file_sha256": _sha256_file(args.gold_file, label="gold"),
        "prediction_files": [
            {
                "path": str(path),
                "sha256": _sha256_file(path, label="prediction"),
            }
            for path in args.predictions_file
        ],
        "protocol_file_sha256": (
            _sha256_file(args.protocol_package, label="protocol")
            if args.protocol_package is not None
            else None
        ),
    }


def _comparison_command_provenance(args: argparse.Namespace) -> dict[str, Any]:
    """Return command-path provenance for one D7 comparison report."""
    return {
        "project_id": args.project_id,
        "gold_file": str(args.gold_file),
        "prediction_files": [str(path) for path in args.predictions_file],
        "protocol_package": (
            str(args.protocol_package) if args.protocol_package is not None else None
        ),
        "output": str(args.output) if args.output is not None else None,
        "artifact_dir": str(args.artifact_dir) if args.artifact_dir is not None else None,
    }


def write_d7_comparison_artifact(
    report: dict[str, Any],
    artifact_root: Path,
    *,
    state: ProjectState,
    generated_at: datetime | None = None,
    report_text: str | None = None,
) -> Path:
    """Write a versioned D7 comparison artifact package."""
    generated_at = _utc_generated_at(generated_at)
    run_dir = artifact_root / d7_comparison_artifact_dir_name(state.id, generated_at)
    if run_dir.exists():
        raise ValueError(f"D7 comparison artifact directory already exists: {run_dir}")

    report_text = report_text if report_text is not None else json.dumps(report, indent=2)
    report_bytes = report_text.encode("utf-8")
    manifest = d7_comparison_artifact_manifest(
        report,
        state=state,
        generated_at=generated_at,
        report_sha256=hashlib.sha256(report_bytes).hexdigest(),
    )

    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "report.json").write_bytes(report_bytes)
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return run_dir


def d7_comparison_artifact_manifest(
    report: dict[str, Any],
    *,
    state: ProjectState,
    generated_at: datetime,
    report_sha256: str,
) -> dict[str, Any]:
    """Build a manifest for one D7 retrieval comparison artifact package."""
    meta = report.get("_meta", {})
    input_hashes = meta.get("input_hashes")
    if not isinstance(input_hashes, dict):
        raise ValueError("D7 comparison report is missing _meta.input_hashes")
    command = meta.get("command")
    if not isinstance(command, dict):
        raise ValueError("D7 comparison report is missing _meta.command")
    return {
        "schema_version": 1,
        "artifact_type": "qualitative_coding.d7_retrieval_comparison",
        "generated_at": _format_generated_at(generated_at),
        "project_id": state.id,
        "project_name": state.name,
        "report_file": "report.json",
        "report_sha256": report_sha256,
        "input_hashes": input_hashes,
        "command": command,
        "claim_discipline": {
            "caveat": D7_COMPARISON_ARTIFACT_CAVEAT,
        },
        "prompt_eval": {
            "status": "not_run",
            "owner": "prompt_eval",
            "note": (
                "D7 comparison artifact packaging only; held-out datasets, live "
                "baseline runs, statistical comparisons, and experiment tracking "
                "belong to the future prompt_eval-backed suite."
            ),
        },
    }


def d7_comparison_artifact_dir_name(project_id: str, generated_at: datetime) -> str:
    """Return the versioned run-directory name for a D7 comparison artifact."""
    return f"{_format_artifact_timestamp(generated_at)}-{_artifact_slug(project_id)}-d7-comparison"


def _sha256_jsonable(payload: Any) -> str:
    """Hash a JSON-serializable object with canonical JSON and SHA-256."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sha256_file(path: Path, *, label: str = "prediction") -> str:
    """Hash file bytes with SHA-256."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(
            f"D7 comparison {label} file '{path}' could not be hashed: {exc}"
        ) from exc


def _utc_generated_at(generated_at: datetime | None) -> datetime:
    """Normalize artifact generation time to UTC."""
    if generated_at is None:
        return datetime.now(timezone.utc)
    if generated_at.tzinfo is None:
        return generated_at.replace(tzinfo=timezone.utc)
    return generated_at.astimezone(timezone.utc)


def _format_generated_at(generated_at: datetime) -> str:
    """Return an ISO-8601 UTC artifact timestamp."""
    return _utc_generated_at(generated_at).isoformat().replace("+00:00", "Z")


def _format_artifact_timestamp(generated_at: datetime) -> str:
    """Return a filesystem-safe UTC artifact timestamp."""
    return _utc_generated_at(generated_at).strftime("%Y%m%dT%H%M%S%fZ")


def _artifact_slug(value: str) -> str:
    """Return a filesystem-safe artifact slug."""
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-._")
    return slug or "project"


if __name__ == "__main__":
    raise SystemExit(main())
