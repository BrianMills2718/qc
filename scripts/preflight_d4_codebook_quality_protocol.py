#!/usr/bin/env python3
"""Preflight D4 codebook-quality result files against a registered protocol."""

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

from qc_clean.core.d4_codebook_quality_preflight import (
    D4_CODEBOOK_QUALITY_PREFLIGHT_CAUTION,
    D4CodebookQualityPreflightError,
    D4CodebookQualityPreflightReport,
    preflight_d4_codebook_quality_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run D4 codebook-quality preflight and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(
        description=(
            "Preflight D4 codebook-quality result files against a registered "
            "protocol"
        )
    )
    parser.add_argument(
        "protocol",
        help="Path to a schema_version=1 D4 codebook-quality protocol JSON",
    )
    parser.add_argument(
        "--quality-file",
        help="Optional D4 codebook-quality result JSON file",
    )
    args = parser.parse_args(argv)

    try:
        protocol_payload = _load_json(Path(args.protocol), label="protocol")
        quality_payload = None
        quality_hash = None
        if args.quality_file:
            quality_path = Path(args.quality_file)
            quality_payload = _load_json(quality_path, label="quality")
            quality_hash = _sha256_file(quality_path, label="quality")
        report = preflight_d4_codebook_quality_payloads(
            protocol_payload,
            quality_payload,
            quality_file_sha256=quality_hash,
        )
    except ValueError as exc:
        report = D4CodebookQualityPreflightReport(
            schema_version=1,
            package_type="d4_codebook_quality_protocol_result_preflight",
            status="fail",
            rubric_metrics=[],
            target_scopes=[],
            result_row_count=0,
            evaluator_count=0,
            evaluator_types=[],
            errors=[D4CodebookQualityPreflightError(field="inputs", message=str(exc))],
            caution=D4_CODEBOOK_QUALITY_PREFLIGHT_CAUTION,
        )

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"D4 codebook-quality {label} file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"D4 codebook-quality {label} file '{path}' is not valid JSON: {exc}"
        ) from exc


def _sha256_file(path: Path, *, label: str) -> str:
    """Hash file bytes with SHA-256."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(
            f"D4 codebook-quality {label} file '{path}' could not be hashed: {exc}"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
