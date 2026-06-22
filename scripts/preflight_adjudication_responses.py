#!/usr/bin/env python3
"""Preflight completed adjudication responses against protocol and sample packages."""

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

from qc_clean.core.adjudication_preflight import AdjudicationPreflightError
from qc_clean.core.adjudication_response_preflight import (
    AdjudicationResponsePreflightReport,
    preflight_adjudication_responses_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run response preflight and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(
        description="Preflight completed adjudication responses against protocol and sample packages"
    )
    parser.add_argument("protocol", help="Path to a schema_version=1 protocol JSON package")
    parser.add_argument("sample", help="Path to a schema_version=1 adjudication sample JSON package")
    parser.add_argument("responses", help="Path to a completed adjudication response JSON package")
    args = parser.parse_args(argv)

    protocol_path = Path(args.protocol)
    sample_path = Path(args.sample)
    responses_path = Path(args.responses)
    try:
        protocol_payload = _load_json(protocol_path, label="protocol")
        sample_payload = _load_json(sample_path, label="sample")
        response_payload = _load_json(responses_path, label="responses")
        sample_hash = _sha256_file(sample_path)
        report = preflight_adjudication_responses_payloads(
            protocol_payload,
            sample_payload,
            response_payload,
            sample_file_sha256=sample_hash,
        )
    except ValueError as exc:
        report = AdjudicationResponsePreflightReport(
            schema_version=1,
            package_type="adjudication_response_preflight",
            status="fail",
            sample_item_count=0,
            response_item_count=0,
            completed_response_count=0,
            errors=[AdjudicationPreflightError(field="package", message=str(exc))],
            caution=(
                "Adjudication response preflight is process metadata only; it is not "
                "expert evidence, labels, correctness estimates, validity evidence, "
                "or a benchmark result."
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
