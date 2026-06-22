#!/usr/bin/env python3
"""Preflight D3 baseline comparison inputs against a registered protocol."""

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

from qc_clean.core.d3_comparison_preflight import (
    D3_COMPARISON_PREFLIGHT_CAUTION,
    D3ComparisonPreflightError,
    D3ComparisonPreflightReport,
    preflight_d3_comparison_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run D3 comparison preflight and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(
        description="Preflight D3 baseline comparison inputs against a protocol"
    )
    parser.add_argument("protocol", help="Path to a schema_version=1 D3 comparison protocol JSON")
    parser.add_argument("gold", help="Path to a schema_version=1 D3 gold package JSON")
    parser.add_argument(
        "predictions",
        nargs="+",
        help="One or more D3 baseline prediction package JSON files",
    )
    args = parser.parse_args(argv)

    try:
        protocol_payload = _load_json(Path(args.protocol), label="protocol")
        gold_payload = _load_json(Path(args.gold), label="gold")
        prediction_payloads: list[Any] = []
        prediction_hashes: dict[str, str] = {}
        for prediction_path_text in args.predictions:
            prediction_path = Path(prediction_path_text)
            prediction_payload = _load_json(prediction_path, label="prediction")
            prediction_payloads.append(prediction_payload)
            prediction_hash = _sha256_file(prediction_path)
            for baseline_name in _baseline_names(prediction_payload):
                prediction_hashes[baseline_name] = prediction_hash
        report = preflight_d3_comparison_payloads(
            protocol_payload,
            gold_payload,
            prediction_payloads,
            prediction_file_sha256_by_baseline=prediction_hashes,
        )
    except ValueError as exc:
        report = D3ComparisonPreflightReport(
            schema_version=1,
            package_type="d3_baseline_comparison_preflight",
            status="fail",
            expected_prediction_count=0,
            prediction_package_count=0,
            baseline_count=0,
            errors=[D3ComparisonPreflightError(field="inputs", message=str(exc))],
            caution=D3_COMPARISON_PREFLIGHT_CAUTION,
        )

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D3 comparison {label} file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D3 comparison {label} file '{path}' is not valid JSON: {exc}") from exc


def _baseline_names(payload: Any) -> list[str]:
    """Return baseline names from a prediction payload when structurally available."""
    if not isinstance(payload, dict):
        return []
    raw_baselines = payload.get("application_baselines")
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
        raise ValueError(f"D3 comparison prediction file '{path}' could not be hashed: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
