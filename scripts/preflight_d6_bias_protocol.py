#!/usr/bin/env python3
"""Preflight D6 bias result files against a registered protocol."""

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

from qc_clean.core.d6_bias_preflight import (
    D6_BIAS_PREFLIGHT_CAUTION,
    D6BiasPreflightError,
    D6BiasPreflightReport,
    preflight_d6_bias_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run D6 bias protocol/result preflight and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(
        description="Preflight D6 bias result files against a registered protocol"
    )
    parser.add_argument("protocol", help="Path to a schema_version=1 D6 bias protocol JSON")
    parser.add_argument(
        "--stratified-file",
        help="Optional D6 stratified correctness/error result JSON file",
    )
    parser.add_argument(
        "--counterfactual-file",
        help="Optional D6 counterfactual identity-swap result JSON file",
    )
    args = parser.parse_args(argv)

    try:
        protocol_payload = _load_json(Path(args.protocol), label="protocol")
        stratified_payload = None
        stratified_hash = None
        if args.stratified_file:
            stratified_path = Path(args.stratified_file)
            stratified_payload = _load_json(stratified_path, label="stratified")
            stratified_hash = _sha256_file(stratified_path, label="stratified")
        counterfactual_payload = None
        counterfactual_hash = None
        if args.counterfactual_file:
            counterfactual_path = Path(args.counterfactual_file)
            counterfactual_payload = _load_json(counterfactual_path, label="counterfactual")
            counterfactual_hash = _sha256_file(counterfactual_path, label="counterfactual")
        report = preflight_d6_bias_payloads(
            protocol_payload,
            stratified_payload,
            counterfactual_payload,
            stratified_file_sha256=stratified_hash,
            counterfactual_file_sha256=counterfactual_hash,
        )
    except ValueError as exc:
        report = D6BiasPreflightReport(
            schema_version=1,
            package_type="d6_bias_protocol_result_preflight",
            status="fail",
            dimensions=[],
            stratified_row_count=0,
            counterfactual_row_count=0,
            errors=[D6BiasPreflightError(field="inputs", message=str(exc))],
            caution=D6_BIAS_PREFLIGHT_CAUTION,
        )

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D6 bias {label} file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D6 bias {label} file '{path}' is not valid JSON: {exc}") from exc


def _sha256_file(path: Path, *, label: str) -> str:
    """Hash file bytes with SHA-256."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(f"D6 bias {label} file '{path}' could not be hashed: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
