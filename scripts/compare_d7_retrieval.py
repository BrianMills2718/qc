#!/usr/bin/env python3
"""Compare exported D7 retrieval prediction packages against a gold file."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d7_comparison_preflight import (
    D7ComparisonPreflightReport,
    preflight_d7_comparison_payloads,
)
from qc_clean.core.d7_retrieval import compare_d7_retrieval_predictions
from qc_clean.core.persistence.project_store import ProjectStore
from scripts.bench_phase0 import load_d7_gold_file


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
    args = parser.parse_args(argv)

    store = ProjectStore()
    try:
        state = store.load(args.project_id)
        gold_payload = load_d7_gold_file(args.gold_file)
        packages = [load_prediction_package(path) for path in args.predictions_file]
        preflight_report = _run_preflight_if_requested(args, gold_payload, packages)
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
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    text = json.dumps(report, indent=2)
    if preflight_report is not None:
        report["preflight_report"] = preflight_report.model_dump(mode="json")
        text = json.dumps(report, indent=2)
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
) -> D7ComparisonPreflightReport | None:
    """Run D7 comparison preflight when a protocol package is supplied."""
    protocol_path = args.protocol_package
    if protocol_path is None:
        return None
    protocol_payload = _load_json(protocol_path, label="protocol package")
    prediction_hashes: dict[str, str] = {}
    for path, package in zip(args.predictions_file, prediction_packages, strict=True):
        prediction_hash = _sha256_file(path)
        for baseline_name in _baseline_names(package):
            prediction_hashes[baseline_name] = prediction_hash
    return preflight_d7_comparison_payloads(
        protocol_payload,
        gold_payload,
        prediction_packages,
        prediction_file_sha256_by_baseline=prediction_hashes,
    )


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


def _sha256_file(path: Path) -> str:
    """Hash file bytes with SHA-256."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(f"D7 retrieval prediction file '{path}' could not be hashed: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
