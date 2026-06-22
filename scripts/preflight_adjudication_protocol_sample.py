#!/usr/bin/env python3
"""Preflight an adjudication protocol package against a sample package."""

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

from qc_clean.core.adjudication_preflight import (
    AdjudicationPreflightError,
    AdjudicationProtocolSamplePreflightReport,
    preflight_adjudication_protocol_sample_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run protocol-to-sample preflight and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(
        description="Preflight an adjudication protocol package against a sample package"
    )
    parser.add_argument("protocol", help="Path to a schema_version=1 protocol JSON package")
    parser.add_argument("sample", help="Path to a schema_version=1 adjudication sample JSON package")
    args = parser.parse_args(argv)

    protocol_path = Path(args.protocol)
    sample_path = Path(args.sample)
    try:
        protocol_payload = _load_json(protocol_path, label="protocol")
        sample_payload = _load_json(sample_path, label="sample")
        sample_hash = _sha256_file(sample_path)
        report = preflight_adjudication_protocol_sample_payloads(
            protocol_payload,
            sample_payload,
            sample_file_sha256=sample_hash,
        )
    except ValueError as exc:
        report = AdjudicationProtocolSamplePreflightReport(
            schema_version=1,
            package_type="adjudication_protocol_sample_preflight",
            status="fail",
            total_returned_count=0,
            errors=[AdjudicationPreflightError(field="package", message=str(exc))],
            caution=(
                "Adjudication protocol/sample preflight is process metadata only; "
                "it is not expert evidence, labels, correctness estimates, validity "
                "evidence, or a benchmark result."
            ),
        )

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Adjudication {label} file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Adjudication {label} file '{path}' is not valid JSON: {exc}") from exc


def _sha256_file(path: Path) -> str:
    """Return the SHA-256 hash for a local file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
