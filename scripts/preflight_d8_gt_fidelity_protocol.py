#!/usr/bin/env python3
"""Preflight D8 GT-fidelity result files against a registered protocol."""

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

from qc_clean.core.d8_gt_fidelity_preflight import (
    D8_GT_FIDELITY_PREFLIGHT_CAUTION,
    D8GTFidelityPreflightError,
    D8GTFidelityPreflightReport,
    preflight_d8_gt_fidelity_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run D8 GT-fidelity preflight and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(
        description=(
            "Preflight D8 GT-fidelity result files against a registered "
            "protocol"
        )
    )
    parser.add_argument(
        "protocol",
        help="Path to a schema_version=1 D8 GT-fidelity protocol JSON",
    )
    parser.add_argument(
        "--gt-fidelity-file",
        help="Optional D8 GT-fidelity result JSON file",
    )
    args = parser.parse_args(argv)

    try:
        protocol_payload = _load_json(Path(args.protocol), label="protocol")
        gt_fidelity_payload = None
        gt_fidelity_hash = None
        if args.gt_fidelity_file:
            gt_fidelity_path = Path(args.gt_fidelity_file)
            gt_fidelity_payload = _load_json(gt_fidelity_path, label="GT-fidelity")
            gt_fidelity_hash = _sha256_file(gt_fidelity_path, label="GT-fidelity")
        report = preflight_d8_gt_fidelity_payloads(
            protocol_payload,
            gt_fidelity_payload,
            gt_fidelity_file_sha256=gt_fidelity_hash,
        )
    except ValueError as exc:
        report = D8GTFidelityPreflightReport(
            schema_version=1,
            package_type="d8_gt_fidelity_protocol_result_preflight",
            status="fail",
            rubric_metrics=[],
            target_scopes=[],
            result_row_count=0,
            evaluator_count=0,
            evaluator_types=[],
            artifact_count=0,
            errors=[D8GTFidelityPreflightError(field="inputs", message=str(exc))],
            caution=D8_GT_FIDELITY_PREFLIGHT_CAUTION,
        )

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"D8 GT-fidelity {label} file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"D8 GT-fidelity {label} file '{path}' is not valid JSON: {exc}"
        ) from exc


def _sha256_file(path: Path, *, label: str) -> str:
    """Hash file bytes with SHA-256."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(
            f"D8 GT-fidelity {label} file '{path}' could not be hashed: {exc}"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
