#!/usr/bin/env python3
"""Preflight confidence-calibration results against a protocol."""

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

from qc_clean.core.confidence_calibration_preflight import (  # noqa: E402
    CONFIDENCE_CALIBRATION_PREFLIGHT_CAUTION,
    ConfidenceCalibrationPreflightError,
    ConfidenceCalibrationPreflightReport,
    preflight_confidence_calibration_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run confidence-calibration preflight and emit JSON."""
    parser = argparse.ArgumentParser(
        description=(
            "Preflight confidence-calibration result files against a registered "
            "protocol"
        )
    )
    parser.add_argument(
        "protocol",
        help="Path to a schema_version=1 confidence-calibration protocol JSON",
    )
    parser.add_argument(
        "--calibration-file",
        help="Optional confidence-calibration result JSON file",
    )
    args = parser.parse_args(argv)

    try:
        protocol_payload = _load_json(Path(args.protocol), label="protocol")
        calibration_payload = None
        calibration_hash = None
        if args.calibration_file:
            calibration_path = Path(args.calibration_file)
            calibration_payload = _load_json(calibration_path, label="calibration")
            calibration_hash = _sha256_file(calibration_path, label="calibration")
        report = preflight_confidence_calibration_payloads(
            protocol_payload,
            calibration_payload,
            calibration_file_sha256=calibration_hash,
        )
    except ValueError as exc:
        report = ConfidenceCalibrationPreflightReport(
            schema_version=1,
            package_type="confidence_calibration_protocol_result_preflight",
            status="fail",
            target_surfaces=[],
            outcome_metrics=[],
            result_row_count=0,
            item_count=0,
            evaluator_count=0,
            evaluators=[],
            errors=[
                ConfidenceCalibrationPreflightError(
                    field="inputs",
                    message=str(exc),
                )
            ],
            caution=CONFIDENCE_CALIBRATION_PREFLIGHT_CAUTION,
        )

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"Confidence-calibration {label} file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Confidence-calibration {label} file '{path}' is not valid JSON: {exc}"
        ) from exc


def _sha256_file(path: Path, *, label: str) -> str:
    """Hash file bytes with SHA-256."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(
            f"Confidence-calibration {label} file '{path}' could not be hashed: {exc}"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
