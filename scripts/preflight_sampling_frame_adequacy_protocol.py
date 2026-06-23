#!/usr/bin/env python3
"""Preflight sampling-frame adequacy result packages against protocols."""

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

from qc_clean.core.sampling_frame_adequacy_preflight import (
    SAMPLING_FRAME_ADEQUACY_PREFLIGHT_CAUTION,
    SamplingFrameAdequacyPreflightError,
    SamplingFrameAdequacyPreflightReport,
    preflight_sampling_frame_adequacy_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run sampling-frame adequacy preflight and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(
        description=(
            "Preflight sampling-frame adequacy result packages against a "
            "registered protocol"
        )
    )
    parser.add_argument(
        "protocol",
        help="Path to a schema_version=1 sampling-frame adequacy protocol JSON",
    )
    parser.add_argument(
        "--adequacy-file",
        help="Optional sampling-frame adequacy result JSON file",
    )
    args = parser.parse_args(argv)

    try:
        protocol_payload = _load_json(Path(args.protocol), label="protocol")
        adequacy_payload = None
        adequacy_hash = None
        if args.adequacy_file:
            adequacy_path = Path(args.adequacy_file)
            adequacy_payload = _load_json(adequacy_path, label="adequacy")
            adequacy_hash = _sha256_file(adequacy_path, label="adequacy")
        report = preflight_sampling_frame_adequacy_payloads(
            protocol_payload,
            adequacy_payload,
            adequacy_file_sha256=adequacy_hash,
        )
    except ValueError as exc:
        report = SamplingFrameAdequacyPreflightReport(
            schema_version=1,
            package_type="sampling_frame_adequacy_protocol_result_preflight",
            status="fail",
            dimensions=[],
            result_row_count=0,
            reviewer_count=0,
            reviewer_types=[],
            ratings=[],
            errors=[SamplingFrameAdequacyPreflightError(field="inputs", message=str(exc))],
            caution=SAMPLING_FRAME_ADEQUACY_PREFLIGHT_CAUTION,
        )

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"sampling-frame adequacy {label} file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"sampling-frame adequacy {label} file '{path}' is not valid JSON: {exc}"
        ) from exc


def _sha256_file(path: Path, *, label: str) -> str:
    """Hash file bytes with SHA-256."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(
            f"sampling-frame adequacy {label} file '{path}' could not be hashed: {exc}"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
